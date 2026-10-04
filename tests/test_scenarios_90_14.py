"""Scenarios for 90.14: a pad click is decided once, through a Click Entry Point.

A click adds `LTP: Click Entry Point` or `RTP: Click Entry Point`. That layer binds the pad's
edge with two repeating Soft Presses: the centre range adds the single-button Middle Click
layer, the outer range adds the D-pad layer (`LTP: Arrow Keys`, `RTP: Mouse Buttons`). The
record is findings/2026-10-03-pad-middle-click/README.md.

The simulator knows a pad's edge as held or not: held is the outer range, not held is the
centre. `press_pad(pad, "ring left")` is the ring where the two ranges overlap. Since 90.18 the
Click Entry Point removes itself when it adds the chosen layer, so the two are never on the stack
together. P5 and P7 were
rewritten for 90.16, and P6 (the ring without the interruption) went with A39. The left pad's
centre was Show Keyboard until 90.16, which the simulator doesn't show; it is Caps Lock since 90.17.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

RANGES = ("A6", "A10", "A40", "A41")       # what a pad click's outcome rests on: the repeating add, the output
GYRO = (None, ("Base", "Gyro"))            # on a held click, and the two ranges


class PadClick(ScenarioCase):
    @scenario("90.14 P1", rules=("R113",), rests=RANGES)
    def test_a_centre_click_is_the_middle_click(self):
        for start in GYRO:
            for pad in self.each(start=start):
                home = pad.stack
                pad.press_pad("RP", "centre")                                             # at once: the centre bind repeats (A6)
                self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))
                self.assertTrue(pad.lacks("RTP: Mouse Buttons"))
                pad.wait(1000)
                self.assertEqual(pad.down(), ["mouse_button MIDDLE"])                     # held for a middle drag
                pad.let_go_pad("RP").wait(400)
                self.assertEqual((pad.stack, pad.down(), pad.typed()), (home, [], ["mouse_button MIDDLE"]))

    @scenario("90.14 P2", rules=("R113",), rests=RANGES)
    def test_an_outer_click_is_the_d_pad_button(self):
        for where, output in (("left", "mouse_button BACK"), ("right", "mouse_button FORWARD")):
            for pad in self.each():
                pad.press_pad("RP", where).wait(50)
                self.assertEqual((pad.top, pad.down()), ("RTP: Mouse Buttons", [output]))
                self.assertTrue(pad.lacks("RTP: Middle Click"))
                pad.let_go_pad("RP").wait(400)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), [output]))
        for pad in self.each():
            pad.press_pad("RP", "up").wait(100)
            self.assertEqual(pad.typed(), ["mouse_wheel SCROLL_UP"])                      # one step at once
            pad.wait(600)
            self.assertGreater(len(pad.typed()), 2)                                       # held: it keeps scrolling
            pad.let_go_pad("RP").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.14 P3", rules=("R113",), rests=RANGES)
    def test_the_left_pad_has_the_same_two_layers(self):
        for pad in self.each():
            pad.press_pad("LP", "centre").wait(50)
            self.assertEqual((pad.names()[1:], pad.down()), (("LTP: Entry Point", "LTP: Middle Click"), ["CAPSLOCK"]))   # the Entry Point since 90.25
            pad.let_go_pad("LP").wait(400)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), ["CAPSLOCK"]))   # Caps Lock since 90.17
        for where, key in (("up", "UP_ARROW"), ("down", "DOWN_ARROW"), ("left", "LEFT_ARROW"), ("right", "RIGHT_ARROW")):
            for pad in self.each():
                pad.press_pad("LP", where).wait(50)
                self.assertEqual((pad.names()[1:], pad.down()), (("LTP: Entry Point", "LTP: Arrow Keys"), [key]))
                pad.let_go_pad("LP").wait(400)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), [key]))

    @scenario("90.14 P4", rests=("A2", "A10"))
    def test_the_choice_holds_while_the_thumb_slides(self):
        for pad in self.each():
            pad.press_pad("RP", "centre").wait(100).slide_pad("RP", "left").wait(300)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))
            pad.let_go_pad("RP").wait(400)
            self.assertEqual(pad.typed(), ["mouse_button MIDDLE"])                        # never Back
        for pad in self.each():
            pad.press_pad("RP", "left").wait(100).slide_pad("RP", "centre").wait(300)
            self.assertEqual((pad.top, pad.down()), ("RTP: Mouse Buttons", []))           # Back let go, no middle click
            pad.slide_pad("RP", "right").wait(100)
            self.assertEqual(pad.down(), ["mouse_button FORWARD"])                        # the D-pad buttons still work
            pad.let_go_pad("RP").wait(400)
            self.assertEqual(pad.typed(), ["mouse_button BACK", "mouse_button FORWARD"])

    @scenario("90.14 P5", rests=RANGES + ("A5",))
    def test_the_overlap_of_the_two_ranges_sends_one_output(self):
        """Changed in 90.16. Until 90.15 the centre Soft Press was meant to interrupt the outer one (A39). Now both
        are uninterruptible and the outer one has a 5 ms delay. The centre one has no delay and repeats.

        Changed on 2026-10-04 (author): a repeating action always triggers, so the centre one fires as the layer
        lands (A6) and the outer one's 5 ms delay gives it priority: the middle click wins the ring. Until then
        the simulator made the centre one wait for its repeat, and the D-pad button won. Either way it is one
        output."""
        for pad in self.each():
            pad.press_pad("RP", "ring left").wait(300)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))
            self.assertTrue(pad.lacks("RTP: Mouse Buttons"))
            pad.let_go_pad("RP").wait(400)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), ["mouse_button MIDDLE"]))
        for pad in self.each():
            pad.press_pad("LP", "ring up").wait(300)
            self.assertEqual((pad.top, pad.down()), ("LTP: Middle Click", ["CAPSLOCK"]))
            pad.let_go_pad("LP").wait(400)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), ["CAPSLOCK"]))

    @scenario("90.14 P7", rules=("R113",), rests=("A6",))
    def test_a_very_short_click_sends_nothing(self):
        """Changed in 90.16: the outer buttons come after a 5 ms delay. Changed on 2026-10-04 (author): the
        middle click comes at once, because its bind repeats (A6), so no centre click is too short."""
        for where, too_short, enough in (("left", 3, 10),):
            for pad in self.each():
                pad.click_pad("RP", where, ms=too_short).wait(400)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))
            for pad in self.each():
                pad.click_pad("RP", where, ms=enough).wait(400)
                self.assertEqual(len(pad.typed()), 1)
        for pad in self.each():
            pad.click_pad("RP", "centre", ms=1).wait(400)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), ["mouse_button MIDDLE"]))

    @scenario("90.14 P8", rules=("R113",), rests=("A10",))
    def test_a_modifier_and_a_pad_click_leave_each_other_alone(self):
        for pad in self.each():                                                           # the modifier first
            pad.hold("L1").wait(50).press_pad("RP", "centre").wait(100)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))
            self.assertTrue(pad.has("L1: Modifier 0"))
            pad.let_go_pad("RP", lift=False).wait(100)
            self.assertTrue(pad.has("L1: Modifier 0") and pad.lacks("RTP: Click Entry Point", "RTP: Middle Click"))
        for pad in self.each():                                                           # the click first
            pad.press_pad("RP", "centre").wait(100).hold("L1").wait(100)
            self.assertEqual((pad.top, pad.down()), ("L1: Modifier 0", ["mouse_button MIDDLE"]))
            pad.let_go_pad("RP").wait(300)
            self.assertEqual((pad.top, pad.down()), ("L1: Modifier 0", []))               # the pad's exit wasn't hidden
            pad.let_go("L1").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.14 P9", rules=("R133",), rests=("A27",))
    def test_a_stick_touch_leaves_a_pad_click_that_is_held(self):
        for stick in ("LS", "RS"):
            for pad in self.each():
                pad.press_pad("RP", "left").wait(100).touch(stick).wait(300)
                self.assertEqual((pad.down(), pad.has("RTP: Mouse Buttons")), (["mouse_button BACK"], True))
                pad.lift(stick).wait(300)
                self.assertTrue(pad.has("RTP: Mouse Buttons"))                            # the thumb on the pad guards it
                pad.let_go_pad("RP").wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.14 P10", rules=("R114",), rests=("A25",), either=("A9",))
    def test_a_missed_click_release_clears_on_its_own(self):
        for where, layer in (("centre", "RTP: Middle Click"), ("left", "RTP: Mouse Buttons")):
            for pad in self.each():
                pad.press_pad("RP", where).wait(100)
                self.assertTrue(pad.has(layer))
                pad.recentre("RP").miss("RP click").wait(300)                             # the exit repeats
                self.assertTrue(pad.lacks("RTP: Click Entry Point", layer))
                self.assertEqual(pad.down(), [])

    @scenario("90.14 P11", rules=("R113",), rests=RANGES)
    def test_a_click_in_circular_scroll_goes_through_the_entry_point(self):
        touch = ("right_trackpad", "touch")
        for pad in self.each():
            pad.sim.press(touch).wait(60).release(touch)                                  # a centre tap outlasts the 50 ms hand-over (90.25)
            pad.wait(50)
            pad.sim.press(touch).press(("right_trackpad", "dpad_north")).release(("right_trackpad", "dpad_north"))
            self.assertEqual(pad.top, "RTP: Circular Scroll")
            pad.wait(200).mark().hold("RP click").wait(100)
            self.assertEqual((pad.names()[-2:], pad.down()),
                             (("RTP: Circular Scroll", "RTP: Middle Click"), ["mouse_button MIDDLE"]))
            pad.let_go("RP click").wait(100)
            self.assertEqual(pad.top, "RTP: Circular Scroll")                             # back to scrolling
            pad.sim.release(touch)
            pad.wait(300)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.14 P12", rests=RANGES)
    def test_a_pad_click_works_in_steering_and_the_modifier_2_clear_takes_it(self):
        for pad in self.each(start="steering"):
            pad.press_pad("RP", "centre").wait(100)
            self.assertEqual((pad.names()[1:], pad.down()),
                             (("Steering", "RTP: Middle Click"), ["mouse_button MIDDLE"]))
            pad.let_go_pad("RP").wait(300)
            self.assertEqual(pad.names(), ("Base", "Steering"))
        for pad in self.each(start="steering"):
            pad.hold("L1").wait(50).hold("R1").wait(50)
            self.assertEqual(pad.top, "Steering | L1!R1: Modifier 2")
            pad.press_pad("RP", "centre").wait(100)
            self.assertEqual(pad.top, "RTP: Middle Click")
            pad.miss("RP click", "RP touch").let_go("R1").wait(50)                        # the quick tap clears to Base
            self.assertTrue(pad.lacks("Steering", "Steering | L1!R1: Modifier 2", "RTP: Click Entry Point",
                                      "RTP: Middle Click"))


if __name__ == "__main__":
    unittest.main()
