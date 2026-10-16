"""90.64: the layer list in a new order. From 90.63, with no bind, setting or group changed.

The author, 2026-10-12: "keep the initial order ramp up 0, ramp up 1. then the stateful base layers: gyro,
steering, cursor gyro, menu, gamepad. then the other layer still separate by the parent statful layers, so all
the base then gyro, so on so forth. Within that group ... determine the order yourself".

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.layer_order_90_64 import *

class LayerOrder(unittest.TestCase):

    def test_the_ramp_then_the_five_stateful_layers_come_first(self):
        for variant in VARIANTS:
            self.assertEqual(titles(layout_data(variant))[:7], ['Turning Ramp Up 0', 'Turning Ramp Up 1', 'Gyro', 'Steering',
                                                                'Cursor Gyro', 'Menu Keys', 'Gamepad'], variant)

    def test_the_rest_is_grouped_by_parent_base_then_gyro_then_steering_then_the_shared_menu_layers(self):
        def parent(title):
            if title.startswith('Stateful | '):
                return 'Steering and Cursor Gyro'
            return title.split(' | ')[0] if ' | ' in title else 'Base'
        for variant in VARIANTS:
            rest = [parent(title) for title in titles(layout_data(variant))[7:]]
            self.assertEqual(list(dict.fromkeys(rest)), ['Base', 'Gyro', 'Steering', 'Steering and Cursor Gyro'], variant)
            self.assertEqual(rest, sorted(rest, key=list(dict.fromkeys(rest)).index), variant)      # each group in one run

    def test_the_working_layout_has_the_builders_order(self):
        for variant in VARIANTS:
            wanted = [title for _, group in builder.ORDER for title in group]
            wanted = [map_title(title, RENAME) for title in wanted] if variant == 'alternative' else wanted
            self.assertEqual(titles(layout_data(variant)), wanted, variant)

    def test_the_preset_keys_and_blocks_follow_the_list(self):                          # R104
        for variant in VARIANTS:
            cm = layout_data(variant)['controller_mappings']
            keys = list(cm['action_layers'])
            self.assertEqual(keys, sorted(keys, key=lambda key: int(key.split('_')[1])), variant)
            self.assertEqual([preset['name'] for preset in cm['preset']], [*cm['actions'], *keys], variant)
            self.assertEqual([preset['id'] for preset in cm['preset']], [str(i) for i in range(len(cm['preset']))])



if __name__ == "__main__":
    unittest.main()
