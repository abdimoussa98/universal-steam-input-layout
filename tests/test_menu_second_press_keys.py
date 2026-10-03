"""The menu second-press layers' stick keys, checked on the generated candidates.

Builds both variants with the second 2026-10-03 builder and runs the fix
pipeline, as the install does (findings/2026-10-03-menu-second-press-keys/README.md).
The press sequence itself is a scenario test (tests/test_scenarios_90_15.py).
"""
import importlib.util
import json
from pathlib import Path
import unittest

from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'menu_second_press_keys', ROOT / 'findings/2026-10-03-menu-second-press-keys/build_candidate.py')
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)

BEFORE = '90.14'
KEYS = {'dpad_north': 'W', 'dpad_south': 'S'}
HOLD = 'Steering | LS: Fallback Hold'
# Every layer a menu button's hold or double tap puts on the stack. None may leave stick up or down to Steering.
MENU_LAYERS = ('Menu Left: Double Tap', 'Menu Right: Double Tap', 'Steering | Menu Left: Entry Point',
               'Steering | Menu Right: Entry Point') + sp.SECOND_PRESS


class MenuSecondPressKeysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = sp.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def test_the_second_press_layers_type_w_and_s(self):
        for variant, layout in self.layouts.items():
            base = layout.active('Base')['joystick']['inputs']
            for name in sp.SECOND_PRESS:
                with self.subTest(variant=variant, layer=name):
                    stick = layout.active(name)['joystick']['inputs']
                    for direction, key in KEYS.items():
                        self.assertEqual(stick[direction]['activators'], {'Full_Press': {
                            'bindings': {'binding': f'key_press {key}, , '}, 'settings': {'interruptable': '0'}}})
                        self.assertEqual(stick[direction]['activators'], base[direction]['activators'])   # Base's own keys

    def test_nothing_else_changed(self):
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            with self.subTest(variant=variant):
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(set(report['layers']), set(sp.SECOND_PRESS))
                for rows in report['layers'].values():
                    self.assertEqual([(row['source'], row['input'], row['what']) for row in rows],
                                     [('joystick', direction, 'input added') for direction in KEYS])

    def test_no_menu_layer_leaves_stick_up_or_down_to_steering(self):
        """Steering's stick up and down add the Fallback Hold, which answers Start and Select. A layer a menu
        button keeps alive must bind both directions itself, or the hold lands on it and takes its Release."""
        for variant, layout in self.layouts.items():
            steering = layout.active('Steering')['joystick']['inputs']
            for direction in KEYS:
                self.assertIn(HOLD, json.dumps(steering[direction]), direction)      # the premise still holds
            for name in MENU_LAYERS:
                with self.subTest(variant=variant, layer=name):
                    stick = layout.active(name)['joystick']['inputs']
                    for direction, key in KEYS.items():
                        self.assertEqual(json.dumps(stick[direction]['activators']).count('_layer'), 0)
                        self.assertIn(f'key_press {key}', json.dumps(stick[direction]))


if __name__ == '__main__':
    unittest.main()
