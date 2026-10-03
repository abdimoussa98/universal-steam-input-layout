// Exhaustive layer-stack search for a Steam Input layout.
//
// Reads a model written by steam_layout (search_model.py, or held_model.py for
// --held) and visits every reachable state from Base, exactly once, until
// nothing new appears. No depth or state cap.
//
//   stack_search MODEL OUTDIR [--held [--missed] [--top K]] [--threads N] [--max-depth D] [--memory-limit GB] [--dump] [--progress SECONDS]
//
// Stops cleanly (and still writes everything) at --max-depth, at --memory-limit,
// or on Ctrl-C / SIGTERM. summary.json records why it stopped and the depth up
// to which the results are exact (every state within that many events is in).
//
// Default mode: states are stacks; every entry of the top layer for an input
// can fire (chords unchecked). --held: the realistic model of held_model.py:
// states are (stack, held buttons, missed-release flag); presses, holds,
// releases, taps and Always On timers follow real buttons. --missed adds
// releases while the Steam menu is open (off by default: cleanup covers them).
//
// Each level is processed in batches. Phase A (parallel, read-only) expands a
// batch into candidate states not yet known; phase B (parallel, one thread per
// shard) inserts them. Every state keeps its parent and the event that first
// reached it, so any fact can be explained as a button sequence.
//
// OUTDIR receives summary.json, indexes.json (under / top / below_top / idle
// facts with witnesses), stacks.tsv (every distinct ordered stack: layer ids,
// fewest events, witness state, reachable without a missed release, state
// count, idle flags, input-owner profile of the stack and of the stack below
// its top), profiles.tsv (owner of every input per profile, see rules.hpp) and
// shard_<s>.stacks/.meta (every state). stack_search_disk.cpp is the
// disk-backed version of --held for searches that don't fit in memory.
#include "rules.hpp"

static const int SHARDS = 64;

struct Shard {
  std::vector<u8> arena;
  std::vector<u64> off, parent;
  std::vector<u32> event;
  std::vector<uint16_t> depth;
  std::vector<u32> slots;
  u64 mask = 0;
  bool held = false;
  Shard() { slots.assign(1 << 12, 0); mask = slots.size() - 1; }
  const u8 *at(u64 local) const { return arena.data() + off[local]; }
  u32 find(const u8 *r, int size, u64 h) const {
    for (u64 i = (h >> 6) & mask;; i = (i + 1) & mask) {
      u32 v = slots[i];
      if (!v) return NONE;
      const u8 *t = at(v - 1);
      if (rec_size(t, held) == size && memcmp(t, r, size) == 0) return v - 1;
    }
  }
  void grow() {
    std::vector<u32> old; old.swap(slots);
    slots.assign(old.size() * 2, 0); mask = slots.size() - 1;
    for (u32 v : old) if (v) {
      const u8 *t = at(v - 1);
      u64 h = hash_bytes(t, rec_size(t, held));
      for (u64 i = (h >> 6) & mask;; i = (i + 1) & mask) if (!slots[i]) { slots[i] = v; break; }
    }
  }
  u32 insert(const u8 *r, int size, u64 h, u64 par, u32 ev, uint16_t d) {
    if ((off.size() + 1) * 2 > slots.size()) grow();
    for (u64 i = (h >> 6) & mask;; i = (i + 1) & mask) {
      u32 v = slots[i];
      if (!v) {
        u32 local = (u32)off.size();
        off.push_back(arena.size());
        arena.insert(arena.end(), r, r + size);
        parent.push_back(par); event.push_back(ev); depth.push_back(d);
        slots[i] = local + 1;
        return local;
      }
      const u8 *t = at(v - 1);
      if (rec_size(t, held) == size && memcmp(t, r, size) == 0) return NONE;
    }
  }
};

static inline u64 gid_of(int shard, u64 local) { return local * SHARDS + shard; }
static inline int shard_of(u64 gid) { return (int)(gid % SHARDS); }
static inline u64 local_of(u64 gid) { return gid / SHARDS; }

struct Candidates {
  std::vector<u8> bytes;
  std::vector<u64> hash, parent;
  std::vector<u32> event, start;
  void clear() { bytes.clear(); hash.clear(); parent.clear(); event.clear(); start.clear(); }
};

