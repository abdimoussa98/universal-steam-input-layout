"""Scenarios for 90.31: the fallback's second lives in a window.

The plan is plans/2026-10-04-fallback-window.md, the author's design; the record is
findings/2026-10-04-fallback-window/README.md. All of it is in Steering with no driver held.

- Stick up or down adds `Steering | LS: Fallback Hold` and, on top, `Steering | LS: Fallback
  Window`, which types W or S, pulses, and removes itself after 1000 ms.
- Letting up or down go, or the edge, inside that second removes both; Steering stays.
- After the second the Fallback Hold is on top and types W or S. Letting go then leaves Steering.
- A driver or a menu button leaves Steering, inside the second or after it: in the window it
  removes the window alone, and the Fallback Hold's repeating bind for it does the rest.
- The Entry Guard ends on any direction's Release.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

WINDOW, HOLD, GUARD = "Steering | LS: Fallback Window", "Steering | LS: Fallback Hold", "Steering | LS: Entry Guard"
NORTH, SOUTH = ("joystick", "dpad_north"), ("joystick", "dpad_south")
BOTH = (("up", "W", NORTH), ("down", "S", SOUTH))


def left_steering(pad):
    return pad.lacks("Steering", HOLD, WINDOW)


class FallbackWindow(ScenarioCase):
    @scenario("90.31 F1", rules=("R137", "R161"), rests=("A8", "A10", "A11", "A16"))
    def test_holding_past_the_second_and_letting_go_leaves_steering(self):
        for direction, key, _ in BOTH:
            for pad in self.each(start="steering"):
                pad.mark().push("LS", direction)
                self.assertEqual((pad.names()[-2:], pad.down()), ((HOLD, WINDOW), [key]))   # the hold, the window on top
                pad.wait(999)
                self.assertEqual(pad.top, WINDOW)
                self.assertEqual(len(pad.seen("haptic")), 4)                # the pulse: at once, then every 250 ms
                pad.wait(2)
                self.assertEqual((pad.top, pad.down()), (HOLD, [key]))      # the window is gone and the key carries on (A11)
                pad.mark().wait(2000)
                self.assertTrue(pad.has("Steering", HOLD))                  # nothing leaves while the stick is held
                self.assertEqual((pad.seen("haptic", "beep"), pad.down()), ([], [key]))
                pad.mark().recentre("LS")
                self.assertTrue(left_steering(pad))
                self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], ["haptic", "beep"])
                self.assertEqual(pad.seen("beep"), [("beep", "Steering")])

    @scenario("90.31 F2", rules=("R137",), rests=("A8", "A10"))
    def test_letting_go_inside_the_second_keeps_steering_every_time(self):
        for direction, key, control in BOTH:
            for pad in self.each(start="steering"):
                for held in (100, 500, 990):
                    pad.push("LS", direction).wait(held)
                    self.assertEqual((pad.top, pad.down()), (WINDOW, [key]))
                    pad.sim.release(control)                                 # up or down lets go before the edge does
                    self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), []))
                    pad.recentre("LS").wait(300)
                    self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.31 F3", rules=("R137",), rests=("A8", "A10", "A16"))
    def test_a_roll_to_the_side_ends_the_second_and_coming_back_starts_a_new_one(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(600).roll("LS", "left")
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), ["A"]))
            pad.wait(2000)                                                   # no timer runs on A
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))
            pad.roll("LS", "up").wait(999)
            self.assertEqual(pad.top, WINDOW)                                # a full second again
            pad.wait(2).recentre("LS")
            self.assertTrue(left_steering(pad))

    @scenario("90.31 F4", rules=("R137",), rests=("A16",), either=("A9",))
    def test_a_driver_or_a_menu_button_leaves_steering_once_the_second_is_over(self):
        """In 90.31 the button also left Steering inside the second: the window removed itself and the Fallback
        Hold answered. Since 90.32 the window blocks it with a replacement (test_scenarios_90_32.py), so a button
        pressed inside the second leaves Steering only if it is still held when the second ends."""
        for button in ("R1", "L1", "Start", "Select"):
            for held in (400, 1500):
                for pad in self.each(start="steering"):
                    pad.push("LS", "up").wait(held)
                    self.assertEqual(pad.top, WINDOW if held < 1000 else HOLD)
                    pad.mark().hold(button).wait(60)                         # the Fallback Hold's bind repeats every 50 ms
                    if held < 1000:
                        self.assertTrue(pad.has("Steering", WINDOW), (button, held))
                        pad.wait(600)                                        # past the end of the second
                    self.assertTrue(left_steering(pad), (button, held))
                    self.assertEqual(pad.seen("beep"), [("beep", "Steering")])
                    pad.let_go(button).lift("LS").wait(600)
                    self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.31 F5", rules=("R137",), rests=("A7", "A16"), either=("A9",))
    def test_a_thumb_leaving_a_stick_starts_the_second_over(self):
        for pad in self.each(start="steering"):
            pad.touch("RS").wait(300).push("LS", "up").wait(600)
            pad.lift("RS").wait(60)                                          # the window's touch Release takes both layers
            self.assertEqual(pad.names()[-2:], (HOLD, WINDOW))               # and Steering's repeating add puts them back
            pad.wait(900)
            self.assertEqual(pad.top, WINDOW)                                # 600 ms in when the thumb lifted: still counting
            pad.wait(150)
            self.assertEqual(pad.top, HOLD)
            pad.recentre("LS")
            self.assertTrue(left_steering(pad))

    @scenario("90.31 F6", rules=("R133",), rests=("A16", "A36"))
    def test_thumbs_resting_on_both_sticks_do_nothing_as_the_window_closes(self):
        """At 1000 ms the Fallback Hold's cleanup binds start answering both stick touches. The chord on
        the left stick being out holds them back (A36); if it didn't, Steering would end here."""
        for pad in self.each(start="steering"):
            pad.touch("RS").wait(300).mark().push("LS", "up").wait(3000)
            self.assertEqual((pad.names()[-2:], pad.down()), (("Steering", HOLD), ["W"]))
            self.assertEqual(pad.seen("beep"), [])
            pad.push("RS").wait(500)                                         # the right stick pushed out as well: still held back
            self.assertTrue(pad.has("Steering", HOLD))

    @scenario("90.31 F7", rules=("R133",), rests=("A17", "A25"))
    def test_after_a_missed_release_a_fresh_stick_touch_leaves_steering(self):
        for stick in ("LS", "RS"):
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(1500)
                pad.sim.lose(NORTH)                                          # the Steam menu was open: no Release was seen
                pad.recentre("LS").wait(500)
                self.assertEqual(pad.top, HOLD)                              # left on; the guard chord latched (A17)
                pad.lift("LS").wait(300).mark().touch(stick).wait(150)
                self.assertTrue(left_steering(pad))                          # the cleanup bind does what the Release would have
                self.assertEqual(pad.seen("beep"), [("beep", "Steering")])

    @scenario("90.31 F8", rules=("R137",), rests=("A25",))
    def test_a_release_missed_inside_the_second_leaves_steering_alone(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(400)
            pad.sim.lose(NORTH)
            pad.recentre("LS").wait(2000)                                    # the edge's Release still clears both
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))


    @scenario("90.31 F9", rests=("A7",))
    def test_after_leaving_by_the_stick_the_left_sticks_touch_gestures_work(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(1100).recentre("LS").wait(50)
            self.assertTrue(left_steering(pad))
            self.assertEqual(pad.top, "LST: Entry Point")                    # Base's touch add, on the thumb that is still down
            pad.lift("LS")
            self.assertEqual(pad.top, "LST: Double Tap")                     # lifted inside 150 ms: the stick's window
            pad.wait(50).touch("LS")
            self.assertTrue(pad.has("LST: Temporary Gyro"))                  # the double touch
            pad.lift("LS").wait(600)
            self.assertEqual(pad.stack, pad.layers("Base"))


class EntryGuard(ScenarioCase):
    @scenario("90.31 G1", rules=("R137",), rests=("A8", "A26"))
    def test_the_entry_guard_ends_when_the_direction_held_at_entry_lets_go(self):
        for direction, key, control in BOTH:
            for pad in self.each():
                pad.push("LS", direction).wait(300).hold("Start").wait(50)
                pad.sim.press(("joystick", "click"))
                pad.wait(30)
                pad.sim.release(("joystick", "click"))
                pad.let_go("Start").wait(50)
                self.assertEqual((pad.names()[-2:], pad.down()), (("Steering", GUARD), [key]))   # the stick was out at entry
                pad.wait(2000)
                self.assertTrue(pad.has("Steering", GUARD))                  # no second, no exit, while the guard is on
                pad.sim.release(control)                                     # the direction lets go; the edge is still out
                self.assertTrue(pad.lacks(GUARD) and pad.has("Steering"))
                pad.recentre("LS").wait(100).push("LS", direction)
                self.assertEqual(pad.names()[-2:], (HOLD, WINDOW))           # the next push starts the fallback's second


if __name__ == "__main__":
    unittest.main()
