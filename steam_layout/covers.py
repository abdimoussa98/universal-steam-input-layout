"""Focused checks for lightweight covers, on backward chains.

A cover (Layer Definition of Done section 5) is only ever added on top of an
owner and inherits everything it doesn't define from it. Its owners are the
layers it is placed on: the layer directly below it right after each add. In
every stack the family view visits with the cover in it:

    outlives owners      no owner is present: nothing owns or recovers it
    below its owner      an owner sits above the cover and none below: the
                         cover can't override the owner's inputs
    intervening layer    an input the cover inherits comes from a non-owner
                         layer between the cover and its nearest owner

The checks above are findings. Also listed, for review only: the layers seen
above each cover and which of the cover's own controls they take over, with
whether that binding also removes the cover (Modifier 2 deliberately sits over
the single covers, for example).

The stacks come from the family view of the chains (chains.py): chains start
from each declared context (Base, and Base with Gyro), and only layers the
chain itself added may arrive mid-chain. That keeps each cover with its own
family, as the family walk this replaced did (deprecated 2026-10-01, now in
archived/depth-search-and-family-walk/ with the test that both gave the same
result on the 90.9 layouts).

An exception to R144 in the exceptions register (exceptions.py) accepts named
checks for a cover with a reason; accepted findings stay listed.
"""
import json
from pathlib import Path

from .chains import Chains
from .flow_model import resolve
from .model import defined, map_title

RULES = Path(__file__).with_name("flow_config.json")


def load_rules(path=None):
    """The rules file, with the exceptions register expanded into the sections the audits read."""
    from .exceptions import load_config
    return load_config(path or RULES)


def family_view(layout, rules=None):
    """The chains the cover check runs on, starting from the contexts the rules declare."""
    rules = rules or {}
    variant = "alternative" if "alternative" in layout.cm.get("title", "") else "default"
    mapping = rules.get("variants", {}).get(variant, {})
    contexts = [tuple(map_title(t, mapping) for t in context) for context in rules.get("contexts", [])]
    return Chains(layout, contexts=[c for c in contexts if len(c) > 1], foreign_arrivals=False)


def owners(view, cover):
    """{owner layer: Why}: the layer directly below `cover` right after each add."""
    found = {}
    for stack, why in view.added(cover).items():
        index = stack.index(cover)
        if index > 0:
            found.setdefault(stack[index - 1], why)
    return found


def _removes(layout, activators, cover):
    return any(("remove_layer", cover) in layout.layer_ops(e)
               for value in activators.values() for e in (value if isinstance(value, list) else [value]))


def check_cover(layout, view, cover, allowed=None):
    allowed = allowed or {}
    owned = owners(view, cover)
    findings, above = {}, {}

    def note(check, detail, stack, why):
        """One finding per check and detail, with its first example and a stack count."""
        found = findings.get((check, detail))
        if found:
            found["stacks"].add(stack)
            return
        findings[(check, detail)] = {"cover": cover, "check": check, "detail": detail, "stack": list(stack),
                                     "allowed": allowed.get(check), "stacks": {stack}, "path": why.describe()}

    own = {(source, name) for source, group in layout.active(cover).items()
           for name in group.get("inputs", {}) if defined(group, name)}
    for stack, why in view.stacks().items():
        if cover not in stack:
            continue
        i = stack.index(cover)
        below, over = stack[:i], stack[i + 1:]
        under = [t for t in below if t in owned]
        if not under:
            top = [t for t in over if t in owned]
            if top:
                note("below its owner", f"{top[-1]} is above the cover", stack, why)
            else:
                note("outlives owners", "no owner is present", stack, why)
            continue
        k = below.index(under[-1])
        for title in below[k + 1:]:
            for source, group in layout.active(title).items():
                for name in group.get("inputs", {}):
                    if (source, name) in own or not defined(group, name):
                        continue
                    if resolve(layout, below, source, name)[1] == title:
                        note("intervening layer", f"{source}/{name} comes from {title}, "
                             f"between the cover and its owner {under[-1]}", stack, why)
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
