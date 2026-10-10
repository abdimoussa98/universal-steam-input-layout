"""Menu chords and RTP access during Steering; physical thresholds remain A53/A54."""
import unittest
from tests.scenario import ScenarioCase, scenario

GUARD = 'Steering | LS: Fallback Guard'
ENTRY_GUARD = 'Steering | LS: Entry Guard'


class SteeringRtp(ScenarioCase):
    @scenario('90.38 M1', rests=('A16', 'A36'), either=('A9',))
    def test_each_stateful_owner_enters_and_releases_both_menu_fn_layers(self):
        # Entry Guard now hands off to the menu instead of surviving it;
        # 90.43 E6/E8 cover that temporary guard separately.
        for owner in ('Steering', 'Cursor Gyro'):
            for button, side in (('Select', 'Left'), ('Start', 'Right')):
                for pad in self.each(start=('Base', owner)):
                    pad.hold(button).wait(199)
                    self.assertTrue(pad.has(f'Stateful | Menu {side}: Entry Point'))
                    self.assertTrue(pad.lacks(f'Stateful | Menu {side}: Fn Layer'))
                    pad.wait(1)
                    self.assertTrue(pad.has(f'Stateful | Menu {side}: Fn Layer'))
                    self.assertEqual(pad.seen('beep'), [])  # Fn entry is silent since 90.41
                    pad.let_go(button).wait(400)
                    self.assertTrue(pad.has(owner))
                    self.assertTrue(pad.lacks(f'Stateful | Menu {side}: Fn Layer', f'Stateful | Menu {side}: Entry Point'))

    @scenario('90.38 M2', rules=('R114',), rests=('A16', 'A25', 'A36'))
    def test_stateful_menu_reenters_after_a_pad_window_and_recovers_a_missed_release(self):
        for owner in ('Steering', 'Cursor Gyro'):
            for button, side in (('Select', 'Left'), ('Start', 'Right')):
                for pad in self.each(start=('Base', owner)):
                    pad.touch('RP').wait(30).lift('RP').hold(button).wait(600)
                    self.assertTrue(pad.has(f'Stateful | Menu {side}: Fn Layer'))
                    pad.miss(button).touch('RS').wait(150)
                    self.assertTrue(pad.lacks(f'Stateful | Menu {side}: Fn Layer'))
                    pad.hold(button).wait(300)
                    self.assertTrue(pad.has(f'Stateful | Menu {side}: Fn Layer'))

    @scenario('90.38 P1', rules=('R139',), rests=('A16',))
    def test_touch_hold_and_double_tap_scroll_work_in_armed_steering(self):
        # Restored Entry Guard blocks pad helpers until it ends (90.43 E9).
        for owner in ('Steering',):
            for pad in self.each(start=('Base', owner)):
                pad.mark().touch('RP').wait(150)
                self.assertTrue(pad.has(owner, 'RTP: Entry Point', 'RTP: Tap Cover'))
                self.assertEqual(pad.seen('haptic'), [])
                pad.lift('RP').wait(200)
                self.assertEqual(pad.stack, pad.layers('Base', owner))
                pad.touch('RP').wait(30).lift('RP')
                self.assertTrue(pad.has('RTP: Double Tap'))
                pad.sim.press(('right_trackpad', 'dpad_north'))
                self.assertTrue(pad.has(owner, 'RTP: Circular Scroll'))
                self.assertTrue(pad.lacks('RTP: Double Tap'))

    @scenario('90.38 P2', rules=('R140', 'R148'), rests=('A16',))
    def test_rtp_window_blocks_steering_direction_mutations_until_it_exits(self):
        for direction in ('up', 'down'):
            for pad in self.each(start='steering'):
                pad.touch('RP').wait(30).lift('RP').push('LS', direction).wait(100)
                self.assertTrue(pad.has('Steering', 'RTP: Double Tap'))
                self.assertTrue(pad.lacks(ENTRY_GUARD))
                pad.mark().wait(200)
                self.assertTrue(pad.lacks(ENTRY_GUARD, 'Steering', 'RTP: Double Tap'))
                changes = [(event, detail) for _, event, detail in pad.sim.log[pad._mark:] if event in ('add', 'remove')]
                self.assertLess(changes.index(('remove', 'RTP: Double Tap')), changes.index(('remove', 'Steering')))

    @scenario('90.38 D1', rules=('R123',), rests=('A13', 'A16'))
    def test_menu_delay_adds_its_target_before_removing_rtp(self):
        for side, button in (('Left', 'Select'), ('Right', 'Start')):
            for pad in self.each(start='steering'):
                pad.touch('RP').wait(170).hold(button).wait(199).mark().wait(1)
                target = f'Stateful | Menu {side}: Fn Layer'
                self.assertTrue(pad.has(target))
                changes = [(event, detail) for _, event, detail in pad.sim.log[pad._mark:] if event in ('add', 'remove')]
                self.assertLess(changes.index(('add', target)), changes.index(('remove', 'RTP: Entry Point')))
                # The still-held thumb may re-enter RTP after cleanup; that is intended inheritance.

    @scenario('90.38 D2', rules=('R123',), rests=('A13', 'A16'))
    def test_directional_hold_completes_before_rtp_cleanup(self):
        for direction in ('up', 'down'):
            for pad in self.each(start='steering'):
                pad.touch('RP').wait(170).hold('R1').push('LS', direction).wait(199).mark().wait(1)
                self.assertTrue(pad.has('Steering | LS: Tap Cover'))
                changes = [(event, detail) for _, event, detail in pad.sim.log[pad._mark:] if event in ('add', 'remove')]
                self.assertLess(changes.index(('add', 'Steering | LS: Tap Cover')), changes.index(('remove', 'RTP: Entry Point')))

    @scenario('90.38 S1', rests=('A6', 'A53'))
    def test_full_direction_exits_steering_once_with_a_low_pulse(self):
        # Binary full deflection only. Numeric 29031 and physical distance are not simulated.
        for direction, key in (('up', 'W'), ('down', 'S')):
            for pad in self.each(start='steering'):
                pad.mark().push('LS', direction).wait(600)
                self.assertTrue(pad.lacks('Steering', ENTRY_GUARD))
                self.assertEqual(pad.down(), [key])
                pulses = [d for _, d in pad.seen('haptic') if d.startswith('1 Steering joystick/dpad_')]
                self.assertEqual(len(pulses), 1)

    @scenario('90.38 S2', rests=('A1', 'A36', 'A54'), frozen="90.41")
    def test_gyro_modifier_edge_still_takes_precedence_over_the_fallback_chord(self):
        # The requested binding is local to fallback, not a global override.
        for driver, modifier in (('L1', 'Gyro | L1: Modifier 0'), ('R1', 'Gyro | R1: Modifier 1')):
            for pad in self.each(start='steering'):
                pad.push('LS', 'up').hold(driver).wait(50)
                owner, _ = pad.sim.binding(('joystick', 'edge'))
                self.assertEqual(owner, pad.title(modifier))
                pad.recentre('LS').wait(50)
                self.assertTrue(pad.has(GUARD, modifier) and pad.lacks('Steering'))

    @scenario('90.38 S3', rules=('R139', 'R159'), rests=('A3', 'A54'), frozen="90.41")
    def test_the_additive_return_stack_can_drive_reenter_fallback_and_clear(self):
        # Seed the stack permitted by the requested additive edge. Its physical
        # reachability depends on the edge being exposed and on A54.
        for pad in self.each(start=('Base', GUARD, 'Steering')):
            pad.hold('R1').wait(30)
            self.assertTrue(pad.has('Steering', 'Steering | R1: W Key'))
            pad.let_go('R1').wait(300).push('LS', 'up').wait(500)
            self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', GUARD), ['W']))
            pad.hold('L1').wait(30).hold('R1').wait(30).let_go('R1').let_go('L1').lift('LS').wait(500)
            self.assertEqual(pad.stack, pad.layers('Base'))


if __name__ == '__main__':
    unittest.main()
