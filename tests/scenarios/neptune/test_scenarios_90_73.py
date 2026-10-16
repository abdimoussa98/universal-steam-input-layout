"""Scenarios for 90.73: the left pad's click in the four key layers.

The record is findings/2026-10-15-key-layer-click/README.md; the plan is
plans/2026-10-14-key-layer-click-and-fn-right-stick.md, part 1.

- In `Escape`, `Tab`, `Backspace` and `Enter` the left pad's click is a repeating, silent Soft Press that removes the
  layer itself. Base's repeating click then fires on the held click and adds `LTP: Click Entry Point`, so a click after
  a swipe goes where a click from Base goes (author, 2026-10-14).
"""
import unittest

from tests.scenario import ScenarioCase, scenario

LP = "left_trackpad"
SWIPES = {"Escape": ("left", "dpad_west", "ESCAPE"), "Enter": ("right", "dpad_east", "RETURN"),
          "Tab": ("up", "dpad_north", "TAB"), "Backspace": ("down", "dpad_south", "BACKSPACE")}
ARROWS = {"left": "LEFT_ARROW", "right": "RIGHT_ARROW", "up": "UP_ARROW", "down": "DOWN_ARROW"}


def swipe(pad, direction):
    """The thumb lands on the left pad and slides out to a direction, with no click: Base's swipe."""
    pad.touch("LP").wait(20)
    pad.sim.press((LP, "edge"))
    pad.sim.press((LP, SWIPES_BY_DIRECTION[direction]))
    return pad.wait(60)


SWIPES_BY_DIRECTION = {where: part for where, part, _ in SWIPES.values()}


class KeyLayerClick(ScenarioCase):
    @scenario("90.73 K1", rests=("A5", "A6"), either=("A9",))
    def test_a_click_after_a_swipe_goes_where_a_click_from_base_goes(self):
        for layer, (where, part, key) in SWIPES.items():
            for pad in self.each():
                swipe(pad, where)
                self.assertEqual(pad.top, layer)
                pad.sim.press((LP, "click"))
                pad.wait(150)
                self.assertTrue(pad.lacks(layer), "the click removes the key layer")
                self.assertTrue(pad.has("LTP: Arrow Keys"), "Base's click carried on, at the ring")
                self.assertEqual(pad.typed(), [key, ARROWS[where]])
                pad.sim.release((LP, part))
                pad.sim.release((LP, "click"))
                pad.lift("LP").wait(150)
                self.assertEqual(pad.names(), ("Base",))

    @scenario("90.73 K2", rests=("A5", "A6", "A39"), either=("A9",))
    def test_a_click_back_at_the_centre_after_a_swipe_is_the_middle_click(self):
        for layer, (where, part, key) in SWIPES.items():
            for pad in self.each():
                swipe(pad, where)
                pad.sim.release((LP, part))
                pad.sim.release((LP, "edge"))
                pad.wait(30)
                self.assertEqual(pad.top, layer, "back at the centre, the key layer is still on")
                pad.sim.press((LP, "click"))
                pad.wait(150)
                self.assertTrue(pad.lacks(layer))
                self.assertTrue(pad.has("LTP: Middle Click"))
                pad.sim.release((LP, "click"))
                pad.lift("LP").wait(150)
                self.assertEqual(pad.names(), ("Base",))

    @scenario("90.73 K3")
    def test_a_swipe_and_a_lift_without_a_click_is_unchanged(self):
        for layer, (where, part, key) in SWIPES.items():
            for pad in self.each():
                swipe(pad, where)
                pad.sim.release((LP, part))
                pad.lift("LP").wait(100)
                self.assertEqual(pad.typed(), [key])
                self.assertEqual(pad.names(), ("Base",))

    @scenario("90.73 K4")
    def test_the_click_is_a_silent_repeating_soft_press_that_removes_the_layer(self):
        for pad in self.each():
            for layer in SWIPES:
                group = pad.layout.active(layer)[LP]
                entry = group["inputs"]["click"]["activators"]["Soft_Press"]
                self.assertEqual(pad.layout.layer_ops(entry), [("remove_layer", layer)])
                self.assertEqual(entry["settings"], {"haptic_intensity": "0", "hold_repeats": "1",
                                                     "repeat_rate": "50", "interruptable": "0"})


if __name__ == "__main__":
    unittest.main()
