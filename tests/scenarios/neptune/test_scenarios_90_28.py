"""Scenarios for 90.28: the chorded menu chain on every press, and the right pad's touch in a window.

The record is findings/2026-10-04-menu-chain-and-window-pads/README.md.

- With one menu button held, every press of the other one goes through the chain: a tap types Enter
  or Backspace, a double tap and hold holds it, and a 200 ms hold enters `Menu Keys`. In 90.25 to
  90.27 only the first press of a hold did (found by the author on the Deck). The Fn layer adds the
  chain's Entry Point on each press, so that layer lands on a button that is already down: its
  Release and its delay still fire there (A7, A6), and its chord is read as it lands (A36).
- Inside `Steering` and `Cursor Gyro` the second button types its key at once, as before: they have
  Fn layers of their own.
- In a Double Tap window the right pad's touch is a Release, as the stick touches are: lifting the
  thumb ends the window and clears the pad's own layers. The clicks stay blocked.
"""
import unittest

from tests.scenario import DIRECTIONS, SOURCES, ScenarioCase, scenario

MENU_KEYS = "Menu Keys"
# first held, pressed, key, the first button's Entry Point and Fn layer, the chain's Entry Point, window, second-press layer, cover
CHAINS = (
    ("Select", "Start", "RETURN", "Menu Left: Entry Point", "Menu Left: Fn Layer", "Menu Left!Right: Entry Point",
     "Menu Left!Right: Double Tap", "Menu Left!Right: Enter", "Menu Left!Right: Double Tap Cover"),
    ("Start", "Select", "BACKSPACE", "Menu Right: Entry Point", "Menu Right: Fn Layer", "Menu Right!Left: Entry Point",
     "Menu Right!Left: Double Tap", "Menu Right!Left: Backspace", "Menu Right!Left: Double Tap Cover"),
)
STARTS = (("Base",), ("Base", "Gyro"))
STATEFUL = (("Base", "Steering"), ("Base", "Gyro", "Cursor Gyro"))


class EveryPress(ScenarioCase):
    @scenario("90.28 M1", rests=("A6", "A7", "A36"))
    def test_every_tap_in_one_hold_types_the_key(self):
        for first, second, key, plain, fn, entry, window, _, _ in CHAINS:
            for pad in self.each():
                pad.hold(first).wait(400)
                self.assertEqual(pad.names()[-2:], ("Base", fn))             # the hold brings the Fn layer alone; since Ibex 1.1 the Fn adder hands over: its Entry Point goes
                for _ in range(3):
                    pad.mark().hold(second)
                    self.assertEqual((pad.top, pad.typed()), (entry, []))    # the Fn layer adds it; nothing is typed at the press
                    pad.wait(60).let_go(second)
                    self.assertEqual(pad.top, window)
                    pad.wait(300)
                    self.assertEqual((pad.typed(), pad.top), ([key], fn))

    @scenario("90.28 M2", rules=("R157",), rests=("A6", "A7", "A16", "A36"))
    def test_a_hold_enters_menu_keys_on_a_later_press_too(self):
        for start in STARTS:
            for first, second, key, _, _, entry, _, _, _ in CHAINS:
                for pad in self.each(start=start):
                    pad.hold(first).wait(400).tap(second, 60).wait(400)      # the first press was a tap
                    pad.mark().hold(second).wait(199)
                    self.assertEqual(pad.top, entry)
                    pad.wait(1)
                    self.assertEqual(pad.stack, pad.layers("Base", MENU_KEYS))
                    self.assertEqual((pad.typed(), pad.seen("beep")), ([], [("beep", MENU_KEYS)]))

    @scenario("90.28 M3", rules=("R120",), rests=("A7", "A10", "A36"))
    def test_a_double_tap_and_hold_holds_the_key_on_a_later_press_too(self):
        for first, second, key, _, fn, _, _, held, cover in CHAINS:
            for pad in self.each():
                pad.hold(first).wait(400).tap(second, 60).wait(400)
                pad.tap(second, 60).wait(60).hold(second).wait(100)
                self.assertEqual((pad.top, pad.down()), (held, [key]))
                pad.wait(200)
                self.assertEqual((pad.top, pad.down()), (cover, [key]))
                pad.let_go(second).wait(300)
                self.assertEqual((pad.top, pad.down()), (fn, []))

    @scenario("90.28 M4", rests=("A5", "A6", "A7", "A36"))
    def test_the_fn_layer_types_nothing_as_it_lands(self):
        """The second button down before the Fn layer is up. The Entry Point's bind adds the Fn layer and
        the chain's Entry Point in one array. The Fn layer's own bind for that button is a layer command
        now, which doesn't fire on a button that is already down (A5); until 90.27 it was the key."""
        for first, second, key, plain, fn, entry, _, _, _ in CHAINS:
            for pad in self.each():
                pad.hold(first).wait(60).mark().hold(second)
                self.assertEqual((pad.names()[-3:], pad.typed()), (("Base", fn, entry), []))   # since Ibex 1.1 the Fn adder hands over: its Entry Point goes
                pad.wait(200)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base", MENU_KEYS), []))
            for pad in self.each():
                pad.hold(first).wait(60).mark().tap(second, 60).wait(300)
                self.assertEqual(pad.typed(), [key])                        # once, from the window

    @scenario("90.28 M5", rests=("A7", "A36"))
    def test_a_thumb_lift_brings_the_fn_layer_and_the_chain_still_runs(self):
        for first, second, key, plain, fn, entry, _, _, _ in CHAINS:
            for pad in self.each():
                pad.touch("RS").wait(300).hold(first).wait(60).lift("RS").wait(60)
                self.assertEqual(pad.names()[-2:], ("Base", fn))             # since Ibex 1.1 the Fn adder hands over: its Entry Point goes
                pad.mark().tap(second, 60).wait(300)
                self.assertEqual(pad.typed(), [key])
                pad.hold(second).wait(200)
                self.assertEqual(pad.stack, pad.layers("Base", MENU_KEYS))

    @scenario("90.28 M6", rules=("R157",), rests=("A10",))
    def test_in_steering_and_cursor_gyro_the_second_button_types_at_once(self):
        for start in STATEFUL:
            for first, second, key, _, _, _, _, _, _ in CHAINS:
                for pad in self.each(start=start):
                    home = pad.stack
                    pad.hold(first).wait(400)
                    self.assertEqual(pad.top, f"Stateful | Menu {'Left' if first == 'Select' else 'Right'}: Fn Layer")
                    pad.mark().hold(second)
                    self.assertEqual(pad.down(), [key])                      # at the press, and held
                    pad.wait(600)
                    self.assertEqual((pad.down(), pad.lacks(MENU_KEYS)), ([key], True))
                    pad.let_go(second).let_go(first).wait(400)
                    self.assertEqual(pad.stack, home)


