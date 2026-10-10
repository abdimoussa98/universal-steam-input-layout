"""90.47: inherited stick touches must not expose Steering clears in windows."""
import copy
import json
import unittest

from steam_layout import exceptions
from steam_layout.fixes.window_routes import fix as fix_windows
from steam_layout.inheritance import audit, declared_stacks
from steam_layout.model import Layout
from tests.scenario import ROOT, VARIANTS, layout_data
from tests.test_audit_inheritance import EMPTY, act, add, build

WINDOWS = ('LST: Double Tap', 'RST: Double Tap')
DIRECTIONS = {'dpad_north': 'W', 'dpad_south': 'S'}
CONTEXTS = {('Base', 'Steering'), ('Base', 'Gyro', 'Steering')}
PREVIOUS = ROOT / 'findings/2026-10-10-ramp-menu-and-driver-chords'


def config():
    return exceptions.window(json.loads((ROOT / 'steam_layout/traced_stacks.json').read_text()),
                             exceptions.load())


class ConditionalDeclaredStacks(unittest.TestCase):
    """Scope extra coverage to the inherited input, not a release version."""

    def fixture(self, mode='dpad', inputs=None):
        return build({'Base': {'joystick': ('dpad', {'touch': act(add('Entry'))})},
                      'Steering': {'joystick': (mode, inputs or {})}, 'Entry': {}})

    def spec(self, layers=('Base', 'Steering'), owner='Base'):
        return {'stacks': [{'layers': list(layers), 'why': 'An inherited touch enters the helper family.',
                           'when_inherited': {'source': 'joystick', 'input': 'touch', 'from_layer': owner}}]}

    def test_inheritance_enables_the_stack_but_local_release_or_empty_blocks_skip_it(self):
        for override in ({'release': {'bindings': {'binding': EMPTY}}}, act(EMPTY), act('key_press W, , ')):
            with self.subTest(override=override):
                data = self.fixture(inputs={'touch': override})
                self.assertEqual(declared_stacks(Layout(data), self.spec(), {}), [])
                Layout(data).active('Steering')['joystick']['inputs'].pop('touch')
                self.assertEqual(declared_stacks(Layout(data), self.spec(), {}), [('Base', 'Steering')])

    def test_disabled_and_changed_source_modes_do_not_expose_a_lower_touch(self):
        for mode in ('disabled', 'joystick_mouse'):
            with self.subTest(mode=mode):
                self.assertEqual(declared_stacks(Layout(self.fixture(mode)), self.spec(), {}), [])

    def test_unavailable_historical_context_and_wrong_owner_do_not_activate_a_stack(self):
        layout = Layout(self.fixture())
        self.assertEqual(declared_stacks(layout, self.spec(('Base', 'Missing')), {}), [])
        self.assertEqual(declared_stacks(layout, self.spec(owner='Steering'), {}), [])
        self.assertEqual(declared_stacks(layout, self.spec(('Base',)), {}), [])

    def test_variant_mapping_applies_to_the_condition_owner_and_context(self):
        data = build({'Base': {}, 'L2: Owner': {'joystick': ('dpad', {'touch': act(add('Entry'))})},
                      'Steering': {'joystick': ('dpad', {})}, 'Entry': {}})
        spec = self.spec(('Base', 'L1: Owner', 'Steering'), owner='L1: Owner')
        self.assertEqual(declared_stacks(Layout(data), spec, {'L1': 'L2'}),
                         [('Base', 'L2: Owner', 'Steering')])

    def test_a_malformed_condition_is_an_error_not_a_silent_coverage_skip(self):
        spec = self.spec()
        spec['stacks'][0]['when_inherited']['unexpected'] = 'x'
        with self.assertRaises(ValueError):
            declared_stacks(Layout(self.fixture()), spec, {})


class SteeringTouchWindowContracts(unittest.TestCase):
    def test_only_steering_touch_nodes_and_window_directions_change_in_these_groups(self):
        for variant in VARIANTS:
            current = Layout(layout_data(variant))
            old = Layout(json.loads((PREVIOUS / f'{variant}-candidate.json').read_text()))
            with self.subTest(variant=variant):
                for source in ('joystick', 'right_joystick'):
                    expected = copy.deepcopy(old.active('Steering')[source])
                    expected['inputs'].pop('touch')
                    self.assertEqual(current.active('Steering')[source], expected)
                self.assertEqual(current.active('Steering | LS: Entry Guard'),
                                 old.active('Steering | LS: Entry Guard'))
                for window in WINDOWS:
                    expected = copy.deepcopy(old.active(window))
                    for direction, key in DIRECTIONS.items():
                        replacement = current.active(window)['joystick']['inputs'][direction]
                        self.assertEqual(replacement['activators'], {'Full_Press': {
                            'bindings': {'binding': f'key_press {key}, , '},
                            'settings': {'haptic_intensity': '0', 'interruptable': '0'}}})
                        self.assertFalse(replacement.get('disabled_activators'))
                        expected['joystick']['inputs'][direction] = copy.deepcopy(replacement)
                    self.assertEqual(current.active(window), expected)

    def test_window_audit_covers_steering_clears_with_and_without_gyro(self):
        for variant in VARIANTS:
            report = audit(layout_data(variant), config())
            with self.subTest(variant=variant):
                self.assertTrue(report['ok'])
                for window in WINDOWS:
                    blocked = report['targets'][window]['blocked']
                    for direction in DIRECTIONS:
                        self.assertTrue(CONTEXTS <= {
                            tuple(row['stack']) for row in blocked
                            if row['source'] == 'joystick' and row['input'] == direction
                            and row['from_layer'] == 'Steering' and row['kind'] == 'replaced'})

    def test_removing_either_direction_in_either_window_fails_the_window_audit(self):
        for variant in VARIANTS:
            for window in WINDOWS:
                for direction in DIRECTIONS:
                    with self.subTest(variant=variant, window=window, direction=direction):
                        data = copy.deepcopy(layout_data(variant))
                        Layout(data).active(window)['joystick']['inputs'].pop(direction)
                        report = audit(data, config())
                        self.assertFalse(report['ok'])
                        routes = report['targets'][window]['routes']
                        self.assertTrue(CONTEXTS <= {
                            tuple(row['stack']) for row in routes
                            if row['source'] == 'joystick' and row['input'] == direction
                            and row['from_layer'] == 'Steering' and row['status'] == 'open'})

    def test_old_touch_overrides_skip_new_contexts_and_do_not_change_frozen_builds(self):
        cfg = config()
        for variant in VARIANTS:
            data = json.loads((PREVIOUS / f'{variant}-candidate.json').read_text())
            layout = Layout(data)
            with self.subTest(variant=variant):
                for window in WINDOWS:
                    self.assertTrue(all(direction not in layout.active(window)['joystick']['inputs']
                                        for direction in DIRECTIONS))
                    self.assertEqual(declared_stacks(layout, cfg['targets'][window], {}), [])
                original = copy.deepcopy(data)
                self.assertEqual(fix_windows(data, cfg), {'changed': []})
                self.assertEqual(data, original)


if __name__ == '__main__':
    unittest.main()
