// Disk-backed exhaustive search of the realistic (held-button) model.
//
// Same rules and results as `stack_search --held` (rules.hpp), but only a
// 128-bit fingerprint of each visited state is ever needed in memory, and only
// one slice of those at a time, so the search can go as deep as the disk allows.
//
//   stack_search_disk MODEL OUTDIR [--missed] [--threads N] [--max-depth D]
//                     [--memory GB] [--disk-limit GB] [--progress SECONDS] [--resume]
//
// Breadth first, one level (one more button event) at a time:
//
// - Every state is written once to OUTDIR/levels/level_<d>.rec (records as in
//   rules.hpp) and level_<d>.meta (parent state id u64, record offset u64,
//   event u32): state ids are global and consecutive, level by level, so any
//   state can be traced back to Base as a button sequence.
// - Fingerprints of visited states live in OUTDIR/visited/b_<bucket>.fp, 4096
//   buckets by the fingerprint's top bits, each sorted. A level is computed in
//   G groups of buckets: each group loads its buckets' fingerprints, expands the
//   whole frontier, and keeps only successors in its buckets. G is chosen from
//   --memory (default 12 GB: visited fingerprints plus new states; buffers add a
//   fixed few hundred MB) and doubles if a group doesn't fit.
// - A checkpoint is written after every group, so --resume continues an
//   interrupted run (Ctrl-C / SIGTERM stop cleanly) without losing work.
//
// Fingerprints are two independent 64-bit hashes: a false "already visited"
// needs a 128-bit collision (about 1e-20 for 1e9 states).
//
// At the end (complete, --max-depth, --disk-limit or interrupted) it writes
// stacks.tsv and profiles.tsv (see stack_search.cpp and rules.hpp) and
// summary.json ("format": "levels", "level_starts", "exact_depth", ...).
#include "rules.hpp"
#include <filesystem>

namespace fs = std::filesystem;

struct Fp {
  u64 hi, lo;
  bool operator<(const Fp &o) const { return hi < o.hi || (hi == o.hi && lo < o.lo); }
  bool operator==(const Fp &o) const { return hi == o.hi && lo == o.lo; }
};

static inline u64 mix64(u64 x) {
  x ^= x >> 30; x *= 0xBF58476D1CE4E5B9ull;
  x ^= x >> 27; x *= 0x94D049BB133111EBull;
  return x ^ (x >> 31);
}

static Fp fingerprint(const u8 *p, int n) {
  u64 a = 0x243F6A8885A308D3ull ^ (u64)n, b = 0x13198A2E03707344ull + (u64)n * 0x9E3779B97F4A7C15ull;
  int i = 0;
  for (; i + 8 <= n; i += 8) {
    u64 w; memcpy(&w, p + i, 8);
    a = mix64(a ^ w); b = mix64(b + w * 0xD6E8FEB86659FD93ull);
  }
  u64 w = 0; memcpy(&w, p + i, n - i);
  a = mix64(a ^ w ^ ((u64)(n - i) << 56));
  b = mix64(b + (w ^ 0xA0761D6478BD642Full) * 0xE7037ED1A0B428DBull);
  return {mix64(a ^ (b >> 17)), mix64(b ^ (a << 13))};
}

static const int BUCKET_BITS = 12, BUCKETS = 1 << BUCKET_BITS, SUBSETS = 64;
static inline int bucket_of(const Fp &f) { return (int)(f.hi >> (64 - BUCKET_BITS)); }
static inline int subset_of(const Fp &f) { return (int)(f.lo >> 58); }
static const int META = 20;

// ---- files -------------------------------------------------------------------
struct Paths {
  std::string out;
  std::string rec(int d) const { char b[64]; snprintf(b, sizeof b, "/levels/level_%03d.rec", d); return out + b; }
  std::string meta(int d) const { char b[64]; snprintf(b, sizeof b, "/levels/level_%03d.meta", d); return out + b; }
  std::string visited(int k) const { char b[64]; snprintf(b, sizeof b, "/visited/b_%04d.fp", k); return out + b; }
  std::string pending(int k) const { char b[64]; snprintf(b, sizeof b, "/pending/b_%04d.fp", k); return out + b; }
  std::string checkpoint() const { return out + "/checkpoint.txt"; }
};

static std::vector<Fp> read_fps(const std::string &path) {
  std::vector<Fp> v;
  std::ifstream in(path, std::ios::binary);
  if (!in) return v;
  in.seekg(0, std::ios::end);
  v.resize((size_t)in.tellg() / sizeof(Fp));
  in.seekg(0);
  in.read((char *)v.data(), v.size() * sizeof(Fp));
  return v;
}

