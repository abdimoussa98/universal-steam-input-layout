"""The Cleanup audit: what a cleanup function and a release may remove.

Tiny layouts, one rule per test, then the frozen 90.10 snapshots. The rules are in
findings/2026-10-02-cleanup-boundaries/README.md; the plan is plans/2026-10-02-cleanup-audit.md.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.cleanups import *

class SteeringConditionalOwnerTests(unittest.TestCase):
    MOD = 'Steering | LS Up: Modifier 1'
    DRIVER = 'Steering | R1: W Key'
    COVER = 'Steering | LS: Tap Cover'

    def layout(self, *, remove_owner=False, all_conditions=True, historical=False, owner_only=False):
        """Small modern Steering stack with a deflection-conditioned modifier cleanup."""
        commands = [remove(self.MOD), remove(self.COVER)]
        if remove_owner:
            commands.append(remove(self.DRIVER))
        mask = 4 if owner_only else (1 << 30) | 4
        recovery = {**press(*commands, hold_repeats=1), **on('chord', EMPTY,
            gyro_ratchet_button_mask=mask, gyro_ratchet_button_requireany_or_all=int(all_conditions))}
        clear = {direction: on('Soft_Press', remove('Steering'))
                 for direction in ('dpad_north', 'dpad_south')}
        if historical:
            clear = {direction: press(KEY) for direction in clear}
        return build({
            'Base': {'switch': (SW, {'right_bumper': press(add(self.DRIVER))})},
            'Steering': {'joystick': ('dpad', clear)},
            'Steering | LS: Entry Guard': {},
            self.DRIVER: {'switch': (SW, {
                'right_bumper': release(remove(self.DRIVER)),
                'button_b': press(add(self.MOD)),
            })},
            self.MOD: {
                'switch': (SW, {'button_a': press(add(self.COVER))}),
                'right_joystick': ('joystick_mouse', {'edge': recovery}),
                'joystick': ('dpad', {'edge': release(remove(self.MOD), remove(self.COVER))}),
            },
            self.COVER: {'joystick': ('dpad', {'edge': release(remove(self.COVER))})},
        })

    def owner_findings(self, data):
        return {(check, host, target) for check, host, target, _, _ in Cleanups(Layout(data)).findings()
                if host == self.MOD and target == self.DRIVER}

    def test_deflection_guard_must_not_remove_held_driver(self):
        self.assertEqual(self.owner_findings(self.layout(remove_owner=True)),
                         {('outside the guard', self.MOD, self.DRIVER)})
        self.assertEqual(self.owner_findings(self.layout()), set())

    def test_any_or_owner_only_guard_still_requires_driver_cleanup(self):
        for changes in ({'all_conditions': False}, {'owner_only': True}):
            with self.subTest(changes=changes):
                self.assertEqual(self.owner_findings(self.layout(**changes)),
                                 {('left below', self.MOD, self.DRIVER), ('left above', self.MOD, self.DRIVER)})
                self.assertEqual(self.owner_findings(self.layout(remove_owner=True, **changes)), set())

    def test_modifier_still_owns_its_cover(self):
        data = self.layout()
        value = Layout(data).active(self.MOD)['right_joystick']['inputs']['edge']['activators']['Full_Press']
        value['bindings']['binding'] = remove(self.MOD)
        findings = {(check, host, target) for check, host, target, _, _ in Cleanups(Layout(data)).findings()}
        self.assertIn(('left above', self.MOD, self.COVER), findings)
        self.assertNotIn(('left below', self.MOD, self.DRIVER), findings)

    def test_fix_drops_invalid_owner_and_does_not_reintroduce_it(self):
        data = self.layout(remove_owner=True)
        first = cleanup_lists.fix(data, {})
        self.assertEqual(first['remaining'], 0)
        self.assertTrue(any('drops' in change and self.DRIVER in change for change in first['changed']))
        self.assertEqual(cleanup_lists.fix(data, {}), {'changed': [], 'remaining': 0})
        self.assertEqual(self.owner_findings(data), set())

    def test_frozen_guard_without_base_soft_clear_keeps_old_generator_semantics(self):
        self.assertEqual(self.owner_findings(self.layout(historical=True)),
                         {('left below', self.MOD, self.DRIVER), ('left above', self.MOD, self.DRIVER)})
        self.assertEqual(self.owner_findings(self.layout(remove_owner=True, historical=True)), set())


if __name__ == "__main__":
    unittest.main()
