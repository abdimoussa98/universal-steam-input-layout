"""The Cleanup audit: what a cleanup function and a release may remove.

The author's rule (2026-10-02): every layer takes care of itself and what is
below it, and of what is above it if it has that responsibility. The six rules
are in findings/2026-10-02-cleanup-boundaries/README.md; the plan is
plans/2026-10-02-cleanup-audit.md.

    cleanup function   a guarded recovery: a repeating, interruptible removal beside a
                       chord with the owner's button (flow_model role "recovery")
    guard              the buttons of the chords on the same input
    keeper             what keeps a layer alive:
                         mode     a stateful layer
                         timer    an Always On window
                         thumb    a stick-touch helper (its Release is on a stick touch)
                         button   the buttons whose Release removes it, checked against
                                  the guards of its own cleanup functions
                         inside   its Release is on a stick, not a button: it lives inside
                                  the hold of a layer that adds it
                         other    none of these (a threshold or pressure exit)

The stacks are the backward chains (chains.py): `present(layer)` is every layer
that can be under it or on top of it. Chords are ignored there, and timing and
missed releases are not modelled, so "never there" means never in a normal
sequence.

Checks, each a failing finding:

    outside the guard   a cleanup removes a layer its guard's buttons don't keep
                        alive, or a stateful layer, a stick-touch helper or a window
    left below          a layer under the host is kept by the guard's buttons and
                        isn't removed (one step, no exceptions)
    left above          the same for a layer on top that leaves the input alone
    hidden cleanup      a layer of the same interaction binds an input that has a
                        cleanup below and puts no cleanup or accepted shape there
    never there         a cleanup, an ordinary release or a Modifier 2 quick tap
                        removes a layer that can never be on the stack with it
    guard mismatch      one layer's cleanups have different guard buttons
    hidden exit         a layer that can land on top of another covers an exit on what
                        keeps the lower layer alive, and doesn't remove it there (R136)

An exit is a Release that removes its own layer. For the hidden-exit check a
layer on top covers it when it answers that input instead: it binds it, or blocks
it with a disabled source or another source mode. The stack is taken after the
whole binding that added the upper layer has run. Since 2026-10-03 "on top" also
counts a landing: any adding binding that answers on a stack the chains visited,
whichever layer it belongs to (chains.landings). Covering an exit that is not on
the keeper is information, not a finding: the keeper's exit still works.

    exit to review      such a pair, where either layer changed since the last snapshot:
                        it fails until it is fixed or accepted in the exceptions register
                        (author, 2026-10-02). `changed` names the changed layers.

The touchpad exception (author, 2026-10-02) sets a hidden-exit pair aside when
either layer is a touchpad layer (only trackpad bindings add it) or the covered
exit is a trackpad input. It applies while the exceptions register has it
(`cleanups.touchpad_exits`, filled by steam_layout/exceptions.py).

The walk (author, 2026-10-03). With `walk=N` the hidden-exit check reads other
stacks: every stack the bindings can build with at most N layers on at once, in any
order and with any number of presses (walk.py), not the chain stacks. Every layer of
every such stack is tested. It is slower and complete up to N; the chain stacks stay
the default because they follow a chain to any length. N is at most 10 by the author's
ceiling (`walk.MAX_SIMULTANEOUS`). With `extras=K` it reads the chain walk with K extra
presses per chain instead, every stack tested: the author's choice of 2026-10-03, a cap on
presses rather than on layers. Both run in the compiled engines (native.py) when they can
be built; the Python walk is the reference.

Left out, by the author's choice: layers that only `hold_layer` adds. They are
neither audited nor counted as removed layers.
"""
from collections import defaultdict

from .chains import Chains
from .flow_model import Inventory, chord_condition, resolve
from .model import always_on_layers, entries, map_title
from .stacks import apply_ops
from . import native
from .walk import MAX_SIMULTANEOUS, Walk

