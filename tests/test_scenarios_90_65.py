"""90.65: the left edge of ten Steering layers cleans up with the press and its guard chord again, 5 ms late.

From 90.64. The author, 2026-10-13: "change the steering left stick clean up back to the non inverted chord with
interruptible regular press removals pattern we'd had before. Make the left in those steering layers also no
longer have the edge inverted ... the regular press removal to also have a start delay of 5ms".

On each of the ten edges: a repeating, interruptible Regular Press of removes with a start delay of 5 ms and,
beside it, an empty chord on the drivers that is not interruptible (the shape of 90.56 to 90.58, R133). The
ring is a normal ring again, so the press runs with the stick at the rim and no driver held.

The simulator never misses a held driver, so nothing here shows the Deck fault of 90.58 fixed
(findings/2026-10-12-steering-ends-on-a-stick-touch).

90.66 took the 5 ms off again (tests/test_scenarios_90_66.py): the shape tests and the two scenarios that state
the delay (P2, P3) run on the 90.65 build.
"""

import unittest

from steam_layout.model import EMPTY, Layout, actions, entries
from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, scenario
from tests.test_scenarios_90_55 import DRIVERS, EDGE_CHORDS, FAMILY, SIDES, TIMERS
from tests.test_scenarios_90_61 import GUARD, inputs, named

DELAY = '5'


def edge(layout, title):
    return list(entries(layout.active(title)['joystick']['inputs']['edge']['activators']))