static void write_atomic(const std::string &path, const void *data, size_t size) {
  std::string tmp = path + ".tmp";
  { std::ofstream o(tmp, std::ios::binary | std::ios::trunc); o.write((const char *)data, size); }
  fs::rename(tmp, path);
}

static void write_meta(std::ofstream &o, u64 parent, u64 offset, u32 event) {
  o.write((const char *)&parent, 8); o.write((const char *)&offset, 8); o.write((const char *)&event, 4);
}

// ---- checkpoint --------------------------------------------------------------
struct Checkpoint {
  int complete = 0;               // levels 0..complete are fully known
  std::vector<u64> starts;        // first state id of each level (plus one past the last known state)
  u64 next_count = 0, next_bytes = 0;  // states / record bytes written so far for level complete+1
  std::string done;               // per bucket '1' once level complete+1 is computed for it
  double growth = 4.0;            // last level's new states per frontier state
  int groups = 1;

  void save(const Paths &p) const {
    std::ostringstream o;
    o << "complete " << complete << "\nstarts";
    for (u64 s : starts) o << " " << s;
    o << "\nnext_count " << next_count << "\nnext_bytes " << next_bytes << "\ngrowth " << growth
      << "\ngroups " << groups << "\ndone " << done << "\n";
    std::string s = o.str();
    write_atomic(p.checkpoint(), s.data(), s.size());
  }
  bool load(const Paths &p) {
    std::ifstream in(p.checkpoint());
    if (!in) return false;
    std::string line, word;
    while (std::getline(in, line)) {
      std::istringstream s(line);
      s >> word;
      if (word == "complete") s >> complete;
      else if (word == "starts") { starts.clear(); u64 v; while (s >> v) starts.push_back(v); }
      else if (word == "next_count") s >> next_count;
      else if (word == "next_bytes") s >> next_bytes;
      else if (word == "growth") s >> growth;
      else if (word == "groups") s >> groups;
      else if (word == "done") s >> done;
    }
    return true;
  }
};

// ---- this level's new states in one group --------------------------------------
struct NewSet {
  std::vector<Fp> fp;
  std::vector<u64> parent, off;
  std::vector<u32> event, slots;
  std::vector<u8> arena;
  u64 mask;
  NewSet() { slots.assign(1 << 10, 0); mask = slots.size() - 1; }
  size_t bytes() const {
    return fp.capacity() * sizeof(Fp) + (parent.capacity() + off.capacity()) * 8 + (event.capacity() + slots.capacity()) * 4 + arena.capacity();
  }
  bool has(const Fp &f) const {
    for (u64 i = f.lo & mask;; i = (i + 1) & mask) {
      u32 v = slots[i];
      if (!v) return false;
      if (fp[v - 1] == f) return true;
    }
  }
  void grow() {
    slots.assign(slots.size() * 2, 0); mask = slots.size() - 1;
    for (u32 k = 0; k < fp.size(); k++)
      for (u64 i = fp[k].lo & mask;; i = (i + 1) & mask) if (!slots[i]) { slots[i] = k + 1; break; }
  }
  void insert(const Fp &f, const u8 *r, int size, u64 par, u32 ev) {
    if ((fp.size() + 1) * 2 > slots.size()) grow();
    for (u64 i = f.lo & mask;; i = (i + 1) & mask) {
      u32 v = slots[i];
      if (!v) {
        fp.push_back(f); parent.push_back(par); event.push_back(ev); off.push_back(arena.size());
        arena.insert(arena.end(), r, r + size);
        slots[i] = (u32)fp.size();
        return;
      }
      if (fp[v - 1] == f) return;
    }
  }
};

struct Cand {
  std::vector<u8> bytes;
  std::vector<Fp> fp;
  std::vector<u64> parent;
  std::vector<u32> event, start;
  void clear() { bytes.clear(); fp.clear(); parent.clear(); event.clear(); start.clear(); }
};

// Visited fingerprints of buckets [b0, b1), loaded for one group.
struct Visited {
  int b0 = 0, b1 = 0;
  std::vector<Fp> v;
  std::vector<u64> start;
  void load(const Paths &p, int from, int to) {
    b0 = from; b1 = to; v.clear(); start.assign(1, 0);
    for (int b = from; b < to; b++) {
      std::vector<Fp> part = read_fps(p.visited(b));
      v.insert(v.end(), part.begin(), part.end());
      start.push_back(v.size());
    }
  }
  bool has(const Fp &f) const {
    int b = bucket_of(f) - b0;
    return std::binary_search(v.begin() + start[b], v.begin() + start[b + 1], f);
  }
  size_t bytes() const { return v.capacity() * sizeof(Fp) + start.capacity() * 8; }
};