class WindowPads(ScenarioCase):
    @scenario("90.28 W1", rules=("R149", "R172"), rests=("A7",))
    def test_a_pad_thumb_that_lifts_inside_a_window_ends_it_and_clears_the_pads_layers(self):
        for button, window in (("L1", "L1: Double Tap"), ("R1", "R1: Double Tap"),
                               ("Select", "Menu Left: Double Tap"), ("Start", "Menu Right: Double Tap")):
            for pad in self.each():
                pad.touch("RP").wait(300)
                self.assertEqual(pad.names()[-2:], ("RTP: Entry Point", "RTP: Tap Cover"))
                pad.tap(button, 60).wait(40)
                self.assertEqual(pad.top, window)
                pad.mark().lift("RP")
                self.assertEqual(pad.stack, pad.layers("Base"))              # until 90.27 the two pad layers were left on
                pad.wait(400)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))

    @scenario("90.28 W2", rules=("R172",), rests=("A7",))
    def test_it_ends_a_circular_scroll_too(self):
        touch, north = (SOURCES["RP"], "touch"), (SOURCES["RP"], DIRECTIONS["up"])
        for pad in self.each():
            pad.sim.press(touch).release(touch)
            pad.wait(50)
            pad.sim.press(touch).press(north).release(north)
            pad.wait(200)
            self.assertEqual(pad.top, "RTP: Circular Scroll")
            pad.tap("L1", 60).wait(40).lift("RP")
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.28 W3", rules=("R149",), either=("A9",))
    def test_a_touch_and_a_click_that_start_inside_a_window_do_nothing_until_it_ends(self):
        for pad in self.each():
            pad.tap("L1", 60).wait(30).mark().touch("RP")
            pad.sim.press((SOURCES["RP"], "click"))
            pad.wait(60)
            self.assertEqual((pad.top, pad.typed()[1:]), ("L1: Double Tap", []))     # only the tap's own scroll
            pad.sim.release((SOURCES["RP"], "click"))
            pad.wait(500)
            self.assertEqual(pad.names()[-1], "RTP: Tap Cover")              # the Entry Point came when the window went
            pad.lift("RP").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.28 W4", rules=("R149", "R172"), rests=("A10",))
    def test_a_swipe_inside_a_window_types_its_key_with_no_layer(self):
        for direction, key in (("left", "ESCAPE"), ("right", "RETURN"), ("up", "TAB"), ("down", "BACKSPACE")):
            for pad in self.each():
                pad.tap("L1", 60).wait(60).mark().touch("LP")
                pad.sim.press((SOURCES["LP"], DIRECTIONS[direction]))
                self.assertEqual((pad.top, pad.typed()), ("L1: Double Tap", [key]))
                pad.sim.release((SOURCES["LP"], DIRECTIONS[direction]))
                pad.lift("LP").wait(400)
                self.assertEqual(pad.stack, pad.layers("Base"))


if __name__ == "__main__":
    unittest.main()
