// The walks of steam_layout/walk.py and steam_layout/chains.py, compiled.
//
// It reads the layout's tables from stdin (steam_layout/native.py writes them), builds every
// stack in memory on every core, tests each one for lost exits, and prints the result as JSON.
// Nothing is written to disk. The Python walks stay the reference; tests/test_native.py checks
// that both give the same stacks and the same findings.
//
//   mode 0  the capped walk: every followed binding on every stack, at most MAX_LAYERS on at once
//   mode 1  the chain walk: one layer's chain, with up to EXTRAS extra presses (arrivals) per chain
//
// Build: clang++ -O3 -std=c++17 -pthread -o build/walk_engine walk_engine.cpp
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
static const int MAXL = 16;                          // layers in one stack, the action set included
static const u128 STACK_MASK = (((u128)1) << 112) - 1;
static const u128 KEY_MASK = (((u128)1) << 123) - 1;

struct Group { int source, mode; std::vector<int> controls; };
struct Move { int id, control, adding; std::vector<std::pair<int, int>> ops; };
struct Exit { int id, control, source, on_keeper, mine; };

static int NL, BASE, NC, NS, MAX_LAYERS, MODE, EXTRAS, LANDINGS, THREADS;
static long MEMORY_MB;
static std::vector<std::vector<Group>> groups;
static std::vector<std::vector<Move>> moves;
static std::vector<std::vector<Exit>> exits_;
static std::vector<int> carry_index;                 // layer * NC + control -> index into carry_mask, or -1
static std::vector<std::pair<uint64_t, uint64_t>> carry_mask;
static std::atomic<bool> overflow(false);

static inline u128 pack(const uint8_t* s, int n, int head, int used) {
    u128 k = 0;
    for (int i = n - 1; i >= 0; --i) k = (k << 7) | (u128)(s[i] + 1);
    return k | ((u128)(head + 1) << 112) | ((u128)used << 119);
}
static inline int unpack(u128 k, uint8_t* s, int& head, int& used) {
    int n = 0;
    u128 low = k & STACK_MASK;
    while (low) { s[n++] = (uint8_t)((uint64_t)(low & 127) - 1); low >>= 7; }
    head = (int)((uint64_t)(k >> 112) & 127) - 1;
    used = (int)((uint64_t)(k >> 119) & 15);
    return n;
}
static inline uint64_t hash128(u128 k) {
    uint64_t lo = (uint64_t)k, hi = (uint64_t)(k >> 64);
    uint64_t h = (lo * 0x9E3779B97F4A7C15ULL) ^ (hi * 0xC2B2AE3D27D4EB4FULL);
    h ^= h >> 29; h *= 0xBF58476D1CE4E5B9ULL; h ^= h >> 32;
    return h;
}

// A table of known keys, split into shards so every thread can insert at once.
struct Entry { u128 key, value; };
struct Shard { std::mutex m; Entry* e = nullptr; uint64_t cap = 0, n = 0; };
struct Table {
    static const int BITS = 12;
    std::vector<Shard> shards;
    std::atomic<uint64_t> bytes{0}, count{0};
    Table() : shards(1 << BITS) {}
    static void place(Entry* e, uint64_t cap, u128 key, u128 value, uint64_t h) {
        uint64_t i = (h >> 8) & (cap - 1);
        while (e[i].key) i = (i + 1) & (cap - 1);
        e[i].key = key; e[i].value = value;
    }
    // True when the key is new. An existing key keeps the smaller value if `smaller` allows it.
    bool insert(u128 key, u128 value, bool same_level) {
        uint64_t h = hash128(key);
        Shard& s = shards[h >> (64 - BITS)];
        std::lock_guard<std::mutex> lock(s.m);
        if (s.cap) {
            uint64_t i = (h >> 8) & (s.cap - 1);
            while (s.e[i].key) {
                if (s.e[i].key == key) {
                    // Same depth, another parent: keep the smaller one, so the result doesn't depend on timing.
                    if (same_level && (s.e[i].value >> 123) == (value >> 123) && value < s.e[i].value) s.e[i].value = value;
                    return false;
                }
                i = (i + 1) & (s.cap - 1);
            }
        }
        if ((s.n + 1) * 10 > s.cap * 7) {
            uint64_t cap = s.cap ? s.cap * 2 : 64;
            Entry* e = (Entry*)calloc(cap, sizeof(Entry));
            if (!e) { fprintf(stderr, "out of memory\n"); exit(3); }
            for (uint64_t j = 0; j < s.cap; ++j)
                if (s.e[j].key) place(e, cap, s.e[j].key, s.e[j].value, hash128(s.e[j].key));
            free(s.e);
            bytes += (cap - s.cap) * sizeof(Entry);
            s.e = e; s.cap = cap;
        }
        place(s.e, s.cap, key, value, h);
        ++s.n; ++count;
        return true;
    }
    bool find(u128 key, u128& value) {
        uint64_t h = hash128(key);
        Shard& s = shards[h >> (64 - BITS)];
        if (!s.cap) return false;
        uint64_t i = (h >> 8) & (s.cap - 1);
        while (s.e[i].key) {
            if (s.e[i].key == key) { value = s.e[i].value; return true; }
            i = (i + 1) & (s.cap - 1);
        }
        return false;
    }
};

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

