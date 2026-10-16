"""90.51: the ring pads bump by their own binds; the stick modifiers have no cleanup on their own direction.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_51 import *

class StickDeflect(ScenarioCase):
    @scenario('90.51 S1', rules=('R130',), rests=('A6', 'A8', 'A55', 'A58'), either=('A9', 'A32'))
    def test_four_deflects_in_one_driver_hold_each_scroll_once(self):
        for driver in ('R1', 'L1'):
            for direction, wheel in (('up', 'SCROLL_UP'), ('down', 'SCROLL_DOWN')):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300)
                    for _ in range(4):
                        pad.mark().flick('LS', direction).wait(600)
                        self.assertEqual([x for x in pad.typed() if x.startswith('mouse_wheel')], [f'mouse_wheel {wheel}'])
                        self.assertTrue(pad.has('Steering'))
                    pad.let_go(driver).lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.51 S2', rules=('R130', 'R133'), rests=('A25', 'A36'), either=('A9',))
    def test_a_missed_driver_release_with_the_stick_held_clears_on_the_next_input(self):
        for modifier, direction, _ in MODIFIERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold('R1').push('LS', direction).wait(60).miss('R1').wait(300)
                pad.recentre('LS').wait(300).tap('A').wait(300)
                self.assertTrue(pad.lacks(modifier, 'Steering | R1: W Key', 'Steering | LS: Tap Cover'))
                pad.lift('LS').wait(300)
                self.assertEqual(pad.down(), [])



class RingBump(ScenarioCase):
    @scenario('90.51 C1', rules=('R161',), rests=('A10', 'A56', 'A57'))
    def test_a_ring_click_types_its_output_on_both_pads(self):
        for stick, where, output in (('LP', 'left', 'LEFT_ARROW'), ('RP', 'left', 'mouse_button BACK')):
            for pad in self.each():
                pad.press_pad(stick, where).wait(120)
                self.assertIn(output, pad.down())
                pad.let_go_pad(stick).wait(300)
                self.assertEqual(pad.down(), [])



if __name__ == "__main__":
    unittest.main()
