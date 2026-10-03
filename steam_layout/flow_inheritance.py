"""What a layer inherits on each intended lower stack.

For a target and every lower stack the backward chains put under it
(chains.Chains.lineage), each input resolves to the nearest lower
definition, walking down to the action set: an inherited binding, a disabled
source, or nothing. Definitions are compared as normalized JSON (activators,
settings and command order), so the same binding from two owners is one
variant. The target's own handling is reported too: inherits, clears,
replaces or disables.

Each input whose lower bindings differ between stacks gets a label. They are
information here. The Flow audit fails on the first two where the layer changed
since the last snapshot (R139), until each is fixed or accepted:

    varies     the target inherits, and two or more distinct non-Base bindings
               reach it
    review     the target inherits one non-Base binding on some flows and a
               different Base fallback (or nothing) on others
    replaced   the target replaces an input that has differing bindings below
    satisfied  the target already clears or disables an input with differing
               bindings below

Inheritance is the default for an ordinary layer. Blocking is only required
under a layer with an Always On action, when one of the bindings it could
inherit is a layer command: clear the input if more than one keybind is
possible, otherwise override it with that keybind (author, 2026-10-01). The
Window audit (inheritance.py) checks that. Until 2026-10-01 "varies" was called
"conflict" and failed the Flow audit for every layer, which misread that rule.

A group in a different source mode, in the target or below it, blocks
inheritance (author rule, 2026-10-01): those inputs resolve to "blocked by a
mode change", never to the lower mode's binding.
"""
import json
from dataclasses import dataclass, field

from .flow_model import is_clear, resolve
from .inheritance import changes_layers
from .model import defined


def nearest(layout, lower, source, name, mode=None, mode_from=None):
    """(kind, layer, activators, mode) for the nearest lower definition.

    kind is "binding", "disabled", "mode" (a group in a different source mode
    blocks inheritance) or "none". `mode` is the target's own mode, if it has a
    group for the source.
    """
    return resolve(layout, lower, source, name, mode, mode_from)


def target_status(layout, target, source, name):
    group = layout.active(target).get(source)
    if group is None:
        return "inherits", None
    if group["mode"] == "disabled":
        return "disables", group["mode"]
    if defined(group, name):
        return ("clears" if is_clear(group["inputs"][name]["activators"]) else "replaces"), group["mode"]
    return "inherits", group["mode"]


@dataclass
class Variant:
    key: str
    kind: str
    activators: dict
    providers: set = field(default_factory=set)
    lowers: list = field(default_factory=list)   # lower stacks showing this variant
    base: bool = False                            # every provider is the action set
    changes_layers: str = None

    def label(self):
        if self.kind == "none":
            return "nothing"
        if self.kind == "disabled":
            return "disabled source in " + ", ".join(sorted(self.providers))
        if self.kind == "mode":
            return "blocked by a mode change in " + ", ".join(sorted(self.providers))
        return ", ".join(sorted(self.providers))


@dataclass
class InputReport:
    source: str
    name: str
    status: str
    variants: list
    finding: str = None
    unsupported: str = None

    @property
    def non_base(self):
        return [v for v in self.variants if v.kind == "binding" and not v.base]


def inspect_input(layout, target, lowers, source, name):
    status, own_mode = target_status(layout, target, source, name)
    variants = {}
    lookup_mode = own_mode if own_mode not in (None, "disabled") else None
    for lower in lowers:
        kind, layer, activators, _ = nearest(layout, lower, source, name, lookup_mode, target)
        key = kind if kind != "binding" else json.dumps(activators, sort_keys=True)
        v = variants.setdefault(key, Variant(key, kind, activators))
        if layer:
            v.providers.add(layer)
        v.lowers.append(lower)
    for v in variants.values():
        v.base = v.kind == "binding" and v.providers == {layout.base}
        v.changes_layers = changes_layers(layout, v.activators) if v.kind == "binding" else None
    ordered = sorted(variants.values(), key=lambda v: (v.kind != "binding", v.base, v.label()))
    if status == "inherits" and all(v.kind == "mode" for v in ordered):
        status = "blocks by mode"
    report = InputReport(source, name, status, ordered)
    competing = len(report.non_base) >= 2
    if status == "inherits":
        if competing:
            report.finding = "varies"
        elif report.non_base and len(ordered) > 1:
            report.finding = "review"
    elif status == "replaces" and competing:
        report.finding = "replaced"
    elif status in ("clears", "disables") and len(ordered) > 1:
        report.finding = "satisfied"
    return report


def inspect_target(layout, target, lowers):
    """InputReports for every input defined anywhere in the lower stacks or the target."""
    keys = {}
    for title in [t for lower in lowers for t in lower] + [target]:
        for source, group in layout.active(title).items():
            for name in group.get("inputs", {}):
                keys.setdefault((source, name), None)
    return [inspect_input(layout, target, lowers, source, name) for source, name in keys]
