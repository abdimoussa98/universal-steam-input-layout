"""Block every derived layer-API route under the Always On Double Tap windows.

Author rule, 2026-09-30: trace every stack a Double Tap window can be applied
on. If any of them has a layer command under an input the window leaves open,
the window must block that input for its lifetime. **Replace** it with the
underlying output only when that output is identical in every stack (always E,
always middle mouse); otherwise **clear** it, because a hard-coded replacement
would be wrong somewhere.

This applies audit_inheritance.py's `blocks_needed` to the Always On windows,
using the backward-chain stacks (steam_layout/chains.py: no depth cap, no
config) and the decisions in traced_stacks.json. `depth` adds the older
depth-limited search (deprecated 2026-10-01). Idempotent: a second run finds
nothing to block. Works with numeric IDs or title tokens.
"""
import copy
import json
from pathlib import Path

from ..inheritance import audit
from ..model import Layout, always_on_layers

ROOT = Path(__file__).resolve().parents[2]

EMPTY = "controller_action empty_binding, , "


def fix(data, config=None, depth=0):
    config = config if config is not None else json.loads((ROOT / "traced_stacks.json").read_text())
    report = audit(data, config, depth)
    layout = Layout(data)
    windows = set(always_on_layers(layout))
    changed = []
    for title, row in report["targets"].items():
        if title not in windows:
            continue
        for need in row["blocks_needed"]:
            group = layout.active(title).get(need["source"])
            if group is None or group["mode"] == "disabled":
                raise ValueError(f"{title}: no active {need['source']} group to block {need['input']} in")
            activators = (copy.deepcopy(need["activators"]) if need["action"] == "replace"
                          else {"Full_Press": {"bindings": {"binding": EMPTY}}})
            group.setdefault("inputs", {})[need["input"]] = {"activators": activators, "disabled_activators": {}}
            changed.append(f"{title} / {need['source']}/{need['input']} ({need['action']})")
    return {"changed": changed}
