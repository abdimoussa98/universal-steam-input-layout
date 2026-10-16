"""90.53: the Steering stick's timers sit on the drivers, its entry carries no cleanup, and the left edge cleans up with one inverted chord.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_53 import *

class EntryAndEdge(ScenarioCase):
    def held(self):
        """Every driver, on a pad in Steering with the driver held and the thumb on the stick."""
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.53 S1', rules=('R133', 'R170'), rests=('A61', 'A62'), either=('A9', 'A32'), frozen='90.53')
    def test_no_stick_movement_removes_the_driver_layer_while_the_driver_is_held(self):
        # The fault of 2026-10-10: a flick could drop the W layer under a held driver and leave Steering.
        for pad, _, owner, key in self.held():
            for direction in ('up', 'down', 'up', 'left', 'right', 'down'):
                for ms in (30, 60, 150, 300):
                    pad.flick('LS', direction, ms)
                    self.assertTrue(pad.has('Steering', owner))
                    self.assertIn(key, pad.down())
                    pad.wait(40)
            for _ in range(3):                               # the edge alone, out and back
                pad.hold('LS edge').wait(40).let_go('LS edge').wait(40)
                self.assertTrue(pad.has('Steering', owner))
            pad.wait(400)
            self.assertTrue(pad.has('Steering', owner) and pad.lacks(*FAMILY))
            self.assertEqual(pad.down(), [key])

    @scenario('90.53 S2', rules=('R130',), rests=('A60', 'A62'), either=('A9', 'A32'), frozen='90.53')
    def test_every_deflect_in_one_driver_hold_adds_its_modifier_and_scrolls_once(self):
        for pad, _, owner, _ in self.held():
            for direction, _, modifier, _, _, wheel in SIDES * 3:
                pad.mark().push('LS', direction).wait(60)
                self.assertTrue(pad.has(owner, modifier))
                pad.recentre('LS').wait(400)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                self.assertTrue(pad.has(owner) and pad.lacks(*FAMILY))

    @scenario('90.53 S3', rules=('R133',), rests=('A25', 'A61'), either=('A9', 'A32'), frozen='90.53')
    def test_a_missed_driver_release_clears_when_the_edge_comes_back(self):
        # With no driver held the edge's inverted chord runs as the stick comes back from the rim.
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(300)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has(owner))                  # the chord's own input is pressed: off
            pad.let_go('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            self.assertEqual(pad.down(), [])

    @scenario('90.53 S4', rules=('R133',), rests=('A61',), either=('A9', 'A32'), frozen='90.53')
    def test_pressing_the_driver_again_shuts_the_edge_chord_off(self):
        for pad, driver, owner, key in self.held():
            pad.miss(driver).wait(100).hold(driver).wait(100)
            pad.hold('LS edge').wait(60).let_go('LS edge').wait(200)
            self.assertTrue(pad.has('Steering', owner))
            self.assertIn(key, pad.down())

    @scenario('90.53 S5', rests=('A10', 'A60'), either=('A9', 'A32'), frozen='90.53')
    def test_a_side_key_never_adds_the_hold_marker(self):
        # Left and right send A and D only (author, 2026-10-10). A roll inside 200 ms is a tap of up or
        # down: the window opens and scrolls once. Past 200 ms the marker is on and nothing scrolls.
        for pad, _, _, _ in self.held():
            for direction, _, _, window, _, wheel in SIDES:
                pad.mark().push('LS', direction).wait(60).roll('LS', 'left').wait(20)
                self.assertTrue(pad.has(window) and pad.lacks(MARKER))
                self.assertIn('A', pad.down())
                pad.wait(300)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                pad.recentre('LS').wait(300)
                pad.mark().push('LS', direction).wait(300).roll('LS', 'right').wait(100)
                self.assertIn('D', pad.down())
                pad.recentre('LS').wait(300)
                self.assertEqual(wheels(pad), [])
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.53 S6', rests=('A59',), either=('A9', 'A32'), frozen='90.53')
    def test_the_right_pad_layers_stay_when_the_hold_marker_lands(self):
        # No right pad removes in the Steering modifier layers (author, 2026-10-10).
        for pad, _, _, _ in self.held():
            for direction, _, modifier, _, _, _ in SIDES:
                pad.hold('RP touch').wait(300)
                self.assertTrue(pad.has(*RIGHT_PAD))
                pad.push('LS', direction).wait(300)
                self.assertTrue(pad.has(modifier, MARKER, *RIGHT_PAD))
                pad.recentre('LS').wait(300)
                self.assertTrue(pad.has(*RIGHT_PAD) and pad.lacks(*FAMILY))
                pad.let_go('RP touch').wait(300)
                self.assertTrue(pad.lacks(*RIGHT_PAD))


class TimersOnTheDrivers(ScenarioCase):
    """The fault of 90.50 to 90.52 (author, on the Deck): the 200 ms hold timer was owned by the stick's
    direction, and after one tap it landed at once on every later deflect. The simulator never showed it."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key
                pad.let_go(driver).lift('LS').wait(300)
                self.assertEqual(pad.down(), [])
                self.assertTrue(pad.lacks(owner, *FAMILY))

    @scenario('90.53 T1', rules=('R120',), rests=('A6', 'A16', 'A36', 'A59', 'A60', 'A63'), either=('A9', 'A32'), frozen='90.53')
    def test_taps_and_holds_in_any_order_keep_their_meaning(self):
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

    @scenario('90.53 T2', rules=('R120',), rests=('A6', 'A16', 'A36', 'A59', 'A60', 'A63'), either=('A9', 'A32'), frozen='90.53')
    def test_second_deflects_chain_and_the_cover_waits_its_150_ms_every_time(self):
        for pad, _, _, _ in self.held():
            for direction, _, _, window, layer, wheel in SIDES:
                pad.mark().flick('LS', direction).wait(30)
                for _ in range(3):                                         # three quick second deflects
                    pad.push('LS', direction).wait(60)
                    self.assertTrue(pad.has(layer) and pad.lacks(COVER))
                    pad.recentre('LS').wait(30)
                    self.assertTrue(pad.has(window))
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'] * 3)          # one on each press
                pad.push('LS', direction).wait(149)
                self.assertTrue(pad.lacks(COVER))
                pad.wait(251)
                self.assertTrue(pad.has(layer, COVER))
                self.assertGreater(len(wheels(pad)), 8)
                pad.recentre('LS').wait(400)
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.53 T3', rules=('R113',), rests=('A5', 'A10', 'A37', 'A59'), either=('A9', 'A32'), frozen='90.53')
    def test_the_other_driver_enters_modifier_2_at_once_from_any_stick_layer(self):
        # One shared stick modifier binds both drivers (author, 2026-10-10), and Modifier 2 has to stay in
        # reach while the stick is out (author, 2026-10-11). The held driver's key press never runs its layer
        # commands (A5); the other driver's fresh press does. Its key shows for that moment only.
        for driver, owner, key in DRIVERS:
            other, other_key = ('L1', 'S') if driver == 'R1' else ('R1', 'W')
            second = f'Steering | {driver}!{other}: Modifier 2'
            for direction, _, modifier, _, layer, _ in SIDES:
                for stage in ('modifier', 'marker', 'scroll'):
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.hold(driver).touch('LS').wait(300)
                        if stage == 'scroll':
                            pad.flick('LS', direction).wait(20).push('LS', direction).wait(40)
                        else:
                            pad.push('LS', direction).wait(100 if stage == 'modifier' else 300)
                        self.assertTrue(pad.has(owner, layer if stage == 'scroll' else modifier) and pad.lacks(second))
                        self.assertEqual(pad.down(), [key])                # landing ran no layer command
                        pad.mark().hold(other).wait(20)
                        self.assertTrue(pad.has(owner, second) and pad.lacks(*FAMILY), stage)
                        self.assertEqual(pad.down(), [key])
                        self.assertEqual([x for x in pad.typed() if not x.startswith('mouse_wheel')], [other_key])
                        pad.recentre('LS').let_go(other).wait(100).let_go(driver).lift('LS').wait(300)
                        self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                        self.assertEqual(pad.down(), [])

    @scenario('90.53 T4', rests=('A7', 'A10'), either=('A9', 'A32'), frozen='90.53')
    def test_the_driver_let_go_ends_the_stick_layers_wherever_the_sequence_is(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, modifier, window, layer, _ in SIDES:
                for stage, on in (('modifier', modifier), ('marker', MARKER), ('window', window), ('scroll', layer), ('cover', COVER)):
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.hold(driver).touch('LS').wait(300)
                        if stage == 'modifier':
                            pad.push('LS', direction).wait(60)
                        elif stage == 'marker':
                            pad.push('LS', direction).wait(300)
                        else:
                            pad.flick('LS', direction).wait(20)
                            if stage != 'window':
                                pad.push('LS', direction).wait(60 if stage == 'scroll' else 300)
                        self.assertTrue(pad.has(on), stage)
                        pad.let_go(driver).wait(50)
                        self.assertTrue(pad.lacks(owner, *FAMILY), stage)
                        pad.lift('LS').wait(300)
                        self.assertEqual(pad.down(), [], stage)


class EntryGuard(ScenarioCase):
    """What `Steering | LS: Entry Guard` does on the corrected simulator, and is meant to do (author,
    2026-10-11): protect a stick that is held at the rim through the entry, and nothing else."""

    def enter(self, pad):
        pad.hold('Start').click('LS').let_go('Start').wait(300)

    @scenario('90.53 G1', rules=('R111',), rests=('A54', 'A61'))
    def test_a_centred_entry_keeps_no_guard_and_the_first_full_push_is_steerings_exit(self):
        for pad in self.each():
            self.enter(pad)
            self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
            pad.mark().push('LS', 'up').wait(100)
            self.assertTrue(pad.lacks('Steering', GUARD))
            self.assertIn(('beep', 'Steering'), pad.seen('beep'))
            pad.lift('LS').wait(300)
            self.assertEqual(pad.down(), [])

    @scenario('90.53 G2', rules=('R111',), rests=('A8', 'A10', 'A54', 'A61'))
    def test_a_stick_held_at_the_rim_through_the_entry_is_guarded_until_it_comes_back(self):
        for direction, key in (('up', 'W'), ('down', 'S')):
            for pad in self.each():
                pad.push('LS', direction).wait(200)
                self.enter(pad)
                self.assertTrue(pad.has('Steering', GUARD))
                self.assertEqual(pad.down(), [key])                       # the stick still walks, and Steering stays
                pad.wait(1000)
                self.assertTrue(pad.has('Steering', GUARD))
                pad.recentre('LS').wait(100)
                self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                self.assertEqual(pad.down(), [])
                pad.lift('LS').wait(300)

    @scenario('90.53 G3', rules=('R111',), rests=('A6', 'A54', 'A61'), either=('A9',))
    def test_a_driver_takes_over_from_the_guard(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each():
                pad.push('LS', 'left').wait(200)
                self.enter(pad)
                self.assertTrue(pad.has('Steering', GUARD))
                pad.hold(driver).wait(100)
                self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD))
                self.assertIn(key, pad.down())
                pad.let_go(driver).lift('LS').wait(300)
                self.assertEqual(pad.down(), [])


if __name__ == "__main__":
    unittest.main()
