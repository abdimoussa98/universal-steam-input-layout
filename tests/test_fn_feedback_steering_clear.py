"""90.42: Fn feedback and the full-deflection exit from Steering."""
import re
import unittest

from steam_layout.model import Layout, actions, always_on_layers, entries, map_title
from tests.scenario import RENAME, VARIANTS, layout_data

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

    def test_steering_full_deflection_removes_its_entire_family_and_keeps_gyro(self):
        for variant in VARIANTS:
            layout = Layout(layout_data(variant))
            family = steering_family(layout)
            covers = {map_title(title, RENAME) if variant == 'alternative' else title
                      for title in ('L1: Tap Cover', 'R1: Tap Cover')}
            cleared = family | covers
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
