// The chain walk of steam_layout/chains.py with extra presses, built for large press counts.
//
// It gives the same stacks and the same lost exits as walk_engine.cpp's chain mode, which
// tests/test_native.py checks. It differs in how it gets there:
//
//   - A state is (stack, the layer the chain is on). How many extra presses it took is not part
//     of the state: the walk goes by cost, cheapest first, so every state is met once, at its
//     lowest cost. A press of the chain's own layer or a removal is free; any other add costs one.
//   - The table of known states is split into parts by the stack's hash. New states are sorted
//     into one queue per part, and each part is then filled by a single thread, so the part being
//     worked on fits in the processor's cache and no lock guards it.
//   - A stack is tested once, when its first state is met, not once per state.
//   - A state takes 18 bytes. No path is kept; steam_layout/native.py gets paths from
//     walk_engine.cpp, which keeps them, at the cost the example needs.
//
// It reads the layout's tables from stdin (native.py writes them) and prints JSON. Nothing is
// written to disk.
//
// Build: clang++ -O3 -std=c++17 -pthread -o build/chain_engine chain_engine.cpp
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <vector>

typedef unsigned __int128 u128;
static const int MAXL = 18;                          // layers in one stack, the action set included
static const int PART_BITS = 14;
static const uint32_t PARTS = 1u << PART_BITS;
static const size_t CHUNK = 2000000;                 // states expanded before their children are filed
enum { FREE = 0, ARRIVAL = 1 };

struct Group { int source, mode; std::vector<int> controls; };
struct Move { int id, control, adding; std::vector<std::pair<int, int>> ops; };
struct Exit { int id, control, source, on_keeper, mine; };

static int NL, BASE, NC, NS, MAX_LAYERS, EXTRAS, LANDINGS, THREADS;
static long MEMORY_MB;
static std::vector<std::vector<Group>> groups;
static std::vector<std::vector<Move>> moves;
static std::vector<std::vector<Exit>> exits_;
static std::vector<int> carry_index;                 // layer * NC + control -> index into carry_mask, or -1
static std::vector<std::pair<uint64_t, uint64_t>> carry_mask;
static std::atomic<bool> overflow(false);
static std::atomic<uint64_t> table_bytes(0), pending(0);

static inline u128 pack(const uint8_t* s, int n) {
    u128 k = 0;
    for (int i = n - 1; i >= 0; --i) k = (k << 7) | (u128)(s[i] + 1);
    return k;
}
static inline int unpack(u128 k, uint8_t* s) {
    int n = 0;
    while (k) { s[n++] = (uint8_t)((uint64_t)(k & 127) - 1); k >>= 7; }
    return n;
}
static inline uint64_t mix(uint64_t h) {
    h ^= h >> 29; h *= 0xBF58476D1CE4E5B9ULL; h ^= h >> 32; h *= 0x94D049BB133111EBULL; h ^= h >> 29;
    return h;
}
static inline uint64_t hash_stack(u128 k) {
    return mix(((uint64_t)k * 0x9E3779B97F4A7C15ULL) ^ ((uint64_t)(k >> 64) * 0xC2B2AE3D27D4EB4FULL));
}
static inline uint32_t hash_state(uint64_t hs, int head) { return (uint32_t)mix(hs ^ ((uint64_t)(head + 1) * 0xD6E8FEB86659FD93ULL)); }

struct SpinLock {
    std::atomic_flag flag = ATOMIC_FLAG_INIT;
    void lock() {
        for (int spins = 0; flag.test_and_set(std::memory_order_acquire); ++spins) {
            if (spins < 128) {
#if defined(__aarch64__)
                __asm__ __volatile__("yield");
#elif defined(__x86_64__)
                __builtin_ia32_pause();
#endif
            } else { std::this_thread::yield(); spins = 0; }
        }
    }
    void unlock() { flag.clear(std::memory_order_release); }
};

#pragma pack(push, 1)
struct Rec { u128 stack; uint8_t head, kind; };      // one child, on its way to the part that owns it
struct State { u128 stack; uint8_t head; };
#pragma pack(pop)

// meta: bits 0-6 the chain's layer, 7-10 the cost, 11 set while the state waits for its cost's turn.
static const uint16_t WAITING = 1u << 11;
static inline uint16_t meta_of(int head, int cost, bool waiting) { return (uint16_t)(head | (cost << 7) | (waiting ? WAITING : 0)); }
static inline int cost_of(uint16_t m) { return (m >> 7) & 15; }

