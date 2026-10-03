"""Scenarios for the Deck checks of 90.9 (menu combo keys), 90.7 (slim steering overlays) and 90.6
(chorded delays and the dead-group prune).

Several checks of these three releases were replaced by later ones and are recorded as obsolete
(90.9 K1; 90.7 S5, S7, S8; 90.6 C1, C3, T1), and some are static tests that already existed.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

MOD1, MOD0, TAP_COVER = "Steering | LS Up: Modifier 1", "Steering | LS Down: Modifier 0", "Steering | LS: Tap Cover"
DRIVER = "Steering | R1: W Key"


class MenuComboKeys(ScenarioCase):
    @scenario("90.9 K2", rules=("R138",))
    def test_with_fn_up_the_other_menu_button_types_its_key_on_every_press(self):
        for first, second, key in (("Start", "Select", "BACKSPACE"), ("Select", "Start", "RETURN")):
            for pad in self.each():
                pad.hold(first).wait(250).mark().tap(second).wait(20).tap(second)
                self.assertEqual(pad.typed(), [key, key])
                pad.hold(second).wait(800)
                self.assertEqual(pad.down(), [key])                          # held: the system repeats it

    @scenario("90.9 K3", rules=("R138",), rests=("A11",))
    def test_the_accepted_stray_key_when_the_first_menu_button_is_lifted_first(self):
        for first, second, stray in (("Start", "Select", "ESCAPE"), ("Select", "Start", "TAB")):
            for pad in self.each():
                pad.hold(first).wait(50).hold(second).wait(100).mark().let_go(first)
                self.assertIn(pad.top, ("Menu Left: Entry Point", "Menu Right: Entry Point"))   # it fell through to Base
                pad.wait(100).let_go(second).wait(400)
                self.assertEqual((pad.typed(), pad.stack), ([stray], pad.layers("Base")))        # the only extra output
            for pad in self.each():
                pad.hold(first).wait(50).hold(second).wait(100).mark().let_go(second).let_go(first).wait(400)
                self.assertEqual(pad.typed(), [])                            # the second released first: nothing extra

    @scenario("90.9 K4", rules=("R138",), either=("A9",))
    def test_a_held_fn_key_becomes_its_base_binding_when_the_menu_button_lifts(self):
        for pad in self.each(variants=("default",)):                         # LB is the L1 modifier in the default
            pad.hold("Start").wait(250).hold("LB")
            self.assertEqual(pad.down(), ["F10"])
            pad.let_go("Start").wait(60)
            self.assertEqual((pad.top, pad.down()), ("L1: Modifier 0", []))

    @scenario("90.9 M5", rules=("R148",))
    def test_the_right_pad_double_tap(self):
        touch = ("right_trackpad", "touch")
        for direction, lands in (("dpad_north", "RTP: Circular Scroll"), ("dpad_south", "RTP: Circular Scroll"),
                                 ("dpad_east", "RTP: Entry Point")):         # elsewhere: back in mouse mode
            for pad in self.each():
                pad.sim.press(touch).release(touch)
                self.assertEqual(pad.top, "RTP: Double Tap")
                pad.wait(50)
                pad.sim.press(touch).press(("right_trackpad", direction))
                self.assertEqual(pad.top, lands)
                pad.sim.release(("right_trackpad", direction)).release(touch)
                pad.wait(300).hold("L1")
                self.assertEqual(pad.top, "L1: Modifier 0")                  # the bumpers keep their modifiers


class SlimSteeringOverlays(ScenarioCase):
    @scenario("90.7 S1", rests=("A16",))
    def test_a_face_button_inside_the_stick_window(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(50).mark().tap("A")
            self.assertEqual(pad.typed(), ["F"])                             # once
            pad.wait(300)
            self.assertEqual(pad.typed(), ["F", "mouse_wheel SCROLL_UP"])    # one scroll, about 150 ms after centre
            self.assertEqual(pad.top, DRIVER)                                # nothing left stuck

    @scenario("90.7 S2", rests=("A10",))
    def test_flick_then_flick_and_hold_repeats_the_scroll(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(50).mark().push("LS", "up").wait(300)
            self.assertGreater(pad.typed().count("mouse_wheel SCROLL_UP"), 2)
            pad.sim.press(("joystick", "dpad_west"))                          # a true diagonal: A steers, the scroll goes on
            pad.mark().wait(200)
            self.assertIn("A", pad.down())
            self.assertGreater(pad.typed().count("mouse_wheel SCROLL_UP"), 1)
            pad.recentre("LS").mark().wait(300)
            self.assertEqual(pad.typed(), [])                                # releasing stops it
            pad.push("LS", "up").wait(100)
            self.assertEqual((pad.top, pad.typed()), (MOD1, []))             # the next push gives no scroll

    @scenario("90.7 S3", rules=("R117",))
    def test_lifting_the_thumb_during_a_stick_modifier(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "up").wait(300)
            self.assertEqual(pad.top, TAP_COVER)
            pad.mark()
            pad.sim.release(("joystick", "touch")).press(("joystick", "touch"))      # off and back on
            self.assertEqual(pad.top, TAP_COVER)                             # the stick stays used up
            pad.recentre("LS").wait(300)
            self.assertEqual((pad.top, pad.typed()), (DRIVER, []))           # no phantom scroll

    @scenario("90.7 S4", rules=("R129", "R133"), rests=("A25",))
    def test_the_drivers_recovery_clears_through_the_cover(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "up").wait(300).miss("R1")
            self.assertEqual(pad.top, TAP_COVER)
            pad.touch("RS")
            self.assertTrue(pad.lacks(TAP_COVER, MOD1, DRIVER) and pad.has("Steering"))

    @scenario("90.7 S6")
    def test_no_right_pad_touch_mode_starts_while_steering(self):
        """The cursor moving and the pad's click are not simulated; what is checked is that no RTP layer starts."""
        touch = ("right_trackpad", "touch")
        for pad in self.each(start="steering"):
            pad.sim.press(touch).release(touch)
            pad.wait(50)
            pad.sim.press(touch)
            pad.wait(300)
            self.assertFalse([t for t in pad.stack if t.startswith("RTP")])


