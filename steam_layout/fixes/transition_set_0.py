"""Give Transition Set 0 the side-local stick-touch release cleanup.

Every non-cover layer must bind its stick-touch release explicitly (see
resources/Layer Definition of Done.md, section 5). The steering build gave
Transition Set 1 a release that removes the side's LST/RST trio; Transition
Set 0 still had none.

Transition Set 0's touch inputs already use three entries: one empty chord per
menu button plus the repeating guarded recovery. To stay within the budget,
the two empty chords become one multi-button Any chord (Menu Left bit 12 +
Menu Right bit 14 = 20480) with the same settings. The release is copied from
Transition Set 1's same-side touch, so it works with numeric IDs or title
tokens. Idempotent.
"""
import json

MENU_ANY = str((1 << 12) | (1 << 14))  # Menu Left (button_menu) + Menu Right (button_escape)
EMPTY = "controller_action empty_binding, , "
LEGACY_MENU = {"14", "15"}  # legacy chord_button IDs for Menu Right / Menu Left


def touch(cm, groups, title, source):
    key = next(k for k, v in cm["action_layers"].items() if v["title"] == title)
    preset = next(p for p in cm["preset"] if p["name"] == key)
    gid = next(g for g, s in preset["group_source_bindings"].items() if s == f"{source} active")
    return groups[gid]["inputs"]["touch"]


def fix(data):
    cm = data["controller_mappings"]
    groups = {g["id"]: g for g in cm["group"]}
    changed = []
    for source in ("joystick", "right_joystick"):
        target = touch(cm, groups, "Transition Set 0", source)
        acts = target["activators"]
        if "release" in acts:
            continue
        chords = acts.get("chord")
        if not (isinstance(chords, list) and len(chords) == 2 and list(acts) == ["chord", "Full_Press"]
                and {c["settings"].get("chord_button") for c in chords} == LEGACY_MENU
                and all(c["bindings"]["binding"] == EMPTY and c["settings"].get("interruptable") == "0"
                        and set(c["settings"]) == {"chord_button", "interruptable"} for c in chords)):
            raise ValueError(f"Transition Set 0 {source} touch: unexpected shape {list(acts)}")
        release = touch(cm, groups, "Transition Set 1", source)["activators"]["release"]
        target["activators"] = {
            "chord": {"bindings": {"binding": EMPTY},
                      "settings": {"gyro_ratchet_button_mask": MENU_ANY,
                                   "gyro_ratchet_button_requireany_or_all": "0", "interruptable": "0"}},
            "Full_Press": acts["Full_Press"],
            "release": json.loads(json.dumps(release)),
        }
        changed.append(source)
    return {"changed": changed}