BUTTONS = {("switch", "left_bumper"): "LB", ("switch", "right_bumper"): "RB",
           ("switch", "button_escape"): "Start", ("switch", "button_menu"): "Select",
           ("joystick", "touch"): "LSt", ("right_joystick", "touch"): "RSt",
           ("joystick", "click"): "L3", ("right_joystick", "click"): "R3",
           ("left_trigger", "click"): "LT", ("right_trigger", "click"): "RT",
           ("left_trigger", "edge"): "LT", ("right_trigger", "edge"): "RT",
           ("left_trackpad", "touch"): "LTP", ("right_trackpad", "touch"): "RTP"}
THUMBS = frozenset({"LSt", "RSt"})
PADS = frozenset({"left_trackpad", "right_trackpad"})
NAMES = frozenset(BUTTONS.values())
CHECKS = ("outside the guard", "left below", "left above", "hidden cleanup", "never there", "guard mismatch",
          "hidden exit", "exit to review")
ENFORCES = {"outside the guard": ("R127", "R131"), "left below": ("R128",), "left above": ("R129",),   # check -> rules
            "hidden cleanup": ("R130",), "never there": ("R132",), "guard mismatch": ("R127",),
            "hidden exit": ("R136",), "exit to review": ("R136",)}
PATHS_UP_TO = 4            # extra presses up to which the engine that keeps paths runs the chain walk
TOUCHPAD_STALE = "the touchpad exception to R136"
LISTS = ("recovery", "release")          # the roles whose removal lists follow "never there"
ROLE = {"recovery": "cleanup function", "release": "release"}


def name(control):
    """A control's button name, or source/input when it isn't one a chord can name."""
    return BUTTONS.get(control, f"{control[0]}/{control[1]}")


def plus(buttons):
    return "+".join(sorted(buttons)) or "none"


