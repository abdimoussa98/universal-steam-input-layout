"""90.62: rocking in Steering the way the bumper modifiers do it.

From 90.61. With one driver held, pressing the other adds the other driver's layer and then Modifier 2 on top of
it. A Release inside Modifier 2 only removes: the layer of the driver still held is underneath already. Until
90.61 the first driver's Release added it (the hand-over of 90.57), and on the Deck W to S worked and S back to W
did not (author, 2026-10-12). The simulator played both directions before and plays them now.
"""


import unittest


from steam_layout.model import Layout, entries, map_title


from tests.support.sources import load_json


from tests.scenario import RENAME, ROOT, VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario


from tests.support.fixtures.scenarios_90_57 import INPUT, MODIFIER_2, ORDERS, S, STEERING, W


from tests.support.fixtures.scenarios_90_61 import inputs


BUILD = ROOT / 'findings/2026-10-12-steering-rocking-like-the-bumper-modifiers'


REMOVES = {'default': (2851, 2885), 'alternative': (2909, 2943)}            # 90.61, 90.62


def built(variant):
    return load_json(BUILD / f'{variant}-candidate.json')


def named(variant):
    return (lambda title: map_title(title, RENAME)) if variant == 'alternative' else (lambda title: title)


def ops_of(layout, title, control, kind):
    source, name = control
    return layout.layer_ops(dict(entries(layout.active(title)[source]['inputs'][name]['activators']))[kind])


__all__ = ['BUILD', 'INPUT', 'Layout', 'MODIFIER_2', 'ORDERS', 'REMOVES', 'RENAME', 'ROOT', 'S', 'STEERING', 'ScenarioCase', 'VARIANTS', 'W', 'built', 'entries', 'frozen_layout_data', 'inputs', 'layout_data', 'load_json', 'map_title', 'named', 'ops_of', 'scenario', 'unittest']
