"""90.66: in `Steering` each driver mode-shifts the left stick to a group whose up and down are empty.

From 90.65. Confirmed by the author on the Deck, 2026-10-13 (A69): a burst of `remove_layer` calls makes a chord
evaluate again and an evaluation can fail, so the interruptible press beside a guard chord runs. In `Steering`
that took the driver's layer off with the driver held, and `Steering`'s exit on up or down then ended `Steering`.

The author: "in steering base if you are pressing bumper/triggers the up and down on left stick will be empty
binds, this protects from that edge case kicking us out of the steering stateful set accidently. I also want you
to remove the 5sec delay". The 5 ms start delay of 90.65 is gone from the ten left-edge cleanup presses.

The simulator never fails a guard, so the scenarios take the driver's layer off by hand (`drop`). What a mode shift
bound in a layer does on the Deck is A70, unverified: the simulator has it on while its layer answers the held
driver, in place of that layer's own stick group only.

90.67 took the mode shift out again (author, 2026-10-13: "revert the mode shift change"), so everything here reads
the 90.66 build.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_66 import *

class TheLeak(ScenarioCase):
    """The driver's layer goes with the driver held (A69). `Steering` has to stay and the layer come back."""

    def out(self, frozen=None):
        for driver, owner, key in DRIVERS:
            for direction in EXIT:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).push('LS', direction).wait(400)
                    yield pad, driver, pad.title(owner), key, direction

    @scenario('90.66 S1', rests=('A6', 'A69', 'A70'), either=('A9', 'A32'), frozen='90.66')
    def test_the_driver_layer_leaking_off_with_the_stick_up_or_down_keeps_steering(self):
        for pad, driver, owner, key, direction in self.out():
            pad.sim.drop(*(t for t in pad.stack if t.startswith('Steering |')))      # the driver's layer and the stick's
            self.assertTrue(pad.has('Steering'), (driver, direction))
            pad.wait(60)                                     # the driver's repeating chord, every 50 ms
            self.assertTrue(pad.has('Steering', owner), (driver, direction))
            self.assertIn(key, pad.down())
            pad.recentre('LS').wait(300).let_go(driver).wait(300)
            self.assertEqual(pad.stack[:2], pad.layers('Base', 'Steering'))
            self.assertTrue(pad.lacks(owner))

    @scenario('90.66 S2', rests=('A69',), either=('A9', 'A32'), frozen='90.65')
    def test_on_90_65_the_same_leak_ends_steering(self):
        for pad, driver, owner, key, direction in self.out():
            pad.sim.drop(*(t for t in pad.stack if t.startswith('Steering |')))
            pad.wait(60)
            self.assertTrue(pad.lacks('Steering'), (driver, direction))

    @scenario('90.66 S3', rests=('A70',), either=('A9', 'A32'), frozen='90.66')
    def test_with_no_driver_held_up_and_down_still_end_steering(self):
        for direction in EXIT:
            for pad in self.each(start=('Base', 'Steering')):
                pad.push('LS', direction).wait(100)
                self.assertTrue(pad.lacks('Steering'), direction)

    @scenario('90.66 S4', rests=('A10', 'A69', 'A70'), either=('A9', 'A32'), frozen='90.66')
    def test_a_and_d_stay_down_through_the_leak(self):
        for driver, owner, key in DRIVERS:
            for direction, letter in (('left', 'A'), ('right', 'D')):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).push('LS', direction).wait(200)
                    self.assertEqual(pad.down(), sorted([letter, key]))
                    pad.sim.drop(pad.title(owner))
                    self.assertIn(letter, pad.down())
                    pad.wait(60)
                    self.assertTrue(pad.has('Steering', pad.title(owner)))
                    self.assertEqual(pad.down(), sorted([letter, key]))

    @scenario('90.66 S5', rests=('A70',), either=('A9', 'A32'), frozen='90.66')
    def test_the_stick_still_scrolls_in_the_driver_layer(self):
        # The shift is held from `Steering` underneath; the driver's layer has its own stick group (A70).
        for driver, owner, _ in DRIVERS:
            for direction in EXIT:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300)
                    pad.mark()
                    pad.flick('LS', direction, 60).wait(300)
                    self.assertEqual(len([t for t in pad.typed() if 'SCROLL' in t]), 1, (driver, direction))
                    self.assertTrue(pad.has('Steering', pad.title(owner)))


if __name__ == "__main__":
    unittest.main()