class Cleanups:
    """Guards, keepers and stacks of one layout, and the six checks."""

    def __init__(self, layout, stacks=None):
        """`stacks`: an earlier Cleanups of the same layout whose stacks still hold (the cleanup fix edits
        only lists the chains don't follow, so it reuses them instead of rebuilding)."""
        self.layout = layout
        self.base = layout.base
        self.chains = stacks.chains if stacks else Chains.of(layout)
        self.inv = Inventory.of(layout) if stacks else self.chains.inventory
        self.windows = set(always_on_layers(layout))
        self.omitted = sorted(t for t in layout.presets if t != self.base and self.inv.legacy_only(t))
        self.layers = [t for t in layout.presets if t != self.base and t not in self.omitted]
        self.adders = defaultdict(set)       # layer -> the layers whose bindings add it
        self._adding = defaultdict(list)     # layer -> the bindings that add it
        for t in self.inv.transitions:
            for op, target in t.ops:
                if op == "add_layer" and target != t.layer:
                    self.adders[target].add(t.layer)
                    self._adding[target].append(t)
        self.stateful = {t for t in self.layers if self._is_stateful(t)}
        self._keeper = {}
        self._present, self._above = (stacks._present, stacks._above) if stacks else ({}, {})

    # --- reading -------------------------------------------------------------------------

    def _releases(self, layer):
        """The controls whose Release removes `layer`, as names."""
        return {name(t.control) for t in self.inv.by_layer(layer)
                if t.role == "release" and ("remove_layer", layer) in t.ops}

    def _is_stateful(self, layer):
        """It outlives every binding that adds it, has no Always On action and no Release of its own."""
        adding = self._adding.get(layer)
        return bool(adding) and layer not in self.windows and not self._releases(layer) \
            and all(("remove_layer", t.layer) in t.ops for t in adding)

    def guard(self, host, source, inp):
        """The buttons whose chord sits beside this input's entries. Stick-deflection conditions are dropped."""
        activators = self.layout.active(host)[source]["inputs"][inp]["activators"]
        found = set()
        for kind, entry in entries(activators):
            condition = chord_condition(entry.get("settings", {})) if kind == "chord" else None
            if condition and condition.known:
                for group in condition.groups:
                    found |= {BUTTONS[c] for c in group if c in BUTTONS}
        return frozenset(found)

    def cleanups(self, host):
        """(binding, guard, removed layers) for each cleanup function of `host`."""
        for t in self.inv.by_layer(host):
            if t.role == "recovery":
                yield t, self.guard(host, t.source, t.input), frozenset(x for op, x in t.ops if op == "remove_layer")

    def keeper(self, layer):
        """(kind, buttons): what keeps `layer` alive. See the module text for the kinds."""
        if layer not in self._keeper:
            if layer in self.stateful:
                result = ("mode", frozenset())
            elif layer in self.windows:
                result = ("timer", frozenset())
            else:
                guards = set().union(*[g for _, g, _ in self.cleanups(layer)])
                released = self._releases(layer)
                buttons = released & NAMES
                keep = frozenset((buttons & guards) or buttons or (guards if not released else ()))
                if keep and keep <= THUMBS:
                    result = ("thumb", keep)
                elif keep:
                    result = ("button", keep)
                else:
                    result = ("inside" if released else "other", frozenset())
            self._keeper[layer] = result
        return self._keeper[layer]

    # --- stacks: the backward chains ------------------------------------------------------

    def reached(self, layer):
        return self.chains.reached(layer)

    def below(self, layer):
        return set().union(*self.chains.below(layer)) - {self.base, layer}

    def above(self, layer):
        if layer not in self._above:
            self._above[layer] = set(self.chains.above(layer))
        return self._above[layer]

    def present(self, layer):
        """Every layer that can be on the stack with `layer`, itself included."""
        if layer not in self._present:
            self._present[layer] = self.below(layer) | self.above(layer) | {layer}
        return self._present[layer]

    def leaves_alone(self, upper, host, source, inp):
        """True if `upper` on top of `host` still lets the host's binding on this input fire."""
        kind, layer, _, _ = resolve(self.layout, (host, upper), source, inp)
        return kind == "binding" and layer == host

    def inside(self, layer, guard, host, seen=()):
        """True if the guard's buttons are what keeps `layer` alive on the host's stack.

        A layer kept by a button is inside when all its buttons are in the guard. A layer
        that lives inside another layer's hold is inside when a layer that adds it, and is
        on the stack with the host, is inside. A window in between is passed through.
        """
        kind, keep = self.keeper(layer)
        if kind == "button":
            return keep <= guard
        if kind in ("mode", "thumb") or (kind == "timer" and not seen):
            return False
        present = self.present(host)
        return any(a == host or (a in present and self.inside(a, guard, host, seen + (layer,)))
                   for a in self.adders[layer] if a != self.base and a not in seen and a != layer)

    def same_interaction(self, upper, guard, host):
        kind, keep = self.keeper(upper)
        if kind == "button":
            return keep <= guard or (self.keeper(host)[0] == "button" and self.keeper(host)[1] <= keep)
        return self.inside(upper, guard, host)

    def is_clear(self, removed):
        """A deliberate clear: it removes every layer that isn't stateful."""
        return set(self.layers) - self.stateful <= set(removed)

    # --- the checks -----------------------------------------------------------------------

    def left(self, host, t, guard, removed):
        """[(layer, check)]: what this cleanup should remove and doesn't (rules 2 and 3)."""
        result = []
        for target in sorted(self.below(host) - removed - set(self.omitted)):
            if self.inside(target, guard, host):
                result.append((target, "left below"))
        for target in sorted(self.above(host) - removed - set(self.omitted)):
            if self.leaves_alone(target, host, t.source, t.input) and self.inside(target, guard, host):
                result.append((target, "left above"))
        return result

    def hiding(self, host, t, guard):
        """The layers of the same interaction on top of the host that hide this cleanup's input (rule 4)."""
        result = []
        for target in sorted(self.above(host) - set(self.omitted)):
            if self.leaves_alone(target, host, t.source, t.input) or target in self.windows \
                    or not self.same_interaction(target, guard, host):
                continue
            mine = [x for x in self.inv.by_layer(target) if x.control == t.control]
            if name(t.control) in self.keeper(target)[1] or any(x.role in ("recovery", "cancel") for x in mine):
                continue
            result.append(target)
        return result

    def unneeded(self, host, t):
        """{removed layer: (check, reason)} for the removals this binding shouldn't have (rules 1, 5 and 6)."""
        removed = [x for op, x in t.ops if op == "remove_layer"]
        if t.role not in LISTS or not removed or (t.role == "release" and self.is_clear(removed)):
            return {}
        present = self.present(host)
        guard = self.guard(host, t.source, t.input) if t.role == "recovery" else None
        on_touch = t.role == "release" and name(t.control) in THUMBS
        result = {}
        for target in dict.fromkeys(removed):
            if target == host or target in self.omitted:
                continue
            kind, keep = self.keeper(target) if target in self.layout.presets else ("other", frozenset())
            if t.role == "recovery" and kind in ("mode", "timer", "thumb"):
                result[target] = ("outside the guard", {
                    "mode": "a stateful layer", "timer": "a window: it always clears itself",
                    "thumb": "a stick-touch helper: only the stick-touch Release removes it"}[kind])
            elif t.role == "recovery" and target in present and not self.inside(target, guard, host):
                result[target] = ("outside the guard", f"kept by {plus(keep) if keep else 'something else'}")
            elif target not in present and not (on_touch and kind == "thumb"):
                result[target] = ("never there", "it can never be on the stack with this layer")
        return result

    def findings(self, only=None):
        """Every failing finding, as (check, layer, target, role, reason) -> the inputs it is on."""
        rows = {}

        def add(check, layer, target, role, reason, t, guard=None):
            row = rows.setdefault((check, layer, target, role, reason), {"inputs": [], "guards": set(), "bindings": []})
            row["inputs"].append(name(t.control))
            row["bindings"].append(t.describe())
            if guard is not None:
                row["guards"].add(plus(guard))

        for host in self.layers:
            if not self.reached(host) or (only and host not in only):
                continue
            found = list(self.cleanups(host))
            everywhere = frozenset().union(*[g for _, g, _ in found]) if found else frozenset()
            for t, guard, removed in found:
                for target, check in self.left(host, t, guard, removed):
                    reason = "under it, kept by the same button" if check == "left below" else \
                        "on top of it, kept by the same button, and it leaves this input alone"
                    add(check, host, target, "recovery", reason, t, guard)
                for target in self.hiding(host, t, guard):
                    add("hidden cleanup", target, host, "recovery",
                        "it binds this input and carries no cleanup for the layer below", t, guard)
                expected = everywhere - {name(t.control)}
                if guard != expected:
                    add("guard mismatch", host, None, "recovery",
                        f"the guard is {plus(guard)} here and {plus(expected)} on the layer's other cleanups", t, guard)
            for t in self.inv.by_layer(host):
                for target, (check, reason) in self.unneeded(host, t).items():
                    guard = self.guard(host, t.source, t.input) if check == "outside the guard" else None
                    add(check, host, target, t.role, reason, t, guard)
        return rows

    # --- hidden exits (R136) ----------------------------------------------------------------

    def exits(self, layer):
        """The inputs whose Release removes `layer`."""
        return sorted({t.control for t in self.inv.by_layer(layer)
                       if t.role == "release" and ("remove_layer", layer) in t.ops})

    def keeper_exits(self, layer, exits):
        """The exits on what keeps `layer` alive: its keeper's buttons, or every exit when no button keeps it."""
        kind, keep = self.keeper(layer)
        on_keeper = [e for e in exits if BUTTONS.get(e) in keep] if kind in ("button", "thumb") else []
        return on_keeper or list(exits)

    def touchpad_layers(self):
        """Layers that only trackpad bindings add."""
        return {t for t in self.layers if self._adding.get(t) and all(a.source in PADS for a in self._adding[t])}

    def _settled(self, full, upper, why):
        """The stack once the binding that added `upper` has run to the end: its array can add more on top."""
        for _, t in reversed(why.steps):
            if ("add_layer", upper) in t.ops:
                return apply_ops(full, t.ops[t.ops.index(("add_layer", upper)) + 1:], self.base)
        return full

    def covered_exits(self):
        """{(upper, lower): {"hidden", "side", "stack", "path"}}: every pair where a layer covers a lower layer's exit.

        `upper` is the layer that answers the exit's input instead of `lower`. `hidden` are the covered exits on
        the lower layer's keeper, `side` the covered exits that aren't. An exit the upper layer's binding also
        removes the lower layer on is carried, not covered.

        Two sources of stacks. The first is `above`: the upper layer's own chain, or one bystander under it.
        The second is every landing (chains.landings): one more adding binding on a stack the walk visited.
        Without it a layer that lands through a lower layer's binding is missed, as the Fallback Hold over
        the menu second-press layers was from 90.11 to 90.14.
        """
        pairs = {}
        exits = {lower: found for lower in self.layers if (found := self.exits(lower))}
        keeping = {lower: self.keeper_exits(lower, found) for lower, found in exits.items()}

        def cover(lower, full, path):
            for control in exits[lower]:
                kind, layer, acts, _ = resolve(self.layout, full, *control)
                if kind == "binding" and layer == lower:
                    continue
                if kind == "mode":
                    # Nobody answers: a source mode changed somewhere above. `resolve` names the top layer of
                    # that source; the layer that covers this exit is the first one above `lower` in another mode.
                    mine = self.layout.active(lower)[control[0]]["mode"]
                    layer = next((t for t in full[full.index(lower) + 1:]
                                  if (g := self.layout.active(t).get(control[0])) and g["mode"] != mine), layer)
                if acts and any(("remove_layer", lower) in self.layout.layer_ops(e) for _, e in entries(acts)):
                    continue                   # carried: the upper layer removes it there
                row = pairs.setdefault((layer, lower), {"hidden": [], "side": [], "stack": full, "path": path()})
                side = "hidden" if control in keeping[lower] else "side"
                if control not in row[side]:
                    row[side].append(control)

        for lower in exits:
            for upper, (stack, why) in self.chains.above(lower).items():
                full = self._settled(tuple(stack) + (upper,), upper, why)
                if lower in full:              # else the same binding removes it again
                    cover(lower, full, why.describe)
        visited = self.chains.stacks()
        for before, t, after in self.chains.landings():
            landed = [x for op, x in t.ops if op == "add_layer" and x in after and x not in before]
            if not landed:
                continue
            first = min(after.index(x) for x in landed)
            for lower in after[:first]:
                if lower in exits:
                    cover(lower, after, lambda: visited[before].describe() + ["landing: " + t.describe()])
        return pairs

    def _exit_rows(self, walk):
        """{layer number: [(control number, exit, on the keeper, the layer's mode on that source)]} for the walks."""
        rows = {}
        for lower in self.layers:
            found = self.exits(lower)
            if found:
                keeping = self.keeper_exits(lower, found)
                modes = {source: mode for source, mode, _ in walk.groups[walk.ident[lower]]}
                rows[walk.ident[lower]] = [(walk.control(*c), c, c in keeping, modes[c[0]]) for c in found]
        return rows

    @staticmethod
    def _adopt(walk, result):
        """Give `walk` the numbers of an engine's run."""
        walk.engine = result
        walk.settled, walk.stopped = result["settled"], result["stopped"] or None
        walk.presses, walk.longest = result["presses"], result["longest"]

    def _engine_exits(self, walk, rows, memory, progress, workers, **options):
        """The pairs and the walk's numbers from the compiled engine (native.py), in `covered_exits`' shape."""
        listed = [(lower, control, on_keeper) for lower, found in rows.items() for _, control, on_keeper, _ in found]
        numbers = iter(range(len(listed)))
        table = {lower: [(next(numbers), number, control[0], on_keeper, mine) for number, control, on_keeper, mine in found]
                 for lower, found in rows.items()}
        result = native.run(walk, table, memory=memory, progress=progress, threads=workers, **options)
        self._adopt(walk, result)
        pairs = {}
        for found in result["pairs"]:
            row = {"hidden": [], "side": [], "stack": walk.named(bytes(found["stack"])),
                   "path": native.describe(result, found["path"]), "cost": found.get("cost")}
            for number in found["exits"]:
                _, control, on_keeper = listed[number]
                row["hidden" if on_keeper else "side"].append(control)
            pairs[(walk.titles[found["who"]], walk.titles[found["lower"]])] = row
        return pairs

    def walked_exits(self, max_layers=MAX_SIMULTANEOUS, memory=None, progress=None, workers=None, engine=None):
        """(pairs, walk): `covered_exits` read from every stack with at most `max_layers` layers on at once.

        The pairs have the same shape. The stacks are the capped walk's (walk.py): every order, any number of
        presses, and every layer of every stack is tested, so nothing depends on a chain, an arrival or a
        bystander. The example stack of a pair has a shortest path. `engine`: True for the compiled engine
        (native.py), False for the Python walk; by default the engine when it can be built.
        """
        walk = Walk(self.layout, max_layers, self.inv)
        rows = self._exit_rows(walk)
        if engine or (engine is None and native.available()):
            return self._engine_exits(walk, rows, memory, progress, workers, max_layers=max_layers), walk
        pairs = {}

        def test(stack, found, stops):
            """(covering layer, lower layer, exit, whether it is on the keeper) for every lost exit in the stack."""
            result = []
            for at, lower in enumerate(stack):
                for number, control, on_keeper, mine in rows.get(lower, ()):
                    who = found.get(number)
                    if who == lower:
                        continue
                    if who is not None:
                        if lower in walk.removes.get((who, number), ()):
                            continue               # carried: the upper layer removes it there
                    else:
                        kind, top = stops.get(control[0], ("mode", stack[-1]))
                        # A disabled source is charged to its layer; a mode change to the first layer above
                        # `lower` in another mode, as in `covered_exits`.
                        who = top if kind == "disabled" else next(
                            (x for x in stack[at + 1:] for source, mode, _ in walk.groups[x]
                             if source == control[0] and mode != mine), top)
                    result.append((who, lower, control, on_keeper))
            return result

        def collect(item, stack):
            who, lower, control, on_keeper = item
            row = pairs.get((who, lower))
            if row is None:
                row = pairs[(who, lower)] = {"hidden": [], "side": [], "stack": stack}
            side = "hidden" if on_keeper else "side"
            if control not in row[side]:
                row[side].append(control)

        walk.run(test, collect, memory, progress, workers)
        named = {}
        for (who, lower), row in pairs.items():
            named[(walk.titles[who], walk.titles[lower])] = {
                "hidden": row["hidden"], "side": row["side"], "stack": walk.named(row["stack"]),
                "path": walk.path(row["stack"])}
        return named, walk

    def chained_exits(self, extras, memory=None, progress=None, workers=None):
        """(pairs, walk): the chain walk with `extras` extra presses per chain, every stack tested.

        The stacks are the chains' own (chains.py with `arrivals=extras`): one layer's chain, with up to that
        many arrivals, and no bystander. Every stack is tested, and every stack one landing past it. Only the
        compiled engines run this (native.py); `walk.count` is the number of distinct stacks.

        Up to `PATHS_UP_TO` extra presses one engine does it all and keeps a shortest path to every stack.
        Past that the chain engine walks (a quarter of the memory, no paths), and the example stack and path
        of each pair come from a second, small run at `PATHS_UP_TO`. A pair that only shows with more extra
        presses keeps the chain engine's example, with no path.
        """
        walk = Walk(self.layout, None, self.inv)
        rows = self._exit_rows(walk)
        if extras <= PATHS_UP_TO:
            return self._engine_exits(walk, rows, memory, progress, workers, extras=extras, landings=True), walk
        pairs = self._engine_exits(walk, rows, memory, progress, workers, extras=extras, landings=True,
                                   program=native.CHAIN)
        whole = walk.engine
        shown = self._engine_exits(walk, rows, memory, None, workers, extras=PATHS_UP_TO, landings=True)
        self._adopt(walk, whole)
        for pair, row in pairs.items():
            if pair in shown:
                row["stack"], row["path"] = shown[pair]["stack"], shown[pair]["path"]
            else:
                row["path"] = [f"no path kept: this stack needs {row['cost']} extra presses"]
        return pairs, walk

    def unreached_by_cleanup(self):
        """Button-kept layers that have no cleanup function and that no cleanup function removes."""
        covered = set()
        for host in self.layers:
            for _, _, removed in self.cleanups(host):
                covered |= removed
        return sorted(t for t in self.layers if self.reached(t) and self.keeper(t)[0] == "button" and t not in covered)


