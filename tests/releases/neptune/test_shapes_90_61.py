"""90.61: on the left stick's edge of ten Steering layers the cleanup is one chord with Invert Activation again.

From 90.58, one change: the repeating Regular Press and its guard chord become one repeating chord on the same
drivers with Invert Activation, carrying the press's list. For an open Deck fault
(findings/2026-10-12-steering-ends-on-a-stick-touch): the driver layer's press ran although its bumper was held.
The simulator does not reproduce the fault, so nothing here shows it fixed.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_61 import *

class OnlyTheTenEdgesChange(unittest.TestCase):
    """The author, 2026-10-12: "all we're doing is updating the edge cleanup bind on the left stick. And all the
    steering layers." And, before the build: "you're going to be keeping the removal lists from ninety fifty eight"."""

    @classmethod
    def setUpClass(cls):
        # Distinct frozen sources: the 90.61 build/delta and the later 90.64 shape.
        cls.layouts = {variant: {
            'old': Layout(frozen_layout_data(variant, '90.58')),
            'built': Layout(built(variant)),
            'later': Layout(frozen_layout_data(variant, '90.64')),
        } for variant in VARIANTS}
        cls.rows = {variant: {stage: inputs(layout) for stage, layout in layouts.items() if stage != 'later'}
                    for variant, layouts in cls.layouts.items()}

    def test_against_90_58_ten_left_edges_differ_and_nothing_else(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = self.rows[variant]['old'], self.rows[variant]['built']
            self.assertEqual(old.keys(), new.keys())
            self.assertEqual({key for key in old if old[key] != new[key]},
                             {(name(title), 'joystick', 'edge') for title in EDGE_CHORDS}, variant)

    def test_each_chord_carries_the_list_its_press_had_on_90_58_command_for_command(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = self.layouts[variant]['old'], self.layouts[variant]['built']
            count = lambda rows: sum(1 for found in rows.values() for _, _, ops in found
                                       for op in ops if isinstance(op, tuple) and op[0] == 'remove_layer')
            self.assertEqual((count(self.rows[variant]['old']), count(self.rows[variant]['built'])),
                             (REMOVES[variant],) * 2)
            for title in EDGE_CHORDS:
                edge = lambda layout: list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))
                (_, press), (_, guard), *_ = edge(old)
                (_, chord), *_ = edge(new)
                self.assertEqual(old.layer_ops(press), new.layer_ops(chord), title)
                self.assertEqual(len(actions(press)), len(actions(chord)), title)
                self.assertEqual(guard['settings']['gyro_ratchet_button_mask'], chord['settings']['gyro_ratchet_button_mask'])

    def test_the_left_edge_is_one_inverted_chord_and_the_timer_stays_a_soft_press(self):
        timers = {layer: (target, delay) for layer, _, target, delay, _ in TIMERS}
        for variant in VARIANTS:
            layout, name = self.layouts[variant]['later'], named(variant)   # 90.65 put the press back
            for title in EDGE_CHORDS:
                found = list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))
                self.assertEqual([kind for kind, _ in found], ['chord', 'Soft_Press'] if title in timers else ['chord'], title)
                settings = dict(found[0][1]['settings'])
                mask = int(settings.pop('gyro_ratchet_button_mask'))
                self.assertEqual(settings, {'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                                            'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}, title)
                self.assertFalse(mask & DEFLECT)
                ops = layout.layer_ops(found[0][1])
                self.assertIn(('remove_layer', name(title)), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)
                if title in timers:
                    self.assertEqual(layout.layer_ops(found[1][1]), [('add_layer', timers[title][0])], title)

    def test_the_two_driver_layers_chords_have_one_sub_command(self):
        # A repeating chord with more than one sub-command does not fire its repeat (author, 2026-10-10). The
        # driver layers' chords have one; the other eight keep 90.58's lists of two to five.
        for variant in VARIANTS:
            layout, name = self.layouts[variant]['built'], named(variant)        # 90.62 adds one to the two Modifier 2 lists
            sizes = {title: len(actions(list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))[0][1]))
                     for title in EDGE_CHORDS}
            self.assertEqual([sizes[owner] for _, owner, _ in DRIVERS], [1, 1])
            self.assertEqual(sorted(set(sizes.values())), [1, 2, 3, 5], variant)

    def test_inverted_chords_are_on_the_left_edge_of_the_ten_layers_and_the_entry_guard_only(self):
        for variant in VARIANTS:
            layout, name = self.layouts[variant]['later'], named(variant)   # 90.65 put the press back
            found = {(title, source, control) for title in layout.presets
                     for source, group in layout.active(title).items()
                     for control, value in (group.get('inputs') or {}).items()
                     for kind, entry in entries(value.get('activators', {}))
                     if kind == 'chord' and (entry.get('settings') or {}).get('edge_binding_invert') == '1'}
            self.assertEqual(found, {(name(t), 'joystick', 'edge') for t in (*EDGE_CHORDS, GUARD)}, variant)


if __name__ == "__main__":
    unittest.main()
