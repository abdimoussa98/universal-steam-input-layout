"""90.53: the Steering stick's timers sit on the drivers, its entry carries no cleanup, and the left edge cleans up with one inverted chord.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_53 import *

class EntryAndEdgeShape(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.53'))
            yield layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)

    def test_no_steering_layer_states_an_outer_ring_radius_on_the_left_stick(self):
        # The default, as in the Temp Cursor Gyro layers (author, 2026-10-10).
        for layout, _ in self.each():
            steering = [t for t in layout.presets if t.startswith('Steering')]
            self.assertEqual(len(steering), 14)
            for title in steering + [t for t in layout.presets if t.endswith('Temp Cursor Gyro')]:
                self.assertNotIn('edge_binding_radius', layout.active(title)['joystick'].get('settings', {}), title)

    def test_the_left_edge_cleans_up_with_one_inverted_chord_on_the_layers_drivers(self):
        for layout, name in self.each():
            for title in map(name, EDGE_CHORDS):
                edge = layout.active(title)['joystick']['inputs']['edge']['activators']
                self.assertEqual(list(edge), ['chord'], title)
                chord = edge['chord']
                settings = dict(chord['settings'])
                mask = int(settings.pop('gyro_ratchet_button_mask'))
                self.assertEqual(settings, {'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                                            'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}, title)
                self.assertFalse(mask & DEFLECT)
                ops = layout.layer_ops(chord)
                self.assertIn(('remove_layer', title), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)

    def test_the_entry_guard_keeps_its_chord_and_its_release(self):
        for layout, _ in self.each():
            edge = layout.active(GUARD)['joystick']['inputs']['edge']['activators']
            self.assertEqual(sorted(edge), ['chord', 'release'])
            self.assertEqual(edge['chord']['settings']['edge_binding_invert'], '1')
            for kind in edge:
                self.assertEqual(layout.layer_ops(edge[kind]), [('remove_layer', GUARD)])

    def test_up_and_down_in_the_driver_layers_hold_one_chord_and_no_cleanup(self):
        for layout, name in self.each():
            for _, owner, _ in DRIVERS:
                stick = layout.active(name(owner))['joystick']['inputs']
                guard = int(stick['edge']['activators']['chord']['settings']['gyro_ratchet_button_mask'])
                for _, direction, modifier, _, _, _ in SIDES:
                    found = list(entries(stick[direction]['activators']))
                    self.assertEqual([kind for kind, _ in found], ['chord'], (owner, direction))
                    chord = found[0][1]
                    self.assertEqual(layout.layer_ops(chord), [('add_layer', modifier)])
                    settings = chord['settings']
                    self.assertEqual(settings['gyro_ratchet_button_requireany_or_all'], '1')        # both, not either
                    mask = int(settings['gyro_ratchet_button_mask'])
                    self.assertEqual(bin(mask).count('1'), 2)
                    self.assertTrue(mask & DEFLECT and mask & guard, (owner, direction))
                    self.assertEqual((settings['hold_repeats'], settings['repeat_rate'], settings['interruptable']),
                                     ('1', '50', '0'))

    def test_no_start_delay_is_owned_by_a_stick_direction_in_the_steering_layers(self):
        for layout, _ in self.each():
            for title in (t for t in layout.presets if t.startswith('Steering')):
                for source in ('joystick', 'right_joystick'):
                    for name, value in layout.active(title)[source]['inputs'].items():
                        for kind, entry in entries(value.get('activators', {})):
                            self.assertFalse(entry.get('settings', {}).get('delay_start'), (title, source, name, kind))

    def test_each_driver_carries_its_key_the_timer_and_its_release_in_the_four_timer_layers(self):
        timers = [(side[2], side[1], MARKER, '200', '250') for side in SIDES] + [(side[4], side[1], COVER, '150', '200') for side in SIDES]
        for layout, name in self.each():
            for layer, direction, target, delay, rate in timers:
                on_stick = dict(entries(layout.active(layer)['joystick']['inputs'][direction]['activators']))
                self.assertNotIn('chord', on_stick, layer)
                resets = [e for kind, e in entries(layout.active(layer)['joystick']['inputs'][direction]['activators'])
                          if kind == 'Full_Press' and layout.layer_ops(e) == [('remove_layer', target)]]
                self.assertEqual([e['settings'] for e in resets], [{'hold_repeats': '1', 'repeat_rate': rate, 'interruptable': '0'}], layer)
                for _, owner, key in DRIVERS:
                    home = [(source, control, value['activators']) for source, group in layout.active(name(owner)).items()
                            for control, value in group.get('inputs', {}).items()
                            if any(a == f'key_press {key}, , ' for _, e in entries(value.get('activators', {})) for a in actions(e))]
                    self.assertEqual(len(home), 1)
                    source, control, there = home[0]
                    here = layout.active(layer)[source]['inputs'][control]['activators']
                    self.assertEqual(list(here), ['release', 'chord', 'Full_Press'], (layer, owner))
                    self.assertEqual(here['Full_Press']['settings'], there['Full_Press']['settings'])
                    # the key, then the other driver's way into Modifier 2: the add its own layer has on this
                    # input, and only the two removes that can matter here (R132)
                    other = name(next(o for _, o, _ in DRIVERS if o != owner))
                    entry = layout.active(other)[source]['inputs'][control]['activators']['chord']
                    second = layout.layer_ops(entry)[-1]
                    self.assertEqual(second[0], 'add_layer')
                    self.assertIn('Modifier 2', second[1])
                    self.assertEqual(actions(here['Full_Press'])[0], f'key_press {key}, , ')
                    ops = layout.layer_ops(here['Full_Press'])
                    self.assertEqual(ops[-1], second)
                    self.assertEqual(sorted(ops[:-1]), sorted([('remove_layer', target), ('remove_layer', layer)]))
                    self.assertIn(('remove_layer', name(owner)), layout.layer_ops(here['release']))
                    self.assertIn(('remove_layer', layer), layout.layer_ops(here['release']))
                    self.assertEqual(layout.layer_ops(here['chord']), [('add_layer', target)])
                    self.assertEqual(here['chord']['settings'], {
                        'gyro_ratchet_button_mask': str(DEFLECT), 'gyro_ratchet_button_requireany_or_all': '0',
                        'delay_start': delay, 'interruptable': '0', 'haptic_intensity': '0'}, (layer, owner))

    def test_the_drivers_key_press_in_a_timer_layer_is_a_relay_the_chains_do_not_follow(self):
        from steam_layout.flow_model import layer_transitions
        for layout, _ in self.each():
            for layer in (*STICK_MODIFIERS, *(side[4] for side in SIDES)):
                relays = [t for t in layer_transitions(layout, layer) if t.role == 'relay']
                self.assertEqual(len(relays), 2, layer)
                self.assertEqual({t.activator for t in relays}, {'Full_Press'})

    def test_left_and_right_in_the_stick_modifiers_send_only_their_key(self):
        for layout, _ in self.each():
            for modifier in STICK_MODIFIERS:
                stick = layout.active(modifier)['joystick']['inputs']
                for direction, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
                    self.assertEqual([actions(e) for _, e in entries(stick[direction]['activators'])],
                                     [[f'key_press {key}, , ']])
                clicks = [e for kind, e in entries(stick['click']['activators']) if kind == 'chord']
                self.assertEqual(len(clicks), 2)                 # a stick can be clicked while W is held: these stay
                for chord in clicks:
                    self.assertIn(('add_layer', MARKER), layout.layer_ops(chord))

    def test_only_the_clear_to_base_removes_right_pad_layers_in_the_steering_modifier_layers(self):
        for layout, name in self.each():
            for title in map(name, STICK_MODIFIERS + MODIFIER_2):
                for source, group in layout.active(title).items():
                    for control, value in group.get('inputs', {}).items():
                        for kind, entry in entries(value.get('activators', {})):
                            pads = [t for op, t in layout.layer_ops(entry) if op == 'remove_layer' and t.startswith('RTP:')]
                            if pads:
                                self.assertEqual(kind, 'release', (title, source, control))
                                self.assertGreater(len(actions(entry)), 50, (title, source, control))


if __name__ == "__main__":
    unittest.main()
