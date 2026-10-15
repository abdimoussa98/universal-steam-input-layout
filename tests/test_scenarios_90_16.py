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
    # On the 90.70 build: since 90.71 the final layers have no inverted repeating removal on the click and the
    # D-pad layers work on touch; the 90.71 counterparts are in test_scenarios_90_71.py.
    @scenario("90.16 X1", rules=("R136",), rests=("A6", "A7"), either=("A9",), frozen="90.70")
    def test_a_thumb_that_lifts_takes_the_click_layers_and_what_is_under_them(self):
        """Base has the click's add (not from 90.25 to 90.26). With the click still down it is exposed: if
        Steam fires it (A9) the Click Entry Point lands on the held click and its centre bind, which
        repeats, fires at once (A6), so the centre click is back until the click lets go."""
        for where in ("centre", "left"):
            for pad in self.each():
                pad.press_pad("RP", where).wait(100)
                self.assertTrue(pad.has("RTP: Entry Point") and pad.top in ("RTP: Middle Click", "RTP: Mouse Buttons"))
                pad.recentre("RP")
                pad.sim.release((RP, "touch"))                                    # the touch Release, before the click's
                self.assertTrue(pad.lacks("RTP: Entry Point", "RTP: Tap Cover", "RTP: Mouse Buttons"))
                back = pad.sim.exposed_fires
                self.assertEqual((pad.has("RTP: Middle Click"), pad.down()), (back, ["mouse_button MIDDLE"] if back else []))
                pad.sim.release((RP, "click"))
                pad.wait(300)
                self.assertEqual(pad.stack, pad.layers("Base"))                   # and no Double Tap window opened

    # On the 90.70 build: since 90.71 the final layers have no inverted repeating removal on the click and the
    # D-pad layers work on touch; the 90.71 counterparts are in test_scenarios_90_71.py.
    @scenario("90.16 X2", rules=("R136",), rests=("A6", "A7"), either=("A9",), frozen="90.70")
    def test_a_thumb_that_lifts_in_circular_scroll_ends_the_scroll_too(self):
        touch = (RP, "touch")
        for pad in self.each():
            pad.sim.press(touch).release(touch)
            pad.wait(50)
            pad.sim.press(touch).press((RP, "dpad_north")).release((RP, "dpad_north"))
            pad.wait(200).hold("RP click").wait(100)
            self.assertEqual(pad.names()[-2:], ("RTP: Circular Scroll", "RTP: Middle Click"))
            pad.sim.release(touch)
            self.assertTrue(pad.lacks("RTP: Circular Scroll"))
            self.assertEqual(pad.has("RTP: Middle Click"), pad.sim.exposed_fires)  # Base's click, exposed under the held one (X1)
            pad.let_go("RP click").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.16 X3", rests=("A6", "A10"), either=("A9",), frozen="90.56")
    def test_a_click_still_held_after_a_clear_comes_back_only_if_steam_fires_the_exposed_add(self):
        """On the 90.56 build: the clear here is the Steering Modifier 2 quick tap, which 90.57 took out. A click
        held through the second driver's Release now stays down (90.57 P1).

        Changed in 90.20. From 90.16 to 90.19 Base had a second, repeating add, which brought the Click
        Entry Point back either way. Base has one add now, with no repeat: after a clear the layer returns
        only if Steam fires the add it exposed under the held click (A9). Otherwise the next click does it.
        From 90.25 to 90.26 the add was in the pad's Entry Point and repeated, so it came back either way."""
        for pad in self.each(start="steering"):
            # Keep the original resting-thumb recovery context explicit now
            # that the generic Steering fixture starts with both thumbs up.
            pad.touch("LS").wait(300)
            pad.hold("L1").wait(50).hold("R1").wait(50).press_pad("RP", "centre").wait(100)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["S", "mouse_button MIDDLE"]))
            pad.let_go("R1").wait(5)                                              # pad cleanup still runs; Steering stays since 90.44
            self.assertTrue(pad.has("Steering") and pad.lacks("Steering | L1!R1: Modifier 2"))
            pad.wait(150)
            self.assertEqual((pad.has("RTP: Middle Click"), "mouse_button MIDDLE" in pad.down()),
                             (pad.sim.exposed_fires, pad.sim.exposed_fires))
            pad.let_go_pad("RP").wait(400)
            self.assertTrue(pad.lacks(*CLICK_LAYERS))
            pad.press_pad("RP", "centre").wait(100)                               # a new click always works
            self.assertTrue(pad.has("RTP: Middle Click"))
            pad.let_go_pad("RP").let_go("L1").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering", "LST: Entry Point", "LST: Tap Cover"))
            pad.lift("LS").wait(300)
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), []))

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

    @scenario("90.16 X5", frozen="90.49")
    def test_a_click_bumps_once_on_base_and_the_entry_point_adds_none(self):
        """Historical 90.49 entry-feedback behavior; 90.50 moves it to the final output."""
        for where in ("centre", "left", "ring left"):
            for pad in self.each():
                pad.click_pad("RP", where, ms=600).wait(400)
                self.assertEqual(pad.seen("haptic"), [("haptic", "1 Base right_trackpad/click")])
        for pad in self.each():
            pad.click_pad("LP", "up", ms=600).wait(400)
            self.assertEqual(pad.seen("haptic"), [("haptic", "1 Base left_trackpad/click")])


if __name__ == "__main__":
    unittest.main()
