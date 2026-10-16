"""Scenarios for 90.21: the stateful Cursor Gyro layer.

The record is findings/2026-10-03-cursor-gyro/README.md. Select plus the right-stick click enters
it, on top of Gyro. It is left by any menu button plus any stick click and by pushing both
sticks out. Since 90.44 the Modifier 2 quick tap retains Cursor Gyro. The stick exit is only
in Cursor Gyro: a layer on top that
binds the stick edges answers instead.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

GESTURES = (("Start", "LS"), ("Select", "RS"), ("Start", "RS"), ("Select", "LS"))
FEEDBACK = ["haptic", "beep"]              # the low pulse on the menu Release (since 90.41), then the beep
CURSOR = "Cursor Gyro"
HOME = ("Base", "Gyro", CURSOR)
ENTRY_POINT = {"Select": "Stateful | Menu Left: Entry Point", "Start": "Stateful | Menu Right: Entry Point"}
RAMP = ("Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1")


def enter(pad):
    """Select plus the right-stick click, the click released first, and the thumb off the stick."""
    return pad.hold("Select").click("RS").let_go("Select").lift("RS").wait(300)


def out(pad, stick):
    return pad.push(stick, "up" if stick == "LS" else None)


def both_out(pad):
    return out(out(pad, "LS"), "RS").wait(100)


class CursorGyro(ScenarioCase):
    @scenario("90.21 C1", rules=("R157", "R161", "R163"))
    def test_select_plus_the_right_stick_click_enters_it_on_top_of_gyro(self):
        for start in (None, ("Base", "Gyro")):
            for pad in self.each(start=start):
                pad.hold("Select").click("RS")                                  # the click released first
                self.assertEqual(pad.top, "Transition Set 1")
                self.assertEqual(len(pad.stack), len(start or ("Base",)) + 1)   # everything else is cleared (R163)
                pad.mark().let_go("Select")
                self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], FEEDBACK)
                self.assertEqual(pad.seen("beep"), [("beep", CURSOR)])          # one beep, on the layer's add
                pad.lift("RS").wait(300)
                self.assertEqual(pad.stack, pad.layers(*HOME))                  # Gyro is on, whether it was or not
                self.assertFalse(pad.gyro_off())

    @scenario("90.21 C2", rules=("R158", "R161"))
    def test_all_four_gestures_leave_it_and_keep_gyro(self):
        for menu, stick in GESTURES:
            for pad in self.each():
                enter(pad).hold(menu)
                self.assertEqual(pad.top, ENTRY_POINT[menu])
                pad.click(stick)
                self.assertEqual(pad.stack, pad.layers("Base", "Gyro", "Transition Set 2"))    # the clear
                pad.mark().let_go(menu)
                self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], FEEDBACK)
                pad.lift(stick).wait(300)
                self.assertEqual(pad.stack, pad.layers("Base", "Gyro"))

    @scenario("90.21 C3", rules=("R159",))
    def test_the_modifier_2_quick_tap_removes_gyro_and_retains_cursor(self):
        for first, second in (("L1", "R1"), ("R1", "L1")):
            for pad in self.each():
                enter(pad).hold(first).wait(20).hold(second).wait(40)
                self.assertTrue(pad.has(CURSOR))
                pad.let_go(second).wait(20).let_go(first).wait(300)
                self.assertEqual(pad.stack, pad.layers("Base", CURSOR))

    @scenario("90.21 C4", rules=("R135",), rests=("A36",))
    def test_both_sticks_out_remove_only_the_layer(self):
        for first in ("LS", "RS"):
            for pad in self.each():
                out(enter(pad), first).wait(300)
                self.assertTrue(pad.has(CURSOR))                                # one stick alone does nothing
                self.assertTrue(pad.lacks(*RAMP))                               # and adds no ramp-up: the layer takes the edge
                out(pad.mark(), "RS" if first == "LS" else "LS").wait(100)      # either stick can be the second
                self.assertTrue(pad.lacks(CURSOR) and pad.has("Gyro"))
                self.assertEqual(pad.seen("beep"), [("beep", CURSOR)])
                pad.lift("LS").lift("RS").wait(300)
                self.assertEqual(pad.stack, pad.layers("Base", "Gyro"))

    @scenario("90.21 C5", rules=("R135",), either=("A9",))
    def test_a_held_modifier_answers_both_sticks_and_the_exit_waits_for_it(self):
        """Nothing on top carries the exit (author, 2026-10-03). Under a held modifier both sticks add its
        Tap Cover, as they always did. The exit's chords repeat, so it follows when the modifier is let go
        with the sticks still out."""
        for pad in self.each():
            both_out(enter(pad).hold("L1").wait(100))
            self.assertEqual(pad.stack, pad.layers(*HOME, "Gyro | L1: Modifier 0", "L1: Tap Cover"))
            pad.let_go("L1").wait(150)
            self.assertTrue(pad.lacks(CURSOR) and pad.has("Gyro"))
        for pad in self.each():                                                 # sticks back first: the layer stays
            both_out(enter(pad).hold("L1").wait(100)).lift("LS").lift("RS").wait(100).let_go("L1").wait(300)
            self.assertEqual(pad.stack, pad.layers(*HOME))

    @scenario("90.21 C6", rules=("R135", "R140"), either=("A9",))
    def test_a_window_answers_both_sticks_and_the_exit_follows_when_it_closes(self):
        for pad in self.each():
            out(out(enter(pad).tap("L1").wait(10), "LS"), "RS").wait(40)
            self.assertEqual(pad.stack, pad.layers(*HOME, "L1: Double Tap"))    # the window clears both edges
            pad.wait(200)
            self.assertTrue(pad.lacks(CURSOR, "L1: Double Tap") and pad.has("Gyro"))

    @scenario("90.21 C7", rules=("R162",), rests=("A10",))
    def test_a_menu_tap_types_its_key_and_the_layer_stays(self):
        for menu, key in (("Start", "TAB"), ("Select", "ESCAPE")):
            for pad in self.each():
                enter(pad).mark().hold(menu).wait(50)
                self.assertEqual(pad.top, ENTRY_POINT[menu])
                self.assertTrue(pad.gyro_off())                                 # the pointer stops while a menu button is held
                pad.let_go(menu).wait(400)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers(*HOME), [key]))

    @scenario("90.21 C8", rules=("R120",))
    def test_a_modifier_hold_still_brings_the_temp_cursor_and_leaves_the_layer(self):
        for side in ("L1", "R1"):
            for pad in self.each():
                enter(pad).hold(side).wait(350)
                self.assertEqual(pad.top, f"{side}: Temp Cursor Gyro")
                pad.let_go(side).wait(300)
                self.assertEqual(pad.stack, pad.layers(*HOME))

    @scenario("90.21 C9", rules=("R135",), either=("A9",))
    def test_entering_with_both_sticks_out_leaves_again_at_once(self):
        for pad in self.each():
            both_out(pad).hold("Select").wait(30).click("RS").mark().let_go("Select").wait(150)
            self.assertIn(("add", pad.title(CURSOR)), pad.seen("add"))
            self.assertTrue(pad.lacks(CURSOR) and pad.has("Gyro"))              # Gyro stays on


if __name__ == "__main__":
    unittest.main()
