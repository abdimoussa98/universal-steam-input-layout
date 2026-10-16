"""The pad click layers' extra exits, the 5 ms outer delay and the haptic settings, on the generated candidates.

Builds both variants with the third 2026-10-03 builder and runs the fix pipeline, as the install
does (findings/2026-10-03-pad-click-exits/README.md). These verify saved configuration contracts.
Whether the exits fire and how many bumps a click gives are for the Deck.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from tools.audit_command_budget import audit_layout
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, entries

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    'pad_click_exits', ROOT / 'findings/2026-10-03-pad-click-exits/build_candidate.py')
px = importlib.util.module_from_spec(spec); spec.loader.exec_module(px)
pc = px.pc

BEFORE = '90.15'
PRESSURE_EXIT = {'hold_repeats': '1', 'haptic_intensity': '0', 'interruptable': '0', 'edge_binding_invert': '1'}


class PadClickExitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = px.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            for pad, (source, dpad, _) in pc.PADS.items():
                with self.subTest(variant=variant, pad=pad):
                    yield layout, pad, source, dpad

    def click_layers(self, pad, dpad):
        entry = pc.entry_point(pad)
        return ((entry, [entry]), (pc.middle(pad), [entry, pc.middle(pad)]), (dpad, [entry, dpad]))

    def test_only_base_and_the_six_pad_click_layers_changed(self):
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            with self.subTest(variant=variant):
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(set(report['layers']), {'Base', 'LTP: Arrow Keys', 'RTP: Mouse Buttons', *pc.NEW})
                self.assertEqual({row['source'] for rows in report['layers'].values() for row in rows},
                                 {'left_trackpad', 'right_trackpad'})

    def test_no_hold_layer_came_back(self):                                                  # R101
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                self.assertNotIn('hold_layer', json.dumps(layout.cm['group']))

    def test_base_adds_the_entry_point_once_with_the_bump_and_then_repeats_silently(self):
        for layout, pad, source, dpad in self.each():
            first, again = layout.active('Base')[source]['inputs']['click']['activators']['Soft_Press']
            for entry in (first, again):
                self.assertEqual(layout.layer_ops(entry), [('add_layer', pc.entry_point(pad))])
            self.assertEqual(first['settings'], {'haptic_intensity': '3'})                   # the one bump, as in 90.13
            self.assertEqual(again['settings'], {'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0'})

    def test_both_soft_presses_are_uninterruptible_and_only_the_outer_one_is_delayed(self):
        for layout, pad, source, dpad in self.each():
            centre, outer = layout.active(pc.entry_point(pad))[source]['inputs']['edge']['activators']['Soft_Press']
            self.assertEqual(layout.layer_ops(centre), [('add_layer', pc.middle(pad))])
            # No delay. It keeps its repeat: an inverted entry already true when the layer lands fires on a repeat (R114).
            self.assertEqual(centre['settings'], {
                'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0',
                'activation_threshold': str(pc.CENTRE_RADIUS), 'interruptable': '0', 'edge_binding_invert': '1'})
            self.assertEqual(layout.layer_ops(outer), [('add_layer', dpad)])
            # 5 ms, and no repeat: a delayed add fires over a held input by itself (R115).
            self.assertEqual(outer['settings'], {
                'haptic_intensity': '0', 'activation_threshold': '23000', 'delay_start': '5', 'interruptable': '0'})

    def test_every_pad_click_layer_has_three_exits(self):
        for layout, pad, source, dpad in self.each():
            under = list(px.UNDER[pad])
            for layer, names in self.click_layers(pad, dpad):
                inputs = layout.active(layer)[source]['inputs']
                click = inputs['click']['activators']
                removes = [('remove_layer', name) for name in names]
                # 1. The pad is no longer pressed: the inverted, repeating Soft Press of 90.13.
                self.assertEqual((click['Soft_Press']['settings'], layout.layer_ops(click['Soft_Press'])),
                                 (PRESSURE_EXIT, removes), layer)
                # 2. The click's Release, where 90.13 had the layer's hold of itself.
                self.assertEqual((click['release']['settings'], layout.layer_ops(click['release'])),
                                 ({'haptic_intensity': '0'}, removes), layer)
                # 3. The thumb lifts. It takes the layers the same thumb keeps under the click layer too.
                touch = inputs['touch']['activators']
                self.assertEqual(list(touch), ['release'], layer)
                self.assertEqual((touch['release']['settings'], layout.layer_ops(touch['release'])),
                                 ({'haptic_intensity': '0'}, removes + [('remove_layer', name) for name in under]), layer)
                self.assertLessEqual(len(list(entries(click))), 3, layer)                 # R109

    def test_the_click_layers_haptics(self):
        """One bump on the press (Base) and one on the output, as in 90.13. Nothing else may add one."""
        for layout, pad, source, dpad in self.each():
            entry = layout.active(pc.entry_point(pad))[source]
            self.assertEqual(entry['settings'], {'layer': '1', 'haptic_intensity_override': '0'})   # stated, not Steam's default
            for name, value in entry['inputs'].items():
                for _, e in entries(value['activators']):
                    self.assertEqual(e['settings'].get('haptic_intensity'), '0', name)
            middle = layout.active(pc.middle(pad))[source]['inputs']
            bumps = [(name, kind) for name, value in middle.items() for kind, e in entries(value['activators'])
                     if e.get('settings', {}).get('haptic_intensity', '0') != '0']
            self.assertEqual(bumps, [('click', 'Full_Press')])                               # the output alone
            for name in ('click', 'touch', 'edge'):                                          # the D-pad layer's plumbing
                for _, e in entries(layout.active(dpad)[source]['inputs'][name]['activators']):
                    self.assertEqual(e.get('settings', {}).get('haptic_intensity', '0'), '0', name)

    def test_entry_budget(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                self.assertEqual(audit_layout(data)['violations'], [])


if __name__ == '__main__':
    unittest.main()
