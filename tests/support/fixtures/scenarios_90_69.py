"""90.69, a trial off the line: no Hold to Repeat on the cleanup presses in the Steering layers.

From 90.68, not installed (90.70 is, also from 90.68). The author, 2026-10-13: "we've never tried just making the
regular press no longer repeating. Still interruptible, but no longer repeating", scope "all in steering", and "undo
the change to add the layer the entry guard in the cleanup functions for now".

Every test here reads the 90.69 build. Whether the missing repeat keeps a press from running past its guard chord
(A69) is for the Deck: the simulator decides a guard once and never fails it, and it does not run a held-back
repeating press when its guard goes either, so it shows no difference under an input that is already held.
"""


import unittest


from steam_layout.flow_model import Inventory


from steam_layout.model import Layout


from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS, EDGE_CHORDS


from tests.support.fixtures.scenarios_90_61 import inputs, named


GUARD = 'Steering | LS: Entry Guard'


def cleanups(layout):
    return [t for t in Inventory.of(layout).transitions if t.role == 'recovery']


__all__ = ['DRIVERS', 'EDGE_CHORDS', 'GUARD', 'Inventory', 'Layout', 'ScenarioCase', 'VARIANTS', 'cleanups', 'frozen_layout_data', 'inputs', 'named', 'scenario', 'unittest']
