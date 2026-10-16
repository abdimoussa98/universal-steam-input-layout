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

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_66 import *

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


if __name__ == "__main__":
    unittest.main()
