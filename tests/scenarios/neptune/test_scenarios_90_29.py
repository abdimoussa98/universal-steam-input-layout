"""Scenarios for 90.29: the beep is the second flag of a layer command.

The record is findings/2026-10-04-quiet-resets-and-beeps/README.md.

- Until 90.28 every transition, the stateful exits and the `Menu Keys` entry set the first flag,
  which shows the layer's name, and were silent on the Deck (the author, 2026-10-04). They now set
  the second (A49). The scenarios of 90.10, 90.21, 90.22 and 90.25 check the transitions' feedback
  on the working layout; these two cover what they leave out.
- The Fn layers' delayed add used `0 1` until 90.40. Since 90.41 its beep is
  disabled; the live scenario checks that entering Fn stays silent.

The Tap Cover resets' haptic has no scenario: a reset that removes nothing leaves no trace on the
simulator. `test_quiet_resets_and_beeps.py` checks the setting.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

MENU_KEYS = "Menu Keys"
# first held, pressed, the first button's Fn layer, the chain's Entry Point
CHAINS = (("Select", "Start", "Menu Left: Fn Layer", "Menu Left!Right: Entry Point"),
          ("Start", "Select", "Menu Right: Fn Layer", "Menu Right!Left: Entry Point"))


def pulses(pad):
    """The haptic pulses since the mark: (intensity, layer)."""
    return [tuple(detail.split(" ", 1)[0:1] + [detail.split(" ", 1)[1].rsplit(" ", 1)[0]]) for _, detail in pad.seen("haptic")]


class Beeps(ScenarioCase):
    @scenario("90.29 Q1", rests=("A49", "A6"))
    def test_the_fn_hold_and_tap_do_not_beep(self):
        for first, _, fn, _ in CHAINS:
            for pad in self.each():
                pad.mark().tap(first, 60).wait(400)
                self.assertEqual(pad.seen("beep"), [])
                pad.mark().hold(first).wait(199)
                self.assertEqual(pad.seen("beep"), [])
                pad.wait(2)
                self.assertEqual((pad.top, pad.seen("beep")), (fn, []))
                pad.wait(1000)
                self.assertEqual(pad.seen("beep"), [])  # no beep during a held Fn entry

    @scenario("90.29 Q2", rules=("R161",), rests=("A49", "A6", "A16", "A36"))
    def test_menu_keys_beeps_and_pulses_coming_on_and_beeps_going_off(self):
        for first, second, _, entry in CHAINS:
            for pad in self.each():
                pad.hold(first).wait(400).mark().hold(second).wait(199)
                self.assertEqual((pad.top, pad.seen("haptic", "beep")), (entry, []))
                pad.wait(2)
                self.assertEqual(pad.stack, pad.layers("Base", MENU_KEYS))
                self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], ["haptic", "beep"])
                self.assertEqual((pulses(pad), pad.seen("beep")), ([("1", entry)], [("beep", MENU_KEYS)]))
                pad.let_go(second).let_go(first).wait(300)
                pad.mark().push("LS", "up").push("RS")                       # both sticks out: the exit
                self.assertTrue(pad.lacks(MENU_KEYS))
                self.assertEqual(pad.seen("beep"), [("beep", MENU_KEYS)])


if __name__ == "__main__":
    unittest.main()
