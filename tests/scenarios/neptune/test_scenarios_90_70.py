"""90.70: every cleanup function in the Steering layers adds the Entry Guard before it removes.

From 90.68. The author, 2026-10-13: "for 90.70 keep the changes from 90.68 and have all the steering cleanups add the
entry steering guard." 90.67 had the add on the left stick's edge of ten Steering layers; a cleanup press can run past
its guard chord on any input (A69), so the other 80 cleanup presses of those layers carry it too.

The simulator never runs a press past its guard and is not made to (the author, on 90.67). The scenarios state the
ordinary cleanup, which carries the same add.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_70 import *

class TheGuardInEveryCleanup(ScenarioCase):
    """A driver's release is missed (A25), so its layer stays on with no driver held, and a cleanup function on
    another input than the left stick's edge clears it."""

    @scenario('90.70 J1', rules=('R176',), rests=('A4', 'A25', 'A61'), either=('A9', 'A32'))
    def test_with_the_stick_at_centre_the_guard_comes_and_leaves_at_once(self):
        # The guard's own inverted chord takes it off: the stick is inside the ring and no driver is held.
        for driver, owner, _ in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).wait(300).miss(driver).wait(100).mark()
                pad.touch('RS').wait(20)
                self.assertTrue(pad.has('Steering') and pad.lacks(owner, GUARD), driver)
                self.assertEqual(pad.down(), [])

    @scenario('90.70 J2', rules=('R176',), rests=('A4', 'A10', 'A25', 'A61'), either=('A9', 'A32'))
    def test_with_the_stick_up_or_down_a_button_cleanup_leaves_the_guard_and_steering_stays(self):
        # A's cleanup function is the stick modifier's and removes only that layer, so the stale driver layer
        # stays under the guard until the stick comes back. On 90.68 the driver layer's left edge then ran and
        # left the guard by itself; here the guard is over that edge.
        for pad, driver, owner, direction in self.out():
            self.assertTrue(pad.has('Steering', GUARD), (driver, direction))
            self.assertFalse([title for title in pad.stack if 'Modifier' in title], (driver, direction))
            self.assertIn(KEYS[direction], pad.down())
            pad.let_go('A').recentre('LS').wait(300)
            self.assertTrue(pad.has('Steering') and pad.lacks(GUARD, owner), (driver, direction))
            self.assertEqual(pad.down(), [])

    def out(self):
        # The stick goes out with the driver held, so the left edge's own press is held back; then the release is
        # missed and a face button's cleanup function clears the stale layers.
        for driver, owner, _ in DRIVERS:
            for direction in KEYS:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).push('LS', direction).wait(60).miss(driver).hold('A').wait(100)
                    yield pad, driver, pad.title(owner), direction


if __name__ == "__main__":
    unittest.main()
