"""Scenarios for 90.24: the required cleanups (R169 to R171).

The record is findings/2026-10-04-required-cleanups/README.md. Every layer got a cleanup function on
both stick touches, on the stick edges and on every button it retypes or blocks. A layer left on by a
release that was missed while the Steam menu was open (A25) now ends on the next stick touch, push or
button press, and the same press then does what it does in the layer underneath.
"""
import unittest

from tests.scenario import SOURCES, ScenarioCase, scenario

TRANSITIONS = ("Transition Set 0", "Transition Set 1", "Transition Set 2")


def lose_pad(pad, name="RP"):
    """The thumb leaves the pad while the Steam menu is open: the layout never sees it (A25)."""
    pad.sim.lose((SOURCES[name], "touch"))
    return pad


def second_press(pad, button):
    """Tap, then press and hold: the button's second-press layer and its Double Tap Cover."""
    return pad.tap(button).wait(30).hold(button).wait(400)


# What leaves a layer on, and the layers that must be gone after the next press.
STUCK = {
    "the menu second-press layer and its cover": (
        lambda pad: second_press(pad, "Select").miss("Select"), ("Menu Left: Escape", "Menu Left: Double Tap Cover")),
    "the scroll layer and its cover": (
        lambda pad: second_press(pad, "R1").miss("R1"), ("R1: Scroll Up", "R1: Double Tap Cover")),
    "the Fn layer and its Entry Point": (
        lambda pad: pad.hold("Select").wait(300).miss("Select"), ("Menu Left: Fn Layer", "Menu Left: Entry Point")),
    "the Modifier 2 layer and the combined cover": (
        lambda pad: pad.hold("L1").wait(50).hold("R1").wait(500).miss("L1", "R1"),
        ("L1!R1: Modifier 2", "L1&R1: Tap Cover", "L1: Modifier 0", "R1: Modifier 1")),
    "the right pad's Entry Point and Tap Cover": (
        lambda pad: lose_pad(pad.touch("RP").wait(300)), ("RTP: Entry Point", "RTP: Tap Cover")),
}


