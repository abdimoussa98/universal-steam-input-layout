"""90.67: the mode shift of 90.66 is gone; the ten left-edge cleanup presses add the Entry Guard before they remove.

From 90.66. The author, 2026-10-13: "revert the mode shift change. I still want keep the removal of the delays on
the clean up functions though. ... for the left stick clean up removals to before cleaning up i want you to add the
left stick steering guard, this is a precaution for the weird edge case where the guard would fail for repeated
removal calls."

A press that runs past its guard chord (A69) then leaves `Steering | LS: Entry Guard` on top, not `Steering` and its
exit on up and down. The simulator never runs a press past its guard and is not made to (the author: "I don't think
we need to necessarily account for that super edge case"). The scenarios state the ordinary cleanup, which carries
the same add: after a missed driver release the stick at the rim leaves the Entry Guard, and `Steering` stays.

90.70 put the add on every cleanup press of the ten layers, so the shape tests here read the 90.67 build; the
scenarios hold on the working layout too.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_67 import *

class TheGuardInTheCleanup(ScenarioCase):
    """A driver's release is missed (A25), so its layer stays on with no driver held; the stick then reaches the rim
    and the layer's cleanup press runs, as it should."""

    def stale(self):
        for driver, owner, _ in DRIVERS:
            for direction in KEYS:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).miss(driver).wait(100)
                    assert pad.has(owner)
                    pad.push('LS', direction).wait(400)
                    yield pad, driver, pad.title(owner), direction

    @scenario('90.67 G1', rules=('R176',), rests=('A4', 'A10', 'A25', 'A61'), either=('A9', 'A32'))
    def test_a_stale_driver_layer_cleared_at_the_rim_leaves_the_entry_guard_and_steering_stays(self):
        for pad, driver, owner, direction in self.stale():
            self.assertTrue(pad.has('Steering', GUARD), (driver, direction))
            self.assertTrue(pad.lacks(owner), (driver, direction))
            self.assertEqual(pad.down(), [KEYS[direction]])                 # the guard's own key, by the stick
            pad.recentre('LS').wait(300)
            self.assertTrue(pad.has('Steering') and pad.lacks(GUARD), (driver, direction))
            self.assertEqual(pad.down(), [])

    @scenario('90.67 G2', rules=('R176',), rests=('A25',), either=('A9', 'A32'), frozen='90.66')
    def test_on_90_66_the_same_cleanup_ends_steering(self):
        for pad, driver, owner, direction in self.stale():
            self.assertTrue(pad.lacks('Steering', GUARD), (driver, direction))

    @scenario('90.67 G3', rules=('R176',), rests=('A4', 'A25', 'A61'), either=('A9', 'A32'))
    def test_after_the_guard_has_left_a_second_push_up_or_down_ends_steering(self):
        for pad, driver, owner, direction in self.stale():
            pad.recentre('LS').wait(300)
            pad.push('LS', direction).wait(100)
            self.assertTrue(pad.lacks('Steering'), (driver, direction))

    @scenario('90.67 G4', rules=('R176', 'R133'), rests=('A27',), either=('A9', 'A32'))
    def test_with_the_driver_held_the_press_does_not_run_and_no_guard_lands(self):
        for driver, owner, key in DRIVERS:
            for direction in ('up', 'down', 'left', 'right'):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).push('LS', direction).wait(400)
                    self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD), (driver, direction))
                    self.assertIn(key, pad.down())
                    pad.recentre('LS').wait(300).let_go(driver).wait(300)
                    self.assertEqual(pad.stack[:2], pad.layers('Base', 'Steering'))
                    self.assertTrue(pad.lacks(owner, GUARD))

    @scenario('90.67 G5', rules=('R176', 'R137'), rests=('A4', 'A25', 'A61'), either=('A9', 'A32'))
    def test_a_driver_pressed_over_the_guard_takes_it_over(self):
        # What the held driver does after a press that ran past its guard (A69): the guard's repeating chord on
        # the driver removes the guard and adds the driver's layer.
        for pad, driver, owner, direction in self.stale():
            pad.hold(driver).wait(60)
            self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD), (driver, direction))
            self.assertIn(dict((d, k) for d, _, k in DRIVERS)[driver], pad.down())
            pad.recentre('LS').wait(300).let_go(driver).wait(300)
            self.assertEqual(pad.stack[:2], pad.layers('Base', 'Steering'))


if __name__ == "__main__":
    unittest.main()
