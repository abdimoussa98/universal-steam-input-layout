// Shared by stack_search.cpp and stack_search_disk.cpp: the model file loader,
// layer ops and the realistic (held-button) rules, mirroring steam_layout/held_model.py.
#pragma once
#include <algorithm>
#include <atomic>
#include <csignal>
#include <unordered_map>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

using u8 = uint8_t;
using u32 = uint32_t;
using u64 = uint64_t;

static const int MAXLEN = 96;
static const int MAXREC = MAXLEN + 1 + 9;  // len + stack + held(8) + missed(1)
static const u32 NONE = 0xFFFFFFFFu;
static std::atomic<bool> interrupted(false);
static void on_signal(int) { interrupted = true; }

struct Bits {  // input set, up to 128 inputs
  u64 w[2] = {0, 0};
  void set(int i) { w[i >> 6] |= 1ull << (i & 63); }
  bool has(int i) const { return (w[i >> 6] >> (i & 63)) & 1; }
  void clr(int i) { w[i >> 6] &= ~(1ull << (i & 63)); }
  void orr(const Bits &o) { w[0] |= o.w[0]; w[1] |= o.w[1]; }
};

struct Entry {
  char kind = 'P';
  bool delay = false, repeat = false, interr = true;
  int cond = -1;
  std::vector<std::pair<char, int>> ops;
  std::vector<int> shift;
};

struct Cond { int type = 0; std::vector<u64> specs; };  // type 0 unknown, 1 any, 2 all

struct Control {
  bool owner = false;
  char thumb = '-';
  int thumbsrc = -1, input = -1, source = -1, dir = -1;
  std::string family, kind, name;
  std::vector<std::pair<char, int>> unhold;  // releasing it removes the layers its hold_layer holds
};

struct Model {
  int L = 0, M = 0;
  std::vector<std::string> layer, input_name;
  std::vector<Bits> binds, blocks, either;
  std::vector<std::vector<std::vector<u32>>> fires;    // blind: [layer][input] -> events
  std::vector<std::vector<std::pair<char, int>>> ops;  // blind: [event]
  std::vector<std::pair<int, u32>> holds;              // blind: (layer, event)
  // held model
  bool held = false;
  std::vector<Control> ctl;
  int always = -1;
  std::vector<Cond> conds;
  std::vector<std::vector<std::vector<Entry>>> ent;      // [layer][control + 1] (0 = Always On)
  std::vector<std::vector<std::vector<Entry>>> sent;     // [shift group][control]
  std::vector<int> src_touch, src_edge;
  std::vector<std::string> src_family;
};

static Entry read_entry(std::istringstream &s) {
  Entry e;
  std::string kind;
  int d, r, i, n;
  s >> kind >> d >> r >> i >> e.cond >> n;
  e.kind = kind[0]; e.delay = d; e.repeat = r; e.interr = i;
  for (int k = 0; k < n; k++) { std::string op; int t; s >> op >> t; e.ops.push_back({op[0], t}); }
  int ns = 0;
  s >> ns;
  for (int k = 0; k < ns; k++) { int g; s >> g; e.shift.push_back(g); }
  return e;
}

