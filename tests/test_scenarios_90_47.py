"""90.47: quiet Temp Cursor adds and safe stick-touch inheritance in Steering."""
import unittest

from tests.scenario import ScenarioCase, scenario, old_inverted_chord
from tests.test_scenarios_90_43 import DRIVERS, GUARD, MODIFIERS, RAMP, home


TOUCHES = (('LS', 'LST'), ('RS', 'RST'))
WINDOWS = ('LST: Double Tap', 'RST: Double Tap')


def touch_helper(pad, stick, kind):
    """Keep the thumb down with one of the ordinary touch helpers active."""
    pad.touch(stick).wait(200 if kind == 'cover' else 30)
    if kind == 'temporary':
        pad.lift(stick).wait(30).touch(stick).wait(30)
    return pad


class QuietTempCursorAdds(ScenarioCase):
    @scenario('90.47 H1', rules=('R120',), rests=('A6', 'A16'))
    def test_both_ordinary_and_gyro_modifiers_apply_the_cursor_silently_at_200_ms(self):
        for gyro in (False, True):
            for side, owner in (('L1', 'L1: Modifier 0'), ('R1', 'R1: Modifier 1')):
                for pad in self.each(start=home(gyro)):
                    parent = ('Gyro | ' if gyro else '') + owner
                    cursor = f'{side}: Temp Cursor Gyro'
                    pad.hold(side).wait(199)
                    self.assertTrue(pad.has(parent) and pad.lacks(cursor))
                    pad.wait(1)
                    self.assertTrue(pad.has(parent, cursor))
                    pad.wait(600)
                    self.assertEqual(pad.seen('beep', 'haptic'), [])
                    pad.let_go(side).wait(300)
                    self.assertEqual(pad.stack, pad.layers(*home(gyro)))
                    self.assertEqual((pad.typed(), pad.down()), ([], []))


class SteeringStickTouches(ScenarioCase):
    @scenario('90.47 T1', rules=('R120', 'R148'), rests=('A4', 'A6', 'A16'), either=('A9',))
    def test_each_stick_inherits_hold_and_double_tap_after_entry_protection(self):
        for stick, prefix in TOUCHES:
            for kind in ('cover', 'temporary'):
                for gyro in (False, True):
                    for pad in self.each(start=home(gyro)):
                        # Consume the protected movement, then lift the thumb
                        # before starting a new touch gesture.
                        pad.enter_steering().lift('LS').wait(300).mark()
                        touch_helper(pad, stick, kind)
                        target = f'{prefix}: ' + ('Tap Cover' if kind == 'cover' else 'Temporary Gyro')
                        self.assertTrue(pad.has('Steering', f'{prefix}: Entry Point', target))
                        self.assertTrue(pad.lacks(GUARD, *WINDOWS))
                        self.assertEqual(pad.seen('beep'), [])
                        # Stick double-tap feedback remains; this release only
                        # quiets the bumper/trigger Temp Cursor application.
                        self.assertEqual(len(pad.seen('haptic')), int(kind == 'temporary'))
                        pad.lift(stick).wait(400)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))
                        self.assertEqual(pad.down(), [])

    @old_inverted_chord
    @scenario('90.47 T2', rules=('R137',), rests=('A6', 'A7', 'A10', 'A53'), either=('A9', 'A32'))
    def test_resting_thumbs_do_not_bypass_the_guard_but_resume_helpers_after_disarming(self):
        for gyro in (False, True):
            for direction in ('up', 'down'):
                for carried in (False, True):
                    for pad in self.each(start=home(gyro)):
                        pad.touch('LS').touch('RS')
                        if carried:
                            pad.push('LS', direction)
                        pad.enter_steering(settle=False).wait(300).mark()
                        if not carried:
                            pad.push('LS', direction)
                        pad.wait(300)
                        self.assertTrue(pad.has('Steering', GUARD))
                        self.assertTrue(pad.lacks('LST: Entry Point', 'RST: Entry Point'))
                        self.assertEqual(pad.seen('beep', 'haptic'), [])
                        pad.recentre('LS').wait(300)
                        self.assertTrue(pad.has('Steering', 'LST: Entry Point', 'RST: Entry Point'))
                        self.assertTrue(pad.lacks(GUARD))
                        pad.lift('LS').lift('RS').wait(400)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))


