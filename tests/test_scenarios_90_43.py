"""90.43 entry protection, driver ownership during recovery, and layer beeps."""
import unittest

from tests.scenario import DIRECTIONS, ScenarioCase, scenario, old_inverted_chord

GUARD = 'Steering | LS: Entry Guard'
DRIVERS = {'R1': 'Steering | R1: W Key', 'L1': 'Steering | L1: S Key'}
MODIFIERS = {'up': 'Steering | LS Up: Modifier 1', 'down': 'Steering | LS Down: Modifier 0'}
RAMP = ('Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1')


def home(gyro):
    return ('Base', 'Gyro') if gyro else ('Base',)


def enter(pad):
    return pad.enter_steering(settle=False)


def both_home_states(case):
    for gyro in (False, True):
        for pad in case.each(start=home(gyro)):
            yield gyro, pad


def both_armed_states(case):
    for gyro, pad in both_home_states(case):
        pad.enter_steering().mark()
        yield gyro, pad


class SteeringEntryProtection(ScenarioCase):
    @scenario('90.43 E1', rules=('R137', 'R161'), rests=('A5', 'A6', 'A10', 'A49', 'A53'), either=('A9',))
    def test_a_direction_carried_into_entry_is_protected_until_released(self):
        for gyro in (False, True):
            for direction, key in (('up', 'W'), ('down', 'S')):
                for pad in self.each(start=home(gyro)):
                    pad.push('LS', direction).wait(30).mark()
                    enter(pad).wait(600)
                    self.assertTrue(pad.has('Steering', GUARD))
                    self.assertIn(key, pad.down())
                    self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                    self.assertFalse(any(GUARD in detail for _, detail in pad.seen('haptic')))
                    pad.mark().recentre('LS').wait(100)
                    self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                    self.assertEqual(pad.seen('haptic', 'beep'), [])
                    self.assertEqual(pad.has('Gyro'), gyro)

    @old_inverted_chord
    @scenario('90.43 E2', rules=('R137', 'R169', 'R170'), rests=('A7', 'A8', 'A10'))
    def test_centered_entry_and_resting_thumbs_preserve_the_first_push(self):
        for gyro in (False, True):
            for direction, key in (('up', 'W'), ('down', 'S'), ('left', 'A'), ('right', 'D')):
                for pad in self.each(start=home(gyro)):
                    pad.touch('LS').touch('RS').wait(300)
                    enter(pad).wait(500).lift('LS').lift('RS').wait(500).mark()
                    self.assertTrue(pad.has(GUARD))
                    pad.push('LS', direction).wait(500)
                    self.assertTrue(pad.has('Steering', GUARD))
                    self.assertIn(key, pad.down())
                    self.assertEqual(pad.seen('haptic', 'beep'), [])
                    pad.recentre('LS')
                    self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))

    @old_inverted_chord
    @scenario('90.43 E3', rules=('R137',), rests=('A7', 'A8', 'A10'))
    def test_a_shallow_direction_release_disarms_without_an_outer_edge(self):
        for direction, key in (('up', 'W'), ('down', 'S'), ('left', 'A'), ('right', 'D')):
            for gyro, pad in both_home_states(self):
                enter(pad).mark()
                control = 'LS ' + DIRECTIONS[direction]
                pad.hold(control).wait(60)
                self.assertTrue(pad.has(GUARD))
                self.assertIn(key, pad.down())
                self.assertNotIn(('joystick', 'edge'), pad.sim.held)
                pad.let_go(control).wait(100)
                self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                self.assertEqual(pad.seen('haptic', 'beep'), [])

    @scenario('90.43 E4', rules=('R137',), rests=('A7', 'A8', 'A53'), either=('A9',))
    def test_direction_roll_or_edge_release_can_arm_a_still_held_full_direction(self):
        # This is the selected release contract, not strict center detection.
        for gesture in ('roll', 'edge_release'):
            for gyro, pad in both_home_states(self):
                enter(pad).mark()
                if gesture == 'roll':
                    pad.push('LS', 'left').wait(30).roll('LS', 'up')
                else:
                    pad.push('LS', 'up').wait(30).let_go('LS edge')
                pad.wait(100)
                self.assertTrue(pad.lacks('Steering', GUARD))
                self.assertIn('W', pad.down())
                self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])

    @old_inverted_chord
    @scenario('90.43 E5', rules=('R137', 'R171'), rests=('A4', 'A6', 'A36'), either=('A9',))
    def test_fresh_or_carried_drivers_remove_the_guard_before_driving(self):
        for driver, layer in DRIVERS.items():
            for carried in (False, True):
                for gyro, pad in both_home_states(self):
                    if carried:
                        pad.hold('Start').click('LS').hold(driver).mark().let_go('Start')
                    else:
                        enter(pad).push('LS', 'up').mark().hold(driver)
                    pad.wait(100)
                    self.assertTrue(pad.has('Steering', layer) and pad.lacks(GUARD))
                    changes = pad.seen('add', 'remove')
                    self.assertLess(changes.index(('remove', GUARD)),
                                    changes.index(('add', pad.title(layer))))
                    self.assertEqual(pad.has('Steering | LS Up: Modifier 1'), not carried)

    @old_inverted_chord
    @scenario('90.43 E6', rules=('R137', 'R171'), rests=('A4', 'A16', 'A36'))
    def test_fresh_menu_handoffs_preserve_fn_feedback(self):
        for menu, side in (('Start', 'Right'), ('Select', 'Left')):
            for gyro, pad in both_home_states(self):
                enter(pad).mark().hold(menu).wait(200)
                entry = f'Stateful | Menu {side}: Entry Point'
                fn = f'Stateful | Menu {side}: Fn Layer'
                self.assertTrue(pad.has('Steering', fn) and pad.lacks(GUARD))
                changes = pad.seen('add', 'remove')
                self.assertLess(changes.index(('remove', GUARD)), changes.index(('add', entry)))
                self.assertEqual(pad.seen('beep'), [])
                pulses = pad.seen('haptic')
                self.assertEqual(len(pulses), 1)
                self.assertTrue(pulses[0][1].startswith('1 '))

    @scenario('90.43 E7', rules=('R137', 'R158', 'R161'), rests=('A7', 'A49'))
    def test_every_menu_click_clear_removes_guard_and_preserves_gyro(self):
        for gyro in (False, True):
            for menu in ('Start', 'Select'):
                for stick in ('LS', 'RS'):
                    for pad in self.each(start=home(gyro)):
                        enter(pad).mark().hold(menu).click(stick).let_go(menu).lift('LS').lift('RS').wait(400)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro)))
                        self.assertEqual(pad.seen('beep'), [('beep', 'Transition Set 2')])

    @old_inverted_chord
    @scenario('90.43 E8', rules=('R137',), rests=('A5', 'A7', 'A36'))
    def test_a_carried_opposite_menu_does_not_consume_first_push_protection(self):
        for gyro, pad in both_home_states(self):
            pad.hold('Start').click('LS').hold('Select').let_go('Start').wait(500).mark()
            self.assertTrue(pad.has('Steering', GUARD))
            self.assertTrue(pad.lacks('Stateful | Menu Left: Entry Point', 'Stateful | Menu Left: Fn Layer'))
            pad.let_go('Select').wait(50).hold('Select').wait(200)
            self.assertTrue(pad.lacks(GUARD))
            self.assertTrue(pad.has('Stateful | Menu Left: Fn Layer'))
            self.assertEqual(pad.seen('beep'), [])

    @old_inverted_chord
    @scenario('90.43 E9', rules=('R137',), rests=('A6', 'A7', 'A8', 'A10'))
    def test_pad_and_ramp_inputs_do_not_hide_the_protected_release(self):
        for gyro in (False, True):
            for pad in self.each(start=home(gyro)):
                enter(pad).push('LS', 'up').mark()
                pad.touch('RP').hold('RP click').touch('LP').hold('LP click').push('RS').wait(600)
                self.assertTrue(pad.has('Steering', GUARD))
                self.assertTrue(pad.lacks(*RAMP))
                self.assertFalse(any(title.startswith(('RTP:', 'LTP:')) for title in pad.stack))
                self.assertEqual(pad.down(), ['W'])
                pad.recentre('LS').wait(100)
                self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                pad.let_go('RP click', 'LP click').lift('RP').lift('LP').lift('RS').lift('LS').wait(500)
                self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))

    @old_inverted_chord
    @scenario('90.43 E10', rules=('R137',), rests=('A7', 'A10'))
    def test_left_pad_swipes_keep_plain_keys_without_helpers(self):
        for direction, key in (('left', 'ESCAPE'), ('right', 'RETURN'), ('up', 'TAB'), ('down', 'BACKSPACE')):
            for gyro, pad in both_home_states(self):
                enter(pad).mark().touch('LP').hold('LP ' + DIRECTIONS[direction]).wait(60)
                self.assertEqual(pad.typed(), [key])
                self.assertTrue(pad.has(GUARD))
                self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering', GUARD))

    @old_inverted_chord
    @scenario('90.43 E11', rules=('R137', 'R169', 'R170', 'R171'), rests=('A25',), either=('A9',))
    def test_a_missed_movement_release_recovers_on_a_real_release_or_handoff(self):
        for recovery in ('direction', 'driver', 'menu'):
            for gyro, pad in both_home_states(self):
                enter(pad).push('LS', 'up').wait(30).miss('LS dpad_north', 'LS edge', 'LS touch').wait(300)
                self.assertTrue(pad.has(GUARD))
                if recovery == 'direction':
                    pad.push('LS', 'left').recentre('LS')
                elif recovery == 'driver':
                    pad.hold('R1')
                else:
                    pad.hold('Start')
                pad.wait(100)
                self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))

    @scenario('90.43 E12', rules=('R148', 'R161'), rests=('A6', 'A10', 'A49', 'A53'), either=('A9',))
    def test_a_new_full_direction_after_disarming_clears_once_and_keeps_gyro(self):
        for gyro in (False, True):
            for direction, key in (('up', 'W'), ('down', 'S')):
                for pad in self.each(start=home(gyro)):
                    enter(pad).flick('LS', 'left').wait(100).mark().push('LS', direction).wait(600)
                    self.assertFalse(any(t == 'Steering' or t.startswith('Steering | ') for t in pad.stack))
                    self.assertEqual(pad.has('Gyro'), gyro)
                    self.assertEqual(pad.down(), [key])
                    self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                    self.assertEqual(len(pad.seen('haptic')), 1)
                    pad.lift('LS').wait(400)
                    self.assertEqual(pad.stack, pad.layers(*home(gyro)))


