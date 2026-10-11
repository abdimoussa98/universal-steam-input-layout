"""90.54: 90.52 with one change, the stick modifiers' 200 ms hold timer on the left stick's edge."""

# Since 90.55 these run on the 90.54 candidate (`frozen`): the timer is a Soft Press there (tests/test_scenarios_90_55.py).

import unittest

from steam_layout.model import EMPTY, Layout, actions, entries
from tests.scenario import ScenarioCase, frozen_layout_data, scenario

DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
# driver, its layer, its key
DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))
# direction, input, modifier, window, scroll layer, wheel
SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))
FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


class TimerOnTheEdge(ScenarioCase):
    """The author's trial of 2026-10-11: the timer misfired on the stick's direction (A63) and behaved on the
    bumper. Here it sits on the edge, the stick's outer ring. The simulator never showed the fault, so these
    say only that the build is wired as 90.52 was; whether the edge behaves is A64, for the Deck."""

    def held(self):
        """Every driver, on a pad in Steering with the driver held and the thumb on the stick."""
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.54 E1', rules=('R120',), rests=('A6', 'A16', 'A27', 'A36', 'A64'), either=('A9', 'A32'), frozen='90.54')
    def test_taps_and_holds_in_any_order_keep_their_meaning(self):
        # The modifier lands with the stick already past the edge: the timer starts on a held edge (R165).
        for pad, _, _, key in self.held():
            for direction, _, modifier, _, _, wheel in SIDES:
                for gesture in ('tap', 'tap', 'hold', 'tap', 'hold', 'hold', 'tap', 'tap'):
                    pad.mark().push('LS', direction).wait(60)
                    self.assertTrue(pad.has(modifier) and pad.lacks(MARKER))
                    if gesture == 'hold':
                        pad.wait(139)
                        self.assertTrue(pad.lacks(MARKER))                 # the full 200 ms, every time
                        pad.wait(1)
                        self.assertTrue(pad.has(MARKER))
                        pad.wait(200)
                    pad.recentre('LS').wait(400)
                    self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'] if gesture == 'tap' else [], gesture)
                    self.assertEqual(pad.down(), [key])                    # the key never lets go
                    self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.54 E2', rests=('A10', 'A27', 'A64'), either=('A9', 'A32'), frozen='90.54')
    def test_a_press_during_the_deflect_makes_it_a_hold_at_once(self):
        for pad, _, _, key in self.held():
            for direction, _, modifier, _, _, _ in SIDES:
                for press in ('A', 'LS', 'RS'):
                    pad.mark().push('LS', direction).wait(60)
                    pad.click(press) if press in ('LS', 'RS') else pad.tap(press)
                    pad.wait(50)
                    self.assertTrue(pad.has(modifier, MARKER))
                    pad.recentre('LS').wait(400)
                    self.assertEqual(wheels(pad), [])
                    self.assertEqual(pad.down(), [key])
                    self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.54 E3', rules=('R113',), rests=('A10', 'A37'), either=('A9', 'A32'), frozen='90.54')
    def test_the_other_driver_enters_modifier_2_during_the_deflect(self):
        # The stick modifiers bind no driver, so the driver layer under them still answers the other one.
        for pad, driver, owner, key in self.held():
            other = 'L1' if driver == 'R1' else 'R1'
            for direction, _, _, _, _, _ in SIDES:
                pad.push('LS', direction).wait(60).hold(other).wait(100)
                self.assertTrue(pad.has(f'Steering | {driver}!{other}: Modifier 2'))
                self.assertEqual(pad.down(), [key])
                pad.recentre('LS').wait(300).let_go(other).wait(400)
                self.assertEqual(pad.stack[-1], pad.title(owner))

    @scenario('90.54 E4', rules=('R133',), rests=('A6', 'A25', 'A27'), either=('A9', 'A32'), frozen='90.54')
    def test_a_missed_driver_release_during_the_deflect_leaves_no_steering_stick_layer(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, _, _, _, _ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300).push('LS', direction).wait(100).miss(driver).wait(600)
                    self.assertTrue(pad.lacks(owner, *FAMILY))
                    pad.recentre('LS').lift('LS').wait(400)
                    self.assertEqual(pad.down(), [])
                    self.assertTrue(pad.lacks(owner, *FAMILY))


class TimerOnTheEdgeShape(unittest.TestCase):
    def test_the_hold_timer_is_the_edges_third_entry_and_the_direction_keeps_the_reset_and_the_release(self):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.54'))
            for _, own, modifier, window, _, _ in SIDES:
                inputs = layout.active(modifier)['joystick']['inputs']
                on_stick = list(entries(inputs[own]['activators']))
                self.assertEqual([kind for kind, _ in on_stick], ['Full_Press', 'release'], (variant, modifier))
                reset, release = (entry for _, entry in on_stick)
                self.assertEqual(layout.layer_ops(reset), [('remove_layer', MARKER)])
                self.assertEqual(reset['settings'], {'hold_repeats': '1', 'repeat_rate': '250', 'interruptable': '0'})
                self.assertIn(('add_layer', window), layout.layer_ops(release))
                on_edge = list(entries(inputs['edge']['activators']))
                self.assertEqual([kind for kind, _ in on_edge], ['Full_Press', 'chord', 'chord'], (variant, modifier))
                cleanup, guard, timer = (entry for _, entry in on_edge)
                self.assertIn(('remove_layer', modifier), layout.layer_ops(cleanup))
                self.assertEqual(cleanup['settings'], {'hold_repeats': '1'})
                self.assertEqual(actions(guard), [EMPTY + ', , '])
                self.assertIn(('add_layer', MARKER), layout.layer_ops(timer))
                self.assertEqual(timer['settings'], {
                    'gyro_ratchet_button_mask': str(DEFLECT), 'gyro_ratchet_button_requireany_or_all': '0',
                    'delay_start': '200', 'interruptable': '0'}, (variant, modifier))

    def test_no_other_steering_bind_moved(self):
        # One change: the two stick scroll layers keep their 150 ms on up and down, as in 90.52.
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.54'))
            for _, own, _, _, scroll, _ in SIDES:
                delays = [entry['settings'].get('delay_start') for kind, entry in
                          entries(layout.active(scroll)['joystick']['inputs'][own]['activators']) if kind == 'chord']
                self.assertEqual(delays, ['150'], (variant, scroll))


if __name__ == '__main__':
    unittest.main()
