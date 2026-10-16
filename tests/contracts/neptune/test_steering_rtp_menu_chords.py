"""90.38 generated configuration, ordering, and narrow inverted-edge exception.

The contracts were last written against 90.42. 90.43 replaced `Steering | LS: Fallback Guard` with
`Steering | LS: Entry Guard`, and the tests below name the Entry Guard where the requirement still holds.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.steering_rtp_menu_chords import *

class SteeringRtpMenu(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            data = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())
            yield variant, data, Layout(data)



    def test_menu_entry_conditions_repeat_and_do_not_repeat_key_output(self):
        for _, _, layout in self.each():
            # Not the Entry Guard: it binds both as a silent Start Press (90.43, tests/test_steering_entry_feedback.py).
            for title in ('Base', 'Steering', 'Cursor Gyro'):
                for button, mask in (('button_menu', '4096'), ('button_escape', '16384')):
                    acts = layout.active(title)['switch']['inputs'][button]['activators']
                    self.assertEqual(list(acts), ['chord'])
                    self.assertEqual(acts['chord']['settings'], {
                        'gyro_ratchet_button_mask': mask, 'hold_repeats': '1', 'interruptable': '0'})
            for side, button, selector in (('Left', 'button_escape', '15'), ('Right', 'button_menu', '14')):
                for title in (f'Menu {side}: Entry Point', f'Menu {side}: Fn Layer',
                              f'Stateful | Menu {side}: Entry Point'):
                    chord = layout.active(title)['switch']['inputs'][button]['activators']['chord']
                    expected = {'chord_button': selector, 'interruptable': '0', 'hold_repeats': '1'}
                    if title.endswith(': Entry Point'):
                        expected['haptic_intensity'] = '1'
                    self.assertEqual(chord['settings'], expected)
                key = layout.active(f'Stateful | Menu {side}: Fn Layer')['switch']['inputs'][button]['activators']['chord']
                self.assertNotEqual(key['settings'].get('hold_repeats'), '1')

    def test_steering_inherits_pad_and_direction_soft_presses_leave_steering(self):
        # Until 90.57 up and down removed the whole family, the Entry Guard included. Each of those layers binds
        # up and down itself, so this bind only runs with `Steering` bare; since 90.58 it removes `Steering` alone.
        for _, _, layout in self.each():
            self.assertNotIn('right_trackpad', layout.active('Steering'))      # the Entry Guard blocks both pads, by design
            for name in ('dpad_north', 'dpad_south'):
                acts = layout.active('Steering')['joystick']['inputs'][name]['activators']
                self.assertEqual(list(acts), ['Soft_Press'])
                entry = acts['Soft_Press']
                self.assertEqual(entry['settings'], {'hold_repeats': '1', 'repeat_rate': '50',
                    'interruptable': '0', 'haptic_intensity': '1', 'activation_threshold': '29031'})
                self.assertEqual(layout.layer_ops(entry), [('remove_layer', 'Steering')])
                self.assertIn(name, layout.active(ENTRY_GUARD)['joystick']['inputs'])

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
            # Two delays and four thumb completions, in the two stateful menu entries. Until 90.48 the four
            # Steering modifier layers had three each (18); they remove no right pad layer any more (author,
            # 2026-10-10 and 2026-10-11; tests/test_scenarios_90_55.py).
            self.assertEqual(len(found), 6)
            self.assertEqual({title for title, _, _, _ in found}, set(STATEFUL_MENU))

    def test_inverted_edge_exception_rejects_changed_action_selector_repeat_or_owner(self):
        for _, data, layout in self.each():
            report = audit_layout(data)
            self.assertEqual(len(report['allowed_inverted']), 1)        # the Entry Guard's; 90.61 to 90.64 had ten left edges too
            self.assertFalse(report['inverted_edges'])
            for change in ('selector', 'repeat', 'target', 'owner'):
                mutant = copy.deepcopy(data)
                m = Layout(mutant)
                group = m.active(ENTRY_GUARD)['joystick']
                edge = group['inputs']['edge']['activators']['chord']
                if change == 'selector': edge['settings']['gyro_ratchet_button_mask'] = '4096'
                if change == 'repeat': edge['settings']['hold_repeats'] = '0'
                if change == 'target': edge['bindings']['binding'] = build.op('add', 'Gyro')
                if change == 'owner': m.presets['Steering']['group_source_bindings'][group['id']] = 'joystick active'
                self.assertTrue(audit_layout(mutant)['inverted_edges'], change)


if __name__ == "__main__":
    unittest.main()
