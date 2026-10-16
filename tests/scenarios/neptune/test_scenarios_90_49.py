"""Steering flick completion and final-output feedback for pad clicks.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_49 import *

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



if __name__ == "__main__":
    unittest.main()
