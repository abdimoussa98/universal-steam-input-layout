"""The realistic stack model: tracks which buttons are held.

A state is (stack, held buttons, missed-release flag). From each state:

- **Tracked buttons** are the inputs whose timing matters: a chord checks
  them (bumpers, trigger pulls, Select/Start, stick touch/click/directions,
  pad touch: a pad chord means the thumb is on the pad), or they have a
  release entry, a `hold_layer`, or a delayed or repeating layer command.
  They can be
  pressed, held (delayed and repeating entries fire) and released. With
  missed=True they can also be released while the Steam menu is open
  (nothing fires; the missed flag is set). That is off by default: the
  cleanup functions exist to recover from it, so the search leaves it out.
- **Other inputs** (most face buttons, D-pad and back buttons, pad
  directions/click/edge/scroll without the timings above) are taps: press,
  optionally held long enough for delays and repeats, then released (or,
  with missed=True, lost).
- **Always On** entries of the layer on top can fire at any time.
- Releasing a control removes the layers its `hold_layer` bindings hold.
- One thumb is in one place; a pad or stick input needs its touch held
  (when touch is tracked), a trigger click its edge (when the edge is).

What fires is decided by the layer on top for that input (a `disabled` source
stops the lookup):

- press: Regular, Start and Soft Press without a delay, and chords whose
  buttons are held. A satisfied chord blocks every interruptible Regular
  Press on the same input (guarded recovery).
- held: entries with a Fire Start Delay or Hold to Repeat (chords only while
  their buttons are held; the same blocking applies).
- release: Release entries.

When several entries fire together, every order is considered (up to three).
Re-adding a layer that's already present doesn't move it.

Physical limits: a thumb rests on one source at a time (left: left stick,
left pad, D-pad, Select; right: right stick, right pad, face buttons, Start);
a stick or pad click, edge or direction needs that thumb touching it; at most
two adjacent directions; a trigger's full pull includes its soft pull.

Mode shifts: while the button that shifts a source is held, the shifted
group's inputs can be tapped with the shifted group's bindings.

`HeldModel.successors` is the Python reference; the engine
(tools/stack_search, `--held`) implements the same rules and the tests check
they agree exactly.
"""
import itertools

from .model import MODE_SHIFT, actions, entries
from .search_model import ADD, REMOVE, SearchModel

LEGACY = {"1": [("switch", "left_bumper")], "2": [("switch", "right_bumper")],
          "5": [("left_trigger", "click")], "6": [("right_trigger", "click")],
          "7": [("left_trigger", "edge"), ("left_trigger", "click")],
          "8": [("right_trigger", "edge"), ("right_trigger", "click")],
          "9": [("joystick", "click")], "20": [("right_joystick", "click")],
          "14": [("switch", "button_escape")], "15": [("switch", "button_menu")],
          "16": "pad:left_trackpad", "17": "pad:right_trackpad",
          "23": [("joystick", "touch")], "24": [("right_joystick", "touch")]}
BITS = {3: [("switch", "left_bumper")], 2: [("switch", "right_bumper")],
        1: [("left_trigger", "click")], 0: [("right_trigger", "click")],
        25: [("left_trigger", "edge"), ("left_trigger", "click")],
        24: [("right_trigger", "edge"), ("right_trigger", "click")],
        22: [("joystick", "click")], 26: [("right_joystick", "click")],
        14: [("switch", "button_escape")], 12: [("switch", "button_menu")],
        19: "pad:left_trackpad", 20: "pad:right_trackpad",
        46: [("joystick", "touch")], 47: [("right_joystick", "touch")],
        30: "deflect:joystick", 31: "deflect:right_joystick"}
THUMBS = {"joystick": "L", "left_trackpad": "L", "dpad": "L", ("switch", "button_menu"): "L",
          "right_joystick": "R", "right_trackpad": "R", "button_diamond": "R", ("switch", "button_escape"): "R"}