class OnlyTheTenEdgesChange(unittest.TestCase):

    def test_against_90_64_ten_left_edges_and_their_ten_rings_differ_and_nothing_else(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = Layout(frozen_layout_data(variant, '90.64')), Layout(frozen_layout_data(variant, '90.65'))
            a, b = inputs(old), inputs(new)
            self.assertEqual(a.keys(), b.keys())
            self.assertEqual({key for key in a if a[key] != b[key]},
                             {(name(title), 'joystick', 'edge') for title in EDGE_CHORDS}, variant)
            differ = {(title, source) for title in old.presets for source, group in old.active(title).items()
                      if group.get('settings') != new.active(title)[source].get('settings')}
            self.assertEqual(differ, {(name(title), 'joystick') for title in EDGE_CHORDS}, variant)
            for title, source in differ:
                x, y = old.active(title)[source]['settings'], new.active(title)[source]['settings']
                self.assertEqual({k for k in x if x[k] != y[k]}, {'edge_binding_invert'}, title)

    def test_each_press_carries_the_list_the_chord_had_on_90_64_command_for_command(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = Layout(frozen_layout_data(variant, '90.64')), Layout(frozen_layout_data(variant, '90.65'))
            for title in EDGE_CHORDS:
                (_, chord), *_ = edge(old, name(title))
                (_, press), (_, guard), *_ = edge(new, name(title))
                self.assertEqual(actions(chord), actions(press), title)
                self.assertEqual(chord['settings']['gyro_ratchet_button_mask'], guard['settings']['gyro_ratchet_button_mask'])

    def test_the_press_and_the_guard_have_their_90_58_settings_and_the_press_a_5_ms_start_delay(self):
        timers = {layer for layer, *_ in TIMERS}
        for variant in VARIANTS:
            name = named(variant)
            old, new = Layout(frozen_layout_data(variant, '90.58')), Layout(frozen_layout_data(variant, '90.65'))
            for title in EDGE_CHORDS:
                found = edge(new, name(title))
                self.assertEqual([kind for kind, _ in found],
                                 ['Full_Press', 'chord', 'Soft_Press'] if title in timers else ['Full_Press', 'chord'], title)
                (_, was_press), (_, was_guard), *_ = edge(old, name(title))
                press, guard = found[0][1], found[1][1]
                self.assertEqual(press['settings'], {**was_press['settings'], 'delay_start': DELAY}, title)
                self.assertEqual(press['settings']['hold_repeats'], '1')
                self.assertNotEqual(press['settings'].get('interruptable'), '0')         # the guard holds it back
                self.assertEqual(guard, was_guard, title)
                self.assertTrue(all(a.startswith(EMPTY) for a in actions(guard)), title)
                self.assertEqual(guard['settings']['interruptable'], '0')
                self.assertNotIn('edge_binding_invert', guard['settings'])
                ops = new.layer_ops(press)
                self.assertIn(('remove_layer', name(title)), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)

    def test_no_steering_layer_has_an_inverted_ring_and_only_the_entry_guard_an_inverted_chord(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, '90.65'))
            steering = [t for t in layout.presets if t.startswith('Steering') and 'joystick' in layout.active(t)]
            self.assertFalse([t for t in steering if layout.active(t)['joystick'].get('settings', {}).get('edge_binding_invert') == '1'])
            found = {(title, source, control) for title in layout.presets
                     for source, group in layout.active(title).items()
                     for control, value in (group.get('inputs') or {}).items()
                     for kind, entry in entries(value.get('activators', {}))
                     if kind == 'chord' and (entry.get('settings') or {}).get('edge_binding_invert') == '1'}
            self.assertEqual(found, {(GUARD, 'joystick', 'edge')}, variant)

    def test_the_5_ms_press_is_the_only_delayed_regular_press_on_a_steering_stick(self):
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.65')), named(variant)
            found = {title for title in layout.presets if title.startswith('Steering') and 'joystick' in layout.active(title)
                     for control, value in layout.active(title)['joystick']['inputs'].items()
                     for kind, entry in entries(value.get('activators', {}))
                     if kind == 'Full_Press' and entry.get('settings', {}).get('delay_start')}
            self.assertEqual(found, {name(title) for title in EDGE_CHORDS}, variant)


class EdgeCleanupLate(ScenarioCase):
    """The press runs 5 ms after the stick reaches the rim, unless a driver is held: the guard chord holds it back."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.65 P1', rules=('R133', 'R170'), rests=('A27', 'A36', 'A68'), either=('A9', 'A32'))
    def test_no_stick_movement_removes_the_driver_layer_while_the_driver_is_held(self):
        for pad, _, owner, key in self.held():
            for direction in ('up', 'down', 'up', 'left', 'right', 'down'):
                for ms in (3, 30, 60, 150, 300):
                    pad.flick('LS', direction, ms)
                    self.assertTrue(pad.has('Steering', owner))
                    self.assertIn(key, pad.down())
                    pad.wait(40)
            for _ in range(3):                               # the edge alone, out and back
                pad.hold('LS edge').wait(300).let_go('LS edge').wait(40)
                self.assertTrue(pad.has('Steering', owner))
            pad.wait(400)
            self.assertTrue(pad.has('Steering', owner) and pad.lacks(*FAMILY))
            self.assertEqual(pad.down(), [key])

    @scenario('90.65 P2', rules=('R133',), rests=('A25', 'A27', 'A68'), either=('A9', 'A32'), frozen='90.65')
    def test_a_missed_driver_release_clears_5_ms_after_the_stick_reaches_the_rim(self):
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(400)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(3)
            self.assertTrue(pad.has(owner))                  # the start delay
            pad.wait(10)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            pad.let_go('LS edge').wait(100)
            self.assertEqual(pad.down(), [])

    @scenario('90.65 P3', rules=('R133',), rests=('A25', 'A27', 'A68'), either=('A9', 'A32'), frozen='90.65')
    def test_a_stick_back_off_the_rim_inside_5_ms_leaves_the_layer_for_the_next_reach(self):
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(400)
            pad.hold('LS edge').wait(3).let_go('LS edge').wait(200)
            self.assertTrue(pad.has(owner))
            pad.hold('LS edge').wait(20)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))

    @scenario('90.65 P4', rules=('R133',), rests=('A27', 'A36', 'A68'), either=('A9', 'A32'))
    def test_pressing_the_driver_again_holds_the_press_back_at_the_rim(self):
        for pad, driver, owner, key in self.held():
            pad.miss(driver).wait(100).hold(driver).wait(100)
            pad.hold('LS edge').wait(300).let_go('LS edge').wait(100)
            self.assertTrue(pad.has('Steering', owner))
            self.assertIn(key, pad.down())

    @scenario('90.65 P5', rules=('R133',), rests=('A7', 'A27', 'A36', 'A68'), either=('A9', 'A32'))
    def test_the_reported_gesture_keeps_steering_and_the_driver_layer_on_the_simulator(self):
        # A driver held, the right stick touch tapped, the left stick flicked to the rim and back. On the Deck
        # this ended `Steering` on 90.58, which had this press without the 5 ms. The simulator kept it there too.
        for driver, owner, key in DRIVERS:
            for direction in ('up', 'down', 'left', 'right'):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(100).touch('RS')
                    for step in range(8):
                        pad.wait(35).lift('RS').wait(35).touch('RS')
                        if step % 2:
                            pad.recentre('LS')
                        else:
                            pad.push('LS', direction)
                    pad.lift('RS').recentre('LS').wait(400)
                    self.assertTrue(pad.has('Steering', owner), direction)
                    self.assertEqual(pad.down(), [key])

    @scenario('90.65 P6', rules=('R133',), rests=('A64', 'A65'), either=('A9', 'A32'))
    def test_the_timers_on_those_edges_still_run_with_the_stick_out(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, modifier, *_ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).push('LS', direction).wait(100)
                    self.assertTrue(pad.has(owner, modifier) and pad.lacks('Steering | LS: Tap Cover'))
                    pad.wait(200)                            # the 200 ms timer on the modifier's edge
                    self.assertTrue(pad.has(owner, modifier, 'Steering | LS: Tap Cover'), direction)
                    pad.recentre('LS').wait(300)
                    self.assertTrue(pad.has('Steering', owner))


if __name__ == '__main__':
    unittest.main()
