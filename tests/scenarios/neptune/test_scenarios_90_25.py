"""Scenarios for 90.25: the pad touch bumps, the middle-click mouse, Menu Keys and the Tap Cover resets.

The record is findings/2026-10-04-pad-bumps-and-menu-keys/README.md; the plan is
plans/2026-10-04-pad-bumps-and-menu-layer.md.

- The pad touch bump of 90.25 and 90.26 is gone since 90.27 (findings/2026-10-04-pad-touch-bump/README.md);
  its scenarios, P1, P2, P4 and P6, went with it. The ones kept here read the pads as they are now.
- `RTP: Middle Click` is a mouse pad. The simulator has no cursor; the static tests check the mode.
- With one menu button held, the other goes through the Menu chain's recipe: a tap types Enter or
  Backspace, a double tap and hold holds it, and a 200 ms hold enters `Menu Keys` (150 ms in 90.25).
  Until 90.27 only the first press of a hold did; 90.28 made it every press, and M4, which pinned the
  old behaviour, went (tests/scenarios/neptune/test_scenarios_90_28.py).
- The stick and pad Entry Points' delayed Tap Cover has a reset, which a normal touch never fires.
"""
import unittest

from tests.scenario import DIRECTIONS, SOURCES, ScenarioCase, scenario

MENU_KEYS = "Menu Keys"
# first held, pressed, key, the chain's Entry Point, window, second-press layer and cover, the first button's Entry Point and Fn layer
CHAINS = (
    ("Select", "Start", "RETURN", "Menu Left!Right: Entry Point", "Menu Left!Right: Double Tap", "Menu Left!Right: Enter",
     "Menu Left!Right: Double Tap Cover", "Menu Left: Entry Point", "Menu Left: Fn Layer"),
    ("Start", "Select", "BACKSPACE", "Menu Right!Left: Entry Point", "Menu Right!Left: Double Tap",
     "Menu Right!Left: Backspace", "Menu Right!Left: Double Tap Cover", "Menu Right: Entry Point", "Menu Right: Fn Layer"),
)
STATEFUL_STARTS = (("Base", "Steering"), ("Base", "Gyro", "Cursor Gyro"))


def bumps(pad):
    """The haptics since the mark, as (strength, layer)."""
    return [tuple(detail.split(" ", 1)[0:1]) + (detail.split(" ", 1)[1].rsplit(" ", 1)[0],) for _, detail in pad.seen("haptic")]


def swipe(pad, direction):
    """Swipe on the left pad: its swipe input goes down. The thumb is already on the pad."""
    pad.sim.press((SOURCES["LP"], DIRECTIONS[direction]))
    return pad


class PadTouch(ScenarioCase):
    @scenario("90.25 P3")
    def test_a_click_after_the_thumb_has_rested_still_works(self):
        for name, key in (("RP", "mouse_button MIDDLE"), ("LP", "CAPSLOCK")):
            for pad in self.each():
                pad.touch(name).wait(400).mark()
                pad.sim.press((SOURCES[name], "click"))
                pad.wait(120)
                self.assertEqual((pad.typed(), pad.down()), ([key], [key]))
                pad.sim.release((SOURCES[name], "click"))
                pad.lift(name).wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.25 P8", rests=("A6", "A40"))
    def test_a_click_that_lands_with_the_touch_is_read_all_the_same(self):
        """The thumb and the click at the same moment. The Click Entry Point lands on a pad that is already
        pressed, and its centre bind repeats, so it fires as the layer lands (A6): the middle click is down at
        once. At the rim the outer bind's 5 ms delay is all that is left."""
        for pad in self.each():
            pad.press_pad("RP", "centre", rest=False)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))
            pad.let_go_pad("RP").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))
        for pad in self.each():
            pad.press_pad("RP", "left", rest=False).wait(4)
            self.assertEqual(pad.down(), [])
            pad.wait(1)
            self.assertEqual((pad.top, pad.down()), ("RTP: Mouse Buttons", ["mouse_button BACK"]))
        for pad in self.each():                                              # a rim click shorter than that sends nothing
            pad.click_pad("RP", "left", ms=4, rest=False).wait(400)
            self.assertEqual((pad.typed(), pad.stack), ([], pad.layers("Base")))

    @scenario("90.25 P5", rests=("A10",))
    def test_a_left_pad_swipe_types_its_key(self):
        """From Base again since 90.27; from 90.25 to 90.26 the swipes were in `LTP: Entry Point`."""
        swipes = {"left": ("ESCAPE", "Escape"), "right": ("RETURN", "Enter"), "up": ("TAB", "Tab"), "down": ("BACKSPACE", "Backspace")}
        for direction, (key, layer) in swipes.items():
            for pad in self.each():
                pad.touch("LP").wait(60).mark()
                swipe(pad, direction).wait(30)
                self.assertEqual((pad.typed(), pad.stack), ([key], pad.layers("Base", layer)))
                pad.sim.release((SOURCES["LP"], DIRECTIONS[direction]))
                pad.lift("LP").wait(300)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.25 P7", rests=("A10",), frozen="90.49")
    def test_a_pad_click_still_works_in_steering(self):
        for pad in self.each(start="steering"):
            pad.mark().click_pad("RP", "centre")
            self.assertEqual(pad.typed(), ["mouse_button MIDDLE"])
            self.assertEqual(bumps(pad)[0], ("1", "Base"))                   # the click's own pulse, from Base again (90.27)
            pad.wait(300)
            self.assertEqual(pad.top, "Steering")