struct alignas(128) Part {
    u128* keys = nullptr; uint16_t* meta = nullptr; uint32_t cap = 0, n = 0;     // the states
    u128* seen = nullptr; uint32_t seen_cap = 0, seen_n = 0;                    // the stacks already tested
    SpinLock lock; std::vector<Rec> queue;

    static inline uint32_t slot(uint32_t h, uint32_t cap) { return (uint32_t)(((uint64_t)h * cap) >> 32); }
    void grow() {
        uint32_t cap2 = cap ? cap + cap / 4 + 16 : 16;
        u128* k2 = (u128*)calloc(cap2, sizeof(u128));
        uint16_t* m2 = (uint16_t*)calloc(cap2, sizeof(uint16_t));
        if (!k2 || !m2) { fprintf(stderr, "out of memory\n"); exit(3); }
        for (uint32_t i = 0; i < cap; ++i)
            if (keys[i]) {
                uint32_t j = slot(hash_state(hash_stack(keys[i]), meta[i] & 127), cap2);
                while (k2[j]) j = j + 1 == cap2 ? 0 : j + 1;
                k2[j] = keys[i]; m2[j] = meta[i];
            }
        free(keys); free(meta);
        table_bytes += (uint64_t)(cap2 - cap) * (sizeof(u128) + sizeof(uint16_t));
        keys = k2; meta = m2; cap = cap2;
    }
    // The slot of (stack, head), or of the empty slot where it belongs.
    inline uint32_t find(u128 stack, int head, uint64_t hs) const {
        uint32_t j = slot(hash_state(hs, head), cap);
        while (keys[j] && !(keys[j] == stack && (meta[j] & 127) == head)) j = j + 1 == cap ? 0 : j + 1;
        return j;
    }
    // True the first time a stack is seen.
    bool first_time(u128 stack, uint64_t hs) {
        if ((uint64_t)(seen_n + 1) * 5 > (uint64_t)seen_cap * 4) {
            uint32_t cap2 = seen_cap ? seen_cap + seen_cap / 4 + 16 : 16;
            u128* s2 = (u128*)calloc(cap2, sizeof(u128));
            if (!s2) { fprintf(stderr, "out of memory\n"); exit(3); }
            for (uint32_t i = 0; i < seen_cap; ++i)
                if (seen[i]) {
                    uint32_t j = slot((uint32_t)hash_stack(seen[i]), cap2);
                    while (s2[j]) j = j + 1 == cap2 ? 0 : j + 1;
                    s2[j] = seen[i];
                }
            free(seen);
            table_bytes += (uint64_t)(cap2 - seen_cap) * sizeof(u128);
            seen = s2; seen_cap = cap2;
        }
        uint32_t j = slot((uint32_t)hs, seen_cap);
        while (seen[j]) { if (seen[j] == stack) return false; j = j + 1 == seen_cap ? 0 : j + 1; }
        seen[j] = stack; ++seen_n;
        return true;
    }
};
static std::vector<Part> parts(PARTS);
static inline uint32_t part_of(uint64_t hs) { return (uint32_t)(hs >> (64 - PART_BITS)); }

struct Scratch {
    std::vector<int16_t> found, smode, stop_layer, top;
    std::vector<uint8_t> sstate, stop_kind;          // source state: 1 set, 2 stopped; stop kind: 1 disabled, 2 mode
    std::vector<uint32_t> cgen, sgen;
    uint32_t g = 0;
    Scratch() : found(NC), smode(NS), stop_layer(NS), top(NS), sstate(NS), stop_kind(NS), cgen(NC, 0), sgen(NS, 0) {}
    inline int answer(int control) const { return cgen[control] == g ? found[control] : -1; }
};

