"""90.64: the layer list in a new order. From 90.63, with no bind, setting or group changed.

The author, 2026-10-12: "keep the initial order ramp up 0, ramp up 1. then the stateful base layers: gyro,
steering, cursor gyro, menu, gamepad. then the other layer still separate by the parent statful layers, so all
the base then gyro, so on so forth. Within that group ... determine the order yourself".

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.layer_order_90_64 import *

class LayerOrder(unittest.TestCase):





    def test_every_layer_is_bind_for_bind_what_it_was_on_90_63(self):
        for variant in VARIANTS:
            old, new = (builder.layers_by_title(_readable(frozen_layout_data(variant, version))) for version in ('90.63', '90.64'))
            self.assertEqual(old, new, variant)


if __name__ == "__main__":
    unittest.main()