static Model load(const char *path) {
  Model m;
  std::ifstream in(path);
  if (!in) { std::cerr << "cannot read " << path << "\n"; exit(2); }
  std::string line, word;
  std::map<std::string, int> sources;
  while (std::getline(in, line)) {
    std::istringstream s(line);
    s >> word;
    if (word == "layers") { s >> m.L; m.layer.resize(m.L); m.binds.resize(m.L); m.blocks.resize(m.L); }
    else if (word == "layer") { int i; s >> i; std::string rest; std::getline(s, rest); m.layer[i] = rest.substr(1); }
    else if (word == "inputs") {
      s >> m.M; m.input_name.resize(m.M);
      if (m.M > 128) { std::cerr << "more than 128 inputs\n"; exit(2); }
      m.fires.assign(m.L, std::vector<std::vector<u32>>(m.M));
    }
    else if (word == "input") { int i; s >> i; std::string rest; std::getline(s, rest); m.input_name[i] = rest.substr(1); }
    else if (word == "bind") { int l, j; s >> l >> j; m.binds[l].set(j); }
    else if (word == "block") { int l, j; s >> l >> j; m.blocks[l].set(j); }
    else if (word == "events") { int n; s >> n; m.ops.resize(n); }
    else if (word == "event") {
      int id, l, j, n; s >> id >> l >> j >> n;
      for (int k = 0; k < n; k++) { std::string op; int t; s >> op >> t; m.ops[id].push_back({op[0], t}); }
      if (j >= 0) m.fires[l][j].push_back(id); else m.holds.push_back({l, (u32)id});
    }
    else if (word == "controls") {
      int n; s >> n; m.ctl.resize(n);
      if (n > 64) { std::cerr << "more than 64 controls\n"; exit(2); }
      m.ent.assign(m.L, std::vector<std::vector<Entry>>(n + 1));
    }
    else if (word == "control") {
      int c, owner, dir; std::string thumb, family, kind, source, name;
      s >> c;
      Control &k = m.ctl[c];
      s >> owner >> thumb >> k.thumbsrc >> k.input >> family >> kind >> dir >> source >> name;
      k.owner = owner; k.thumb = thumb[0]; k.family = family; k.kind = kind; k.dir = dir; k.name = source + "/" + name;
      if (!sources.count(source)) { int id = (int)sources.size(); sources[source] = id; m.src_touch.push_back(-1); m.src_edge.push_back(-1); m.src_family.push_back(family); }
      k.source = sources[source];
      if (kind == "touch") m.src_touch[k.source] = c;
      if (kind == "edge") m.src_edge[k.source] = c;
    }
    else if (word == "hold") {
      int c, n; s >> c >> n;
      for (int k = 0; k < n; k++) { int t; s >> t; m.ctl[c].unhold.push_back({'r', t}); }
    }
    else if (word == "always") s >> m.always;
    else if (word == "conds") { int n; s >> n; m.conds.resize(n); }
    else if (word == "cond") {
      int n; std::string type; s >> n >> type;
      Cond &c = m.conds[n];
      if (type == "unknown") c.type = 0;
      else {
        c.type = type == "any" ? 1 : 2;
        int k; s >> k;
        for (int i = 0; i < k; i++) { int len; s >> len; u64 mask = 0; for (int q = 0; q < len; q++) { int id; s >> id; mask |= 1ull << id; } c.specs.push_back(mask); }
      }
    }
    else if (word == "entry") { int l, c; s >> l >> c; m.ent[l][c + 1].push_back(read_entry(s)); }
    else if (word == "shifts") { int g; s >> g; m.sent.assign(g, std::vector<std::vector<Entry>>(m.ctl.size())); }
    else if (word == "sentry") { int g, c; s >> g >> c; m.sent[g][c].push_back(read_entry(s)); }
  }
  m.either.resize(m.L);
  for (int l = 0; l < m.L; l++) { m.either[l] = m.binds[l]; m.either[l].orr(m.blocks[l]); }
  return m;
}

static inline u64 hash_bytes(const u8 *p, int n) {
  u64 h = 0x9E3779B97F4A7C15ull ^ (u64)n;
  for (int i = 0; i < n; i++) { h ^= p[i]; h *= 0x100000001B3ull; h ^= h >> 29; }
  h ^= h >> 32; h *= 0xD6E8FEB86659FD93ull; h ^= h >> 32;
  return h;
}

// A record is [n][stack ids...] plus, in held mode, [held u64][missed u8].
static inline int rec_size(const u8 *r, bool held) { return 1 + r[0] + (held ? 9 : 0); }

// Apply layer ops to a stack in place (len updated). Re-adding a present layer does nothing; Base stays.
static void apply_ops(const std::vector<std::pair<char, int>> &ops, u8 *st, int &len) {
  for (auto &op : ops) {
    int t = op.second, at = -1;
    for (int i = 0; i < len; i++) if (st[i] == t) { at = i; break; }
    if (op.first == 'r') {
      if (at > 0) { memmove(st + at, st + at + 1, len - at - 1); len--; }
    } else if (at < 0) {
      if (len >= MAXLEN) { std::cerr << "stack longer than " << MAXLEN << "\n"; exit(3); }
      st[len++] = (u8)t;
    }
  }
}

// ---- held model (mirrors steam_layout/held_model.py) --------------------------
enum { PRESS, LATER, RELEASE, LOST, TAP, TAP_LOST, TAP_HELD, TAP_HELD_LOST, TIMER, SHIFT_TAP };
enum Phase { P_PRESS, P_LATER, P_RELEASE, P_ALWAYS };

