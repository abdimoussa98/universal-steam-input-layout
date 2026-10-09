"""Reference comparison and generated-layout contract for 90.37."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from steam_layout.model import Layout, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'menu_base_chords', ROOT / 'findings/2026-10-06-menu-base-chords/build_candidate.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class MenuBaseChords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = Layout(json.loads(build.REFERENCE.read_text()))

    def test_90_37_snapshot_is_generated_and_only_base_menu_activators_change(self):
        for variant in ('default', 'alternative'):
            with self.subTest(variant=variant):
                data = build.build(variant)
                # Frozen contract; 90.38's builder owns the live-layout check.
                working = json.loads((ROOT / f'versions/neptune/90.37/single-set-{variant}_hold-gyro_90.37.json').read_text())
                before = json.loads((ROOT / f'versions/neptune/90.36/single-set-{variant}_hold-gyro_90.36.json').read_text())
                for item in (data, working, before):
                    item['controller_mappings'].pop('title')
                    item['controller_mappings'].pop('description')
                self.assertEqual(json.dumps(data), json.dumps(working))  # stored order too (R133/R156)
                actual = Layout(working).active('Base')['switch']['inputs']
                old = Layout(before).active('Base')['switch']['inputs']
                reference = self.reference.active('Base')['switch']['inputs']
                for button in build.BUTTONS:
                    self.assertEqual(list(actual[button]['activators']), ['chord'])
                    entry = actual[button]['activators']['chord']
                    self.assertEqual(entry['settings'], reference[button]['activators']['chord']['settings'])
                    self.assertEqual(entry['bindings'], old[button]['activators']['Full_Press']['bindings'])
                    old[button] = copy.deepcopy(actual[button])
                self.assertEqual(json.dumps(before), json.dumps(working))

    def test_gyro_and_all_four_modifiers_match_july_active_settings(self):
        names = ['Base', 'Gyro', 'L1: Modifier 0', 'R1: Modifier 1',
                 'L1!R1: Modifier 2', 'R1!L1: Modifier 2']
        for variant in ('default', 'alternative'):
            layout = Layout(json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text()))
            for name in names:
                old = name if name in ('Base', 'Gyro') else '*' + name
                new = name if name in ('Base', 'Gyro') else 'Gyro | ' + name
                if variant == 'alternative':
                    new = map_title(new, {'L1': 'L2', 'R1': 'R2'})
                with self.subTest(variant=variant, layer=new):
                    actual, reference = layout.active(new)['gyro'], self.reference.active(old)['gyro']
                    self.assertEqual(actual['mode'], reference['mode'])
                    self.assertEqual(actual['settings'], reference['settings'])
                    self.assertEqual(actual.get('inputs', {}), reference.get('inputs', {}))


if __name__ == '__main__':
    unittest.main()
