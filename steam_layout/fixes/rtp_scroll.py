"""Replace RTP: Mouse Buttons' Long Press scroll repeat with a chorded delay.

Long Press is banned (see resources/Steam Input JSON Structure.md, Allowed
Activation Types). Each pad direction keeps its immediate Regular Press wheel
tick; the 150 ms Long Press becomes a chord on right-pad touch (bit 20) with
`delay_start 150` and the same repeat/haptic settings. No layer is added, so no
interrupted-delay reset is needed (and RTP deliberately has none). Idempotent;
works with numeric IDs or title tokens.
"""

RIGHT_PAD_TOUCH = 1 << 20  # k_eGamepadButtonBitMask_CapSenseRightTouchPad
LAYER = "RTP: Mouse Buttons"
SLOT = "right_trackpad active"
INPUTS = ("dpad_north", "dpad_south")


def fix(data):
    cm = data["controller_mappings"]
    key = next((k for k, v in cm["action_layers"].items() if v["title"] == LAYER), None)
    if key is None:                       # a controller without the right pad has no such layer (R178)
        return {"group": None, "changed": []}
    preset = next(p for p in cm["preset"] if p["name"] == key)
    gid = next(g for g, s in preset["group_source_bindings"].items() if s == SLOT)
    group = next(g for g in cm["group"] if g["id"] == gid)
    changed = []
    for name in INPUTS:
        activators = group["inputs"][name]["activators"]
        if "Long_Press" not in activators:
            continue
        old = activators["Long_Press"]
        if isinstance(old, list) or "chord" in activators:
            raise ValueError(f"{LAYER} {name}: unexpected activator shape")
        settings = {k: v for k, v in old.get("settings", {}).items() if k != "long_press_time"}
        delay = old.get("settings", {}).get("long_press_time", "150")
        chord = {"bindings": old["bindings"], "settings": {
            "gyro_ratchet_button_mask": str(RIGHT_PAD_TOUCH),
            "gyro_ratchet_button_requireany_or_all": "0",
            "delay_start": delay, **settings}}
        # Keep activator position: the chord replaces the Long Press in place.
        group["inputs"][name]["activators"] = {("chord" if k == "Long_Press" else k): (chord if k == "Long_Press" else v)
                                               for k, v in activators.items()}
        changed.append(name)
    return {"group": gid, "changed": changed}
