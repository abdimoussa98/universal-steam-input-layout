"""90.47: inherited stick touches must not expose Steering clears in windows.

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.steering_touch_windows import *

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


if __name__ == "__main__":
    unittest.main()
