"""90.44: inward Entry Guard recovery, quiet drivers and retained stateful layers."""
import unittest

from tests.scenario import ScenarioCase, scenario
from tests.test_scenarios_90_43 import DRIVERS, GUARD, MODIFIERS, home
from tests.test_steering_entry_quiet_drivers import gyro_settings


ORDERS = (('L1', 'R1'), ('R1', 'L1'))
CURSOR = 'Cursor Gyro'


def enter_with_drivers(pad, drivers):
    pad.hold('Start').click('LS')
    for driver in drivers:
        pad.hold(driver)
    return pad.mark().let_go('Start')


def toggle(pad, first, second, released, gap=30):
    last = second if released == first else first
    return pad.hold(first).wait(30).hold(second).wait(30).let_go(released).wait(gap).let_go(last).wait(400)


class EntryGuardDriverEdge(ScenarioCase):
    @scenario('90.44 E1', rules=('R111', 'R137'), rests=('A5', 'A6', 'A19', 'A54'), either=('A9', 'A32'))
    def test_both_carried_drivers_disarm_centered_entry_without_clearing_steering(self):
        for gyro in (False, True):
            for drivers in ORDERS:
                for pad in self.each(start=home(gyro)):
                    enter_with_drivers(pad, drivers).wait(350)
                    self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                    self.assertEqual(pad.has('Gyro'), gyro)
                    self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                    self.assertEqual(pad.seen('remove').count(('remove', GUARD)), 1)
                    self.assertFalse(any(GUARD in detail for _, detail in pad.seen('haptic')))

    @scenario('90.44 E2', rules=('R111', 'R137'), rests=('A5', 'A6', 'A19', 'A54'), either=('A9', 'A32'))
    def test_deflected_both_driver_entry_hands_off_without_exposing_the_steering_clear(self):
        for gyro in (False, True):
            for drivers in ORDERS:
                for direction in ('up', 'down'):
                    for pad in self.each(start=home(gyro)):
                        pad.push('LS', direction)
                        enter_with_drivers(pad, drivers).wait(250)
                        # Since 90.46 both held drivers can acquire a repeating
                        # self-chord entry and continue into Mod 2. The explicit
                        # driver handoff removes Guard without exposing the clear.
                        self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                        self.assertNotIn(('remove', 'Steering'), pad.seen('remove'))
                        # Since 90.53 a stick layer binds both drivers, and here both were down before it
                        # landed: neither press is fresh, so Modifier 2 waits for the stick to come back
                        # (the accepted edge of the shared stick modifier, author 2026-10-11).
                        pad.mark().recentre('LS').wait(350)
                        self.assertTrue(any(': Modifier 2' in title for title in pad.stack))
                        self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                        self.assertEqual(pad.has('Gyro'), gyro)
                        self.assertEqual(pad.seen('beep'), [])

    @scenario('90.44 E3', rules=('R111', 'R137', 'R148'), rests=('A19', 'A25', 'A54'), either=('A9', 'A32'))
    def test_reexposed_guard_recovers_after_a_timed_window_with_both_drivers_held(self):
        for gyro in (False, True):
            for drivers in ORDERS:
                for window in ('LST: Double Tap', 'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap'):
                    for pad in self.each(start=(*home(gyro), 'Steering', GUARD, window)):
                        pad.hold(*drivers).wait(100)
                        self.assertTrue(pad.has(GUARD, window))
                        pad.mark().wait(400)
                        self.assertTrue(pad.has('Steering') and pad.lacks(GUARD, window))
                        self.assertEqual(pad.has('Gyro'), gyro)
                        self.assertEqual(pad.seen('beep'), [])
                        # The new repeating entries now reach Mod 2 after the
                        # window. Its existing delayed cover still gives one
                        # bump; neither Guard nor the driver entry gives one.
                        mod2 = next(title for title in pad.names() if ': Modifier 2' in title)
                        second = mod2.split('!')[1].split(':')[0]
                        source, name = pad.control(second)
                        self.assertEqual(pad.seen('haptic'), [
                            ('haptic', f'1 {pad.title(mod2)} {source}/{name}')])

    @scenario('90.44 E4', rules=('R137', 'R171'), rests=('A4', 'A19', 'A36', 'A54'), either=('A9', 'A32'))
    def test_single_driver_handoffs_remain_quiet_for_carried_and_fresh_inputs(self):
        for gyro in (False, True):
            for driver, owner in DRIVERS.items():
                for carried in (False, True):
                    for pad in self.each(start=home(gyro)):
                        if carried:
                            enter_with_drivers(pad, (driver,)).wait(80)
                        else:
                            pad.enter_steering(settle=False).wait(100).mark().hold(driver).wait(80)
                        self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD))
                        self.assertFalse(any(pad.title(owner) in detail or GUARD in detail
                                             for _, detail in pad.seen('haptic')))
                        pad.mark().let_go(driver).wait(300)
                        self.assertTrue(pad.has('Steering') and pad.lacks(owner, GUARD))
                        self.assertEqual(pad.has('Gyro'), gyro)
                        self.assertEqual(pad.seen('haptic', 'beep'), [])


