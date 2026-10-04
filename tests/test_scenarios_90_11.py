"""Scenarios for the Deck checks of 90.11 (Steering fallback hold) and 90.13 (no turn assist in Steering).

Each test is one check from the retired Deck checklist, replayed on both working layouts.
All of 90.11 is in Steering with no driver held, as the checklist said.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

HOLD, GUARD = "Steering | LS: Fallback Hold", "Steering | LS: Entry Guard"


class FallbackHold(ScenarioCase):
    @scenario("90.11 F1", rules=("R137",), rests=("A8", "A10"))
    def test_rolling_to_a_or_d_removes_the_hold_and_steering_stays(self):
        for pad in self.each(start="steering"):
            for direction, key in (("up", "W"), ("down", "S")):
                pad.push("LS", direction).wait(1000)
                self.assertEqual((pad.top, pad.down()), (HOLD, [key]))
                pad.roll("LS", "left").mark().wait(3000)
                self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), ["A"]))
                self.assertEqual(pad.seen("haptic"), [])                # the pulses stopped
                pad.recentre("LS")

    @scenario("90.11 F2", rules=("R137",), rests=("A10", "A16"))
    def test_holding_up_types_w_pulses_and_leaves_steering_at_1500_ms(self):
        for pad in self.each(start="steering"):
            for direction, key in (("up", "W"), ("down", "S")):
                pad.mark().push("LS", direction)
                self.assertEqual((pad.top, pad.down()), (HOLD, [key]))
                pad.wait(1499)
                self.assertTrue(pad.has("Steering", HOLD))
                self.assertGreaterEqual(len(pad.seen("haptic")), 6)     # from the start, every 250 ms
                pad.mark().wait(1)
                self.assertTrue(pad.lacks("Steering", HOLD))
                self.assertEqual(pad.seen("beep"), [("beep", "Steering")])   # one beep
                pad.lift("LS").enter_steering()

    @scenario("90.11 F3", rules=("R137",), rests=("A8", "A16"))
    def test_the_exit_counts_from_the_second_push(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(1000).recentre("LS").wait(100)
            self.assertTrue(pad.lacks(HOLD))
            pad.push("LS", "up").wait(1499)
            self.assertTrue(pad.has("Steering", HOLD))
            pad.wait(1)
            self.assertTrue(pad.lacks("Steering"))

    @scenario("90.11 F5", rests=("A10", "A16"))
    def test_a_diagonal_holds_w_and_a_and_still_exits(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up")
            pad.sim.press(("joystick", "dpad_west"))                   # up-left: two directions at once
            self.assertEqual(pad.down(), ["A", "W"])
            pad.wait(1499)
            self.assertTrue(pad.has(HOLD))
            pad.wait(1)
            self.assertTrue(pad.lacks("Steering"))

    @scenario("90.11 F6", rules=("R137",), either=("A9",))
    def test_a_driver_press_removes_the_hold_and_it_returns_when_the_driver_lets_go(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(500).hold("R1").mark()
            self.assertTrue(pad.lacks(HOLD))
            pad.wait(50)                                                 # the driver's layer adds it with a repeating bind
            self.assertEqual(pad.top, "Steering | LS Up: Modifier 1")   # the R1 modifier map
            pad.wait(2000)
            self.assertTrue(pad.has("Steering"))                         # no exit
            self.assertEqual(pad.seen("beep"), [])
            pad.let_go("R1").wait(50)                                    # the checklist asked: do W and the pulses come back?
            self.assertEqual((pad.top, pad.down()), (HOLD, ["W"]))       # yes, by either way of A9

    @scenario("90.11 F7", rules=("R137", "R169"), rests=("A6", "A8"))
    def test_the_entry_guard_holds_w_with_no_exit_until_the_stick_has_been_back_to_centre(self):
        """Until 90.23 the guard also stayed after an entry with the stick centred, through the first push.
        Since 90.24 its stick-touch cleanup is guarded by the left stick being out (R169): with the stick
        centred and the thumb resting on it, the cleanup removes the guard as it lands: a repeating action
        always triggers (A6; until 2026-10-04 this was read as about 100 ms later). The first push gets the
        Fallback Hold."""
        for pad in self.each():
            pad.enter_steering(settle=False)                             # stick centred at entry
            self.assertEqual(pad.top, "Steering")
            pad.mark().push("LS", "up").wait(200)
            self.assertEqual((pad.top, pad.down()), (HOLD, ["W"]))
        for pad in self.each():
            pad.push("LS", "up").hold("Start").click("LS").let_go("Start")   # stick already up at entry
            pad.mark().wait(3000)
            self.assertEqual((pad.top, pad.down()), (GUARD, ["W"]))
            self.assertEqual(pad.seen("beep"), [])
            pad.recentre("LS").push("LS", "up")                          # the guard's edge Release (A8)
            self.assertEqual(pad.top, HOLD)

    @scenario("90.11 F8", rules=("R136", "R137"), rests=("A16",))
    def test_a_menu_tap_types_its_key_and_adds_nothing_over_the_hold(self):
        for pad in self.each(start="steering"):
            for button, key in (("Start", "TAB"), ("Select", "ESCAPE")):
                pad.push("LS", "up").wait(100).mark()
                pad.tap(button)
                self.assertEqual((pad.typed(), pad.top, pad.down()), ([key], HOLD, ["W"]))
                pad.hold(button).wait(1000)                              # held: the key, and no Fn
                self.assertEqual((pad.top, pad.down()), (HOLD, sorted([key, "W"])))
                pad.let_go(button).wait(369)                             # 1499 ms after the push
                self.assertTrue(pad.has("Steering"))
                pad.wait(1)
                self.assertTrue(pad.lacks("Steering"))                   # the exit still came 1.5 s after the push
                pad.lift("LS").enter_steering()

    @scenario("90.11 F9", rules=("R109",), rests=("A16",))
    def test_f1_and_f2_on_the_desktop_configuration(self):
        for pad in self.each(desktop_configuration=True):
            pad.enter_steering()
            pad.push("LS", "up").wait(1000).roll("LS", "left").wait(3000)
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), ["A"]))
            pad.recentre("LS").push("LS", "up").wait(1499)
            self.assertTrue(pad.has("Steering", HOLD))
            pad.wait(1)
            self.assertTrue(pad.lacks("Steering"))

    @scenario("90.11 F10", rules=("R137",))
    def test_pushing_up_with_a_menu_button_held_types_w_and_adds_no_hold(self):
        for pad in self.each(start="steering"):
            pad.hold("Start").mark().push("LS", "up").wait(3000)
            self.assertEqual(pad.down(), ["W"])
            self.assertTrue(pad.has("Steering") and pad.lacks(HOLD))
            self.assertEqual(pad.seen("haptic", "beep"), [])            # no pulses, no exit
            pad.mark().let_go("Start")
            self.assertNotIn("TAB", pad.typed())                         # held past 200 ms with a stick out: silent

    @scenario("90.11 F11", rules=("R137", "R171"))
    def test_start_and_select_type_their_keys_in_the_entry_guard(self):
        for pad in self.each():
            pad.push("LS", "up").hold("Start").click("LS").let_go("Start").mark()   # the stick is out at entry
            pad.tap("Start").tap("Select")
            self.assertEqual((pad.typed(), pad.top), (["TAB", "ESCAPE"], GUARD))
            pad.hold("Start").wait(1000)
            self.assertEqual((pad.top, sorted(pad.down())), (GUARD, ["TAB", "W"]))   # no Fn
            pad.let_go("Start").recentre("LS").wait(300).mark()          # back to centre ends the guard
            pad.hold("Start").wait(300)
            self.assertEqual(pad.top, "Menu Right: Fn Layer")            # Start's Fn is back
            pad.let_go("Start")
        for pad in self.each():
            pad.enter_steering(settle=False).hold("R1").let_go("R1")      # a driver press ends it too
            self.assertTrue(pad.lacks(GUARD))
        for pad in self.each():                # since 90.24: with the stick centred, a Start press removes the guard
            pad.enter_steering(settle=False).mark()                      # (its cleanup, R171), and Steering's Start answers
            pad.hold("Start")
            self.assertTrue(pad.lacks(GUARD))
            pad.let_go("Start").wait(300)
            self.assertEqual((pad.typed(), pad.stack), (["TAB"], pad.layers("Base", "Steering")))


class NoTurnAssistInSteering(ScenarioCase):
    RAMP = ("Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1")

    @scenario("90.13 N1")
    def test_the_right_stick_adds_no_ramp_layer_in_steering(self):
        for pad in self.each(start="steering"):
            pad.push("RS").wait(1000)
            self.assertTrue(pad.lacks(*self.RAMP))
            self.assertFalse(pad.gyro_off())                             # the gyro keeps aiming
            pad.recentre("RS").hold("R1").push("RS").wait(1000)          # and with a driver held
            self.assertTrue(pad.lacks(*self.RAMP))
            self.assertFalse(pad.gyro_off())

    @scenario("90.13 N2", rules=("R136",))
    def test_the_drivers_release_still_reaches_its_layer_while_firing_and_turning(self):
        for pad in self.each(start="steering"):
            pad.hold("R1", "RF").push("RS").wait(500)
            self.assertIn("W", pad.down())
            pad.let_go("R1").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))  # back in fallback
            self.assertNotIn("W", pad.down())                            # no W stuck on

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