int main(int argc, char **argv) {
  const char *usage = "usage: stack_search MODEL OUTDIR [--held [--missed] [--top K]] [--threads N] [--max-depth D] [--memory-limit GB] [--dump] [--progress S]\n";
  if (argc < 3) { std::cerr << usage; return 2; }
  std::string outdir = argv[2];
  int threads = (int)std::thread::hardware_concurrency(), max_depth = -1;
  bool dump = false, held_mode = false, missed_mode = false;
  int top = 0;
  double every = 2.0, memory_limit = 0;
  for (int i = 3; i < argc; i++) {
    std::string a = argv[i];
    bool has_value = i + 1 < argc;
    if (a == "--threads" && has_value) threads = atoi(argv[++i]);
    else if (a == "--max-depth" && has_value) max_depth = atoi(argv[++i]);
    else if (a == "--memory-limit" && has_value) memory_limit = atof(argv[++i]) * 1e9;
    else if (a == "--progress" && has_value) every = atof(argv[++i]);
    else if (a == "--dump") dump = true;
    else if (a == "--held") held_mode = true;
    else if (a == "--missed") missed_mode = true;
    else if (a == "--top" && has_value) top = atoi(argv[++i]);
    else { std::cerr << "unknown or incomplete option: " << a << "\n" << usage; return 2; }
  }
  std::signal(SIGINT, on_signal);
  std::signal(SIGTERM, on_signal);
  Model m = load(argv[1]);
  m.held = held_mode;
  if (held_mode && m.ctl.empty()) { std::cerr << "--held needs a model from HeldModel.write_held\n"; return 2; }
  if (top && !held_mode) { std::cerr << "--top needs --held\n"; return 2; }
  Held rules(m, missed_mode, top);
  std::vector<Shard> shards(SHARDS);
  for (auto &s : shards) s.held = held_mode;
  auto t0 = std::chrono::steady_clock::now();
  auto secs = [&] { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };

  u8 root[MAXREC] = {1, 0};
  int root_size = 2;
  if (top) { root[0] = 2; root[2] = Held::SEP; root_size = 3; }  // deep {Base}, top empty
  if (held_mode) { memset(root + root_size, 0, 9); root_size += 9; }
  u64 h0 = hash_bytes(root, root_size);
  int s0 = (int)(h0 % SHARDS);
  u32 l0 = shards[s0].insert(root, root_size, h0, UINT64_MAX, NONE, 0);
  std::vector<u64> frontier = {gid_of(s0, l0)}, next;
  u64 total = 1, processed = 0;
  int level = 0, exact_depth = 0;
  bool complete = true;
  std::string stopped = "complete";
  const size_t BATCH = 200000;
  double last = 0;
  std::vector<std::vector<Candidates>> cand(threads, std::vector<Candidates>(SHARDS));

  auto memory = [&] {
    u64 b = 0;
    for (auto &s : shards) b += s.arena.capacity() + s.off.capacity() * 8 + s.parent.capacity() * 8 + s.event.capacity() * 4 + s.depth.capacity() * 2 + s.slots.capacity() * 4;
    return b;
  };

  while (!frontier.empty() && stopped == "complete") {
    exact_depth = level;  // every state within `level` events is known
    if (max_depth >= 0 && level >= max_depth) { stopped = "max depth"; break; }
    next.clear();
    for (size_t b0 = 0; b0 < frontier.size(); b0 += BATCH) {
      if (interrupted) { stopped = "interrupted"; break; }
      if (memory_limit > 0 && memory() > memory_limit) { stopped = "memory limit"; break; }
      size_t b1 = std::min(frontier.size(), b0 + BATCH);
      std::vector<std::thread> pool;
      std::atomic<size_t> cursor(b0);
      for (int t = 0; t < threads; t++) pool.emplace_back([&, t] {
        for (auto &c : cand[t]) c.clear();
        u8 rec[MAXREC];
        for (;;) {
          size_t i = cursor.fetch_add(256);
          if (i >= b1) break;
          size_t end = std::min(b1, i + 256);
          for (; i < end; i++) {
            u64 gid = frontier[i];
            const u8 *r = shards[shard_of(gid)].at(local_of(gid));
            int n = r[0];
            const u8 *s = r + 1;
            auto push = [&](const u8 *rr, int size, u32 ev) {
              u64 h = hash_bytes(rr, size);
              int sh2 = (int)(h % SHARDS);
              if (shards[sh2].find(rr, size, h) != NONE) return;
              Candidates &c = cand[t][sh2];
              c.start.push_back((u32)c.bytes.size());
              c.bytes.insert(c.bytes.end(), rr, rr + size);
              c.hash.push_back(h); c.parent.push_back(gid); c.event.push_back(ev);
            };
            if (held_mode) {
              Stack st; st.n = n; memcpy(st.s, s, n);
              u64 held; memcpy(&held, s + n, 8);
              bool missed = s[n + 8];
              auto emit = [&](const Stack &ns, u64 nh, bool nm, int c, int phase) {
                rec[0] = (u8)ns.n; memcpy(rec + 1, ns.s, ns.n); memcpy(rec + 1 + ns.n, &nh, 8); rec[1 + ns.n + 8] = nm;
                push(rec, ns.n + 10, (u32)((c + 1) * 16 + phase));
              };
              rules.successors(st, held, missed, emit);
            } else {
              Bits any;
              for (int k = 0; k < n; k++) any.orr(m.either[s[k]]);
              auto emit = [&](u32 ev) {
                int len = n;
                memcpy(rec + 1, s, n);
                apply_ops(m.ops[ev], rec + 1, len);
                rec[0] = (u8)len;
                push(rec, len + 1, ev);
              };
              for (int w = 0; w < 2; w++) for (u64 bits = any.w[w]; bits; bits &= bits - 1) {
                int j = w * 64 + __builtin_ctzll(bits);
                for (int k = n - 1; k >= 0; k--) {
                  int l = s[k];
                  if (m.blocks[l].has(j)) break;
                  if (m.binds[l].has(j)) { for (u32 ev : m.fires[l][j]) emit(ev); break; }
                }
              }
              for (auto &hl : m.holds) for (int k = 0; k < n; k++) if (s[k] == hl.first) { emit(hl.second); break; }
            }
          }
        }
      });
      for (auto &th : pool) th.join();
      pool.clear();
      std::vector<std::vector<u64>> fresh(SHARDS);
      std::atomic<int> next_shard(0);
      for (int t = 0; t < threads; t++) pool.emplace_back([&] {
        for (;;) {
          int sh = next_shard.fetch_add(1);
          if (sh >= SHARDS) break;
          Shard &S = shards[sh];
          for (int t2 = 0; t2 < threads; t2++) {
            Candidates &c = cand[t2][sh];
            for (size_t k = 0; k < c.hash.size(); k++) {
              const u8 *p = c.bytes.data() + c.start[k];
              u32 local = S.insert(p, rec_size(p, held_mode), c.hash[k], c.parent[k], c.event[k], (uint16_t)(level + 1));
              if (local != NONE) fresh[sh].push_back(gid_of(sh, local));
            }
          }
        }
      });
      for (auto &th : pool) th.join();
      for (auto &f : fresh) { next.insert(next.end(), f.begin(), f.end()); total += f.size(); }
      processed += b1 - b0;
      if (secs() - last >= every) {
        last = secs();
        fprintf(stdout, "[%7.1fs] level %d  batch %zu/%zu  states %llu  processed %llu  rate %.0f/s  memory %.2f GB\n",
                secs(), level + 1, b1, frontier.size(), (unsigned long long)total, (unsigned long long)processed,
                processed / std::max(secs(), 1e-9), memory() / 1e9);
        fflush(stdout);
      }
    }
    if (stopped != "complete") break;
    level++;
    exact_depth = level;
    fprintf(stdout, "[%7.1fs] level %d done: %zu new states, %llu total, memory %.2f GB\n", secs(), level, next.size(),
            (unsigned long long)total, memory() / 1e9);
    fflush(stdout);
    frontier.swap(next);
  }
  complete = stopped == "complete";
  fprintf(stdout, "[%7.1fs] search %s: %llu states, exact through %d events. Writing results...\n", secs(),
          complete ? "COMPLETE" : ("stopped (" + stopped + ")").c_str(), (unsigned long long)total, exact_depth);
  fflush(stdout);

  const int LN = m.L + 1;
  // --top stacks aren't real stacks: the facts below and the profiles are for exact searches only
  const int index_shards = top ? 0 : SHARDS;
  struct Wit { u64 gid = UINT64_MAX; uint16_t d = 0xFFFF; };
  auto better = [](Wit &w, u64 gid, uint16_t d) { if (d < w.d || (d == w.d && gid < w.gid)) { w.gid = gid; w.d = d; } };
  std::vector<std::vector<Wit>> under_t(threads), top_t(threads), below_t(threads), idle_t(threads);
  std::vector<std::thread> pool;
  std::atomic<int> next_shard(0);
  for (int t = 0; t < threads; t++) pool.emplace_back([&, t] {
    auto &U = under_t[t]; U.assign((size_t)m.L * m.L, Wit());
    auto &T = top_t[t]; T.assign((size_t)m.M * LN * LN, Wit());
    auto &B = below_t[t]; B.assign((size_t)m.L * m.M * LN, Wit());
    auto &I = idle_t[t]; I.assign((size_t)2 * m.L, Wit());
    std::vector<int> cur(m.M);
    for (;;) {
      int sh = next_shard.fetch_add(1);
      if (sh >= index_shards) break;
      const Shard &S = shards[sh];
      for (u64 local = 0; local < S.off.size(); local++) {
        const u8 *st = S.at(local);
        int n = st[0];
        const u8 *s = st + 1;
        u64 gid = gid_of(sh, local);
        uint16_t d = S.depth[local];
        for (int i = 1; i < n; i++) for (int k = 1; k < i; k++) better(U[(size_t)s[i] * m.L + s[k]], gid, d);
        std::fill(cur.begin(), cur.end(), m.L);
        for (int p = 0; p < n; p++) {
          int x = s[p];
          if (p > 0) for (int j = 0; j < m.M; j++) better(B[((size_t)x * m.M + j) * LN + cur[j]], gid, d);
          for (int w = 0; w < 2; w++) for (u64 bits = m.either[x].w[w]; bits; bits &= bits - 1) cur[w * 64 + __builtin_ctzll(bits)] = x;
        }
        for (int j = 0; j < m.M; j++) {
          int owner = cur[j];
          better(T[((size_t)j * LN + owner) * LN + m.L], gid, d);
          for (int k = 1; k < n; k++) if (s[k] != owner) better(T[((size_t)j * LN + owner) * LN + s[k]], gid, d);
        }
        if (held_mode) {
          u64 held; memcpy(&held, s + n, 8);
          bool missed = s[n + 8];
          if (!held) for (int k = 1; k < n; k++) better(I[(size_t)missed * m.L + s[k]], gid, d);
        }
      }
    }
  });
  for (auto &th : pool) th.join();
  auto merge = [&](std::vector<std::vector<Wit>> &parts) {
    std::vector<Wit> out = parts[0];
    for (size_t t = 1; t < parts.size(); t++) for (size_t i = 0; i < out.size(); i++)
      if (parts[t][i].gid != UINT64_MAX) better(out[i], parts[t][i].gid, parts[t][i].d);
    return out;
  };
  auto U = merge(under_t), T = merge(top_t), B = merge(below_t), I = merge(idle_t);

  std::string cmd = "mkdir -p '" + outdir + "'";
  if (system(cmd.c_str()) != 0) { std::cerr << "cannot create " << outdir << "\n"; return 2; }
  {
    std::ofstream o(outdir + "/indexes.json");
    o << "{\n\"under\": [";
    bool first = true;
    for (int x = 0; x < m.L; x++) for (int y = 0; y < m.L; y++) if (U[(size_t)x * m.L + y].gid != UINT64_MAX) {
      o << (first ? "" : ",") << "[" << y << "," << x << "," << U[(size_t)x * m.L + y].gid << "]"; first = false; }
    o << "],\n\"top\": [";
    first = true;
    for (int j = 0; j < m.M; j++) for (int a = 0; a < LN; a++) for (int y = 0; y < LN; y++) {
      const Wit &w = T[((size_t)j * LN + a) * LN + y];
      if (w.gid != UINT64_MAX) { o << (first ? "" : ",") << "[" << j << "," << a << "," << y << "," << w.gid << "]"; first = false; }
    }
    o << "],\n\"below_top\": [";
    first = true;
    for (int x = 0; x < m.L; x++) for (int j = 0; j < m.M; j++) for (int a = 0; a < LN; a++) {
      const Wit &w = B[((size_t)x * m.M + j) * LN + a];
      if (w.gid != UINT64_MAX) { o << (first ? "" : ",") << "[" << x << "," << j << "," << a << "," << w.gid << "]"; first = false; }
    }
    o << "],\n\"idle\": [";  // [layer, missed (0/1), witness]: present with nothing held
    first = true;
    for (int mi = 0; mi < 2; mi++) for (int x = 0; x < m.L; x++) {
      const Wit &w = I[(size_t)mi * m.L + x];
      if (w.gid != UINT64_MAX) { o << (first ? "" : ",") << "[" << x << "," << mi << "," << w.gid << "]"; first = false; }
    }
    o << "]\n}\n";
  }
  for (int sh = 0; sh < SHARDS; sh++) {
    const Shard &S = shards[sh];
    std::ofstream st(outdir + "/shard_" + std::to_string(sh) + ".stacks", std::ios::binary);
    st.write((const char *)S.arena.data(), S.arena.size());
    std::ofstream me(outdir + "/shard_" + std::to_string(sh) + ".meta", std::ios::binary);
    for (u64 k = 0; k < S.off.size(); k++) {
      me.write((const char *)&S.off[k], 8); me.write((const char *)&S.parent[k], 8);
      me.write((const char *)&S.event[k], 4); me.write((const char *)&S.depth[k], 2);
    }
  }
  if (dump) {
    std::ofstream o(outdir + "/states.txt");
    for (int sh = 0; sh < SHARDS; sh++) for (u64 k = 0; k < shards[sh].off.size(); k++) {
      const u8 *st = shards[sh].at(k);
      o << gid_of(sh, k);
      for (int i = 0; i < st[0]; i++) o << " " << (int)st[1 + i];
      o << "\n";
    }
  }
  {  // every distinct ordered stack: fewest events, witness, reachable without a missed release, state count
    struct Info { uint16_t depth; u64 witness; bool clean; u64 count; int idle; };
    std::unordered_map<std::string, Info> distinct;
    for (int sh = 0; sh < SHARDS; sh++) {
      const Shard &S = shards[sh];
      for (u64 k = 0; k < S.off.size(); k++) {
        const u8 *r = S.at(k);
        int n = r[0];
        bool missed = held_mode ? r[1 + n + 8] : false;
        u64 held = 0;
        if (held_mode) memcpy(&held, r + 1 + n, 8);
        int idle = held_mode && !held ? (missed ? IDLE_MISSED : IDLE_CLEAN) : 0;
        std::string key((const char *)r + 1, n);
        u64 gid = gid_of(sh, k);
        uint16_t d = S.depth[k];
        auto it = distinct.find(key);
        if (it == distinct.end()) distinct.emplace(key, Info{d, gid, !missed, 1, idle});
        else {
          Info &inf = it->second;
          if (d < inf.depth || (d == inf.depth && gid < inf.witness)) { inf.depth = d; inf.witness = gid; }
          inf.clean = inf.clean || !missed;
          inf.count++;
          inf.idle |= idle;
        }
      }
    }
    // ids \t depth \t witness \t clean \t count \t idle flags \t profile \t below-top profile
    Profiles profiles;
    std::ofstream o(outdir + "/stacks.tsv");
    for (auto &kv : distinct) {
      const u8 *st = (const u8 *)kv.first.data();
      int n = (int)kv.first.size();
      for (int i = 0; i < n; i++) o << (i ? " " : "") << (int)st[i];
      o << "\t" << kv.second.depth << "\t" << kv.second.witness << "\t" << (kv.second.clean ? 1 : 0) << "\t" << kv.second.count
        << "\t" << kv.second.idle;
      if (top) o << "\t-1\t-1\n";
      else o << "\t" << profiles.of(m, st, n) << "\t" << profiles.of(m, st, n - 1) << "\n";
    }
    profiles.write(outdir + "/profiles.tsv");
    fprintf(stdout, "[%7.1fs] %zu distinct stacks\n", secs(), distinct.size());
  }
  {
    std::ofstream o(outdir + "/summary.json");
    o << "{\"states\": " << total << ", \"levels\": " << level << ", \"complete\": " << (complete ? "true" : "false")
      << ", \"stopped\": \"" << stopped << "\", \"exact_depth\": " << exact_depth
      << ", \"held\": " << (held_mode ? "true" : "false") << ", \"missed\": " << (missed_mode ? "true" : "false")
      << ", \"top\": " << top
      << ", \"seconds\": " << secs() << ", \"shards\": " << SHARDS
      << ", \"layers\": " << m.L << ", \"inputs\": " << m.M << "}\n";
  }
  fprintf(stdout, "[%7.1fs] done. %llu states written to %s\n", secs(), (unsigned long long)total, outdir.c_str());
  return 0;
}
