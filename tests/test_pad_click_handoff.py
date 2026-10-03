"""The Click Entry Point's hand-over, checked on the generated candidates.

Builds both variants with the fifth 2026-10-03 builder and runs the fix pipeline, as the install
does (findings/2026-10-03-pad-click-handoff/README.md). These verify saved configuration contracts.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from tools.audit_command_budget import audit_layout
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, bindings

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'pad_click_handoff', ROOT / 'findings/2026-10-03-pad-click-handoff/build_candidate.py')
ho = importlib.util.module_from_spec(spec); spec.loader.exec_module(ho)
pc, px = ho.pc, ho.px

BEFORE = '90.17'
PRESSURE_EXIT = {'hold_repeats': '1', 'haptic_intensity': '0', 'interruptable': '0', 'edge_binding_invert': '1'}


class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = ho.Builder(variant).finish()
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

    def test_each_soft_press_removes_the_entry_point_and_then_adds_its_layer(self):
        for layout, pad, source, dpad in self.each():
            entry = pc.entry_point(pad)
            centre, outer = layout.active(entry)[source]['inputs']['edge']['activators']['Soft_Press']
            for soft, target in ((centre, pc.middle(pad)), (outer, dpad)):
                self.assertEqual(layout.layer_ops(soft), [('remove_layer', entry), ('add_layer', target)])   # in run order
                self.assertEqual((soft['settings']['hold_repeats'], soft['settings']['repeat_rate'],
                                  soft['settings']['interruptable'], soft['settings']['haptic_intensity']),
                                 ('1', '50', '0', '0'))
            self.assertNotIn('delay_start', centre['settings'])
            self.assertEqual(outer['settings']['delay_start'], '5')

    def test_the_entry_point_binds_no_click(self):
        for layout, pad, source, dpad in self.each():
            inputs = layout.active(pc.entry_point(pad))[source]['inputs']
            self.assertEqual(set(inputs), {'edge', 'touch'})
            # What still ends it besides a hand-over: the thumb lifting, and the stick-touch cleanup.
            self.assertEqual(layout.layer_ops(inputs['touch']['activators']['release'])[0],
                             ('remove_layer', pc.entry_point(pad)))
            for stick in pc.STICKS:
                press = layout.active(pc.entry_point(pad))[stick]['inputs']['touch']['activators']['Full_Press']
                self.assertIn(('remove_layer', pc.entry_point(pad)), layout.layer_ops(press))

    def test_the_chosen_layers_no_longer_name_the_entry_point(self):
        for layout, pad, source, dpad in self.each():
            entry = pc.entry_point(pad)
            for layer in (pc.middle(pad), dpad):
                for group in layout.active(layer).values():
                    for value in group.get('inputs', {}).values():
                        self.assertFalse([b for b in bindings(value.get('activators', {})) if entry in b], layer)
                click = layout.active(layer)[source]['inputs']['click']['activators']['Soft_Press']
                self.assertEqual((click['settings'], layout.layer_ops(click)), (PRESSURE_EXIT, [('remove_layer', layer)]))
                touch = layout.active(layer)[source]['inputs']['touch']['activators']['release']
                self.assertEqual(layout.layer_ops(touch),
                                 [('remove_layer', name) for name in [layer] + list(px.UNDER[pad])])

    def test_entry_budget(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                self.assertEqual(audit_layout(data)['violations'], [])


if __name__ == '__main__':
    unittest.main()
