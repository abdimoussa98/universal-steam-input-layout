"""90.68: in the Entry Guard each driver's chord adds the driver's layer first, then removes the guard.

From 90.67. The author, 2026-10-13: "in the steering left stick guard change the execution order so that the first
thing that happens is we add either the W layer on the right bumper slash right trigger depending on the layout then
we remove the guard and then the same for the opposite side."

Between the two commands the stack is `Steering`, the guard and the driver's layer; on 90.67 it was `Steering` alone,
with its exit on up and down. The simulator runs a bind's commands with nothing in between, so it cannot tell the two
orders apart: the scenario states only that the hand-over still ends the same.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_68 import *

class Shape(unittest.TestCase):


    def test_against_90_67_only_those_two_chords_differ_and_only_in_their_order(self):
        for variant in VARIANTS:
            old, new = inputs(Layout(frozen_layout_data(variant, '90.67'))), inputs(Layout(frozen_layout_data(variant, '90.68')))
            self.assertEqual(old.keys(), new.keys())
            differ = {key for key in old if old[key] != new[key]}
            self.assertEqual(differ, {(GUARD, *where) for where in WHERE[variant]}, variant)
            for key in differ:
                for (kind, settings, ops), (was_kind, was_settings, was) in zip(new[key], old[key]):
                    self.assertEqual((kind, settings, sorted(ops)), (was_kind, was_settings, sorted(was)), key)


if __name__ == "__main__":
    unittest.main()
