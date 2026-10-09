"""90.38 generated configuration, ordering, and narrow inverted-edge exception."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from steam_layout.model import Layout, entries
from tools.audit_command_budget import audit_layout

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'steering_rtp_build', ROOT / 'findings/2026-10-08-steering-rtp-and-menu-chords/build_candidate.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class SteeringRtpMenu(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            data = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())
            yield variant, data, Layout(data)

    def test_working_layouts_are_generated_including_stored_order(self):
        for variant, working, _ in self.each():
            generated, _ = build.build(variant)
            for data in (working, generated):
                for field in ('title', 'description'):
                    data['controller_mappings'].pop(field)
            self.assertEqual(json.dumps(working), json.dumps(generated))

    def test_menu_entry_conditions_repeat_and_do_not_repeat_key_output(self):
        for _, _, layout in self.each():
            for title in ('Base', *build.MENU_OWNERS):
                for button, mask in (('button_menu', '4096'), ('button_escape', '16384')):
                    acts = layout.active(title)['switch']['inputs'][button]['activators']
                    self.assertEqual(list(acts), ['chord'])
                    self.assertEqual(acts['chord']['settings'], {
                        'gyro_ratchet_button_mask': mask, 'hold_repeats': '1', 'interruptable': '0'})
            for side, button, selector in (('Left', 'button_escape', '15'), ('Right', 'button_menu', '14')):
                for title in (f'Menu {side}: Entry Point', f'Menu {side}: Fn Layer',
                              f'Stateful | Menu {side}: Entry Point'):
                    chord = layout.active(title)['switch']['inputs'][button]['activators']['chord']
                    self.assertEqual(chord['settings'], {'chord_button': selector,
                                                        'interruptable': '0', 'hold_repeats': '1'})
                key = layout.active(f'Stateful | Menu {side}: Fn Layer')['switch']['inputs'][button]['activators']['chord']
                self.assertNotEqual(key['settings'].get('hold_repeats'), '1')

    def test_steering_inherits_pad_and_direction_soft_presses_keep_the_swap(self):
        for _, _, layout in self.each():
            for title in ('Steering', build.GUARD):
                self.assertNotIn('right_trackpad', layout.active(title))
            for name in ('dpad_north', 'dpad_south'):
                acts = layout.active('Steering')['joystick']['inputs'][name]['activators']
                self.assertEqual(list(acts), ['Soft_Press'])
                entry = acts['Soft_Press']
                self.assertEqual(entry['settings'], {'hold_repeats': '1', 'repeat_rate': '50',
                    'interruptable': '0', 'haptic_intensity': '3', 'activation_threshold': '29031'})
                self.assertEqual(layout.layer_ops(entry), [('add_layer', build.GUARD), ('remove_layer', 'Steering')])

    def test_delayed_targets_complete_before_rtp_cleanup_including_touch_completion(self):
        for _, _, layout in self.each():
            found = []
            for title in layout.presets:
                if not title.startswith(('Steering |', 'Stateful |')):
                    continue
                for source, group in layout.active(title).items():
                    for name, value in group.get('inputs', {}).items():
                        for kind, entry in entries(value.get('activators', {})):
                            if not (int(entry.get('settings', {}).get('delay_start', '0'))
                                    or (kind == 'release' and name == 'touch')):
                                continue
                            ops = layout.layer_ops(entry)
                            removed = [target for op, target in ops if op == 'remove_layer' and target in build.RTP]
                            if not removed:
                                continue
                            added = [target for op, target in ops if op == 'add_layer']
                            if not added:
                                continue
                            if added == ['Steering']:
                                continue  # fallback's separate handback/cleanup, not a pending apply
                            self.assertEqual(ops[0][0], 'add_layer', (title, source, name, kind))
                            self.assertEqual(set(removed), set(build.RTP))
                            self.assertNotIn(('remove_layer', 'RTP: Double Tap'), ops)
                            found.append((title, source, name, kind))
            self.assertEqual(len(found), 18)  # six delays and twelve thumb completions

    def test_inverted_edge_exception_rejects_changed_action_selector_repeat_or_owner(self):
        for _, data, layout in self.each():
            report = audit_layout(data)
            self.assertEqual(len(report['allowed_inverted']), 1)
            self.assertFalse(report['inverted_edges'])
            for change in ('selector', 'repeat', 'target', 'owner'):
                mutant = copy.deepcopy(data)
                m = Layout(mutant)
                group = m.active(build.GUARD)['joystick']
                edge = group['inputs']['edge']['activators']['chord']
                if change == 'selector': edge['settings']['gyro_ratchet_button_mask'] = '4096'
                if change == 'repeat': edge['settings']['hold_repeats'] = '0'
                if change == 'target': edge['bindings']['binding'] = build.op('add', 'Gyro')
                if change == 'owner': m.presets['Steering']['group_source_bindings'][group['id']] = 'joystick active'
                self.assertTrue(audit_layout(mutant)['inverted_edges'], change)


if __name__ == '__main__':
    unittest.main()