class TapCoverResets(ScenarioCase):
    @scenario("90.25 T1", rules=("R120",), rests=("A16",))
    def test_a_normal_touch_never_fires_the_reset(self):
        for name, prefix in (("LS", "LST"), ("RS", "RST"), ("RP", "RTP")):
            for pad in self.each():
                pad.touch(name).wait(149)
                self.assertTrue(pad.lacks(f"{prefix}: Tap Cover"))
                pad.wait(2)
                self.assertEqual(pad.top, f"{prefix}: Tap Cover")
                pad.wait(2000)
                self.assertEqual(pad.seen("remove"), [])
                pad.lift(name).wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.25 T2", rules=("R120",), rests=("A7",))
    def test_a_tap_still_opens_the_double_tap_window(self):
        for name, prefix in (("LS", "LST"), ("RS", "RST"), ("RP", "RTP")):
            for pad in self.each():
                pad.touch(name).wait(60).lift(name)
                self.assertEqual(pad.top, f"{prefix}: Double Tap")
                pad.wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))


class ChordedMenu(ScenarioCase):
    @scenario("90.25 M1", rules=("R120",), rests=("A16",))
    def test_a_chorded_tap_types_the_key_once(self):
        for first, second, key, entry, window, _, _, plain, fn in CHAINS:
            for pad in self.each():
                pad.hold(first).wait(40).hold(second)
                self.assertEqual(pad.names()[-3:], (plain, fn, entry))
                pad.wait(60).let_go(second)
                self.assertEqual((pad.top, pad.typed()), (window, []))
                pad.wait(60)
                self.assertEqual((pad.typed(), pad.down()), ([key], [key]))  # the window types it, 50 ms in
                pad.wait(200)
                self.assertEqual((pad.names()[-2:], pad.down()), ((plain, fn), []))   # back on the Fn layer
                pad.let_go(first).wait(300)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), [key]))

    @scenario("90.25 M2", rules=("R157", "R162"), rests=("A16",))
    def test_holding_both_menu_buttons_enters_menu_keys(self):
        for start in (("Base",), ("Base", "Gyro")):
            for first, second, _, entry, _, _, _, plain, _ in CHAINS:
                for pad in self.each(start=start):
                    pad.touch("LS").touch("RS").wait(300)                    # resting thumbs: their helpers are cleared too
                    pad.hold(first).wait(40).mark().hold(second).wait(199)
                    self.assertEqual(pad.top, entry)
                    pad.wait(2)
                    self.assertEqual(pad.stack, pad.layers("Base", MENU_KEYS))            # Gyro is gone
                    self.assertEqual((pad.seen("beep"), bumps(pad)),
                                     ([("beep", MENU_KEYS)], [("1", plain), ("1", entry)]))
                    pad.let_go(second).let_go(first).wait(500)
                    self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base", MENU_KEYS), []))

    @scenario("90.25 M3", rules=("R120",), rests=("A10",))
    def test_a_double_tap_and_hold_holds_the_key_and_a_third_press_chains(self):
        for first, second, key, _, window, held, cover, plain, fn in CHAINS:
            for pad in self.each():
                pad.hold(first).wait(40).tap(second).wait(70).mark().hold(second).wait(100)
                self.assertEqual((pad.top, pad.down()), (held, [key]))
                pad.wait(200)
                self.assertEqual((pad.top, pad.down()), (cover, [key]))      # held past 150 ms
                pad.mark().let_go(second).wait(300)
                self.assertEqual((pad.typed(), pad.names()[-2:]), ([], (plain, fn)))      # a clean end, no window
            for pad in self.each():
                pad.hold(first).wait(40).tap(second).wait(70).tap(second, 60)
                self.assertEqual(pad.top, window)                            # a short second press reopens the window
                pad.wait(30).hold(second).wait(300)
                self.assertEqual((pad.top, pad.down()), (cover, [key]))      # the third press holds the key
                pad.let_go(second).let_go(first).wait(300)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.25 M5", rests=("A16",))
    def test_the_hold_also_works_once_the_fn_layer_is_up(self):
        for first, second, _, entry, _, _, _, plain, fn in CHAINS:
            for pad in self.each():
                pad.hold(first).wait(250)
                self.assertEqual(pad.names()[-2:], (plain, fn))              # the hold brings the Fn layer alone (90.28)
                pad.hold(second).wait(210)
                self.assertEqual(pad.stack, pad.layers("Base", MENU_KEYS))

    @scenario("90.25 M6", rests=("A7",))
    def test_letting_go_of_the_first_button_ends_its_family(self):
        for first, second, key, _, window, held, _, _, _ in CHAINS:
            for pad in self.each():                                          # inside the window
                pad.hold(first).wait(40).tap(second).wait(20).let_go(first).wait(300)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))
            for pad in self.each():                                          # under the held key: the key stays
                pad.hold(first).wait(40).tap(second).wait(70).hold(second).wait(60).let_go(first)
                self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", held), [key]))
                pad.let_go(second).wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.25 M7", rules=("R157",), rests=("A10",))
    def test_inside_a_stateful_layer_both_menu_buttons_type_the_key_as_before(self):
        for start in STATEFUL_STARTS:
            for first, second, key, _, _, _, _, _, _ in CHAINS:
                for pad in self.each(start=start):
                    home = pad.stack
                    pad.hold(first).wait(40).hold(second)
                    self.assertEqual(pad.down(), [key])                      # at once
                    pad.wait(400)
                    self.assertTrue(pad.lacks(MENU_KEYS))
                    pad.let_go(second).let_go(first).wait(300)
                    self.assertEqual(pad.stack, home)

    @scenario("90.25 M8", rules=("R169",), rests=("A25",))
    def test_a_missed_release_of_the_second_button_is_cleaned_up(self):
        for first, second, _, _, _, held, _, _, _ in CHAINS:
            for stick in ("LS", "RS"):
                for pad in self.each():
                    pad.hold(first).wait(40).tap(second).wait(70).hold(second).wait(60).miss(second).let_go(first).wait(400)
                    self.assertEqual(pad.stack, pad.layers("Base", held))
                    pad.touch(stick)
                    self.assertTrue(pad.lacks(held))


