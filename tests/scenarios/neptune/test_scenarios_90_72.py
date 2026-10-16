"""Scenarios for 90.72: stick-edge cleanups on the pad layers, and pad-click stand-ins for what they hide.

The record is findings/2026-10-14-pad-stick-edge-cleanups/README.md; the plan is
plans/2026-10-14-pad-stick-edge-cleanups.md.

- The pad click layers have a cleanup function on both stick edges, the four left-pad key layers on the left edge only:
  a copy of their stick-touch cleanup, guarded by the pad's touch (legacy chord IDs 16 and 17). With stick touch the
  touch cleanup clears a stuck pad layer first; the edges are for a controller without it (author, 2026-10-14).
- While a pad layer is on and its thumb is on the pad, the guard hides the stick edges below. A layer whose edge bind
  would be lost does it on the pad's click instead: the Steering stick layers add their cover, and the cover carries the
  click on into the Click Entry Point; the ramp layers remove themselves and add the left pad's Click Entry Point.
- The menu Entry Points and the two menu chord layers block both pad clicks; the left swipes type their keys (R172).

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_72 import *

class PadStickEdgeCleanups(ScenarioCase):
    @scenario("90.72 E1", rules=("R170",), rests=("A6",))
    def test_a_stuck_pad_layer_clears_on_a_stick_push_with_no_stick_touch(self):
        """The layer is on with no thumb on its pad, and the stick's touch isn't seen: only its edge."""
        for layer in CLICK_LAYERS + KEY_LAYERS:
            for stick in ("joystick", "right_joystick"):
                for pad in self.each(start=("Base", layer)):
                    pad.sim.press((stick, "edge"))
                    pad.wait(200)
                    cleared = stick == "joystick" or layer in CLICK_LAYERS
                    self.assertEqual(not pad_layers(pad), cleared, (layer, stick))

    @scenario("90.72 E2", rests=("A5", "A6", "A10"), either=("A9",))
    def test_a_right_pad_click_in_the_steering_stick_window_adds_the_tap_cover(self):
        for where in ("left", "centre"):
            for pad in self.each(start=("Base", "Steering")):
                pad.hold("R1").push("LS", "up").wait(30).press_pad("RP", where).wait(100)
                self.assertTrue(pad.has("Steering | LS: Tap Cover"), "on the click, not the 200 ms timer")
                self.assertTrue([t for t in pad.names() if t.startswith("RTP: ") and t != "RTP: Entry Point"],
                                "the click carried on into its layer")
                pad.wait(500).mark().recentre("LS").wait(300)
                self.assertEqual([x for x in pad.typed() if "wheel" in x], [], "a hold, not a flick: no scroll")

    @scenario("90.72 E3", rests=("A5", "A6", "A10"), either=("A9",))
    def test_a_right_pad_click_in_a_steering_scroll_layer_adds_the_double_tap_cover(self):
        for pad in self.each(start=("Base", "Steering")):
            pad.hold("R1").flick("LS", "up").wait(60).push("LS", "up").wait(20)
            self.assertTrue(pad.has("Steering | LS Up: Scroll Up"))
            pad.press_pad("RP", "left").wait(100)
            self.assertTrue(pad.has("Steering | LS: Double Tap Cover", "RTP: Mouse Buttons"))

    @scenario("90.72 E4", rests=("A5", "A6", "A10"), either=("A9",))
    def test_a_left_pad_click_ends_the_ramp_and_carries_on(self):
        for pad in self.each():
            pad.push("RS").wait(400)
            self.assertEqual(ramps(pad), list(RAMPS))
            pad.mark().press_pad("LP", "left").wait(100)
            self.assertEqual(ramps(pad), [])
            self.assertTrue(pad.has("LTP: Arrow Keys"))
            self.assertEqual(pad.typed(), ["LEFT_ARROW"])
            pad.let_go_pad("LP").wait(300)
            self.assertTrue(ramps(pad), "the stick is still out: Base's repeating add brings the ramp back")

    @scenario("90.72 E5", rules=("R172",), rests=("A10",))
    def test_inside_a_menu_entry_the_pad_clicks_are_blocked_and_the_swipes_type_their_keys(self):
        for menu in ("Select", "Start"):
            for pad in self.each():
                pad.hold(menu).wait(30).mark()
                pad.click_pad("RP", "left").wait(50).click_pad("LP", "left").wait(50)
                self.assertFalse([t for t in pad.names() if t.startswith(("LTP", "RTP: Click", "RTP: Mouse",
                                                                          "RTP: Middle"))])
                pad.touch("LP").sim.press(("left_trackpad", "dpad_north"))
                pad.wait(50)
                self.assertFalse(pad_layers(pad), "a swipe types its key, with no key layer")
                self.assertIn("TAB", pad.typed())

    @scenario("90.72 E6", rests=("A5", "A6", "A10"))
    def test_scroll_click_into_mouse_buttons_back_to_scroll_and_a_lift_clears_all(self):
        touch = (RP, "touch")
        for pad in self.each():
            pad.sim.press(touch).wait(60).release(touch)
            pad.wait(50)
            pad.sim.press(touch).press((RP, "dpad_north")).release((RP, "dpad_north"))
            pad.wait(200)
            self.assertEqual(pad.top, "RTP: Circular Scroll")
            pad.sim.press((RP, "edge")).press((RP, "dpad_west")).press((RP, "click"))
            pad.wait(100)
            self.assertEqual(pad.names()[-2:], ("RTP: Circular Scroll", "RTP: Mouse Buttons"))
            pad.sim.release((RP, "click"))
            pad.wait(100)
            pad.sim.release((RP, "dpad_west")).release((RP, "edge"))
            pad.wait(100)
            self.assertEqual(pad.top, "RTP: Circular Scroll", "the direction's Release took only Mouse Buttons")
            pad.lift("RP").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.72 E7", rests=("A5", "A6", "A10"))
    def test_a_touch_release_clears_only_its_own_pad(self):
        for pad in self.each():
            pad.press_pad("LP", "left").wait(100).press_pad("RP", "left").wait(100)
            self.assertTrue(pad.has("LTP: Arrow Keys", "RTP: Mouse Buttons"))
            pad.let_go_pad("RP").wait(300)
            self.assertTrue(pad.has("LTP: Arrow Keys"))
            self.assertFalse([t for t in pad.names() if t.startswith("RTP")])
            pad.let_go_pad("LP").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base"))


    @scenario("90.72 E8", rules=("R172",), rests=("A1", "A2"))
    def test_inside_a_menu_hold_the_right_pad_opens_nothing_and_a_lift_clears_what_was_on(self):
        touch = (RP, "touch")
        for menu in ("Select", "Start"):
            for pad in self.each():                                         # the menu first: nothing opens
                pad.hold(menu).wait(30)
                pad.sim.press(touch).wait(60).release(touch)
                pad.wait(50)
                pad.sim.press(touch).press((RP, "dpad_north")).release((RP, "dpad_north"))
                pad.wait(100).mark()
                pad.sim.press((RP, "edge")).press((RP, "dpad_west")).press((RP, "click"))
                pad.wait(100)
                self.assertFalse([t for t in pad.names() if t.startswith("RTP")])
                self.assertEqual(pad.typed(), [])
            for pad in self.each():                                         # scrolling first: the lift clears it
                pad.sim.press(touch).wait(60).release(touch)
                pad.wait(50)
                pad.sim.press(touch).press((RP, "dpad_north")).release((RP, "dpad_north"))
                pad.wait(100)
                self.assertTrue(pad.has("RTP: Circular Scroll"))
                pad.hold(menu).wait(30).lift("RP").wait(100)
                self.assertFalse([t for t in pad.names() if t.startswith("RTP")])
                self.assertTrue([t for t in pad.names() if "Menu" in t], "the lift does not end the menu hold")


if __name__ == "__main__":
    unittest.main()
