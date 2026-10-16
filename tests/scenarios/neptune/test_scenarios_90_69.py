"""90.69, a trial off the line: no Hold to Repeat on the cleanup presses in the Steering layers.

From 90.68, not installed (90.70 is, also from 90.68). The author, 2026-10-13: "we've never tried just making the
regular press no longer repeating. Still interruptible, but no longer repeating", scope "all in steering", and "undo
the change to add the layer the entry guard in the cleanup functions for now".

Every test here reads the 90.69 build. Whether the missing repeat keeps a press from running past its guard chord
(A69) is for the Deck: the simulator decides a guard once and never fails it, and it does not run a held-back
repeating press when its guard goes either, so it shows no difference under an input that is already held.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_69 import *

class TheCleanupWithoutARepeat(ScenarioCase):

    @scenario('90.69 N1', rules=('R133',), rests=('A25', 'A27'), either=('A9', 'A32'), frozen='90.69')
    def test_a_stale_driver_layer_clears_when_the_stick_reaches_the_rim_and_no_guard_lands(self):
        for driver, owner, _ in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.touch('LS').hold(driver).wait(300).miss(driver).wait(100)
                self.assertTrue(pad.has(owner))
                pad.push('LS', 'left').wait(100)
                self.assertTrue(pad.has('Steering') and pad.lacks(owner, GUARD), driver)
                self.assertEqual(pad.down(), ['A'])

    @scenario('90.69 N2', rules=('R133',), rests=('A27',), either=('A9', 'A32'), frozen='90.69')
    def test_with_the_driver_held_no_cleanup_runs_at_the_rim_or_on_a_stick_touch(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.touch('LS').hold(driver).wait(300).push('LS', 'left').wait(300).touch('RS').wait(300)
                self.assertTrue(pad.has('Steering', owner), driver)
                self.assertEqual(pad.down(), sorted(['A', key]))
                pad.lift('RS').recentre('LS').wait(300).let_go(driver).wait(300)
                self.assertTrue(pad.has('Steering') and pad.lacks(owner))


if __name__ == "__main__":
    unittest.main()
