"""90.63: the ring is inverted on the left edge of ten Steering layers.

From 90.62, one setting in ten groups: Outer Ring Binding Invert on the left stick. The chord with Invert
Activation that has been the edge's cleanup function since 90.61 then runs with the stick at the rim and no
driver held, where it ran off the rim. The author, 2026-10-12: "We need to invert the left stick edge for the
chorded inverted clean functions ... every where in steering except in entry steering guard."

The Soft Press timers on four of those edges don't follow the ring's setting (author, A67).

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_63 import *

class EdgeCleanupAtTheRim(ScenarioCase):
    """The chord runs while the stick is at the rim and no driver is held (A61 on an inverted ring). On the 90.64
    build: 90.65 put the press and its guard back on a normal ring."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.63 G1', rules=('R133', 'R170'), rests=('A61', 'A66'), either=('A9', 'A32'), frozen='90.64')
    def test_the_rim_with_a_driver_held_keeps_the_driver_layer(self):
        for pad, _, owner, key in self.held():
            for _ in range(3):
                pad.hold('LS edge').wait(300).let_go('LS edge').wait(40)
                self.assertTrue(pad.has('Steering', owner))
            for direction in ('up', 'down', 'left', 'right'):
                pad.push('LS', direction).wait(400)
                self.assertTrue(pad.has('Steering', owner), direction)
                self.assertIn(key, pad.down())
                pad.recentre('LS').wait(60)
            self.assertTrue(pad.has('Steering', owner))
            self.assertEqual(pad.down(), [key])

    @scenario('90.63 G2', rules=('R133',), rests=('A25', 'A61'), either=('A9', 'A32'), frozen='90.64')
    def test_a_missed_driver_release_clears_when_the_stick_reaches_the_rim(self):
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(400)
            self.assertTrue(pad.has(owner))                  # off the rim the chord's input counts as pressed: off
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            pad.let_go('LS edge').wait(100)
            self.assertEqual(pad.down(), [])

    @scenario('90.63 G3', rules=('R133',), rests=('A61',), either=('A9', 'A32'), frozen='90.64')
    def test_pressing_the_driver_again_shuts_the_chord_off_at_the_rim(self):
        for pad, driver, owner, key in self.held():
            pad.miss(driver).wait(100).hold(driver).wait(100)
            pad.hold('LS edge').wait(300).let_go('LS edge').wait(100)
            self.assertTrue(pad.has('Steering', owner))
            self.assertIn(key, pad.down())

    @scenario('90.63 G4', rules=('R133',), rests=('A61', 'A64', 'A67'), either=('A9', 'A32'), frozen='90.64')
    def test_the_timers_on_the_inverted_ring_still_run_with_the_stick_out(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, modifier, *_ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).push('LS', direction).wait(100)
                    self.assertTrue(pad.has(owner, modifier) and pad.lacks('Steering | LS: Tap Cover'))
                    pad.wait(200)                            # the 200 ms timer on the modifier's edge
                    self.assertTrue(pad.has(owner, modifier, 'Steering | LS: Tap Cover'), direction)
                    pad.recentre('LS').wait(300)
                    self.assertTrue(pad.has('Steering', owner))


if __name__ == "__main__":
    unittest.main()
