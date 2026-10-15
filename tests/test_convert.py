"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/test_scenarios_dse_1_0.py.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from steam_layout import controllers, convert
from steam_layout.model import Layout, actions, entries
from tools import release

ROOT = Path(__file__).resolve().parents[1]
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


class HeaderTests(unittest.TestCase):
    def test_the_header_names_the_controller(self):                                         # R179, R180
        for controller, variant, version in ((controllers.NEPTUNE, "alternative", "90.80"),
                                             (controllers.DSE, "default", "1.3")):
            with self.subTest(controller.name):
                data = toy({"Base": {}})
                convert.header(data, controller, variant, version)
                cm = data["controller_mappings"]
                self.assertEqual(cm["title"], f"single-set-default :: always-gyro :: {version}")
                self.assertEqual((cm["controller_type"], cm["controller_caps"], cm["url"], cm["description"]),
                                 (controller.controller_type, controller.controller_caps, controller.urls[variant],
                                  controller.descriptions[variant]))

    def test_every_gyro_to_mouse_group_states_the_style(self):                             # R179, R180
        data = toy({"Base": {"gyro": ("gyro_to_mouse", {}, {"gyro_natural_sensitivity": "300"})},
                    "Off": {"gyro": ("disabled", {})}, "Aim": {"gyro": ("gyro_to_mouse", {})}})
        self.assertEqual(convert.gyro_style(data, 2), 2)
        self.assertEqual(group(data, "Base", "gyro")["settings"],
                         {"gyro_natural_sensitivity": "300", "gyro_to_2d_conversion_style": "2"})
        self.assertEqual(group(data, "Aim", "gyro")["settings"], {"gyro_to_2d_conversion_style": "2"})
        self.assertEqual(group(data, "Off", "gyro")["settings"], {})


class GripTests(unittest.TestCase):
    def test_the_grips_trade_places_and_keep_their_places(self):                           # R181
        data = toy({"Base": {"switch": ("switches", {
            "button_back_left": act("key_press LEFT_SHIFT, , "), "button_back_right": act("key_press SPACE, , "),
            "button_back_left_upper": act("key_press LEFT_CONTROL, , "),
            "button_back_right_upper": act("key_press LEFT_ALT, , ")})},
            "Mod": {"switch": ("switches", {"button_back_left_upper": act(EMPTY)}),
                    "dpad": ("dpad", {"dpad_north": act("key_press A, , ")})}})
        self.assertEqual(convert.swap_grips(data, controllers.DSE), 2)
        inputs = group(data, "Base", "switch")["inputs"]
        self.assertEqual(list(inputs), ["button_back_left", "button_back_right", "button_back_left_upper",
                                        "button_back_right_upper"])
        self.assertEqual({name: actions(value["activators"]["Full_Press"])[0] for name, value in inputs.items()},
                         {"button_back_left": "key_press LEFT_CONTROL, , ", "button_back_right": "key_press LEFT_ALT, , ",
                          "button_back_left_upper": "key_press LEFT_SHIFT, , ",
                          "button_back_right_upper": "key_press SPACE, , "})
        self.assertEqual(list(group(data, "Mod", "switch")["inputs"]), ["button_back_left"])
        self.assertEqual(convert.swap_grips(data, controllers.NEPTUNE), 0)


