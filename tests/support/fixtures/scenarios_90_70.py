"""90.70: every cleanup function in the Steering layers adds the Entry Guard before it removes.

From 90.68. The author, 2026-10-13: "for 90.70 keep the changes from 90.68 and have all the steering cleanups add the
entry steering guard." 90.67 had the add on the left stick's edge of ten Steering layers; a cleanup press can run past
its guard chord on any input (A69), so the other 80 cleanup presses of those layers carry it too.

The simulator never runs a press past its guard and is not made to (the author, on 90.67). The scenarios state the
ordinary cleanup, which carries the same add.
"""


import unittest


from steam_layout.flow_model import Inventory


from steam_layout.model import Layout, actions, entries


from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS, EDGE_CHORDS


from tests.support.fixtures.scenarios_90_61 import inputs, named


GUARD = 'Steering | LS: Entry Guard'


KEYS = {'up': 'W', 'down': 'S'}


def cleanups(layout):
    return [t for t in Inventory.of(layout).transitions if t.role == 'recovery']


__all__ = ['DRIVERS', 'EDGE_CHORDS', 'GUARD', 'Inventory', 'KEYS', 'Layout', 'ScenarioCase', 'VARIANTS', 'actions', 'cleanups', 'entries', 'frozen_layout_data', 'inputs', 'layout_data', 'named', 'scenario', 'unittest']