class QuietSteeringDrivers(ScenarioCase):
    @scenario('90.44 H1', rules=('R148', 'R161'), rests=('A6', 'A16', 'A49', 'A53'), either=('A9', 'A32'))
    def test_modifier_release_and_delayed_wheel_step_are_silent(self):
        for gyro in (False, True):
            for driver, owner in DRIVERS.items():
                for direction, modifier in MODIFIERS.items():
                    for pad in self.each(start=(*home(gyro), 'Steering')):
                        pad.mark().hold(driver).push('LS', direction).wait(40)
                        self.assertTrue(pad.has(owner, modifier))
                        pad.recentre('LS').wait(220)
                        wheel = 'mouse_wheel SCROLL_UP' if direction == 'up' else 'mouse_wheel SCROLL_DOWN'
                        self.assertIn(wheel, pad.typed())
                        self.assertTrue(pad.has('Steering', owner) and pad.lacks(modifier))
                        self.assertEqual(pad.seen('haptic', 'beep'), [])
                        pad.let_go(driver).lift('LS').wait(300)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))

    @scenario('90.44 S1', rules=('R133', 'R161'), rests=('A6', 'A7', 'A49'), either=('A9', 'A32'))
    def test_centered_mod2_cleanup_permits_the_still_held_driver_to_reacquire(self):
        for gyro in (False, True):
            for first, second in ORDERS:
                for pad in self.each(start=(*home(gyro), 'Steering')):
                    pad.hold(first).wait(30).hold(second).wait(30).mark().let_go(second).wait(120)
                    self.assertTrue(pad.has('Steering', DRIVERS[first]))
                    self.assertFalse(any(': Modifier 2' in title for title in pad.stack))
                    self.assertFalse(pad.has('Gyro'))
                    self.assertEqual(pad.seen('beep', 'haptic'), [])
                    pad.let_go(first).wait(300)
                    self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))

    @scenario('90.44 S2', rules=('R133', 'R161'), rests=('A7', 'A16', 'A25'), either=('A9', 'A32'))
    def test_covered_mod2_use_preserves_steering_and_missed_release_recovers(self):
        for gyro in (False, True):
            for first, second in ORDERS:
                for released, missed in ((first, False), (second, False), (first, True)):
                    for pad in self.each(start=(*home(gyro), 'Steering')):
                        pad.hold(first).wait(30).hold(second).wait(300).mark().tap('A')
                        if missed:
                            pad.miss(first, second).touch('RS').wait(300)
                        else:
                            last = second if released == first else first
                            pad.let_go(released).wait(30).let_go(last).wait(300)
                        pad.lift('LS').lift('RS').wait(300)
                        self.assertTrue(pad.has('Steering'))
                        self.assertFalse(any(': Modifier 2' in title for title in pad.stack))
                        self.assertFalse(any(title.endswith(': Tap Cover') for title in pad.stack))
                        self.assertEqual(pad.seen('beep'), [])

    @scenario('90.44 S3', rules=('R133', 'R161'), rests=('A6', 'A7', 'A49', 'A53'), either=('A9', 'A32'))
    def test_full_direction_after_mod2_cleanup_still_uses_the_separate_steering_clear(self):
        for gyro in (False, True):
            for first, second in ORDERS:
                for direction in ('up', 'down'):
                    for pad in self.each(start=(*home(gyro), 'Steering')):
                        pad.hold(first).wait(30).hold(second).wait(30).let_go(second).wait(120)
                        pad.let_go(first).wait(200).mark().push('LS', direction).wait(200)
                        self.assertTrue(pad.lacks('Steering'))
                        self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                        self.assertEqual(len(pad.seen('haptic')), 1)

    @scenario('90.44 S4', rules=('R133', 'R161'), rests=('A6', 'A7', 'A49', 'A53'), either=('A9', 'A32'))
    def test_full_direction_carried_through_mod2_cleanup_exposes_the_independent_clear(self):
        for gyro in (False, True):
            for first, second in ORDERS:
                for direction in ('up', 'down'):
                    for pad in self.each(start=(*home(gyro), 'Steering')):
                        mod2 = f'Steering | {first}!{second}: Modifier 2'
                        pad.hold(first).wait(30).hold(second).wait(30).push('LS', direction).wait(30)
                        self.assertTrue(pad.has('Steering', mod2))
                        pad.mark().let_go(second).wait(200)
                        self.assertTrue(pad.lacks('Steering', mod2))
                        self.assertFalse(any(title.startswith('Steering | ') for title in pad.stack))
                        self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                        clear_haptics = [detail for _, detail in pad.seen('haptic')
                                         if 'Steering joystick/' in detail]
                        self.assertEqual(len(clear_haptics), 1)
                        removals = pad.seen('remove')
                        self.assertLess(removals.index(('remove', pad.title(mod2))),
                                        removals.index(('remove', 'Steering')))
                        pad.let_go(first).lift('LS').lift('RS').wait(400)
                        self.assertEqual(pad.stack, pad.layers('Base'))