class ChordTests(unittest.TestCase):
    def chord(self, settings, controller=controllers.DSE, where="Base / joystick edge chord"):
        report = convert.Report()
        result, kept = convert.chord(dict(settings), controller, report, where)
        return result, kept, list(report)

    def test_a_chord_on_a_moved_button_names_it_where_it_is(self):                        # R180, R181, R183
        settings, kept, _ = self.chord({"chord_button": "16", "interruptable": "0"})
        self.assertTrue(kept)
        self.assertEqual(list(settings.items()), [("gyro_ratchet_button_mask", str(1 << 27)),
                                                  ("gyro_ratchet_button_requireany_or_all", "0"),
                                                  ("interruptable", "0")])       # no chord_button ID: a mask, in place
        settings, _, _ = self.chord({"gyro_ratchet_button_mask": str(1 << 41 | 1 << 3)})
        self.assertEqual(settings["gyro_ratchet_button_mask"], str(1 << 15 | 1 << 3))           # L4's bit is L5's
        for unchanged in ({"chord_button": "1"}, {"gyro_ratchet_button_mask": str(1 << 30 | 1 << 2)}):
            self.assertEqual(self.chord(unchanged)[:2], (unchanged, True))
        for any_controller in (controllers.NEPTUNE,):
            self.assertEqual(self.chord({"chord_button": "16"}, any_controller)[:2], ({"chord_button": "16"}, True))

    def test_a_chord_on_an_absent_button(self):                                             # R178 (b) to (e)
        touch_l, touch_r, lb, deflect_l = 1 << 46, 1 << 47, 1 << 3, 1 << 30
        any_of, all_of = "0", "1"

        def mask(bits, mode):
            return {"gyro_ratchet_button_mask": str(bits), "gyro_ratchet_button_requireany_or_all": mode}
        self.assertEqual(self.chord({"chord_button": "23"})[1], False)                                # (c)
        self.assertEqual(self.chord({"chord_button": "17"})[1], False)                                # the right pad
        self.assertEqual(self.chord(mask(lb | touch_l, any_of))[:2], (mask(lb, any_of), True))         # (b)
        self.assertEqual(self.chord(mask(touch_l | touch_r, any_of))[1], False)                       # (b), none left
        self.assertEqual(self.chord(mask(lb | touch_l, all_of))[1], False)                            # (c)
        self.assertEqual(self.chord(mask(deflect_l | touch_l, all_of))[:2], (mask(deflect_l, all_of), True))  # (d)
        self.assertEqual(self.chord(mask(1 << 31 | touch_l, all_of))[1], False)          # (d) needs the same stick
        settings, kept, listed = self.chord({"chord_button": "24", "edge_binding_invert": "1"})       # (e)
        self.assertTrue(kept)
        self.assertEqual(settings["chord_button"], "24")
        self.assertTrue(listed and listed[0].startswith("R178 (e)"))
        settings, kept, listed = self.chord(mask(touch_l, any_of), where="gyro LST: Temporary Gyro / gyro")
        self.assertEqual((settings, kept), (mask(touch_l, any_of), True))                             # a gyro mask
        self.assertTrue(listed and listed[0].startswith("R178 (c)"))


class AbsentTests(unittest.TestCase):
    def test_binds_on_absent_inputs_go_and_so_do_groups_nothing_binds(self):              # R178 (a), R182
        data = convert.readable(toy({
            "Base": {"joystick": ("dpad", {"touch": act(add("LST")), "edge": act("key_press W, , ")}),
                     "right_trackpad": ("absolute_mouse", {"click": act("mouse_button LEFT, , ")}),
                     "switch": ("switches", {"right_trackpad_touch": act("mode_shift dpad 9")})},
            "LST": {"joystick": ("dpad", {"touch": act(remove("LST"), "release")})}}))
        groups = len(data["controller_mappings"]["group"])
        self.assertEqual(convert.drop_absent(data, controllers.DSE, convert.Report()), 3)
        base = Layout(data).active("Base")
        self.assertEqual(list(base), ["joystick", "switch"])
        self.assertEqual(list(base["joystick"]["inputs"]), ["edge"])
        self.assertIn("right_trackpad_touch", base["switch"]["inputs"])          # the touchpad's right half (A76)
        self.assertEqual(len(data["controller_mappings"]["group"]), groups - 1)
        self.assertEqual(Layout(data).active("LST")["joystick"]["inputs"], {})

    def test_a_layer_no_chain_reaches_goes_with_every_command_naming_it(self):           # R178 (f)
        data = convert.readable(toy({
            "Base": {"switch": ("switches", {"button_a": act(add("Kept")),
                                             "button_b": act([remove("Gone"), remove("Kept")]),
                                             "button_x": act(remove("Gone"))})},
            "Gone": {"switch": ("switches", {"button_y": act(add("Also gone"))})},
            "Kept": {"switch": ("switches", {"button_a": act(remove("Kept"), "release")})},
            "Also gone": {}}))
        report = convert.Report()
        self.assertEqual(convert.delete_unreachable(data, report), ["Gone", "Also gone"])
        cm = data["controller_mappings"]
        self.assertEqual([v["title"] for v in cm["action_layers"].values()], ["Kept"])
        self.assertEqual([p["id"] for p in cm["preset"]], ["0", "1"])
        base = Layout(data).active("Base")["switch"]["inputs"]
        self.assertEqual(actions(base["button_b"]["activators"]["Full_Press"]), [remove("Kept")])
        self.assertEqual(actions(base["button_x"]["activators"]["Full_Press"]), [EMPTY])       # still a block
        self.assertEqual(len(cm["group"]), 2)
        convert.dumps(data)                                                       # every command still resolves


class WholePadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ibex = json.loads(controllers.IBEX.snapshot("default", "1.0").read_text(encoding="utf-8"))
        cls.data = convert.readable(cls.ibex)
        cls.report = convert.Report()
        convert.whole_pad(cls.data, cls.report)
        cls.layout = Layout(cls.data)

    def test_the_left_pads_binds_go_to_the_whole_pad(self):                                # R183
        states = [state for p in self.data["controller_mappings"]["preset"]
                  for state in p["group_source_bindings"].values()]
        self.assertFalse([s for s in states if s.startswith("left_trackpad ")])
        self.assertEqual(sum(s.startswith("center_trackpad ") for s in states),
                         sum(s.startswith("left_trackpad ") for p in self.ibex["controller_mappings"]["preset"]
                             for s in p["group_source_bindings"].values()))

    def test_the_six_layers_are_the_whole_pads_in_their_models_places(self):              # R183, R104
        before = [v["title"] for v in self.ibex["controller_mappings"]["action_layers"].values()]
        after = [v["title"] for v in self.data["controller_mappings"]["action_layers"].values()]
        self.assertEqual(after, [convert.WHOLE_PAD_LAYERS.get(title, title) for title in before])
        named = {target for g in self.data["controller_mappings"]["group"] for _, _, e in convert.activators(g)
                 for _, target in convert.COMMAND.findall(" ".join(actions(e)))}
        self.assertFalse(named & set(convert.WHOLE_PAD_LAYERS))

    def test_the_click_entry_point_has_a_ring_press_and_no_centre_press(self):           # R183
        pad = self.layout.active("CTP: Click Entry Point")["center_trackpad"]
        self.assertEqual(pad["settings"]["edge_binding_radius"], "23000")
        (kind, ring), = entries(pad["inputs"]["edge"]["activators"])
        self.assertEqual(kind, "Full_Press")
        self.assertEqual(ring["settings"], {"hold_repeats": "1", "repeat_rate": "50", "haptic_intensity": "0",
                                            "delay_start": "5", "interruptable": "0"})
        self.assertEqual(self.layout.layer_ops(ring), [("add_layer", "CTP: Arrow Keys"),
                                                       ("remove_layer", "CTP: Click Entry Point")])

    def test_every_click_on_the_whole_pad_is_a_regular_press(self):                       # R183
        clicks = [kind for title, p in self.layout.presets.items() for gid, state in p["group_source_bindings"].items()
                  if state.startswith("center_trackpad") and title != "LTP: Middle Click"
                  for name, value in (self.layout.groups[gid].get("inputs") or {}).items()
                  for kind, _ in entries(value.get("activators") or {}) if name == "click"]
        self.assertTrue(clicks)
        self.assertNotIn("Soft_Press", clicks)


