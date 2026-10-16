"""90.67: the mode shift of 90.66 is gone; the ten left-edge cleanup presses add the Entry Guard before they remove.

From 90.66. The author, 2026-10-13: "revert the mode shift change. I still want keep the removal of the delays on
the clean up functions though. ... for the left stick clean up removals to before cleaning up i want you to add the
left stick steering guard, this is a precaution for the weird edge case where the guard would fail for repeated
removal calls."

A press that runs past its guard chord (A69) then leaves `Steering | LS: Entry Guard` on top, not `Steering` and its
exit on up and down. The simulator never runs a press past its guard and is not made to (the author: "I don't think
we need to necessarily account for that super edge case"). The scenarios state the ordinary cleanup, which carries
the same add: after a missed driver release the stick at the rim leaves the Entry Guard, and `Steering` stays.

90.70 put the add on every cleanup press of the ten layers, so the shape tests here read the 90.67 build; the
scenarios hold on the working layout too.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_67 import *

class Shape(unittest.TestCase):

    def test_no_layer_has_a_mode_shift_and_steering_has_no_mode_shift_group(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, '90.67'))
            found = {title for title in layout.presets if title != layout.base
                     for group in layout.active(title).values() for value in group.get('inputs', {}).values()
                     for _, entry in entries(value.get('activators') or {}) if any(MODE_SHIFT.search(a) for a in actions(entry))}
            self.assertEqual(found, set(), variant)
            self.assertFalse([s for s in layout.presets[STEERING]['group_source_bindings'].values() if 'modeshift' in s])
            for source, name in WHERE[variant]:
                (kind, chord), = entries(layout.active(STEERING)[source]['inputs'][name]['activators'])
                self.assertEqual((kind, [op for op, _ in layout.layer_ops(chord)]), ('chord', ['add_layer']), name)

    def test_each_of_the_ten_presses_is_90_66s_with_the_entry_guard_add_stored_last(self):
        for variant in VARIANTS:
            layout, old, name = Layout(frozen_layout_data(variant, '90.67')), Layout(frozen_layout_data(variant, '90.66')), named(variant)
            for title in EDGE_CHORDS:
                (kind, press), *rest = edge(layout, name(title))
                (_, was), *was_rest = edge(old, name(title))
                self.assertEqual(kind, 'Full_Press', title)
                self.assertEqual(layout.layer_ops(press), [('add_layer', GUARD)] + old.layer_ops(was), title)   # in run order
                self.assertEqual(actions(press)[:-1], actions(was), title)
                self.assertIn('add_layer', actions(press)[-1], title)             # stored last, so it runs first (A4)
                self.assertEqual(press['settings'], was['settings'], title)
                self.assertNotIn('delay_start', press['settings'], title)
                self.assertEqual(rest, was_rest, title)                              # the guard chord, the timers

    def test_the_ten_presses_are_still_cleanup_functions(self):
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.67')), named(variant)
            found = {t.layer for t in Cleanups(layout).inv.transitions
                     if t.role == 'recovery' and (t.source, t.input) == ('joystick', 'edge')}
            self.assertLessEqual({name(title) for title in EDGE_CHORDS}, found, variant)

    def test_no_other_cleanup_function_adds_a_layer(self):
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.67')), named(variant)
            adding = {(t.layer, t.source, t.input) for t in Cleanups(layout).inv.transitions
                      if t.role == 'recovery' and any(op == 'add_layer' for op, _ in t.ops)}
            self.assertEqual(adding, {(name(title), 'joystick', 'edge') for title in EDGE_CHORDS}, variant)

    def test_against_90_66_only_the_two_drivers_and_the_ten_edges_differ_and_no_remove(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = inputs(Layout(frozen_layout_data(variant, '90.66'))), inputs(Layout(frozen_layout_data(variant, '90.67')))
            self.assertEqual(old.keys(), new.keys())
            self.assertEqual({key for key in old if old[key] != new[key]},
                             {(name(title), 'joystick', 'edge') for title in EDGE_CHORDS}
                             | {(STEERING, *where) for where in WHERE[variant]}, variant)
            count = lambda rows, wanted: sum(1 for found in rows.values() for _, _, ops in found
                                             for op in ops if isinstance(op, tuple) and op[0] == wanted)
            self.assertEqual(count(old, 'remove_layer'), count(new, 'remove_layer'))
            self.assertEqual(count(old, 'add_layer') + 10, count(new, 'add_layer'))


if __name__ == "__main__":
    unittest.main()
