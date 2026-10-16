"""90.42: Fn feedback and the full-deflection exit from Steering.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.fn_feedback_steering_clear import *

class FnFeedbackAndSteeringClear(unittest.TestCase):


    def test_on_the_90_57_build_full_deflection_removed_the_entire_family_windows_first(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, '90.57'))
            family = steering_family(layout)
            cleared = family
            windows = family & set(always_on_layers(layout))
            for direction in ('dpad_north', 'dpad_south'):
                with self.subTest(variant=variant, direction=direction):
                    activators = layout.active('Steering')['joystick']['inputs'][direction]['activators']
                    self.assertEqual(list(activators), ['Soft_Press'])
                    entry = activators['Soft_Press']
                    self.assertEqual(entry['settings'], {
                        'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0',
                        'haptic_intensity': '1', 'activation_threshold': '29031'})
                    operations = layout.layer_ops(entry)
                    self.assertEqual({(op, title) for op, title in operations},
                                     {('remove_layer', title) for title in cleared})
                    self.assertEqual(len(operations), len(cleared))
                    # A stale timed helper must leave before any ordinary
                    # layer mutation, even when Steering is above it.
                    removed = [title for _, title in operations]
                    self.assertEqual(set(removed[:len(windows)]), windows)
                    self.assertEqual(removed[-1], 'Steering')
                    self.assertNotIn(('remove_layer', 'Gyro'), operations)
                    for action in actions(entry):
                        command = REMOVE.search(action)
                        self.assertIsNotNone(command)
                        self.assertEqual(command.group(2), '0')
                        self.assertEqual(command.group(3),
                                         '1' if layout.resolve(command.group(1)) == 'Steering' else '0')


if __name__ == "__main__":
    unittest.main()
