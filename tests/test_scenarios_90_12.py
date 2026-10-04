"""Scenarios for the Deck checks of 90.12 (cleanup lists).

"Miss the release" is the checklist's phrase for: hold the buttons, press the Steam
button, let go of everything, close the Steam menu. The layout never sees the Release.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

GYRO = (None, ("Base", "Gyro"))


class CleanupLists(ScenarioCase):
    @scenario("90.12 C1", rules=("R127", "R128", "R130"))
    def test_a_stick_touch_clears_a_stuck_modifier_2(self):
        for start in GYRO:
            for first, second in (("L1", "R1"), ("R1", "L1")):
                for stick in ("LS", "RS"):
                    for pad in self.each(start=start):
                        home = len(pad.stack)
                        pad.hold(first, second).wait(50).miss(first, second)
                        self.assertGreater(len(pad.stack), home + 3)             # Modifier 2 and its covers are stuck
                        pad.touch(stick)
                        self.assertEqual(pad.stack[:home], pad.layers(*(start or ("Base",))))
                        self.assertFalse([t for t in pad.stack if "Modifier" in t or "Tap Cover" in t and "ST:" not in t])
                        pad.lift(stick).wait(300).mark().tap("A")
                        self.assertEqual(pad.typed(), ["F"])                      # typing works again

    @scenario("90.12 C2", rules=("R127", "R133"), rests=("A27",))
    def test_a_held_bumper_keeps_modifier_2_through_a_stick_touch(self):
        for pad in self.each():
            pad.hold("L1", "R1").wait(300).touch("LS").touch("RS")
            self.assertEqual(pad.top, "L1&R1: Tap Cover")                         # nothing cleared
            pad.mark().tap("A")
            self.assertEqual(pad.typed(), ["M"])                                  # Modifier 2's key
        for pad in self.each():
            pad.hold("L1", "R1").wait(300).miss("R1").touch("RS")                 # stuck, but L1 is still held
            self.assertTrue(pad.has("L1!R1: Modifier 2"))
            pad.lift("RS").let_go("L1").touch("RS")                               # that bumper released too
            self.assertFalse([t for t in pad.stack if "Modifier" in t])

    @scenario("90.12 C3", rules=("R128",))
    def test_one_edge_push_clears_a_stuck_cursor_and_its_modifier(self):
        for side, cursor in (("L1", "L1: Temp Cursor Gyro"), ("R1", "R1: Temp Cursor Gyro")):
            for stick, direction in (("RS", None), ("LS", "up")):
                for pad in self.each():
                    pad.hold(side).wait(300)
                    self.assertEqual(pad.top, cursor)
                    pad.miss(side).push(stick, direction)                         # once
                    self.assertFalse([t for t in pad.stack if "Modifier" in t or "Cursor" in t])

    @scenario("90.12 C4", rules=("R127",), rests=("A27",))
    def test_steering_modifier_2_stays_while_one_bumper_is_held(self):
        for pad in self.each(start="steering"):
            pad.hold("R1", "L1").wait(50)
            self.assertEqual(pad.top, "Steering | R1!L1: Modifier 2")
            pad.miss("R1").touch("RS")
            self.assertEqual(pad.top, "Steering | R1!L1: Modifier 2")             # nothing clears
            pad.lift("RS").let_go("L1").wait(200)
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.12 C5", rests=("A3",))
    def test_rocking_never_scrolls_and_ends_on_base(self):
        for start in GYRO:
            for first, second in (("L1", "R1"), ("R1", "L1")):
                for pad in self.each(start=start):
                    home = pad.stack
                    pad.hold(first, second).wait(200).let_go(first).hold(first).wait(200).let_go(second).let_go(first)
                    self.assertEqual((pad.stack, pad.typed()), (home, []))

    @scenario("90.12 C6", rests=("A10",))
    def test_a_double_tap_scrolls_a_used_bumper_does_not_and_the_quick_tap_toggles_gyro(self):
        for pad in self.each():
            pad.tap("L1").wait(30).hold("L1")                                     # the second tap, inside 150 ms
            self.assertEqual((pad.top, pad.typed()), ("L1: Scroll Down", ["mouse_wheel SCROLL_DOWN"]))
        for pad in self.each():
            pad.hold("L1").tap("A").mark().let_go("L1")
            self.assertEqual(pad.stack, pad.layers("Base"))                       # a clean exit: no window
            pad.hold("L1")                                                        # at once: a new press, not a second tap
            self.assertEqual((pad.top, pad.typed()), ("L1: Modifier 0", []))
        for pad in self.each():
            pad.hold("L1").tap("R1", ms=100)                                      # inside 200 ms
            self.assertTrue(pad.has("Gyro"))
            pad.let_go("L1").wait(300).hold("L1").tap("R1", ms=100).let_go("L1").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base"))                       # and back off

    @scenario("90.12 C7", rules=("R127", "R133"), rests=("A11",))
    def test_a_stuck_modifier_fn_layer_and_driver_each_clear(self):
        """Which input clears depends on where the layer has its cleanup functions: a modifier on the face
        buttons and the stick touches, the Fn layer on the face buttons and the stick edges, a Steering
        driver on the stick touches."""
        for clear in (lambda p: p.hold("A"), lambda p: p.touch("RS")):
            for pad in self.each():
                pad.hold("L1").miss("L1")
                clear(pad)
                self.assertTrue(pad.lacks("L1: Modifier 0"))
        for clear in (lambda p: p.hold("A"), lambda p: p.push("RS")):
            for pad in self.each():
                pad.hold("Start").wait(300).miss("Start")
                self.assertEqual(pad.names()[-2], "Menu Right: Fn Layer")         # under the chorded Entry Point since 90.25
                clear(pad)
                self.assertTrue(pad.lacks("Menu Right: Fn Layer", "Menu Right: Entry Point"))
        for pad in self.each(start="steering"):
            pad.hold("R1").miss("R1")
            self.assertEqual(pad.top, "Steering | R1: W Key")
            pad.touch("RS")
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.12 C8", rules=("R128",), rests=("A8",))
    def test_the_menu_hold_with_a_stick_out_and_the_fn_release_leave_nothing_behind(self):
        for pad in self.each():
            pad.hold("Start").push("LS", "up")
            self.assertEqual(pad.top, "Menu Buttons: Left Stick Guard")
            pad.mark().let_go("Start").wait(200)                                  # a quick release: Tab, as before
            self.assertIn("TAB", pad.typed())
            self.assertFalse([t for t in pad.stack if "Menu" in t])
        for pad in self.each():
            pad.hold("Start").wait(250)
            self.assertEqual(pad.names()[-2], "Menu Right: Fn Layer")
            pad.mark().let_go("Start").wait(300)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))  # Fn gone, nothing typed


if __name__ == "__main__":
    unittest.main()
