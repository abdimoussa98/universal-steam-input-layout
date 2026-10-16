"""90.47: inherited stick touches must not expose Steering clears in windows.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.steering_touch_windows import *

class SteeringTouchWindowContracts(unittest.TestCase):
    def test_only_steering_touch_nodes_and_window_directions_change_in_these_groups(self):
        # On the 90.57 build, the last one this comparison holds on: 90.58 cut `Steering`'s exit on up and down
        # to `Steering` alone and took the ramp layers out of the Entry Guard's menu presses (R132).
        for variant in VARIANTS:
            current = Layout(frozen_layout_data(variant, '90.57'))
            old = Layout(json.loads((PREVIOUS / f'{variant}-candidate.json').read_text()))
            with self.subTest(variant=variant):
                for source in ('joystick', 'right_joystick'):
                    expected = self.without_bumper_covers(old, old.active('Steering')[source])
                    expected['inputs'].pop('touch')
                    self.assertEqual(self.without_scroll_layers(current, current.active('Steering')[source]), expected)
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

    @staticmethod
    def without_bumper_covers(layout, group):
        """The group without the removals of the two bumper Tap Covers, which Steering's exit had until 90.56."""
        covers = {str(layout.order.index(layout.presets[title]['name']) + 1) for title in layout.presets
                  if title.endswith(': Tap Cover') and title[:2] in ('L1', 'R1', 'L2', 'R2') and '&' not in title}
        assert len(covers) == 2
        group = copy.deepcopy(group)
        for item in group['inputs'].values():
            for value in item.get('activators', {}).values():
                for one in value if isinstance(value, list) else [value]:
                    binding = one['bindings']['binding']
                    if isinstance(binding, list):
                        one['bindings']['binding'] = [b for b in binding if not (
                            b.startswith('controller_action remove_layer ') and b.split()[2] in covers)]
        return group

    @staticmethod
    def without_scroll_layers(layout, group):
        """The group without the removals of the two stick scroll layers, which Steering's exit has had since 90.52."""
        new = {str(layout.order.index(layout.presets[title]['name']) + 1)
               for title in ('Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down')}
        group = copy.deepcopy(group)
        for item in group['inputs'].values():
            for value in item.get('activators', {}).values():
                for one in value if isinstance(value, list) else [value]:
                    binding = one['bindings']['binding']
                    if isinstance(binding, list):
                        one['bindings']['binding'] = [b for b in binding if not (
                            b.startswith('controller_action remove_layer ') and b.split()[2] in new)]
        return group

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


if __name__ == "__main__":
    unittest.main()
