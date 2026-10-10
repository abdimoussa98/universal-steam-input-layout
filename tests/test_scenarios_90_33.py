"""Scenarios for 90.33: the Steering fallback is a layer the stick brings in and the bumpers take out.

The plan is plans/2026-10-04-steering-fallback-layer.md, the author's design of 2026-10-04 and
2026-10-05; the record is findings/2026-10-05-steering-fallback-guard/README.md. "R1" and "L1" are the
modifier pair, which are also Steering's drivers: the bumpers in the default layout, the triggers in
the alternative.

The retired fallback-entry scenarios explicitly use frozen 90.41 data.
The ordinary Steering Modifier 2 cleanup remains live and retains Steering since 90.44;
90.42 covers the directional exit. The following fallback behaviors are historical.

- In Steering with no driver held, stick up or down adds `Steering | LS: Fallback Guard`, with a strong
  pulse: after 100 ms in 90.33, at once since 90.34. It types W and S and stays when the stick is let go.
- In the guard a bumper pressed with the stick out is its Gyro modifier, over the guard. Pressed with
  the stick at centre it removes the guard, with a pulse, and drives.
- The quick tap of both bumpers clears everything to Base from there, with the beep.
- Start and Select are Steering's own; a menu button plus a stick click clears and keeps Gyro.
- A fresh touch of either stick with the left stick at centre removes the guard (R169).
"""
import unittest

from tests.scenario import ScenarioCase, scenario

GUARD = "Steering | LS: Fallback Guard"
BOTH = (("up", "W"), ("down", "S"))
PULSE = ("haptic", "1 Steering joystick/dpad_{}")
MODIFIERS = (("L1", "Gyro | L1: Modifier 0", "mouse_wheel SCROLL_DOWN"), ("R1", "Gyro | R1: Modifier 1", "mouse_wheel SCROLL_UP"))
DRIVERS = (("R1", "Steering | R1: W Key", "W"), ("L1", "Steering | L1: S Key", "S"))


def pulses(pad):
    """The low pulses since the mark that came from Steering's add of the guard."""
    return [detail for _, detail in pad.seen("haptic") if detail.startswith("1 Steering joystick/dpad_")]


