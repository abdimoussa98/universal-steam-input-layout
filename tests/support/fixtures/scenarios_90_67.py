"""90.67: the mode shift of 90.66 is gone; the ten left-edge cleanup presses add the Entry Guard before they remove.

From 90.66. The author, 2026-10-13: "revert the mode shift change. I still want keep the removal of the delays on
the clean up functions though. ... for the left stick clean up removals to before cleaning up i want you to add the
left stick steering guard, this is a precaution for the weird edge case where the guard would fail for repeated
removal calls."

A press that runs past its guard chord (A69) then leaves `Steering | LS: Entry Guard` on top, not `Steering` and its
exit on up and down. The simulator never runs a press past its guard and is not made to (the author: "I don't think
we need to necessarily account for that super edge case"). The scenarios state the ordinary cleanup, which carries
the same add: after a missed driver release the stick at the rim leaves the Entry Guard, and `Steering` stays.

90.70 put the add on every cleanup press of the ten layers, so the shape tests here read the 90.67 build; the
scenarios hold on the working layout too.
"""


import unittest


from steam_layout.cleanups import Cleanups


from steam_layout.model import MODE_SHIFT, Layout, actions, entries


from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS, EDGE_CHORDS


from tests.support.fixtures.scenarios_90_61 import inputs, named


from tests.support.fixtures.scenarios_90_66 import WHERE


STEERING, GUARD = 'Steering', 'Steering | LS: Entry Guard'


KEYS = {'up': 'W', 'down': 'S'}


def edge(layout, title):
    return list(entries(layout.active(title)['joystick']['inputs']['edge']['activators']))


__all__ = ['Cleanups', 'DRIVERS', 'EDGE_CHORDS', 'GUARD', 'KEYS', 'Layout', 'MODE_SHIFT', 'STEERING', 'ScenarioCase', 'VARIANTS', 'WHERE', 'actions', 'edge', 'entries', 'frozen_layout_data', 'inputs', 'named', 'scenario', 'unittest']
