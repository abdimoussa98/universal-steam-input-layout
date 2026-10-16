"""90.56: the left edge's cleanup is the press and its guard chord again in ten Steering layers; only the Entry Guard keeps a chord with Invert Activation.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_56 import *

class EdgeCleanup(ScenarioCase):
    """The author's fault on 90.55: a thumb lifting in the stick modifiers cleared the W or S layer and ended
    `Steering`. The author suspects the chord with Invert Activation fires after a remove_layer call although a
    bumper is held. The simulator never showed it (A61), so these say what the binds are meant to do."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.56 E1', rules=('R133', 'R170'), rests=('A27', 'A36'), either=('A9', 'A32'))
    def test_no_stick_movement_removes_the_driver_layer_while_the_driver_is_held(self):
        for pad, _, owner, key in self.held():
            for direction in ('up', 'down', 'up', 'left', 'right', 'down'):
                for ms in (30, 60, 150, 300):
                    pad.flick('LS', direction, ms)
                    self.assertTrue(pad.has('Steering', owner))
                    self.assertIn(key, pad.down())
                    pad.wait(40)
            for _ in range(3):                               # the edge alone, out and back
                pad.hold('LS edge').wait(40).let_go('LS edge').wait(40)
                self.assertTrue(pad.has('Steering', owner))
            pad.wait(400)
            self.assertTrue(pad.has('Steering', owner) and pad.lacks(*FAMILY))
            self.assertEqual(pad.down(), [key])

    @scenario('90.56 E2', rules=('R133',), rests=('A25', 'A27'), either=('A9', 'A32'), frozen='90.58')
    def test_a_missed_driver_release_clears_when_the_stick_reaches_the_edge(self):
        # The press runs when the edge goes out with no driver held. The inverted chord of 90.55 ran as it came back.
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(300)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            pad.let_go('LS edge').wait(100)
            self.assertEqual(pad.down(), [])

    @scenario('90.56 E3', rules=('R133',), rests=('A6', 'A25', 'A27'), either=('A9', 'A32'))
    def test_a_missed_driver_release_during_a_deflect_leaves_no_stick_layer(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, _, _, _ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300).push('LS', direction).wait(100).miss(driver).wait(600)
                    pad.recentre('LS').wait(400)
                    self.assertTrue(pad.lacks(owner, *FAMILY))
                    pad.lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.56 E4', rules=('R133',), rests=('A7', 'A27', 'A36'), either=('A9', 'A32'))
    def test_a_thumb_lifting_at_any_stage_keeps_the_driver_layer_and_steering(self):
        # The thumbs rest before the driver goes down, so the stick helpers are under the driver's layer and
        # each lift takes real layers off. The right thumb lifts, then the left one loses touch with the stick out.
        for driver, owner, key in DRIVERS:
            for direction, _, modifier, _, layer in SIDES:
                for stage in ('modifier', 'marker', 'scroll', 'cover'):
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.touch('LS').touch('RS').wait(400).hold(driver).wait(300)
                        self.assertTrue(pad.has('LST: Entry Point', 'RST: Entry Point', owner))
                        if stage in ('modifier', 'marker'):
                            pad.push('LS', direction).wait(60 if stage == 'modifier' else 300)
                        else:
                            pad.flick('LS', direction).wait(20).push('LS', direction).wait(60 if stage == 'scroll' else 300)
                        self.assertTrue(pad.has(layer if stage in ('scroll', 'cover') else modifier), stage)
                        pad.lift('RS').wait(60)
                        self.assertTrue(pad.has('Steering', owner) and key in pad.down(), stage)
                        pad.sim.release(('joystick', 'touch'))
                        pad.wait(60)
                        self.assertTrue(pad.has('Steering', owner) and key in pad.down(), stage)
                        pad.recentre('LS').wait(400)
                        self.assertTrue(pad.has('Steering', owner) and pad.lacks(*FAMILY), stage)
                        self.assertEqual(pad.down(), [key])
                        pad.let_go(driver).wait(300)
                        self.assertEqual(pad.down(), [])


if __name__ == "__main__":
    unittest.main()
