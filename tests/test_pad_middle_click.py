"""The pad Click Entry Points and Middle Click layers, checked on the generated candidates.

Builds both variants with the 2026-10-03 builder and runs the fix pipeline, as
the install does (findings/2026-10-03-pad-middle-click/README.md). These verify
saved configuration contracts, not Steam's runtime behaviour: the ranges, the
interruption and the outputs on a held click are assumptions A39 to A41 and A10.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from tools.audit_command_budget import audit_layout
from steam_layout.fixes import apply_all
from steam_layout.model import EMPTY, Layout, actions, bindings, entries

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'pad_middle_click', ROOT / 'findings/2026-10-03-pad-middle-click/build_candidate.py')
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)

BEFORE = '90.13'                       # the last release with the centre chord and hold_layer
EXIT = {'hold_repeats': '1', 'haptic_intensity': '0', 'interruptable': '0', 'edge_binding_invert': '1'}
TRIO = ('Entry Point', 'Tap Cover', 'Temporary Gyro')
SCROLL = pc.SCROLL


def ops(layout, entry):
    return layout.layer_ops(entry)


class PadMiddleClickTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.before = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = pc.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)
            cls.before[variant] = Layout(json.loads(
                (ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text()))

    def each(self):
        for variant, layout in self.layouts.items():
            for pad, (source, dpad, chord) in pc.PADS.items():
                with self.subTest(variant=variant, pad=pad):
                    yield variant, layout, pad, source, dpad, str(chord)

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def test_the_four_layers_are_appended(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                before = [self.before[variant].titles[k] for k in self.before[variant].order]
                self.assertEqual([layout.titles[k] for k in layout.order], before + pc.NEW)

    def test_no_hold_layer_is_left(self):                                                   # R101
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                self.assertNotIn('hold_layer', json.dumps(layout.cm['group']))

    def test_a_click_adds_the_entry_point(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            hosts = [('Base', '3')] + ([(SCROLL, '0')] if pad == 'RTP' else [])
            for host, haptic in hosts:
                click = self.acts(layout, host, source, 'click')
                self.assertEqual(list(click), ['Soft_Press'], host)
                self.assertEqual(ops(layout, click['Soft_Press']), [('add_layer', pc.entry_point(pad))], host)
                # One pulse on the press, as before; the Click Entry Point adds none.
                self.assertEqual(click['Soft_Press']['settings'], {'haptic_intensity': haptic}, host)

    def test_the_entry_point_decides_on_two_repeating_soft_presses(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            group = layout.active(pc.entry_point(pad))[source]
            self.assertEqual((group['mode'], group['settings']), ('dpad', {'layer': '1'}))
            self.assertEqual(set(group['inputs']), {'edge', 'click'})
            edge = group['inputs']['edge']['activators']
            self.assertEqual(list(edge), ['Soft_Press'])
            centre, outer = edge['Soft_Press']
            # The centre range: inverted, not interruptible, so it has priority where the two overlap (A39).
            self.assertEqual(ops(layout, centre), [('add_layer', pc.middle(pad))])
            self.assertEqual(centre['settings'], {
                'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0',
                'activation_threshold': str(pc.CENTRE_RADIUS), 'interruptable': '0', 'edge_binding_invert': '1'})
            # The outer range: the D-pad layer's own deadzone, interruptible (no `interruptable` key).
            deadzone = layout.active(dpad)[source]['settings']['deadzone']
            self.assertEqual(ops(layout, outer), [('add_layer', dpad)])
            self.assertEqual(outer['settings'], {
                'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0', 'activation_threshold': deadzone})
            self.assertEqual(deadzone, '23000')

    def test_the_ranges_are_the_sizes_of_the_last_release(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            old = self.before[variant].active(dpad)[source]
            new = layout.active(dpad)[source]
            # The directions: the D-pad layer's group settings are untouched.
            self.assertEqual(new['settings'], old['settings'])
            for direction in ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'):
                self.assertEqual(new['inputs'][direction], old['inputs'][direction], direction)
            # The centre: an inverted edge with no stated radius, so Steam's default (A41).
            self.assertEqual(old['settings'].get('edge_binding_invert'), '1')
            self.assertNotIn('edge_binding_radius', old['settings'])

    def test_the_entry_point_has_no_haptics(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            for name, group in layout.active(pc.entry_point(pad)).items():
                self.assertFalse([k for k in group['settings'] if 'haptic' in k], name)
                for input_name, value in group['inputs'].items():
                    for _, entry in entries(value['activators']):
                        self.assertIn(entry.get('settings', {}).get('haptic_intensity', '0'), ('0',), (name, input_name))
            edge = self.acts(layout, pc.entry_point(pad), source, 'edge')['Soft_Press']
            self.assertEqual([e['settings']['haptic_intensity'] for e in edge], ['0', '0'])   # stated, not left to a default

    def test_the_middle_click_layer_is_one_button_with_the_old_centre_output(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            group = layout.active(pc.middle(pad))[source]
            self.assertEqual((group['mode'], group['settings'], set(group['inputs'])),
                             ('single_button', {'layer': '1'}, {'click'}))
            click = group['inputs']['click']['activators']
            self.assertEqual(set(click), {'Full_Press', 'Soft_Press'})
            old = self.before[variant].active(dpad)[source]['inputs']['edge']['activators']['chord']
            self.assertEqual(actions(click['Full_Press']), actions(old))
            self.assertEqual(actions(old), ['mouse_button MIDDLE, , ' if pad == 'RTP' else 'controller_action SHOW_KEYBOARD, , '])
            self.assertEqual(click['Full_Press']['settings'], {'haptic_intensity': '3'})
            self.assertEqual(old['settings']['haptic_intensity'], '3')

    def test_the_d_pad_layer_has_no_centre_and_covers_the_edge(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            inputs = layout.active(dpad)[source]['inputs']
            # Empty, so the Click Entry Point's Soft Presses aren't inherited while a direction is held.
            self.assertEqual(inputs['edge'], {'activators': {'Full_Press': {'bindings': {'binding': EMPTY + ', , '}}},
                                              'disabled_activators': {}})
            centre = 'MIDDLE' if pad == 'RTP' else 'SHOW_KEYBOARD'
            self.assertNotIn(centre, json.dumps(layout.active(dpad)))

    def test_every_exit_is_a_pressure_exit_that_removes_the_entry_point_first(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            entry = pc.entry_point(pad)
            for layer, expected in ((entry, [entry]), (pc.middle(pad), [entry, pc.middle(pad)]), (dpad, [entry, dpad])):
                soft = self.acts(layout, layer, source, 'click')['Soft_Press']
                self.assertIsInstance(soft, dict, layer)                               # one Soft Press: no self-hold
                self.assertEqual(soft['settings'], EXIT, layer)
                self.assertEqual(ops(layout, soft), [('remove_layer', t) for t in expected], layer)

    def test_stick_touches_are_guarded_by_a_thumb_on_the_pad(self):                         # R116, R133
        for variant, layout, pad, source, dpad, chord in self.each():
            entry = pc.entry_point(pad)
            for layer in (entry, pc.middle(pad), dpad):
                for stick, side in (('joystick', 'LST'), ('right_joystick', 'RST')):
                    touch = self.acts(layout, layer, stick, 'touch')
                    self.assertEqual(set(touch), {'Full_Press', 'chord', 'release'}, layer)
                    self.assertEqual(touch['Full_Press']['settings'], {'hold_repeats': '1'})   # interruptible
                    removed = [t for _, t in ops(layout, touch['Full_Press'])]
                    self.assertEqual(removed[0], entry, layer)                           # the entry point goes first
                    self.assertIn(layer, removed)
                    self.assertEqual(touch['chord'], {'bindings': {'binding': EMPTY + ', , '},
                                                      'settings': {'chord_button': chord, 'interruptable': '0'}})
                    self.assertEqual(ops(layout, touch['release']),
                                     [('remove_layer', f'{side}: {part}') for part in TRIO])

    def test_the_whole_layout_clears_name_the_new_layers(self):
        for variant, layout in self.layouts.items():
            clears = [e for group in layout.cm['group'] for value in group.get('inputs', {}).values()
                      for _, e in entries(value.get('activators', {}))
                      if sum(1 for b in actions(e) if 'remove_layer' in b) > 60]
            with self.subTest(variant=variant):
                self.assertEqual(len(clears), 10)                     # eight stick clicks and the two Modifier 2 taps
                for entry in clears:
                    removed = {t for op, t in ops(layout, entry) if op == 'remove_layer'}
                    self.assertLessEqual(set(pc.NEW), removed)

    def test_circular_scroll_removes_the_click_layers_with_the_d_pad_layer(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                wanted = [('remove_layer', t) for t in (pc.entry_point('RTP'), pc.middle('RTP'),
                                                        'RTP: Mouse Buttons', SCROLL)]
                self.assertEqual(ops(layout, self.acts(layout, SCROLL, 'right_trackpad', 'touch')['release']), wanted)
                for stick in ('joystick', 'right_joystick'):
                    self.assertEqual(ops(layout, self.acts(layout, SCROLL, stick, 'touch')['Full_Press']), wanted)

    def test_the_outputs_keep_their_haptics(self):
        for variant, layout, pad, source, dpad, _ in self.each():
            for name, value in layout.active(dpad)[source]['inputs'].items():
                for _, entry in entries(value['activators']):
                    commands = list(bindings({'x': entry}))
                    haptic = entry.get('settings', {}).get('haptic_intensity')
                    if any(c.startswith(('key_press', 'mouse_button')) for c in commands):
                        self.assertEqual(haptic, '3', name)                              # arrows, Back, Forward
                    elif any(c.startswith('mouse_wheel') for c in commands):
                        self.assertEqual(haptic, '0', name)                              # scroll

    def test_entry_budget(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                self.assertEqual(audit_layout(data)['violations'], [])


if __name__ == '__main__':
    unittest.main()
