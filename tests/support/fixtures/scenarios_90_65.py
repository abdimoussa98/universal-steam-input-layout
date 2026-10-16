"""90.65: the left edge of ten Steering layers cleans up with the press and its guard chord again, 5 ms late.

From 90.64. The author, 2026-10-13: "change the steering left stick clean up back to the non inverted chord with
interruptible regular press removals pattern we'd had before. Make the left in those steering layers also no
longer have the edge inverted ... the regular press removal to also have a start delay of 5ms".

On each of the ten edges: a repeating, interruptible Regular Press of removes with a start delay of 5 ms and,
beside it, an empty chord on the drivers that is not interruptible (the shape of 90.56 to 90.58, R133). The
ring is a normal ring again, so the press runs with the stick at the rim and no driver held.

The simulator never misses a held driver, so nothing here shows the Deck fault of 90.58 fixed
(findings/2026-10-12-steering-ends-on-a-stick-touch).

90.66 took the 5 ms off again (tests/scenarios/neptune/test_scenarios_90_66.py): the shape tests and the two scenarios that state
the delay (P2, P3) run on the 90.65 build.
"""


import unittest


from steam_layout.model import EMPTY, Layout, actions, entries


from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS, EDGE_CHORDS, FAMILY, SIDES, TIMERS


from tests.support.fixtures.scenarios_90_61 import GUARD, inputs, named


DELAY = '5'


def edge(layout, title):
    return list(entries(layout.active(title)['joystick']['inputs']['edge']['activators']))


__all__ = ['DELAY', 'DRIVERS', 'EDGE_CHORDS', 'EMPTY', 'FAMILY', 'GUARD', 'Layout', 'SIDES', 'ScenarioCase', 'TIMERS', 'VARIANTS', 'actions', 'edge', 'entries', 'frozen_layout_data', 'inputs', 'named', 'scenario', 'unittest']
