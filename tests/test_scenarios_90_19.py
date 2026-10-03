"""Scenarios for 90.19: the final pad click layers hold themselves, and the Click Entry Point adds first.

The record is findings/2026-10-03-pad-click-holds/README.md. On the simulator the hold never fires
during an ordinary click: the final layer lands on a pad that is already pressed, and a layer
command doesn't fire on an input that was already held (A5). The inverted Soft Press removal does
the work there, as it did in 90.18. The hold only fires on a fresh press inside the layer.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

FINAL = {("LP", "centre"): "LTP: Middle Click", ("LP", "up"): "LTP: Arrow Keys",
         ("RP", "centre"): "RTP: Middle Click", ("RP", "left"): "RTP: Mouse Buttons"}
ENTRY = {"LP": "LTP: Click Entry Point", "RP": "RTP: Click Entry Point"}


class Holds(ScenarioCase):
    @scenario("90.19 K1", rules=("R113", "R114"), rests=("A5", "A6", "A10"), either=("A9", "A42"))
    def test_an_ordinary_click_comes_and_goes_whether_or_not_the_hold_works(self):
        for (name, where), layer in FINAL.items():
            for pad in self.each():
                pad.press_pad(name, where).wait(60)
                self.assertTrue(pad.has(layer) and pad.lacks(ENTRY[name]))        # added, then the entry point went
                self.assertEqual(len(pad.down()), 1)
                pad.wait(1000)
                self.assertEqual((pad.top, len(pad.down())), (layer, 1))          # one press, held
                pad.let_go_pad(name, lift=False).wait(150)
                self.assertTrue(pad.lacks(layer, ENTRY[name]))
                self.assertEqual(pad.down(), [])
                pad.lift(name).wait(400)
                self.assertEqual((pad.stack, len(pad.typed())), (pad.layers("Base"), 1))

    @scenario("90.19 K2", rests=("A6",), either=("A9", "A42"))
    def test_a_press_inside_a_final_layer_is_held_by_the_layer_and_ends_with_it(self):
        """A click too short for the hand-over leaves the Click Entry Point on; with the thumb still down it
        hands over to a final layer that nobody is pressing. A second press before that layer's backup removal
        fires is a fresh press in the layer: its output and its hold both fire."""
        for pad in self.each():
            pad.press_pad("RP", "centre").wait(30).let_go_pad("RP", lift=False).wait(25)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", []))    # landed on a pad that isn't pressed
            pad.hold("RP click").wait(300)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))
            pad.let_go("RP click").wait(150)
            self.assertTrue(pad.lacks("RTP: Middle Click", "RTP: Click Entry Point"))
            self.assertEqual((pad.down(), pad.typed()), ([], ["mouse_button MIDDLE"]))

    @scenario("90.19 K3", rules=("R136",), rests=("A7", "A25"), either=("A9", "A42"))
    def test_the_thumb_lifting_and_a_missed_release_still_clear_a_final_layer(self):
        for pad in self.each():
            pad.press_pad("RP", "left").wait(100)
            pad.recentre("RP")
            pad.sim.release(("right_trackpad", "touch"))                          # the thumb lifts
            self.assertTrue(pad.lacks("RTP: Mouse Buttons", "RTP: Entry Point"))
            pad.sim.release(("right_trackpad", "click"))
            pad.wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))
        for pad in self.each():
            pad.press_pad("RP", "centre").wait(100).miss("RP click").wait(300)    # the Steam menu took the release
            self.assertTrue(pad.lacks("RTP: Middle Click", "RTP: Click Entry Point"))
            self.assertEqual(pad.down(), [])


if __name__ == "__main__":
    unittest.main()
