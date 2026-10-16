"""90.68: in the Entry Guard each driver's chord adds the driver's layer first, then removes the guard.

From 90.67. The author, 2026-10-13: "in the steering left stick guard change the execution order so that the first
thing that happens is we add either the W layer on the right bumper slash right trigger depending on the layout then
we remove the guard and then the same for the opposite side."

Between the two commands the stack is `Steering`, the guard and the driver's layer; on 90.67 it was `Steering` alone,
with its exit on up and down. The simulator runs a bind's commands with nothing in between, so it cannot tell the two
orders apart: the scenario states only that the hand-over still ends the same.
"""


import unittest


from steam_layout.model import Layout, actions, entries


from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS


from tests.support.fixtures.scenarios_90_61 import inputs, named


from tests.support.fixtures.scenarios_90_66 import WHERE


GUARD = 'Steering | LS: Entry Guard'


__all__ = ['DRIVERS', 'GUARD', 'Layout', 'ScenarioCase', 'VARIANTS', 'WHERE', 'actions', 'entries', 'frozen_layout_data', 'inputs', 'layout_data', 'named', 'scenario', 'unittest']
