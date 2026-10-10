"""Fn entry bumps and Steering's full-deflection exit; no Mod 2 redesign."""
import unittest

from tests.scenario import ScenarioCase, scenario

GUARD = 'Steering | LS: Entry Guard'
MENUS = (('Select', 'Start', 'Left'), ('Start', 'Select', 'Right'))


def steering_family(pad):
    return {title for title in pad.layout.presets
            if title == 'Steering' or title.startswith('Steering | ')}


def direction_pulses(pad):
    return [detail for _, detail in pad.seen('haptic')
            if ' Steering joystick/dpad_' in detail]


class FnEntryFeedback(ScenarioCase):
    @scenario('90.42 F1', rests=('A16', 'A36'))
    def test_delayed_fn_entry_bumps_once_without_a_beep(self):
        for owner in (None, 'Steering', GUARD, 'Cursor Gyro'):
            for button, _, side in MENUS:
                for pad in self.each(start=('Base', owner) if owner else None):
                    prefix = 'Stateful | ' if owner else ''
                    target = f'{prefix}Menu {side}: Fn Layer'
                    pad.hold(button).wait(199)
                    self.assertTrue(pad.lacks(target))
                    self.assertEqual(pad.seen('haptic', 'beep'), [])
                    pad.wait(1)
                    self.assertTrue(pad.has(target))
                    self.assertEqual(pad.seen('beep'), [])
                    self.assertEqual(len(pad.seen('haptic')), 1)
                    self.assertTrue(pad.seen('haptic')[0][1].startswith('1 '))
                    pad.wait(400)
                    self.assertEqual(len(pad.seen('haptic')), 1)
                    pad.let_go(button).wait(400)
                    self.assertTrue(pad.lacks(target))

    @scenario('90.42 F2', rests=('A16', 'A36'))
    def test_the_opposite_menu_chord_bumps_on_early_fn_entry(self):
        for owner in (None, 'Steering'):
            for button, opposite, side in MENUS:
                for pad in self.each(start=('Base', owner) if owner else None):
                    prefix = 'Stateful | ' if owner else ''
                    target = f'{prefix}Menu {side}: Fn Layer'
                    pad.hold(button).wait(30).mark().hold(opposite)
                    self.assertTrue(pad.has(target))
                    self.assertEqual(pad.seen('beep'), [])
                    pulses = [detail for _, detail in pad.seen('haptic')
                              if f'{prefix}Menu {side}: Entry Point ' in detail]
                    self.assertEqual(len(pulses), 1)
                    self.assertTrue(pulses[0].startswith('1 '))

    @scenario('90.42 F3', rules=('R123',), rests=('A7', 'A13', 'A16', 'A36'))
    def test_both_thumb_release_completions_bump_before_helper_cleanup(self):
        for owner in (None, 'Steering'):
            for button, _, side in MENUS:
                for stick in ('LS', 'RS'):
                    for pad in self.each(start=('Base', owner) if owner else None):
                        prefix = 'Stateful | ' if owner else ''
                        target = f'{prefix}Menu {side}: Fn Layer'
                        pad.touch(stick).wait(30).hold(button).wait(50).mark()
                        pad.sim.release(pad.control(stick + ' touch'))
                        self.assertTrue(pad.has(target))
                        self.assertEqual(pad.seen('beep'), [])
                        pulses = pad.seen('haptic')
                        self.assertEqual(len(pulses), 1)
                        self.assertTrue(pulses[0][1].startswith('1 '))
                        changes = pad.seen('add', 'remove')
                        target_index = changes.index(('add', pad.title(target)))
                        helpers = ('LST: ', 'RST: ')
                        self.assertTrue(all(target_index < index for index, (kind, title) in enumerate(changes)
                                            if kind == 'remove' and title.startswith(helpers)))


