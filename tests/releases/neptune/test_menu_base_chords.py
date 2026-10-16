"""Reference comparison and generated-layout contract for 90.37.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.menu_base_chords import *

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



if __name__ == "__main__":
    unittest.main()