// The lookup of flow_model.resolve, for every input of a stack at once.
static void answers(const uint8_t* s, int n, Scratch& a) {
    ++a.g;
    for (int i = n - 1; i >= 0; --i) {
        int layer = s[i];
        for (const Group& grp : groups[layer]) {
            int src = grp.source;
            if (a.sgen[src] != a.g) { a.sgen[src] = a.g; a.sstate[src] = 0; a.stop_kind[src] = 0; }
            if (a.sstate[src] == 2) continue;
            if (grp.mode < 0) { a.sstate[src] = 2; a.stop_kind[src] = 1; a.stop_layer[src] = (int16_t)layer; continue; }
            if (a.sstate[src] == 0) { a.sstate[src] = 1; a.smode[src] = (int16_t)grp.mode; a.top[src] = (int16_t)layer; }
            else if (a.smode[src] != grp.mode) { a.sstate[src] = 2; a.stop_kind[src] = 2; a.stop_layer[src] = a.top[src]; continue; }
            for (int c : grp.controls)
                if (a.cgen[c] != a.g) { a.cgen[c] = a.g; a.found[c] = (int16_t)layer; }
        }
    }
}

static inline int apply(const uint8_t* s, int n, const Move& mv, uint8_t* t) {
    memcpy(t, s, n);
    int m = n;
    for (const auto& op : mv.ops) {
        int at = -1;
        for (int i = 0; i < m; ++i) if (t[i] == op.second) { at = i; break; }
        if (op.first) {
            if (at < 0) { if (m == MAXL) { overflow = true; return -1; } t[m++] = (uint8_t)op.second; }
        } else if (op.second != BASE && at >= 0) {
            memmove(t + at, t + at + 1, m - at - 1); --m;
        }
    }
    return m;
}

// One lost exit: (covering layer, lower layer) -> its exits, and the smallest stack that shows it.
struct Pair {
    std::vector<int> exits;
    int layers = 1 << 30, landing = -1;
    u128 shown = 0, source = 0;                      // the stack with the lost exit; the visited stack it came from
    void offer(int n, u128 stack, u128 from, int land) {
        if (n < layers || (n == layers && (stack < shown || (stack == shown && from < source)))) {
            layers = n; shown = stack; source = from; landing = land;
        }
    }
};
typedef std::unordered_map<uint32_t, Pair> Pairs;

static void lost(const uint8_t* s, int n, const Scratch& a, Pairs& out, u128 from, int landing) {
    u128 stack = 0;
    for (int at = 0; at < n; ++at) {
        int lower = s[at];
        for (const Exit& x : exits_[lower]) {
            int who = a.answer(x.control);
            if (who == lower) continue;
            if (who >= 0) {
                int ci = carry_index[who * NC + x.control];
                if (ci >= 0) {
                    const auto& mask = carry_mask[ci];
                    if (lower < 64 ? (mask.first >> lower) & 1 : (mask.second >> (lower - 64)) & 1) continue;
                }
            } else {
                bool stopped = a.sgen[x.source] == a.g && a.sstate[x.source] == 2;
                int top = stopped ? a.stop_layer[x.source] : s[n - 1];
                who = top;
                if (!(stopped && a.stop_kind[x.source] == 1)) {
                    // A mode change is charged to the first layer above `lower` in another mode.
                    bool found_one = false;
                    for (int j = at + 1; j < n && !found_one; ++j)
                        for (const Group& grp : groups[s[j]])
                            if (grp.source == x.source && grp.mode != x.mine) { who = s[j]; found_one = true; break; }
                }
            }
            if (!stack) stack = pack(s, n);
            Pair& p = out[(uint32_t)who << 16 | (uint32_t)lower];
            if (std::find(p.exits.begin(), p.exits.end(), x.id) == p.exits.end()) p.exits.push_back(x.id);
            p.offer(n, stack, from, landing);
        }
    }
}

struct Worker {
    Scratch a, b;
    std::vector<Rec> out;                            // PARTS small buffers, flushed to the parts' queues
    std::vector<uint8_t> fill;
    std::vector<State> next;
    Pairs pairs;
    uint64_t landings = 0;
    int longest = 0;
    static const int BUF = 16;
    Worker() : out((size_t)PARTS * BUF), fill(PARTS, 0) {}
    inline void emit(u128 stack, int head, int kind) {
        uint32_t p = part_of(hash_stack(stack));
        Rec& r = out[(size_t)p * BUF + fill[p]];
        r.stack = stack; r.head = (uint8_t)head; r.kind = (uint8_t)kind;
        if (++fill[p] == BUF) flush(p);
    }
    void flush(uint32_t p) {
        if (!fill[p]) return;
        Part& part = parts[p];
        std::lock_guard<SpinLock> hold(part.lock);
        part.queue.insert(part.queue.end(), out.begin() + (size_t)p * BUF, out.begin() + (size_t)p * BUF + fill[p]);
        fill[p] = 0;
    }
    void flush_all() { for (uint32_t p = 0; p < PARTS; ++p) flush(p); }
};

