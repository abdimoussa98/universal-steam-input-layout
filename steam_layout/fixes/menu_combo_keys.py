"""Type Backspace/Enter straight from the menu chords; drop the two overlay layers.

Author decision, 2026-10-01: `Menu Left: Backspace` and `Menu Right: Enter`
are not needed. The menu whose button is held owns the combo, like every other
Fn key: when that menu's family goes, a still-held second button falls through
to Base. The overlays existed to hold that second button until its release
(plans/2026-09-27-split-menu-entry-point.md, problem 4); the cost of removing
them is the documented stray Escape/Tab when the first button is lifted first
and the second is released within 300 ms.

For each overlay, in title form:
- every `add_layer <overlay>` becomes the overlay's own key command, in place.
  So the Fn chord is `key_press BACKSPACE` again (its pre-split shape), and
  the Entry Point's early chord adds Fn, then types the key.
- every `remove_layer <overlay>` subcommand is dropped.
- the layer, its preset and the groups only it used are deleted; preset ids
  are renumbered. Later layers' runtime IDs shift, so references are converted
  through titles and back.

Works with numeric runtime IDs or title tokens. Idempotent: a layout without
the overlays is left untouched.
"""
import json
import re

from convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

OVERLAYS = ("Menu Left: Backspace", "Menu Right: Enter")
EMPTY = "controller_action empty_binding, , "


def _command(overlay, verb):
    return re.compile(r"controller_action %s_layer \{\{(?:[^:}]+::)?%s\}\} \d+ \d+, , " % (verb, re.escape(overlay)))


def fix(data):
    present = [v["title"] for v in data["controller_mappings"]["action_layers"].values() if v["title"] in OVERLAYS]
    if not present:
        return {"changed": []}
    raw = json.dumps(data)
    numeric = "{{" not in raw
    readable, _ = ids_to_titles(raw, generate_lookup(data))
    new = json.loads(readable)
    cm = new["controller_mappings"]
    groups = {g["id"]: g for g in cm["group"]}
    changed = []
    for overlay in present:
        key = next(k for k, v in cm["action_layers"].items() if v["title"] == overlay)
        preset = next(p for p in cm["preset"] if p["name"] == key)
        own = set(preset["group_source_bindings"])
        outputs = [b for gid in own for value in groups[gid].get("inputs", {}).values()
                   for entry in _entries(value) for b in _commands(entry) if b.startswith("key_press ")]
        if len(set(outputs)) != 1:
            raise ValueError(f"{overlay}: expected one key output, found {outputs}")
        add, remove = _command(overlay, "add"), _command(overlay, "remove")
        for group in cm["group"]:
            if group["id"] in own:
                continue
            for name, value in group.get("inputs", {}).items():
                for entry in _entries(value):
                    before = _commands(entry)
                    after = [outputs[0] if add.fullmatch(c) else c for c in before if not remove.fullmatch(c)]
                    if after != before:
                        entry["bindings"]["binding"] = after if len(after) > 1 else (after[0] if after else EMPTY)
                        changed.append(f"group {group['id']} {name}: {overlay}")
        shared = {gid for p in cm["preset"] if p is not preset for gid in p["group_source_bindings"]}
        cm["group"] = [g for g in cm["group"] if g["id"] not in own - shared]
        cm["preset"].remove(preset)
        del cm["action_layers"][key]
        changed.append(f"removed layer {overlay}")
    for index, preset in enumerate(cm["preset"]):
        preset["id"] = str(index)
    text = json.dumps(new)
    if numeric:
        text, _ = titles_to_ids(text, generate_lookup(new))
        if "{{" in text:
            raise ValueError("menu_combo_keys: unresolved layer reference after removing the overlays")
    data.clear()
    data.update(json.loads(text))
    return {"changed": changed}


def _entries(value):
    for item in value.get("activators", {}).values():
        yield from item if isinstance(item, list) else [item]


def _commands(entry):
    binding = entry.get("bindings", {}).get("binding", [])
    return binding if isinstance(binding, list) else [binding]