// Calls fn(record) for every record of a level file, reading it in chunks.
template <class Fn>
static void for_each_record(const std::string &path, Fn fn) {
  std::ifstream in(path, std::ios::binary);
  std::vector<u8> buf;
  size_t have = 0;
  for (;;) {
    buf.resize(have + (1 << 24));
    in.read((char *)buf.data() + have, 1 << 24);
    size_t size = have + (size_t)in.gcount();
    size_t pos = 0;
    while (pos < size && pos + 1 + buf[pos] + 9 <= size) { fn(buf.data() + pos); pos += 1 + buf[pos] + 9; }
    if (size == have) break;  // nothing more to read
    memmove(buf.data(), buf.data() + pos, size - pos);
    have = size - pos;
  }
}

static u64 dir_bytes(const std::string &dir) {
  u64 total = 0;
  std::error_code ec;
  for (auto &e : fs::recursive_directory_iterator(dir, ec)) if (e.is_regular_file(ec)) total += e.file_size(ec);
  return total;
}

int main(int argc, char **argv) {
  const char *usage = "usage: stack_search_disk MODEL OUTDIR [--missed] [--threads N] [--max-depth D] [--memory GB] "
                      "[--disk-limit GB] [--progress S] [--resume]\n";
  if (argc < 3) { std::cerr << usage; return 2; }
  Paths P{argv[2]};
  int threads = (int)std::thread::hardware_concurrency(), max_depth = -1;
  bool missed_mode = false, resume = false;
  double every = 2.0, budget = 12e9, disk_limit = 0;
  for (int i = 3; i < argc; i++) {
    std::string a = argv[i];
    bool has_value = i + 1 < argc;
    if (a == "--threads" && has_value) threads = atoi(argv[++i]);
    else if (a == "--max-depth" && has_value) max_depth = atoi(argv[++i]);
    else if (a == "--memory" && has_value) budget = atof(argv[++i]) * 1e9;
    else if (a == "--disk-limit" && has_value) disk_limit = atof(argv[++i]) * 1e9;
    else if (a == "--progress" && has_value) every = atof(argv[++i]);
    else if (a == "--missed") missed_mode = true;
    else if (a == "--resume") resume = true;
    else { std::cerr << "unknown or incomplete option: " << a << "\n" << usage; return 2; }
  }
  std::signal(SIGINT, on_signal);
  std::signal(SIGTERM, on_signal);
  Model m = load(argv[1]);
  m.held = true;
  if (m.ctl.empty()) { std::cerr << "needs a model from HeldModel.write_held\n"; return 2; }
  if (m.L >= 128) { std::cerr << "more than 127 layers\n"; return 2; }
  Held rules(m, missed_mode);
  auto t0 = std::chrono::steady_clock::now();
  auto secs = [&] { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };

  Checkpoint cp;
  if (!(resume && cp.load(P))) {
    for (const char *d : {"/levels", "/visited", "/pending"}) { fs::remove_all(P.out + d); fs::create_directories(P.out + d); }
    u8 root[11] = {1, 0};
    memset(root + 2, 0, 9);
    { std::ofstream r(P.rec(0), std::ios::binary); r.write((const char *)root, 11); }
    { std::ofstream me(P.meta(0), std::ios::binary); write_meta(me, UINT64_MAX, 0, NONE); }
    Fp f = fingerprint(root, 11);
    write_atomic(P.visited(bucket_of(f)), &f, sizeof f);
    cp = Checkpoint();
    cp.starts = {0, 1};
    cp.done.assign(BUCKETS, '0');
    cp.save(P);
    fprintf(stdout, "[%7.1fs] started: level 0 is Base with nothing held\n", secs());
  } else {
    fprintf(stdout, "[%7.1fs] resumed: levels 0..%d complete, %llu states of level %d so far\n", secs(), cp.complete,
            (unsigned long long)cp.next_count, cp.complete + 1);
  }
  fflush(stdout);

  std::string stopped = "complete";
  const size_t BATCH = 200000;
  std::vector<std::vector<Cand>> cand(threads, std::vector<Cand>(SUBSETS));
  double last = 0;

  for (;;) {
    int d = cp.complete;
    u64 frontier = cp.starts[d + 1] - cp.starts[d];
    if (frontier == 0) { stopped = "complete"; break; }
    if (max_depth >= 0 && d >= max_depth) { stopped = "max depth"; break; }
    if (interrupted) { stopped = "interrupted"; break; }
    if (disk_limit > 0 && dir_bytes(P.out) > disk_limit) { stopped = "disk limit"; break; }

    // Level d+1 files: drop anything past the checkpoint (a group that didn't finish).
    { std::ofstream touch(P.rec(d + 1), std::ios::binary | std::ios::app); std::ofstream touch2(P.meta(d + 1), std::ios::binary | std::ios::app); }
    fs::resize_file(P.rec(d + 1), cp.next_bytes);
    fs::resize_file(P.meta(d + 1), cp.next_count * META);
    for (int b = 0; b < BUCKETS; b++) if (cp.done[b] == '0') fs::remove(P.pending(b));

    u64 visited_total = cp.starts[d + 1] + cp.next_count;
    double need = visited_total * 16.0 + frontier * cp.growth * 72.0;
    int G = 1;
    while (need / G > budget * 0.6 && G < BUCKETS) G *= 2;
    G = std::max(G, cp.groups);
    bool level_ok = true;

    for (int g = 0; g < G && level_ok; g++) {
      int b0 = g * (BUCKETS / G), b1 = (g + 1) * (BUCKETS / G);
      if (cp.done.compare(b0, b1 - b0, std::string(b1 - b0, '1')) == 0) continue;
      Visited V;
      V.load(P, b0, b1);
      std::vector<NewSet> sets(SUBSETS);
      std::ifstream frec(P.rec(d), std::ios::binary);
      std::vector<u8> buf;
      std::vector<u64> starts_in_buf;
      u64 gid = cp.starts[d], done_states = 0;
      bool overflow = false;
      const size_t CHUNK = 1 << 24;
      std::vector<u8> carry;
      bool eof = false;
      while (!eof) {
        // read the next whole records of the frontier
        buf.swap(carry); carry.clear();
        size_t have = buf.size();
        buf.resize(have + CHUNK);
        frec.read((char *)buf.data() + have, CHUNK);
        size_t got = (size_t)frec.gcount();
        buf.resize(have + got);
        if (got == 0) eof = true;
        starts_in_buf.clear();
        size_t pos = 0;
        while (pos < buf.size() && pos + 1 + buf[pos] + 9 <= buf.size()) { starts_in_buf.push_back(pos); pos += 1 + buf[pos] + 9; }
        carry.assign(buf.begin() + pos, buf.end());
        for (size_t b0s = 0; b0s < starts_in_buf.size(); b0s += BATCH) {
          if (interrupted) break;
          size_t b1s = std::min(starts_in_buf.size(), b0s + BATCH);
          std::vector<std::thread> pool;
          std::atomic<size_t> cursor(b0s);
          for (int t = 0; t < threads; t++) pool.emplace_back([&, t] {
            for (auto &c : cand[t]) c.clear();
            u8 rec[MAXREC];
            for (;;) {
              size_t i = cursor.fetch_add(256);
              if (i >= b1s) break;
              size_t end = std::min(b1s, i + 256);
              for (; i < end; i++) {
                const u8 *r = buf.data() + starts_in_buf[i];
                u64 parent = gid + i;
                Stack st; st.n = r[0]; memcpy(st.s, r + 1, st.n);
                u64 held; memcpy(&held, r + 1 + st.n, 8);
                bool missed = r[1 + st.n + 8];
                auto emit = [&](const Stack &ns, u64 nh, bool nm, int c, int phase) {
                  rec[0] = (u8)ns.n; memcpy(rec + 1, ns.s, ns.n); memcpy(rec + 1 + ns.n, &nh, 8); rec[1 + ns.n + 8] = nm;
                  int size = ns.n + 10;
                  Fp f = fingerprint(rec, size);
                  int b = bucket_of(f);
                  if (b < b0 || b >= b1 || V.has(f)) return;
                  int s = subset_of(f);
                  if (sets[s].has(f)) return;
                  Cand &c2 = cand[t][s];
                  c2.start.push_back((u32)c2.bytes.size());
                  c2.bytes.insert(c2.bytes.end(), rec, rec + size);
                  c2.fp.push_back(f); c2.parent.push_back(parent); c2.event.push_back((u32)((c + 1) * 16 + phase));
                };
                rules.successors(st, held, missed, emit);
              }
            }
          });
          for (auto &th : pool) th.join();
          pool.clear();
          std::atomic<int> next_set(0);
          for (int t = 0; t < threads; t++) pool.emplace_back([&] {
            for (;;) {
              int s = next_set.fetch_add(1);
              if (s >= SUBSETS) break;
              for (int t2 = 0; t2 < threads; t2++) {
                Cand &c = cand[t2][s];
                for (size_t k = 0; k < c.fp.size(); k++) {
                  const u8 *p = c.bytes.data() + c.start[k];
                  sets[s].insert(c.fp[k], p, rec_size(p, true), c.parent[k], c.event[k]);
                }
              }
            }
          });
          for (auto &th : pool) th.join();
          done_states += b1s - b0s;
          // --memory bounds what grows with the search: visited fingerprints and new states
          // (the read buffer and per-batch candidates add a fixed few hundred MB)
          size_t used = V.bytes();
          u64 found = 0;
          for (auto &s : sets) { used += s.bytes(); found += s.fp.size(); }
          if (used > budget) { overflow = true; break; }
          if (secs() - last >= every) {
            last = secs();
            fprintf(stdout, "[%7.1fs] level %d  group %d/%d  frontier %llu/%llu  new %llu  memory %.2f GB\n", secs(), d + 1,
                    g + 1, G, (unsigned long long)done_states, (unsigned long long)frontier, (unsigned long long)found, used / 1e9);
            fflush(stdout);
          }
        }
        gid += starts_in_buf.size();
        if (overflow || interrupted) break;
      }
      if (interrupted) { stopped = "interrupted"; level_ok = false; break; }
      if (overflow) {
        if (G >= BUCKETS) { stopped = "memory limit"; level_ok = false; break; }
        cp.groups = G * 2;
        cp.save(P);
        fprintf(stdout, "[%7.1fs] level %d: group %d/%d doesn't fit in memory; splitting into %d groups\n", secs(), d + 1, g + 1, G, G * 2);
        fflush(stdout);
        G *= 2;
        g = -1;  // restart the group loop; finished buckets are skipped
        continue;
      }
      // write this group's new states, then its fingerprints, then the checkpoint
      std::vector<std::vector<Fp>> per_bucket(b1 - b0);
      {
        std::ofstream orec(P.rec(d + 1), std::ios::binary | std::ios::app), ometa(P.meta(d + 1), std::ios::binary | std::ios::app);
        for (auto &s : sets) for (size_t k = 0; k < s.fp.size(); k++) {
          const u8 *r = s.arena.data() + s.off[k];
          int size = rec_size(r, true);
          orec.write((const char *)r, size);
          write_meta(ometa, s.parent[k], cp.next_bytes, s.event[k]);
          cp.next_bytes += size;
          cp.next_count++;
          per_bucket[bucket_of(s.fp[k]) - b0].push_back(s.fp[k]);
        }
      }
      for (int b = b0; b < b1; b++) {
        auto &v = per_bucket[b - b0];
        if (!v.empty()) { std::sort(v.begin(), v.end()); write_atomic(P.pending(b), v.data(), v.size() * sizeof(Fp)); }
        cp.done[b] = '1';
      }
      cp.save(P);
    }
    if (!level_ok) break;

    // level d+1 is complete: merge its fingerprints into the visited buckets
    std::vector<std::thread> pool;
    std::atomic<int> next_b(0);
    for (int t = 0; t < threads; t++) pool.emplace_back([&] {
      for (;;) {
        int b = next_b.fetch_add(1);
        if (b >= BUCKETS) break;
        if (!fs::exists(P.pending(b))) continue;
        std::vector<Fp> a = read_fps(P.visited(b)), n = read_fps(P.pending(b)), out(a.size() + n.size());
        out.erase(std::set_union(a.begin(), a.end(), n.begin(), n.end(), out.begin()), out.end());
        write_atomic(P.visited(b), out.data(), out.size() * sizeof(Fp));
        fs::remove(P.pending(b));
      }
    });
    for (auto &th : pool) th.join();
    u64 fresh = cp.next_count;
    cp.growth = frontier ? std::max(1.0, (double)fresh / frontier) : 4.0;
    cp.complete = d + 1;
    cp.starts.push_back(cp.starts.back() + fresh);
    cp.next_count = cp.next_bytes = 0;
    cp.done.assign(BUCKETS, '0');
    cp.groups = 1;
    cp.save(P);
    fprintf(stdout, "[%7.1fs] level %d done: %llu new states, %llu total, %d group%s, disk %.2f GB\n", secs(), d + 1,
            (unsigned long long)fresh, (unsigned long long)cp.starts.back(), G, G == 1 ? "" : "s", dir_bytes(P.out) / 1e9);
    fflush(stdout);
  }

  // A stopped level keeps the states of the groups it finished: real states, not yet all of that level.
  int exact_depth = cp.complete;
  bool complete = stopped == "complete";
  int last_level = cp.next_count ? cp.complete + 1 : cp.complete;
  std::vector<u64> starts = cp.starts;
  if (cp.next_count) starts.push_back(starts.back() + cp.next_count);
  u64 total = starts.back();
  fprintf(stdout, "[%7.1fs] search %s: %llu states, exact through %d events. Writing results...\n", secs(),
          complete ? "COMPLETE" : ("stopped (" + stopped + ")").c_str(), (unsigned long long)total, exact_depth);
  fflush(stdout);

  // every distinct ordered stack, in order of first appearance (fewest events)
  struct Info { u64 witness, count; uint16_t depth; u8 clean, idle; u32 off; u8 n; };
  std::vector<Info> info;
  std::vector<u8> arena;
  std::vector<u32> slots(1 << 16, 0);
  u64 mask = slots.size() - 1;
  auto find_or_add = [&](const u8 *s, int n, u64 gid, int depth) -> Info & {
    if ((info.size() + 1) * 2 > slots.size()) {
      slots.assign(slots.size() * 2, 0); mask = slots.size() - 1;
      for (u32 k = 0; k < info.size(); k++)
        for (u64 i = hash_bytes(arena.data() + info[k].off, info[k].n) & mask;; i = (i + 1) & mask) if (!slots[i]) { slots[i] = k + 1; break; }
    }
    for (u64 i = hash_bytes(s, n) & mask;; i = (i + 1) & mask) {
      u32 v = slots[i];
      if (!v) {
        info.push_back(Info{gid, 0, (uint16_t)depth, 0, 0, (u32)arena.size(), (u8)n});
        arena.insert(arena.end(), s, s + n);
        slots[i] = (u32)info.size();
        return info.back();
      }
      Info &e = info[v - 1];
      if (e.n == n && memcmp(arena.data() + e.off, s, n) == 0) return e;
    }
  };
  for (int d = 0; d <= last_level; d++) {
    u64 gid = starts[d];
    for_each_record(P.rec(d), [&](const u8 *r) {
      int n = r[0];
      u64 held; memcpy(&held, r + 1 + n, 8);
      bool missed = r[1 + n + 8];
      Info &e = find_or_add(r + 1, n, gid++, d);
      e.count++;
      e.clean |= !missed;
      if (!held) e.idle |= missed ? IDLE_MISSED : IDLE_CLEAN;
    });
  }
  {
    Profiles profiles;
    std::ofstream o(P.out + "/stacks.tsv");
    for (auto &e : info) {
      const u8 *st = arena.data() + e.off;
      for (int i = 0; i < e.n; i++) o << (i ? " " : "") << (int)st[i];
      o << "\t" << e.depth << "\t" << e.witness << "\t" << (int)e.clean << "\t" << e.count << "\t" << (int)e.idle
        << "\t" << profiles.of(m, st, e.n) << "\t" << profiles.of(m, st, e.n - 1) << "\n";
    }
    profiles.write(P.out + "/profiles.tsv");
    fprintf(stdout, "[%7.1fs] %zu distinct stacks, %zu input profiles\n", secs(), info.size(), profiles.rows.size());
  }
  {
    std::ofstream o(P.out + "/summary.json");
    o << "{\"format\": \"levels\", \"states\": " << total << ", \"levels\": " << cp.complete << ", \"complete\": "
      << (complete ? "true" : "false") << ", \"stopped\": \"" << stopped << "\", \"exact_depth\": " << exact_depth
      << ", \"held\": true, \"missed\": " << (missed_mode ? "true" : "false") << ", \"seconds\": " << secs()
      << ", \"layers\": " << m.L << ", \"inputs\": " << m.M << ", \"level_starts\": [";
    for (size_t i = 0; i < starts.size(); i++) o << (i ? ", " : "") << starts[i];
    o << "]}\n";
  }
  fprintf(stdout, "[%7.1fs] done. %llu states written to %s\n", secs(), (unsigned long long)total, P.out.c_str());
  return 0;
}
