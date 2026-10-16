"""90.52: the Steering stick deflect follows the bumper modifier lifecycle, with a scroll layer for the second deflect.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_52 import *

class StickDeflect(ScenarioCase):
    def held(self):
        """Every driver and direction, on a pad in Steering with the driver held and the thumb on the stick."""
        for driver in ('R1', 'L1'):
            for side in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300)
                    yield pad, driver, side
                    pad.let_go(driver).lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])
                    self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S1', rules=('R130',), rests=('A6', 'A60'), either=('A9', 'A32'))
    def test_four_quick_deflects_scroll_once_each_at_50_ms(self):
        for pad, _, (direction, _, modifier, window, _, wheel) in self.held():
            for _ in range(4):
                pad.mark().push('LS', direction).wait(60)
                self.assertTrue(pad.has(modifier))
                pad.recentre('LS').wait(40)
                self.assertTrue(pad.has(window))
                self.assertEqual(wheels(pad), [])
                pad.wait(20)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                pad.wait(540)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                self.assertTrue(pad.has('Steering') and pad.lacks(*FAMILY))

    @scenario('90.52 S2', rules=('R120',), rests=('A6', 'A60'), either=('A9', 'A32'))
    def test_a_second_deflect_scrolls_on_the_press_and_reopens_the_window(self):
        for pad, _, (direction, _, _, window, layer, wheel) in self.held():
            for _ in range(2):
                pad.mark().flick('LS', direction).wait(30).push('LS', direction).wait(20)
                self.assertTrue(pad.has(layer) and pad.lacks(window, COVER))
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                pad.recentre('LS').wait(20)
                self.assertTrue(pad.has(window) and pad.lacks(layer))
                pad.wait(500)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'] * 2)
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S3', rules=('R120',), rests=('A6', 'A59', 'A60'), either=('A9', 'A32'))
    def test_a_second_deflect_held_past_150_ms_repeats_and_ends_on_its_release(self):
        for pad, _, (direction, _, _, _, layer, wheel) in self.held():
            for _ in range(2):
                pad.mark().flick('LS', direction).wait(30).push('LS', direction).wait(400)
                self.assertTrue(pad.has(layer, COVER))
                self.assertGreater(len(wheels(pad)), 4)
                self.assertEqual(set(wheels(pad)), {f'mouse_wheel {wheel}'})
                pad.recentre('LS').wait(20)
                count = len(wheels(pad))
                pad.wait(400)
                self.assertEqual(len(wheels(pad)), count)
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S4', rules=('R120',), rests=('A59', 'A60'), either=('A9', 'A32'))
    def test_a_hold_past_200_ms_adds_the_marker_and_does_not_scroll(self):
        for pad, _, (direction, _, modifier, _, _, _) in self.held():
            for _ in range(2):
                pad.mark().push('LS', direction).wait(300)
                self.assertTrue(pad.has(modifier, MARKER))
                pad.recentre('LS').wait(400)
                self.assertEqual(wheels(pad), [])
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S5', rests=('A10', 'A60'), either=('A9', 'A32'))
    def test_a_roll_into_a_side_ends_the_modifier_without_a_scroll(self):
        # Past 200 ms the marker is on, and the roll ends a hold. Until 90.52 a side also added the marker, so
        # a roll inside 200 ms was a hold too; since 90.53 a side sends only its key and that roll is a tap,
        # which scrolls once (author, 2026-10-10; 90.53 S5).
        for pad, _, (direction, _, _, _, _, _) in self.held():
            for before in (300,):
                pad.mark().push('LS', direction).wait(before).roll('LS', 'left').wait(100)
                self.assertTrue(pad.lacks(*FAMILY))
                self.assertIn('A', pad.down())
                pad.recentre('LS').wait(300)
                self.assertEqual(wheels(pad), [])

    @scenario('90.52 S6', rules=('R125',), rests=('A60',), either=('A9', 'A32'))
    def test_a_thumb_lifted_in_the_window_only_closes_it(self):
        for pad, _, (direction, _, _, _, _, wheel) in self.held():
            pad.mark().flick('LS', direction).wait(20).lift('LS').wait(300)
            self.assertEqual(wheels(pad), [])
            pad.touch('LS').wait(300)
            pad.mark().flick('LS', direction).wait(80).lift('LS').wait(300)
            self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
            self.assertTrue(pad.lacks(*FAMILY))
            pad.touch('LS').wait(300)

    @scenario('90.52 S7', rules=('R123',), rests=('A60',), either=('A9', 'A32'))
    def test_a_thumb_that_leaves_the_stick_in_a_second_deflect_ends_it_clean(self):
        for pad, _, (direction, _, _, _, _, wheel) in self.held():
            pad.mark().flick('LS', direction).wait(30).push('LS', direction).wait(40).lift('LS').wait(400)
            self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
            self.assertTrue(pad.lacks(*FAMILY))
            pad.touch('LS').wait(300)

    @scenario('90.52 S8', rules=('R130', 'R133'), rests=('A25', 'A36', 'A59', 'A60'), either=('A9',))
    def test_a_missed_driver_release_with_the_stick_held_clears_as_the_marker_lands(self):
        for direction, _, _, _, _, _ in SIDES:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold('R1').touch('LS').wait(300).push('LS', direction).wait(60).miss('R1').wait(300)
                # The marker lands at 200 ms, with no driver held, and its cleanup clears the family; the stick
                # is then on Steering's own binds. So until 90.52 and again since 90.55, where the timer is on
                # the stick's edge. In 90.53 it was on the driver and went with it (tests/test_scenarios_90_53.py).
                self.assertTrue(pad.lacks('Steering | R1: W Key', *FAMILY))
                pad.recentre('LS').wait(300)
                self.assertTrue(pad.lacks('Steering | R1: W Key', *FAMILY))
                pad.lift('LS').wait(300)
                self.assertEqual(pad.down(), [])


class HeldPadClick(ScenarioCase):
    # Guards the shape only: on the Deck with 90.51 a held click dropped when a thumb lifted from a stick,
    # and the simulator held it (plans/2026-10-10-stick-lifecycle-and-pad-click-after-stick-tap.md, part 2).
    @scenario('90.52 P1', rests=('A10', 'A18'), either=('A42',))
    def test_a_held_pad_click_stays_when_a_thumb_lifts_from_a_stick(self):
        for stick in ('LS', 'RS'):
            for click in (('LP', 'left', 'LEFT_ARROW'), ('RP', 'left', 'mouse_button BACK'),
                                  ('LP', 'centre', 'CAPSLOCK'), ('RP', 'centre', 'mouse_button MIDDLE')):
                for order in ('thumb first', 'short touch', 'click first'):
                    for pad in self.each():
                        if order == 'click first':
                            pad.press_pad(*click[:2]).wait(200).touch(stick).wait(60)
                        else:
                            pad.touch(stick).wait(400 if order == 'thumb first' else 40).press_pad(*click[:2]).wait(40)
                        pad.lift(stick).wait(310)
                        self.assertIn(click[2], pad.down(), (stick, click, order))
                        pad.let_go_pad(click[0]).wait(300)
                        self.assertEqual(pad.down(), [])


if __name__ == "__main__":
    unittest.main()
