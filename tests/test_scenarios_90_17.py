"""Scenarios for 90.17: the pad click layers are moved by Soft Presses only, and both adds repeat.

The record is findings/2026-10-03-pad-click-soft-press-only/README.md. The simulator has one
"click" per pad: it can't tell the Soft Press threshold from the full click, which is the reason
the click's Release went. What it can show is that the layers still come and go without it.
"""
import unittest

from tests.scenario import ScenarioCase, scenario


class SoftPressOnly(ScenarioCase):
    @scenario("90.17 S1", rests=("A6", "A10"), either=("A9",))
    def test_the_d_pad_layer_comes_back_under_a_held_click_only_if_steam_fires_the_exposed_add(self):
        """Changed in 90.20, with Base's repeating add gone: see 90.16 X3."""
        for pad in self.each(start="steering"):
            pad.hold("L1").wait(50).hold("R1").wait(50).press_pad("RP", "left").wait(100)
            self.assertEqual((pad.top, "mouse_button BACK" in pad.down()), ("RTP: Mouse Buttons", True))
            pad.let_go("R1").wait(2)                                              # pad cleanup still runs; Steering stays since 90.44
            self.assertTrue(pad.has("Steering") and pad.lacks("Steering | L1!R1: Modifier 2", "RTP: Mouse Buttons"))
            pad.wait(150)
            self.assertEqual((pad.has("RTP: Mouse Buttons"), "mouse_button BACK" in pad.down()),
                             (pad.sim.exposed_fires, pad.sim.exposed_fires))
            pad.let_go_pad("RP").wait(400)
            self.assertTrue(pad.lacks("RTP: Click Entry Point", "RTP: Mouse Buttons", "RTP: Middle Click"))
            pad.let_go("L1").wait(300)
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), []))

    @scenario("90.17 S2", rules=("R113",), rests=("A6", "A10", "A40", "A41"))
    def test_the_left_centre_holds_caps_lock_and_lets_go_with_the_click(self):
        for pad in self.each():
            pad.press_pad("LP", "centre").wait(500)
            self.assertEqual((pad.top, pad.down()), ("LTP: Middle Click", ["CAPSLOCK"]))
            pad.let_go_pad("LP", lift=False)                                      # the thumb stays on the pad
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base"), []))   # the Soft Press exit alone
            pad.lift("LP").wait(300)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), ["CAPSLOCK"]))

    @scenario("90.17 S3", rules=("R114",), rests=("A25",), either=("A9",))
    def test_each_click_layer_clears_by_its_soft_press_exit_with_the_thumb_still_down(self):
        for where, layer in (("centre", "RTP: Middle Click"), ("left", "RTP: Mouse Buttons")):
            for pad in self.each():
                pad.press_pad("RP", where).wait(100)
                self.assertTrue(pad.has(layer))
                pad.let_go_pad("RP", lift=False).wait(120)
                self.assertTrue(pad.lacks("RTP: Click Entry Point", layer))
                self.assertTrue(pad.has("RTP: Entry Point"))                      # the touch layer stays: no thumb lift


if __name__ == "__main__":
    unittest.main()
