"""90.66: in `Steering` each driver mode-shifts the left stick to a group whose up and down are empty.

From 90.65. Confirmed by the author on the Deck, 2026-10-13 (A69): a burst of `remove_layer` calls makes a chord
evaluate again and an evaluation can fail, so the interruptible press beside a guard chord runs. In `Steering`
that took the driver's layer off with the driver held, and `Steering`'s exit on up or down then ended `Steering`.

The author: "in steering base if you are pressing bumper/triggers the up and down on left stick will be empty
binds, this protects from that edge case kicking us out of the steering stateful set accidently. I also want you
to remove the 5sec delay". The 5 ms start delay of 90.65 is gone from the ten left-edge cleanup presses.

The simulator never fails a guard, so the scenarios take the driver's layer off by hand (`drop`). What a mode shift
bound in a layer does on the Deck is A70, unverified: the simulator has it on while its layer answers the held
driver, in place of that layer's own stick group only.

90.67 took the mode shift out again (author, 2026-10-13: "revert the mode shift change"), so everything here reads
the 90.66 build.
"""

import unittest

from steam_layout.model import EMPTY, MODE_SHIFT, Layout, actions, entries
from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, scenario
from tests.test_scenarios_90_55 import DRIVERS, EDGE_CHORDS
from tests.test_scenarios_90_61 import inputs, named

STEERING = 'Steering'
WHERE = {'default': (('switch', 'right_bumper'), ('switch', 'left_bumper')),
         'alternative': (('right_trigger', 'edge'), ('left_trigger', 'edge'))}
EXIT = {'up': 'dpad_north', 'down': 'dpad_south'}


def shift_groups(layout):
    return {gid: state for gid, state in layout.presets[STEERING]['group_source_bindings'].items() if 'modeshift' in state}


