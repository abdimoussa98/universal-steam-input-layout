"""90.62: rocking in Steering the way the bumper modifiers do it.

From 90.61. With one driver held, pressing the other adds the other driver's layer and then Modifier 2 on top of
it. A Release inside Modifier 2 only removes: the layer of the driver still held is underneath already. Until
90.61 the first driver's Release added it (the hand-over of 90.57), and on the Deck W to S worked and S back to W
did not (author, 2026-10-12). The simulator played both directions before and plays them now.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_62 import *

class Shapes(unittest.TestCase):




    def test_against_90_61_only_the_two_driver_layers_and_the_two_modifier_2_layers_change(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = inputs(Layout(frozen_layout_data(variant, '90.61'))), inputs(Layout(built(variant)))
            self.assertEqual(old.keys(), new.keys())
            changed = {key for key in old if old[key] != new[key]}
            self.assertEqual({title for title, _, _ in changed}, {name(t) for t in (W, S, *MODIFIER_2)}, variant)
            self.assertEqual(len(changed), 2 + 2 * 18, variant)        # two chords; per Modifier 2, two Releases and sixteen cleanups
            count = lambda rows: sum(1 for found in rows.values() for _, _, ops in found
                                     for op in ops if isinstance(op, tuple) and op[0] == 'remove_layer')
            self.assertEqual((count(old), count(new)), REMOVES[variant])
            self.assertEqual(inputs(Layout(frozen_layout_data(variant, '90.64'))), new, variant)  # up to 90.64; 90.65 changes ten edges


if __name__ == "__main__":
    unittest.main()
