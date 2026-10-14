"""90.68: in the Entry Guard each driver's chord adds the driver's layer first, then removes the guard.

From 90.67. The author, 2026-10-13: "in the steering left stick guard change the execution order so that the first
thing that happens is we add either the W layer on the right bumper slash right trigger depending on the layout then
we remove the guard and then the same for the opposite side."

Between the two commands the stack is `Steering`, the guard and the driver's layer; on 90.67 it was `Steering` alone,
with its exit on up and down. The simulator runs a bind's commands with nothing in between, so it cannot tell the two
orders apart: the scenario states only that the hand-over still ends the same.
"""

import unittest

from steam_layout.model import Layout, actions, entries
from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario
from tests.test_scenarios_90_55 import DRIVERS
from tests.test_scenarios_90_61 import inputs, named
from tests.test_scenarios_90_66 import WHERE

GUARD = 'Steering | LS: Entry Guard'


class Shape(unittest.TestCase):

    def test_each_driver_chord_in_the_entry_guard_stores_the_add_last(self):
        for variant in VARIANTS:
            layout, name = Layout(layout_data(variant)), named(variant)
            for (source, control), (_, owner, _) in zip(WHERE[variant], DRIVERS):
                (kind, chord), = entries(layout.active(GUARD)[source]['inputs'][control]['activators'])
                self.assertEqual(kind, 'chord')
                self.assertEqual(layout.layer_ops(chord), [('add_layer', name(owner)), ('remove_layer', GUARD)])   # run order
                self.assertIn('remove_layer', actions(chord)[0])
                self.assertIn('add_layer', actions(chord)[-1])              # stored last, so it runs first (A4)

    def test_against_90_67_only_those_two_chords_differ_and_only_in_their_order(self):
        for variant in VARIANTS:
            old, new = inputs(Layout(frozen_layout_data(variant, '90.67'))), inputs(Layout(frozen_layout_data(variant, '90.68')))
            self.assertEqual(old.keys(), new.keys())
            differ = {key for key in old if old[key] != new[key]}
            self.assertEqual(differ, {(GUARD, *where) for where in WHERE[variant]}, variant)
            for key in differ:
                for (kind, settings, ops), (was_kind, was_settings, was) in zip(new[key], old[key]):
                    self.assertEqual((kind, settings, sorted(ops)), (was_kind, was_settings, sorted(was)), key)
            self.assertEqual(inputs(Layout(layout_data(variant))), new, variant)             # what is installed


class TheHandOver(ScenarioCase):

    @scenario('90.68 H1', rules=('R137',), rests=('A4',), either=('A9', 'A32'))
    def test_a_driver_pressed_in_the_guard_ends_with_its_layer_on_steering_and_no_guard(self):
        for driver, owner, key in DRIVERS:
            for direction in ('up', 'down', 'left', 'right'):
                for pad in self.each():
                    pad.push('LS', direction).enter_steering(settle=False)
                    self.assertTrue(pad.has('Steering', GUARD), direction)      # the stick was out through the entry
                    pad.hold(driver).wait(60)
                    self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD), (driver, direction))
                    self.assertEqual(pad.stack.index(pad.title('Steering')) + 1, pad.stack.index(pad.title(owner)))
                    self.assertIn(key, pad.down())


if __name__ == '__main__':
    unittest.main()
