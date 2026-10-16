"""The stateful Cursor Gyro layer, checked on the generated candidates.

Builds both variants with the 2026-10-03 Cursor Gyro builder and runs the fix pipeline, as the
install does (findings/2026-10-03-cursor-gyro/README.md). These verify saved configuration
contracts, not Steam's runtime scheduling.
"""
import importlib.util
import json
from pathlib import Path
import re
import unittest

from tools.audit_command_budget import audit_layout
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries, map_title

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    'cursor_gyro', ROOT / 'findings/2026-10-03-cursor-gyro/build_candidate.py')
cg = importlib.util.module_from_spec(spec); spec.loader.exec_module(cg)
st = cg.st

BEFORE = '90.20'
CURSOR, GYRO = cg.CURSOR, cg.GYRO
SIDES = {'Left': 'button_menu', 'Right': 'button_escape'}
STICKS = ('joystick', 'right_joystick')
ENTRY_POINTS = [st.entry_point(side) for side in SIDES] + [cg.stateful_entry_point(side) for side in SIDES]
ALTERNATIVE = {'L1': 'L2', 'R1': 'R2'}
MOD_2 = ('Gyro | L1!R1: Modifier 2', 'Gyro | R1!L1: Modifier 2')


class CursorGyroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = cg.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def test_one_layer_is_new_and_two_are_renamed(self):
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            with self.subTest(variant=variant):
                self.assertEqual(sorted(report['added']), sorted([CURSOR] + list(cg.RENAMED.values())))
                self.assertEqual(sorted(report['removed']), sorted(cg.RENAMED))
                # The renamed layers keep their place, so no runtime ID moves; the new one is last.
                old, new = (list(d['controller_mappings']['action_layers'].values()) for d in (before, data))
                self.assertEqual([cg.RENAMED.get(layer['title'], layer['title']) for layer in old],
                                 [layer['title'] for layer in new[:-1]])
                self.assertEqual(new[-1]['title'], CURSOR)

    def test_the_layer_states_the_temp_cursor_response_and_no_gate(self):
        for variant, layout in self.each():
            gyro = layout.active(CURSOR)['gyro']
            temp = layout.active(map_title('L1: Temp Cursor Gyro', ALTERNATIVE if variant == 'alternative' else {}))['gyro']
            self.assertEqual(gyro['mode'], 'gyro_to_mouse')
            self.assertEqual(gyro['settings'], {**cg.RESPONSE, 'layer': '1'})
            self.assertEqual(gyro['settings'], temp['settings'])
            self.assertFalse([k for k in gyro['settings'] if k.startswith('gyro_ratchet')])   # Gyro underneath gates it

    def test_it_binds_only_the_gyro_the_menu_buttons_and_the_stick_edges(self):
        for variant, layout in self.each():
            sources = layout.active(CURSOR)
            self.assertEqual({source: sorted(group.get('inputs', {})) for source, group in sources.items()},
                             {'gyro': [], 'switch': ['button_escape', 'button_menu'],
                              'joystick': ['edge'], 'right_joystick': ['edge']})
            self.assertEqual((sources['joystick']['mode'], sources['right_joystick']['mode']),
                             (layout.active('Base')['joystick']['mode'], layout.active('Base')['right_joystick']['mode']))

    def test_its_menu_presses_add_the_stateful_entry_points_with_a_repeating_press(self):
        for variant, layout in self.each():
            for side, button in SIDES.items():
                acts = self.acts(layout, CURSOR, 'switch', button)
                # Clean entry (R162): no Release, delay or chord on a menu button.
                self.assertEqual(list(acts), ['Full_Press'])
                self.assertEqual(acts['Full_Press'].get('settings'), {'hold_repeats': '1'})
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('add_layer', cg.stateful_entry_point(side))])

    def test_both_sticks_out_remove_only_the_layer(self):
        for variant, layout in self.each():
            for source, (other, radius) in cg.STICKS.items():
                group = layout.active(CURSOR)[source]
                self.assertEqual(group['settings'], {'edge_binding_radius': radius, 'edge_binding_invert': '0', 'layer': '1'})
                acts = self.acts(layout, CURSOR, source, 'edge')
                self.assertEqual(list(acts), ['chord'])
                chord = acts['chord']
                # A cancellation (R135): only itself, repeating, uninterruptible, and the other stick as its only condition.
                self.assertEqual(layout.layer_ops(chord), [('remove_layer', CURSOR)])
                self.assertEqual(chord['settings'], {
                    'gyro_ratchet_button_mask': str(1 << other), 'gyro_ratchet_button_requireany_or_all': '1',
                    'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'})
                # Meant as the beep. `1 0` is the on-screen name; 90.29 moves it to `0 1` (A49).
                self.assertRegex(actions(chord)[0], r'remove_layer \S.* 1 0')

    def test_select_in_the_cross_transition_adds_gyro_and_then_the_layer(self):
        for variant, layout in self.each():
            release = self.acts(layout, st.CROSS, 'switch', 'button_menu')
            self.assertEqual(list(release), ['release'])
            self.assertEqual(layout.layer_ops(release['release']),
                             [('remove_layer', st.CROSS), ('add_layer', GYRO), ('add_layer', CURSOR)])
            self.assertEqual(release['release']['settings'], {'haptic_intensity': '3'})
            # One beep (R161): on the stateful layer's add. Written first here; the second since 90.29 (A49).
            flags = {layout.resolve(m.group(1)): m.group(2) for a in actions(release['release'])
                     if (m := re.search(r'_layer (\{\{.+?\}\}|\d+) (\d) \d', a))}
            self.assertEqual(flags, {st.CROSS: '0', GYRO: '0', CURSOR: '1'})
            # Start still enters Steering.
            start = self.acts(layout, st.CROSS, 'switch', 'button_escape')['release']
            self.assertEqual(layout.layer_ops(start)[1], ('add_layer', 'Steering'))

    def test_every_entry_point_click_clears_the_layer_and_keeps_gyro(self):
        for variant, layout in self.each():
            everything = set(layout.presets) - {'Base', GYRO}
            self.assertIn(CURSOR, everything)
            for name in ENTRY_POINTS:
                for source in STICKS:
                    ops = layout.layer_ops(self.acts(layout, name, source, 'click')['release'])
                    self.assertEqual({t for op, t in ops[:-1] if op == 'remove_layer'}, everything, (name, source))
                    if name in cg.RENAMED.values():
                        self.assertEqual(ops[-1], ('add_layer', st.CLEAR), (name, source))

    def test_the_gyro_modifier_2_quick_tap_also_removes_the_layer(self):
        for variant, layout in self.each():
            for title in MOD_2:
                name = map_title(title, ALTERNATIVE) if variant == 'alternative' else title
                clears = [layout.layer_ops(e) for group in layout.active(name).values()
                          for value in group.get('inputs', {}).values() for _, e in entries(value['activators'])
                          if ('remove_layer', GYRO) in layout.layer_ops(e)]
                self.assertEqual(len(clears), 2, name)
                for ops in clears:
                    self.assertIn(('remove_layer', CURSOR), ops)
                    self.assertEqual(ops[-1], ('remove_layer', GYRO))                      # Gyro goes last

    def test_no_other_layer_carries_the_both_sticks_exit(self):
        # Author, 2026-10-03: the exit is only in Cursor Gyro. Apart from the clears, nothing removes the layer.
        # Steering's Modifier 2 quick tap is a whole-layout clear too (R132 lets a deliberate clear keep its list).
        clears = set(ENTRY_POINTS) | set(MOD_2) | {CURSOR, 'Steering | L1!R1: Modifier 2', 'Steering | R1!L1: Modifier 2'}
        for variant, layout in self.each():
            names = {map_title(t, ALTERNATIVE) if variant == 'alternative' else t for t in clears}
            removing = {name for name in layout.presets for group in layout.active(name).values()
                        for value in group.get('inputs', {}).values() for _, e in entries(value['activators'])
                        if ('remove_layer', CURSOR) in layout.layer_ops(e)}
            self.assertEqual(removing, names)

    def test_nothing_refers_to_the_old_entry_point_titles(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                text = json.dumps(data)
                for old in cg.RENAMED:
                    self.assertNotIn(old, text)

    def test_entry_budget(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                report = audit_layout(data)
                self.assertFalse(report['violations'] or report['banned_activators'] or report['inverted_edges'])


if __name__ == '__main__':
    unittest.main()