class TheStickBringsItIn(ScenarioCase):
    @scenario("90.33 G1", rules=("R161",), rests=("A10",), frozen="90.41")
    def test_up_or_down_brings_the_guard_in_at_once_with_a_low_pulse(self):
        """Changed in 90.34: the add is a repeating press and comes at once. 90.33 had July's 100 ms delay."""
        for direction, key in BOTH:
            for pad in self.each(start="steering"):
                pad.push("LS", direction).wait(5)
                self.assertEqual((pad.top, pad.down()), (GUARD, [key]))
                self.assertEqual(len(pulses(pad)), 1)
                pad.mark().wait(1000)
                self.assertEqual((pad.top, pad.down(), pulses(pad)), (GUARD, [key], []))       # no timer, no second pulse
                self.assertTrue(pad.lacks("Steering"))                                         # since 90.35 they swap

    @scenario("90.33 G2", rules=("R137",), frozen="90.41")
    def test_letting_the_stick_go_leaves_the_guard_on_and_the_next_push_types_at_once(self):
        # The author, 2026-10-05: "pushing the stick will get you into the fallback layer, but releasing it won't."
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300)
            for direction, key in BOTH * 2:
                pad.recentre("LS").wait(400)
                self.assertEqual((pad.top, pad.down()), (GUARD, []))
                pad.mark().push("LS", direction).wait(5)
                self.assertEqual((pad.top, pad.down(), pulses(pad)), (GUARD, [key], []))
            pad.roll("LS", "left").wait(200)                                            # A and D come from Steering
            self.assertEqual((pad.top, pad.down()), (GUARD, ["A"]))

    @scenario("90.33 G3", rules=("R137",), rests=("A36",), frozen="90.41")
    def test_whichever_comes_first_decides_the_stick_or_the_driver(self):
        """Changed in 90.34 (the author, 2026-10-05: "If you deflect the stick up or down you be in fall out unless
        you press the bumpers/trigger and if you are in steering base itll be the opposite"). In 90.33 a driver
        pressed inside the first 100 ms of the push still drove."""
        for driver, layer, key in DRIVERS:
            modifier = "Gyro | R1: Modifier 1" if driver == "R1" else "Gyro | L1: Modifier 0"
            for pad in self.each(start="steering"):                                     # the stick first, by 10 ms
                pad.push("LS", "up").wait(10).hold(driver).wait(100)
                self.assertTrue(pad.has(GUARD, modifier) and pad.lacks(layer), driver)
                self.assertEqual(pad.down(), ["W"])
            for pad in self.each(start="steering"):                                     # the driver first, by 10 ms
                pad.hold(driver).wait(10).push("LS", "up").wait(400)
                self.assertTrue(pad.has(layer) and pad.lacks(GUARD, modifier), driver)
                self.assertIn(key, pad.down())
                pad.recentre("LS").let_go(driver).wait(300)
                self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.33 G4", rules=("R157",), rests=("A6", "A10"), frozen="90.41")
    def test_entering_steering_with_the_stick_up_brings_the_guard_in_and_with_it_left_does_not(self):
        # No guard is added at entry any more: Steering's own up and down do it, as it lands on the held stick.
        for pad in self.each():
            pad.push("LS", "up").wait(100).mark().enter_steering(settle=False).wait(60)
            self.assertEqual((pad.top, pad.down(), len(pulses(pad))), (GUARD, ["W"], 1))
        for pad in self.each():
            pad.push("LS", "left").wait(100).enter_steering(settle=False).wait(300)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))
            pad.hold("R1").wait(100)                                                    # the bumper is a driver there
            self.assertTrue(pad.has("Steering | R1: W Key") and pad.lacks("Gyro | R1: Modifier 1"))

    @scenario("90.33 G5", rules=("R109",), rests=("A21",), frozen="90.41")
    def test_the_guard_and_its_bumpers_on_the_desktop_configuration(self):
        # The desktop configuration keeps three entries on an input. Steering's up and down have two, and the
        # guard's bumpers two, so nothing is dropped. (Until 90.32 this was 90.11 F9, for the fallback hold.)
        for pad in self.each(start="steering", desktop_configuration=True):
            pad.push("LS", "up").wait(110)
            self.assertEqual((pad.top, pad.down(), len(pulses(pad))), (GUARD, ["W"], 1))
            pad.hold("L1").wait(60)
            self.assertEqual((pad.top, pad.down()), ("Gyro | L1: Modifier 0", ["W"]))
            pad.let_go("L1").wait(500).recentre("LS").wait(200).hold("R1").wait(160)
            self.assertEqual((pad.top, pad.down()), ("Steering | R1: W Key", ["W"]))