class ChordedDelays(ScenarioCase):
    @scenario("90.6 C4/C5/S7", rules=("R120", "R122"), rests=("A8", "A12"))
    def test_holding_the_stick_uses_up_the_tap(self):
        """Its last clause said that after a Modifier 2 exit with the stick held, centre never scrolls. Since
        90.10 the stick's map is entered afresh then, so 90.10 D4's rule applies: silent once it has been
        held 250 ms, one scroll if the stick recentres sooner."""
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "down").wait(300)
            self.assertEqual(pad.names()[-2:], (MOD0, TAP_COVER))            # past 250 ms: the tap is used up
            pad.mark().recentre("LS").wait(300)
            self.assertEqual(pad.typed(), [])
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "down").wait(100).recentre("LS").wait(300)     # an interrupted hold
            pad.push("LS", "down").wait(300)
            self.assertEqual(pad.top, TAP_COVER)                             # never blocks the next
            pad.mark().roll("LS", "up").wait(100)
            self.assertEqual(pad.names()[-2:], (MOD0, TAP_COVER))            # reversing does nothing
            pad.recentre("LS").wait(300)
            self.assertEqual(pad.typed(), [])                                # and centre never scrolls
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "up").wait(300).hold("L1").wait(300)   # the other driver takes over: Modifier 2
            self.assertTrue(pad.has("Steering | R1!L1: Modifier 2"))
            pad.let_go("L1").wait(250)                                       # out of Modifier 2, the stick still up
            self.assertEqual(pad.top, TAP_COVER)
            pad.mark().recentre("LS").wait(300)
            self.assertEqual(pad.typed(), [])

    @scenario("90.6 R1", rules=("R120", "R124"), rests=("A10",))
    def test_double_tap_and_hold_then_a_clean_release_through_the_cover(self):
        for button, key, cover in (("Select", "ESCAPE", "Menu Left: Double Tap Cover"),
                                   ("Start", "TAB", "Menu Right: Double Tap Cover")):
            for pad in self.each():
                pad.tap(button).wait(30).mark().hold(button).wait(300)
                self.assertEqual((pad.top, pad.down(), pad.typed()), (cover, [key], [key]))   # the key holds
                pad.mark().let_go(button).wait(300)
                self.assertEqual((pad.typed(), pad.stack), ([], pad.layers("Base")))          # no extra key
        for pad in self.each():
            pad.tap("L1").wait(30).hold("L1").wait(300)
            self.assertEqual(pad.top, "L1: Double Tap Cover")
            pad.mark().let_go("L1").wait(300)
            self.assertEqual((pad.typed(), pad.stack), ([], pad.layers("Base")))


if __name__ == "__main__":
    unittest.main()