class StickTouchWindows(ScenarioCase):
    @scenario('90.47 W1', rules=('R140', 'R148'), rests=('A6', 'A10', 'A16', 'A53'), either=('A9', 'A32'))
    def test_plain_ws_isolates_each_window_and_a_held_full_direction_clears_only_after_expiry(self):
        for window in WINDOWS:
            for start in (('Base',), ('Base', 'Gyro'), ('Base', 'Steering'), ('Base', 'Gyro', 'Steering')):
                for part, key in (('dpad_north', 'W'), ('dpad_south', 'S')):
                    for pad in self.each(start=(*start, window)):
                        # Exercise the direction throughout the window. A
                        # second touch on its own stick is a separate early
                        # exit into Temporary Gyro, covered by T1.
                        pad.hold('LS ' + part, 'LS edge').wait(199)
                        self.assertEqual(pad.stack, pad.layers(*start, window))
                        self.assertEqual(pad.down(), [key])
                        self.assertEqual(pad.seen('add', 'remove', 'beep', 'haptic'), [])
                        pad.wait(101)
                        expected = tuple(t for t in start if t != 'Steering')
                        self.assertEqual(pad.stack, pad.layers(*expected))
                        self.assertEqual(pad.down(), [key])
                        if 'Steering' in start:
                            changes = pad.seen('remove')
                            self.assertLess(changes.index(('remove', window)),
                                            changes.index(('remove', 'Steering')))
                            self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                            self.assertEqual(len(pad.seen('haptic')), 1)
                        else:
                            self.assertEqual(pad.seen('beep', 'haptic'), [])
                        pad.let_go('LS ' + part, 'LS edge').wait(300)
                        self.assertEqual(pad.down(), [])

    @scenario('90.47 W2', rules=('R140', 'R148'), rests=('A6', 'A10', 'A16', 'A53'), either=('A9',))
    def test_a_real_right_stick_tap_protects_a_full_left_stick_push_until_its_window_expires(self):
        for direction, key in (('up', 'W'), ('down', 'S')):
            for pad in self.each(start=('Base', 'Steering')):
                pad.touch('RS').wait(30).lift('RS').mark().push('LS', direction).wait(199)
                self.assertTrue(pad.has('Steering', 'RST: Double Tap'))
                self.assertEqual(pad.down(), [key])
                self.assertEqual(pad.seen('add', 'remove', 'beep', 'haptic'), [])
                pad.wait(101)
                self.assertTrue(pad.lacks('Steering', 'RST: Double Tap'))
                self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                pad.lift('LS').wait(400)
                self.assertEqual((pad.stack, pad.down()), (pad.layers('Base'), []))

    @scenario('90.47 W3', rules=('R140', 'R114'), rests=('A6', 'A16'), either=('A9', 'A32'))
    def test_windows_keep_driver_adds_and_menus_blocked_then_held_drivers_resume(self):
        for stick, prefix in TOUCHES:
            for driver, owner in DRIVERS.items():
                for held in (False, True):
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.touch(stick).wait(30).lift(stick).mark().hold(driver).wait(30)
                        self.assertTrue(pad.has('Steering', f'{prefix}: Double Tap') and pad.lacks(owner))
                        wheel = 'mouse_wheel SCROLL_UP' if driver == 'R1' else 'mouse_wheel SCROLL_DOWN'
                        self.assertEqual(pad.typed(), [wheel])
                        if not held:
                            pad.let_go(driver)
                        pad.wait(300)
                        self.assertEqual(pad.has(owner), held)
                        self.assertEqual(pad.seen('beep', 'haptic'), [])
                        if held:
                            pad.let_go(driver).wait(300)
                        self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
            for menu in ('Start', 'Select'):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch(stick).wait(30).lift(stick).mark().tap(menu).wait(300)
                    self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                    self.assertEqual(pad.typed(), [])
                    self.assertEqual(pad.seen('beep', 'haptic'), [])


class SteeringTouchHandoffs(ScenarioCase):
    @scenario('90.47 T3', rules=('R133', 'R161'), rests=('A6', 'A7', 'A16', 'A36'), either=('A9',))
    def test_existing_helpers_allow_driver_modifiers_and_clean_up_after_release(self):
        for stick, _ in TOUCHES:
            for helper in ('entry', 'cover', 'temporary'):
                for mode in ('up', 'down', 'dual'):
                    for pad in self.each(start=('Base', 'Steering')):
                        touch_helper(pad, stick, helper).hold('R1').wait(100)
                        self.assertTrue(pad.has('Steering', DRIVERS['R1']))
                        if mode == 'dual':
                            pad.hold('L1').wait(300)
                            self.assertTrue(any(': Modifier 2' in title for title in pad.stack))
                            pad.let_go('L1').wait(150)
                            self.assertTrue(pad.has('Steering', DRIVERS['R1']))
                        else:
                            pad.push('LS', mode).wait(300)
                            self.assertTrue(pad.has('Steering', DRIVERS['R1'], MODIFIERS[mode]))
                            pad.recentre('LS').wait(250)
                        pad.let_go('R1').lift('LS').lift('RS').wait(500)
                        self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                        self.assertEqual(pad.down(), [])

    @scenario('90.47 T4', rules=('R110', 'R140', 'R161'), rests=('A6', 'A7', 'A16'), either=('A9',))
    def test_helpers_allow_ramps_and_contextual_menus_without_residue(self):
        for stick, _ in TOUCHES:
            for helper in ('entry', 'cover', 'temporary'):
                for ramp in (False, True):
                    for menu, side in (('Start', 'Right'), ('Select', 'Left')):
                        for pad in self.each(start=('Base', 'Steering')):
                            touch_helper(pad, stick, helper)
                            if ramp:
                                pad.push('RS').wait(300)
                                self.assertTrue(pad.has(RAMP[2]))
                            pad.hold(menu).wait(30)
                            self.assertTrue(pad.lacks(*RAMP))
                            self.assertTrue(pad.has('Steering', f'Stateful | Menu {side}: Entry Point'))
                            pad.let_go(menu).wait(400).lift('LS').lift('RS').wait(500)
                            self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                            self.assertEqual(pad.down(), [])

    @scenario('90.47 T5', rules=('R133', 'R161'), rests=('A6', 'A7', 'A25', 'A36'), either=('A9',))
    def test_fresh_touch_recovers_a_missed_driver_release_and_helpers_recover_a_missed_thumb_lift(self):
        for stick, _ in TOUCHES:
            for helper in ('entry', 'cover', 'temporary'):
                for pad in self.each(start=('Base', 'Steering')):
                    touch_helper(pad, stick, helper).hold('R1').wait(100).miss('R1')
                    other = 'RS' if stick == 'LS' else 'LS'
                    pad.touch(other).wait(150)
                    self.assertTrue(pad.has('Steering') and pad.lacks(DRIVERS['R1']))
                    pad.lift('LS').lift('RS').wait(500)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', 'Steering'), []))
                for pad in self.each(start=('Base', 'Steering')):
                    touch_helper(pad, stick, helper).miss(stick + ' touch').wait(300)
                    pad.touch(stick).wait(200).lift(stick).wait(500)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', 'Steering'), []))


if __name__ == '__main__':
    unittest.main()
