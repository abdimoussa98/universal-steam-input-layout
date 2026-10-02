"""Deprecated 2026-10-01: the cover check on the family walk. The audit now uses covers.py, on chains.

Kept for reference; tests/test_covers.py checks both give the same result on the 90.9 layouts.

Focused checks for lightweight covers, from their intended owners and overlays.

Plan section 6. A cover (Layer Definition of Done section 5) is only ever added
on top of an owner and inherits everything it doesn't define from it. Its
owners are the layers it is placed on: the layer directly below it right after
each add in the intended flows (a window that removes itself and adds a cover
hands it to the layer under the window). In every flow state with the cover:

    outlives owners      no owner is present: nothing owns or recovers it
    below its owner      an owner sits above the cover and none below: the
                         cover can't override the owner's inputs
    intervening layer    an input the cover inherits comes from a non-owner
                         layer between the cover and its nearest owner

The checks above are findings. Also listed, for review only: the layers seen
above each cover and which of the cover's own controls they take over, with
whether that binding also removes the cover (Modifier 2 deliberately sits over
the single covers, for example).

`covers.allow` in the flow rules accepts named checks for a cover with a
reason; accepted findings stay listed.
"""
from .flow_inheritance import nearest
from .model import defined


def owners(results, cover):
    """{owner layer: (family, state)}: the layer directly below `cover` right after each add."""
    found = {}
    for name, result in results.items():
        for state, entry in result.states.items():
            stack = state[0]
            if not entry or cover not in stack or cover in entry[0][0]:
                continue
            i = stack.index(cover)
            if i > 0:
                found.setdefault(stack[i - 1], (name, state))
    return found


def _removes(layout, activators, cover):
    return any(("remove_layer", cover) in layout.layer_ops(e)
               for value in activators.values() for e in (value if isinstance(value, list) else [value]))


def check_cover(layout, results, cover, allowed=None):
    allowed = allowed or {}
    owned = owners(results, cover)
    findings, above = {}, {}

    def note(check, detail, family, state):
        """One finding per check and detail, with its first example and a stack count."""
        found = findings.get((check, detail))
        if found:
            found["stacks"].add(state[0])
            return
        _, steps = results[family].path(state)
        findings[(check, detail)] = {"cover": cover, "check": check, "detail": detail, "family": family,
                                     "stack": list(state[0]), "allowed": allowed.get(check), "stacks": {state[0]},
                                     "path": [s.describe() for s in steps if s.fired or s.layer]}

    own = {(source, name) for source, group in layout.active(cover).items()
           for name in group.get("inputs", {}) if defined(group, name)}
    for family, result in results.items():
        for state in result.states:
            stack = state[0]
            if cover not in stack:
                continue
            i = stack.index(cover)
            below, over = stack[:i], stack[i + 1:]
            under = [t for t in below if t in owned]
            if not under:
                top = [t for t in over if t in owned]
                if top:
                    note("below its owner", f"{top[-1]} is above the cover", family, state)
                else:
                    note("outlives owners", "no owner is present", family, state)
                continue
            k = below.index(under[-1])
            for title in below[k + 1:]:
                for source, group in layout.active(title).items():
                    for name in group.get("inputs", {}):
                        if (source, name) in own or not defined(group, name):
                            continue
                        if nearest(layout, below, source, name)[1] == title:
                            note("intervening layer", f"{source}/{name} comes from {title}, "
                                 f"between the cover and its owner {under[-1]}", family, state)
            for upper in over:
                for source, name in own:
                    group = layout.active(upper).get(source)
                    if not group:
                        continue
                    if group["mode"] == "disabled" or defined(group, name):
                        removes = group["mode"] != "disabled" and _removes(
                            layout, group["inputs"][name]["activators"], cover)
                        above.setdefault(upper, {})[f"{source}/{name}"] = removes
    for f in findings.values():
        f["stacks"] = len(f["stacks"])
    return {"cover": cover, "owners": sorted(owned), "findings": list(findings.values()),
            "above": {upper: dict(sorted(c.items())) for upper, c in sorted(above.items())}}
