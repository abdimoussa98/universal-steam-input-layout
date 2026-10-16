"""Scenarios for 90.30: the pad window's Releases, the fallback's edge, and the Tap Cover resets off.

The plan is plans/2026-10-04-window-releases-and-tap-cover-resets.md; the record is
findings/2026-10-04-window-releases-and-tap-cover-resets/README.md.

- `RTP: Double Tap`, the 150 ms after a short touch of the right pad, covered the Release of a menu
  or modifier button that was already down. Its layers stayed on, and the next press was in the Fn
  layer at once (found by the author on the Deck). Each of the four buttons now has a Release there
  that removes the window and then the layers its pair can be holding (A7).
- The fallback hold left by its up and down Releases and its exit, and no longer by the outer edge's
  Release. 90.33 deleted the Fallback Hold; its two scenarios here, F1 and F2, are retired
  (test_scenarios_90_33.py has the fallback's).
- The three Entry Points have no Tap Cover reset, so a touch of the right pad no longer postpones a
  hold that is still counting.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

WINDOW = "RTP: Double Tap"
# button, what a 400 ms hold puts on, the key a tap types afterwards
MENU = (("Select", ("Menu Left: Entry Point", "Menu Left: Fn Layer"), "ESCAPE"),
        ("Start", ("Menu Right: Entry Point", "Menu Right: Fn Layer"), "TAB"))
MODIFIERS = (("L1", ("L1: Modifier 0", "L1: Temp Cursor Gyro")), ("R1", ("R1: Modifier 1", "R1: Temp Cursor Gyro")))
STARTS = (("Base",), ("Base", "Gyro"))


def tap_pad(pad, ms=60):
    """A short touch of the right pad: it ends in the pad's Double Tap window."""
    return pad.touch("RP").wait(ms).lift("RP")


class PadWindow(ScenarioCase):
    # On the 90.71 build: since 90.72 the menu layers bind the right pad's touch, so its tap chain (RTP: Entry Point,
    # the Double Tap window, Circular Scroll) no longer opens during a menu hold (90.72 E8).
    @scenario("90.30 W1", rules=("R136",), rests=("A7",), frozen="90.71")
    def test_a_menu_button_let_go_inside_the_pads_window_leaves_nothing_on(self):
        for button, held, key in MENU:
            for pad in self.each():
                pad.hold(button).wait(400)
                self.assertEqual(pad.names()[-2:], held)
                tap_pad(pad).wait(50)
                self.assertEqual(pad.top, WINDOW)
                pad.mark().let_go(button)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))     # until 90.29 both layers stayed on
                pad.wait(600)
                # The next press is an ordinary one: a tap types the key, a hold brings the Fn layer at 200 ms.
                pad.mark().tap(button, 60).wait(400)
                self.assertEqual((pad.typed(), pad.stack), ([key], pad.layers("Base")))
                pad.hold(button).wait(199)
                self.assertEqual(pad.top, held[0])
                pad.wait(2)
                self.assertEqual(pad.names()[-2:], held)

    @scenario("90.30 W2", rules=("R136",), rests=("A7",))
    def test_a_modifier_let_go_inside_the_pads_window_leaves_nothing_on(self):
        for start in STARTS:
            for button, _ in MODIFIERS:
                for pad in self.each(start=start):
                    pad.hold(button).wait(400)
                    tap_pad(pad).wait(50)
                    self.assertEqual(pad.top, WINDOW)
                    pad.let_go(button).wait(600)
                    self.assertEqual(pad.stack, pad.layers(*start))

    @scenario("90.30 W3", rules=("R136",), rests=("A7",), either=("A9",))
    def test_with_both_modifiers_held_the_one_still_down_gets_its_modifier_back(self):
        for first, second, back in (("L1", "R1", "R1: Modifier 1"), ("R1", "L1", "L1: Modifier 0")):
            for pad in self.each():
                pad.hold(first).wait(300).hold(second).wait(150)
                tap_pad(pad).wait(50)
                pad.let_go(first)                          # inside the window: both modifiers' layers go
                self.assertTrue(pad.lacks(WINDOW))
                pad.wait(60)                               # Base's add for the one still held repeats every 50 ms
                self.assertTrue(pad.has(back))
                pad.let_go(second).wait(600)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.30 W4", rules=("R136",), rests=("A7",))
    def test_the_same_through_several_pad_taps_in_one_hold(self):
        for button, held, _ in MENU:
            for pad in self.each():
                pad.hold(button).wait(400)
                for _ in range(3):
                    tap_pad(pad).wait(300)                 # each window runs out on its own
                    self.assertEqual(pad.names()[-2:], held)
                tap_pad(pad).wait(100)
                pad.let_go(button).wait(600)
                self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.30 W5", rests=("A7",))
    def test_a_press_that_starts_and_ends_inside_the_window_ends_it_and_does_nothing_else(self):
        for button in ("Select", "Start", "L1", "R1"):
            for pad in self.each():
                tap_pad(pad).wait(30)
                self.assertEqual(pad.top, WINDOW)
                pad.mark().tap(button, 40)
                self.assertEqual(pad.stack, pad.layers("Base"))             # the window is gone, early
                pad.wait(600)
                self.assertEqual(pad.stack, pad.layers("Base"))
                self.assertEqual([k for k in pad.typed() if "SCROLL" not in k], [])      # a modifier's press still scrolls

    # On the 90.71 build: since 90.72 the menu layers bind the right pad's touch, so its tap chain (RTP: Entry Point,
    # the Double Tap window, Circular Scroll) no longer opens during a menu hold (90.72 E8).
    @scenario("90.30 W6", rules=("R157",), rests=("A7",), frozen="90.71")
    def test_in_cursor_gyro_the_stateful_menu_layers_go_too(self):
        start = ("Base", "Gyro", "Cursor Gyro")
        for button in ("Select", "Start"):
            for pad in self.each(start=start):
                pad.hold(button).wait(400)
                tap_pad(pad).wait(50)
                self.assertEqual(pad.top, WINDOW)
                pad.let_go(button).wait(600)
                self.assertEqual(pad.stack, pad.layers(*start))


class NoCoverResets(ScenarioCase):
    @scenario("90.30 T1", rests=("A13", "A16"))
    def test_a_pad_touch_no_longer_postpones_a_hold(self):
        holds = (("L1", "L1: Temp Cursor Gyro"), ("Select", "Menu Left: Fn Layer"))
        for button, lands in holds:
            for first in ("hold", "touch"):
                for gap in (10, 60, 120, 190):
                    for pad in self.each():
                        if first == "hold":
                            pad.hold(button).wait(gap).touch("RP").wait(199 - gap)
                        else:
                            pad.touch("RP").wait(gap).hold(button).wait(199)
                        self.assertTrue(pad.lacks(lands))
                        pad.wait(2)
                        self.assertTrue(pad.has(lands), (button, first, gap))     # 200 ms after the press, every time

    @scenario("90.30 T2", rests=("A16",))
    def test_the_tap_covers_still_come_at_150_ms_and_a_short_touch_still_opens_the_window(self):
        for stick, prefix in (("LS", "LST"), ("RS", "RST"), ("RP", "RTP")):
            for pad in self.each():
                pad.touch(stick).wait(149)
                self.assertEqual(pad.top, f"{prefix}: Entry Point")
                pad.wait(2)
                self.assertEqual(pad.top, f"{prefix}: Tap Cover")
                pad.lift(stick).wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))
                pad.touch(stick).wait(60).lift(stick)
                self.assertEqual(pad.top, f"{prefix}: Double Tap")
                pad.wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))


if __name__ == "__main__":
    unittest.main()
