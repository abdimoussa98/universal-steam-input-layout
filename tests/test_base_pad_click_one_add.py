"""Base's pad clicks add the Click Entry Point with one Soft Press, checked on the generated candidates.

Builds both variants with the seventh 2026-10-03 builder and runs the fix pipeline, as the install
does (findings/2026-10-03-base-pad-click-one-add/README.md).
"""
import importlib.util
import json
from pathlib import Path
import unittest

from tools.audit_command_budget import audit_layout
from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'base_pad_click_one_add', ROOT / 'findings/2026-10-03-base-pad-click-one-add/build_candidate.py')
oa = importlib.util.module_from_spec(spec); spec.loader.exec_module(oa)
pc = oa.pc

BEFORE = '90.19'


class OneAddTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = oa.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

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

    def test_only_bases_two_pad_clicks_changed(self):
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            with self.subTest(variant=variant):
                self.assertEqual((report['added'], report['removed'], list(report['layers'])), ([], [], ['Base']))
                self.assertEqual([(row['source'], row['input'], row['what']) for row in report['layers']['Base']],
                                 [('left_trackpad', 'click', 'binding'), ('right_trackpad', 'click', 'binding')])

    def test_each_pad_click_adds_the_entry_point_once_with_the_bump_and_no_repeat(self):
        for variant, layout in self.layouts.items():
            for pad, (source, _, _) in pc.PADS.items():
                with self.subTest(variant=variant, pad=pad):
                    click = layout.active('Base')[source]['inputs']['click']['activators']
                    self.assertEqual(list(click), ['Soft_Press'])
                    soft = click['Soft_Press']
                    self.assertIsInstance(soft, dict)                                    # one entry, not a list of two
                    self.assertEqual(layout.layer_ops(soft), [('add_layer', pc.entry_point(pad))])
                    self.assertEqual(soft['settings'], {'haptic_intensity': '3'})        # the 90.13 press: no Hold to Repeat

    def test_entry_budget(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                self.assertEqual(audit_layout(data)['violations'], [])


if __name__ == '__main__':
    unittest.main()
