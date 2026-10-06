"""Scenarios for the Deck checks of 90.11 (Steering fallback hold) and 90.13 (no turn assist in Steering).

Each test is one check from the retired Deck checklist, replayed on both working layouts.
All of 90.11 is in Steering with no driver held, as the checklist said.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

GUARD = "Steering | LS: Fallback Guard"


class FallbackHold(ScenarioCase):
    """90.33 walked the fallback hold back: stick up or down now brings in `Steering | LS: Fallback Guard`,
    which stays, and there is no exit by holding the stick (the author's design, 2026-10-04 and 2026-10-05).
    F1 to F9 and F11 were about the second, its exit and the Entry Guard, and are retired; the fallback's
    scenarios are in test_scenarios_90_33.py. F10 still holds."""

    @scenario("90.11 F10", rules=("R137",))
    def test_pushing_up_with_a_menu_button_held_types_w_and_adds_no_guard(self):
        for pad in self.each(start="steering"):
            pad.hold("Start").mark().push("LS", "up").wait(3000)
            self.assertEqual(pad.down(), ["W"])
            self.assertTrue(pad.has("Steering") and pad.lacks(GUARD))
            self.assertEqual(pad.seen("haptic", "beep"), [])            # no pulse: no guard comes on
            pad.mark().let_go("Start")
            self.assertNotIn("TAB", pad.typed())                         # held past 200 ms with a stick out: silent

class NoTurnAssistInSteering(ScenarioCase):
    """90.13 blocked the right stick's edge in `Steering`, so turn assist was off everywhere in Steering. 90.34
    took that block out of Steering base (the author, 2026-10-05): turn assist is off only while a driver is
    held, whose layer binds the edge itself. N1 and N2 are rewritten for that."""
    RAMP = ("Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1")

    @scenario("90.13 N1")
    def test_the_right_stick_adds_no_ramp_layer_while_a_driver_is_held(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").push("RS").wait(1000)
            self.assertTrue(pad.lacks(*self.RAMP))
            self.assertFalse(pad.gyro_off())                             # the gyro keeps aiming
        for pad in self.each(start="steering"):                          # since 90.34 Steering base has turn assist again
            pad.push("RS").wait(1000)
            self.assertTrue(pad.has("Gyro Off Ramp Up") and pad.gyro_off())
            pad.recentre("RS").wait(100)
            self.assertEqual(pad.names()[:2], ("Base", "Steering"))
            self.assertTrue(pad.lacks(*self.RAMP))

    @scenario("90.13 N2", rules=("R136",))
    def test_the_drivers_release_still_reaches_its_layer_while_firing_and_turning(self):
        for pad in self.each(start="steering"):
            pad.hold("R1", "RF").push("RS").wait(500)
            self.assertIn("W", pad.down())
            self.assertTrue(pad.lacks(*self.RAMP))
            pad.let_go("R1").wait(300)
            self.assertTrue(pad.lacks("Steering | R1: W Key"))           # the Release reached the driver's layer
            self.assertNotIn("W", pad.down())                            # no W stuck on
            pad.let_go("RF").lift("RS").wait(300)                        # since 90.34 the ramp comes on in between;
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))  # it leaves with the stick

    @scenario("90.13 N3", rules=("R140",))
    def test_a_trigger_pull_inside_a_steering_window_clicks(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(50)
            self.assertEqual(pad.top, "Steering | LS Up: Double Tap")
            pad.mark().hold("RF")
            self.assertEqual(pad.typed(), ["mouse_button RIGHT"])

    @scenario("90.13 N4", rules=("R114",))
    def test_outside_steering_the_ramp_layers_come_and_go(self):
        for pad in self.each():
            pad.push("RS")
            self.assertTrue(pad.has("Gyro Off Ramp Up") and pad.gyro_off())
            pad.wait(5)
            self.assertEqual(pad.top, "Turning Ramp Up 0")
            pad.wait(250)
            self.assertEqual(pad.top, "Turning Ramp Up 1")
            pad.recentre("RS")
            self.assertTrue(pad.lacks(*self.RAMP))
            self.assertFalse(pad.gyro_off())


if __name__ == "__main__":
    unittest.main()
