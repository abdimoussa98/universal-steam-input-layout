"""Scenarios for the Deck checks of 90.10 (stateful transitions).

The gates G1 to G4 and G6 are Steam assumptions (A26, A8, A15, A14), not scenarios:
each is its assumption's Deck procedure. D2 was replaced by 90.11, and D9 is 90.11 F7.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

GESTURES = (("Start", "LS"), ("Select", "RS"), ("Start", "RS"), ("Select", "LS"))
FEEDBACK = ["haptic", "beep"]              # the low pulse on the menu Release (since 90.41), then the beep
LEFT_GUARD, RIGHT_GUARD, COVER = ("Menu Buttons: Left Stick Guard", "Menu Buttons: Right Stick Guard",
                                  "Menu Buttons: Tap Cover")
MOD1, MOD0 = "Steering | LS Up: Modifier 1", "Steering | LS Down: Modifier 0"
WINDOW = "Steering | LS Up: Double Tap"


class MenuAndTransitions(ScenarioCase):
    @scenario("90.10 G5")
    def test_a_start_tap_with_a_stick_out_types_one_tab(self):
        for pad in self.each():
            pad.push("LS", "up").mark().tap("Start").wait(300)
            self.assertEqual(pad.typed(), ["TAB"])

    @scenario("90.10 T1", rules=("R157", "R161", "R163"))
    def test_one_gesture_enters_steering_and_the_other_three_clear(self):
        """The name is from 90.10, when only Steering was built. Since 90.21 Select plus the right-stick
        click enters Cursor Gyro, which brings Gyro with it (90.21 C1), and since 90.22 the two same-side
        gestures enter Gamepad (90.22 G1). From Base no gesture only clears any more."""
        for start in (None, ("Base", "Gyro")):
            for menu, stick in GESTURES:
                for pad in self.each(start=start):
                    pad.hold(menu).click(stick)                              # the click released first
                    same_side = (menu, stick) in (("Start", "RS"), ("Select", "LS"))
                    self.assertEqual(pad.top, "Transition Set 0" if same_side else "Transition Set 1")
                    self.assertEqual(len(pad.stack), len(start or ("Base",)) + 1)    # everything else is cleared (R163)
                    pad.mark().let_go(menu)
                    cursor = (menu, stick) == ("Select", "RS")
                    self.assertEqual(pad.has("Steering"), (menu, stick) == ("Start", "LS"))
                    self.assertEqual(pad.has("Cursor Gyro"), cursor)
                    self.assertEqual(pad.has("Gamepad"), same_side)
                    self.assertEqual(pad.has("Gyro"), bool(start) or cursor)          # Gyro is kept as it was
                    self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], FEEDBACK)

    @scenario("90.10 T2", rules=("R158", "R161"))
    def test_all_four_gestures_leave_steering_and_keep_gyro(self):
        for menu, stick in GESTURES:
            for pad in self.each(start=("Base", "Gyro")):
                pad.enter_steering().hold(menu).click(stick)
                self.assertEqual(pad.top, "Transition Set 2")                    # the clear, renamed in 90.22
                pad.mark().let_go(menu)
                self.assertTrue(pad.lacks("Steering") and pad.has("Gyro"))
                self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], FEEDBACK)

    @scenario("90.10 T3", rules=("R157",), rests=("A11",))
    def test_letting_go_of_the_menu_button_first_cancels(self):
        """The checklist asked what the click's release does. Base's click key (Q) goes down when Start is
        let go with the click still held, and comes up with the click; then Start's tap types Tab."""
        for pad in self.each():
            pad.hold("Start").touch("LS")
            pad.sim.press(("joystick", "click"))
            pad.let_go("Start")
            self.assertEqual(pad.down(), ["Q"])
            pad.sim.release(("joystick", "click"))
            pad.wait(300)
            self.assertTrue(pad.lacks("Steering", "Transition Set 0", "Transition Set 1", "Transition Set 2"))
            self.assertEqual(pad.typed(), ["Q", "TAB"])

    @scenario("90.10 T4", rules=("R160", "R169", "R170", "R171"), rests=("A17", "A25"))
    def test_a_transition_left_by_a_missed_release_ends_on_the_next_menu_tap(self):
        """From 90.10 to 90.23 only the next menu tap ended a stuck transition: the sticks, bumpers and
        triggers were blocked. Since 90.24 each of those has a cleanup function guarded by either menu
        button (R169 to R171), so the next stick touch, push or bumper press ends it as well."""
        for pad in self.each():
            pad.hold("Start").click("LS").lift("LS").miss("Start").wait(500)
            self.assertEqual(pad.names()[:2], ("Base", "Transition Set 1"))  # nothing pressed: it is still on
            pad.tap("Start")
            self.assertTrue(pad.has("Steering"))                             # a Start tap in the cross transition
        for press in (lambda pad: pad.touch("RS"), lambda pad: pad.push("LS", "up"), lambda pad: pad.hold("L1"),
                      lambda pad: pad.hold("R1")):
            for pad in self.each():
                pad.hold("Start").click("LS").lift("LS").miss("Start").wait(500)
                press(pad)
                self.assertTrue(pad.lacks("Transition Set 1", "Steering"))   # cleared, and not committed
        for pad in self.each():                                              # the thumb still on the stick: the guard
            pad.hold("Start").click("LS").miss("Start").wait(500)            # chord latched while Start was held (A17),
            self.assertTrue(pad.has("Transition Set 1"))                     # so the held touch does not clear it
        for pad in self.each():
            pad.hold("Select").click("RS").miss("Select").tap("Select")
            self.assertTrue(pad.lacks("Transition Set 0", "Transition Set 1", "Transition Set 2"))

    @scenario("90.10 T5", rules=("R137",), rests=("A8", "A14"))
    def test_stick_guards_come_and_go_and_the_menu_tap_or_hold_behaves(self):
        for pad in self.each():
            pad.hold("Start").push("LS", "up")
            self.assertEqual(pad.top, LEFT_GUARD)
            pad.push("RS")
            self.assertEqual(pad.names()[-2:], (LEFT_GUARD, RIGHT_GUARD))    # both together
            pad.recentre("RS")
            self.assertEqual(pad.top, LEFT_GUARD)
            pad.recentre("LS")
            self.assertEqual(pad.top, "Menu Right: Entry Point")
            pad.wait(200)
            self.assertEqual(pad.top, "Menu Right: Fn Layer")                # Fn follows once the last guard is off
        for pad in self.each():                                              # a quick tap with a guard on
            pad.push("LS", "left").mark().hold("Select").wait(60)
            self.assertEqual(pad.top, LEFT_GUARD)
            pad.let_go("Select").wait(200)
            self.assertEqual(pad.typed(), ["ESCAPE"])
        for pad in self.each():                                              # a 200 ms hold makes the release silent
            pad.push("LS", "left").mark().hold("Start").wait(260)
            self.assertEqual(pad.top, COVER)
            pad.let_go("Start").wait(300)
            self.assertEqual(pad.typed(), [])
        for pad in self.each():                                              # and so does a thumb lift
            pad.hold("Start").push("LS", "left").wait(60).mark().lift("LS").let_go("Start").wait(300)
            self.assertEqual(pad.typed(), [])

    @scenario("90.10 T6", rules=("R133",), rests=("A25", "A27"))
    def test_a_stick_touch_clears_a_stale_guard(self):
        for pad in self.each():
            pad.push("LS", "left").hold("Start").wait(100)
            self.assertEqual(pad.top, LEFT_GUARD)
            pad.miss("Start").wait(300).touch("RS")
            self.assertTrue(pad.lacks(LEFT_GUARD, "Menu Right: Entry Point"))
            pad.lift("RS").lift("LS").wait(300).mark().tap("Start").wait(300)
            self.assertEqual((pad.typed(), pad.stack), (["TAB"], pad.layers("Base")))    # the next tap is normal

    @scenario("90.10 T7", rests=("A8", "A14"))
    def test_the_accepted_gap_under_the_menu_tap_cover(self):
        for pad in self.each():
            pad.push("LS", "left").hold("Start").wait(300)
            self.assertEqual(pad.top, COVER)
            pad.tap("Select", ms=20)                                         # a bump of the other menu button
            self.assertTrue(pad.lacks(COVER))
            pad.wait(250)
            self.assertEqual(pad.top, COVER)                                 # back within about 200 ms
        for pad in self.each():
            pad.push("LS", "left").hold("Start").wait(300).mark()
            pad.tap("Select", ms=20).wait(50).let_go("Start").wait(300)
            self.assertEqual(pad.typed(), ["TAB"])                           # a release inside the gap types its key
        for pad in self.each():                                              # a stick out and no cover yet
            pad.push("LS", "left").hold("Start").wait(80).mark().tap("Select", ms=20).wait(300)
            self.assertEqual(pad.typed(), ["ESCAPE"])

    @scenario("90.10 T8", rules=("R138",), rests=("A10",))
    def test_the_other_menu_button_types_one_backspace_or_enter_before_fn_is_up(self):
        """Changed in 90.25. The press no longer types at once: a tap types the key once, from its window, and
        a hold of 150 ms enters Menu Keys (90.25 M1, M2). The key held down is the double tap and hold (M3)."""
        for first, second, key in (("Start", "Select", "BACKSPACE"), ("Select", "Start", "RETURN")):
            for pad in self.each():
                pad.hold(first).wait(50).hold(second)
                self.assertEqual((pad.typed(), pad.down()), ([], []))
                pad.wait(100).let_go(second).wait(60)
                self.assertEqual((pad.typed(), pad.down()), ([key], [key]))  # one tap, one key
                pad.wait(300).let_go(first).wait(300)
                self.assertEqual((pad.typed(), pad.stack), ([key], pad.layers("Base")))

    @scenario("90.10 T9")
    def test_the_right_stick_does_nothing_while_a_menu_button_is_held(self):
        for pad in self.each():
            pad.hold("Start").push("RS").wait(500)
            self.assertTrue(pad.lacks("Gyro Off Ramp Up", "Turning Ramp Up 0"))
            self.assertEqual(pad.typed(), [])
            pad.recentre("RS").let_go("Start").wait(400).push("RS")
            self.assertTrue(pad.has("Gyro Off Ramp Up"))                     # and comes back on release

    @scenario("90.10 T10", rules=("R140",), rests=("A37",))
    def test_a_mouse_button_fires_through_a_window(self):
        """The checklist asked whether a held click is interrupted when a window lands or times out. The
        binding hands the button over at the same moment both times (A37), so by that assumption it isn't."""
        for pad in self.each():
            pad.tap("L1").wait(20)
            self.assertEqual(pad.top, "L1: Double Tap")
            pad.mark().hold("LF")
            self.assertEqual(pad.typed(), ["mouse_button LEFT"])
        for pad in self.each(variants=("default",)):                         # with the ramp layers up first; in the
            # alternative a soft pull during ramp-up keeps the block, so its modifier tap opens no window there
            pad.push("RS").wait(300).tap("L1").wait(20).mark().hold("LF")
            self.assertEqual((pad.top, pad.typed()), ("L1: Double Tap", ["mouse_button LEFT"]))
        for pad in self.each():                                              # a click held across the window
            pad.hold("LF").tap("L1").wait(200)
            self.assertEqual(pad.down(), ["mouse_button LEFT"])
            self.assertEqual(pad.typed().count("mouse_button LEFT"), 1)
        for pad in self.each(start="steering"):                              # and inside a Steering window
            pad.hold("R1").flick("LS", "up").wait(50).mark().hold("LF")
            self.assertEqual((pad.top, pad.typed()), (WINDOW, ["mouse_button LEFT"]))