class SteeringModifierRecovery(ScenarioCase):
    @scenario('90.43 D1', rules=('R133', 'R170'), rests=('A6', 'A17', 'A36', 'A53'), either=('A9', 'A32'))
    def test_camera_recovery_keeps_the_held_driver_through_the_old_fifty_ms_gap(self):
        # The first push is below the outer edge; binary inputs cannot verify
        # real radial thresholds. Until 90.51 it left the modifier until RS recovery.
        # Since 90.52 the direction's own Release ends it, so no modifier is left.
        for driver, owner in DRIVERS.items():
            for direction, modifier in MODIFIERS.items():
                for gap in (0, 49, 50):
                    for gyro, pad in both_armed_states(self):
                        control = 'LS ' + DIRECTIONS[direction]
                        pad.hold(driver).touch('LS').hold(control).wait(30).let_go(control)
                        self.assertTrue(pad.has(owner) and pad.lacks(modifier))
                        pad.mark().push('RS').wait(gap)
                        self.assertTrue(pad.has(owner) and pad.lacks(modifier))
                        pad.wait(200).hold(control).wait(300)                # past the window: a fresh hold, not a second deflect
                        self.assertTrue(pad.has('Steering', owner, modifier))
                        self.assertNotIn(('remove', pad.title(owner)), pad.seen('remove'))
                        self.assertEqual(pad.seen('beep'), [])

    @scenario('90.43 D2', rules=('R133', 'R171'), rests=('A17', 'A36'), either=('A9',))
    def test_button_recovery_does_not_take_ownership_of_a_valid_driver(self):
        for driver, owner in DRIVERS.items():
            for direction, modifier in MODIFIERS.items():
                for gyro, pad in both_armed_states(self):
                    control = 'LS ' + DIRECTIONS[direction]
                    pad.hold(driver).touch('LS').hold(control).wait(30).let_go(control).mark().tap('A').wait(100)
                    self.assertTrue(pad.has('Steering', owner) and pad.lacks(modifier))
                    self.assertNotIn(('remove', pad.title(owner)), pad.seen('remove'))

    @scenario('90.43 D3', rules=('R133', 'R170'), rests=('A6', 'A25'), either=('A9', 'A32'))
    def test_the_driver_still_cleans_itself_after_its_release_was_missed(self):
        for driver, owner in DRIVERS.items():
            for direction, modifier in MODIFIERS.items():
                for gyro, pad in both_armed_states(self):
                    control = 'LS ' + DIRECTIONS[direction]
                    # Since 90.52 the partial push opens the window, which blocks the right stick's edge for
                    # 150 ms; the stale driver's cleanup fires on a push after it.
                    pad.hold(driver).touch('LS').hold(control).wait(30).let_go(control).miss(driver).wait(200)
                    pad.push('RS').wait(200)
                    self.assertTrue(pad.has('Steering') and pad.lacks(owner, modifier, 'Steering | LS: Tap Cover'))
                    self.assertEqual(pad.seen('beep'), [])
                    pad.lift('RS').lift('LS').wait(400)
                    self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))

    @scenario('90.43 D4', rules=('R133', 'R170', 'R171'), rests=('A6', 'A25', 'A49', 'A53'), either=('A9', 'A32'))
    def test_full_held_movement_cannot_reapply_a_modifier_over_a_stale_driver(self):
        # Recovery must also terminate with LS still out. Otherwise the
        # exposed stale driver's repeating direction can re-add the modifier
        # before its button recovery completes, looping without time passing.
        controls = ('A', 'B', 'X', 'Y', 'Up', 'Down', 'Left', 'Right',
                    'Start', 'Select', 'LS click', 'RS click', 'RS edge')
        for driver, owner in DRIVERS.items():
            for direction, modifier in MODIFIERS.items():
                for dwell in (60, 300):
                    for control in controls:
                        for gyro, pad in both_armed_states(self):
                            pad.hold(driver).push('LS', direction).wait(dwell).miss(driver).mark()
                            # A direct edge press keeps the unchanged RS-touch
                            # recovery from masking the edge's own behavior.
                            pad.hold(control).wait(300)
                            self.assertTrue(pad.lacks('Steering', GUARD, owner, modifier,
                                                      'Steering | LS: Tap Cover'))
                            self.assertEqual(pad.has('Gyro'), gyro)
                            self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                            pad.let_go(control).lift('LS').lift('RS').wait(400)
                            self.assertEqual(pad.stack, pad.layers(*home(gyro)))

    @scenario('90.43 D5', rules=('R133', 'R169'), rests=('A6', 'A16', 'A25', 'A49', 'A53'), either=('A9', 'A32'))
    def test_a_scroll_cover_keeps_its_held_output_and_recovers_a_missed_driver_release(self):
        for driver, owner in DRIVERS.items():
            for direction in MODIFIERS:
                for gyro, pad in both_armed_states(self):
                    pad.hold(driver).flick('LS', direction).wait(30).mark().push('LS', direction).wait(300)
                    self.assertTrue(pad.has('Steering', owner, 'Steering | LS: Double Tap Cover'))
                    wheel = 'mouse_wheel SCROLL_UP' if direction == 'up' else 'mouse_wheel SCROLL_DOWN'
                    self.assertGreater(pad.typed().count(wheel), 2)
                    self.assertEqual(pad.seen('beep'), [])
                    pad.miss(driver).mark().touch('RS').wait(300)
                    self.assertTrue(pad.lacks('Steering', GUARD, owner, 'Steering | LS: Double Tap Cover'))
                    self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                    pad.lift('LS').lift('RS').wait(400)
                    self.assertEqual(pad.stack, pad.layers(*home(gyro)))


