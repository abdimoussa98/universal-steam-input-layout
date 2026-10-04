"""Scenarios for the older Deck checks on the menu buttons and the modifier layers.

These sections of the checklist had no release number: they predate 90.6 and were never run.
"Holding for 300 ms" in them is 200 ms since 90.10.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

MENUS = (("Select", "ESCAPE", "Menu Left"), ("Start", "TAB", "Menu Right"))


class MenuButtons(ScenarioCase):
    @scenario("Menu buttons MB1")
    def test_a_tap_types_escape_or_tab(self):
        for button, key, _ in MENUS:
            for pad in self.each():
                pad.tap(button).wait(300)
                self.assertEqual((pad.typed(), pad.stack), ([key], pad.layers("Base")))

    @scenario("Menu buttons MB2", rules=("R120",))
    def test_holding_brings_up_the_fn_layer_and_the_release_is_silent(self):
        for button, key, menu in MENUS:
            for pad in self.each():
                pad.hold(button).wait(250)
                self.assertEqual(pad.top, f"{menu}: Fn Layer")
                pad.mark().tap("A").tap("B")
                self.assertTrue(all(k.startswith("F") and k[1:].isdigit() for k in pad.typed()), pad.typed())   # F-keys
                pad.mark().let_go(button).wait(300)
                self.assertEqual((pad.typed(), pad.stack), ([], pad.layers("Base")))    # nothing is sent
                pad.tap("A").tap(button).wait(300)
                self.assertEqual(pad.typed(), ["F", key])       # face buttons back to normal; the next tap still types

    @scenario("Menu buttons MB4", rules=("R138",), rests=("A10",))
    def test_enter_and_backspace_quickly_and_with_fn_up(self):
        for first, second, key in (("Select", "Start", "RETURN"), ("Start", "Select", "BACKSPACE")):
            for hold in (50, 250):                                           # before Fn is up, and with it up
                for pad in self.each():
                    pad.hold(first).wait(hold).tap(second).wait(30).tap(second)
                    self.assertEqual(pad.typed(), [key, key])                # pressing it again sends it again
                    pad.hold(second).wait(500)
                    self.assertEqual(pad.down(), [key])                      # held: it repeats
                    pad.mark().let_go(second).let_go(first).wait(300)
                    self.assertEqual(pad.typed(), [])                        # the second released first: nothing extra

    @scenario("Menu buttons MB5", rules=("R124",), rests=("A10",))
    def test_double_tap_and_hold_holds_the_key(self):
        for button, key, _ in MENUS:
            for pad in self.each():
                pad.tap(button).wait(30).mark().hold(button).wait(400)
                self.assertEqual(pad.down(), [key])
                pad.mark().let_go(button).wait(300)
                self.assertEqual((pad.down(), pad.typed()), ([], []))        # releasing stops it

    @scenario("Menu buttons MB6", rules=("R157",))
    def test_the_stick_click_enters_a_transition_and_the_fn_directions_type_punctuation(self):
        keys = {"LS": ["BACKSLASH", "FORWARD_SLASH", "LEFT_BRACKET", "RIGHT_BRACKET"],
                "RS": ["SEMICOLON", "SINGLE_QUOTE", "COMMA", "PERIOD"]}
        for pad in self.each():
            pad.hold("Select").click("LS")
            self.assertEqual(pad.top, "Transition Set 0")                    # since 90.22 the one that enters Gamepad
        for stick, source in (("LS", "joystick"), ("RS", "right_joystick")):
            for pad in self.each():
                pad.hold("Select").wait(250).touch(stick).mark()
                for direction in ("dpad_north", "dpad_south", "dpad_west", "dpad_east"):
                    pad.sim.press((source, direction)).release((source, direction))
                self.assertEqual(pad.typed(), keys[stick])

    @scenario("Menu buttons MB8", rules=("R123",))
    def test_a_thumb_lift_completes_the_fn_hold(self):
        for button, key, menu in MENUS:
            for stick in ("LS", "RS"):
                for pad in self.each():
                    pad.hold(button).wait(50).touch(stick).wait(20).lift(stick)
                    self.assertEqual(pad.top, f"{menu}: Fn Layer")           # Fn comes up on the lift
                    pad.let_go(button).wait(300)
                    self.assertEqual(pad.typed(), [])                        # and no Tab or Escape is sent

    @scenario("Menu buttons MB9", rules=("R133",), rests=("A25",))
    def test_a_stuck_fn_layer_clears_on_the_next_input(self):
        for button, key, menu in MENUS:
            for clear in (lambda p: p.push("RS"), lambda p: p.hold("A")):
                for pad in self.each():
                    pad.hold(button).wait(250).miss(button)
                    self.assertEqual(pad.top, f"{menu}: Fn Layer")
                    clear(pad)
                    self.assertFalse([t for t in pad.stack if "Menu" in t])
            for pad in self.each():
                pad.hold(button).wait(250).miss(button).hold("A").let_go("A").wait(300).mark().tap(button).wait(300)
                self.assertEqual(pad.typed(), [key])                         # the menu buttons work normally again

    @scenario("Menu buttons MB10", rules=("R133", "R169"), rests=("A25",))
    def test_a_stuck_entry_point_clears_on_the_other_menu_button(self):
        for pad in self.each():
            pad.hold("Start").wait(50).miss("Start")
            self.assertEqual(pad.top, "Menu Right: Entry Point")
            pad.mark().tap("Select").wait(300)
            self.assertFalse([t for t in pad.stack if "Menu" in t])
            pad.mark().tap("Select").wait(300)
            self.assertEqual(pad.typed(), ["ESCAPE"])                        # and then works normally
        for pad in self.each():                                              # since 90.24 a stick touch clears it too (R169);
            pad.hold("Start").wait(50).miss("Start").touch("RS")             # until 90.23 only the other menu button did
            self.assertFalse([t for t in pad.stack if "Menu" in t])


class ModifierLayers(ScenarioCase):
    @scenario("Modifier layers ML1")
    def test_nav_keys(self):
        self.nav(None)

    @scenario("Modifier layers ML2")
    def test_nav_keys_in_gyro(self):
        self.nav(("Base", "Gyro"))

    def nav(self, start):
        for held, keys in ((("L1",), ["INSERT", "DELETE"]), (("R1",), ["HOME", "END"]),
                           (("L1", "R1"), ["PAGE_UP", "PAGE_DOWN"]), (("R1", "L1"), ["PAGE_UP", "PAGE_DOWN"])):
            for pad in self.each(start=start):
                pad.hold(*held).mark().tap("Start").tap("Select")
                self.assertEqual(pad.typed(), keys)

    @scenario("Modifier layers ML3")
    def test_a_menu_button_in_a_modifier_leaves_the_gyro_alone(self):
        """The checklist added: confirm that's what you want. That question stays with the author."""
        for start in (None, ("Base", "Gyro")):
            for held in (("L1",), ("R1",), ("L1", "R1")):
                for pad in self.each(start=start):
                    pad.hold(*held)
                    before = (pad.gyro_off(), pad.has("Gyro"))
                    pad.hold("Start").wait(400)
                    self.assertEqual((pad.gyro_off(), pad.has("Gyro")), before)
                    pad.let_go("Start").hold("Select").wait(400)
                    self.assertEqual((pad.gyro_off(), pad.has("Gyro")), before)

    @scenario("Modifier layers ML4", rules=("R124", "R133"), rests=("A25",))
    def test_no_tap_action_after_a_nav_chord_and_a_menu_button_alone_clears_a_stuck_modifier(self):
        for pad in self.each():
            pad.hold("L1").tap("Start").mark().let_go("L1").wait(300)
            self.assertEqual((pad.typed(), pad.stack), ([], pad.layers("Base")))    # no scroll
        for button in ("Start", "Select"):
            for pad in self.each():
                pad.hold("L1").miss("L1").tap(button).wait(300)
                self.assertFalse([t for t in pad.stack if "Modifier" in t])


if __name__ == "__main__":
    unittest.main()
