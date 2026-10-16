"""90.68: in the Entry Guard each driver's chord adds the driver's layer first, then removes the guard.

From 90.67. The author, 2026-10-13: "in the steering left stick guard change the execution order so that the first
thing that happens is we add either the W layer on the right bumper slash right trigger depending on the layout then
we remove the guard and then the same for the opposite side."

Between the two commands the stack is `Steering`, the guard and the driver's layer; on 90.67 it was `Steering` alone,
with its exit on up and down. The simulator runs a bind's commands with nothing in between, so it cannot tell the two
orders apart: the scenario states only that the hand-over still ends the same.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_68 import *

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



if __name__ == "__main__":
    unittest.main()