class Shape(unittest.TestCase):

    def test_steering_has_one_mode_shift_group_with_a_and_d_and_empty_up_and_down(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, '90.66'))
            found = shift_groups(layout)
            self.assertEqual(list(found.values()), ['joystick inactive modeshift'], variant)
            group, own = layout.groups[next(iter(found))], layout.active(STEERING)['joystick']
            self.assertEqual((group['mode'], group['settings']), (own['mode'], own['settings']))
            self.assertEqual(set(group['inputs']), set(own['inputs']))
            for name in ('dpad_east', 'dpad_west'):
                self.assertEqual(group['inputs'][name], own['inputs'][name], name)
            for name in EXIT.values():
                (kind, entry), = entries(group['inputs'][name]['activators'])
                self.assertEqual(kind, 'Full_Press')
                self.assertTrue(all(a.startswith(EMPTY) for a in actions(entry)), name)
                self.assertEqual(layout.layer_ops(next(entries(own['inputs'][name]['activators']))[1]),
                                 [('remove_layer', STEERING)])                 # the exit itself is untouched

    def test_each_driver_in_steering_shifts_the_left_stick_with_an_uninterruptible_press_before_its_chord(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, '90.66'))
            gid, = shift_groups(layout)
            for source, name in WHERE[variant]:
                (kind, press), (second, chord) = entries(layout.active(STEERING)[source]['inputs'][name]['activators'])
                self.assertEqual((kind, second), ('Full_Press', 'chord'), name)
                self.assertEqual(MODE_SHIFT.search(actions(press)[0]).groups(), ('joystick', gid))
                self.assertEqual(press['settings'], {'interruptable': '0', 'haptic_intensity': '0'})
                self.assertEqual([op for op, _ in layout.layer_ops(chord)], ['add_layer'])
                self.assertEqual(chord['settings']['hold_repeats'], '1')        # it puts the driver's layer back

    def test_no_other_layer_has_a_mode_shift(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, '90.66'))
            found = {title for title in layout.presets if title != layout.base
                     for group in layout.active(title).values() for value in group.get('inputs', {}).values()
                     for _, entry in entries(value.get('activators') or {}) if any(MODE_SHIFT.search(a) for a in actions(entry))}
            self.assertEqual(found, {STEERING}, variant)

    def test_the_ten_left_edge_presses_have_no_start_delay(self):
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.66')), named(variant)
            old = Layout(frozen_layout_data(variant, '90.58'))
            for title in EDGE_CHORDS:
                (kind, press), (_, guard), *_ = entries(layout.active(name(title))['joystick']['inputs']['edge']['activators'])
                (_, was), (_, was_guard), *_ = entries(old.active(name(title))['joystick']['inputs']['edge']['activators'])
                self.assertEqual(kind, 'Full_Press')
                self.assertEqual((press['settings'], guard), (was['settings'], was_guard), title)   # as on 90.58

    def test_against_90_65_only_the_two_drivers_and_the_ten_edges_differ_and_no_remove(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = inputs(Layout(frozen_layout_data(variant, '90.65'))), inputs(Layout(frozen_layout_data(variant, '90.66')))
            self.assertEqual(old.keys(), new.keys())
            self.assertEqual({key for key in old if old[key] != new[key]},
                             {(name(title), 'joystick', 'edge') for title in EDGE_CHORDS}
                             | {(STEERING, *where) for where in WHERE[variant]}, variant)
            count = lambda rows: sum(1 for found in rows.values() for _, _, ops in found
                                     for op in ops if isinstance(op, tuple) and op[0] == 'remove_layer')
            self.assertEqual(count(old), count(new))


class TheLeak(ScenarioCase):
    """The driver's layer goes with the driver held (A69). `Steering` has to stay and the layer come back."""

    def out(self, frozen=None):
        for driver, owner, key in DRIVERS:
            for direction in EXIT:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).push('LS', direction).wait(400)
                    yield pad, driver, pad.title(owner), key, direction

    @scenario('90.66 S1', rests=('A6', 'A69', 'A70'), either=('A9', 'A32'), frozen='90.66')
    def test_the_driver_layer_leaking_off_with_the_stick_up_or_down_keeps_steering(self):
        for pad, driver, owner, key, direction in self.out():
            pad.sim.drop(*(t for t in pad.stack if t.startswith('Steering |')))      # the driver's layer and the stick's
            self.assertTrue(pad.has('Steering'), (driver, direction))
            pad.wait(60)                                     # the driver's repeating chord, every 50 ms
            self.assertTrue(pad.has('Steering', owner), (driver, direction))
            self.assertIn(key, pad.down())
            pad.recentre('LS').wait(300).let_go(driver).wait(300)
            self.assertEqual(pad.stack[:2], pad.layers('Base', 'Steering'))
            self.assertTrue(pad.lacks(owner))

    @scenario('90.66 S2', rests=('A69',), either=('A9', 'A32'), frozen='90.65')
    def test_on_90_65_the_same_leak_ends_steering(self):
        for pad, driver, owner, key, direction in self.out():
            pad.sim.drop(*(t for t in pad.stack if t.startswith('Steering |')))
            pad.wait(60)
            self.assertTrue(pad.lacks('Steering'), (driver, direction))

    @scenario('90.66 S3', rests=('A70',), either=('A9', 'A32'), frozen='90.66')
    def test_with_no_driver_held_up_and_down_still_end_steering(self):
        for direction in EXIT:
            for pad in self.each(start=('Base', 'Steering')):
                pad.push('LS', direction).wait(100)
                self.assertTrue(pad.lacks('Steering'), direction)

    @scenario('90.66 S4', rests=('A10', 'A69', 'A70'), either=('A9', 'A32'), frozen='90.66')
    def test_a_and_d_stay_down_through_the_leak(self):
        for driver, owner, key in DRIVERS:
            for direction, letter in (('left', 'A'), ('right', 'D')):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300).push('LS', direction).wait(200)
                    self.assertEqual(pad.down(), sorted([letter, key]))
                    pad.sim.drop(pad.title(owner))
                    self.assertIn(letter, pad.down())
                    pad.wait(60)
                    self.assertTrue(pad.has('Steering', pad.title(owner)))
                    self.assertEqual(pad.down(), sorted([letter, key]))

    @scenario('90.66 S5', rests=('A70',), either=('A9', 'A32'), frozen='90.66')
    def test_the_stick_still_scrolls_in_the_driver_layer(self):
        # The shift is held from `Steering` underneath; the driver's layer has its own stick group (A70).
        for driver, owner, _ in DRIVERS:
            for direction in EXIT:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(300)
                    pad.mark()
                    pad.flick('LS', direction, 60).wait(300)
                    self.assertEqual(len([t for t in pad.typed() if 'SCROLL' in t]), 1, (driver, direction))
                    self.assertTrue(pad.has('Steering', pad.title(owner)))


if __name__ == '__main__':
    unittest.main()
