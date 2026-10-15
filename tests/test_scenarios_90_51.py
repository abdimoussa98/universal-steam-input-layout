"""90.51: the ring pads bump by their own binds; the stick modifiers have no cleanup on their own direction."""

import unittest

from steam_layout.model import Layout, entries
from tests.scenario import ScenarioCase, frozen_layout_data, layout_data, scenario

MODIFIERS = (('Steering | LS Up: Modifier 1', 'up', 'dpad_north'), ('Steering | LS Down: Modifier 0', 'down', 'dpad_south'))


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

    def test_the_modifiers_own_direction_has_the_hold_marker_and_its_reset_only(self):
        # The 90.51 shape, on its frozen candidate: 90.52 gave the direction its own Release and a chord on the deflect.
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.51'))
            for modifier, _, name in MODIFIERS:
                found = list(entries(layout.active(modifier)['joystick']['inputs'][name]['activators']))
                self.assertEqual(sorted(kind for kind, _ in found), ['Full_Press', 'chord'])
                by = dict(found)
                self.assertEqual(layout.layer_ops(by['Full_Press']), [('remove_layer', 'Steering | LS: Tap Cover')])
                self.assertEqual(by['Full_Press']['settings'].get('interruptable'), '0')
                self.assertEqual(by['chord']['settings']['delay_start'], '200')
                self.assertIn(('add_layer', 'Steering | LS: Tap Cover'), layout.layer_ops(by['chord']))


class RingBump(ScenarioCase):
    @scenario('90.51 C1', rules=('R161',), rests=('A10', 'A56', 'A57'))
    def test_a_ring_click_types_its_output_on_both_pads(self):
        for stick, where, output in (('LP', 'left', 'LEFT_ARROW'), ('RP', 'left', 'mouse_button BACK')):
            for pad in self.each():
                pad.press_pad(stick, where).wait(120)
                self.assertIn(output, pad.down())
                pad.let_go_pad(stick).wait(300)
                self.assertEqual(pad.down(), [])

    def test_the_ring_pads_leave_haptics_to_their_binds(self):
        # On the 90.70 build: since 90.71 the D-pad outputs are silent and the click bumps High (90.71 Shape).
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.70'))
            for title, source in (('LTP: Arrow Keys', 'left_trackpad'), ('RTP: Mouse Buttons', 'right_trackpad')):
                group = layout.active(title)[source]
                self.assertEqual(group['settings']['haptic_intensity_override'], '5')
                for name, node in group['inputs'].items():
                    for kind, entry in entries(node['activators']):
                        low = name.startswith('dpad_') and kind == 'Full_Press'
                        self.assertEqual(entry['settings']['haptic_intensity'], '1' if low else '0', (title, name, kind))


if __name__ == '__main__':
    unittest.main()
