"""The three questions for one layer, and what its exits clean up.

For a layer X (resources/Layer Definition of Done.md, sections 7 and 8):

1. what is inherited: the inputs X doesn't bind that a layer below provides
2. what each inherited input does, and which layer it comes from
3. what can be below X and above X

The stacks come from the backward chains (chains.py), so every answer carries
the bindings that built it. The inherited inputs reuse the Flow audit's lookup
(flow_inheritance.inspect_target).

The cleanup lists compare each binding of X that removes layers with the layers
that can be on the stack with X. They are a report, not a check: whether a
layer left behind is a problem depends on its type (a parent or another
owner's layer is not X's to remove). A layer above X that binds the exit's own
input is listed as intercepting it: the exit can't fire while that layer is on
top. Stale layers left by a missed release are not modelled.

Plan: plans/2026-10-01-backward-chain-audit.md, step 6.
"""
from .chains import Chains
from .flow_inheritance import inspect_target
from .model import bindings, defined


def explain(why):
    return why.describe() + ([f"bystander: {why.bystander}"] if why.bystander else [])


def report(layout, title):
    if title not in layout.presets:
        raise ValueError(f"unknown layer: {title}")
    chains = Chains.of(layout)
    result = {"layer": title, "reached": chains.reached(title),
              "below": {"layers": {}, "stacks": []}, "above": {}, "inherited": [], "exits": []}
    if not result["reached"]:
        return result
    lowers = {} if title == layout.base else chains.below(title)
    for stack in sorted(lowers, key=lambda s: (len(s), s)):
        reason = explain(lowers[stack])
        result["below"]["stacks"].append({"stack": list(stack), "reason": reason})
        for layer in stack:
            result["below"]["layers"].setdefault(layer, reason)
    above = chains.above(title)
    result["above"] = {layer: {"stack": list(stack), "reason": explain(why)} for layer, (stack, why) in above.items()}
    for row in inspect_target(layout, title, list(lowers)):
        providers = [{"layers": sorted(v.providers), "bindings": list(bindings(v.activators)),
                      "changes_layers": v.changes_layers} for v in row.variants if v.kind == "binding"]
        if row.status == "inherits" and providers:
            result["inherited"].append({"source": row.source, "input": row.name, "providers": providers})
    present_below = set(result["below"]["layers"]) - {layout.base}
    present_above = set(above)
    for t in chains.inventory.by_layer(title):
        removes = list(dict.fromkeys(target for op, target in t.ops if op == "remove_layer"))
        if not removes:
            continue
        removed = set(removes) - {title}
        intercepting = sorted(z for z in present_above if defined(layout.active(z).get(t.source), t.input))
        result["exits"].append({
            "binding": t.describe(), "input": f"{t.source}/{t.input}", "role": t.role,
            "removes": removes, "removes_itself": title in removes,
            "present_and_removed": sorted(removed & (present_below | present_above)),
            "present_not_removed": {"below": sorted(present_below - removed),
                                    "above": sorted(present_above - removed - set(intercepting))},
            "intercepted_by": intercepting,
            "removed_never_present": sorted(removed - present_below - present_above)})
    return result
