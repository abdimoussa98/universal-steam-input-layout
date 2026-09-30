"""Read the exhaustive stack search's results and answer questions from them.

    python3 -m steam_layout.stackdb run LAYOUT OUTDIR --held            # in memory
    python3 -m steam_layout.stackdb run LAYOUT OUTDIR --disk [--memory 12] [--disk-limit 150] [--resume]
    python3 -m steam_layout.stackdb sqlite LAYOUT OUTDIR                 # (re)build OUTDIR/stacks.sqlite

    db = StackDB("out/default", layout)
    db.values(("Base", "L1: Modifier 0"))        # what every input does in this stack: {(source, name): Value}
    db.moment(gid)                               # one state: stack, held buttons, every input's value, witness
    db.inheritance("L1: Double Tap")             # every input: what the layers below it can give it
    db.inherited_values("L1: Double Tap", "switch", "button_a")
        # for every stored stack with the layer on top, the layer below it that binds the
        # input, with its activators, stacks and a witness
    db.sql("SELECT ...")                         # anything else, on the tables below
    db.witness(gid)                              # the button events that reach a state
    db.idle(missed=False)                        # --held: layers left with nothing held

The engines (tools/stack_search) visit every reachable state once, breadth
first; `summary["exact_depth"]` is the number of button events up to which
the results are complete. For every distinct ordered stack they also record
which layer owns each input (its "profile") for the whole stack and for the
stack below its top layer (what the top layer inherits).

SQLite tables (stacks.sqlite):
    layers(id, title)                  inputs(id, source, name)
    stacks(id, layers JSON, top, size, depth, witness, clean, idle, count, profile, below)
    profile_inputs(profile, input, owner, blocked_by)   -- only inputs some layer binds or blocks
    bindings(layer, input, activators JSON, summary)     -- from the layout JSON
Views:
    stack_values(stack, top, source, name, owner, blocked_by, summary)   -- every input, whole stack
    inherited(stack, top, source, name, owner, blocked_by, summary)      -- every input, below the top
"""
import bisect
import json
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "tools/stack_search"
META = struct.Struct("<QQIH")        # in-memory engine: offset, parent, event, depth
LEVEL_META = struct.Struct("<QQI")   # disk engine: parent, offset, event
NONE_OWNER, BLOCKED, SEP = 255, 128, 255
NO_PARENT = 2 ** 64 - 1


def build_engine(name="stack_search"):
    """Compile an engine (stack_search or stack_search_disk) if missing or older than its sources; return its path."""
    binary = ENGINE_DIR / "build" / name
    sources = [ENGINE_DIR / f"{name}.cpp", ENGINE_DIR / "rules.hpp"]
    if not binary.exists() or binary.stat().st_mtime < max(s.stat().st_mtime for s in sources):
        binary.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["clang++", "-O3", "-std=c++17", "-pthread", "-o", str(binary), str(sources[0])], check=True)
    return binary


class Value:
    """What one input does in a stack: the layer that binds it (owner), or the layer whose
    disabled source blocks it (blocked_by), or neither; with the binding's activators."""
    __slots__ = ("owner", "blocked_by", "activators")

    def __init__(self, owner=None, blocked_by=None, activators=None):
        self.owner, self.blocked_by, self.activators = owner, blocked_by, activators

    def __eq__(self, other):
        return isinstance(other, Value) and (self.owner, self.blocked_by) == (other.owner, other.blocked_by)

    def __hash__(self):
        return hash((self.owner, self.blocked_by))

    def __repr__(self):
        if self.owner:
            return f"Value({self.owner!r})"
        return f"Value(blocked by {self.blocked_by!r})" if self.blocked_by else "Value(nothing)"


def describe(activators):
    """One line per activator entry: kind, bindings, and the settings that change when it fires."""
    from .model import actions, entries
    parts = []
    for kind, entry in entries(activators or {}):
        s = entry.get("settings", {})
        extra = [f"{k}={s[k]}" for k in ("chord_button", "gyro_ratchet_button_mask", "delay_start",
                                        "hold_repeats", "interruptable") if k in s]
        parts.append(f"{kind}: " + "; ".join(a.rstrip(", ").strip() for a in actions(entry))
                     + (f" [{' '.join(extra)}]" if extra else ""))
    return " | ".join(parts)


