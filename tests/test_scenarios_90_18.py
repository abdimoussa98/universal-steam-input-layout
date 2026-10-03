"""Scenarios for 90.18: the Click Entry Point removes itself when it adds the chosen layer.

The record is findings/2026-10-03-pad-click-handoff/README.md. The Click Entry Point binds no
click any more: it ends by handing over, or when the thumb lifts.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

ENTRY = {"LP": "LTP: Click Entry Point", "RP": "RTP: Click Entry Point"}
CHOSEN = {("LP", "centre"): "LTP: Middle Click", ("LP", "up"): "LTP: Arrow Keys",
          ("RP", "centre"): "RTP: Middle Click", ("RP", "left"): "RTP: Mouse Buttons"}


class Handoff(ScenarioCase):
    @scenario("90.18 H1", rules=("R113",), rests=("A6", "A10", "A40", "A41"))
    def test_the_entry_point_is_gone_once_the_chosen_layer_is_on(self):
        for (name, where), layer in CHOSEN.items():
            for pad in self.each():
                pad.press_pad(name, where)
                self.assertEqual(pad.top, ENTRY[name])                            # until one Soft Press fires
                pad.wait(60)
                self.assertTrue(pad.has(layer) and pad.lacks(ENTRY[name]))
                self.assertEqual(len(pad.down()), 1)
                pad.wait(1000)
                self.assertTrue(pad.has(layer) and pad.lacks(ENTRY[name]))        # Base doesn't bring it back
                pad.let_go_pad(name).wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.18 H2", rules=("R114",), rests=("A6",), either=("A9",))
    def test_a_click_that_ends_before_the_hand_over_sends_nothing_and_clears(self):
        """The entry point has no click exit, so it is still on when a short click ends. With the thumb still
        on the pad, its Soft Press hands over anyway; the chosen layer finds the pad not pressed and leaves."""
        for where, ms in (("centre", 30), ("left", 2)):
            for pad in self.each():
                pad.press_pad("RP", where).wait(ms).let_go_pad("RP", lift=False)
                self.assertEqual(pad.top, "RTP: Click Entry Point")
                pad.wait(400)
                self.assertTrue(pad.lacks("RTP: Click Entry Point", "RTP: Middle Click", "RTP: Mouse Buttons"))
                self.assertEqual((pad.typed(), pad.down()), ([], []))

    @scenario("90.18 H3", rules=("R136",), rests=("A7", "A40"), either=("A9",))
    def test_a_thumb_that_lifts_ends_the_entry_point(self):
        for pad in self.each():
            pad.press_pad("RP", "centre").wait(20)
            self.assertEqual(pad.top, "RTP: Click Entry Point")
            pad.let_go_pad("RP").wait(400)                                        # the click lets go, then the thumb
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))

    @scenario("90.18 H4", rests=("A40",), either=("A9",))
    def test_a_touch_release_seen_before_the_click_lets_go(self):
        """If Steam reports the thumb gone while the pad still reads as pressed, the touch Release removes the
        entry point and Base adds it again. It has no click exit now, so what ends it is its centre Soft Press
        handing over with no thumb on the pad: an inverted Soft Press has to count as true then (A40). If it
        doesn't, the entry point stays on until the pad is touched again."""
        for pad in self.each():
            pad.press_pad("RP", "centre").wait(20)
            pad.sim.release(("right_trackpad", "touch"))
            self.assertTrue(pad.lacks("RTP: Entry Point"))
            pad.wait(10)                                                          # Base may have added the entry point again
            pad.sim.release(("right_trackpad", "click"))
            pad.wait(400)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))


if __name__ == "__main__":
    unittest.main()
