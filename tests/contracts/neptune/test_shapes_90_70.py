"""90.70: every cleanup function in the Steering layers adds the Entry Guard before it removes.

From 90.68. The author, 2026-10-13: "for 90.70 keep the changes from 90.68 and have all the steering cleanups add the
entry steering guard." 90.67 had the add on the left stick's edge of ten Steering layers; a cleanup press can run past
its guard chord on any input (A69), so the other 80 cleanup presses of those layers carry it too.

The simulator never runs a press past its guard and is not made to (the author, on 90.67). The scenarios state the
ordinary cleanup, which carries the same add.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_70 import *

class Shape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Current cleanup inventory; the 90.68 -> 90.70 delta remains independently frozen."""
        cls.layouts = {variant: Layout(layout_data(variant)) for variant in VARIANTS}
        cls.cleanup_rows = {variant: cleanups(layout) for variant, layout in cls.layouts.items()}

    def test_every_steering_cleanup_press_repeats_and_stores_the_entry_guard_add_last(self):
        for variant in VARIANTS:
            layout, name = self.layouts[variant], named(variant)
            found = [t for t in self.cleanup_rows[variant] if t.layer.startswith('Steering')]
            self.assertEqual(len(found), 90, variant)
            self.assertEqual({t.layer for t in found}, {name(title) for title in EDGE_CHORDS})
            for t in found:
                _, entry = list(entries(layout.active(t.layer)[t.source]['inputs'][t.input]['activators']))[t.index]
                self.assertEqual(t.ops[0], ('add_layer', GUARD), t)                       # in run order
                self.assertTrue(all(op == 'remove_layer' for op, _ in t.ops[1:]) and len(t.ops) > 1, t)
                self.assertIn('add_layer', actions(entry)[-1], t)                         # stored last (A4)
                self.assertEqual((entry['settings'].get('hold_repeats'), t.interruptible), ('1', True), t)

    def test_no_cleanup_function_outside_the_steering_layers_adds_a_layer(self):
        for variant in VARIANTS:
            found = [t for t in self.cleanup_rows[variant] if not t.layer.startswith('Steering')]
            # 439 and 465 until 90.71; 90.72 adds the pad layers' sixteen stick-edge cleanups.
            self.assertEqual(len(found), {'default': 455, 'alternative': 481}[variant])
            self.assertFalse([t for t in found if any(op == 'add_layer' for op, _ in t.ops)], variant)



if __name__ == "__main__":
    unittest.main()