class StackDB:
    def __init__(self, outdir, layout=None):
        self.dir = Path(outdir)
        self.layout = layout
        self.summary = json.loads((self.dir / "summary.json").read_text())
        self.complete = self.summary["complete"]
        self.held = self.summary.get("held", False)
        self.levels = self.summary.get("format") == "levels"
        self.top = self.summary.get("top", 0)  # --top K: stacks are (deep layers, top layers)
        self.layers, self.inputs, self.labels, self.controls = [], [], {}, []
        for line in (self.dir / "model.txt").read_text(encoding="utf-8").splitlines():
            word, _, rest = line.partition(" ")
            if word == "layer":
                self.layers.append(rest.split(" ", 1)[1])
            elif word == "input":
                _, source, name = rest.split(" ", 2)
                self.inputs.append((source, name))
            elif word == "control":
                parts = rest.split(" ")
                self.controls.append((parts[8], parts[9]))
            elif word == "event":
                self.labels[int(rest.split(" ", 1)[0])] = rest.split("| ", 1)[1] if "| " in rest else ""
        self.none = len(self.layers)
        self._files = {}
        self._profiles = None
        self._rows = None
        self._under, self._top, self._below, self._idle = {}, {}, {}, {}
        if self.levels:
            self.starts = self.summary["level_starts"]
        else:
            self.shards = self.summary["shards"]
            idx = json.loads((self.dir / "indexes.json").read_text())
            name = lambda i: None if i == self.none else self.layers[i]
            self._under = {(self.layers[y], self.layers[x]): gid for y, x, gid in idx["under"]}
            self._top = {(self.inputs[j], name(a), name(y)): gid for j, a, y, gid in idx["top"]}
            self._below = {(self.layers[x], self.inputs[j], name(a)): gid for x, j, a, gid in idx["below_top"]}
            self._idle = {(self.layers[x], bool(missed)): gid for x, missed, gid in idx.get("idle", [])}

    # -- raw states ------------------------------------------------------------
    def _open(self, path):
        if path not in self._files:
            self._files[path] = open(path, "rb")
        return self._files[path]

    def close(self):
        for f in self._files.values():
            f.close()
        self._files.clear()

    def _names(self, ids):
        """Layer names of stored ids; with --top, (frozenset of deep layers, top layers in order)."""
        if self.top:
            sep = ids.index(SEP)
            return frozenset(self.layers[i] for i in ids[:sep]), tuple(self.layers[i] for i in ids[sep + 1:])
        return tuple(self.layers[i] for i in ids)

    def _decode(self, data, offset):
        n = data[offset]
        stack = self._names(list(data[offset + 1:offset + 1 + n]))
        if not self.held:
            return stack, frozenset(), False
        held = int.from_bytes(data[offset + 1 + n:offset + 9 + n], "little")
        buttons = frozenset(self.controls[c] for c in range(len(self.controls)) if held >> c & 1)
        return stack, buttons, bool(data[offset + 9 + n])

    def _locate(self, gid):
        """(record file, record offset, parent, event) of one state."""
        if self.levels:
            level = bisect.bisect_right(self.starts, gid) - 1
            f = self._open(self.dir / f"levels/level_{level:03d}.meta")
            f.seek((gid - self.starts[level]) * LEVEL_META.size)
            parent, offset, event = LEVEL_META.unpack(f.read(LEVEL_META.size))
            return self.dir / f"levels/level_{level:03d}.rec", offset, parent, event
        shard, local = gid % self.shards, gid // self.shards
        f = self._open(self.dir / f"shard_{shard}.meta")
        f.seek(local * META.size)
        offset, parent, event, _ = META.unpack(f.read(META.size))
        return self.dir / f"shard_{shard}.stacks", offset, parent, event

    def state(self, gid):
        """(stack, held buttons, missed flag) of one state (buttons empty and flag False without --held)."""
        path, offset, _, _ = self._locate(gid)
        f = self._open(path)
        f.seek(offset)
        return self._decode(f.read(1) + f.read(255), 0)

    def stack(self, gid):
        """The stack (layer names, bottom first) of one state."""
        return self.state(gid)[0]

    def all_states(self):
        """Every reachable (stack, held buttons, missed flag) (reads every state file)."""
        if self.levels:
            for level in range(len(self.starts) - 1):
                data = (self.dir / f"levels/level_{level:03d}.rec").read_bytes()
                pos = 0
                while pos < len(data):
                    yield self._decode(data, pos)
                    pos += 1 + data[pos] + 9
            return
        for shard in range(self.shards):
            data = (self.dir / f"shard_{shard}.stacks").read_bytes()
            meta = (self.dir / f"shard_{shard}.meta").read_bytes()
            for k in range(len(meta) // META.size):
                yield self._decode(data, META.unpack_from(meta, k * META.size)[0])

    def all_stacks(self):
        """Every reachable stack (once per state)."""
        for stack, _, _ in self.all_states():
            yield stack

    def label(self, event):
        if not self.held:
            return self.labels.get(event, str(event))
        from .held_model import PHASE_NAMES
        control, phase = event // 16 - 1, event % 16
        where = "Always On" if control < 0 else "/".join(self.controls[control])
        return f"{PHASE_NAMES[phase]}: {where}"

    def witness(self, gid):
        """[(event label, stack after it)] from Base to this state; the first item is ("start", ("Base",))."""
        path = []
        while True:
            _, _, parent, event = self._locate(gid)
            if parent == NO_PARENT:
                path.append(("start", self.stack(gid)))
                break
            path.append((self.label(event), self.stack(gid)))
            gid = parent
        return path[::-1]

    # -- distinct ordered stacks and their input owners ---------------------------
    def distinct_stacks(self):
        """Every distinct ordered stack: {id, stack, top, depth (fewest events), witness, clean, count,
        idle (1: nothing held, 2: nothing held after a missed release), profile, below}."""
        with open(self.dir / "stacks.tsv") as f:
            for n, line in enumerate(f):
                cols = line.rstrip("\n").split("\t")
                stack = self._names([int(i) for i in cols[0].split()])
                top = (stack[1][-1] if stack[1] else None) if self.top else stack[-1]
                row = {"id": n, "stack": stack, "top": top, "depth": int(cols[1]), "witness": int(cols[2]),
                       "clean": cols[3] == "1", "count": int(cols[4])}
                if len(cols) >= 8 and cols[6] != "-1":
                    row.update(idle=int(cols[5]), profile=int(cols[6]), below=int(cols[7]))
                yield row

    def distinct_stack_names(self):
        for row in self.distinct_stacks():
            yield row["stack"]

    def profiles(self):
        """[owner codes per input] for every profile (see tools/stack_search/rules.hpp)."""
        if self._profiles is None:
            self._profiles = [[int(c) for c in line.split("\t")[1].split()]
                              for line in (self.dir / "profiles.tsv").read_text().splitlines()]
        return self._profiles

    def _value(self, code, j):
        if code == NONE_OWNER:
            return Value()
        if code >= BLOCKED:
            return Value(blocked_by=self.layers[code - BLOCKED])
        title = self.layers[code]
        return Value(owner=title, activators=self._activators(title, j))

    def profile_values(self, profile):
        """{input: Value} for one profile id."""
        return {j: self._value(code, j) for j, code in zip(self.inputs, self.profiles()[profile])}

    def _rows_by_stack(self):
        if self._rows is None:
            self._rows = {row["stack"]: row for row in self.distinct_stacks()}
        return self._rows

    def values(self, stack, below=False):
        """{input: Value}: what every input does in this stack (below=True: in the stack under its top layer).

        Read from the stored profile when the search found the stack; otherwise
        computed from the layout."""
        stack = tuple(stack)
        row = self._rows_by_stack().get(stack)
        if row and "profile" in row:
            return self.profile_values(row["below"] if below else row["profile"])
        return {j: self._lookup(stack[:-1] if below else stack, j) for j in self.inputs}

    def _lookup(self, layers, j):
        """The Value of input j in `layers`, from the layout JSON (mirrors stacks.definer)."""
        from .model import defined
        if self.layout is None:
            raise ValueError("StackDB needs the layout for stacks the search didn't store")
        for title in reversed(layers):
            group = self.layout.active(title).get(j[0])
            if group is None:
                continue
            if group["mode"] == "disabled":
                return Value(blocked_by=title)
            if defined(group, j[1]):
                return Value(owner=title, activators=group["inputs"][j[1]]["activators"])
        return Value()

    def moment(self, gid):
        """One state in full: {"stack", "held", "missed", "values" (every input), "witness"}."""
        stack, held, missed = self.state(gid)
        return {"stack": stack, "held": held, "missed": missed, "values": self.values(stack),
                "witness": self.witness(gid)}

    # -- SQLite ------------------------------------------------------------------
    def build_sqlite(self, path=None):
        """Write the stacks, their input owners and the layout's bindings to SQLite; returns the path."""
        path = Path(path or self.dir / "stacks.sqlite")
        if path.exists():
            path.unlink()
        jindex = {j: n for n, j in enumerate(self.inputs)}
        index = {t: n for n, t in enumerate(self.layers)}
        con = sqlite3.connect(path)
        con.executescript("""
            CREATE TABLE layers (id INTEGER PRIMARY KEY, title TEXT);
            CREATE TABLE inputs (id INTEGER PRIMARY KEY, source TEXT, name TEXT);
            CREATE TABLE stacks (id INTEGER PRIMARY KEY, layers TEXT, top INT, size INT, depth INT, witness INT,
                                 clean INT, idle INT, count INT, profile INT, below INT);
            CREATE TABLE profile_inputs (profile INT, input INT, owner INT, blocked_by INT);
            CREATE TABLE bindings (layer INT, input INT, activators TEXT, summary TEXT);
        """)
        con.executemany("INSERT INTO layers VALUES (?, ?)", enumerate(self.layers))
        con.executemany("INSERT INTO inputs VALUES (?, ?, ?)", ((n, s, name) for n, (s, name) in enumerate(self.inputs)))
        con.executemany("INSERT INTO stacks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        ((r["id"], json.dumps(r["stack"]), index[r["top"]], len(r["stack"]), r["depth"], r["witness"],
                          int(r["clean"]), r.get("idle"), r["count"], r.get("profile"), r.get("below"))
                         for r in self.distinct_stacks()))
        if (self.dir / "profiles.tsv").exists():
            con.executemany("INSERT INTO profile_inputs VALUES (?, ?, ?, ?)",
                            ((p, j, code if code < BLOCKED else None, code - BLOCKED if code >= BLOCKED else None)
                             for p, codes in enumerate(self.profiles()) for j, code in enumerate(codes)
                             if code != NONE_OWNER))
        if self.layout is not None:
            rows = []
            for lid, title in enumerate(self.layers):
                for source, group in self.layout.active(title).items():
                    if group["mode"] == "disabled":
                        continue
                    for name, value in group.get("inputs", {}).items():
                        acts = value.get("activators")
                        if acts and (source, name) in jindex:
                            rows.append((lid, jindex[(source, name)], json.dumps(acts), describe(acts)))
            con.executemany("INSERT INTO bindings VALUES (?, ?, ?, ?)", rows)
        views = []
        for view, column in (("stack_values", "profile"), ("inherited", "below")):
            views.append(f"""
            CREATE VIEW {view} AS
                SELECT s.id AS stack, t.title AS top, i.source, i.name, o.title AS owner, b.title AS blocked_by,
                       g.summary
                FROM stacks s JOIN layers t ON t.id = s.top CROSS JOIN inputs i
                LEFT JOIN profile_inputs p ON p.profile = s.{column} AND p.input = i.id
                LEFT JOIN layers o ON o.id = p.owner LEFT JOIN layers b ON b.id = p.blocked_by
                LEFT JOIN bindings g ON g.layer = p.owner AND g.input = i.id;""")
        con.executescript("""
            CREATE INDEX stacks_top ON stacks (top);
            CREATE INDEX stacks_layers ON stacks (layers);
            CREATE INDEX profile_inputs_key ON profile_inputs (profile, input);
            CREATE INDEX bindings_key ON bindings (layer, input);
        """ + "".join(views))
        con.commit()
        con.close()
        self._sqlite = path
        return path

    def _connect(self):
        path = getattr(self, "_sqlite", None) or self.dir / "stacks.sqlite"
        if not Path(path).exists():
            path = self.build_sqlite()
        return sqlite3.connect(path)

    def sql(self, query, params=()):
        """Run a query on stacks.sqlite (built on first use); returns the rows."""
        con = self._connect()
        try:
            return con.execute(query, params).fetchall()
        finally:
            con.close()

    def stacks_with_top(self, title, clean_only=False):
        """Rows for every stored stack with `title` on top."""
        query = ("SELECT s.layers, s.depth, s.witness, s.clean, s.count, s.below FROM stacks s"
                 " JOIN layers t ON t.id = s.top WHERE t.title = ?" + (" AND s.clean = 1" if clean_only else ""))
        return [{"stack": tuple(json.loads(l)), "depth": d, "witness": w, "clean": bool(c), "count": n, "below": b}
                for l, d, w, c, n, b in self.sql(query, (title,))]

    def inherited_values(self, title, source, name, clean_only=False):
        """{layer below `title` that binds this input (None: nothing does or it is blocked): details}.

        Over every stored stack with `title` on top, the layer that fires the input from
        below it (topmost binding; a disabled source stops the lookup). Details:
        activators (from the JSON), stacks, count, and the shallowest witness.
        """
        j = (source, name)
        result = {}
        for row in self.stacks_with_top(title, clean_only):
            if row["below"] is not None:
                value = self.profile_values(row["below"]).get(j, Value())
            else:
                value = self._lookup(row["stack"][:-1], j)
            info = result.setdefault(value.owner, {"activators": value.activators, "stacks": [], "count": 0,
                                                   "witness": row["witness"], "depth": row["depth"]})
            info["stacks"].append(row["stack"])
            info["count"] += 1
            if row["depth"] < info["depth"]:
                info["depth"], info["witness"] = row["depth"], row["witness"]
        return result

    def inheritance(self, title, clean_only=False):
        """{input: {Value: number of stacks}}: everything `title` can inherit, for every input,
        over every stored stack with it on top."""
        rows = self.sql("SELECT s.below, COUNT(*) FROM stacks s JOIN layers t ON t.id = s.top WHERE t.title = ?"
                        + (" AND s.clean = 1" if clean_only else "") + " GROUP BY s.below", (title,))
        result = {j: {} for j in self.inputs}
        for below, count in rows:
            for j, value in self.profile_values(below).items():
                result[j][value] = result[j].get(value, 0) + count
        return result

    # -- facts -------------------------------------------------------------------
    def _derive(self):
        """under / idle facts for the disk format, from the distinct stacks."""
        if self._under or not self.levels:
            return
        for row in self.distinct_stacks():
            stack = row["stack"]
            for i, x in enumerate(stack):
                for y in stack[1:i]:
                    self._under.setdefault((y, x), row["witness"])
            for flag, missed in ((1, False), (2, True)):
                if row.get("idle", 0) & flag:
                    for y in stack[1:]:
                        self._idle.setdefault((y, missed), row["witness"])

    def under_pairs(self):
        self._derive()
        return set(self._under)

    def under_witnesses(self):
        self._derive()
        return dict(self._under)

    def top_facts(self):
        return set(self._top)

    def below_top_facts(self):
        return set(self._below)

    def idle(self, missed=False):
        """--held: layers that can be present with nothing held (after a missed release, or with none)."""
        self._derive()
        return {x for x, m in self._idle if m == missed}

    def idle_witnesses(self, missed=False):
        self._derive()
        return {x: gid for (x, m), gid in self._idle.items() if m == missed}

    # -- queries -----------------------------------------------------------------
    def under(self, title):
        """Every layer that can be below `title` (Base isn't listed)."""
        self._derive()
        return {y for y, x in self._under if x == title}

    def inherited(self, title, source, name, below=True):
        """[(layer or None, activators)] that fire this input while `title` is active (in-memory format)."""
        j = (source, name)
        if below:
            owners = sorted({a for x, jj, a in self._below if x == title and jj == j}, key=str)
        else:
            owners = sorted({a for jj, a, y in self._top if jj == j and y == title}, key=str)
        return [(a, self._activators(a, j)) for a in owners]

    def present_when(self, title, source, name):
        """Every layer that can be present when `title` fires this input (itself included), or empty."""
        j = (source, name)
        if (j, title, None) not in self._top:
            return set()
        return {y for jj, a, y in self._top if jj == j and a == title and y} | {title}

    def _activators(self, title, j):
        if self.layout is None or title is None:
            return None
        group = self.layout.active(title).get(j[0])
        return (group or {}).get("inputs", {}).get(j[1], {}).get("activators") or None