class MuteAndGyroTests(unittest.TestCase):
    def test_mute_is_the_middle_mouse_button_in_base(self):                                # R184
        data = toy({"Base": {"switch": ("switches", {"button_a": act("key_press A, , ")})}})
        convert.mute(data, controllers.DSE)
        inputs = group(data, "Base", "switch")["inputs"]
        self.assertEqual(list(inputs), ["button_a", "button_capture"])
        self.assertEqual(inputs["button_capture"]["activators"], act("mouse_button MIDDLE, , "))

    def test_the_gyro_layers_lose_their_enable_mask_and_base_keeps_its(self):            # R185
        masked = {"gyro_ratchet_button_mask": "3221225472", "gyro_ratchet_button_requireany_or_all": "0",
                  "gyro_natural_sensitivity": "300"}
        data = toy({"Base": {"gyro": ("gyro_to_mouse", {}, masked)}, "Gyro": {"gyro": ("gyro_to_mouse", {}, masked)},
                    "Gyro | L1: Modifier 0": {"gyro": ("gyro_to_mouse", {}, masked)},
                    "Gyro Off Ramp Up": {"gyro": ("disabled", {})}})
        self.assertEqual(convert.gyro_always_on(data), ["Gyro", "Gyro | L1: Modifier 0"])
        self.assertEqual(group(data, "Gyro", "gyro")["settings"], {"gyro_natural_sensitivity": "300"})
        self.assertEqual(group(data, "Base", "gyro")["settings"], masked)              # author: "does not include base"
        self.assertEqual(group(data, "Gyro Off Ramp Up", "gyro")["mode"], "disabled")


class BaseTests(unittest.TestCase):
    def test_ibex_is_built_and_the_others_are_converted_from_it(self):                    # R177
        neptune = json.loads(controllers.NEPTUNE.snapshot("default", "90.74").read_text(encoding="utf-8"))
        ibex = json.loads(controllers.IBEX.snapshot("default", "1.0").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "base layout"):
            convert.convert(ibex, "ibex", "default", "1.1")
        with self.assertRaisesRegex(ValueError, "not an Ibex layout"):
            convert.convert(neptune, "dse", "default", "1.0")
        with self.assertRaisesRegex(ValueError, "reads a Neptune layout"):
            convert.bootstrap(ibex, "default", "1.0")


