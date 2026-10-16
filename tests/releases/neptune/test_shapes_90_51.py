"""90.51: the ring pads bump by their own binds; the stick modifiers have no cleanup on their own direction.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_51 import *

class StickDeflect(ScenarioCase):


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


if __name__ == "__main__":
    unittest.main()