struct Stack { u8 s[MAXLEN]; int n; bool operator==(const Stack &o) const { return n == o.n && memcmp(s, o.s, n) == 0; } };

struct Held {
  const Model &m;
  const bool lost_on;  // --missed: also try releases while the Steam menu is open
  // --top K: keep only the top K layers in order (TopModel in held_model.py). A stack is then
  // encoded as [deep layer ids, ascending (Base first)] SEP [top layer ids, bottom first].
  int topk = 0;
  static const u8 SEP = 255;
  Held(const Model &model, bool missed_releases, int top = 0) : m(model), lost_on(missed_releases), topk(top) {}

  static int sep_of(const Stack &st) { int k = 0; while (st.s[k] != SEP) k++; return k; }

  bool satisfied(int cond, u64 held, bool blocking) const {
    if (cond < 0) return true;
    const Cond &c = m.conds[cond];
    if (c.type == 0) return !blocking;
    bool all = true, any = false;
    for (u64 spec : c.specs) { bool hit = (spec & held) != 0; all = all && hit; any = any || hit; }
    return c.type == 2 ? all : any;
  }

  bool valid(u64 held) const {
    int thumb[2] = {-1, -1};
    for (u64 b = held; b; b &= b - 1) {
      const Control &k = m.ctl[__builtin_ctzll(b)];
      if (k.thumb == 'L' || k.thumb == 'R') {
        int &t = thumb[k.thumb == 'R'];
        if (t >= 0 && t != k.thumbsrc) return false;
        t = k.thumbsrc;
      }
    }
    for (u64 b = held; b; b &= b - 1) {
      int c = __builtin_ctzll(b);
      const Control &k = m.ctl[c];
      if (k.family == "stick") {
        int dirs[4], nd = 0;
        bool other = false;
        for (u64 b2 = held; b2; b2 &= b2 - 1) {
          const Control &k2 = m.ctl[__builtin_ctzll(b2)];
          if (k2.source != k.source) continue;
          if (k2.dir >= 0) { if (nd < 4) dirs[nd] = k2.dir; nd++; }
          if (k2.kind != "touch") other = true;
        }
        if (nd > 2) return false;
        if (nd == 2) { int a = std::min(dirs[0], dirs[1]), z = std::max(dirs[0], dirs[1]); if (z - a != 1 && z - a != 3) return false; }
        int touch = m.src_touch[k.source];
        if (other && touch >= 0 && m.ctl[touch].owner && !((held >> touch) & 1)) return false;
      }
      if (k.family == "trigger" && k.kind == "click") {
        int edge = m.src_edge[k.source];
        if (edge >= 0 && m.ctl[edge].owner && !((held >> edge) & 1)) return false;
      }
    }
    return true;
  }

  // Entries of the topmost layer binding `key` (control, or -1 for Always On); null if none or blocked.
  const std::vector<Entry> *owner(const Stack &st, int key) const {
    int j = key < 0 ? m.always : m.ctl[key].input;
    if (j < 0) return nullptr;
    for (int k = st.n - 1; k >= 0; k--) {
      int l = st.s[k];
      if (m.blocks[l].has(j)) return nullptr;
      if (m.binds[l].has(j)) return &m.ent[l][key + 1];
    }
    return nullptr;
  }

  // Every entry list that can be the topmost binding of `key` (null: nothing fires or it is blocked).
  // Exact stacks have one; with --top, an input falling into the deep set can come from any deep
  // layer binding or blocking it (Base only when none does).
  void owners(const Stack &st, int key, std::vector<const std::vector<Entry> *> &out) const {
    out.clear();
    if (!topk) { out.push_back(owner(st, key)); return; }
    int j = key < 0 ? m.always : m.ctl[key].input;
    if (j < 0) { out.push_back(nullptr); return; }
    int sep = sep_of(st);
    for (int k = st.n - 1; k > sep; k--) {
      int l = st.s[k];
      if (m.blocks[l].has(j)) { out.push_back(nullptr); return; }
      if (m.binds[l].has(j)) { out.push_back(&m.ent[l][key + 1]); return; }
    }
    bool none_added = false;
    for (int k = 0; k < sep; k++) {
      int l = st.s[k];
      if (l == 0) continue;
      if (m.blocks[l].has(j)) { if (!none_added) { out.push_back(nullptr); none_added = true; } }
      else if (m.binds[l].has(j)) out.push_back(&m.ent[l][key + 1]);
    }
    if (!out.empty()) return;
    out.push_back(m.binds[0].has(j) && !m.blocks[0].has(j) ? &m.ent[0][key + 1] : nullptr);
  }