class ConversionTests(unittest.TestCase):
    """The real layouts: C1, C2, C3 and C5."""

    @classmethod
    def setUpClass(cls):
        cls.ibex = {v: json.loads(controllers.IBEX.snapshot(v, "1.0").read_text(encoding="utf-8"))
                    for v in controllers.VARIANTS}
        cls.dse = {v: json.loads(controllers.DSE.working_json(v).read_text(encoding="utf-8"))
                   for v in controllers.VARIANTS}

    def test_c1_each_conversion_is_what_tools_convert_makes_from_its_ibex_release(self):  # R177
        checked = 0
        for controller in controllers.with_layouts():
            if controller.base:
                continue
            version = release.working_version(controller)
            if controller.built_until and controllers.version_key(version) <= controllers.version_key(
                    controller.built_until):
                continue
            base = release.base_release(release.changelog_section(controller.name, version))
            with self.subTest(controller.name):
                self.assertIsNotNone(base, f"CHANGELOG.md: {controller.name} {version} names no Ibex release")
                for variant in controllers.VARIANTS:
                    source = json.loads(controllers.IBEX.snapshot(variant, base).read_text(encoding="utf-8"))
                    made, _ = convert.convert(source, controller.name, variant, version)
                    working = json.loads(controller.working_json(variant).read_text(encoding="utf-8"))
                    self.assertEqual(made, working, f"{controller.working_json(variant).name} was edited by hand")
                    checked += 1
        self.assertGreaterEqual(checked, 4)

    def test_c2_every_layout_passes_the_build_audit(self):                                # R150, R178 (g)
        layouts = [str(path) for c in (controllers.IBEX, controllers.DSE) for path in c.working()]
        result = subprocess.run([sys.executable, "-m", "tools.audit_build", *layouts], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_c3_ibex_converts_back_to_neptune_90_74_but_for_the_gyro_style(self):         # R179
        for variant in controllers.VARIANTS:
            with self.subTest(variant):
                made, _ = convert.convert(self.ibex[variant], "neptune", variant, "90.74")
                deck = json.loads(controllers.NEPTUNE.snapshot(variant, "90.74").read_text(encoding="utf-8"))
                styles = 0
                for kept, old in zip(made["controller_mappings"]["group"], deck["controller_mappings"]["group"]):
                    if kept["mode"] == "gyro_to_mouse":
                        self.assertEqual(kept["settings"].pop("gyro_to_2d_conversion_style"), "2")
                        styles += old["settings"].pop("gyro_to_2d_conversion_style", None) is not None or 1
                self.assertEqual(styles, 11)
                self.assertEqual(made, deck)

    def test_c5_the_whole_pads_layers_are_their_models_with_only_the_tables_changes(self):  # R183
        for variant in controllers.VARIANTS:
            model, made = Layout(convert.readable(self.ibex[variant])), Layout(convert.readable(self.dse[variant]))
            for old, new in convert.WHOLE_PAD_LAYERS.items():
                with self.subTest(variant, layer=new):
                    self.assertEqual(differences(model, old, made, new), [])

    def test_what_the_edge_has_and_lacks(self):                                           # R178, R180, R182, R183
        for variant, data in self.dse.items():
            layout = Layout(convert.readable(data))
            titles = list(layout.presets)
            with self.subTest(variant):
                self.assertEqual(len(titles), 75)
                self.assertFalse([t for t in titles if t.startswith(("LST:", "RST:", "LTP:", "RTP:"))])
                self.assertEqual(sorted(t for t in titles if t.startswith("CTP:")),
                                 sorted(convert.WHOLE_PAD_LAYERS.values()))
                states = [s for p in layout.presets.values() for s in p["group_source_bindings"].values()]
                self.assertFalse([s for s in states if s.split(" ")[0] in ("left_trackpad", "right_trackpad")])
                for title, preset in layout.presets.items():
                    for gid, state in preset["group_source_bindings"].items():
                        g = layout.groups[gid]
                        if state.split(" ")[0] in ("joystick", "right_joystick"):
                            self.assertNotIn("touch", g.get("inputs", {}), title)
                        for name, kind, entry in convert.activators(g):
                            settings = entry.get("settings") or {}
                            self.assertNotIn(settings.get("chord_button"), ("16", "17", "23", "24"), title)
                            bits = int(settings.get("gyro_ratchet_button_mask", 0))
                            self.assertFalse(bits & (1 << 19 | 1 << 20 | 1 << 46 | 1 << 47), title)
                            for op, target in layout.layer_ops(entry):
                                self.assertIn(target, layout.presets, f"{title} {name} names a deleted layer")
                cm = data["controller_mappings"]
                self.assertEqual((cm["controller_type"], cm["title"].rsplit(" :: ", 1)[-1]), ("controller_ps5_edge", "1.0"))

    def test_mute_and_gyro_on_the_edge(self):                                            # R184, R185, R180
        for variant, data in self.dse.items():
            layout = Layout(data)
            with self.subTest(variant):
                capture = [t for t in layout.presets if "button_capture" in (layout.active(t).get("switch") or {}).get("inputs", {})]
                self.assertEqual(capture, ["Base"])
                self.assertEqual(layout.active("Base")["switch"]["inputs"]["button_capture"]["activators"],
                                 act("mouse_button MIDDLE, , "))
                gyros = {t: layout.active(t)["gyro"] for t in layout.presets
                         if layout.active(t).get("gyro", {}).get("mode") == "gyro_to_mouse"}
                self.assertEqual(len(gyros), 9)                       # the two Temporary Gyro layers are gone
                masked = {t for t, g in gyros.items() if "gyro_ratchet_button_mask" in g["settings"]}
                self.assertEqual(masked, {"Base"})
                # Base keeps its mask, with the stick touches dropped: each needs that stick's deflection too (R178 d)
                self.assertEqual((gyros["Base"]["settings"]["gyro_ratchet_button_mask"],
                                  gyros["Base"]["settings"]["gyro_ratchet_button_requireany_or_all"]),
                                 (str(1 << 12 | 1 << 14 | 1 << 30 | 1 << 31), "1"))
                for g in gyros.values():
                    self.assertEqual(g["settings"]["gyro_to_2d_conversion_style"], "4")
                self.assertEqual(layout.active("Gyro Off Ramp Up")["gyro"]["mode"], "disabled")


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


if __name__ == "__main__":
    unittest.main()
