"""Scenarios for 90.74: the right stick in the four Fn layers.

The record is findings/2026-10-15-fn-right-stick/README.md; the plan is
plans/2026-10-14-key-layer-click-and-fn-right-stick.md, part 2.

- On the Deck the right stick in the Fn layer gave no bump and not its keys, while the left stick worked (author,
  2026-10-14 and 2026-10-15). The two groups had the same shape; only the right one stated `deadzone` 13276 and
  `requires_click` 0. Since 90.74 the right stick's group has the left stick's settings, and keeps its own keys
  (`;` up, `'` down, `.` right, `,` left, the author's), its R3 guard and its cleanups, each key with a Low bump.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_74 import *

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
