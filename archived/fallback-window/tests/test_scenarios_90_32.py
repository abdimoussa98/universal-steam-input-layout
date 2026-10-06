"""Scenarios for 90.32: in the fallback's window the drivers and the menu buttons take replacements.

The record is findings/2026-10-04-fallback-window-replacements/README.md. All of it is in Steering
with no driver held and the left stick up or down.

- Inside the window's second a driver scrolls and Start and Select type Tab and Escape. No layer
  changes, and the second runs on (the author, 2026-10-04). In 90.31 they left Steering there.
- After the second the Fallback Hold answers them and they leave Steering, as in 90.31.
- A button pressed inside the second and still held when it ends is answered by the Fallback Hold
  at that moment: its bind repeats.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

WINDOW, HOLD = "Steering | LS: Fallback Window", "Steering | LS: Fallback Hold"
TAPS = (("Start", "TAB"), ("Select", "ESCAPE"), ("R1", "mouse_wheel SCROLL_UP"), ("L1", "mouse_wheel SCROLL_DOWN"))


class Replacements(ScenarioCase):
    @scenario("90.32 R1", rules=("R137", "R140"), rests=("A16",))
    def test_a_tap_inside_the_second_sends_its_replacement_and_the_second_runs_on(self):
        for button, output in TAPS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(400).mark().tap(button, 60)
                self.assertEqual(pad.typed(), [output])
                self.assertEqual((pad.top, pad.down()), (WINDOW, ["W"]))    # in 90.31 this left Steering
                pad.wait(539)
                self.assertEqual(pad.top, WINDOW)                            # 999 ms after the push: the tap restarted nothing
                pad.wait(2)
                self.assertEqual(pad.top, HOLD)
                pad.recentre("LS")
                self.assertTrue(pad.lacks("Steering"))

    @scenario("90.32 R2", rules=("R137",), rests=("A8",))
    def test_several_taps_and_then_letting_go_inside_the_second_keeps_steering(self):
        for pad in self.each(start="steering"):
            for _ in range(3):                                              # push, tap all four, let go: again and again
                pad.push("LS", "up").wait(100).mark()
                for button, _ in TAPS:
                    pad.tap(button, 40).wait(40)
                self.assertEqual(pad.typed(), [output for _, output in TAPS])
                pad.recentre("LS").wait(300)
                self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.32 R3", rules=("R137",), rests=("A16",), either=("A9",))
    def test_a_button_held_from_inside_the_second_leaves_steering_when_it_ends(self):
        for button, _ in TAPS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(400).hold(button).wait(599)
                self.assertTrue(pad.has("Steering", WINDOW))                 # blocked for as long as the window is on
                pad.mark().wait(60)                                          # the Fallback Hold's bind repeats every 50 ms
                self.assertTrue(pad.lacks("Steering", HOLD, WINDOW), button)
                self.assertEqual(pad.seen("beep"), [("beep", "Steering")])

    @scenario("90.32 R4", rules=("R137",), rests=("A16",))
    def test_after_the_second_a_driver_or_a_menu_button_leaves_steering_at_once(self):
        for button, output in TAPS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(1500).mark().hold(button)
                self.assertTrue(pad.lacks("Steering", HOLD), button)
                self.assertNotIn(output, pad.typed())                        # no Tab, Escape or scroll there


if __name__ == "__main__":
    unittest.main()