DIRS = {"dpad_north": 0, "dpad_east": 1, "dpad_south": 2, "dpad_west": 3}
ALWAYS = ("switch", "always_on_action")
PRESS, LATER, RELEASE, LOST, TAP, TAP_LOST, TAP_HELD, TAP_HELD_LOST, TIMER, SHIFT_TAP = range(10)
PHASE_NAMES = ["press", "hold", "release", "release while the Steam menu is open (missed)", "tap",
               "tap, released while the Steam menu is open (missed)", "tap and hold",
               "tap and hold, released while the Steam menu is open (missed)", "Always On timer", "mode-shift tap"]
KINDS = {"Full_Press": "P", "Start_Press": "S", "Soft_Press": "F", "chord": "C", "release": "R"}


class HeldModel(SearchModel):
    def __init__(self, layout, missed=False):
        super().__init__(layout)
        self.missed = missed
        self.controls = [j for j in self.inputs if j != ALWAYS]
        self.cid = {j: n for n, j in enumerate(self.controls)}
        self.conds, self._cond_ids = [], {}
        self.entries = {}   # (layer id, control id or "always") -> [entry]
        self.shift_entries = {}  # (group id, control id) -> [entry]
        owners = set()
        for title in self.layer_names:
            lid = self.index[title]
            for source, group in layout.active(title).items():
                if group["mode"] == "disabled":
                    continue
                for name, value in group.get("inputs", {}).items():
                    acts = value.get("activators")
                    if not acts:
                        continue
                    key = (lid, "always" if (source, name) == ALWAYS else self.cid[(source, name)])
                    self.entries[key] = [self._entry(kind, entry, owners) for kind, entry in entries(acts)]
        self.shift_groups = {}
        for (lid, key), ents in list(self.entries.items()):
            for e in ents:
                for gid in e["shift"]:
                    if gid in self.shift_groups:
                        continue
                    group = layout.groups.get(gid, {})
                    self.shift_groups[gid] = {}
                    source = None
                    for p in layout.cm["preset"]:
                        state = p["group_source_bindings"].get(gid)
                        if state:
                            source = state.split(" ", 1)[0]
                    for name, value in group.get("inputs", {}).items():
                        j = (source, name)
                        if j in self.cid and value.get("activators"):
                            self.shift_groups[gid][self.cid[j]] = [self._entry(k, en, owners)
                                                                   for k, en in entries(value["activators"])]
        # Tracked (held) controls: a chord checks them, or their timing changes layers
        # (a release entry, a hold_layer, a delayed or repeating layer command).
        # Everything else is a press-and-release tap.
        self.holds = {}  # control -> hold_layer targets (Steam removes them when it is released)
        per_control = [(key, ents) for (_, key), ents in self.entries.items() if key != "always"]
        per_control += [(c, ents) for group in self.shift_groups.values() for c, ents in group.items()]
        for c, ents in per_control:
            for e in ents:
                if e["kind"] == "R" or e["hold"] or ((e["delay"] or e["repeat"]) and e["ops"]):
                    owners.add(self.controls[c])
                if e["hold"]:
                    self.holds.setdefault(c, set()).update(e["hold"])
        self.owner = [False] * len(self.controls)
        for j in owners:
            if j in self.cid:
                self.owner[self.cid[j]] = True
        self.thumb = [THUMBS.get(j, THUMBS.get(j[0], "-")) for j in self.controls]
        self.thumb_source = [(j[0] if j not in THUMBS else f"{j[0]}/{j[1]}") for j in self.controls]

    def _cond(self, settings, owners):
        if "chord_button" in settings:
            specs, all_ = [LEGACY.get(settings["chord_button"])], False
        elif "gyro_ratchet_button_mask" in settings:
            mask = int(settings["gyro_ratchet_button_mask"])
            specs = [BITS.get(b) for b in range(64) if mask >> b & 1]
            all_ = settings.get("gyro_ratchet_button_requireany_or_all") == "1"
        else:
            return -1
        if any(s is None for s in specs):
            key = ("unknown",)
        else:
            expanded = []
            for spec in specs:
                if isinstance(spec, str):
                    kind, source = spec.split(":")
                    # pad: the thumb is on the pad (every pad input implies touch);
                    # deflect: any stick direction or its edge
                    ids = [j for j in self.inputs if j[0] == source and
                           (j[1] == "touch" if kind == "pad" else j[1] not in ("touch", "click"))]
                else:
                    ids = [j for j in spec if j in self.input_index]
                owners.update(ids)
                expanded.append(tuple(sorted(ids)))
            key = ("all" if all_ else "any", tuple(expanded))
        if key not in self._cond_ids:
            self._cond_ids[key] = len(self.conds)
            self.conds.append(key)
        return self._cond_ids[key]

    def _entry(self, kind, entry, owners):
        s = entry.get("settings", {})
        return {"kind": KINDS.get(kind, "P"), "delay": bool(s.get("delay_start") and s.get("delay_start") != "0"),
                "repeat": s.get("hold_repeats") == "1", "interruptible": s.get("interruptable") != "0",
                "cond": self._cond(s, owners) if kind == "chord" else -1,
                "ops": [(REMOVE if op == "remove_layer" else ADD, self.index[t]) for op, t in self.layout.layer_ops(entry)],
                "hold": [self.index[t] for op, t in self.layout.layer_ops(entry) if op == "hold_layer"],
                "shift": [m.group(2) for a in actions(entry) if (m := MODE_SHIFT.search(a))]}

    # -- rules ---------------------------------------------------------------
    def satisfied(self, cond, held, for_blocking=False):
        if cond < 0:
            return True
        key = self.conds[cond]
        if key == ("unknown",):
            return not for_blocking
        names = {self.controls[c] for c in held}
        hits = [any(j in names for j in spec) for spec in key[1]]
        return all(hits) if key[0] == "all" else any(hits)

    def valid(self, held):
        names = [self.controls[c] for c in held]
        for thumb in "LR":
            if len({self.thumb_source[c] for c in held if self.thumb[c] == thumb}) > 1:
                return False
        by_source = {}
        for j in names:
            by_source.setdefault(j[0], set()).add(j[1])
        for source, got in by_source.items():
            if source.endswith("joystick") or source.endswith("trackpad"):
                dirs = sorted(DIRS[d] for d in got if d in DIRS)
                if len(dirs) > 2 or (len(dirs) == 2 and (dirs[1] - dirs[0]) not in (1, 3)):
                    return False
                if (got - {"touch"}) and self._tracked((source, "touch")) and "touch" not in got:
                    return False
            if source.endswith("trigger") and "click" in got and self._tracked((source, "edge")) and "edge" not in got:
                return False
        return True

    def _tracked(self, j):
        return j in self.cid and self.owner[self.cid[j]]

    def _owner_of(self, stack, key):
        """(layer id, entries) of the topmost layer binding this control, or None (none or blocked)."""
        if key == "always" and ALWAYS not in self.input_index:
            return None
        jid = self.input_index[ALWAYS] if key == "always" else self.input_index[self.controls[key]]
        for lid in reversed(stack):
            if jid in self.blocks.get(lid, set()):
                return None
            if jid in self.binds.get(lid, set()):
                return lid, self.entries.get((lid, key), [])
        return None

    def _selected(self, ents, held, phase):
        blocked = any(e["kind"] == "C" and self.satisfied(e["cond"], held, for_blocking=True) for e in ents)
        chosen = []
        for e in ents:
            if phase == "release":
                ok = e["kind"] == "R"
            elif e["kind"] == "R":
                ok = False
            elif e["kind"] == "C" and not self.satisfied(e["cond"], held):
                ok = False
            elif e["kind"] == "P" and e["interruptible"] and blocked:
                ok = False
            elif phase == "press":
                ok = not e["delay"]
            elif phase == "always":
                ok = True
            else:
                ok = e["delay"] or e["repeat"]
            if ok:
                chosen.append(e)
        return chosen

    def _owners(self, stack, key):
        """Every (layer id, entries) that can be the topmost binding of `key` (None: nothing or blocked)."""
        return [self._owner_of(stack, key)]

    def fire(self, stack, held, key, phase, ents=None):
        """Stacks after `key` fires in `phase` ("press", "later", "release", "always")."""
        choices = [ents] if ents is not None else [found[1] if found else [] for found in self._owners(stack, key)]
        result = set()
        for ents in choices:
            opslists = [e["ops"] for e in self._selected(ents, held, phase) if e["ops"]]
            orders = itertools.permutations(opslists) if len(opslists) <= 3 else [opslists]
            for order in orders:
                s = stack
                for ops in order:
                    s = self.apply(s, ops)
                if phase == "release" and key in self.holds:  # letting go ends its hold_layer
                    s = self.apply(s, [(REMOVE, t) for t in sorted(self.holds[key])])
                result.add(s)
        return result

    def shifted(self, stack, held):
        """{group id} of mode shifts active now (fired by a held button's current binding)."""
        active = set()
        for c in held:
            for found in self._owners(stack, c):
                if found:
                    for e in self._selected(found[1], held, "press"):
                        active.update(e["shift"])
        return active

    def successors(self, state):
        """{(next state, (control id or -1, phase))} from (stack, held frozenset of control ids, missed flag)."""
        stack, held, missed = state
        out = set()
        for c in range(len(self.controls)):
            if self.owner[c]:
                if c in held:
                    for s in self.fire(stack, held, c, "later"):
                        out.add(((s, held, missed), (c, LATER)))
                    rest = held - {c}
                    if self.valid(rest):
                        for s in self.fire(stack, held, c, "release"):
                            out.add(((s, rest, missed), (c, RELEASE)))
                        if self.missed:
                            out.add(((stack, rest, True), (c, LOST)))
                else:
                    more = held | {c}
                    if self.valid(more):
                        for s in self.fire(stack, more, c, "press"):
                            out.add(((s, more, missed), (c, PRESS)))
            else:
                more = held | {c}
                if self.valid(more):
                    self._tap(stack, held, missed, c, more, None, out, TAP)
        for gid in sorted(self.shifted(stack, held)):
            for c, ents in self.shift_groups.get(gid, {}).items():
                more = held | {c}
                if c not in held and self.valid(more):
                    self._tap(stack, held, missed, c, more, ents, out, SHIFT_TAP)
        for s in self.fire(stack, held, "always", "always"):
            out.add(((s, held, missed), (-1, TIMER)))
        return out

    def _tap(self, stack, held, missed, c, more, ents, out, kind):
        for s1 in self.fire(stack, more, c, "press", ents):
            for held_long in (False, True):
                mids = self.fire(s1, more, c, "later", ents) if held_long else {s1}
                for s2 in mids:
                    code = (TAP_HELD if held_long else TAP) if kind == TAP else kind
                    for s3 in self.fire(s2, more, c, "release", ents):
                        out.add(((s3, held, missed), (c, code)))
                    lost = (TAP_HELD_LOST if held_long else TAP_LOST) if kind == TAP else kind
                    if self.missed:
                        out.add(((s2, held, True), (c, lost)))

    def start(self):
        return ((0,), frozenset(), False)

    def label(self, event):
        c, phase = event
        name = "Always On" if c < 0 else f"{self.controls[c][0]}/{self.controls[c][1]}"
        return f"{PHASE_NAMES[phase]}: {name}"

    # -- export ----------------------------------------------------------------
    def write_held(self, path):
        """The model file for `stack_search --held`."""
        self.write(path)
        lines = path.read_text(encoding="utf-8").splitlines()[:-1]  # drop "end"
        lines.append(f"controls {len(self.controls)}")
        sources = sorted({self.thumb_source[c] for c in range(len(self.controls))})
        for c, (source, name) in enumerate(self.controls):
            kind = "touch" if name == "touch" else "click" if name == "click" else "edge" if name == "edge" else \
                "dir" if name in DIRS else "other"
            family = "stick" if source.endswith("joystick") or source.endswith("trackpad") else \
                "trigger" if source.endswith("trigger") else "other"
            lines.append(f"control {c} {int(self.owner[c])} {self.thumb[c]} {sources.index(self.thumb_source[c])} "
                         f"{self.inputs.index(self.controls[c])} {family} {kind} {DIRS.get(name, -1)} {source} {name}")
        for c, targets in sorted(self.holds.items()):
            lines.append(f"hold {c} {len(targets)} " + " ".join(str(t) for t in sorted(targets)))
        lines.append(f"always {self.input_index.get(ALWAYS, -1)}")
        lines.append(f"conds {len(self.conds)}")
        for n, key in enumerate(self.conds):
            if key == ("unknown",):
                lines.append(f"cond {n} unknown")
            else:
                specs = " ".join(f"{len(spec)} " + " ".join(str(self.cid[j]) for j in spec) for spec in key[1])
                lines.append(f"cond {n} {key[0]} {len(key[1])} {specs}")

        def entry_line(prefix, owner, c, e):
            ops = " ".join(f"{op} {t}" for op, t in e["ops"])
            return (f"{prefix} {owner} {c} {e['kind']} {int(e['delay'])} {int(e['repeat'])} {int(e['interruptible'])} "
                    f"{e['cond']} {len(e['ops'])} {ops} {len(e['shift'])} "
                    + " ".join(str(sorted(self.shift_groups).index(g)) for g in e["shift"])).rstrip()
        for (lid, c), ents in sorted(self.entries.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            for e in ents:
                lines.append(entry_line("entry", lid, -1 if c == "always" else c, e))
        gids = sorted(self.shift_groups)
        lines.append(f"shifts {len(gids)}")
        for g, gid in enumerate(gids):
            for c, ents in sorted(self.shift_groups[gid].items()):
                for e in ents:
                    lines.append(entry_line("sentry", g, c, e))
        lines.append("end")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def explore(model, depth=None):
    """Reference search: {state: fewest events} from the start, up to `depth` events (None: until done)."""
    seen = {model.start(): 0}
    frontier = [model.start()]
    level = 0
    while frontier and (depth is None or level < depth):
        level += 1
        following = []
        for state in frontier:
            for nxt, _ in model.successors(state):
                if nxt not in seen:
                    seen[nxt] = level
                    following.append(nxt)
        frontier = following
    return seen


class TopModel(HeldModel):
    """The held model with only the top `k` layers kept in order: the "possible" bound.

    A state's stack is (deep, top): `top` is the topmost layers in order (at most k),
    `deep` the set of layers under them (Base always), order unknown. Everything about
    buttons is exact. When an input falls through `top`, every deep layer that binds
    or blocks it can be its owner (Base only when no other deep layer does), so the
    reachable states cover every real stack (a real stack is some order of `deep`
    followed by `top`) and may include some that can't happen. Without deep order the
    state space is finite and small enough to search to completion. k at least the
    tallest stack is exactly HeldModel.
    """

    def __init__(self, layout, k, missed=False):
        super().__init__(layout, missed=missed)
        self.k = k

    def start(self):
        return ((frozenset({0}), ()), frozenset(), False)

    def apply(self, stack, ops):
        deep, top = stack
        top = list(top)
        for op, t in ops:
            if op == REMOVE:
                if t in top:
                    top.remove(t)
                elif t != 0:
                    deep = deep - {t}
            elif t not in top and t not in deep:
                top.append(t)
                if len(top) > self.k:
                    deep = deep | {top.pop(0)}
        return deep, tuple(top)

    def _owners(self, stack, key):
        if key == "always" and ALWAYS not in self.input_index:
            return [None]
        jid = self.input_index[ALWAYS] if key == "always" else self.input_index[self.controls[key]]
        deep, top = stack
        for lid in reversed(top):
            if jid in self.blocks.get(lid, set()):
                return [None]
            if jid in self.binds.get(lid, set()):
                return [(lid, self.entries.get((lid, key), []))]
        found = [None if jid in self.blocks.get(lid, set()) else (lid, self.entries.get((lid, key), []))
                 for lid in sorted(deep - {0})
                 if jid in self.blocks.get(lid, set()) or jid in self.binds.get(lid, set())]
        if found:
            return found
        if jid in self.binds.get(0, set()) and jid not in self.blocks.get(0, set()):  # Base, under everything
            return [(0, self.entries.get((0, key), []))]
        return [None]

    def covers(self, abstract, stack):
        """True if a real stack (layer ids, Base first) is one of the orders this abstract stack stands for."""
        deep, top = abstract
        n = len(stack) - len(top)
        return n >= 1 and tuple(stack[n:]) == top and set(stack[:n]) == set(deep)

    def names_of(self, stack):
        deep, top = stack
        return tuple(sorted(self.layer_names[i] for i in deep)), tuple(self.layer_names[i] for i in top)
