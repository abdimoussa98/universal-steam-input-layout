"""90.48: silent normal/Gyro two-driver gestures and Steering entry cleanup."""
import unittest
from tests.scenario import ScenarioCase, scenario
from tests.test_scenarios_90_43 import GUARD, DRIVERS, home
from tests.test_scenarios_90_44 import ORDERS, enter_with_drivers


class QuietGyroSwitch(ScenarioCase):
    @scenario('90.48 H1', rules=('R161',), rests=('A6', 'A7', 'A16', 'A49'), either=('A9', 'A32'))
    def test_quick_toggle_and_long_dual_hold_have_no_haptic_in_either_order(self):
        for gyro in (False, True):
            for first, second in ORDERS:
                for released in (first, second):
                    for duration in (30, 199, 200, 350):
                        for pad in self.each(start=home(gyro)):
                            pad.hold(first).wait(30).hold(second).wait(duration)
                            if duration >= 200:
                                self.assertTrue(pad.has('L1&R1: Tap Cover'))
                            self.assertEqual(pad.seen('haptic'), [])
                            last = second if released == first else first
                            pad.let_go(released).wait(30).let_go(last).wait(400)
                            self.assertEqual(pad.seen('haptic'), [])
                            if duration < 200:
                                self.assertEqual(pad.stack, pad.layers(*home(not gyro)))
                                self.assertEqual(pad.seen('beep'), [('beep', 'Gyro')])
                            self.assertEqual(pad.down(), [])

    @scenario('90.48 H2', rules=('R133', 'R161'), rests=('A6', 'A7', 'A16', 'A25'), either=('A9', 'A32'))
    def test_missed_dual_hold_release_recovers_without_haptic(self):
        for gyro in (False, True):
            for first, second in ORDERS:
                for pad in self.each(start=home(gyro)):
                    pad.hold(first).wait(30).hold(second).wait(250)
                    pad.miss(first, second).touch('RS').wait(300).lift('RS').wait(300)
                    self.assertFalse(any(': Modifier 2' in t or t.endswith(': Tap Cover') for t in pad.stack))
                    self.assertEqual(pad.seen('haptic'), [])
                    self.assertEqual(pad.down(), [])


class GuardHandoff(ScenarioCase):
    @scenario('90.48 E1', rules=('R114', 'R137', 'R161'),
              rests=('A4', 'A5', 'A6', 'A16', 'A36', 'A54'), either=('A9', 'A32'))
    def test_fresh_and_carried_driver_handoffs_with_full_deflection_do_not_clear(self):
        for gyro in (False, True):
            for direction in ('up', 'down'):
                for drivers in (('L1',), ('R1',), *ORDERS):
                    for carried in (False, True):
                        for pad in self.each(start=home(gyro)):
                            pad.push('LS', direction)
                            if carried:
                                enter_with_drivers(pad, drivers).wait(150)
                            else:
                                pad.enter_steering(settle=False).wait(100).mark().hold(*drivers).wait(150)
                            self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                            self.assertNotIn(('remove', 'Steering'), pad.seen('remove'))
                            self.assertEqual(pad.seen('remove').count(('remove', GUARD)), 1)
                            if len(drivers) == 1:
                                self.assertTrue(pad.has(DRIVERS[drivers[0]]))
                            pad.recentre('LS').wait(250)
                            if len(drivers) == 2:
                                # With both drivers down before the stick layer landed, Modifier 2 waits for
                                # the stick since 90.53 (the shared stick modifier's accepted edge).
                                self.assertTrue(any(': Modifier 2' in t for t in pad.stack))
                            for driver in drivers:
                                pad.let_go(driver)
                            pad.lift('LS').lift('RS').wait(400)
                            self.assertEqual(pad.down(), [])
                            self.assertTrue(pad.has('Steering'))

    @scenario('90.48 E3', rules=('R133', 'R137'), rests=('A6', 'A7', 'A25'), either=('A9', 'A32'))
    def test_missed_driver_release_after_guard_handoff_recovers(self):
        for driver in DRIVERS:
            for pad in self.each():
                pad.enter_steering(settle=False).wait(100).hold(driver).wait(150)
                self.assertTrue(pad.has('Steering', DRIVERS[driver]) and pad.lacks(GUARD))
                pad.miss(driver).lift('LS').touch('RS').wait(300).lift('RS').wait(300)
                self.assertFalse(any(': W Key' in t or ': S Key' in t or ': Modifier' in t for t in pad.stack))
                self.assertEqual(pad.down(), [])


if __name__ == '__main__':
    unittest.main()
