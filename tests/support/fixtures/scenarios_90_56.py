"""90.56: the left edge's cleanup is the press and its guard chord again in ten Steering layers; only the Entry Guard keeps a chord with Invert Activation."""


import unittest


from steam_layout.model import EMPTY, Layout, actions, entries, map_title


from tests.scenario import RENAME, ScenarioCase, frozen_layout_data, scenario


DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30


MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'


GUARD = 'Steering | LS: Entry Guard'


DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))


SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down'))


STICK_MODIFIERS = tuple(side[2] for side in SIDES)


SCROLLS = tuple(side[4] for side in SIDES)


MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')


FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)


EDGES = (*(d[1] for d in DRIVERS), *STICK_MODIFIERS, MARKER, COVER, *SCROLLS, *MODIFIER_2)


TIMERS = (*STICK_MODIFIERS, *SCROLLS)                     # their edge also holds the timer's Soft Press (90.55)


__all__ = ['COVER', 'DEFLECT', 'DRIVERS', 'EDGES', 'EMPTY', 'FAMILY', 'GUARD', 'Layout', 'MARKER', 'MODIFIER_2', 'RENAME', 'SCROLLS', 'SIDES', 'STICK_MODIFIERS', 'ScenarioCase', 'TIMERS', 'actions', 'entries', 'frozen_layout_data', 'map_title', 'scenario', 'unittest']