def run(layout_path, outdir, extra=()):
    """Export the model and run an engine, streaming its progress.

    --held: the realistic model, in memory. --disk: the realistic model, disk-backed
    (tools/stack_search/stack_search_disk.cpp; takes --memory GB, --disk-limit GB, --resume).
    Add --missed for releases while the Steam menu is open."""
    from .held_model import HeldModel
    from .model import Layout
    from .search_model import SearchModel
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    layout = Layout(json.loads(Path(layout_path).read_text(encoding="utf-8")))
    extra = list(extra)
    if "--disk" in extra:
        extra = [a for a in extra if a not in ("--disk", "--held")]
        HeldModel(layout).write_held(outdir / "model.txt")
        return subprocess.call([str(build_engine("stack_search_disk")), str(outdir / "model.txt"), str(outdir), *extra])
    if "--held" in extra:
        HeldModel(layout).write_held(outdir / "model.txt")
    else:
        SearchModel(layout).write(outdir / "model.txt")
    return subprocess.call([str(build_engine()), str(outdir / "model.txt"), str(outdir), *extra])


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "run":
        sys.exit(run(sys.argv[2], sys.argv[3], sys.argv[4:]))
    if len(sys.argv) == 4 and sys.argv[1] == "sqlite":
        from .model import Layout
        db = StackDB(sys.argv[3], Layout(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))))
        print(db.build_sqlite())
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