class RetainedCursorGyro(ScenarioCase):
    @scenario('90.44 C1', rules=('R159', 'R161'), rests=('A7', 'A49'), either=('A9', 'A32'))
    def test_short_gestures_toggle_gyro_off_and_on_while_retaining_cursor_in_every_order(self):
        for first, second in ORDERS:
            for released in (first, second):
                for gap in (0, 51):
                    for pad in self.each(start=('Base', 'Gyro', CURSOR)):
                        for gyro in (False, True):
                            pad.mark()
                            toggle(pad, first, second, released, gap)
                            expected = ('Base', CURSOR, 'Gyro') if gyro else ('Base', CURSOR)
                            self.assertEqual(pad.stack, pad.layers(*expected))
                            self.assertEqual(pad.seen('beep'), [('beep', 'Gyro')])
                            self.assertEqual(pad.seen('haptic'), [])
                            self.assertNotIn(('remove', CURSOR), pad.seen('remove'))
                            self.assertNotIn(('add', CURSOR), pad.seen('add'))
                            mode, settings = gyro_settings(pad.layout, pad.stack)
                            self.assertEqual(mode, 'gyro_to_mouse')
                            self.assertEqual(settings['gyro_precision_speed'], '750')
                            owner = 'Gyro' if gyro else 'Base'
                            self.assertEqual(settings['gyro_ratchet_button_mask'],
                                             pad.layout.active(owner)['gyro']['settings']['gyro_ratchet_button_mask'])

    @scenario('90.44 C2', rules=('R133', 'R159'), rests=('A7', 'A16', 'A25'), either=('A9', 'A32'))
    def test_held_cover_use_and_missed_releases_keep_cursor_and_recover_modifiers(self):
        for gyro in (False, True):
            for first, second in ORDERS:
                for released, missed in ((first, False), (second, False), (first, True)):
                    for pad in self.each(start=(*home(gyro), CURSOR)):
                        pad.hold(first).wait(30).hold(second).wait(300).tap('A').mark()
                        if missed:
                            pad.miss(first, second).touch('RS').wait(300)
                        else:
                            last = second if released == first else first
                            pad.let_go(released).wait(30).let_go(last).wait(300)
                        pad.lift('RS').wait(300)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), CURSOR))
                        self.assertEqual(pad.seen('beep'), [])

    @scenario('90.44 C3', rules=('R135', 'R158'), rests=('A6', 'A36'), either=('A9',))
    def test_deliberate_stick_and_menu_exits_still_work_after_gyro_was_toggled_off(self):
        for exit_kind in ('LS', 'RS', 'Start LS', 'Start RS', 'Select LS', 'Select RS'):
            for pad in self.each(start=('Base', 'Gyro', CURSOR)):
                toggle(pad, 'L1', 'R1', 'R1')
                self.assertEqual(pad.stack, pad.layers('Base', CURSOR))
                pad.mark()
                if exit_kind in ('LS', 'RS'):
                    other = 'RS' if exit_kind == 'LS' else 'LS'
                    pad.push(exit_kind, 'up' if exit_kind == 'LS' else None).wait(100)
                    self.assertTrue(pad.has(CURSOR))
                    pad.push(other, 'up' if other == 'LS' else None).wait(100)
                else:
                    menu, stick = exit_kind.split()
                    pad.hold(menu).click(stick).let_go(menu)
                pad.lift('LS').lift('RS').wait(400)
                self.assertEqual(pad.stack, pad.layers('Base'))
                self.assertNotIn(('add', CURSOR), pad.seen('add'))


if __name__ == '__main__':
    unittest.main()
