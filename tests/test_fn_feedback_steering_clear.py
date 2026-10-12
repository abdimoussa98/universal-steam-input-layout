"""90.42: Fn feedback and the full-deflection exit from Steering."""
import re
import unittest

from steam_layout.model import Layout, actions, always_on_layers, entries
from tests.scenario import VARIANTS, frozen_layout_data, layout_data

FN = {f'{prefix}Menu {side}: Fn Layer'
      for prefix in ('', 'Stateful | ') for side in ('Left', 'Right')}
ADD = re.compile(r'controller_action add_layer (\{\{.+?\}\}|\d+) (\d+) (\d+)')
REMOVE = re.compile(r'controller_action remove_layer (\{\{.+?\}\}|\d+) (\d+) (\d+)')


def steering_family(layout):
    return {title for title in layout.presets
            if title == 'Steering' or title.startswith('Steering | ')}


class FnFeedbackAndSteeringClear(unittest.TestCase):
    def test_every_fn_add_has_a_low_bump_and_no_beep(self):
        # Include dormant groups and disabled banks: a copied/restored entry
        # must not silently restore the old feedback.
        for variant in VARIANTS:
            layout = Layout(layout_data(variant))
            found = set()
            for group in layout.groups.values():
                for name, slot in group.get('inputs', {}).items():
                    for bank in ('activators', 'disabled_activators'):
                        for kind, entry in entries(slot.get(bank) or {}):
                            targets = {target for op, target in layout.layer_ops(entry)
                                       if op == 'add_layer' and target in FN}
                            if not targets:
                                continue
                            with self.subTest(variant=variant, group=group['id'],
                                              input=name, bank=bank, kind=kind):
                                self.assertEqual(entry.get('settings', {}).get('haptic_intensity'), '1')
                                for action in actions(entry):
                                    match = ADD.search(action)
                                    if match and layout.resolve(match.group(1)) in FN:
                                        self.assertEqual(match.group(3), '0')
                            found.update(targets)
            self.assertEqual(found, FN, variant)

    def test_steering_full_deflection_removes_steering_and_keeps_gyro(self):
        # From 90.42 to 90.57 the exit named the whole Steering family (and until 90.56 the two bumper Tap
        # Covers), the two windows first. Every one of those thirteen layers binds up and down, so with one on,
        # this bind does not run, and none was ever under `Steering`. 90.58 took them out (R132; the author,
        # 2026-10-12: "trim"). The family clear is checked on the 90.57 build below.
        for variant in VARIANTS:
            layout = Layout(layout_data(variant))
            for direction in ('dpad_north', 'dpad_south'):
                with self.subTest(variant=variant, direction=direction):
                    activators = layout.active('Steering')['joystick']['inputs'][direction]['activators']
                    self.assertEqual(list(activators), ['Soft_Press'])
                    entry = activators['Soft_Press']
                    self.assertEqual(entry['settings'], {
                        'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0',
                        'haptic_intensity': '1', 'activation_threshold': '29031'})
                    self.assertEqual(layout.layer_ops(entry), [('remove_layer', 'Steering')])
                    for title in steering_family(layout) - {'Steering'}:       # each answers up and down itself
                        self.assertIn(direction, layout.active(title)['joystick']['inputs'], title)
                    for action in actions(entry):
                        command = REMOVE.search(action)
                        self.assertIsNotNone(command)
                        self.assertEqual((command.group(2), command.group(3)), ('0', '1'))

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


if __name__ == '__main__':
    unittest.main()
