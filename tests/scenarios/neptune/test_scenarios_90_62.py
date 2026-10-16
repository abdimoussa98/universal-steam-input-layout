"""90.62: rocking in Steering the way the bumper modifiers do it.

From 90.61. With one driver held, pressing the other adds the other driver's layer and then Modifier 2 on top of
it. A Release inside Modifier 2 only removes: the layer of the driver still held is underneath already. Until
90.61 the first driver's Release added it (the hand-over of 90.57), and on the Deck W to S worked and S back to W
did not (author, 2026-10-12). The simulator played both directions before and plays them now.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_62 import *

class Rocking(ScenarioCase):
    @scenario('90.62 R1', rules=('R174',), rests=('A4', 'A7', 'A9', 'A10', 'A37'), either=('A9', 'A32'))
    def test_rocking_the_drivers_follows_the_held_one_and_steering_stays(self):
        # R1, L1, R1 up (S), R1 down, L1 up (W), L1 down, and round again. While both are held the first one's
        # key stays: Modifier 2 answers both drivers, and the second driver's layer waits underneath.
        for direction in (None, 'up'):
            for pad in self.each(start=('Base', STEERING)):
                pad.hold('R1').wait(300)
                if direction:
                    pad.push('LS', direction).wait(300)
                pad.hold('L1').wait(120)
                for _ in range(3):
                    self.assertEqual(pad.stack[-3:], pad.layers(W, S, 'Steering | R1!L1: Modifier 2'))
                    self.assertEqual(pad.down(), ['W'])
                    pad.let_go('R1').wait(120)
                    self.assertTrue(pad.has(STEERING, S) and pad.lacks(W, *MODIFIER_2))
                    self.assertEqual(pad.down(), ['S'])
                    pad.hold('R1').wait(120)
                    self.assertEqual(pad.stack[-3:], pad.layers(S, W, 'Steering | L1!R1: Modifier 2'))
                    self.assertEqual(pad.down(), ['S'])
                    pad.let_go('L1').wait(120)
                    self.assertTrue(pad.has(STEERING, W) and pad.lacks(S, *MODIFIER_2))
                    self.assertEqual(pad.down(), ['W'])
                    pad.hold('L1').wait(120)
                pad.let_go('L1').wait(120).recentre('LS').wait(300).let_go('R1').wait(300).lift('LS').wait(300)
                self.assertEqual(pad.stack, pad.layers('Base', STEERING))
                self.assertEqual(pad.down(), [])

    @scenario('90.62 R2', rules=('R174',), rests=('A7', 'A9', 'A10'), either=('A9', 'A32'))
    def test_the_second_driver_let_go_first_leaves_the_first_ones_layer_and_key(self):
        for first, own, own_key, second, other, _, modifier in ORDERS:
            for hold in (60, 400):
                for pad in self.each(start=('Base', STEERING)):
                    pad.hold(first).wait(300).hold(second).wait(hold)
                    self.assertTrue(pad.has(own, other, modifier))
                    self.assertEqual(pad.down(), [own_key])                  # no flash of the other key
                    pad.let_go(second).wait(200)
                    self.assertEqual(pad.stack, pad.layers('Base', STEERING, own))
                    self.assertEqual(pad.down(), [own_key])
                    pad.let_go(first).wait(300)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING), []))

    @scenario('90.62 R3', rules=('R174',), rests=('A7', 'A9', 'A10'), either=('A9', 'A32'))
    def test_the_other_key_is_never_typed_while_the_first_driver_is_held(self):
        for first, own, own_key, second, other, other_key, modifier in ORDERS:
            for pad in self.each(start=('Base', STEERING)):
                pad.hold(first).wait(300).mark()
                for gap in (20, 60, 250):
                    pad.hold(second).wait(gap).let_go(second).wait(gap)
                self.assertNotIn(other_key, [key for kind, key in pad.seen('down')] if pad.seen('down') else [])
                self.assertEqual(pad.down(), [own_key])


class MissedReleases(ScenarioCase):
    @scenario('90.62 M1', rules=('R128', 'R169'), rests=('A7', 'A25', 'A61'), either=('A9', 'A32'))
    def test_a_missed_release_of_the_second_driver_leaves_its_layer_until_a_thumb_is_on_a_stick(self):
        # The second driver's layer was added under Modifier 2 by its press. Its release never arrives; the first
        # driver's Release uncovers it with nobody holding it. It types nothing. (On 90.61 the hand-over added it
        # there and its edge chord, landing with no driver held, took it off at once.)
        for first, own, _, second, other, _, modifier in ORDERS:
            for stick in ('LS', 'RS'):
                for pad in self.each(start=('Base', STEERING)):
                    pad.hold(first).wait(300).hold(second).wait(300).miss(second).wait(500).let_go(first).wait(300)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING, other), []))
                    pad.touch(stick).wait(300).lift(stick).wait(600)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING), []))

    @scenario('90.62 M2', rules=('R128', 'R169'), rests=('A7', 'A25'), either=('A9', 'A32'))
    def test_both_releases_missed_a_button_clears_modifier_2_and_both_driver_layers(self):
        for first, own, _, second, other, _, modifier in ORDERS:
            for pad in self.each(start=('Base', STEERING)):
                pad.hold(first).wait(300).hold(second).wait(300).miss(first, second).wait(100)
                self.assertTrue(pad.has(own, other, modifier))
                pad.tap('A', 120).wait(200).tap('A', 120).wait(200)
                self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING), []))


if __name__ == "__main__":
    unittest.main()
