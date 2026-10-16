"""Reference comparison and generated-layout contract for 90.37.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.menu_base_chords import *

class MenuBaseChords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = Layout(json.loads(build.REFERENCE.read_text()))


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
                    # The gyro style is each controller's own since 90.75 (R179); test_controllers checks it.
                    self.assertEqual(without_gyro_style(actual['settings']), without_gyro_style(reference['settings']))
                    self.assertEqual(actual.get('inputs', {}), reference.get('inputs', {}))


if __name__ == "__main__":
    unittest.main()
