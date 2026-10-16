"""Scenarios for 90.22: the Gamepad layer and the third transition.

The record is findings/2026-10-03-gamepad/README.md. Start plus the right-stick click, or Select
plus the left-stick click, enters Gamepad. Every control is then a gamepad control. Start and
Select use Steam's own Double Press and Long Press (A43), and a menu button held plus a stick
click leaves, through the clear transition. The Modifier 2 quick tap doesn't leave it.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

SAME_SIDE = (("Start", "RS"), ("Select", "LS"))
GESTURES = (("Start", "LS"), ("Select", "RS"), ("Start", "RS"), ("Select", "LS"))
FEEDBACK = ["haptic", "beep"]              # the low pulse on the menu Release (since 90.41), then the beep
GAMEPAD, SAME, CLEAR = "Gamepad", "Transition Set 0", "Transition Set 2"
BUTTON = {"Start": "xinput_button START", "Select": "xinput_button SELECT"}
SENT = {"A": "A", "B": "B", "X": "X", "Y": "Y", "Up": "DPAD_UP", "Down": "DPAD_DOWN", "Left": "DPAD_LEFT",
        "Right": "DPAD_RIGHT", "LB": "SHOULDER_LEFT", "RB": "SHOULDER_RIGHT",
        "L4": "JOYSTICK_LEFT", "L5": "B", "R4": "A", "R5": "Y"}


def enter(pad, menu="Start", stick="RS"):
    """A same-side gesture, the click released first, and the thumb off the stick."""
    return pad.hold(menu).click(stick).let_go(menu).lift(stick).wait(400)


def click_down(pad, stick):
    pad.touch(stick)
    pad.sim.press(pad.control(stick + " click"))
    return pad


def click_up(pad, stick):
    pad.sim.release(pad.control(stick + " click"))
    return pad


class Gamepad(ScenarioCase):
    @scenario("90.22 G1", rules=("R157", "R161", "R163"))
    def test_the_two_same_side_gestures_enter_it(self):
        for start in (None, ("Base", "Gyro")):
            for menu, stick in SAME_SIDE:
                for pad in self.each(start=start):
                    pad.hold(menu).click(stick)                                  # the click released first
                    self.assertEqual(pad.stack, pad.layers(*(start or ("Base",)), SAME))    # everything else cleared (R163)
                    pad.mark().let_go(menu)
                    self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], FEEDBACK)
                    self.assertEqual(pad.seen("beep"), [("beep", GAMEPAD)])
                    pad.lift(stick).wait(300)
                    self.assertEqual(pad.stack, pad.layers(*(start or ("Base",)), GAMEPAD))  # Gyro stays as it was
                    self.assertTrue(pad.gyro_off())
                    self.assertEqual(pad.typed(), [])                            # no Start or Select from the gesture

    @scenario("90.22 G2", rules=("R168",), rests=("A43", "A44"))
    def test_a_tap_a_double_press_and_a_hold_on_start_and_select(self):
        for menu, button in BUTTON.items():
            for pad in self.each():
                enter(pad).mark().tap(menu)
                self.assertEqual(pad.typed(), [])                                # the tap waits out the Double Press time
                pad.wait(300)
                self.assertEqual((pad.typed(), pad.down()), ([button], []))
            for pad in self.each():
                enter(pad).mark().hold(menu).wait(600)
                self.assertEqual((pad.typed(), pad.down()), ([], []))            # a hold sends nothing
                self.assertEqual(len(pad.seen("haptic")), 1)                     # and gives the light pulse
                pad.let_go(menu).wait(300)
                self.assertEqual(pad.typed(), [])
            for pad in self.each():
                enter(pad).mark().tap(menu).wait(60).hold(menu).wait(600)
                self.assertEqual((pad.typed(), pad.down()), ([button], [button]))   # held for as long as the second press
                pad.let_go(menu).wait(300)
                self.assertEqual((pad.typed(), pad.down()), ([button], []))
            for pad in self.each():
                enter(pad).mark().tap(menu).wait(400).tap(menu).wait(400)
                self.assertEqual(pad.typed(), [button, button])                  # two slow taps are two taps
                self.assertEqual(pad.stack, pad.layers("Base", GAMEPAD))         # none of it changes a layer

    @scenario("90.22 G3", rules=("R158", "R161", "R163"), rests=("A27", "A45"))
    def test_a_menu_button_held_plus_a_stick_click_leaves_it(self):
        for start in (None, ("Base", "Gyro")):
            for menu, stick in GESTURES:
                for pad in self.each(start=start):
                    click_down(enter(pad).mark().hold(menu).wait(300), stick)
                    self.assertEqual(pad.stack, pad.layers(*(start or ("Base",)), CLEAR))   # at the click's press
                    click_up(pad, stick).mark().let_go(menu)
                    self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], FEEDBACK)
                    pad.lift(stick).wait(300)
                    self.assertEqual(pad.stack, pad.layers(*(start or ("Base",))))
                    self.assertEqual(pad.typed(), [])                            # no stick click, Start or key was sent

    @scenario("90.22 G4", rules=("R158",), rests=("A15", "A43", "A45"))
    def test_a_quick_press_and_click_leaves_and_sends_no_start(self):
        """The click comes before the Long Press time. The clear transition binds the menu button, which
        ends the tap that was waiting on it."""
        for menu in BUTTON:
            for pad in self.each():
                click_down(enter(pad).mark().hold(menu).wait(50), "LS")
                self.assertEqual(pad.top, CLEAR)
                click_up(pad, "LS").let_go(menu).lift("LS").wait(400)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))

    @scenario("90.22 G5", rules=("R158",), rests=("A11", "A45"))
    def test_letting_go_of_the_menu_button_before_the_click_types_one_key(self):
        """The accepted cost of entering the clear at the click's press: Base is live under a held click."""
        for stick, key in (("LS", "Q"), ("RS", "E")):
            for pad in self.each():
                click_down(enter(pad).mark().hold("Start").wait(300), stick).let_go("Start")
                self.assertTrue(pad.lacks(GAMEPAD, CLEAR))
                self.assertEqual(pad.down(), [key])
                click_up(pad, stick).lift(stick).wait(300)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), [key]))

    @scenario("90.22 G6", rules=("R159",))
    def test_the_modifier_2_quick_tap_does_not_leave_it(self):
        for first, second in (("L1", "R1"), ("R1", "L1")):
            for pad in self.each(start=("Base", "Gyro")):
                enter(pad).mark().hold(first).wait(20).hold(second).wait(40).let_go(second).wait(20).let_go(first).wait(400)
                self.assertEqual(pad.stack, pad.layers("Base", "Gyro", GAMEPAD))
                self.assertFalse(pad.seen("add", "remove"))                      # no modifier layer came or went

    @scenario("90.22 G7", rules=("R168",))
    def test_every_control_is_a_gamepad_control_and_nothing_lands_on_the_layer(self):
        for pad in self.each(start=("Base", "Gyro")):
            entered = len(enter(pad).sim.log)
            for name, button in SENT.items():
                pad.mark().tap(name)
                self.assertEqual(pad.typed(), ["xinput_button " + button], name)
            for name in ("LT", "RT", "LT full", "RT full"):                     # analog triggers: no button, no layer
                pad.mark().tap(name)
                self.assertEqual(pad.typed(), [], name)
            pad.mark().click("LS").click("RS")
            self.assertEqual(pad.typed(), ["xinput_button JOYSTICK_LEFT", "xinput_button JOYSTICK_RIGHT"])
            pad.mark().push("LS", "up").push("RS").wait(400).lift("LS").lift("RS")
            self.assertEqual(pad.typed(), [])                                    # the sticks send no key, and no ramp-up comes
            pad.mark().click_pad("LP", "centre").click_pad("RP", "left").wait(300)
            self.assertEqual(pad.typed(), ["xinput_button SELECT", "xinput_button START"])
            self.assertEqual(pad.stack, pad.layers("Base", "Gyro", GAMEPAD))
            self.assertFalse([what for _, what, _ in pad.sim.log[entered:] if what in ("add", "remove")])   # no layer command at all


if __name__ == "__main__":
    unittest.main()