// Step one: the children of a state, sorted into the queue of the part that owns each.
static void expand(const State& state, int cost, Worker& w) {
    uint8_t s[MAXL], t[MAXL];
    int n = unpack(state.stack, s), head = state.head;
    answers(s, n, w.a);
    for (int i = 0; i < n; ++i) {
        int layer = s[i];
        for (const Move& mv : moves[layer]) {
            if (w.a.answer(mv.control) != layer) continue;
            int m = apply(s, n, mv, t);
            if (m < 0 || (MAX_LAYERS > 0 && m - 1 > MAX_LAYERS)) continue;
            bool changed = m != n || memcmp(s, t, n) != 0;
            u128 child = changed ? pack(t, m) : state.stack;
            if (!mv.adding) { if (changed) w.emit(child, head, FREE); continue; }
            if (cost < EXTRAS && changed) w.emit(child, head, ARRIVAL);
            if (layer == head)
                for (const auto& op : mv.ops)
                    if (op.first && memchr(t, op.second, m) && (changed || op.second != head)) w.emit(child, op.second, FREE);
        }
    }
}

// A stack met for the first time: its lost exits, and those of every stack one landing past it.
static void test(u128 stack, Worker& w) {
    uint8_t s[MAXL], t[MAXL];
    int n = unpack(stack, s);
    if (n - 1 > w.longest) w.longest = n - 1;
    answers(s, n, w.a);
    lost(s, n, w.a, w.pairs, stack, -1);
    if (!LANDINGS) return;
    for (int i = 0; i < n; ++i)
        for (const Move& mv : moves[s[i]]) {
            if (!mv.adding || w.a.answer(mv.control) != s[i]) continue;
            int m = apply(s, n, mv, t);
            if (m < 0 || (m == n && memcmp(s, t, n) == 0)) continue;
            ++w.landings;
            answers(t, m, w.b);
            lost(t, m, w.b, w.pairs, stack, mv.id);
        }
}

// Step two: one part takes in its queue. Only this thread touches the part.
static void file(Part& part, int cost, Worker& w) {
    for (const Rec& r : part.queue) {
        if ((uint64_t)(part.n + 1) * 5 > (uint64_t)part.cap * 4) part.grow();
        uint64_t hs = hash_stack(r.stack);
        uint32_t j = part.find(r.stack, r.head, hs);
        if (part.keys[j]) {
            // Known. A state waiting for the next cost that a free press now reaches belongs to this cost.
            if (r.kind == FREE && (part.meta[j] & WAITING) && cost_of(part.meta[j]) > cost) {
                part.meta[j] = meta_of(r.head, cost, false);
                --pending;
                w.next.push_back({r.stack, r.head});
            }
            continue;
        }
        part.keys[j] = r.stack; ++part.n;
        if (r.kind == FREE) { part.meta[j] = meta_of(r.head, cost, false); w.next.push_back({r.stack, r.head}); }
        else { part.meta[j] = meta_of(r.head, cost + 1, true); ++pending; }
        if (part.first_time(r.stack, hs)) test(r.stack, w);
    }
    part.queue.clear();
    if (part.queue.capacity() > 512) std::vector<Rec>().swap(part.queue);
}

static std::vector<Worker>* workers;

template <class F>
static void across(size_t count, size_t grain, F body) {
    std::atomic<size_t> cursor(0);
    auto run = [&](int i) {
        for (;;) {
            size_t from = cursor.fetch_add(grain);
            if (from >= count) break;
            size_t to = std::min(count, from + grain);
            for (size_t j = from; j < to; ++j) body(j, (*workers)[i]);
        }
    };
    if (THREADS == 1 || count <= grain) { run(0); return; }
    std::vector<std::thread> pool;
    for (int i = 0; i < THREADS; ++i) pool.emplace_back(run, i);
    for (auto& th : pool) th.join();
}

static void file_all(int cost) {
    for (Worker& w : *workers) w.flush_all();
    across(PARTS, 16, [&](size_t p, Worker& w) { if (!parts[p].queue.empty()) file(parts[p], cost, w); });
}

