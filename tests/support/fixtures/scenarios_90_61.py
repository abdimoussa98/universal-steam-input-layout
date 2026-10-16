"""90.61: on the left stick's edge of ten Steering layers the cleanup is one chord with Invert Activation again.

From 90.58, one change: the repeating Regular Press and its guard chord become one repeating chord on the same
drivers with Invert Activation, carrying the press's list. For an open Deck fault
(findings/2026-10-12-steering-ends-on-a-stick-touch): the driver layer's press ran although its bumper was held.
The simulator does not reproduce the fault, so nothing here shows it fixed.
"""


import unittest


from steam_layout.model import Layout, actions, entries, map_title


from tests.support.sources import load_json


from tests.scenario import RENAME, ROOT, VARIANTS, ScenarioCase, frozen_layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS, EDGE_CHORDS, FAMILY, SIDES, TIMERS


BUILD = ROOT / 'findings/2026-10-12-inverted-chord-on-the-steering-left-edge'


GUARD = 'Steering | LS: Entry Guard'


DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30


REMOVES = {'default': 2851, 'alternative': 2909}          # 90.58's, unchanged


def built(variant):
    return load_json(BUILD / f'{variant}-candidate.json')


def named(variant):
    return (lambda title: map_title(title, RENAME)) if variant == 'alternative' else (lambda title: title)


def inputs(layout):
    """{(layer, source, input): [(kind, settings, actions)]} of every live input."""
    return {(title, source, control): [(kind, entry.get('settings') or {}, layout.layer_ops(entry) or actions(entry))
                                       for kind, entry in entries(value.get('activators') or {})]
            for title in layout.presets for source, group in layout.active(title).items()
            for control, value in (group.get('inputs') or {}).items()}


__all__ = ['BUILD', 'DEFLECT', 'DRIVERS', 'EDGE_CHORDS', 'FAMILY', 'GUARD', 'Layout', 'REMOVES', 'RENAME', 'ROOT', 'SIDES', 'ScenarioCase', 'TIMERS', 'VARIANTS', 'actions', 'built', 'entries', 'frozen_layout_data', 'inputs', 'load_json', 'map_title', 'named', 'scenario', 'unittest']
