"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/scenarios/dse/test_scenarios_dse_1_0.py.
"""


import copy


import subprocess


import sys


import unittest


from steam_layout import controllers, convert


from steam_layout.model import Layout, actions, entries


from tools import release


from tests.support.sources import ROOT, load_json


EMPTY = "controller_action empty_binding, , "


def act(binding, kind="Full_Press", **settings):
    entry = {"bindings": {"binding": binding}}
    if settings:
        entry["settings"] = settings
    return {kind: entry}


def add(title):
    return f"controller_action add_layer {{{{Base::{title}}}}} 0 0, , "


def remove(title):
    return f"controller_action remove_layer {{{{Base::{title}}}}} 0 0, , "


def toy(layers, controller=controllers.IBEX):
    """A small layout: {title: {source: (mode, {input: activators}, settings)}}; the first title is the action set."""
    cm = {"title": "single-set-default :: always-gyro :: 1.0", "description": "", "url": "",
          "controller_type": controller.controller_type, "controller_caps": controller.controller_caps,
          "actions": {}, "action_layers": {}, "preset": [], "group": []}
    gid = 0
    for index, (title, sources) in enumerate(layers.items()):
        key = f"Preset_{1000001 + index}"
        entry = {"title": title, "legacy_set": "1"}
        if index:
            entry.update({"set_layer": "1", "parent_set_name": "Preset_1000001"})
        (cm["actions"] if index == 0 else cm["action_layers"])[key] = entry
        bindings = {}
        for source, spec in sources.items():
            mode, inputs, settings = (spec + ({},))[:3]
            gid += 1
            cm["group"].append({"id": str(gid), "mode": mode, "inputs": {
                name: {"activators": a, "disabled_activators": {}} for name, a in inputs.items()},
                "settings": copy.deepcopy(settings)})
            bindings[str(gid)] = f"{source} active"
        cm["preset"].append({"id": str(index), "name": key, "group_source_bindings": bindings})
    return {"controller_mappings": cm}


def group(data, title, source):
    layout = Layout(data)
    return layout.active(title)[source]


def differences(model, old, made, new):
    """What differs between a left-pad layer and the whole pad's layer made from it, beyond R183's table: the
    whole pad for the left pad, no stick touch, the left pad's touch chord as mask bit 27, Regular Presses on the
    click, renamed commands, and in the Click Entry Point no centre press and the ring press on the outer ring."""
    rename = convert.WHOLE_PAD_LAYERS
    found = []
    before, after = model.active(old), made.active(new)
    sources = {("center_trackpad" if s == "left_trackpad" else s) for s in before}
    if sources != set(after):
        found.append(f"sources {sorted(sources)} became {sorted(after)}")
    for source, group_before in before.items():
        target = "center_trackpad" if source == "left_trackpad" else source
        group_after = after.get(target)
        if group_after is None:
            continue
        wanted_settings = dict(group_before.get("settings") or {})
        inputs = {name: value for name, value in (group_before.get("inputs") or {}).items()
                  if not (source in ("joystick", "right_joystick") and name == "touch")}
        for name, value in inputs.items():
            expected = []
            for kind, entry in entries(value.get("activators") or {}):
                entry = copy.deepcopy(entry)
                commands = actions(entry)
                if any(t == convert.CENTRE_PRESS_TARGET for _, t in convert.COMMAND.findall(" ".join(commands))):
                    continue                                                   # the centre press
                settings = dict(entry.get("settings") or {})
                if settings.get("chord_button") == "16":
                    settings = {**{k: v for k, v in settings.items() if k != "chord_button"}}
                    settings = {"gyro_ratchet_button_mask": str(1 << 27), "gyro_ratchet_button_requireany_or_all": "0",
                                **settings}
                if kind == "Soft_Press" and source == "left_trackpad" and name in ("click", "edge"):
                    if name == "edge":
                        wanted_settings["edge_binding_radius"] = settings["activation_threshold"]
                    settings = {k: v for k, v in settings.items() if k not in convert.SOFT_ONLY}
                    kind = "Full_Press"
                new_commands = [b for b in commands]
                for one, other in rename.items():
                    new_commands = [b.replace(f"{{{{Base::{one}}}}}", f"{{{{Base::{other}}}}}") for b in new_commands]
                expected.append((kind, settings, new_commands))
            got = [(kind, dict(entry.get("settings") or {}), actions(entry))
                   for kind, entry in entries((group_after.get("inputs") or {}).get(name, {}).get("activators") or {})]
            if got != expected:
                found.append(f"{target} {name}: {got} is not {expected}")
        extra = set(group_after.get("inputs") or {}) - set(inputs)
        if extra:
            found.append(f"{target}: new inputs {sorted(extra)}")
        if (group_after.get("settings") or {}) != wanted_settings or group_after["mode"] != group_before["mode"]:
            found.append(f"{target}: mode or settings {group_after['mode']} {group_after.get('settings')}")
    return found


__all__ = ['EMPTY', 'Layout', 'ROOT', 'act', 'actions', 'add', 'controllers', 'convert', 'copy', 'differences', 'entries', 'group', 'load_json', 'release', 'remove', 'subprocess', 'sys', 'toy', 'unittest']