// One lost exit: (covering layer, lower layer) -> its exits, and the first stack that showed it.
struct Pair {
    std::vector<int> exits;
    int depth = 1 << 30, landing = -1;
    u128 node = 0, stack = 0;
    void offer(int d, u128 n, u128 st, int land) {
        if (d < depth || (d == depth && (st < stack || (st == stack && n < node)))) { depth = d; node = n; stack = st; landing = land; }
    }
};
typedef std::unordered_map<uint32_t, Pair> Pairs;

static void lost(const uint8_t* s, int n, const Scratch& a, Pairs& out, int depth, u128 node, int landing) {
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
            if (!stack) stack = pack(s, n, -1, 0);
            Pair& p = out[(uint32_t)who << 16 | (uint32_t)lower];
            if (std::find(p.exits.begin(), p.exits.end(), x.id) == p.exits.end()) p.exits.push_back(x.id);
            p.offer(depth, node, stack, landing);
        }
    }
}

struct Worker {
    Scratch a, b;
    std::vector<u128> next;
    Pairs pairs;
    uint64_t landings = 0;
    int longest = 0;
};

static Table table, stacks;

// The nodes one node leads to. `emit(child, move, kind)`; kind: 0 step, 1 settle, 2 arrival.
template <class F>
static void successors(const uint8_t* s, int n, int head, int used, const Scratch& a, F emit) {
    uint8_t t[MAXL];
    for (int i = 0; i < n; ++i) {
        int layer = s[i];
        for (const Move& mv : moves[layer]) {
            if (a.answer(mv.control) != layer) continue;
            int m = apply(s, n, mv, t);
            if (m < 0 || (MAX_LAYERS > 0 && m - 1 > MAX_LAYERS)) continue;
            if (MODE == 0) { emit(pack(t, m, -1, 0), mv, mv.adding ? 0 : 1, m); continue; }
            if (!mv.adding) { emit(pack(t, m, head, used), mv, 1, m); continue; }
            bool changed = m != n || memcmp(s, t, n) != 0;
            if (used < EXTRAS && changed) emit(pack(t, m, head, used + 1), mv, 2, m);
            if (layer == head)
                for (const auto& op : mv.ops)
                    if (op.first && memchr(t, op.second, m)) emit(pack(t, m, op.second, used), mv, 0, m);
        }
    }
}

static void process(u128 node, int depth, Worker& w) {
    uint8_t s[MAXL], t[MAXL];
    int head, used, n = unpack(node, s, head, used);
    answers(s, n, w.a);
    lost(s, n, w.a, w.pairs, depth, node, -1);
    if (MODE == 1) stacks.insert(node & STACK_MASK, 1, false);
    if (LANDINGS) {
        for (int i = 0; i < n; ++i)
            for (const Move& mv : moves[s[i]]) {
                if (!mv.adding || w.a.answer(mv.control) != s[i]) continue;
                int m = apply(s, n, mv, t);
                if (m < 0 || (m == n && memcmp(s, t, n) == 0)) continue;
                ++w.landings;
                answers(t, m, w.b);
                lost(t, m, w.b, w.pairs, depth + 1, node, mv.id);
            }
    }
    u128 value = (node & KEY_MASK) | ((u128)((depth + 1) & 31) << 123);
    successors(s, n, head, used, w.a, [&](u128 child, const Move&, int, int m) {
        if (table.insert(child, value, true)) {
            w.next.push_back(child);
            if (m - 1 > w.longest) w.longest = m - 1;
        }
    });
}

static int read_int() { int v; if (scanf("%d", &v) != 1) { fprintf(stderr, "bad input\n"); exit(2); } return v; }

