"""90.57: in `Steering` the first driver's Release hands over, the second driver's Release removes only the Modifier 2 layer, and 264 removes are gone.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_57 import *

class TwoDrivers(ScenarioCase):
    """The author's report on 90.56: R1 held for W, L1 pressed for Modifier 2, and letting go of R1 with the stick
    up or down ended `Steering` although L1 was held. And: "I don't want to be cleared out of steering in mod 2"."""

    @scenario('90.57 H1', rules=('R174',), rests=('A4', 'A7', 'A10', 'A37'), either=('A9', 'A32'))
    def test_the_first_driver_let_go_in_modifier_2_hands_over_wherever_the_stick_is(self):
        for first, own, own_key, second, other, other_key, modifier in ORDERS:
            for direction in (None, 'up', 'down'):
                for pad in self.each(start=('Base', STEERING)):
                    pad.hold(first).wait(300)
                    if direction:
                        pad.push('LS', direction).wait(300)              # at the rim: bare `Steering` would end here
                    pad.hold(second).wait(300)
                    self.assertTrue(pad.has(STEERING, own, modifier))
                    self.assertEqual(pad.down(), [own_key])
                    pad.let_go(first).wait(5)
                    self.assertTrue(pad.has(STEERING, other) and pad.lacks(own, *MODIFIER_2), direction)
                    self.assertEqual(pad.down(), [other_key])
                    pad.wait(300)
                    self.assertTrue(pad.has(STEERING, other) and pad.lacks(own, *MODIFIER_2), direction)
                    self.assertEqual(pad.down(), [other_key])

    @scenario('90.57 H2', rules=('R174',), rests=('A4', 'A7', 'A10', 'A37'), either=('A9', 'A32'), frozen='90.61')
    def test_rocking_the_drivers_follows_the_held_one_and_steering_stays(self):
        # On the 90.61 build: since 90.62 the second driver's layer is on under Modifier 2 (90.62 R1).
        # R1, L1, R1 up (the S layer), R1 down (L1 first now), L1 up (the W layer), L1 down, and round again.
        for direction in (None, 'up'):
            for pad in self.each(start=('Base', STEERING)):
                pad.hold('R1').wait(300)
                if direction:
                    pad.push('LS', direction).wait(300)
                pad.hold('L1').wait(120)
                for _ in range(3):
                    self.assertTrue(pad.has(STEERING, W, 'Steering | R1!L1: Modifier 2') and pad.lacks(S))
                    self.assertEqual(pad.down(), ['W'])
                    pad.let_go('R1').wait(120)
                    self.assertTrue(pad.has(STEERING, S) and pad.lacks(W, *MODIFIER_2))
                    self.assertEqual(pad.down(), ['S'])
                    pad.hold('R1').wait(120)
                    self.assertTrue(pad.has(STEERING, S, 'Steering | L1!R1: Modifier 2') and pad.lacks(W))
                    self.assertEqual(pad.down(), ['S'])
                    pad.let_go('L1').wait(120)
                    self.assertTrue(pad.has(STEERING, W) and pad.lacks(S, *MODIFIER_2))
                    self.assertEqual(pad.down(), ['W'])
                    pad.hold('L1').wait(120)
                pad.let_go('L1').wait(120).recentre('LS').wait(300).let_go('R1').wait(300).lift('LS').wait(300)
                self.assertEqual(pad.stack, pad.layers('Base', STEERING))
                self.assertEqual(pad.down(), [])

    @scenario('90.57 T1', rules=('R159', 'R174'), rests=('A7',), either=('A9', 'A32'))
    def test_a_tap_and_a_hold_of_the_second_driver_end_the_same_way(self):
        # Three times inside one hold of the first driver, at each length. `Gyro` stays, the first driver's
        # layer and key stay, and there is no bump: the 200 ms timer and its cover are gone.
        for gyro in (False, True):
            for first, own, own_key, second, _, _, modifier in ORDERS:
                for pad in self.each(start=(*home(gyro), STEERING)):
                    pad.hold(first).wait(300).mark()
                    for ms in (30, 60, 150, 250, 500) * 3:
                        pad.hold(second).wait(ms)
                        self.assertTrue(pad.has(modifier) and pad.lacks(*COVERS), ms)
                        pad.let_go(second).wait(60)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro), STEERING, own), ms)
                        self.assertEqual(pad.down(), [own_key], ms)
                    self.assertEqual(pad.seen('beep', 'haptic'), [])
                    self.assertEqual(pad.typed(), [])                    # the first driver's key never let go
                    pad.let_go(first).wait(300)
                    self.assertEqual(pad.stack, pad.layers(*home(gyro), STEERING))

    @scenario('90.57 T2', rules=('R174',), rests=('A6', 'A7'), either=('A9', 'A32'))
    def test_the_second_driver_let_go_with_the_stick_at_the_rim_leaves_steering_on(self):
        for first, own, own_key, second, _, _, modifier in ORDERS:
            for direction in ('up', 'down'):
                for ms in (60, 400):
                    for pad in self.each(start=('Base', STEERING)):
                        pad.hold(first).wait(100).hold(second).wait(ms).push('LS', direction).wait(100)
                        self.assertTrue(pad.has(STEERING, own, modifier))
                        pad.let_go(second).wait(200)
                        self.assertTrue(pad.has(STEERING, own) and pad.lacks(*MODIFIER_2), (direction, ms))
                        self.assertIn(own_key, pad.down())

    @scenario('90.57 T3', rests=('A7',), either=('A9', 'A32'))
    def test_a_command_and_a_lifted_thumb_in_modifier_2_add_no_cover(self):
        for first, own, own_key, second, _, _, modifier in ORDERS:
            for pad in self.each(start=('Base', STEERING)):
                pad.touch('RS').wait(300).hold(first).wait(300).hold(second).wait(60).mark()
                for _ in range(3):
                    pad.tap('A').wait(40)
                self.assertEqual(len(pad.typed()), 3)                    # the Modifier 2 key, each time
                pad.lift('RS').wait(60)
                self.assertTrue(pad.has(STEERING, own, modifier) and pad.lacks(*COVERS))
                pad.let_go(second).wait(200)
                self.assertTrue(pad.has(STEERING, own) and pad.lacks(*MODIFIER_2, *COVERS))
                self.assertEqual(pad.down(), [own_key])

    @scenario('90.57 P1', rests=('A6', 'A7', 'A10'), either=('A9', 'A32'))
    def test_a_pad_click_held_through_the_second_drivers_release_stays_down(self):
        # Until 90.56 that Release was a clear: the click's layers went, and came back only if Steam fired the
        # exposed add (90.16 X3 and 90.17 S1, which run on the 90.56 build).
        for first, own, own_key, second, _, _, modifier in ORDERS:
            for where, layer, button in (('centre', 'RTP: Middle Click', 'mouse_button MIDDLE'),
                                         ('left', 'RTP: Mouse Buttons', 'mouse_button BACK')):
                for pad in self.each(start='steering'):
                    pad.hold(first).wait(50).hold(second).wait(50).press_pad('RP', where).wait(100)
                    self.assertTrue(pad.has(modifier, layer) and button in pad.down(), where)
                    pad.mark().let_go(second).wait(200)
                    self.assertTrue(pad.has(STEERING, own, layer) and pad.lacks(*MODIFIER_2), where)
                    self.assertEqual((sorted(pad.down()), pad.typed()), (sorted([own_key, button]), []), where)
                    pad.let_go_pad('RP').wait(400).let_go(first).wait(300)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING), []))

    @scenario('90.57 M1', rules=('R133',), rests=('A7', 'A25'), either=('A9', 'A32'))
    def test_a_missed_release_of_the_second_driver_is_cleared_by_its_next_tap(self):
        for first, own, own_key, second, _, _, modifier in ORDERS:
            for pad in self.each(start=('Base', STEERING)):
                pad.hold(first).wait(300).hold(second).wait(300).miss(second).wait(500)
                self.assertTrue(pad.has(modifier))                       # nothing has told the layout yet
                pad.tap(second).wait(300)
                self.assertEqual(pad.stack, pad.layers('Base', STEERING, own))
                self.assertEqual(pad.down(), [own_key])
                pad.let_go(first).wait(300)
                self.assertEqual(pad.stack, pad.layers('Base', STEERING))

    @scenario('90.57 M2', rules=('R133', 'R174'), rests=('A7', 'A17', 'A25'), either=('A9', 'A32'), frozen='90.58')
    def test_the_hand_over_after_a_missed_second_driver_adds_a_layer_that_a_stick_touch_clears(self):
        # The add is blind: a Release can't ask whether the other driver is held. The layer types nothing.
        # On the 90.58 build: since 90.61 the layer's inverted edge chord clears it at once (90.61 E7).
        for first, own, _, second, other, _, modifier in ORDERS:
            for stick in ('LS', 'RS'):
                for pad in self.each(start=('Base', STEERING)):
                    pad.hold(first).wait(300).hold(second).wait(300).miss(second).wait(500).let_go(first).wait(300)
                    self.assertEqual(pad.stack, pad.layers('Base', STEERING, other))
                    self.assertEqual(pad.down(), [])
                    pad.touch(stick).wait(100).lift(stick).wait(400)
                    self.assertEqual(pad.stack, pad.layers('Base', STEERING))

    @scenario('90.57 M3', rules=('R133',), rests=('A7', 'A25'), either=('A9', 'A32'))
    def test_a_missed_release_of_the_first_driver_leaves_its_layer_until_a_tap_or_a_touch(self):
        for first, own, _, second, _, _, modifier in ORDERS:
            for clear in ('tap', 'LS', 'RS'):
                for pad in self.each(start=('Base', STEERING)):
                    pad.hold(first).wait(300).hold(second).wait(300).miss(first).wait(500).let_go(second).wait(300)
                    self.assertEqual(pad.stack, pad.layers('Base', STEERING, own))    # the second leaves it on
                    self.assertEqual(pad.down(), [])
                    if clear == 'tap':
                        pad.tap(first).wait(300)
                    else:
                        pad.touch(clear).wait(100).lift(clear).wait(400)
                    self.assertEqual(pad.stack, pad.layers('Base', STEERING), clear)

    @scenario('90.57 G1', rules=('R132', 'R159'), rests=('A7', 'A49'), either=('A9', 'A32'))
    def test_the_gyro_modifier_2_quick_tap_still_toggles_gyro_in_every_order(self):
        for first, second in (('L1', 'R1'), ('R1', 'L1')):
            for released in (first, second):
                for pad in self.each(start=('Base', 'Gyro')):
                    last = second if released == first else first
                    for gyro in (False, True, False):
                        pad.hold(first).wait(30).hold(second).wait(30).mark().let_go(released).wait(30).let_go(last).wait(400)
                        self.assertEqual(pad.stack, pad.layers(*home(gyro)))
                        self.assertEqual(pad.seen('beep'), [('beep', 'Gyro')])
                        self.assertEqual(pad.down(), [])


class Sweep(ScenarioCase):
    """Every two-driver gesture with the left stick, from the record of 2026-10-11 (640 a layout). Hold one
    driver, bring the stick to a state, press the other (100 or 400 ms), move the stick or not, let one driver
    go, then the other, then centre the stick.

    The two stick windows are not built yet (the author, 2026-10-12: "just dont touch the window for now"):
    a second driver pressed inside one types its key until the window closes itself, and Modifier 2 comes
    after. Those three flags are expected in a window state and nowhere else. Nothing else is flagged."""

    STATES = {'centre': lambda p, way: p,
              'out 100 ms': lambda p, way: p.push('LS', way).wait(100),
              'out 400 ms': lambda p, way: p.push('LS', way).wait(400),
              'window +20 ms': lambda p, way: p.flick('LS', way).wait(20),
              'window +100 ms': lambda p, way: p.flick('LS', way).wait(100),
              'scroll layer 60 ms': lambda p, way: p.flick('LS', way).wait(40).push('LS', way).wait(60),
              'scroll layer 400 ms': lambda p, way: p.flick('LS', way).wait(40).push('LS', way).wait(400),
              'window after scroll +20 ms': lambda p, way: p.flick('LS', way).wait(40).flick('LS', way).wait(20)}
    MOVES = {'stick as it is': lambda p, way: p,
             'stick pushed': lambda p, way: p.push('LS', way).wait(120),
             'stick centred': lambda p, way: p.recentre('LS').wait(120)}
    IN_A_WINDOW = ('typed on the way to Modifier 2', 'W and S down together', 'no Modifier 2 after the second press')

    def flags(self, pad, first, way, state, press_ms, move, release_first):
        second = 'L1' if first == 'R1' else 'R1'
        own, other = ('W', 'S') if first == 'R1' else ('S', 'W')
        pad.hold(first).wait(500)
        self.STATES[state](pad, way)
        found, since = [], len(pad.sim.log)
        pad.hold(second).wait(press_ms)
        if other in pad.down() and own in pad.down():
            found.append('W and S down together')
        if any(what == 'down' and detail == other for _, what, detail in pad.sim.log[since:]):
            found.append('typed on the way to Modifier 2')
        if not any('Modifier 2' in title for title in pad.names()):
            found.append('no Modifier 2 after the second press')
        self.MOVES[move](pad, way)
        a, b = (first, second) if release_first == 'first' else (second, first)
        pad.let_go(a).wait(120)
        if pad.lacks(STEERING):
            found.append(f'Steering gone after the {release_first} driver was let go')
        elif (other if release_first == 'first' else own) not in pad.down():
            found.append('the held driver has no key')
        pad.let_go(b).wait(300).lift('LS').wait(400)
        if pad.has(STEERING) and pad.stack != pad.layers('Base', STEERING):
            found.append('left over: ' + ', '.join(pad.names()[2:]))
        if pad.down():
            found.append('keys down at the end: ' + ', '.join(pad.down()))
        return found

    @scenario('90.57 S1', rules=('R174',), rests=('A4', 'A6', 'A7', 'A10', 'A37'), either=('A9',))
    def test_no_two_driver_gesture_outside_a_stick_window_goes_wrong(self):
        gestures = 0
        for first, way, state, press_ms, move, release_first in itertools.product(
                ('R1', 'L1'), ('up', 'down'), self.STATES, (100, 400), self.MOVES, ('first', 'second')):
            if move == 'stick pushed' and ('out' in state or 'scroll layer' in state):
                continue                                                 # the stick is out already
            for pad in self.each(start='steering'):
                gestures += 1
                found = self.flags(pad, first, way, state, press_ms, move, release_first)
                allowed = self.IN_A_WINDOW if state.startswith('window') else ()
                self.assertEqual([flag for flag in found if flag not in allowed], [],
                                 (first, way, state, press_ms, move, release_first))
        self.assertEqual(gestures, 2 * 640)                              # both layouts, A9 both ways


if __name__ == "__main__":
    unittest.main()
