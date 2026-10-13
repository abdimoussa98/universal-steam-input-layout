"""90.64: the layer list in a new order. From 90.63, with no bind, setting or group changed.

The author, 2026-10-12: "keep the initial order ramp up 0, ramp up 1. then the stateful base layers: gyro,
steering, cursor gyro, menu, gamepad. then the other layer still separate by the parent statful layers, so all
the base then gyro, so on so forth. Within that group ... determine the order yourself".
"""

import importlib.util
import unittest

from steam_layout.model import Layout, map_title
from tests.scenario import RENAME, ROOT, VARIANTS, frozen_layout_data, layout_data

spec = importlib.util.spec_from_file_location('layer_order_90_64', ROOT / 'findings/2026-10-12-layer-order/build_candidate.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def titles(data):
    return [value['title'] for value in data['controller_mappings']['action_layers'].values()]


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

    def test_every_layer_is_bind_for_bind_what_it_was_on_90_63(self):
        for variant in VARIANTS:
            old, new = (builder.layers_by_title(_readable(frozen_layout_data(variant, version))) for version in ('90.63', '90.64'))
            self.assertEqual(old, new, variant)


def _readable(numeric):
    import json
    from tools.convert_runtime_ids import generate_lookup, ids_to_titles
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


if __name__ == '__main__':
    unittest.main()
