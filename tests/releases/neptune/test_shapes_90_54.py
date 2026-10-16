"""90.54: 90.52 with one change, the stick modifiers' 200 ms hold timer on the left stick's edge.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_54 import *

class TimerOnTheEdgeShape(unittest.TestCase):
    def test_the_hold_timer_is_the_edges_third_entry_and_the_direction_keeps_the_reset_and_the_release(self):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.54'))
            for _, own, modifier, window, _, _ in SIDES:
                inputs = layout.active(modifier)['joystick']['inputs']
                on_stick = list(entries(inputs[own]['activators']))
                self.assertEqual([kind for kind, _ in on_stick], ['Full_Press', 'release'], (variant, modifier))
                reset, release = (entry for _, entry in on_stick)
                self.assertEqual(layout.layer_ops(reset), [('remove_layer', MARKER)])
                self.assertEqual(reset['settings'], {'hold_repeats': '1', 'repeat_rate': '250', 'interruptable': '0'})
                self.assertIn(('add_layer', window), layout.layer_ops(release))
                on_edge = list(entries(inputs['edge']['activators']))
                self.assertEqual([kind for kind, _ in on_edge], ['Full_Press', 'chord', 'chord'], (variant, modifier))
                cleanup, guard, timer = (entry for _, entry in on_edge)
                self.assertIn(('remove_layer', modifier), layout.layer_ops(cleanup))
                self.assertEqual(cleanup['settings'], {'hold_repeats': '1'})
                self.assertEqual(actions(guard), [EMPTY + ', , '])
                self.assertIn(('add_layer', MARKER), layout.layer_ops(timer))
                self.assertEqual(timer['settings'], {
                    'gyro_ratchet_button_mask': str(DEFLECT), 'gyro_ratchet_button_requireany_or_all': '0',
                    'delay_start': '200', 'interruptable': '0'}, (variant, modifier))

    def test_no_other_steering_bind_moved(self):
        # One change: the two stick scroll layers keep their 150 ms on up and down, as in 90.52.
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.54'))
            for _, own, _, _, scroll, _ in SIDES:
                delays = [entry['settings'].get('delay_start') for kind, entry in
                          entries(layout.active(scroll)['joystick']['inputs'][own]['activators']) if kind == 'chord']
                self.assertEqual(delays, ['150'], (variant, scroll))


if __name__ == "__main__":
    unittest.main()
