"""90.54: 90.52 with one change, the stick modifiers' 200 ms hold timer on the left stick's edge.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_54 import *

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


if __name__ == "__main__":
    unittest.main()
