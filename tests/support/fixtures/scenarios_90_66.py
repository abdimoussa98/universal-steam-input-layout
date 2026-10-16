"""90.66: in `Steering` each driver mode-shifts the left stick to a group whose up and down are empty.

From 90.65. Confirmed by the author on the Deck, 2026-10-13 (A69): a burst of `remove_layer` calls makes a chord
evaluate again and an evaluation can fail, so the interruptible press beside a guard chord runs. In `Steering`
that took the driver's layer off with the driver held, and `Steering`'s exit on up or down then ended `Steering`.

The author: "in steering base if you are pressing bumper/triggers the up and down on left stick will be empty
binds, this protects from that edge case kicking us out of the steering stateful set accidently. I also want you
to remove the 5sec delay". The 5 ms start delay of 90.65 is gone from the ten left-edge cleanup presses.

The simulator never fails a guard, so the scenarios take the driver's layer off by hand (`drop`). What a mode shift
bound in a layer does on the Deck is A70, unverified: the simulator has it on while its layer answers the held
driver, in place of that layer's own stick group only.

90.67 took the mode shift out again (author, 2026-10-13: "revert the mode shift change"), so everything here reads
the 90.66 build.
"""


import unittest


from steam_layout.model import EMPTY, MODE_SHIFT, Layout, actions, entries


from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, scenario


from tests.support.fixtures.scenarios_90_55 import DRIVERS, EDGE_CHORDS


from tests.support.fixtures.scenarios_90_61 import inputs, named


STEERING = 'Steering'


WHERE = {'default': (('switch', 'right_bumper'), ('switch', 'left_bumper')),
         'alternative': (('right_trigger', 'edge'), ('left_trigger', 'edge'))}


EXIT = {'up': 'dpad_north', 'down': 'dpad_south'}


def shift_groups(layout):
    return {gid: state for gid, state in layout.presets[STEERING]['group_source_bindings'].items() if 'modeshift' in state}


__all__ = ['DRIVERS', 'EDGE_CHORDS', 'EMPTY', 'EXIT', 'Layout', 'MODE_SHIFT', 'STEERING', 'ScenarioCase', 'VARIANTS', 'WHERE', 'actions', 'entries', 'frozen_layout_data', 'inputs', 'named', 'scenario', 'shift_groups', 'unittest']