class MenuKeys(ScenarioCase):
    START = ("Base", MENU_KEYS)

    @scenario("90.25 K1")
    def test_the_dpad_is_the_arrows_and_the_face_buttons_are_the_four_keys(self):
        keys = {"Up": "UP_ARROW", "Down": "DOWN_ARROW", "Left": "LEFT_ARROW", "Right": "RIGHT_ARROW",
                "A": "RETURN", "B": "ESCAPE", "X": "BACKSPACE", "Y": "TAB"}
        for pad in self.each(start=self.START):
            for button, key in keys.items():
                pad.mark().tap(button)
                self.assertEqual((pad.typed(), pad.stack), ([key], pad.layers(*self.START)), button)

    @scenario("90.25 K2", rules=("R159", "R162"))
    def test_the_modifiers_the_menu_buttons_and_the_stick_touches_do_nothing(self):
        for pad in self.each(start=self.START):
            pad.tap("L1").wait(300).tap("R1").wait(300).hold("L1").hold("R1").wait(400).let_go("L1").let_go("R1")
            pad.tap("Select").wait(300).tap("Start").wait(300).hold("Select").hold("Start").wait(400).let_go("Select").let_go("Start")
            pad.touch("LS").touch("RS").wait(300).lift("LS").wait(50).touch("LS").lift("RS").lift("LS").wait(400)
            self.assertEqual((pad.stack, pad.typed(), pad.seen("add")), (pad.layers(*self.START), [], []))

    @scenario("90.25 K3")
    def test_the_other_inputs_do_what_they_do_on_base(self):
        for pad in self.each(start=self.START):
            pad.push("LS", "up").wait(50).recentre("LS").lift("LS").tap("L4").click("LS")
            self.assertEqual((pad.typed(), pad.stack), (["W", "LEFT_SHIFT", "Q"], pad.layers(*self.START)))
            pad.mark().click_pad("RP", "centre")
            self.assertEqual(pad.typed(), ["mouse_button MIDDLE"])
            pad.wait(400)
            self.assertEqual(pad.stack, pad.layers(*self.START))

    @scenario("90.25 K4", rules=("R135", "R157"), either=("A9",))
    def test_both_sticks_out_leaves(self):
        for first, second in (("LS", "RS"), ("RS", "LS")):
            for pad in self.each(start=self.START):
                pad.push(first, "up" if first == "LS" else None).wait(50)
                self.assertTrue(pad.has(MENU_KEYS))
                pad.mark().push(second, "up" if second == "LS" else None)
                self.assertTrue(pad.lacks(MENU_KEYS))
                self.assertEqual(pad.seen("beep"), [("beep", MENU_KEYS)])

    @scenario("90.25 K5", rules=("R157",), rests=("A11", "A27"))
    def test_a_stick_out_plus_a_button_leaves_and_the_press_counts_as_bases(self):
        for stick in ("LS", "RS"):
            for button, base_key in (("A", "F"), ("Down", "3")):
                for pad in self.each(start=self.START):
                    pad.push(stick, "left" if stick == "LS" else None).wait(50).mark().hold(button)
                    self.assertTrue(pad.lacks(MENU_KEYS))
                    self.assertEqual(pad.seen("beep"), [("beep", MENU_KEYS)])
                    self.assertEqual(pad.typed(), [base_key])                # not Enter or the arrow: Base's key (A11)

    @scenario("90.25 K6", rules=("R158", "R161", "R163"), rests=("A27",))
    def test_a_menu_button_plus_a_stick_click_clears(self):
        for menu in ("Start", "Select"):
            for stick, key in (("LS", "Q"), ("RS", "E")):
                for pad in self.each(start=self.START):
                    pad.hold(menu).wait(50).mark().click(stick)
                    self.assertEqual((pad.top, pad.typed()), ("Transition Set 2", []))    # the chord, not the stick's key
                    pad.mark().let_go(menu)
                    self.assertTrue(pad.lacks(MENU_KEYS, "Transition Set 2"))
                    self.assertEqual((pad.seen("beep"), bumps(pad)), ([("beep", "Transition Set 2")], [("1", "Transition Set 2")]))
                    pad.mark().lift(stick).wait(300).click(stick)
                    self.assertEqual(pad.typed(), [key])                     # Base again

    @scenario("90.25 K7", rules=("R140",), rests=("A7",))
    def test_a_pad_tap_opens_its_window_over_menu_keys_and_the_face_buttons_wait(self):
        for pad in self.each(start=self.START):
            pad.touch("RP").wait(60).lift("RP")
            self.assertEqual(pad.stack, pad.layers(*self.START, "RTP: Double Tap"))
            pad.mark().tap("A")
            self.assertEqual(pad.typed(), [])                                # cleared for the window's 150 ms
            pad.wait(300).tap("A")
            self.assertEqual((pad.typed(), pad.stack), (["RETURN"], pad.layers(*self.START)))


if __name__ == "__main__":
    unittest.main()
