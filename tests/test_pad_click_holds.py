"""The self-holds on the final pad click layers and the Click Entry Point's add-then-remove order.

Builds both variants with the sixth 2026-10-03 builder and runs the fix pipeline, as the install
does (findings/2026-10-03-pad-click-holds/README.md). These verify saved configuration contracts.
What Steam does with a hold is assumption A42.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from audit_command_budget import audit_layout
from convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import TARGET, Layout, bindings, entries

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'pad_click_holds', ROOT / 'findings/2026-10-03-pad-click-holds/build_candidate.py')
hd = importlib.util.module_from_spec(spec); spec.loader.exec_module(hd)
pc = hd.pc

BEFORE = '90.18'
HOLD = {'haptic_intensity': '0', 'interruptable': '0'}                    # the 90.13 self-hold: no delay, no repeat
BACKUP = {'hold_repeats': '1', 'haptic_intensity': '0', 'interruptable': '0', 'edge_binding_invert': '1'}


class HoldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = hd.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            for pad, (source, dpad, _) in pc.PADS.items():
                with self.subTest(variant=variant, pad=pad):
                    yield variant, layout, pad, source, dpad

    def test_working_layouts_are_this_build(self):
        # neptune/ is generated: a hand edit there would be lost on the next install (R156).
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
                built = json.loads(numeric)['controller_mappings']
                working = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())[
                    'controller_mappings']
                for cm in (built, working):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, working)

    def test_only_the_six_pad_click_layers_changed_and_only_on_the_pads(self):
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            with self.subTest(variant=variant):
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(set(report['layers']), {'LTP: Arrow Keys', 'RTP: Mouse Buttons', *pc.NEW})
                self.assertEqual({(row['source'], row['input']) for rows in report['layers'].values() for row in rows},
                                 {('left_trackpad', 'click'), ('right_trackpad', 'click'),
                                  ('left_trackpad', 'edge'), ('right_trackpad', 'edge')})

    def test_only_the_four_final_pad_layers_hold_and_only_themselves(self):                 # R101's exception
        for variant, layout in self.layouts.items():
            found = {}
            for title in layout.presets:
                for group in layout.active(title).values():
                    for value in group.get('inputs', {}).values():
                        for binding in bindings(value.get('activators', {})):
                            match = TARGET.search(binding)
                            if match and match.group(1) == 'hold_layer':
                                found.setdefault(title, set()).add(layout.resolve(match.group(2)))
            with self.subTest(variant=variant):
                self.assertEqual(found, {layer: {layer} for layer in hd.HELD})
            self.assertEqual(json.dumps(layout.cm['group']).count('hold_layer'), 4)         # no inactive group has one

    def test_the_hold_is_the_90_13_shape_with_the_inverted_removal_behind_it(self):
        for variant, layout, pad, source, dpad in self.each():
            old = Layout(json.loads((ROOT / f'versions/neptune/90.13/single-set-{variant}_hold-gyro_90.13.json').read_text()))
            was_hold, was_backup = old.active(dpad)[source]['inputs']['click']['activators']['Soft_Press']
            self.assertEqual((was_hold['settings'], was_backup['settings']), (HOLD, BACKUP))    # what 90.13 had
            for layer in hd.final_layers(pad):
                click = layout.active(layer)[source]['inputs']['click']['activators']
                hold, backup = click['Soft_Press']
                self.assertEqual((hold['settings'], layout.layer_ops(hold)), (HOLD, [('hold_layer', layer)]), layer)
                self.assertEqual((backup['settings'], layout.layer_ops(backup)), (BACKUP, [('remove_layer', layer)]), layer)
                self.assertNotIn('release', click)
                self.assertLessEqual(len(list(entries(click))), 3, layer)                    # R109

    def test_the_entry_point_adds_the_layer_first_and_then_removes_itself(self):
        for variant, layout, pad, source, dpad in self.each():
            entry = pc.entry_point(pad)
            inputs = layout.active(entry)[source]['inputs']
            self.assertEqual(set(inputs), {'edge', 'touch'})                                 # no click, no hold
            self.assertNotIn('hold_layer', json.dumps(layout.active(entry)))
            for soft, target in zip(inputs['edge']['activators']['Soft_Press'], hd.final_layers(pad)):
                self.assertEqual(layout.layer_ops(soft), [('add_layer', target), ('remove_layer', entry)])   # run order
                self.assertEqual((soft['settings']['hold_repeats'], soft['settings']['interruptable'],
                                  soft['settings']['haptic_intensity']), ('1', '0', '0'))

    def test_the_bumps_are_where_90_13_had_them(self):
        for variant, layout, pad, source, dpad in self.each():
            first, again = layout.active('Base')[source]['inputs']['click']['activators']['Soft_Press']
            self.assertEqual((first['settings'].get('haptic_intensity'), again['settings'].get('haptic_intensity')),
                             ('3', '0'))                                                     # the press
            press = layout.active(pc.middle(pad))[source]['inputs']['click']['activators']['Full_Press']
            self.assertEqual(press['settings'], {'haptic_intensity': '3'})                   # the output
            for layer in hd.final_layers(pad):                                               # the hold and backup are silent
                for soft in layout.active(layer)[source]['inputs']['click']['activators']['Soft_Press']:
                    self.assertEqual(soft['settings']['haptic_intensity'], '0')

    def test_entry_budget(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                self.assertEqual(audit_layout(data)['violations'], [])


if __name__ == '__main__':
    unittest.main()
