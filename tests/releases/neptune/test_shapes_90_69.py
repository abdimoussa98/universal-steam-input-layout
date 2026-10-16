"""90.69, a trial off the line: no Hold to Repeat on the cleanup presses in the Steering layers.

From 90.68, not installed (90.70 is, also from 90.68). The author, 2026-10-13: "we've never tried just making the
regular press no longer repeating. Still interruptible, but no longer repeating", scope "all in steering", and "undo
the change to add the layer the entry guard in the cleanup functions for now".

Every test here reads the 90.69 build. Whether the missing repeat keeps a press from running past its guard chord
(A69) is for the Deck: the simulator decides a guard once and never fails it, and it does not run a held-back
repeating press when its guard goes either, so it shows no difference under an input that is already held.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_69 import *

class Shape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Read-only 90.69 trial inventory, kept separate from live 90.70 descendants."""
        cls.layouts = {variant: Layout(frozen_layout_data(variant, '90.69')) for variant in VARIANTS}
        cls.cleanup_rows = {variant: cleanups(layout) for variant, layout in cls.layouts.items()}

    def test_the_ninety_steering_cleanup_presses_are_interruptible_and_do_not_repeat(self):
        for variant in VARIANTS:
            name = named(variant)
            found = [t for t in self.cleanup_rows[variant] if t.layer.startswith('Steering')]
            self.assertEqual(len(found), 90, variant)
            self.assertEqual({t.layer for t in found}, {name(title) for title in EDGE_CHORDS})
            for t in found:
                settings = dict(t.settings)
                self.assertEqual((t.activator, t.interruptible), ('Full_Press', True), t)
                self.assertNotIn('hold_repeats', settings, t)
                self.assertNotIn('delay_start', settings, t)
                self.assertTrue(all(op == 'remove_layer' for op, _ in t.ops), t)          # no Entry Guard add

    def test_every_cleanup_press_outside_the_steering_layers_still_repeats(self):
        for variant in VARIANTS:
            found = [t for t in self.cleanup_rows[variant] if not t.layer.startswith('Steering')]
            self.assertEqual(len(found), {'default': 439, 'alternative': 465}[variant])
            self.assertTrue(all(dict(t.settings).get('hold_repeats') == '1' for t in found), variant)

    def test_against_90_68_only_those_presses_differ(self):
        for variant in VARIANTS:
            old_layout = Layout(frozen_layout_data(variant, '90.68'))
            new_layout = self.layouts[variant]
            old, new = inputs(old_layout), inputs(new_layout)
            self.assertEqual(old.keys(), new.keys())
            wanted = {(t.layer, t.source, t.input) for t in self.cleanup_rows[variant] if t.layer.startswith('Steering')}
            self.assertEqual({key for key in old if old[key] != new[key]}, wanted, variant)
            for key in wanted:
                for (kind, settings, ops), (was_kind, was_settings, was) in zip(new[key], old[key]):
                    if kind != 'Full_Press' or 'hold_repeats' not in was_settings:
                        self.assertEqual((kind, settings, ops), (was_kind, was_settings, was), key)
                        continue
                    self.assertEqual(settings, {k: v for k, v in was_settings.items() if k != 'hold_repeats'}, key)
                    self.assertEqual(ops, [op for op in was if op != ('add_layer', GUARD)], key)


if __name__ == "__main__":
    unittest.main()
