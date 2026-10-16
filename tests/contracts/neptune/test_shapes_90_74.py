"""Scenarios for 90.74: the right stick in the four Fn layers.

The record is findings/2026-10-15-fn-right-stick/README.md; the plan is
plans/2026-10-14-key-layer-click-and-fn-right-stick.md, part 2.

- On the Deck the right stick in the Fn layer gave no bump and not its keys, while the left stick worked (author,
  2026-10-14 and 2026-10-15). The two groups had the same shape; only the right one stated `deadzone` 13276 and
  `requires_click` 0. Since 90.74 the right stick's group has the left stick's settings, and keeps its own keys
  (`;` up, `'` down, `.` right, `,` left, the author's), its R3 guard and its cleanups, each key with a Low bump.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_74 import *

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


if __name__ == "__main__":
    unittest.main()