  // Apply layer ops to a stack (exact, or top/deep encoded with --top).
  void apply(const std::vector<std::pair<char, int>> &ops, Stack &r) const {
    if (!topk) { apply_ops(ops, r.s, r.n); return; }
    Bits deep;
    u8 top[MAXLEN];
    int nt = 0, sep = sep_of(r);
    for (int k = 0; k < sep; k++) deep.set(r.s[k]);
    for (int k = sep + 1; k < r.n; k++) top[nt++] = r.s[k];
    for (auto &op : ops) {
      int t = op.second, at = -1;
      for (int i = 0; i < nt; i++) if (top[i] == t) { at = i; break; }
      if (op.first == 'r') {
        if (at >= 0) { memmove(top + at, top + at + 1, nt - at - 1); nt--; }
        else if (t != 0) deep.clr(t);
      } else if (at < 0 && !deep.has(t)) {
        top[nt++] = (u8)t;
        if (nt > topk) { deep.set(top[0]); memmove(top, top + 1, nt - 1); nt--; }
      }
    }
    r.n = 0;
    for (int l = 0; l < 128; l++) if (deep.has(l)) r.s[r.n++] = (u8)l;
    r.s[r.n++] = SEP;
    memcpy(r.s + r.n, top, nt);
    r.n += nt;
  }

  void selected(const std::vector<Entry> &ents, u64 held, Phase phase, std::vector<const Entry *> &out) const {
    bool blocked = false;
    for (auto &e : ents) if (e.kind == 'C' && satisfied(e.cond, held, true)) blocked = true;
    for (auto &e : ents) {
      bool ok;
      if (phase == P_RELEASE) ok = e.kind == 'R';
      else if (e.kind == 'R') ok = false;
      else if (e.kind == 'C' && !satisfied(e.cond, held, false)) ok = false;
      else if (e.kind == 'P' && e.interr && blocked) ok = false;
      else if (phase == P_PRESS) ok = !e.delay;
      else if (phase == P_ALWAYS) ok = true;
      else ok = e.delay || e.repeat;
      if (ok) out.push_back(&e);
    }
  }

  // Stacks after firing; uses `ents` if given, else the topmost binding of `key`.
  void fire(const Stack &st, u64 held, int key, Phase phase, const std::vector<Entry> *ents, std::vector<Stack> &out) const {
    out.clear();
    std::vector<const std::vector<Entry> *> choices;
    if (ents) choices.push_back(ents); else owners(st, key, choices);
    const std::vector<std::pair<char, int>> *unhold = phase == P_RELEASE && key >= 0 ? &m.ctl[key].unhold : nullptr;
    for (auto *choice : choices) {
      std::vector<const Entry *> chosen, withops;
      if (choice) selected(*choice, held, phase, chosen);
      for (auto *e : chosen) if (!e->ops.empty()) withops.push_back(e);
      std::vector<int> order(withops.size());
      for (size_t i = 0; i < order.size(); i++) order[i] = (int)i;
      do {
        Stack r = st;
        for (int i : order) apply(withops[i]->ops, r);
        if (unhold) apply(*unhold, r);
        if (std::find(out.begin(), out.end(), r) == out.end()) out.push_back(r);
        if (withops.size() > 3) break;
      } while (std::next_permutation(order.begin(), order.end()));
    }
  }

  template <class Emit>
  void tap(const Stack &st, u64 held, bool missed, int c, u64 more, const std::vector<Entry> *ents, int kind, Emit &emit) const {
    std::vector<Stack> s1s, mids, s3s;
    fire(st, more, c, P_PRESS, ents, s1s);
    for (auto &s1 : s1s) for (int long_ = 0; long_ < 2; long_++) {
      if (long_) fire(s1, more, c, P_LATER, ents, mids); else { mids.clear(); mids.push_back(s1); }
      for (auto &s2 : mids) {
        int code = kind == TAP ? (long_ ? TAP_HELD : TAP) : kind;
        fire(s2, more, c, P_RELEASE, ents, s3s);
        for (auto &s3 : s3s) emit(s3, held, missed, c, code);
        int lost = kind == TAP ? (long_ ? TAP_HELD_LOST : TAP_LOST) : kind;
        if (lost_on) emit(s2, held, true, c, lost);
      }
    }
  }

