"""90.55: the Steering stick's four timers are Soft Presses on the left stick's edge, the left edge cleans up with one inverted chord, and the unnecessary removes are gone.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_55 import *

class TimersOnTheEdge(ScenarioCase):
    """The timers moved off stick up and down because a start delay owned by a stick direction misfires
    (A63). On the edge it held on the Deck (A64, 90.54). Here each is a Soft Press there (A65). The simulator
    never showed the fault, and it presses the edge with the direction, so a shallow push is for the Deck."""

    def held(self):
        """Every driver, on a pad in Steering with the driver held and the thumb on the stick."""
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key
                pad.let_go(driver).lift('LS').wait(300)
                self.assertEqual(pad.down(), [])
                self.assertTrue(pad.lacks(owner, *FAMILY))

    @scenario('90.55 T1', rules=('R120',), rests=('A6', 'A16', 'A60', 'A64', 'A65'), either=('A9', 'A32'))
    def test_taps_and_holds_in_any_order_keep_their_meaning(self):
        # The modifier lands with the stick already past the threshold: the timer starts on a held edge.
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

    @scenario('90.55 T2', rules=('R120',), rests=('A6', 'A16', 'A60', 'A64', 'A65'), either=('A9', 'A32'))
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

    @scenario('90.55 T3', rests=('A10', 'A65'), either=('A9', 'A32'))
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

    @scenario('90.55 T4', rests=('A10', 'A60'), either=('A9', 'A32'))
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

    @scenario('90.55 T5', rests=('A65',), either=('A9', 'A32'))
    def test_the_right_pad_layers_stay_when_the_hold_marker_lands(self):
        # No right pad removes in the Steering modifier layers (author, 2026-10-10 and 2026-10-11).
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

    @scenario('90.55 T6', rules=('R113',), rests=('A6', 'A10', 'A37'), either=('A9', 'A32'))
    def test_the_other_driver_enters_modifier_2_at_once_from_any_stick_layer(self):
        # The stick layers bind no driver, so the driver layer underneath answers the other one: its
        # Modifier 2 entry, now nine removes and the add.
        for driver, owner, key in DRIVERS:
            other = 'L1' if driver == 'R1' else 'R1'
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
                        pad.mark().hold(other).wait(20)
                        self.assertTrue(pad.has(owner, second) and pad.lacks(*FAMILY), stage)
                        self.assertEqual(pad.down(), [key])
                        self.assertEqual([x for x in pad.typed() if not x.startswith('mouse_wheel')], [])
                        pad.recentre('LS').let_go(other).wait(100).let_go(driver).lift('LS').wait(300)
                        self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                        self.assertEqual(pad.down(), [])

    @scenario('90.55 T7', rests=('A7', 'A10'), either=('A9', 'A32'))
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
                        pad.recentre('LS').lift('LS').wait(300)
                        self.assertEqual(pad.down(), [], stage)


class EdgeCleanup(ScenarioCase):
    """The left stick's edge of ten Steering layers: one chord with Invert Activation on the drivers, the Entry
    Guard's pattern. It runs while the stick is inside the ring and no driver is held (A61)."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.55 C1', rules=('R133', 'R170'), rests=('A61',), either=('A9', 'A32'), frozen='90.55')
    def test_no_stick_movement_removes_the_driver_layer_while_the_driver_is_held(self):
        # The fault of 2026-10-10: a flick could drop the W layer under a held driver and leave Steering.
        # Up and down in the W and S layers carry no cleanup any more, and the edge's is off with a driver held.
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

    @scenario('90.55 C2', rules=('R133',), rests=('A25', 'A61'), either=('A9', 'A32'), frozen='90.55')
    def test_a_missed_driver_release_clears_when_the_edge_comes_back(self):
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(300)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has(owner))                  # the chord's own input is pressed: off
            pad.let_go('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            self.assertEqual(pad.down(), [])

    @scenario('90.55 C3', rules=('R133',), rests=('A6', 'A25', 'A61'), either=('A9', 'A32'), frozen='90.55')
    def test_a_missed_driver_release_during_a_deflect_leaves_no_stick_layer(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, _, _, _, _ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300).push('LS', direction).wait(100).miss(driver).wait(600)
                    pad.recentre('LS').wait(400)
                    self.assertTrue(pad.lacks(owner, *FAMILY))
                    pad.lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.55 C4', rules=('R133',), rests=('A61',), either=('A9', 'A32'), frozen='90.55')
    def test_pressing_the_driver_again_shuts_the_edge_chord_off(self):
        for pad, driver, owner, key in self.held():
            pad.miss(driver).wait(100).hold(driver).wait(100)
            pad.hold('LS edge').wait(60).let_go('LS edge').wait(200)
            self.assertTrue(pad.has('Steering', owner))
            self.assertIn(key, pad.down())


if __name__ == "__main__":
    unittest.main()
