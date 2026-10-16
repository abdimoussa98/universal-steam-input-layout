"""Scenarios for 90.35: `Steering` and its fallback guard swap places.

The record is findings/2026-10-06-steering-fallback-swap/README.md, the author's design of
2026-10-06: on the Deck the guard's eight-way stick did not take effect over `Steering`'s four-way
one, so one layer leaves as the other comes. "R1" and "L1" are the modifier pair, which are also
Steering's drivers.

These swap scenarios use the frozen 90.41 builder. Since 90.42 a full
unmodified up/down deflection exits Steering directly, tested in 90.42.

- Stick up or down in Steering base adds the guard and then removes `Steering`.
- Every bind in the guard that removes it adds `Steering` first: a bumper at centre, and a fresh
  touch of either stick with the left stick at centre.
- The guard has `Steering`'s Start and Select and its right pad, since `Steering` is not under it.
- The other fallback scenarios are 90.33's and 90.34's.
"""
import unittest

from tests.scenario import ScenarioCase, scenario, old_inverted_chord

GUARD = "Steering | LS: Fallback Guard"
PAD_LAYERS = ("RTP: Entry Point", "RTP: Tap Cover", "RTP: Double Tap", "RTP: Circular Scroll", "RTP: Mouse Buttons")


def mode(pad):
    """Which of the two is on: exactly one, in every state between gestures."""
    on = [title for title in ("Steering", GUARD) if pad.has(title)]
    return on[0] if len(on) == 1 else on


class TheSwap(ScenarioCase):
    @old_inverted_chord
    @scenario("90.35 S1", rules=("R157",), rests=("A10",), frozen="90.41")
    def test_one_of_the_two_is_on_through_a_whole_round(self):
        for pad in self.each(start="steering"):
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))
            pad.push("LS", "up").wait(100)
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", GUARD), ["W"]))     # handed over
            pad.recentre("LS").wait(300).push("LS", "down").wait(100)
            self.assertEqual((mode(pad), pad.down()), (GUARD, ["S"]))
            pad.hold("L1").wait(100)                                                         # a modifier, over the guard
            self.assertEqual(mode(pad), GUARD)
            pad.let_go("L1").wait(500).recentre("LS").wait(200).hold("R1").wait(100)         # handed back, and driving
            self.assertEqual((mode(pad), pad.top, pad.down()), ("Steering", "Steering | R1: W Key", ["W"]))
            pad.push("LS", "up").wait(200).let_go("R1").wait(200)                            # the stick is up: over again
            self.assertEqual((mode(pad), pad.down()), (GUARD, ["W"]))
            pad.lift("LS").wait(200).touch("LS").wait(200).lift("LS").wait(300)              # the touch hands back
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @old_inverted_chord
    @scenario("90.35 S2", rules=("R133", "R161"), rests=("A6",), frozen="90.41")
    def test_a_bumper_at_centre_hands_back_and_drives_without_waiting_for_an_exposed_bind(self):
        # Steering lands on the held bumper, so its repeating driver bind fires as it lands (A6). In 90.33 and
        # 90.34 Steering was underneath and the bind had to fire on being exposed (A9).
        for driver, layer, key in (("R1", "Steering | R1: W Key", "W"), ("L1", "Steering | L1: S Key", "S")):
            for exposed in (True, False):
                for pad in self.each(start="steering", exposed_fires=exposed):
                    pad.push("LS", "up").wait(200).recentre("LS").wait(200).mark().hold(driver).wait(5)
                    self.assertEqual((mode(pad), pad.top, pad.down()), ("Steering", layer, [key]), (driver, exposed))
                    self.assertEqual(len([d for _, d in pad.seen("haptic") if d.startswith(f"1 {pad.title(GUARD)}")]), 1)
                    self.assertEqual(pad.seen("beep"), [])                               # a swap, not an entry: no beep

    @old_inverted_chord
    @scenario("90.35 S3", rules=("R169",), rests=("A17", "A36"), frozen="90.41")
    def test_a_fresh_stick_touch_at_centre_hands_back_too(self):
        # The author, 2026-10-06: "it would keep them and they would first add steering back and remove fallback."
        for stick in ("LS", "RS"):
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(200).lift("LS").lift("RS").wait(300)
                self.assertEqual(mode(pad), GUARD)
                pad.touch(stick).wait(150)
                self.assertEqual(mode(pad), "Steering", stick)
                pad.lift(stick).wait(300).hold("R1").wait(60)                            # and it is Steering base again
                self.assertEqual((pad.top, pad.down()), ("Steering | R1: W Key", ["W"]))

    @old_inverted_chord
    @scenario("90.35 S4", rules=("R158",), rests=("A10",), frozen="90.41")
    def test_the_guard_has_stateful_menus_and_since_90_38_inherits_bases_pad(self):
        for pad in self.each(start=("Base", "Gyro")):
            pad.enter_steering().push("LS", "up").wait(200).recentre("LS").wait(100)
            self.assertEqual(mode(pad), GUARD)
            pad.hold("Start").wait(30)
            self.assertTrue(pad.has("Stateful | Menu Right: Entry Point") and pad.lacks("Menu Right: Entry Point"))
            pad.mark().click("RS").wait(30).let_go("Start").lift("LS").lift("RS").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base", "Gyro"))                      # the clear, not another entry
            self.assertEqual(pad.seen("beep"), [("beep", "Transition Set 2")])
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(200).touch("RP").wait(400)
            # Author, 90.38: the old Steering touch block goes; Base's RTP route works here.
            self.assertTrue(pad.has('RTP: Entry Point', 'RTP: Tap Cover'))
            pad.lift("RP").wait(300)
            self.assertTrue(pad.lacks(*PAD_LAYERS))
            self.assertEqual((mode(pad), pad.down()), (GUARD, ["W"]))

    @scenario("90.35 S5", rules=("R157", "R161"), rests=("A49",), frozen="90.41")
    def test_the_quick_tap_from_the_guard_beeps_on_the_guard(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(200).mark().hold("L1").wait(30).hold("R1").wait(40).let_go("R1").wait(10).let_go("L1")
            pad.lift("LS").wait(500)
            self.assertEqual(pad.stack, pad.layers("Base"))
            self.assertIn(("beep", GUARD), pad.seen("beep"))

    @old_inverted_chord
    @scenario("90.35 S6", rules=("R136",), rests=("A6",), frozen="90.41")
    def test_a_driver_ends_turn_assist_whenever_it_comes(self):
        ramp = ("Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1")
        for pad in self.each(start="steering"):                 # inside the 5 ms before the first ramp stage
            pad.push("RS").wait(2)
            self.assertEqual(pad.top, "Gyro Off Ramp Up")
            pad.hold("R1").wait(100)
            self.assertTrue(pad.lacks(*ramp))                   # in 90.34 it stayed under the driver's layer, gyro off
            self.assertEqual((pad.top, pad.down(), pad.gyro_off()), ("Steering | R1: W Key", ["W"], False))
        for pad in self.each(start="steering"):                 # handed back over a ramp stage
            pad.push("RS").wait(100).hold("RF").wait(300).push("LS", "up").wait(100)
            self.assertEqual(pad.names()[1:], ("Turning Ramp Up 0", GUARD))
            pad.recentre("LS").wait(100).hold("R1").wait(100)
            self.assertTrue(pad.lacks(*ramp))
            self.assertEqual((mode(pad), pad.top), ("Steering", "Steering | R1: W Key"))
            pad.let_go("R1", "RF").lift("RS").lift("LS").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))


if __name__ == "__main__":
    unittest.main()
