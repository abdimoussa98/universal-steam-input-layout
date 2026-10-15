"""Steering flick completion and final-output feedback for pad clicks."""

import unittest

from steam_layout.model import Layout
from tests.scenario import ScenarioCase, frozen_layout_data, layout_data, scenario


WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')
SCROLL_OWNERS = (
    'Steering | R1: W Key', 'Steering | L1: S Key',
    'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
    'Steering | LS: Tap Cover', *WINDOWS, 'Steering | LS: Double Tap Cover',
)


class SteeringScroll(ScenarioCase):
    # Retired in 90.52: the window scrolls at 50 ms and a thumb's lift only closes it (90.52 S6).
    @scenario('90.49 S1', rules=('R114',), rests=('A6', 'A55'), either=('A9', 'A32'), frozen='90.49')
    def test_flick_and_thumb_lift_complete_once(self):
        for direction, wheel in (('up', 'SCROLL_UP'), ('down', 'SCROLL_DOWN')):
            for lifted in ('LS', 'RS'):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold('R1')
                    if lifted == 'RS':
                        pad.touch('RS')
                    pad.flick('LS', direction).lift(lifted).wait(220)
                    self.assertEqual([x for x in pad.typed() if x.startswith('mouse_wheel')],
                                     [f'mouse_wheel {wheel}'])
                    self.assertTrue(pad.lacks(*WINDOWS))
                    pad.let_go('R1').lift('LS').lift('RS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.49 S2', rules=('R114',), rests=('A6', 'A55'), either=('A9',))
    def test_single_hold_and_second_push_keep_existing_scroll_contract(self):
        for pad in self.each(start=('Base', 'Steering')):
            pad.hold('R1').push('LS', 'up').wait(300).recentre('LS').wait(200)
            self.assertFalse(any('mouse_wheel' in x for x in pad.typed()))
            pad.let_go('R1').lift('LS').wait(300)
            self.assertEqual(pad.down(), [])
        for pad in self.each(start=('Base', 'Steering')):
            pad.hold('R1').flick('LS', 'up').wait(50).push('LS', 'up').wait(300)
            self.assertGreaterEqual(sum('mouse_wheel SCROLL_UP' in x for x in pad.typed()), 2)
            pad.recentre('LS').let_go('R1').lift('LS').wait(300)
            self.assertEqual(pad.down(), [])

    def test_the_edge_states_no_radius_since_90_53(self):
        # 90.49 set the ring to the deadzone's 13276 so that a partial flick released it. Since 90.52 nothing
        # ends on the ring, and since 90.53 these groups use Steam's default (author, 2026-10-10).
        for variant in ('default', 'alternative'):
            layout = Layout(layout_data(variant))
            for title in SCROLL_OWNERS:
                actual = title
                if variant == 'alternative':
                    actual = actual.replace('R1:', 'R2:').replace('L1:', 'L2:')
                group = layout.active(actual)['joystick']
                self.assertNotIn('edge_binding_radius', group['settings'])


class PadClicks(ScenarioCase):
    @scenario('90.50 C1', rules=('R114', 'R133'), rests=('A6', 'A56'), either=('A9',))
    def test_held_right_pad_click_survives_modifier_cover(self):
        for direction in ('up', 'down'):
            for where, output in (('centre', 'mouse_button MIDDLE'),
                                  ('left', 'mouse_button BACK'), ('up', 'mouse_wheel SCROLL_UP')):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold('R1').push('LS', direction).wait(30).mark()
                    pad.press_pad('RP', where).wait(600)
                    # Since 90.71 the held scroll's repeats bump Low; nothing else bumps.
                    self.assertEqual({d for _, d in pad.seen('haptic')},
                                     {'1 RTP: Mouse Buttons right_trackpad/dpad_north'} if where == 'up' else set())
                    self.assertTrue(pad.has('Steering | LS: Tap Cover'))
                    self.assertIn(output, pad.typed())
                    if where != 'up':
                        self.assertIn(output, pad.down())
                    pad.let_go_pad('RP').recentre('LS').let_go('R1').lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.50 C3', rules=('R114',), rests=('A6', 'A56'), either=('A9',))
    def test_held_right_click_survives_stick_thumb_release_completion(self):
        for stick in ('LS', 'RS'):
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold('R1').push('LS', 'up')
                if stick == 'RS':
                    pad.touch('RS')
                pad.wait(30).mark().press_pad('RP', 'centre').wait(30)
                pad.lift(stick).wait(200)
                self.assertTrue(pad.has('RTP: Middle Click'))
                self.assertIn('mouse_button MIDDLE', pad.down())
                bumps = pad.seen('haptic')
                self.assertLessEqual(len(bumps), 1)
                self.assertTrue(all('RTP: Middle Click right_trackpad/click' in source
                                    for _, source in bumps))
                pad.let_go_pad('RP').lift('LS').lift('RS').let_go('R1').wait(300)
                self.assertEqual(pad.down(), [])

    @scenario('90.50 C2', rules=('R161',), rests=('A6', 'A56'), either=('A9',))
    def test_no_early_bump_for_each_pad_and_location(self):
        for stick in ('LP', 'RP'):
            for where in ('centre', 'left', 'up'):
                for pad in self.each():
                    pad.click_pad(stick, where).wait(300)
                    self.assertEqual(pad.seen('haptic'), [])
                    self.assertEqual(pad.down(), [])

    def test_single_configured_bump_is_on_each_final_click_output(self):
        # On the 90.70 build: since 90.71 the bump is on the final layers' self-hold (test_scenarios_90_71 Shape).
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.70'))
            for title, source in (('Base', 'left_trackpad'), ('Base', 'right_trackpad'),
                                  ('RTP: Circular Scroll', 'right_trackpad')):
                entry = layout.active(title)[source]['inputs']['click']['activators']['Soft_Press']
                self.assertEqual(entry['settings']['haptic_intensity'], '0')
            for title, source in (('LTP: Middle Click', 'left_trackpad'),
                                  ('RTP: Middle Click', 'right_trackpad')):
                group = layout.active(title)[source]
                self.assertEqual(group['inputs']['click']['activators']['Full_Press']['settings']['haptic_intensity'], '1')
                for kind in ('Soft_Press',):
                    entries = group['inputs']['click']['activators'][kind]
                    for entry in entries if isinstance(entries, list) else [entries]:
                        self.assertEqual(entry['settings']['haptic_intensity'], '0')
            for title, source in (('LTP: Arrow Keys', 'left_trackpad'),
                                  ('RTP: Mouse Buttons', 'right_trackpad')):
                group = layout.active(title)[source]
                self.assertEqual(group['settings']['haptic_intensity_override'], '5')   # Use Activator Settings, 90.51
                for direction in ('north', 'south', 'east', 'west'):
                    activators = group['inputs'][f'dpad_{direction}']['activators']
                    self.assertEqual(activators['Full_Press']['settings']['haptic_intensity'], '1')
                    if 'chord' in activators:
                        self.assertEqual(activators['chord']['settings']['haptic_intensity'], '0')


if __name__ == '__main__':
    unittest.main()