int main() {
    NL = read_int(); BASE = read_int(); NC = read_int(); NS = read_int(); MAX_LAYERS = read_int();
    MODE = read_int(); EXTRAS = read_int(); LANDINGS = read_int(); THREADS = read_int(); MEMORY_MB = read_int();
    if (NL > 127 || EXTRAS > 15) { fprintf(stderr, "too many layers or extra presses\n"); return 2; }
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

    auto began = std::chrono::steady_clock::now();
    uint8_t root[1] = {(uint8_t)BASE};
    u128 start = pack(root, 1, MODE == 1 ? BASE : -1, 0);
    table.insert(start, 0, false);
    std::vector<u128> frontier{start};
    std::vector<Worker> workers(THREADS);
    std::vector<uint64_t> levels;
    Pairs pairs;
    int depth = 0, longest = 0;
    uint64_t landings = 0;
    bool settled = true;
    const char* stopped = "";
    while (!frontier.empty()) {
        std::atomic<size_t> cursor(0);
        std::vector<std::thread> pool;
        for (int i = 0; i < THREADS; ++i)
            pool.emplace_back([&, i]() {
                Worker& w = workers[i];
                for (;;) {
                    size_t from = cursor.fetch_add(1024);
                    if (from >= frontier.size()) break;
                    size_t to = std::min(frontier.size(), from + 1024);
                    for (size_t j = from; j < to; ++j) process(frontier[j], depth, w);
                }
            });
        for (auto& th : pool) th.join();
        levels.push_back(frontier.size());
        std::vector<u128> next;
        for (Worker& w : workers) {
            next.insert(next.end(), w.next.begin(), w.next.end());
            std::vector<u128>().swap(w.next);
            for (auto& item : w.pairs) {
                Pair& p = pairs[item.first];
                for (int id : item.second.exits)
                    if (std::find(p.exits.begin(), p.exits.end(), id) == p.exits.end()) p.exits.push_back(id);
                p.offer(item.second.depth, item.second.node, item.second.stack, item.second.landing);
            }
            w.pairs.clear();
            landings += w.landings; w.landings = 0;
            longest = std::max(longest, w.longest);
        }
        fprintf(stderr, "walk: %d presses, %llu stacks\n", depth, (unsigned long long)table.count.load());
        if (overflow) { settled = false; stopped = "a stack passed 16 layers"; break; }
        uint64_t used_mb = (table.bytes + stacks.bytes + next.size() * sizeof(u128)) >> 20;
        if (MEMORY_MB > 0 && (long)used_mb > MEMORY_MB && !next.empty()) { settled = false; stopped = "the memory limit was reached"; break; }
        frontier.swap(next);
        if (!frontier.empty()) ++depth;
    }
    double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - began).count();

    printf("{\"settled\": %s, \"stopped\": \"%s\", \"nodes\": %llu, \"stacks\": %llu, \"presses\": %d, \"longest\": %d, "
           "\"landings\": %llu, \"seconds\": %.3f, \"memory_mb\": %llu, \"threads\": %d, \"levels\": [",
           settled ? "true" : "false", stopped, (unsigned long long)table.count.load(),
           (unsigned long long)(MODE == 1 ? stacks.count.load() : table.count.load()), depth, longest,
           (unsigned long long)landings, seconds, (unsigned long long)((table.bytes + stacks.bytes) >> 20), THREADS);
    for (size_t i = 0; i < levels.size(); ++i) printf("%s%llu", i ? ", " : "", (unsigned long long)levels[i]);
    printf("], \"pairs\": [");

    Scratch a;
    std::vector<uint32_t> keys;
    for (auto& item : pairs) keys.push_back(item.first);
    std::sort(keys.begin(), keys.end());
    bool first = true;
    for (uint32_t key : keys) {
        Pair& p = pairs[key];
        std::sort(p.exits.begin(), p.exits.end());
        // The path: follow each node back to the start, then name the binding of every step.
        std::vector<u128> chain{p.node};
        u128 value;
        while (table.find(chain.back(), value) && (value & KEY_MASK)) chain.push_back(value & KEY_MASK);
        std::reverse(chain.begin(), chain.end());
        std::vector<std::pair<int, int>> path;
        uint8_t s[MAXL];
        for (size_t i = 0; i + 1 < chain.size(); ++i) {
            int head, used, n = unpack(chain[i], s, head, used);
            answers(s, n, a);
            int id = -1, kind = 0;
            successors(s, n, head, used, a, [&](u128 child, const Move& mv, int k, int) {
                if (id < 0 && child == chain[i + 1]) { id = mv.id; kind = k; }
            });
            path.push_back({id, kind});
        }
        if (p.landing >= 0) path.push_back({p.landing, 3});
        printf("%s{\"who\": %u, \"lower\": %u, \"exits\": [", first ? "" : ", ", key >> 16, key & 0xffff);
        first = false;
        for (size_t i = 0; i < p.exits.size(); ++i) printf("%s%d", i ? ", " : "", p.exits[i]);
        printf("], \"stack\": [");
        int head, used, n = unpack(p.stack, s, head, used);
        for (int i = 0; i < n; ++i) printf("%s%d", i ? ", " : "", s[i]);
        printf("], \"path\": [");
        for (size_t i = 0; i < path.size(); ++i) printf("%s[%d, %d]", i ? ", " : "", path[i].first, path[i].second);
        printf("]}");
    }
    printf("]}\n");
    return 0;
}
