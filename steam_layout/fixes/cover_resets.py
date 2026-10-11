"""Add the stuck-delay reset to the second-press layers, as a 4th entry.

After an accepted double tap, `Menu Left: Escape`, `Menu Right: Tab` and the two
modifier Scroll layers add their Double Tap Cover with a 150 ms chorded delay.
Since 90.25 the two chorded menu chains have a second-press layer each as well
(`Menu Left!Right: Enter`, `Menu Right!Left: Backspace`): six in all. Since
90.52 the two Steering stick scroll layers make eight; their builder writes
the reset itself. Since 90.53 their 150 ms chord sits on the drivers, chorded
on the stick's deflect, and the reset stays on the stick's direction: such a
chord is left alone here, and the count is six again. Since 90.55 that timer
is a Soft Press on the stick's edge, which this fix does not look at: six.
That delayed add had no repeating reset (see resources/Steam Input JSON
Structure.md, Interrupted Delayed Layer Applies). This adds the usual reset:
a Regular Press removing only the cover, Hold to Repeat every delay + 50 ms,
Interruptable off.

The input already has three entries, so the reset is a deliberate 4th entry
(author decision, 2026-09-30). Steam's desktop editor drops entries past the
third, so the reset must be **last**: activators become release, chord,
Full_Press [original output, reset]. The JSON/VDF converter keeps repeated
activator types together, so the Regular Press list moves to the end.
audit_command_budget.py allows exactly this shape.

Idempotent; works with numeric IDs or title tokens.
"""
import re

ADD = re.compile(r"^controller_action add_layer (.+?) 0 0, , $")
DEFLECT = str(1 << 30)                  # the left stick's deflect as a chord's only button
SECOND_PRESS_LAYERS = (4, 6, 8)         # until 90.24, with the two chorded menu chains, and with the two Steering stick scroll layers


def fix(data):
    cm = data["controller_mappings"]
    titles = {k: v["title"] for k, v in cm["action_layers"].items()}
    groups = {g["id"]: g for g in cm["group"]}
    # Resolve the chord's target title whether the file uses tokens or numeric IDs.
    order = list(cm["actions"]) + list(cm["action_layers"])
    by_id = {str(i + 1): titles.get(key, "") for i, key in enumerate(order)}
    changed, already = [], []
    for preset in cm["preset"]:
        layer = titles.get(preset["name"])
        if not layer:
            continue
        for gid, state in preset["group_source_bindings"].items():
            if state.split(" ", 1)[-1] != "active":
                continue
            for input_name, value in groups[gid].get("inputs", {}).items():
                acts = value.get("activators", {})
                chord = acts.get("chord")
                if not isinstance(chord, dict) or "release" not in acts or "Full_Press" not in acts:
                    continue
                binding = chord.get("bindings", {}).get("binding")
                match = ADD.match(binding) if isinstance(binding, str) else None
                if not match:
                    continue
                token = match.group(1)
                target = by_id.get(token) or token.strip("{}").split("::")[-1]
                if "Double Tap Cover" not in target or not chord.get("settings", {}).get("delay_start"):
                    continue
                if chord["settings"].get("gyro_ratchet_button_mask") == DEFLECT and not state.startswith("joystick "):
                    continue                      # a timer on a driver: its reset is on the stick's direction
                label = f"{layer} / {input_name}"
                reset = {"bindings": {"binding": binding.replace("add_layer", "remove_layer", 1)},
                         "settings": {"hold_repeats": "1",
                                      "repeat_rate": str(int(chord["settings"]["delay_start"]) + 50),
                                      "interruptable": "0"}}
                full = acts["Full_Press"]
                if isinstance(full, list):
                    if list(acts) == ["release", "chord", "Full_Press"] and len(full) == 2 and full[1] == reset:
                        already.append(label)
                        continue
                    raise ValueError(f"{label}: unexpected Regular Press list")
                if len(acts) != 3:
                    raise ValueError(f"{label}: expected exactly three entries, found {list(acts)}")
                value["activators"] = {"release": acts["release"], "chord": chord, "Full_Press": [full, reset]}
                changed.append(label)
    if len(changed) + len(already) not in SECOND_PRESS_LAYERS:
        raise ValueError(f"expected four, six or eight second-press layers, found {changed + already}")
    return {"changed": changed, "already": already}