class LayerFeedback(ScenarioCase):
    @scenario('90.43 B1', rules=('R161',), rests=('A7', 'A49'), either=('A9', 'A32'))
    def test_gyro_toggle_requests_exactly_one_beep_in_every_press_and_release_order(self):
        for gyro in (False, True):
            for first, second in (('L1', 'R1'), ('R1', 'L1')):
                for release_first in (first, second):
                    for gap in (0, 51):
                        for pad in self.each(start=home(gyro)):
                            last = second if release_first == first else first
                            pad.hold(first).wait(30).hold(second).wait(30).let_go(release_first).wait(gap).let_go(last).wait(400)
                            self.assertEqual(pad.stack, pad.layers(*home(not gyro)))
                            self.assertEqual(pad.seen('beep'), [('beep', 'Gyro')])
                            self.assertEqual(pad.seen('haptic'), [])

    @scenario('90.43 B2', rules=('R161',), rests=('A7', 'A49'), either=('A9',))
    def test_steering_mod2_cleanup_preserves_steering_without_a_clear_beep(self):
        for first, second in (('L1', 'R1'), ('R1', 'L1')):
            for release_first in (first, second):
                for gyro, pad in both_armed_states(self):
                    last = second if release_first == first else first
                    mod2 = f'Steering | {first}!{second}: Modifier 2'
                    pad.hold(first).wait(30).hold(second).wait(30)
                    self.assertTrue(pad.has(mod2))
                    pad.let_go(release_first).wait(30).let_go(last).lift('LS').lift('RS').wait(400)
                    # Since 90.44 the second driver's Release retained Steering; until 90.56 it still
                    # removed Gyro. Since 90.57 it removes only the Modifier 2 layer.
                    self.assertEqual(pad.stack, pad.layers(*home(gyro), 'Steering'))
                    self.assertEqual(pad.seen('beep'), [])


if __name__ == '__main__':
    unittest.main()
