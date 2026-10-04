"""Scenarios for 90.16: more exits on the pad click layers, a 5 ms outer delay, and a repeating add on Base.

The author played 90.14 and 90.15 on the Deck: pad click layers got stuck, and a click gave three
or four bumps. The record is findings/2026-10-03-pad-click-exits/README.md. The simulator can't
say why a layer stuck on the Deck; these check that each new exit clears the layers by itself.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

RP = "right_trackpad"
CLICK_LAYERS = ("RTP: Click Entry Point", "RTP: Middle Click", "RTP: Mouse Buttons")


class PadClickExits(ScenarioCase):
    @scenario("90.16 X1", rules=("R136",), rests=("A7",), either=("A9",))
    def test_a_thumb_that_lifts_takes_the_click_layers_and_what_is_under_them(self):
        for where in ("centre", "left"):
            for pad in self.each():
                pad.press_pad("RP", where).wait(100)
                self.assertTrue(pad.has("RTP: Entry Point") and pad.top in ("RTP: Middle Click", "RTP: Mouse Buttons"))
                pad.recentre("RP")
                pad.sim.release((RP, "touch"))                                    # the touch Release, before the click's
                self.assertTrue(pad.lacks("RTP: Entry Point", "RTP: Tap Cover", "RTP: Middle Click", "RTP: Mouse Buttons"))
                self.assertEqual(pad.down(), [])
                pad.sim.release((RP, "click"))
                pad.wait(300)
                self.assertEqual(pad.stack, pad.layers("Base"))                   # and no Double Tap window opened

    @scenario("90.16 X2", rules=("R136",), rests=("A7",))
    def test_a_thumb_that_lifts_in_circular_scroll_ends_the_scroll_too(self):
        touch = (RP, "touch")
        for pad in self.each():
            pad.sim.press(touch).wait(60).release(touch)                          # a centre tap outlasts the 50 ms hand-over (90.25)
            pad.wait(50)
            pad.sim.press(touch).press((RP, "dpad_north")).release((RP, "dpad_north"))
            pad.wait(200).hold("RP click").wait(100)
            self.assertEqual(pad.names()[-2:], ("RTP: Circular Scroll", "RTP: Middle Click"))
            pad.sim.release(touch)
            self.assertTrue(pad.lacks("RTP: Circular Scroll", "RTP: Middle Click"))
            pad.let_go("RP click").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.16 X3", rests=("A6", "A10"), either=("A9",))
    def test_a_click_still_held_after_a_clear_comes_back_only_if_steam_fires_the_exposed_add(self):
        """Changed in 90.20. From 90.16 to 90.19 Base had a second, repeating add, which brought the Click
        Entry Point back either way. Base had one add then, with no repeat: after a clear the layer returned
        only if Steam fired the add it exposed under the held click (A9).

        Changed in 90.25: it comes back either way again: at once if Steam fires the exposed add (A9), on
        Base's next repeat if not. The thumb is still on the pad, so Base's repeating touch add runs the
        hand-over, and the Entry Point's click add repeats, so it fires on a click that is already held (A6)."""
        for pad in self.each(start="steering"):
            pad.hold("L1").wait(50).hold("R1").wait(50).press_pad("RP", "centre").wait(100)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["S", "mouse_button MIDDLE"]))
            pad.let_go("R1").wait(5)                                              # the quick tap clears every layer
            self.assertTrue(pad.lacks("Steering"))
            pad.wait(400)                                                         # Base's touch add may wait for its repeat (A9); the rest is at once
            self.assertEqual((pad.has("RTP: Middle Click"), "mouse_button MIDDLE" in pad.down()), (True, True))
            pad.let_go_pad("RP").wait(400)
            self.assertTrue(pad.lacks(*CLICK_LAYERS))
            pad.press_pad("RP", "centre").wait(100)                               # a new click always works
            self.assertTrue(pad.has("RTP: Middle Click"))

    @scenario("90.16 X4", rules=("R113",), rests=("A6", "A10"))
    def test_the_outer_buttons_come_after_5_ms_and_the_middle_click_at_once(self):
        """Until 2026-10-04 the middle click was read as coming on its 50 ms repeat. A repeating action always
        triggers (author): it fires as the Click Entry Point lands (A6)."""
        for pad in self.each():
            pad.press_pad("RP", "left").wait(4)
            self.assertEqual((pad.top, pad.down()), ("RTP: Click Entry Point", []))
            pad.wait(1)
            self.assertEqual((pad.top, pad.down()), ("RTP: Mouse Buttons", ["mouse_button BACK"]))
        for pad in self.each():
            pad.press_pad("RP", "centre")
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))

    @scenario("90.16 X5")
    def test_a_click_bumps_once_on_base_and_the_entry_point_adds_none(self):
        """The simulator logs a haptic when an entry's commands run. The output's own bump, on the layer
        that lands, is the second one on the Deck (tests/test_pad_click_exits.py checks its setting).

        Since 90.25 the click's bump is on the pad's Entry Point, where its add moved. A touch in the centre
        has the low bump of the hand-over before it (90.25 P1)."""
        touch = ("haptic", "1 RTP: Touch Entry Point right_trackpad/edge")
        click = ("haptic", "3 RTP: Entry Point right_trackpad/click")
        for where, expected in (("centre", [touch, click]), ("left", [click]), ("ring left", [touch, click])):
            for pad in self.each():
                pad.click_pad("RP", where, ms=600).wait(400)
                self.assertEqual(pad.seen("haptic"), expected)
        for pad in self.each():
            pad.click_pad("LP", "up", ms=600).wait(400)
            self.assertEqual(pad.seen("haptic"), [("haptic", "3 LTP: Entry Point left_trackpad/click")])


if __name__ == "__main__":
    unittest.main()