// Every state the frontier reaches by free presses, at this cost.
static void close_over(std::vector<State>& frontier, int cost) {
    while (!frontier.empty() && !overflow) {
        for (size_t from = 0; from < frontier.size(); from += CHUNK) {
            size_t to = std::min(frontier.size(), from + CHUNK);
            across(to - from, 512, [&](size_t j, Worker& w) { expand(frontier[from + j], cost, w); });
            file_all(cost);
        }
        frontier.clear();
        for (Worker& w : *workers) {
            frontier.insert(frontier.end(), w.next.begin(), w.next.end());
            std::vector<State>().swap(w.next);
        }
    }
}

static int read_int() { int v; if (scanf("%d", &v) != 1) { fprintf(stderr, "bad input\n"); exit(2); } return v; }

int main() {
    NL = read_int(); BASE = read_int(); NC = read_int(); NS = read_int(); MAX_LAYERS = read_int();
    read_int();                                      // the mode: this engine only walks chains
    EXTRAS = read_int(); LANDINGS = read_int(); THREADS = read_int(); MEMORY_MB = read_int();
    if (NL > 126 || EXTRAS > 14) { fprintf(stderr, "too many layers or extra presses\n"); return 2; }
    groups.resize(NL); moves.resize(NL); exits_.resize(NL);
    for (int l = 0; l < NL; ++l) {
        int g = read_int();
        for (int i = 0; i < g; ++i) {
            Group grp; grp.source = read_int(); grp.mode = read_int();
            int c = read_int();
            for (int j = 0; j < c; ++j) grp.controls.push_back(read_int());
            groups[l].push_back(grp);
        }
    }
    for (int l = 0; l < NL; ++l) {
        int m = read_int();
        for (int i = 0; i < m; ++i) {
            Move mv; mv.id = read_int(); mv.control = read_int(); mv.adding = read_int();
            int o = read_int();
            for (int j = 0; j < o; ++j) { int add = read_int(); int layer = read_int(); mv.ops.push_back({add, layer}); }
            moves[l].push_back(mv);
        }
    }
    carry_index.assign((size_t)NL * NC, -1);
    int r = read_int();
    for (int i = 0; i < r; ++i) {
        int layer = read_int(), control = read_int(), count = read_int();
        std::pair<uint64_t, uint64_t> mask(0, 0);
        for (int j = 0; j < count; ++j) { int x = read_int(); if (x < 64) mask.first |= 1ULL << x; else mask.second |= 1ULL << (x - 64); }
        carry_index[(size_t)layer * NC + control] = (int)carry_mask.size();
        carry_mask.push_back(mask);
    }
    for (int l = 0; l < NL; ++l) {
        int e = read_int();
        for (int i = 0; i < e; ++i) {
            Exit x; x.id = read_int(); x.control = read_int(); x.source = read_int(); x.on_keeper = read_int(); x.mine = read_int();
            exits_[l].push_back(x);
        }
    }
    if (THREADS < 1) THREADS = std::max(1u, std::thread::hardware_concurrency());
    std::vector<Worker> pool(THREADS);
    workers = &pool;

    auto began = std::chrono::steady_clock::now();
    bool settled = true;
    const char* stopped = "";
    uint8_t root[1] = {(uint8_t)BASE};
    u128 start = pack(root, 1);
    pool[0].emit(start, BASE, FREE);
    file_all(0);
    std::vector<State> frontier;
    for (Worker& w : pool) { frontier.insert(frontier.end(), w.next.begin(), w.next.end()); w.next.clear(); }

    auto total = []() { uint64_t n = 0; for (const Part& p : parts) n += p.n; return n; };
    auto over = [&]() { return MEMORY_MB > 0 && (long)(table_bytes.load() >> 20) > MEMORY_MB; };
    for (int cost = 0; cost <= EXTRAS && settled; ++cost) {
        if (cost == 0) close_over(frontier, 0);
        else {
            // The states that waited for this cost, a batch of parts at a time, so no long list of them is kept.
            uint64_t waiting = pending.load();
            uint32_t batch = (uint32_t)std::max<uint64_t>(16, std::min<uint64_t>(PARTS, 6000000ULL * PARTS / std::max<uint64_t>(1, waiting)));
            for (uint32_t from = 0; from < PARTS && !overflow && !over(); from += batch) {
                uint32_t to = std::min(PARTS, from + batch);
                across(to - from, 4, [&](size_t i, Worker& w) {
                    Part& part = parts[from + i];
                    for (uint32_t j = 0; j < part.cap; ++j)
                        if (part.keys[j] && (part.meta[j] & WAITING) && cost_of(part.meta[j]) == cost) {   // not the ones this cost just added
                            part.meta[j] &= (uint16_t)~WAITING;
                            --pending;
                            w.next.push_back({part.keys[j], (uint8_t)(part.meta[j] & 127)});
                        }
                });
                frontier.clear();
                for (Worker& w : pool) { frontier.insert(frontier.end(), w.next.begin(), w.next.end()); std::vector<State>().swap(w.next); }
                close_over(frontier, cost);
            }
        }
        fprintf(stderr, "walk: %d presses, %llu stacks, %.1f s, %llu MB\n", cost, (unsigned long long)total(),
                std::chrono::duration<double>(std::chrono::steady_clock::now() - began).count(), (unsigned long long)(table_bytes.load() >> 20));
        if (overflow) { settled = false; stopped = "a stack passed 18 layers"; }
        else if (over()) { settled = false; stopped = "the memory limit was reached"; }
    }
    double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - began).count();

    uint64_t states = 0, stacks = 0, landings = 0;
    std::vector<uint64_t> by_cost(EXTRAS + 2, 0);
    for (const Part& p : parts) {
        states += p.n; stacks += p.seen_n;
        for (uint32_t j = 0; j < p.cap; ++j) if (p.keys[j]) ++by_cost[cost_of(p.meta[j])];
    }
    Pairs pairs;
    int longest = 0;
    for (Worker& w : pool) {
        for (auto& item : w.pairs) {
            Pair& p = pairs[item.first];
            for (int id : item.second.exits)
                if (std::find(p.exits.begin(), p.exits.end(), id) == p.exits.end()) p.exits.push_back(id);
            p.offer(item.second.layers, item.second.shown, item.second.source, item.second.landing);
        }
        landings += w.landings;
        longest = std::max(longest, w.longest);
    }

    printf("{\"settled\": %s, \"stopped\": \"%s\", \"nodes\": %llu, \"stacks\": %llu, \"presses\": %d, \"longest\": %d, "
           "\"landings\": %llu, \"seconds\": %.3f, \"memory_mb\": %llu, \"threads\": %d, \"levels\": [",
           settled ? "true" : "false", stopped, (unsigned long long)states, (unsigned long long)stacks, EXTRAS, longest,
           (unsigned long long)landings, seconds, (unsigned long long)(table_bytes.load() >> 20), THREADS);
    for (int c = 0; c <= EXTRAS; ++c) printf("%s%llu", c ? ", " : "", (unsigned long long)by_cost[c]);
    printf("], \"pairs\": [");
    std::vector<uint32_t> keys;
    for (auto& item : pairs) keys.push_back(item.first);
    std::sort(keys.begin(), keys.end());
    bool first = true;
    uint8_t s[MAXL];
    for (uint32_t key : keys) {
        Pair& p = pairs[key];
        std::sort(p.exits.begin(), p.exits.end());
        // The fewest extra presses any state of the example's stack needed.
        uint64_t hs = hash_stack(p.source);
        const Part& part = parts[part_of(hs)];
        int cost = 15;
        for (int head = 0; head < NL && part.cap; ++head) {
            uint32_t j = part.find(p.source, head, hs);
            if (part.keys[j]) cost = std::min(cost, cost_of(part.meta[j]));
        }
        printf("%s{\"who\": %u, \"lower\": %u, \"cost\": %d, \"landing\": %d, \"exits\": [", first ? "" : ", ", key >> 16, key & 0xffff, cost, p.landing);
        first = false;
        for (size_t i = 0; i < p.exits.size(); ++i) printf("%s%d", i ? ", " : "", p.exits[i]);
        printf("], \"stack\": [");
        int n = unpack(p.shown, s);
        for (int i = 0; i < n; ++i) printf("%s%d", i ? ", " : "", s[i]);
        printf("], \"path\": []}");
    }
    printf("]}\n");
    return 0;
}
