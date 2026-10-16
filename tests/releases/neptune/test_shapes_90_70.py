"""90.70: every cleanup function in the Steering layers adds the Entry Guard before it removes.

From 90.68. The author, 2026-10-13: "for 90.70 keep the changes from 90.68 and have all the steering cleanups add the
entry steering guard." 90.67 had the add on the left stick's edge of ten Steering layers; a cleanup press can run past
its guard chord on any input (A69), so the other 80 cleanup presses of those layers carry it too.

The simulator never runs a press past its guard and is not made to (the author, on 90.67). The scenarios state the
ordinary cleanup, which carries the same add.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_70 import *

class Shape(unittest.TestCase):



    def test_against_90_68_eighty_presses_gain_the_add_and_nothing_else_differs(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = inputs(Layout(frozen_layout_data(variant, '90.68'))), inputs(Layout(frozen_layout_data(variant, '90.70')))
            self.assertEqual(old.keys(), new.keys())
            differ = {key for key in old if old[key] != new[key]}
            self.assertTrue(all(key[0] in {name(title) for title in EDGE_CHORDS} for key in differ), variant)
            self.assertFalse([key for key in differ if key[1:] == ('joystick', 'edge')], variant)       # 90.67 did those
            gained = 0
            for key in differ:
                for (kind, settings, ops), (was_kind, was_settings, was) in zip(new[key], old[key]):
                    self.assertEqual((kind, settings), (was_kind, was_settings), key)
                    if ops != was:
                        self.assertEqual(ops, [('add_layer', GUARD)] + was, key)
                        gained += 1
            self.assertEqual(gained, 80, variant)


if __name__ == "__main__":
    unittest.main()
