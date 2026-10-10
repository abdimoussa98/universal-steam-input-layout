"""90.43 Steering entry protection, applied to a readable 90.42 layout.

The fallback layer's existing slot is reused. The guard protects one movement
until a direction/outer-edge Release or a deliberate driver/menu handoff. It
does not poll the stick's center: centered entry is intentionally protected.
"""
import copy
import re

from steam_layout.model import Layout, actions, entries

OLD_GUARD = "Steering | LS: Fallback Guard"
GUARD = "Steering | LS: Entry Guard"
STEERING = "Steering"
TRANSITION = "Transition Set 1"
EMPTY = "controller_action empty_binding, , "
MOVEMENT = {"dpad_north": "W", "dpad_south": "S", "dpad_east": "D", "dpad_west": "A"}
PAD_KEYS = {"dpad_west": "ESCAPE", "dpad_east": "RETURN", "dpad_north": "TAB", "dpad_south": "BACKSPACE"}


def op(verb, title):
    return f"controller_action {verb}_layer {{{{Base::{title}}}}} 0 0, , "


def entry(*execution, **settings):
    stored = list(reversed(execution))
    return {"bindings": {"binding": stored[0] if len(stored) == 1 else stored},
            "settings": {key: str(value) for key, value in settings.items()}}


def slot(**activators):
    return {"activators": activators, "disabled_activators": {}}


def rename(value):
    """Rename just the exact layer title and its readable command token."""
    if isinstance(value, dict):
        for key, child in value.items():
            value[key] = rename(child)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            value[index] = rename(child)
    elif isinstance(value, str):
        if value == OLD_GUARD:
            return GUARD
        return value.replace("{{Base::" + OLD_GUARD + "}}", "{{Base::" + GUARD + "}}")
    return value


