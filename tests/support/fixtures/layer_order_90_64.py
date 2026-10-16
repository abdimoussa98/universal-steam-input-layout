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


def _readable(numeric):
    import json
    from tools.convert_runtime_ids import generate_lookup, ids_to_titles
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


__all__ = ['Layout', 'RENAME', 'ROOT', 'VARIANTS', '_readable', 'builder', 'frozen_layout_data', 'importlib', 'layout_data', 'map_title', 'spec', 'titles', 'unittest']
