"""Remove dead groups from a Steam Input layout JSON.

Steam never runs these, but they hide stale bindings and make audits noisy:

1. Plain-inactive source slots: `group_source_bindings` entries whose state is
   exactly `inactive`. Steam keeps these to remember an alternate source mode.
2. Unreferenced groups: groups that no preset slot and no `mode_shift` binding
   references after step 1.

Kept: `active` slots (including `disabled`-mode groups, which switch a source
off on purpose), every slot whose state contains `modeshift`, and any group a
`mode_shift` binding targets. Group IDs are never renumbered, and layers,
presets, `actions` and `action_layers` are never touched, so runtime layer IDs
cannot shift. Works with numeric IDs or readable title tokens. Idempotent.
"""

import json
import re

MODE_SHIFT = re.compile(r"mode_shift \S+ (\d+)")


def mode_shift_targets(cm):
    return set(MODE_SHIFT.findall(json.dumps(cm.get("group", []))))


def prune(data):
    """Prune `data` in place and return a report of what was removed."""
    cm = data["controller_mappings"]
    targets = mode_shift_targets(cm)
    titles = {k: v.get("title", k) for k, v in {**cm.get("actions", {}), **cm.get("action_layers", {})}.items()}
    removed_slots = []
    for preset in cm.get("preset", []):
        bindings = preset.get("group_source_bindings", {})
        for gid, state in list(bindings.items()):
            if state.split(" ", 1)[-1] == "inactive" and gid not in targets:
                removed_slots.append({"layer": titles.get(preset["name"], preset["name"]),
                                      "group": gid, "slot": state})
                del bindings[gid]
    referenced = {gid for p in cm.get("preset", []) for gid in p.get("group_source_bindings", {})}
    referenced |= mode_shift_targets(cm)
    removed_groups = [g["id"] for g in cm.get("group", []) if g["id"] not in referenced]
    dead = set(removed_groups)
    cm["group"] = [g for g in cm.get("group", []) if g["id"] not in dead]
    return {"removed_inactive_slots": removed_slots, "removed_groups": removed_groups,
            "remaining_groups": len(cm["group"]), "mode_shift_targets": sorted(targets, key=int)}
