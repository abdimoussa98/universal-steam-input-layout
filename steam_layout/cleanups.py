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

Left out, by the author's choice: layers that only `hold_layer` adds. They are
neither audited nor counted as removed layers.
"""
from collections import defaultdict

from .chains import Chains
from .flow_model import Inventory, chord_condition, resolve
from .model import always_on_layers, entries, map_title

BUTTONS = {("switch", "left_bumper"): "LB", ("switch", "right_bumper"): "RB",
           ("switch", "button_escape"): "Start", ("switch", "button_menu"): "Select",
           ("joystick", "touch"): "LSt", ("right_joystick", "touch"): "RSt",
           ("joystick", "click"): "L3", ("right_joystick", "click"): "R3",
           ("left_trigger", "click"): "LT", ("right_trigger", "click"): "RT",
           ("left_trigger", "edge"): "LT", ("right_trigger", "edge"): "RT",
           ("left_trackpad", "touch"): "LTP", ("right_trackpad", "touch"): "RTP"}
THUMBS = frozenset({"LSt", "RSt"})
NAMES = frozenset(BUTTONS.values())
CHECKS = ("outside the guard", "left below", "left above", "hidden cleanup", "never there", "guard mismatch")
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

    def unreached_by_cleanup(self):
        """Button-kept layers that have no cleanup function and that no cleanup function removes."""
        covered = set()
        for host in self.layers:
            for _, _, removed in self.cleanups(host):
                covered |= removed
        return sorted(t for t in self.layers if self.reached(t) and self.keeper(t)[0] == "button" and t not in covered)


def kept(config, variant):
    """{(layer, removed layer): why} from the config's `cleanups.keep` decisions."""
    mapping = config.get("variants", {}).get(variant, {})
    result = {}
    for decision in config.get("cleanups", {}).get("keep", []):
        if not decision.get("why"):
            raise ValueError(f"a kept removal needs a why: {decision}")
        for layer in decision["layers"]:
            for target in decision["removes"]:
                result[(map_title(layer, mapping), map_title(target, mapping))] = decision["why"]
    return result


def audit(data, config=None, only=None):
    """The Cleanup audit's report for one layout: findings, kept removals, stale decisions."""
    return run(data, config, only)[0]


def run(data, config=None, only=None, stacks=None):
    """(report, Cleanups). `stacks`: an earlier Cleanups whose stacks still hold for `data`."""
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
    order = {check: i for i, check in enumerate(CHECKS)}
    findings.sort(key=lambda f: (order[f["check"]], f["layer"], f["target"] or "", f["kind"]))
    counts = {check: {"findings": sum(1 for f in findings if f["check"] == check),
                      "bindings": sum(f["bindings"] for f in findings if f["check"] == check)} for check in CHECKS}
    hosts = [t for t in cleanups.layers if any(True for _ in cleanups.cleanups(t))]
    return {"layout": {"title": layout.cm.get("title"), "variant": variant},
            "ok": not findings, "findings": findings, "kept": keeping, "counts": counts,
            "stale_decisions": [] if only else [f"{layer} removes {target}" for layer, target in sorted(set(decided) - used)],
            "omitted": cleanups.omitted,
            "summary": {"layers": len(cleanups.layers), "layers_with_cleanup": len(hosts),
                        "cleanup_functions": sum(1 for t in hosts for _ in cleanups.cleanups(t)),
                        "stateful": sorted(cleanups.stateful)},
            "no_cleanup_reaches": [] if only else cleanups.unreached_by_cleanup()}, cleanups
