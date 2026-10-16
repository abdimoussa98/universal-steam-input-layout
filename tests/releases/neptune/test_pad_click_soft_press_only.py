"""Pad click layers moved by Soft Presses only, both adds repeating, Caps Lock on the left centre.

Builds both variants with the fourth 2026-10-03 builder and runs the fix pipeline, as the install
does (findings/2026-10-03-pad-click-soft-press-only/README.md). These verify saved configuration
contracts, not what Steam does with them.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from tools.audit_command_budget import audit_layout
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    'pad_click_soft_press_only', ROOT / 'findings/2026-10-03-pad-click-soft-press-only/build_candidate.py')
so = importlib.util.module_from_spec(spec); spec.loader.exec_module(so)
pc = so.pc

BEFORE = '90.16'
PRESSURE_EXIT = {'hold_repeats': '1', 'haptic_intensity': '0', 'interruptable': '0', 'edge_binding_invert': '1'}


class SoftPressOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = so.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            for pad, (source, dpad, _) in pc.PADS.items():
                with self.subTest(variant=variant, pad=pad):
                    yield layout, pad, source, dpad

    def test_only_the_six_pad_click_layers_changed(self):
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            with self.subTest(variant=variant):
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(set(report['layers']), {'LTP: Arrow Keys', 'RTP: Mouse Buttons', *pc.NEW})
                self.assertEqual({(row['source'], row['input']) for rows in report['layers'].values() for row in rows},
                                 {(s, i) for s in ('left_trackpad', 'right_trackpad') for i in ('click', 'edge')})

    def test_no_release_on_any_pad_click(self):
        """A Release fires at the full-click threshold. The layers are moved at the Soft Press threshold."""
        for variant, layout in self.layouts.items():
            for title in layout.presets:
                for source in ('left_trackpad', 'right_trackpad'):
                    click = layout.active(title).get(source, {}).get('inputs', {}).get('click')
                    if click:
                        with self.subTest(variant=variant, layer=title, source=source):
                            self.assertNotIn('release', click['activators'])

    def test_the_pad_click_layers_are_added_and_removed_by_soft_presses_and_the_thumb(self):
        for layout, pad, source, dpad in self.each():
            entry = pc.entry_point(pad)
            first, again = layout.active('Base')[source]['inputs']['click']['activators']['Soft_Press']
            self.assertEqual([layout.layer_ops(e) for e in (first, again)], [[('add_layer', entry)]] * 2)
            for layer, names in ((entry, [entry]), (pc.middle(pad), [entry, pc.middle(pad)]), (dpad, [entry, dpad])):
                inputs = layout.active(layer)[source]['inputs']
                commands = [(kind, layout.layer_ops(e)) for kind, e in entries(inputs['click']['activators'])
                            if layout.layer_ops(e)]
                self.assertEqual(commands, [('Soft_Press', [('remove_layer', name) for name in names])], layer)
                self.assertEqual(inputs['click']['activators']['Soft_Press']['settings'], PRESSURE_EXIT, layer)
                self.assertEqual(list(inputs['touch']['activators']), ['release'], layer)        # the thumb lifting

    def test_both_soft_presses_of_the_entry_point_repeat(self):
        for layout, pad, source, dpad in self.each():
            centre, outer = layout.active(pc.entry_point(pad))[source]['inputs']['edge']['activators']['Soft_Press']
            self.assertEqual(centre['settings'], {
                'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0',
                'activation_threshold': str(pc.CENTRE_RADIUS), 'interruptable': '0', 'edge_binding_invert': '1'})
            self.assertEqual(outer['settings'], {
                'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0', 'activation_threshold': '23000',
                'delay_start': '5', 'interruptable': '0'})
            self.assertEqual((layout.layer_ops(centre), layout.layer_ops(outer)),
                             ([('add_layer', pc.middle(pad))], [('add_layer', dpad)]))

    def test_the_centre_outputs(self):
        for layout, pad, source, dpad in self.each():
            press = layout.active(pc.middle(pad))[source]['inputs']['click']['activators']['Full_Press']
            wanted = 'key_press CAPSLOCK, , ' if pad == 'LTP' else 'mouse_button MIDDLE, , '
            self.assertEqual((actions(press), press['settings']), ([wanted], {'haptic_intensity': '3'}))
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                self.assertNotIn('SHOW_KEYBOARD', json.dumps(layout.cm['group']))

    def test_entry_budget(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                self.assertEqual(audit_layout(data)['violations'], [])


if __name__ == '__main__':
    unittest.main()