def kept(config, variant):
    """{(layer, removed layer): why} from the config's `cleanups.keep`, which the exceptions register fills (R132)."""
    mapping = config.get("variants", {}).get(variant, {})
    result = {}
    for decision in config.get("cleanups", {}).get("keep", []):
        if not decision.get("why"):
            raise ValueError(f"a kept removal needs a why: {decision}")
        for layer in decision["layers"]:
            for target in decision["removes"]:
                result[(map_title(layer, mapping), map_title(target, mapping))] = decision["why"]
    return result


def audit(data, config=None, only=None, changed=None, walk=None, memory=None, progress=None, extras=None, engine=None):
    """The Cleanup audit's report for one layout: findings, kept removals, stale decisions."""
    return run(data, config, only, changed=changed, walk=walk, memory=memory, progress=progress, extras=extras,
               engine=engine)[0]


def run(data, config=None, only=None, stacks=None, changed=None, walk=None, memory=None, progress=None, extras=None,
        engine=None):
    """(report, Cleanups). `stacks`: an earlier Cleanups whose stacks still hold for `data`.

    `changed`: the layers that are new or changed since the last snapshot (steam_layout/changes.py).
    `walk`: read the hidden exits from every stack with at most that many layers on at once (walk.py),
    not from the chain stacks. `memory` (bytes) stops that walk; the report is then not ok.
    `extras`: read them from the chain walk with that many extra presses per chain, every stack tested
    (`chained_exits`; the compiled engine only). `engine`: False keeps `walk` in Python."""
    from .model import Layout
    layout = Layout(data)
    config = config or {}
    variant = "alternative" if "alternative" in layout.cm.get("title", "") else "default"
    cleanups = Cleanups(layout, stacks)
    decided = kept(config, variant)
    used, findings, keeping = set(), [], []
    for (check, layer, target, role, reason), row in cleanups.findings(only).items():
        entry = {"check": check, "layer": layer, "target": target, "kind": ROLE[role], "reason": reason,
                 "inputs": sorted(set(row["inputs"])), "bindings": len(row["bindings"]),
                 "guard": sorted(row["guards"]), "example": row["bindings"][0]}
        if target is not None:
            entry["keeper"] = " ".join(filter(None, [cleanups.keeper(target)[0], plus(cleanups.keeper(target)[1])
                                                    if cleanups.keeper(target)[1] else ""])) \
                if target in layout.presets else "unknown layer"
        if check == "never there" and (layer, target) in decided:
            used.add((layer, target))
            keeping.append({**entry, "why": decided[(layer, target)]})
        else:
            findings.append(entry)
    touchpad = config.get("cleanups", {}).get("touchpad_exits")
    mapping = config.get("variants", {}).get(variant, {})
    accepted = {(map_title(a["upper"], mapping), map_title(a["lower"], mapping)): a["why"]
                for a in config.get("cleanups", {}).get("accepted_exits", [])}
    reviewed = set()
    pads, excepted, information = cleanups.touchpad_layers(), [], []
    walked = None
    if extras is not None:
        covered, walked = cleanups.chained_exits(extras, memory, progress)
    elif walk:
        covered, walked = cleanups.walked_exits(walk, memory, progress, engine=engine)
    else:
        covered = cleanups.covered_exits()
    for (upper, lower), row in covered.items():
        if only and upper not in only and lower not in only:
            continue
        on_keeper = bool(row["hidden"])
        inputs = row["hidden"] or row["side"]
        keeper = cleanups.keeper(lower)
        entry = {"check": "hidden exit", "layer": upper, "target": lower,
                 "kind": "window" if upper in cleanups.windows else "layer",
                 "reason": "it answers the input of the lower layer's exit and doesn't remove the lower layer there",
                 "inputs": sorted(name(c) for c in inputs), "bindings": len(inputs), "guard": [],
                 "example": " > ".join(row["stack"]), "path": row["path"],
                 "keeper": " ".join(filter(None, [keeper[0], plus(keeper[1]) if keeper[1] else ""]))}
        if touchpad and (upper in pads or lower in pads or any(source in PADS for source, _ in inputs)):
            excepted.append({**entry, "on_keeper": on_keeper, "why": touchpad})
        elif on_keeper:
            findings.append(entry)
        elif (upper, lower) in accepted:
            reviewed.add((upper, lower))
            excepted.append({**entry, "on_keeper": False, "why": accepted[(upper, lower)]})
        elif {upper, lower} & set(changed or ()):
            findings.append({**entry, "check": "exit to review",
                             "reason": "it covers an exit that isn't on the keeper, on a layer that changed"})
        else:
            information.append(entry)
    order = {check: i for i, check in enumerate(CHECKS)}
    findings.sort(key=lambda f: (order[f["check"]], f["layer"], f["target"] or "", f["kind"]))
    counts = {check: {"findings": sum(1 for f in findings if f["check"] == check),
                      "bindings": sum(f["bindings"] for f in findings if f["check"] == check)} for check in CHECKS}
    hosts = [t for t in cleanups.layers if any(True for _ in cleanups.cleanups(t))]
    return {"layout": {"title": layout.cm.get("title"), "variant": variant},
            "ok": not findings and (walked is None or walked.settled), "findings": findings, "kept": keeping,
            "counts": counts,
            "walk": None if walked is None else {"layers": walked.max_layers, "extras": extras,
                                                 "stacks": walked.count, "settled": walked.settled,
                                                 "presses": walked.presses, "longest": walked.longest,
                                                 "stopped": walked.stopped, "engine": bool(walked.engine)},
            "excepted": excepted, "information": {"hidden exit": information},
            "stale_decisions": [] if only else [f"{layer} removes {target}" for layer, target in sorted(set(decided) - used)]
            + ([TOUCHPAD_STALE] if touchpad and not any(e["why"] == touchpad for e in excepted) else [])
            + [f"{upper} over {lower}" for upper, lower in sorted(set(accepted) - reviewed)],
            "omitted": cleanups.omitted,
            "summary": {"layers": len(cleanups.layers), "layers_with_cleanup": len(hosts),
                        "cleanup_functions": sum(1 for t in hosts for _ in cleanups.cleanups(t)),
                        "stateful": sorted(cleanups.stateful)},
            "no_cleanup_reaches": [] if only else cleanups.unreached_by_cleanup()}, cleanups
