"""Scenarios for the older Deck checks on the triggers and ramp-up, the left-stick recovery, the WASD
modifier, missed releases and held inputs. These sections of the checklist predate 90.6.

LF and RF are the firing buttons (the triggers in the default layout, the bumpers in the alternative);
L1 and R1 are the modifier buttons. The ramp layers are the right stick's turn assist.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

RAMP = ("Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1")
STARTS = (None, ("Base", "Gyro"))
RP = ("right_trackpad", "touch")


class TriggersAndRampUp(ScenarioCase):
    @scenario("Triggers and ramp-up TR1")
    def test_the_triggers_click_and_a_menu_button_works_with_one_held(self):
        for pad in self.each():
            pad.hold("LF")
            self.assertEqual(pad.down(), ["mouse_button LEFT"])
            pad.tap("Start").wait(300)
            self.assertEqual(pad.typed(), ["mouse_button LEFT", "TAB"])
            pad.let_go("LF").hold("RF")
            self.assertEqual(pad.down(), ["mouse_button RIGHT"])

    @scenario("Triggers and ramp-up TR3", rules=("R114",))
    def test_the_two_ramp_stages_and_the_way_back(self):
        for stage, wait in (("Turning Ramp Up 0", 5), ("Turning Ramp Up 1", 255)):
            for pad in self.each():
                pad.push("RS")
                self.assertTrue(pad.gyro_off())                              # the gyro turns off
                pad.wait(wait)
                self.assertEqual(pad.top, stage)
                pad.recentre("RS")                                           # moving back in, at either stage
                self.assertTrue(pad.lacks(*RAMP))
                self.assertFalse(pad.gyro_off())

    @scenario("Triggers and ramp-up TR4")
    def test_a_held_trigger_keeps_the_gyro_on_during_ramp_up(self):
        for held in (("LF",), ("RF",), ("LF", "RF")):
            for pad in self.each():
                pad.hold(*held).mark().push("RS").wait(300)
                self.assertTrue(pad.has("Turning Ramp Up 0", "Turning Ramp Up 1") and pad.lacks("Gyro Off Ramp Up"))
                self.assertFalse(pad.gyro_off())
                self.assertEqual(pad.typed(), [])                            # no extra mouse clicks

    @scenario("Triggers and ramp-up TR5", rests=("A11",))
    def test_a_trigger_pull_brings_the_gyro_back_and_the_first_click_registers(self):
        for wait in (100, 400):                                              # in both stages
            for pad in self.each():
                pad.push("RS").wait(wait)
                self.assertTrue(pad.gyro_off())
                pad.mark().hold("LF")
                self.assertFalse(pad.gyro_off())
                self.assertEqual(pad.typed(), ["mouse_button LEFT"])         # the first click registers
                pad.hold("RF").let_go("LF")                                  # letting go of one of two
                self.assertFalse(pad.gyro_off())
                self.assertEqual(pad.down(), ["mouse_button RIGHT"])

    @scenario("Triggers and ramp-up TR6")
    def test_a_held_modifier_lets_no_ramp_layer_in(self):
        for held in (("L1",), ("R1",), ("L1", "R1"), ("LF", "L1")):
            for pad in self.each():
                pad.hold(*held).push("RS").wait(400)
                self.assertTrue(pad.lacks("Gyro Off Ramp Up"))
                self.assertFalse(pad.gyro_off())

    @scenario("Triggers and ramp-up TR7", rules=("R113", "R114"), either=("A9",))
    def test_a_modifier_pressed_during_ramp_up_ends_it(self):
        """In the alternative a soft pull keeps the block and a full pull exits, as the checklist said."""
        for pad in self.each(variants=("default",)):
            pad.push("RS").wait(100).hold("L1").wait(60)
            self.assertEqual(pad.top, "L1: Modifier 0")
            self.assertTrue(pad.lacks(*RAMP))
        for pad in self.each(variants=("alternative",)):
            pad.push("RS").wait(100).hold("L1").wait(60)                     # L1 is the left trigger's soft pull here
            self.assertTrue(pad.has("Gyro Off Ramp Up"))
            pad.hold("LT full").wait(60)
            self.assertEqual(pad.top, "L1: Modifier 0")

    @scenario("Triggers and ramp-up TR8", either=("A9",))
    def test_the_edge_the_triggers_and_the_modifiers_in_gyro(self):
        for pad in self.each(start=("Base", "Gyro")):
            pad.push("RS").wait(300)
            self.assertTrue(pad.has("Gyro", "Turning Ramp Up 1") and pad.gyro_off())
            pad.hold("LF")
            self.assertFalse(pad.gyro_off())
            pad.let_go("LF").recentre("RS")
            self.assertTrue(pad.lacks(*RAMP) and pad.has("Gyro"))
        for pad in self.each(start=("Base", "Gyro"), variants=("default",)):
            pad.push("RS").wait(300).hold("R1").wait(60)
            self.assertEqual(pad.top, "Gyro | R1: Modifier 1")               # the Gyro version of the modifier

    @scenario("Triggers and ramp-up TR10")
    def test_the_right_pad_blocks_the_edge_only_while_a_thumb_is_on_it(self):
        """Trackball momentum, which the checklist also asked about, is not simulated (A28)."""
        for order in (("R1", RP), (RP, "R1")):
            for pad in self.each():
                pad.hold("R1")
                pad.sim.press(RP)
                for which in order:
                    pad.sim.release(RP) if which == RP else pad.let_go("R1")
                pad.wait(400).push("RS").wait(300)
                self.assertTrue(pad.has("Turning Ramp Up 1"))                # ramp-up works
        for pad in self.each():
            pad.sim.press(RP)
            pad.wait(200).push("RS").wait(300)
            self.assertTrue(pad.lacks(*RAMP))                                # a thumb on the pad still blocks the edge

    @scenario("Triggers and ramp-up TR11", rules=("R120",))
    def test_the_two_bumper_quick_tap_toggles_gyro_and_a_longer_hold_does_not(self):
        for pad in self.each():
            pad.hold("L1", "R1").wait(50).let_go("R1", "L1").wait(300)
            self.assertEqual(pad.stack, pad.layers("Base", "Gyro"))
        for pad in self.each():
            pad.hold("L1", "R1").wait(250).let_go("R1", "L1").wait(300)      # past 200 ms
            self.assertEqual(pad.stack, pad.layers("Base"))
        for pad in self.each():                                              # right after an interrupted attempt
            pad.hold("L1", "R1").wait(100).let_go("R1").hold("R1").wait(250).let_go("R1", "L1").wait(300)
            self.assertFalse([t for t in pad.stack if "Modifier" in t or "Cover" in t])

    @scenario("Default trigger reference match DT2", rests=("A11",))
    def test_soft_and_full_pulls_in_base_gyro_and_the_ramp_stages(self):
        for start in STARTS:
            for pad in self.each(start=start, variants=("default",)):        # the check is about the default layout
                pad.hold("LT").hold("LT full")
                self.assertEqual((pad.down(), pad.typed()), (["mouse_button LEFT"], ["mouse_button LEFT"]))   # one click
                pad.let_go("LT full").let_go("LT")
                self.assertEqual(pad.down(), [])
                pad.push("RS").wait(400).mark().hold("RT")                   # during the ramp stages
                self.assertEqual(pad.typed(), ["mouse_button RIGHT"])
                self.assertFalse(pad.gyro_off())


class RecoveryAndHeldInputs(ScenarioCase):
    @scenario("Left-stick recovery and Transition Sets LR1", rules=("R133", "R134"), rests=("A25",))
    def test_the_left_stick_edge_clears_a_stuck_modifier_or_scroll_layer(self):
        """Its menu and Transition Set parts were replaced in 90.10: a stuck Entry Point clears on the other
        menu button (MB10), and a transition on the next menu tap (90.10 T4)."""
        for start in STARTS:
            for side in ("L1", "R1"):
                for pad in self.each(start=start):
                    pad.hold(side).miss(side).push("LS", "up")
                    self.assertFalse([t for t in pad.stack if "Modifier" in t])
        for pad in self.each():
            pad.hold("L1", "R1").wait(300).miss("L1", "R1").push("LS", "up")     # Modifier 2
            self.assertFalse([t for t in pad.stack if "Modifier" in t])
        for pad in self.each():
            pad.tap("L1").wait(30).hold("L1").wait(50).miss("L1")
            self.assertEqual(pad.top, "L1: Scroll Down")
            pad.push("LS", "up").wait(100)
            self.assertTrue(pad.lacks("L1: Scroll Down"))
        for pad in self.each():                                              # held across a Double Tap window: nothing changes
            pad.tap("L1").wait(20).push("LS", "up").wait(50)
            self.assertEqual(pad.top, "L1: Double Tap")

    @scenario("WASD modifier scaffold WM3")
    def test_which_stacks_leave_bases_left_stick_edge_exposed(self):
        edge = ("joystick", "edge")
        exposed = {"Base": lambda p: p, "ramp stages": lambda p: p.push("RS").wait(300), "stick touch": lambda p: p.touch("LS")}
        displaced = {"a modifier": lambda p: p.hold("L1"), "a Tap Cover": lambda p: p.hold("L1").tap("A"),
                     "an Fn layer": lambda p: p.hold("Start").wait(250), "a window": lambda p: p.tap("L1").wait(20)}
        for start in STARTS:
            for label, setup in exposed.items():
                for pad in self.each(start=start):
                    self.assertEqual(setup(pad).sim.binding(edge)[0], "Base", label)
        for label, setup in displaced.items():
            for pad in self.each():
                self.assertNotEqual(setup(pad).sim.binding(edge)[0], "Base", label)

    @scenario("Missed releases and cleanup scope MR1", rules=("R127", "R131"), rests=("A25",))
    def test_a_cleanup_leaves_gyro_and_the_other_sticks_helpers(self):
        """What each list may hold is the Cleanup audit's job; this checks the survivors on one stack."""
        for pad in self.each(start=("Base", "Gyro")):
            pad.touch("LS").hold("L1").miss("L1").touch("RS")
            self.assertFalse([t for t in pad.stack if "Modifier" in t])
            self.assertTrue(pad.has("Gyro", "LST: Entry Point"))             # the mode and the other stick's helper stay

    @scenario("Held inputs across layer changes HI2", rules=("R114",), either=("A9",))
    def test_the_staggered_gyro_toggle(self):
        """The checklist asked two things. The regular modifier doesn't appear beside the Gyro one. And letting
        go of the bumper then scrolls once: the Gyro modifier came on fresh and wasn't used, so its release
        is a tap."""
        for start, modifier in ((None, "Gyro | L1: Modifier 0"), (("Base", "Gyro"), "L1: Modifier 0")):
            for pad in self.each(start=start):
                pad.hold("L1").tap("R1", ms=60).wait(100)
                self.assertEqual(pad.has("Gyro"), start is None)             # Gyro toggled
                self.assertEqual(pad.top, modifier)                          # the still-held side, in the new mode
                self.assertEqual(len([t for t in pad.stack if "Modifier" in t]), 1)
                pad.mark().let_go("L1").wait(300)
                self.assertEqual(pad.typed(), ["mouse_wheel SCROLL_DOWN"])


if __name__ == "__main__":
    unittest.main()
