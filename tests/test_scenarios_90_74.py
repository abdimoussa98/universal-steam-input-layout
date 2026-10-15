"""Scenarios for 90.74: the right stick in the four Fn layers.

The record is findings/2026-10-15-fn-right-stick/README.md; the plan is
plans/2026-10-14-key-layer-click-and-fn-right-stick.md, part 2.

- On the Deck the right stick in the Fn layer gave no bump and not its keys, while the left stick worked (author,
  2026-10-14 and 2026-10-15). The two groups had the same shape; only the right one stated `deadzone` 13276 and
  `requires_click` 0. Since 90.74 the right stick's group has the left stick's settings, and keeps its own keys
  (`;` up, `'` down, `.` right, `,` left, the author's), its R3 guard and its cleanups, each key with a Low bump.
"""
import unittest

from steam_layout.model import Layout
from tests.scenario import VARIANTS, ScenarioCase, layout_data, scenario

FN_LAYERS = ("Menu Left: Fn Layer", "Menu Right: Fn Layer", "Stateful | Menu Left: Fn Layer",
             "Stateful | Menu Right: Fn Layer")
KEYS = {"up": "SEMICOLON", "down": "SINGLE_QUOTE", "right": "PERIOD", "left": "COMMA"}
PARTS = {"up": "dpad_north", "down": "dpad_south", "right": "dpad_east", "left": "dpad_west"}
MENU = {"Menu Left": "Select", "Menu Right": "Start"}


class Shape(unittest.TestCase):
    def test_the_right_stick_has_the_left_sticks_settings_and_its_own_keys_with_a_low_bump(self):
        for variant in VARIANTS:
            layout = Layout(layout_data(variant))
            for title in FN_LAYERS:
                left, right = layout.active(title)["joystick"], layout.active(title)["right_joystick"]
                self.assertEqual(right["settings"], left["settings"], (variant, title))
                self.assertNotIn("deadzone", right["settings"])
                for where, part in PARTS.items():
                    key, guard = right["inputs"][part]["activators"]["chord"]
                    self.assertEqual(key["bindings"]["binding"], f"key_press {KEYS[where]}, , ")
                    self.assertEqual(key["settings"].get("haptic_intensity"), "1", (variant, title, where))
                    self.assertEqual(guard["settings"], {"chord_button": "20", "interruptable": "0"})


class FnRightStick(ScenarioCase):
    @scenario("90.74 F1", rests=("A5", "A6"))
    def test_each_direction_types_its_key_from_the_fn_layer(self):
        for side, button in MENU.items():
            for steering in (False, True):
                for where, key in KEYS.items():
                    for pad in self.each():
                        if steering:
                            pad.enter_steering().lift("LS").wait(300)
                        pad.hold(button).wait(300)
                        prefix = "Stateful | " if steering else ""
                        self.assertEqual(pad.top, f"{prefix}{side}: Fn Layer")
                        pad.mark().push("RS", where).wait(80)
                        self.assertEqual(pad.typed(), [key], (side, steering, where))
                        pad.recentre("RS").lift("RS").let_go(button).wait(300)

    @scenario("90.74 F2", rests=("A5", "A6", "A10"))
    def test_with_the_thumb_already_on_the_right_stick(self):
        for side, button in MENU.items():
            for pad in self.each():
                pad.touch("RS").wait(300).hold(button).wait(300)
                self.assertEqual(pad.top, f"{side}: Fn Layer")
                pad.mark().push("RS", "right").wait(80)
                self.assertEqual(pad.typed(), ["PERIOD"])


if __name__ == "__main__":
    unittest.main()
