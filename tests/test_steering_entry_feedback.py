"""90.43 static contracts that binary-input scenarios cannot establish."""
import json
import re
import unittest

from steam_layout.model import Layout, actions, entries
from tests.scenario import Pad, VARIANTS, layout_data

GUARD = 'Steering | LS: Entry Guard'
OLD_GUARD = 'Steering | LS: Fallback Guard'
COMMAND = re.compile(r'controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}|\d+) (\d+) (\d+)')
FN = {f'{prefix}Menu {side}: Fn Layer' for prefix in ('', 'Stateful | ') for side in ('Left', 'Right')}


def commands(layout, entry):
    return [(match.group(1), layout.resolve(match.group(2)), match.group(3), match.group(4))
            for action in reversed(actions(entry)) if (match := COMMAND.search(action))]


class SteeringEntryAndFeedback(unittest.TestCase):
    def each(self):
        for variant in VARIANTS:
            data = layout_data(variant)
            yield variant, data, Layout(data)

    def test_guard_reuses_the_slot_and_copies_the_four_way_movement_settings(self):
        for variant, data, layout in self.each():
            with self.subTest(variant=variant):
                self.assertEqual(len(layout.cm['action_layers']), 90)    # 88 until the two stick scroll layers of 90.52
                self.assertEqual(layout.resolve('65'), GUARD)
                self.assertNotIn(OLD_GUARD, json.dumps(data))
                group = layout.active(GUARD)['joystick']
                steering = layout.active('Steering')['joystick']
                self.assertEqual(group['mode'], steering['mode'])
                self.assertEqual(group['settings'], steering['settings'])
                self.assertEqual(group['settings']['layout'], '0')
                self.assertEqual(group['settings']['edge_binding_invert'], '0')
                self.assertNotIn('edge_binding_radius', group['settings'])
                for direction, key in (('dpad_north', 'W'), ('dpad_south', 'S'), ('dpad_west', 'A'), ('dpad_east', 'D')):
                    acts = group['inputs'][direction]['activators']
                    self.assertEqual(set(acts), {'Full_Press', 'release'})
                    self.assertEqual(actions(acts['Full_Press']), [f'key_press {key}, , '])
                    self.assertEqual(commands(layout, acts['release']), [('remove_layer', GUARD, '0', '0')])
                    self.assertEqual(acts['release']['settings'].get('haptic_intensity'), '0')
                edge = group['inputs']['edge']['activators']
                self.assertEqual(set(edge), {'chord', 'release'})
                self.assertEqual(commands(layout, edge['release']), [('remove_layer', GUARD, '0', '0')])

    def test_entry_and_handoffs_keep_runtime_order_and_feedback(self):
        for variant, data, layout in self.each():
            pad = Pad(variant, data=data)
            commit = layout.active('Transition Set 1')['switch']['inputs']['button_escape']['activators']['release']
            self.assertEqual(commands(layout, commit), [
                ('remove_layer', 'Transition Set 1', '0', '0'),
                ('add_layer', 'Steering', '0', '1'), ('add_layer', GUARD, '0', '0')])
            self.assertEqual(commit['settings']['haptic_intensity'], '1')
            for driver, target in (('R1', 'Steering | R1: W Key'), ('L1', 'Steering | L1: S Key')):
                source, name = pad.control(driver)
                for owner in ('Steering', GUARD):
                    entry = layout.active(owner)[source]['inputs'][name]['activators']['chord']
                    ops = commands(layout, entry)
                    expected = [('add_layer', pad.title(target), '0', '0')]
                    if owner == GUARD:
                        expected.insert(0, ('remove_layer', GUARD, '0', '0'))
                    self.assertEqual(ops, expected)
                    self.assertEqual(entry['settings']['hold_repeats'], '1')
                    self.assertEqual(entry['settings']['repeat_rate'], '50')
            for button, side in (('button_escape', 'Right'), ('button_menu', 'Left')):
                acts = layout.active(GUARD)['switch']['inputs'][button]['activators']
                self.assertEqual(set(acts), {'Start_Press'})
                entry = acts['Start_Press']
                self.assertNotEqual(entry['settings'].get('hold_repeats'), '1')
                # Until 90.57 the three ramp layers were removed first, as in `Steering`'s own menu press. The
                # guard binds the right stick's edge itself, so no ramp layer comes on while it is on, and
                # 90.58 took those three removes out (R132).
                self.assertEqual(commands(layout, entry), [
                    ('remove_layer', GUARD, '0', '0'),
                    ('add_layer', f'Stateful | Menu {side}: Entry Point', '0', '0')])
                self.assertIn('edge', layout.active(GUARD)['right_joystick']['inputs'])

    def test_guard_touches_pads_and_camera_cannot_add_helpers_or_disarm_at_center(self):
        for variant, data, layout in self.each():
            pad = Pad(variant, data=data)
            allowed = {pad.title('Steering | R1: W Key'), pad.title('Steering | L1: S Key'),
                       'Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point'}
            adds = set()
            for source, group in layout.active(GUARD).items():
                for name, slot in group.get('inputs', {}).items():
                    for kind, entry in entries(slot.get('activators', {})):
                        adds.update(target for op, target in layout.layer_ops(entry) if op == 'add_layer')
                        if (source in ('joystick', 'right_joystick') and name == 'touch') or (source == 'right_joystick' and name == 'edge'):
                            self.assertNotIn(('remove_layer', GUARD), layout.layer_ops(entry))
            self.assertEqual(adds, allowed)
            for source, prefix in (('joystick', 'LST'), ('right_joystick', 'RST')):
                entry = layout.active(GUARD)[source]['inputs']['touch']['activators']['release']
                self.assertEqual(set(layout.layer_ops(entry)), {('remove_layer', f'{prefix}: {name}')
                    for name in ('Entry Point', 'Tap Cover', 'Temporary Gyro')})
            for source in ('left_trackpad', 'right_trackpad'):
                for name in ('touch', 'click'):
                    binding = layout.active(GUARD)[source]['inputs'][name]
                    self.assertTrue(binding.get('activators'))
                    for _, entry in entries(binding['activators']):
                        self.assertEqual(layout.layer_ops(entry), [])
                        self.assertFalse(any('key_press ' in action or 'mouse_button ' in action for action in actions(entry)))

    def test_modifier_recovery_removes_only_its_modifier_and_cover(self):
        controls = [('button_diamond', f'button_{key}') for key in 'abxy']
        controls += [('dpad', f'dpad_{direction}') for direction in ('north', 'south', 'east', 'west')]
        controls += [('switch', 'button_escape'), ('switch', 'button_menu'),
                     ('joystick', 'click'), ('right_joystick', 'click'), ('right_joystick', 'edge')]
        for variant, _, layout in self.each():
            checked = 0
            for title in ('Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0'):
                for source, name in controls:
                    with self.subTest(variant=variant, layer=title, source=source, input=name):
                        acts = layout.active(title)[source]['inputs'][name]['activators']
                        self.assertIn('chord', acts)
                        entry = acts['Full_Press']
                        self.assertEqual(set(layout.layer_ops(entry)), {
                            ('remove_layer', title), ('remove_layer', 'Steering | LS: Tap Cover')})
                        self.assertEqual(entry['settings'].get('hold_repeats'), '1')
                        self.assertNotEqual(entry['settings'].get('interruptable'), '0')
                        checked += 1
            self.assertEqual(checked, 26)

    def test_each_feedback_entry_has_one_beep_and_gyro_cleanup_targets_are_quiet(self):
        for variant, data, layout in self.each():
            flagged = []
            for title in layout.presets:
                for source, group in layout.active(title).items():
                    for name, slot in group.get('inputs', {}).items():
                        for kind, entry in entries(slot.get('activators', {})):
                            beeps = [command for command in commands(layout, entry) if command[3] == '1']
                            self.assertLessEqual(len(beeps), 1, (variant, title, source, name, kind))
                            if beeps:
                                flagged.append((title, source, name, kind))
            self.assertEqual(len(flagged), 30)
            pad = Pad(variant, data=data)
            for first, second in (('L1', 'R1'), ('R1', 'L1')):
                gyro = pad.title(f'Gyro | {first}!{second}: Modifier 2')
                steering = pad.title(f'Steering | {first}!{second}: Modifier 2')
                for driver in (first, second):
                    source, name = pad.control(driver)
                    entry = layout.active(gyro)[source]['inputs'][name]['activators']['release']
                    self.assertEqual([item for item in commands(layout, entry) if item[3] == '1'],
                                     [('remove_layer', 'Gyro', '1', '1')])
                source, name = pad.control(second)
                entry = layout.active(steering)[source]['inputs'][name]['activators']['release']
                self.assertEqual([item for item in commands(layout, entry) if item[3] == '1'], [])

    def test_all_sixteen_fn_adds_keep_low_haptic_and_no_beep(self):
        for variant, _, layout in self.each():
            found = []
            for group in layout.groups.values():
                for name, slot in group.get('inputs', {}).items():
                    for bank in ('activators', 'disabled_activators'):
                        for kind, entry in entries(slot.get(bank) or {}):
                            targets = [command for command in commands(layout, entry)
                                       if command[0] == 'add_layer' and command[1] in FN]
                            if targets:
                                self.assertEqual(entry.get('settings', {}).get('haptic_intensity'), '1')
                                self.assertTrue(all(command[3] == '0' for command in targets))
                                found.append((group['id'], name, bank, kind))
            self.assertEqual(len(found), 16, variant)


if __name__ == '__main__':
    unittest.main()