def apply(data, variant):
    """Mutate a readable 90.42 layout and return the exact entry-guard changes.

    This component does not run the fix pipeline or write a layout. The parent
    release builder owns integration, metadata, numeric conversion and export.
    """
    if variant not in ("default", "alternative"):
        raise ValueError(f"Unknown variant: {variant}")
    original = Layout(data)
    assert OLD_GUARD in original.presets and GUARD not in original.presets
    assert not any(re.search(r"controller_action (?:add_layer|remove_layer|hold_layer) \d+", command)
                   for group in original.groups.values() for value in group.get("inputs", {}).values()
                   for bank in ("activators", "disabled_activators")
                   for _, activator in entries(value.get(bank, {})) for command in actions(activator)), \
        "Convert numeric layer IDs to titles before applying Entry Guard"
    old_order = list(original.order)
    old_presets = [preset["name"] for preset in original.cm["preset"]]
    slot_index = list(original.presets).index(OLD_GUARD)
    rename(data)
    layout = Layout(data)
    active = layout.active(GUARD)
    renamed_references = []
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name, value in group.get("inputs", {}).items():
                for kind, activator in entries(value.get("activators", {})):
                    if any(target == GUARD for _, target in layout.layer_ops(activator)):
                        renamed_references.append([title, source, name, kind])

    # Replace the old guard's groups in place; each belongs only to this layer.
    for source, group in active.items():
        assert sum(group["id"] in preset["group_source_bindings"] for preset in layout.cm["preset"]) == 1
        group["inputs"] = {}

    steering = layout.active(STEERING)
    stick = active["joystick"]
    stick["mode"] = steering["joystick"]["mode"]
    stick["settings"] = copy.deepcopy(steering["joystick"]["settings"])
    assert stick["settings"]["edge_binding_invert"] == "0"
    assert "edge_binding_radius" not in stick["settings"]
    for direction, key in MOVEMENT.items():
        stick["inputs"][direction] = slot(
            Full_Press=entry(f"key_press {key}, , ", interruptable=0),
            release=entry(op("remove", GUARD), haptic_intensity=0))
    stick["inputs"]["edge"] = slot(release=entry(op("remove", GUARD), haptic_intensity=0))
    for source in ("joystick", "right_joystick"):
        group = active[source]
        if source == "right_joystick":
            group["mode"] = steering[source]["mode"]
            group["settings"] = {"layer": "1", "edge_binding_invert": "0"}
            group["inputs"]["edge"] = slot(Full_Press=entry(EMPTY, haptic_intensity=0))
        # Lifting either thumb clears only its ordinary helpers, never Entry Guard.
        group["inputs"]["touch"] = copy.deepcopy(steering[source]["inputs"]["touch"])

    # Steering owns driver acquisition. Reuse that complete binding in the guard
    # after adding its quiet self-removal ahead of the existing ramp cleanup/add.
    drivers = [("switch", "left_bumper"), ("switch", "right_bumper")] if variant == "default" else [
        ("left_trigger", "edge"), ("right_trigger", "edge")]
    driver_changes = []
    for source, name in drivers:
        binding = steering[source]["inputs"][name]
        activator = binding["activators"]["Full_Press"]
        stored = actions(activator)
        assert any(command.startswith("controller_action add_layer ") for command in stored)
        activator["bindings"]["binding"] = stored + [op("remove", GUARD)]
        active[source]["inputs"][name] = copy.deepcopy(binding)
        driver_changes.append([source, name])

    # Start Press is deliberately not a repeating/self-chord entry: a menu
    # button carried into the transition must not consume fresh protection.
    switch = active["switch"]
    for name, side in (("button_menu", "Left"), ("button_escape", "Right")):
        target = f"Stateful | Menu {side}: Entry Point"
        switch["inputs"][name] = slot(Start_Press=entry(
            op("remove", GUARD), op("add", target), haptic_intensity=0))

    # Prevent pad helpers/windows from hiding the movement Releases. Keep the
    # right pad's mouse response and the left pad's ordinary swipe key outputs.
    new_groups = []
    next_gid = max(int(gid) for gid in layout.groups) + 1
    for source in ("left_trackpad", "right_trackpad"):
        template = layout.active(layout.base)[source]
        group = {"id": str(next_gid), "mode": template["mode"], "name": "", "description": "",
                 "inputs": {}, "settings": {**copy.deepcopy(template.get("settings", {})), "layer": "1"}}
        next_gid += 1
        group["inputs"]["click"] = slot(Full_Press=entry(EMPTY, haptic_intensity=0))
        group["inputs"]["touch"] = slot(Full_Press=entry(EMPTY, haptic_intensity=0))
        if source == "left_trackpad":
            for direction, key in PAD_KEYS.items():
                group["inputs"][direction] = slot(Full_Press=entry(
                    f"key_press {key}, , ", interruptable=0, haptic_intensity=0))
        layout.cm["group"].append(group)
        layout.presets[GUARD]["group_source_bindings"][group["id"]] = source + " active"
        new_groups.append({"source": source, "id": group["id"]})

    commit = layout.active(TRANSITION)["switch"]["inputs"]["button_escape"]["activators"]["release"]
    assert layout.layer_ops(commit) == [("remove_layer", TRANSITION), ("add_layer", STEERING)]
    # Existing Steering add keeps its beep; the guard add is silent and last.
    commit["bindings"]["binding"] = [op("add", GUARD)] + actions(commit)
    assert layout.order == old_order
    assert [preset["name"] for preset in layout.cm["preset"]] == old_presets
    assert list(Layout(data).presets).index(GUARD) == slot_index
    return {"renamed": {"from": OLD_GUARD, "to": GUARD, "preset_index": slot_index},
            "renamed_reference_entries": renamed_references, "new_groups": new_groups,
            "driver_handoffs": driver_changes,
            "commit_execution": layout.layer_ops(commit),
            "disarm": "First direction Release, normal outer-edge Release, driver acquisition or fresh menu Start Press"}