class Steering(ScenarioCase):
    @scenario("90.10 D1")
    def test_menu_buttons_in_steering(self):
        for pad in self.each(start="steering"):
            pad.tap("Start").wait(300)
            self.assertEqual((pad.typed(), pad.stack), (["TAB"], pad.layers("Base", "Steering")))
            pad.hold("Start").wait(300)
            self.assertEqual(pad.top, "Stateful | Menu Right: Fn Layer")     # Steering's own copy since 90.28
            pad.let_go("Start").hold("R1").mark().tap("Start").tap("Select")
            self.assertEqual(pad.typed(), ["TAB", "ESCAPE"])                 # plain keys with a driver held

    @scenario("90.10 D3", rests=("A8",), either=("A9",))
    def test_the_stick_modifier_ends_on_a_roll_to_the_side(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "up").wait(60)
            self.assertEqual(pad.top, MOD1)                                  # the R1 modifier map
            pad.roll("LS", "left").wait(500)
            self.assertTrue(pad.lacks(MOD1))                                 # since 90.52 the map ends as up lets go (until 90.51 it stayed
            self.assertEqual(pad.down(), ["A", "W"])                         # until the ring came back). A steers either way
            pad.mark().recentre("LS").wait(300)
            self.assertEqual((pad.top, pad.typed()), ("Steering | R1: W Key", []))
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "up").wait(60).roll("LS", "down").wait(50)     # straight to down inside 250 ms
            self.assertEqual(pad.top, MOD0)                                  # the other map takes over

    @scenario("90.10 D4", rests=("A36",))
    def test_stick_first_then_the_driver_is_a_modifier(self):
        """Until 90.30 the driver took over when it came after the stick: the R1 modifier map was there at once.
        In 90.31 and 90.32 it left Steering. Since 90.33 stick up or down with no driver brings in the fallback
        guard, and a driver pressed after that, with the stick out, is its Gyro modifier (the author,
        2026-10-04). Since 90.34 the guard comes at once, so the order alone decides. The map comes when the
        driver is held first (D3). Since 90.42 a full deflection clears Steering
        directly, so the later driver is Base's modifier."""
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(20).mark().hold("R1").wait(60)
            self.assertTrue(pad.lacks("Steering | LS: Entry Guard", "Steering", MOD1))
            self.assertEqual((pad.top, pad.typed(), pad.down()), ("R1: Modifier 1", [], ["W"]))

    @scenario("90.10 D5", rules=("R146", "R147", "R148"), rests=("A16",))
    def test_the_stick_double_tap(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").mark().flick("LS", "up").wait(49)
            self.assertEqual((pad.top, pad.typed()), (WINDOW, []))
            pad.wait(1)
            self.assertEqual(pad.typed(), ["mouse_wheel SCROLL_UP"])         # one scroll, 50 ms after centre since 90.52 (150 before)
            pad.wait(100)
            self.assertEqual((pad.top, pad.typed()), ("Steering | R1: W Key", ["mouse_wheel SCROLL_UP"]))   # the window closes at 150 ms
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(50).mark().push("LS", "up").wait(600)
            self.assertGreater(pad.typed().count("mouse_wheel SCROLL_UP"), 3)        # flick, then flick and hold: it repeats
            pad.recentre("LS").mark().wait(300)
            self.assertEqual((pad.top, pad.typed()), ("Steering | R1: W Key", []))   # releasing stops it and adds nothing
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(50).mark().push("LS", "down").wait(300)
            self.assertTrue(pad.has(MOD0))                                   # down inside 150 ms: the down map
            self.assertEqual(pad.typed(), [])                                # and no scroll
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(20).mark().push("LS", "left")
            self.assertEqual(pad.typed(), ["A"])                             # sideways: A at once
            pad.wait(100)
            self.assertEqual(pad.typed(), ["A", "mouse_wheel SCROLL_UP"])    # and the scroll still lands, at 50 ms since 90.52

    @scenario("90.10 D6", rests=("A10", "A11", "A37"))
    def test_w_carries_on_through_the_window_and_after_it(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").mark().flick("LS", "up")
            self.assertEqual(pad.down(), ["W"])
            pad.wait(300)
            self.assertEqual((pad.down(), pad.typed().count("W")), (["W"], 0))       # held throughout, never retyped
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(50).let_go("R1")           # the driver released inside the window
            self.assertEqual((pad.stack, pad.down()),
                             (pad.layers("Base", "Steering", "LST: Entry Point"), []))  # the thumb still rests on LS
            pad.lift("LS").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.10 D7")
    def test_the_other_driver_inside_the_window_types_its_key_and_adds_no_map(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").flick("LS", "up").wait(50).mark().tap("L1", ms=40).wait(300)
            self.assertEqual(pad.typed(), ["S"])                             # its key for that moment
            self.assertFalse([t for t in pad.stack if "Modifier" in t])      # no two-modifier map
            self.assertEqual(pad.down(), ["W"])                              # driving carries on

    # On the 90.66 build: since 90.67 the left-edge cleanup leaves the Entry Guard, and `Steering` stays (R176).
    @scenario("90.10 D8", rules=("R133",), rests=("A25",), frozen="90.66")
    def test_a_mapped_button_uses_up_the_tap_and_a_stuck_map_clears(self):
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "up").wait(60).mark().tap("A")
            self.assertEqual(pad.typed(), ["H"])
            pad.mark().recentre("LS").wait(300)
            self.assertEqual(pad.typed(), [])                                # recentring is then silent
        for pad in self.each(start="steering"):
            pad.hold("R1").push("LS", "up").wait(60).miss("R1").hold("A")
            self.assertFalse([t for t in pad.stack if "Modifier" in t or "W Key" in t])   # the steering branch clears
            # The held full direction now exits Steering once recovery exposes it.
            self.assertTrue(pad.lacks("Steering", "Steering | LS: Entry Guard"))


if __name__ == "__main__":
    unittest.main()
