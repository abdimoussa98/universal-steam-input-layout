"""Scenarios for 90.27: the pad touch bump is out, and the pads are those of 90.24 again.

The record is findings/2026-10-04-pad-bump-removal/README.md; how the bump was built is in
findings/2026-10-04-pad-touch-bump/README.md.

- A touch gives no bump. On the right pad it puts `RTP: Entry Point` on as the thumb lands; on the
  left pad it does nothing.
- Base has the clicks and the left pad's swipes again. The click layers are as before: the centre
  click at once, the outer buttons 5 ms later, and the centre wins where the two ranges meet.
- A left-pad touch does nothing to a hold that is counting (90.26 D1). A right-pad touch does only
  what the Tap Cover reset on `RTP: Entry Point` does (90.26 D3).
"""
import unittest

from tests.scenario import DIRECTIONS, SOURCES, ScenarioCase, scenario

# pad: centre layer and key, outer layer and its key for a click on the left
CLICKS = {"RP": ("RTP: Middle Click", "mouse_button MIDDLE", "RTP: Mouse Buttons", "mouse_button BACK"),
          "LP": ("LTP: Middle Click", "CAPSLOCK", "LTP: Arrow Keys", "LEFT_ARROW")}


def haptics(pad):
    return [detail for _, detail in pad.seen("haptic")]


class Pads(ScenarioCase):
    @scenario("90.27 B1", rests=("A16",))
    def test_a_touch_gives_no_bump_and_the_right_pads_entry_point_comes_at_once(self):
        for where in ("centre", "ring", "rim"):
            for pad in self.each():
                if where != "centre":
                    (pad.sim.press_between if where == "ring" else pad.sim.press)((SOURCES["RP"], "edge"))
                pad.touch("RP")
                self.assertEqual((pad.stack, haptics(pad)), (pad.layers("Base", "RTP: Entry Point"), []), where)
                pad.wait(150)
                self.assertEqual((pad.top, haptics(pad)), ("RTP: Tap Cover", []))
                pad.lift("RP").wait(400)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))
        for pad in self.each():                                              # the left pad's touch is bound to nothing
            pad.touch("LP").wait(400)
            self.assertEqual((pad.stack, haptics(pad)), (pad.layers("Base"), []))
            pad.lift("LP").wait(400)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))

    @scenario("90.27 B2", rests=("A6", "A40", "A41"))
    def test_the_clicks_come_from_base_with_one_pulse(self):
        for name, (centre, key, outer, outer_key) in CLICKS.items():
            source = SOURCES[name]
            for where, layer, down, after in (("centre", centre, key, 0), ("ring left", centre, key, 0), ("left", outer, outer_key, 5)):
                for pad in self.each():
                    pad.press_pad(name, where)
                    if after:                                                # the outer bind's delay
                        pad.wait(after - 1)
                        self.assertEqual(pad.down(), [])
                        pad.wait(1)
                    self.assertEqual((pad.top, pad.down()), (layer, [down]), (name, where))
                    self.assertEqual(haptics(pad), [f"3 Base {source}/click"])
                    pad.let_go_pad(name).wait(400)
                    self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.27 B3", rests=("A10",))
    def test_a_swipe_needs_no_layer_under_it(self):
        for direction, key, layer in (("left", "ESCAPE", "Escape"), ("right", "RETURN", "Enter"),
                                      ("up", "TAB", "Tab"), ("down", "BACKSPACE", "Backspace")):
            for pad in self.each():
                pad.touch("LP")
                self.assertEqual(pad.stack, pad.layers("Base"))
                pad.sim.press((SOURCES["LP"], DIRECTIONS[direction]))
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base", layer), [key]))
                pad.sim.release((SOURCES["LP"], DIRECTIONS[direction]))
                pad.lift("LP").wait(300)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.27 B4", rests=("A10",))
    def test_steering_and_the_tap_cover_use_bases_click(self):
        for pad in self.each(start="steering"):
            pad.mark().click_pad("RP", "centre")
            self.assertEqual((pad.typed(), haptics(pad)), (["mouse_button MIDDLE"], ["3 Base right_trackpad/click"]))
            pad.wait(300)
            self.assertEqual(pad.top, "Steering")
        for pad in self.each():                                              # a thumb that has rested: the Tap Cover is on
            pad.touch("RP").wait(400).mark()
            self.assertEqual(pad.top, "RTP: Tap Cover")
            pad.sim.press((SOURCES["RP"], "click"))
            self.assertEqual((pad.down(), haptics(pad)), (["mouse_button MIDDLE"], ["3 Base right_trackpad/click"]))
            pad.sim.release((SOURCES["RP"], "click"))
            pad.lift("RP").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))


if __name__ == "__main__":
    unittest.main()
