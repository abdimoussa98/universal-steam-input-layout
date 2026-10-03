"""Generate the minimal Deck layout that tests the held-input rule in isolation.

Writes two files next to this script:

- rule-test.readable.json: {{Base::Title}} tokens, for review
- rule-test.json: numeric runtime IDs, for VDF conversion with pfwobcke.vscode-vdf

Each layer types its own digit on D-pad Up, so the digit shows which layer is on
top while other buttons stay held. See AUDIT.md#deck-checks for the procedure.

    python3 findings/2026-09-29-held-input-layer-transitions/build_rule_test_layout.py
"""
import copy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from tools.convert_runtime_ids import generate_lookup, titles_to_ids  # noqa: E402

LAYERS = ("X1 Immediate", "X2 Delayed", "X3 Repeating", "K Key Output", "R Remover", "Target")
PROBE = {"Base": "0", "X1 Immediate": "1", "X2 Delayed": "2", "X3 Repeating": "3",
         "K Key Output": "4", "R Remover": "5", "Target": "9"}


def add(title):
    return "controller_action add_layer {{Base::" + title + "}} 0 0, , "


def remove(title):
    return "controller_action remove_layer {{Base::" + title + "}} 0 0, , "


def key(name):
    return f"key_press {name}, , "


def press(binding, **settings):
    entry = {"bindings": {"binding": binding}}
    if settings:
        entry["settings"] = {k: str(v) for k, v in settings.items()}
    return {"activators": {"Full_Press": entry}, "disabled_activators": {}}


def group(gid, mode, inputs, settings):
    return {"id": str(gid), "mode": mode, "name": "", "description": "",
            "inputs": inputs, "settings": settings}


def build():
    reset = [remove(title) for title in reversed(LAYERS)]
    base_groups = [
        group(0, "switches", {
            "button_escape": press(reset),                 # Start: reset
            "button_menu": press(add("R Remover")),        # Select: enter R (T4, T6, T7)
            "left_bumper": press(add("K Key Output")),     # T5
            "right_bumper": press(add("Target")),          # exposed by R's RB removal (T4, T7)
        }, {}),
        group(1, "four_buttons", {
            "button_a": press(add("X1 Immediate")),        # T1
            "button_x": press(add("X2 Delayed")),          # T2
            "button_y": press(add("X3 Repeating")),        # T3
        }, {"button_size": "17994", "button_dist": "19994"}),
        group(2, "dpad", {
            "dpad_north": press(key(PROBE["Base"])),
            "dpad_south": press(key("Q")),                 # exposed by R's D-pad Down removal (T6)
            "dpad_east": press(remove("Target")),          # T7 step 2
        }, {"requires_click": "0", "layout": "0", "haptic_intensity_override": "0"}),
    ]
    layer = {"layer": "1"}
    target_b = add("Target")
    layer_groups = {
        "X1 Immediate": [group(3, "four_buttons", {"button_b": press(target_b)}, layer)],
        "X2 Delayed": [group(5, "four_buttons", {"button_b": press(target_b, delay_start=5)}, layer)],
        "X3 Repeating": [group(7, "four_buttons", {"button_b": press(target_b, hold_repeats=1)}, layer)],
        "K Key Output": [group(9, "four_buttons", {"button_b": press(key("K"))}, layer)],
        "R Remover": [group(11, "switches", {"right_bumper": press(remove("R Remover"))}, layer)],
        "Target": [],
    }
    dpad_ids = {"X1 Immediate": 4, "X2 Delayed": 6, "X3 Repeating": 8, "K Key Output": 10,
                "R Remover": 12, "Target": 13}
    for title, gid in dpad_ids.items():
        inputs = {"dpad_north": press(key(PROBE[title]))}
        if title == "R Remover":
            inputs["dpad_south"] = press(remove("R Remover"))
        layer_groups[title].append(group(gid, "dpad", inputs, copy.deepcopy(layer)))

    source = {"switches": "switch", "four_buttons": "button_diamond", "dpad": "dpad"}
    presets = [{"id": "0", "name": "Preset_1000001",
                "group_source_bindings": {g["id"]: source[g["mode"]] + " active" for g in base_groups}}]
    action_layers = {}
    groups = list(base_groups)
    for index, title in enumerate(LAYERS, start=2):
        key_name = f"Preset_{1000000 + index}"
        action_layers[key_name] = {"title": title, "legacy_set": "1", "set_layer": "1",
                                   "parent_set_name": "Preset_1000001"}
        presets.append({"id": str(index - 1), "name": key_name,
                        "group_source_bindings": {g["id"]: source[g["mode"]] + " active"
                                                  for g in layer_groups[title]}})
        groups.extend(layer_groups[title])
    groups.sort(key=lambda g: int(g["id"]))

    return {"controller_mappings": {
        "version": "3",
        "revision": "1",
        "title": "held-input rule test",
        "description": ("Minimal test for the held-input rule. D-pad Up types the top layer's digit "
                        "(Base 0, X1 1, X2 2, X3 3, K 4, R 5, Target 9). Start resets. "
                        "Procedure: findings/2026-09-29-held-input-layer-transitions/AUDIT.md#deck-checks"),
        "creator": "76561198079670632",
        "progenitor": "",
        "url": "template://empty.vdf",
        "export_type": "personal_local",
        "controller_type": "controller_neptune",
        "controller_caps": "23117823",
        "major_revision": "0",
        "minor_revision": "0",
        "Timestamp": "0",
        "actions": {"Preset_1000001": {"title": "Base", "legacy_set": "1"}},
        "action_layers": action_layers,
        "group": groups,
        "preset": presets,
        "settings": {"left_trackpad_mode": "0", "right_trackpad_mode": "0",
                     "action_set_trigger_cursor_show": "0", "action_set_trigger_cursor_hide": "0"},
    }}


def main():
    readable = json.dumps(build(), indent="\t", ensure_ascii=False)
    numeric, count = titles_to_ids(readable, generate_lookup(json.loads(readable)))
    if "{{" in numeric:
        raise SystemExit("unresolved title token in rule-test.json")
    (HERE / "rule-test.readable.json").write_text(readable)
    (HERE / "rule-test.json").write_text(numeric)
    print(f"wrote rule-test.readable.json and rule-test.json ({count} runtime IDs resolved)")


if __name__ == "__main__":
    main()