  template <class Emit>
  void successors(const Stack &st, u64 held, bool missed, Emit &emit) const {
    std::vector<Stack> outs;
    int C = (int)m.ctl.size();
    for (int c = 0; c < C; c++) {
      u64 bit = 1ull << c;
      if (m.ctl[c].owner) {
        if (held & bit) {
          fire(st, held, c, P_LATER, nullptr, outs);
          for (auto &s : outs) emit(s, held, missed, c, LATER);
          u64 rest = held & ~bit;
          if (valid(rest)) {
            fire(st, held, c, P_RELEASE, nullptr, outs);
            for (auto &s : outs) emit(s, rest, missed, c, RELEASE);
            if (lost_on) emit(st, rest, true, c, LOST);
          }
        } else if (valid(held | bit)) {
          fire(st, held | bit, c, P_PRESS, nullptr, outs);
          for (auto &s : outs) emit(s, held | bit, missed, c, PRESS);
        }
      } else if (valid(held | bit)) {
        tap(st, held, missed, c, held | bit, nullptr, TAP, emit);
      }
    }
    // mode shifts fired by held buttons' current bindings
    std::vector<int> groups;
    std::vector<const std::vector<Entry> *> choices;
    for (u64 b = held; b; b &= b - 1) {
      int c = __builtin_ctzll(b);
      owners(st, c, choices);
      for (auto *ents : choices) {
        if (!ents) continue;
        std::vector<const Entry *> chosen;
        selected(*ents, held, P_PRESS, chosen);
        for (auto *e : chosen) for (int g : e->shift) if (std::find(groups.begin(), groups.end(), g) == groups.end()) groups.push_back(g);
      }
    }
    for (int g : groups) for (int c = 0; c < C; c++) {
      if (m.sent[g][c].empty()) continue;
      u64 bit = 1ull << c;
      if (!(held & bit) && valid(held | bit)) tap(st, held, missed, c, held | bit, &m.sent[g][c], SHIFT_TAP, emit);
    }
    fire(st, held, -1, P_ALWAYS, nullptr, outs);
    for (auto &s : outs) emit(s, held, missed, -1, TIMER);
  }
};
// ---- input owners of a stack (mirrors steam_layout.stacks.definer) -----------
// Per input: the id of the topmost layer binding it, 128 + the id of the topmost
// layer blocking it (a disabled source), or 255 when no layer does.
static const u8 OWNER_NONE = 255, OWNER_BLOCKED = 128;

static void owners_of(const Model &m, const u8 *s, int n, u8 *out) {
  for (int j = 0; j < m.M; j++) {
    u8 v = OWNER_NONE;
    for (int k = n - 1; k >= 0; k--) {
      int l = s[k];
      if (m.blocks[l].has(j)) { v = (u8)(OWNER_BLOCKED + l); break; }
      if (m.binds[l].has(j)) { v = (u8)l; break; }
    }
    out[j] = v;
  }
}

// Distinct owner vectors ("profiles"): many stacks share one.
struct Profiles {
  std::unordered_map<std::string, u32> ids;
  std::vector<std::string> rows;
  u32 of(const Model &m, const u8 *s, int n) {
    std::string key(m.M, '\0');
    owners_of(m, s, n, (u8 *)&key[0]);
    auto it = ids.find(key);
    if (it != ids.end()) return it->second;
    u32 id = (u32)rows.size();
    ids.emplace(key, id);
    rows.push_back(key);
    return id;
  }
  void write(const std::string &path) const {  // id \t owner code per input
    std::ofstream o(path);
    for (size_t i = 0; i < rows.size(); i++) {
      o << i << "\t";
      for (size_t j = 0; j < rows[i].size(); j++) o << (j ? " " : "") << (int)(u8)rows[i][j];
      o << "\n";
    }
  }
};

// stacks.tsv row flags: states with nothing held (no missed release / after one)
static const int IDLE_CLEAN = 1, IDLE_MISSED = 2;
