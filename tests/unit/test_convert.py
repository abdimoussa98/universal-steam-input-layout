"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/scenarios/dse/test_scenarios_dse_1_0.py.

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.convert import *

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


if __name__ == "__main__":
    unittest.main()