class TheBumpersInTheGuard(ScenarioCase):
    @scenario("90.33 B1", rules=("R137",), rests=("A36",), frozen="90.41")
    def test_with_the_stick_out_a_bumper_is_its_gyro_modifier_and_w_carries_on(self):
        # The author, 2026-10-04: "in there we'll have the gyro mod 0 & 1 add layer on their respective
        # bumpers/triggers."
        for bumper, modifier, wheel in MODIFIERS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(300).mark()
                for _ in range(3):                                                      # again and again inside one hold
                    pad.hold(bumper).wait(60)
                    self.assertEqual((pad.top, pad.down()), (modifier, ["W"]))
                    self.assertTrue(pad.has(GUARD))                                     # the guard stays underneath
                    pad.let_go(bumper).wait(500)
                    self.assertEqual((pad.top, pad.down()), (GUARD, ["W"]))
                self.assertEqual(pad.typed(), [wheel] * 3)                              # each tap is the modifier's tap
                self.assertEqual(pulses(pad), [])

    @scenario("90.33 B2", rules=("R137",), rests=("A36",), frozen="90.41")
    def test_the_stick_held_sideways_also_makes_a_bumper_a_modifier(self):
        # Coming back to driving needs the stick at centre: with A held, R1 is the modifier, not W.
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300).roll("LS", "left").wait(100).hold("R1").wait(100)
            self.assertEqual((pad.top, pad.down()), ("Gyro | R1: Modifier 1", ["A"]))

    @scenario("90.33 B3", rules=("R133", "R171", "R161"), either=("A9",), frozen="90.41")
    def test_at_centre_a_bumper_ends_the_guard_with_a_pulse_and_drives(self):
        # The author, 2026-10-05: "the bumpers themselves will release the fallback guard if you're going into
        # steering."
        for driver, layer, key in DRIVERS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(300).recentre("LS").wait(200).mark().hold(driver).wait(60)
                self.assertEqual((pad.top, pad.down()), (layer, [key]), driver)
                self.assertTrue(pad.lacks(GUARD))
                self.assertEqual(len([d for _, d in pad.seen("haptic") if d.startswith(f"1 {pad.title(GUARD)}")]), 1)
                pad.let_go(driver).wait(300)
                self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.33 B4", rules=("R120",), rests=("A14",), frozen="90.41")
    def test_letting_the_driver_go_with_the_stick_up_pushes_back_into_the_guard(self):
        # The author, 2026-10-05: "if you let go of either bumper and you go all the way back to the base, the
        # stick will be in the correct position to push you back into the fallback layer."
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300).recentre("LS").wait(200).hold("R1").wait(200)
            pad.push("LS", "up").wait(300)
            self.assertTrue(pad.lacks(GUARD))                                           # driving: Steering's stick modifier
            pad.mark().let_go("R1").wait(400)
            self.assertEqual((pad.top, pad.down(), len(pulses(pad))), (GUARD, ["W"], 1))

    @scenario("90.33 B5", rules=("R137",), either=("A9",), frozen="90.41")
    def test_after_a_bumper_hold_with_the_stick_let_go_the_next_bumper_drives(self):
        # The author, 2026-10-05: "if you hold the bumpers you can actually let go of the stick and it's not going
        # to clean up because you're transferring the hold to the bumpers."
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300).hold("L1").wait(300).recentre("LS").wait(300)
            self.assertTrue(pad.has(GUARD, "Gyro | L1: Modifier 0"))                    # nothing changed under the bumper
            self.assertEqual(pad.down(), [])
            pad.let_go("L1").wait(500)
            # In the simulator the guard's cleanup function then fires on the thumb resting at centre and removes
            # it. On the Deck it may stay. Either way the next bumper at centre drives.
            self.assertTrue(pad.has("Steering") and pad.lacks("Gyro | L1: Modifier 0"))
            pad.hold("R1").wait(60)
            self.assertEqual((pad.top, pad.down()), ("Steering | R1: W Key", ["W"]))
            self.assertTrue(pad.lacks(GUARD))


