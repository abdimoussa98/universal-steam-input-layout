"""90.46: ramp-owned menu exits and repeating Steering driver entries."""
import unittest

from tests.scenario import ScenarioCase, scenario, old_inverted_chord
from tests.test_scenarios_90_43 import DRIVERS, GUARD, MODIFIERS, RAMP, home
from tests.test_scenarios_90_44 import ORDERS, enter_with_drivers


STAGES = ((RAMP[0], 0), (RAMP[1], 5), (RAMP[2], 255))
HOMES = (('Base',), ('Base', 'Gyro'), ('Base', 'Steering'))
MENUS = (('Start', 'Right', 'TAB'), ('Select', 'Left', 'ESCAPE'))


def menu_title(start, side, suffix):
    prefix = 'Stateful | ' if 'Steering' in start else ''
    return f'{prefix}Menu {side}: {suffix}'


class RepeatingSteeringDrivers(ScenarioCase):
    @scenario('90.46 E1', rules=('R114', 'R137', 'R171'),
              rests=('A4', 'A6', 'A36', 'A54'), either=('A9', 'A32'))
    def test_single_fresh_and_carried_drivers_acquire_and_release_quietly(self):
        for gyro in (False, True):
            for driver, owner in DRIVERS.items():
                for carried in (False, True):
                    for pad in self.each(start=home(gyro)):
                        if carried:
                            enter_with_drivers(pad, (driver,)).wait(150)
                        else:
                            pad.enter_steering(settle=False).wait(100).mark().hold(driver).wait(150)
                        self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD))
                        self.assertFalse(any(pad.title(owner) in detail or GUARD in detail
                                             for _, detail in pad.seen('haptic')))
                        self.assertNotIn(('remove', 'Steering'), pad.seen('remove'))
                        pad.mark().let_go(driver).wait(300)
                        # The entry click leaves the left thumb resting. Since
                        # 90.47 Steering inherits its ordinary touch helpers.
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering',
                                                              'LST: Entry Point', 'LST: Tap Cover'))
                        pad.lift('LS').wait(300)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))
                        self.assertEqual(pad.seen('beep', 'haptic'), [])
                        self.assertEqual(pad.down(), [])

    @scenario('90.46 E2', rules=('R114', 'R137', 'R171'),
              rests=('A4', 'A6', 'A36', 'A54'), either=('A9', 'A32'), frozen='90.61')
    def test_both_fresh_and_carried_drivers_reach_mod2_in_either_order(self):
        # On 90.61: one driver layer under Modifier 2. Since 90.62 the second driver's layer is there too
        # (scenario 90.62 R1).
        for gyro in (False, True):
            for order in ORDERS:
                for carried in (False, True):
                    for pad in self.each(start=home(gyro)):
                        if carried:
                            enter_with_drivers(pad, order).wait(150)
                        else:
                            pad.enter_steering(settle=False).wait(100).mark()
                            pad.hold(order[0]).wait(30).hold(order[1]).wait(150)
                        self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                        self.assertEqual(sum(': Modifier 2' in title for title in pad.stack), 1)
                        self.assertEqual(sum(': W Key' in title or ': S Key' in title
                                             for title in pad.stack), 1)
                        self.assertNotIn(('remove', 'Steering'), pad.seen('remove'))
                        # Steering entry may pulse; driver entries themselves remain quiet.
                        self.assertFalse(any('Steering | ' in detail for _, detail in pad.seen('haptic')))

    @scenario('90.46 E3', rules=('R114', 'R133', 'R161'),
              rests=('A6', 'A7', 'A16', 'A36', 'A49'), either=('A9', 'A32'))
    def test_centered_mod2_reacquires_the_remaining_driver_for_each_release_order(self):
        # A full held up/down direction still has the independent Steering clear
        # exposure documented by 90.44 S4; this checks centered reacquisition.
        for gyro in (False, True):
            for first, second in ORDERS:
                for released in (first, second):
                    for covered in (False, True):
                        for pad in self.each(start=(*home(gyro), 'Steering')):
                            pad.hold(first).wait(30).hold(second).wait(30)
                            if covered:
                                pad.wait(250).tap('A')
                            held = second if released == first else first
                            pad.mark().let_go(released).wait(150)
                            self.assertTrue(pad.has('Steering', DRIVERS[held]))
                            self.assertFalse(any(': Modifier 2' in title for title in pad.stack))
                            self.assertEqual(pad.seen('beep', 'haptic'), [])
                            pad.let_go(held).lift('LS').lift('RS').wait(400)
                            self.assertTrue(pad.has('Steering'))
                            self.assertFalse(any(title.startswith('Steering | ') for title in pad.stack))
                            self.assertEqual(pad.down(), [])

    @old_inverted_chord
    @scenario('90.46 E4', rules=('R114', 'R137', 'R171'),
              rests=('A5', 'A6', 'A10', 'A36', 'A53'), either=('A9', 'A32'))
    def test_first_or_carried_direction_stays_protected_until_an_explicit_driver_handoff(self):
        for gyro in (False, True):
            for direction, modifier in MODIFIERS.items():
                for carried in (False, True):
                    for driver, owner in DRIVERS.items():
                        for pad in self.each(start=home(gyro)):
                            if carried:
                                pad.push('LS', direction)
                            pad.enter_steering(settle=False).wait(100)
                            if not carried:
                                pad.push('LS', direction)
                            pad.wait(250)
                            self.assertTrue(pad.has('Steering', GUARD))
                            pad.mark().hold(driver).wait(150)
                            self.assertTrue(pad.has('Steering', owner, modifier) and pad.lacks(GUARD))
                            self.assertNotIn(('remove', 'Steering'), pad.seen('remove'))
                            self.assertEqual(pad.seen('beep', 'haptic'), [])
                            pad.recentre('LS').wait(250).let_go(driver).lift('LS').wait(400)
                            self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))