class RequiredCleanups(ScenarioCase):
    @scenario("90.24 K1", rules=("R169",), rests=("A25",))
    def test_a_stick_touch_ends_a_layer_whose_release_was_missed(self):
        for label, (leave_on, layers) in STUCK.items():
            for stick in ("LS", "RS"):
                for pad in self.each():
                    leave_on(pad)
                    self.assertTrue(pad.has(*layers), label)
                    pad.touch(stick)
                    self.assertTrue(pad.lacks(*layers), label)
        for pad in self.each(start=("Base", "Gyro")):                    # the cursor layer over the Gyro modifier
            pad.hold("L1").wait(500).miss("L1")
            self.assertEqual(pad.top, "L1: Temp Cursor Gyro")
            pad.touch("LS")
            self.assertTrue(pad.lacks("L1: Temp Cursor Gyro", "Gyro | L1: Modifier 0") and pad.has("Gyro"))

    @scenario("90.24 K2", rules=("R169",), rests=("A17", "A27"))
    def test_a_stick_touch_does_nothing_while_the_layers_button_is_held(self):
        for pad in self.each():
            second_press(pad, "R1").mark().touch("LS").touch("RS").wait(300)
            self.assertTrue(pad.has("R1: Scroll Up", "R1: Double Tap Cover"))
            pad.lift("LS").lift("RS").let_go("R1").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))
        for pad in self.each():
            pad.touch("RP").wait(300).touch("LS").touch("RS").wait(300)
            self.assertTrue(pad.has("RTP: Entry Point", "RTP: Tap Cover"))

    @scenario("90.24 K3", rules=("R170",), rests=("A25",))
    def test_a_stick_push_ends_a_steering_layer_whose_release_was_missed(self):
        for pad in self.each(start="steering"):                          # the right edge is new in the W Key layer
            pad.hold("R1").wait(100).miss("R1")
            self.assertEqual(pad.top, "Steering | R1: W Key")
            pad.push("RS").wait(60)
            self.assertTrue(pad.lacks("Steering | R1: W Key"))
            pad.lift("RS").wait(100)                                     # the ramp exits, while the short thumb touch
            self.assertEqual(pad.stack, pad.layers("Base", "Steering", "RST: Double Tap"))  # now opens its 200 ms window
            pad.wait(100)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))
        for pad in self.each(start="steering"):                          # both edges were blocks in the Modifier 2 layer
            pad.hold("R1").wait(50).hold("L1").wait(600).miss("L1", "R1")
            self.assertTrue(pad.has("Steering | R1!L1: Modifier 2"))
            pad.push("RS").wait(60)
            self.assertTrue(pad.lacks("Steering | R1!L1: Modifier 2", "Steering | R1: W Key"))
            pad.lift("RS").wait(100)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering", "RST: Double Tap"))
            pad.wait(100)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))
        for pad in self.each(start="steering"):                          # and nothing happens while the driver is held
            pad.hold("R1").wait(100).push("RS").wait(300)
            self.assertEqual((pad.top, pad.down()), ("Steering | R1: W Key", ["W"]))

    @scenario("90.24 K4", rules=("R171",), rests=("A10", "A25"))
    def test_a_button_press_ends_a_stuck_layer_and_then_does_what_it_does_underneath(self):
        for pad in self.each():                                          # Start was retyped in the scroll layer
            pad.tap("L1").wait(30).hold("L1").wait(100).miss("L1")
            self.assertEqual(pad.top, "L1: Scroll Down")
            pad.mark().tap("Start").wait(300)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), ["TAB"]))
        for pad in self.each():                                          # with L1 held Start is still the scroll layer's
            pad.tap("L1").wait(30).hold("L1").wait(100).mark().tap("Start").wait(300)
            self.assertTrue(pad.has("L1: Scroll Down"))
            self.assertNotIn("TAB", pad.typed())
        for pad in self.each():                                          # the bumpers were retyped in the Entry Point
            pad.hold("Start").wait(30).miss("Start").hold("L1")
            self.assertEqual(pad.stack, pad.layers("Base", "L1: Modifier 0"))
        for pad in self.each(start="steering"):                          # Start in a stuck W Key layer
            pad.hold("R1").wait(100).miss("R1").mark().tap("Start").wait(300)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base", "Steering"), ["TAB"]))

    @scenario("90.24 K5", rules=("R171",), rests=("A17", "A36"))
    def test_the_other_driver_still_adds_the_modifier_2_layer_and_ends_a_stuck_driver_layer(self):
        """In the W and S layers the bind that adds the Modifier 2 layer moved into the guard chord
        (author, 2026-10-04). With this layer's driver held it fires as before."""
        for pad in self.each(start="steering"):
            pad.hold("R1").wait(100).hold("L1").wait(600)
            self.assertTrue(pad.has("Steering | R1: W Key", "Steering | R1!L1: Modifier 2"))
            pad.let_go("L1").wait(100)
            self.assertEqual((pad.top, pad.down()), ("Steering | R1: W Key", ["W"]))
        for pad in self.each(start="steering"):                          # rocking from one driver to the other
            pad.hold("R1").wait(100).hold("L1").wait(100).let_go("R1").wait(100)
            self.assertEqual((pad.top, pad.down()), ("Steering | L1: S Key", ["S"]))
            pad.hold("R1").wait(100).let_go("L1").wait(100)
            self.assertEqual((pad.top, pad.down()), ("Steering | R1: W Key", ["W"]))
        for pad in self.each(start="steering"):                          # R1's release was missed: L1 ends the W Key layer
            pad.hold("R1").wait(100).miss("R1").hold("L1").wait(100)     # and the same press is the S driver
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering", "Steering | L1: S Key"), ["S"]))

    # On the 90.71 build: since 90.72 the menu layers bind the right pad's touch, so its tap chain (RTP: Entry Point,
    # the Double Tap window, Circular Scroll) no longer opens during a menu hold (90.72 E8).
    @scenario("90.24 K6", rules=("R136", "R169"), rests=("A2",), frozen="90.71")
    def test_the_pad_cover_over_a_menu_layer_keeps_the_right_stick_click_from_starting_a_transition(self):
        """Called out by the author (2026-10-04). `RTP: Tap Cover` has a right-stick group in mouse mode since
        90.24. The pad touched first and a menu button pressed before the cover lands at 150 ms puts the cover
        over the menu Entry Point, whose right stick is a D-pad. The Fn layer on top inherits the right-stick
        click from the Entry Point, and across the mode change nothing is inherited (A2): the click does not
        start a transition while the thumb is on the pad. On 90.23 it did in this order.

        Since 90.25 the pad's Entry Point has a reset too, and a reset fires when its layer lands (A6). Here
        the pad's reset and the menu Entry Point's keep restarting each other's delay (A13) until a quiet gap:
        the pad's Tap Cover lands about 550 ms after the touch and the Fn layer about 760 ms."""
        for pad in self.each():
            pad.touch("RP").wait(60).hold("Select").wait(800)
            self.assertLess(pad.stack.index("Menu Left: Entry Point"), pad.stack.index("RTP: Tap Cover"))
            pad.click("RS")
            self.assertTrue(pad.lacks(*TRANSITIONS))
            pad.lift("RS").let_go("Select").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base", "RTP: Entry Point", "RTP: Tap Cover"))
        for pad in self.each():                                          # the pad held for longer first: the Entry Point
            pad.touch("RP").wait(300).hold("Select").wait(100).click("RS")   # is on top, and the click works
            self.assertTrue(pad.has("Transition Set 1"))
        for pad in self.each():                                          # the menu button first: `RTP: Entry Point` already
            pad.hold("Select").wait(60).touch("RP").wait(300).click("RS")    # hid the click before 90.24
            self.assertTrue(pad.lacks(*TRANSITIONS))

    @scenario("90.24 K7", rules=("R140",))
    def test_a_steering_stick_window_types_tab_and_escape_itself(self):
        """The W and S layers' Start and Select hold a cleanup since 90.24, which is a layer command, so the
        two stick windows over them bind the keys themselves."""
        for pad in self.each(start="steering"):
            pad.hold("R1").wait(100).push("LS", "up").wait(100).recentre("LS")
            self.assertEqual(pad.top, "Steering | LS Up: Double Tap")
            pad.mark().tap("Start").tap("Select")
            self.assertEqual([x for x in pad.typed() if not x.startswith("mouse_wheel")], ["TAB", "ESCAPE"])   # the window's own scroll lands at 50 ms since 90.52
            self.assertFalse([t for t in pad.stack if "Menu" in t])


if __name__ == "__main__":
    unittest.main()