class LeavingFromTheGuard(ScenarioCase):
    @scenario("90.33 L1", rules=("R157", "R161", "R132"), rests=("A49",), frozen="90.41")
    def test_the_quick_tap_of_both_bumpers_clears_to_base_with_gyro_on_or_off(self):
        # The author, 2026-10-04: "whether you are in the fallback layer or are in the steering ones if you press
        # bumpers/triggers together it'll take you to the base layer every time."
        for first, second in (("L1", "R1"), ("R1", "L1")):
            for start in (("Base",), ("Base", "Gyro")):
                for stick in ("up", None):
                    for pad in self.each(start=start):
                        pad.enter_steering().push("LS", "up").wait(300)
                        if stick is None:
                            pad.recentre("LS").wait(50).push("LS", "left").wait(50)     # out, so the bumper is a modifier
                        pad.mark().hold(first).wait(30).hold(second).wait(40).let_go(second).wait(10).let_go(first)
                        pad.lift("LS").wait(500)
                        self.assertEqual(pad.stack, pad.layers("Base"), (first, start, stick))
                        self.assertIn(("beep", "Steering"), pad.seen("beep"))

    @scenario("90.33 L2", rules=("R157",))
    def test_the_quick_tap_from_steering_base_cleans_modifiers_and_retains_steering(self):
        for pad in self.each(start=("Base", "Gyro")):
            pad.enter_steering().mark().hold("R1").wait(30).hold("L1").wait(40).let_go("L1").wait(10).let_go("R1")
            pad.lift("LS").wait(500)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))
            self.assertEqual(pad.seen("beep", "haptic"), [])

    @scenario("90.33 L3", rules=("R158", "R161"), frozen="90.41")
    def test_a_menu_button_and_a_stick_click_clear_steering_and_the_guard_and_keep_gyro(self):
        # The author, 2026-10-04: "stick & menu buttons to clean just your stateful layer."
        for menu in ("Select", "Start"):
            for start, left in ((("Base",), ("Base",)), (("Base", "Gyro"), ("Base", "Gyro"))):
                for pad in self.each(start=start):
                    pad.enter_steering().push("LS", "up").wait(300).recentre("LS").wait(100)
                    self.assertEqual(pad.top, GUARD)
                    pad.mark().hold(menu).wait(50).click("LS").wait(30).let_go(menu).lift("LS").wait(400)
                    self.assertEqual(pad.stack, pad.layers(*left), (menu, start))
                    self.assertEqual(pad.seen("beep"), [("beep", "Transition Set 2")])

    @scenario("90.33 L4", rules=("R158",), frozen="90.41")
    def test_start_and_select_keep_steerings_taps_in_the_guard(self):
        # The author, 2026-10-04: "menu buttons in fallback should inherit from steering base."
        for menu, key in (("Start", "TAB"), ("Select", "ESCAPE")):
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(300).mark().tap(menu, 40).wait(400)
                self.assertEqual(pad.typed(), [key])
                self.assertEqual((pad.top, pad.down()), (GUARD, ["W"]))

    @scenario("90.33 L5", rules=("R137",), either=("A9",), frozen="90.41")
    def test_after_a_menu_hold_with_the_stick_let_go_a_bumper_drives(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300).hold("Select").wait(300).recentre("LS").wait(100).let_go("Select").wait(500)
            self.assertTrue(pad.has("Steering"))
            pad.hold("R1").wait(60)
            self.assertEqual((pad.top, pad.down()), ("Steering | R1: W Key", ["W"]))


class TheGuardsCleanup(ScenarioCase):
    @scenario("90.33 C1", rules=("R169", "R133"), rests=("A17", "A36"), frozen="90.41")
    def test_a_fresh_stick_touch_at_centre_removes_the_guard_and_one_with_the_stick_out_does_not(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300).touch("RS").wait(200)                        # the left stick is out: held back
            self.assertEqual((pad.top, pad.down()), (GUARD, ["W"]))
            pad.lift("RS").recentre("LS").wait(200)
            self.assertEqual(pad.top, GUARD)                                            # the left thumb never left
            pad.touch("RS").wait(150)
            self.assertTrue(pad.lacks(GUARD) and pad.has("Steering"))
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300).lift("LS").wait(200)
            self.assertEqual(pad.top, GUARD)                                            # lifting alone does nothing
            pad.touch("LS").wait(150)
            self.assertTrue(pad.lacks(GUARD) and pad.has("Steering"))
            pad.mark().push("LS", "down").wait(110)                                     # and the next push brings it back
            self.assertEqual((pad.top, pad.down(), len(pulses(pad))), (GUARD, ["S"], 1))

    @scenario("90.33 C2", rules=("R133",), rests=("A25",), frozen="90.41")
    def test_a_bumper_release_missed_under_the_guards_modifier_recovers_on_the_next_touch(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(300).hold("L1").wait(100).miss("L1").lift("LS").wait(300)
            self.assertTrue(pad.has("Gyro | L1: Modifier 0"))                           # left on, no button held
            pad.touch("LS").wait(300).lift("LS").wait(300).touch("LS").wait(300)
            self.assertTrue(pad.lacks("Gyro | L1: Modifier 0", "L1: Temp Cursor Gyro", "L1: Tap Cover"))
            pad.hold("R1").wait(100)
            self.assertIn("W", pad.down())
            self.assertTrue(pad.has("Steering | R1: W Key"))


if __name__ == "__main__":
    unittest.main()
