"""90.63: the ring is inverted on the left edge of ten Steering layers.

From 90.62, one setting in ten groups: Outer Ring Binding Invert on the left stick. The chord with Invert
Activation that has been the edge's cleanup function since 90.61 then runs with the stick at the rim and no
driver held, where it ran off the rim. The author, 2026-10-12: "We need to invert the left stick edge for the
chorded inverted clean functions ... every where in steering except in entry steering guard."

The Soft Press timers on four of those edges don't follow the ring's setting (author, A67).

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_63 import *

class OnlyTheRingChanges(unittest.TestCase):

    def test_against_90_62_ten_left_stick_groups_differ_by_one_setting(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = Layout(frozen_layout_data(variant, '90.62')), Layout(frozen_layout_data(variant, '90.63'))
            self.assertEqual(inputs(old), inputs(new), variant)                  # no bind, list or activator setting
            differ = {(title, source) for title in old.presets for source, group in old.active(title).items()
                      if group != new.active(title)[source]}
            self.assertEqual(differ, {(name(title), 'joystick') for title in EDGE_CHORDS}, variant)
            for title, source in differ:
                a, b = old.active(title)[source]['settings'], new.active(title)[source]['settings']
                self.assertEqual({k for k in a if a[k] != b[k]}, {'edge_binding_invert'}, title)

    def test_the_ring_is_inverted_in_the_ten_layers_and_in_no_other_steering_layer(self):
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.64')), named(variant)   # 90.65 took the inversion off
            found = {title for title in layout.presets if title.startswith('Steering')
                     and layout.active(title).get('joystick', {}).get('settings', {}).get('edge_binding_invert') == '1'}
            self.assertEqual(found, {name(title) for title in EDGE_CHORDS}, variant)
            self.assertEqual(layout.active(GUARD)['joystick']['settings']['edge_binding_invert'], '0')

    def test_the_timers_on_those_edges_state_no_inversion_of_their_own(self):
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.64')), named(variant)   # 90.65 took the inversion off
            for title, *_ in TIMERS:
                soft = dict(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))['Soft_Press']
                self.assertNotIn('edge_binding_invert', soft['settings'], title)


if __name__ == "__main__":
    unittest.main()
