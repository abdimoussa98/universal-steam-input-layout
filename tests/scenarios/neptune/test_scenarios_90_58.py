"""90.58: 90.57 without the removes that never take a layer off. Nothing is added, and nothing plays differently.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_58 import *

class MissedReleases(ScenarioCase):
    """The author's cases, 2026-10-12: L1's modifier and its cover, and the plain Modifier 2 layers."""

    @scenario('90.58 M1', rules=('R128', 'R135'), rests=('A1', 'A7', 'A25'), either=('A9', 'A32'))
    def test_a_modifier_left_on_with_its_cursor_layer_goes_in_two_presses_of_a_at_most(self):
        # The modifier's cleanup on A named the cursor layer until 90.57. The cursor layer binds A as a cancel, so
        # it answers A while it is on: that remove never took it off. The first press ends the cursor layer. The
        # modifier's own cleanup is then exposed under the held A: it runs on that press or on the next (A9).
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for bumper, modifier in (('L1', 'L1: Modifier 0'), ('R1', 'R1: Modifier 1')):
                for pad in self.each(start=home):
                    pad.hold(bumper).wait(300).miss(bumper).wait(300)
                    self.assertTrue(pad.has(('Gyro | ' if gyro else '') + modifier, f'{bumper}: Temp Cursor Gyro'))
                    pad.tap('A').wait(200)
                    self.assertTrue(pad.lacks(f'{bumper}: Temp Cursor Gyro'))
                    pad.tap('A').wait(200)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers(*home), []))

    @scenario('90.58 M2', rules=('R128', 'R169'), rests=('A1', 'A7', 'A25'), either=('A9', 'A32'))
    def test_both_bumpers_left_on_go_with_a_thumb_on_a_stick(self):
        # Modifier 2 with its three covers and both modifiers. The Modifier 2 layer's cleanup on a stick touch
        # named `L1&R1: Tap Cover` until 90.57; the cover binds both touches and clears the whole stack of them.
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for first, second in (('L1', 'R1'), ('R1', 'L1')):
                for stick in ('LS', 'RS'):
                    for pad in self.each(start=home):
                        pad.hold(first).wait(60).hold(second).wait(300).miss(first).wait(20).miss(second).wait(300)
                        self.assertTrue(pad.has('L1&R1: Tap Cover'))
                        pad.touch(stick).wait(100).lift(stick).wait(600)
                        self.assertEqual((pad.stack, pad.down()), (pad.layers(*home), []))

    @scenario('90.58 M3', rules=('R128', 'R169'), rests=('A1', 'A7', 'A25'), either=('A9', 'A32'))
    def test_a_modifier_left_on_under_its_cover_goes_with_a_thumb_on_a_stick(self):
        # A key typed with the bumper held puts the cover over the modifier. The modifier's cleanup on a stick
        # touch named the cover until 90.57; the cover binds both touches and removes itself and the modifier.
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for bumper, modifier in (('L1', 'L1: Modifier 0'), ('R1', 'R1: Modifier 1')):
                for stick in ('LS', 'RS'):
                    for pad in self.each(start=home):
                        pad.hold(bumper).wait(60).tap('A').wait(100).miss(bumper).wait(400)
                        self.assertTrue(pad.has(('Gyro | ' if gyro else '') + modifier, f'{bumper}: Tap Cover'))
                        pad.touch(stick).wait(100).lift(stick).wait(600)
                        self.assertEqual((pad.stack, pad.down()), (pad.layers(*home), []))


class Modes(ScenarioCase):
    @scenario('90.58 C1', rules=('R163',), rests=('A4', 'A17'), either=('A9', 'A32'))
    def test_entering_and_leaving_a_mode_over_pad_and_stick_layers_leaves_nothing_on(self):
        # The clears name 26 or 27 layers where they named 89. A thumb on each pad is on the stack when the
        # first click lands, and a thumb on the other stick as well when the second one does: its Tap Cover and
        # Temporary Gyro are the removes the register keeps at the Stateful Entry Points (R132).
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for menu, stick in itertools.product(('Start', 'Select'), ('LS', 'RS')):
                other = 'RS' if stick == 'LS' else 'LS'
                for pad in self.each(start=home):
                    allowed = set(pad.layers('Base', 'Gyro', *MODES))
                    pad.touch('LP').touch('RP').wait(100)
                    pad.hold(menu).wait(60).click(stick).wait(40).let_go(menu).wait(100)
                    pad.lift('LP').lift('RP').lift(stick).wait(600)
                    self.assertLessEqual(set(pad.stack), allowed, (menu, stick))
                    self.assertTrue(set(pad.stack) & set(pad.layers(*MODES)), (menu, stick))
                    self.assertEqual(pad.down(), [])
                    pad.touch('LP').touch('RP').touch(other).wait(400)
                    pad.hold(menu).wait(60).click(stick).wait(40).let_go(menu).wait(100)
                    pad.lift('LP').lift('RP').lift(stick).lift(other).wait(600)
                    self.assertLessEqual(set(pad.stack), allowed, (menu, stick))
                    self.assertEqual(pad.down(), [])


if __name__ == "__main__":
    unittest.main()
