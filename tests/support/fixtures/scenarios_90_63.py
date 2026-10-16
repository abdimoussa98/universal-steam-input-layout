"""90.63: the ring is inverted on the left edge of ten Steering layers.

From 90.62, one setting in ten groups: Outer Ring Binding Invert on the left stick. The chord with Invert
Activation that has been the edge's cleanup function since 90.61 then runs with the stick at the rim and no
driver held, where it ran off the rim. The author, 2026-10-12: "We need to invert the left stick edge for the
chorded inverted clean functions ... every where in steering except in entry steering guard."

The Soft Press timers on four of those edges don't follow the ring's setting (author, A67).
"""


import unittest


from steam_layout.model import Layout, entries


from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS, EDGE_CHORDS, FAMILY, SIDES, TIMERS


from tests.support.fixtures.scenarios_90_61 import GUARD, inputs, named


__all__ = ['DRIVERS', 'EDGE_CHORDS', 'FAMILY', 'GUARD', 'Layout', 'SIDES', 'ScenarioCase', 'TIMERS', 'VARIANTS', 'entries', 'frozen_layout_data', 'inputs', 'named', 'scenario', 'unittest']