class SteeringFullDeflectionExit(ScenarioCase):
    @scenario('90.42 S1', rests=('A6', 'A10', 'A53'), either=('A9',))
    def test_up_and_down_exit_once_and_continue_base_movement_with_gyro_preserved(self):
        for gyro in (False, True):
            for direction, key in (('up', 'W'), ('down', 'S')):
                start = ('Base', 'Gyro', 'Steering') if gyro else ('Base', 'Steering')
                for pad in self.each(start=start):
                    pad.push('LS', direction).wait(600)
                    self.assertFalse(set(pad.stack) & steering_family(pad))
                    self.assertEqual(pad.down(), [key])
                    self.assertEqual(direction_pulses(pad),
                                     [f'1 Steering joystick/dpad_{"north" if direction == "up" else "south"}'])
                    self.assertEqual(pad.seen('beep'), [('beep', 'Steering')])
                    self.assertEqual(pad.has('Gyro'), gyro)
                    self.assertNotIn(('add', GUARD), pad.seen('add'))
                    pad.lift('LS').wait(500)
                    self.assertEqual(pad.stack, pad.layers('Base', 'Gyro') if gyro else pad.layers('Base'))

    @scenario('90.42 S2', rests=('A6', 'A10', 'A53'), either=('A9',))
    def test_a_direction_already_held_when_steering_lands_is_protected_until_release(self):
        for direction, key in (('up', 'W'), ('down', 'S')):
            for pad in self.each():
                pad.push('LS', direction).wait(100).mark().enter_steering(settle=False).wait(600)
                self.assertTrue(pad.has('Steering', GUARD))
                self.assertEqual(pad.down(), [key])
                self.assertEqual(direction_pulses(pad), [])
                pad.lift('LS').wait(500)
                self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                pad.mark().push('LS', direction).wait(100)
                self.assertFalse(set(pad.stack) & steering_family(pad))
                self.assertEqual(len(direction_pulses(pad)), 1)

    @scenario('90.42 S3', rules=('R148',), rests=('A4', 'A6', 'A53'))
    def test_the_exit_removes_stale_steering_helpers_including_windows_first(self):
        # Seed a stale stack deliberately; this checks the recovery list,
        # without claiming this full stack is normally reachable.
        helpers = (GUARD, 'Steering | R1: W Key', 'Steering | L1: S Key',
                   'Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2',
                   'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
                   'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover',
                   'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap',
                   'L1: Tap Cover', 'R1: Tap Cover')
        for direction in ('up', 'down'):
            for pad in self.each(start=('Base', 'Gyro', *helpers, 'Steering')):
                # Thumb contact now reaches the lower touch bindings. Their
                # stale-cover recovery can run before the direction clear;
                # isolate the latter's ordering with both windows still live.
                pad.touch('LS')
                self.assertTrue(pad.has('Steering | LS Up: Double Tap',
                                        'Steering | LS Down: Double Tap'))
                pad.mark().push('LS', direction).wait(600)
                self.assertFalse(set(pad.stack) & steering_family(pad))
                self.assertTrue(pad.lacks('L1: Tap Cover', 'R1: Tap Cover'))
                self.assertTrue(pad.has('Gyro'))
                removed = [title for _, title in pad.seen('remove')]
                self.assertEqual(set(removed[:2]), set(pad.layers('Steering | LS Up: Double Tap',
                                                                  'Steering | LS Down: Double Tap')))
                # Base can own ordinary LST helpers while the thumb remains;
                # release must leave only the preserved persistent Gyro.
                pad.lift('LS').wait(300)
                self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', 'Gyro'), []))

    @scenario('90.42 S4', rules=('R140', 'R148'), rests=('A16', 'A53'), either=('A9',))
    def test_rtp_window_leaves_before_a_held_direction_clears_steering(self):
        for direction in ('up', 'down'):
            for pad in self.each(start='steering'):
                pad.touch('RP').wait(30).lift('RP').push('LS', direction).wait(100)
                self.assertTrue(pad.has('Steering', 'RTP: Double Tap'))
                self.assertEqual(direction_pulses(pad), [])
                pad.mark().wait(300)
                self.assertFalse(set(pad.stack) & steering_family(pad))
                changes = pad.seen('add', 'remove')
                self.assertLess(changes.index(('remove', 'RTP: Double Tap')),
                                changes.index(('remove', 'Steering')))
                self.assertEqual(len(direction_pulses(pad)), 1)
                self.assertNotIn(('add', GUARD), changes)


if __name__ == '__main__':
    unittest.main()
