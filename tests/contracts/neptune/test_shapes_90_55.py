"""90.55: the Steering stick's four timers are Soft Presses on the left stick's edge, the left edge cleans up with one inverted chord, and the unnecessary removes are gone.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_55 import *

class EdgeTimersShape(unittest.TestCase):
    def each(self, frozen=None):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, frozen) if frozen else layout_data(variant))
            yield layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)

    def test_no_steering_layer_states_an_outer_ring_radius_on_the_left_stick(self):
        # The default, as in the Temp Cursor Gyro layers (author, 2026-10-10).
        for layout, _ in self.each():
            steering = [t for t in layout.presets if t.startswith('Steering')]
            self.assertEqual(len(steering), 14)
            for title in steering + [t for t in layout.presets if t.endswith('Temp Cursor Gyro')]:
                self.assertNotIn('edge_binding_radius', layout.active(title)['joystick'].get('settings', {}), title)


    def test_no_start_delay_is_owned_by_a_stick_direction_in_the_steering_layers(self):
        for layout, _ in self.each():
            for title in (t for t in layout.presets if t.startswith('Steering')):
                for name, value in layout.active(title)['joystick']['inputs'].items():
                    for kind, entry in entries(value.get('activators', {})):
                        if entry.get('settings', {}).get('delay_start'):
                            # on 90.65 the edge's cleanup press started 5 ms late; the edge owned that one too
                            late = kind == 'Full_Press' and entry['settings']['delay_start'] == '5'
                            self.assertEqual((name, kind), ('edge', 'Full_Press' if late else 'Soft_Press'), title)

    def test_the_direction_keeps_the_reset_and_the_release(self):
        for layout, _ in self.each():
            for layer, direction, target, _, rate in TIMERS:
                found = list(entries(layout.active(layer)['joystick']['inputs'][direction]['activators']))
                kinds = [kind for kind, _ in found]
                self.assertEqual(kinds, ['Full_Press', 'release'] if layer in STICK_MODIFIERS else ['release', 'Full_Press', 'Full_Press'], layer)
                resets = [e for kind, e in found if kind == 'Full_Press' and layout.layer_ops(e) == [('remove_layer', target)]]
                self.assertEqual([e['settings'] for e in resets], [{'hold_repeats': '1', 'repeat_rate': rate, 'interruptable': '0'}], layer)

    def test_up_and_down_in_the_driver_layers_hold_one_chord_on_the_driver_and_no_cleanup(self):
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
                    mask = int(settings['gyro_ratchet_button_mask'])
                    self.assertEqual(bin(mask).count('1'), 1)                                   # the driver alone:
                    self.assertTrue(mask & guard and not mask & DEFLECT, (owner, direction))    # no deflect, as 90.53 had
                    self.assertEqual((settings['hold_repeats'], settings['repeat_rate'], settings['interruptable']),
                                     ('1', '50', '0'))

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