class RampMenuExits(ScenarioCase):
    @scenario('90.46 R1', rules=('R110', 'R114', 'R140'),
              rests=('A6', 'A7', 'A16', 'A36'), either=('A9', 'A32'))
    def test_either_menu_clears_every_ramp_stage_and_preserves_tap_or_hold(self):
        for start in HOMES:
            for stage, delay in STAGES:
                for menu, side, key in MENUS:
                    for hold in (False, True):
                        for pad in self.each(start=start):
                            pad.push('RS').wait(delay)
                            self.assertTrue(pad.has(stage))
                            pad.mark().hold(menu)
                            self.assertTrue(pad.lacks(*RAMP))
                            self.assertTrue(pad.has(menu_title(start, side, 'Entry Point')))
                            self.assertEqual(pad.seen('beep'), [])
                            pad.wait(250 if hold else 30)
                            self.assertTrue(pad.lacks(*RAMP))
                            self.assertTrue(pad.has('Menu Buttons: Right Stick Guard'))
                            self.assertFalse(pad.has(menu_title(start, side, 'Fn Layer')))
                            self.assertEqual(pad.has('Menu Buttons: Tap Cover'), hold)
                            # Let the existing tap window finish before lifting
                            # the thumb; that lift deliberately cancels the window.
                            pad.let_go(menu).wait(450)
                            self.assertEqual(pad.typed(), [] if hold else [key])
                            pad.lift('RS').wait(450)
                            self.assertEqual(pad.stack, pad.layers(*start))

    @scenario('90.46 R2', rules=('R110', 'R114', 'R140'),
              rests=('A6', 'A7', 'A11', 'A16', 'A36', 'A37'), either=('A9', 'A32'))
    def test_menu_cleanup_with_a_held_firing_button_keeps_one_mouse_press(self):
        for start in HOMES:
            for stage, delay in STAGES:
                for fire in ('LF', 'RF'):
                    for menu, side, _ in MENUS:
                        for pad in self.each(start=start):
                            pad.push('RS').wait(delay)
                            self.assertTrue(pad.has(stage))
                            pad.hold(fire).mark().hold(menu).wait(250)
                            self.assertTrue(pad.lacks(*RAMP))
                            self.assertTrue(pad.has(menu_title(start, side, 'Entry Point'),
                                                    'Menu Buttons: Right Stick Guard',
                                                    'Menu Buttons: Tap Cover'))
                            self.assertFalse(pad.has(menu_title(start, side, 'Fn Layer')))
                            mouse = 'mouse_button LEFT' if fire == 'LF' else 'mouse_button RIGHT'
                            self.assertEqual(pad.down(), [mouse])
                            self.assertEqual(pad.typed(), [])
                            self.assertEqual(pad.seen('beep'), [])
                            pad.let_go(menu).lift('RS').let_go(fire).wait(450)
                            self.assertEqual(pad.stack, pad.layers(*start))

    @scenario('90.46 R5', rules=('R110', 'R114', 'R140'),
              rests=('A6', 'A7', 'A14', 'A16', 'A36'), either=('A9', 'A32'))
    def test_recentering_after_ramp_cleanup_allows_the_normal_menu_tap_and_fn_hold(self):
        for start in HOMES:
            for stage, delay in STAGES:
                for menu, side, key in MENUS:
                    for hold in (False, True):
                        for pad in self.each(start=start):
                            pad.push('RS').wait(delay)
                            self.assertTrue(pad.has(stage))
                            pad.mark().hold(menu).wait(30)
                            self.assertTrue(pad.lacks(*RAMP))
                            pad.recentre('RS').wait(250 if hold else 30)
                            self.assertTrue(pad.lacks(*RAMP, 'Menu Buttons: Right Stick Guard'))
                            self.assertEqual(pad.has(menu_title(start, side, 'Fn Layer')), hold)
                            pad.let_go(menu).wait(450)
                            self.assertEqual(pad.typed(), [] if hold else [key])
                            self.assertEqual(pad.seen('beep'), [])
                            pad.lift('RS').wait(450)
                            self.assertEqual(pad.stack, pad.layers(*start))

    @old_inverted_chord
    @scenario('90.46 R3', rules=('R110', 'R114', 'R137', 'R161'),
              rests=('A6', 'A7', 'A36'), either=('A9', 'A32'))
    def test_start_and_stick_click_enter_steering_from_every_ramp_stage_without_residue(self):
        for gyro in (False, True):
            for stage, delay in STAGES:
                for pad in self.each(start=home(gyro)):
                    pad.push('RS').wait(delay)
                    self.assertTrue(pad.has(stage))
                    pad.hold('Start')
                    self.assertTrue(pad.lacks(*RAMP))
                    pad.click('LS').let_go('Start').wait(150)
                    self.assertTrue(pad.has('Steering', GUARD) and pad.lacks(*RAMP))
                    self.assertEqual(pad.has('Gyro'), gyro)
                    pad.mark().hold('R1').wait(150)
                    self.assertTrue(pad.has('Steering', DRIVERS['R1']) and pad.lacks(GUARD, *RAMP))
                    self.assertFalse(pad.gyro_off())
                    self.assertEqual(pad.seen('beep', 'haptic'), [])
                    pad.let_go('R1').lift('RS').wait(450)
                    # The left thumb used for the entry click is still down;
                    # its inherited helpers leave when that thumb lifts.
                    self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering',
                                                          'LST: Entry Point', 'LST: Tap Cover'))
                    pad.lift('LS').wait(300)
                    self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))

    @scenario('90.46 R4', rules=('R114', 'R137', 'R171'),
              rests=('A6', 'A7', 'A11', 'A36'), either=('A9', 'A32'))
    def test_ramp_owned_driver_recovery_still_clears_initial_gyro_suppression(self):
        for gyro in (False, True):
            for stage, delay in STAGES:
                for driver, owner in DRIVERS.items():
                    for pad in self.each(start=(*home(gyro), 'Steering')):
                        pad.push('RS').wait(delay)
                        self.assertTrue(pad.has(stage))
                        pad.mark().hold(driver)
                        full = 'RT full' if driver == 'R1' else 'LT full'
                        full_pull = pad.variant == 'alternative' and stage != RAMP[0]
                        if full_pull:
                            # The turning stages keep their established full-pull
                            # exit. Initial Gyro Off recovery works on the soft pull.
                            self.assertTrue(pad.has(stage) and pad.lacks(owner))
                            pad.hold(full)
                        pad.wait(150)
                        self.assertTrue(pad.has('Steering', owner) and pad.lacks(*RAMP))
                        self.assertFalse(pad.gyro_off())
                        self.assertEqual(pad.has('Gyro'), gyro)
                        self.assertEqual(pad.seen('beep', 'haptic'), [])
                        if full_pull:
                            pad.let_go(full)
                        pad.let_go(driver).lift('RS').wait(450)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))


if __name__ == '__main__':
    unittest.main()
