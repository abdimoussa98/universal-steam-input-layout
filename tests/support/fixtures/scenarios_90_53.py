"""90.53: the Steering stick's timers sit on the drivers, its entry carries no cleanup, and the left edge cleans up with one inverted chord."""


import unittest


from steam_layout.model import Layout, actions, entries, map_title


from tests.scenario import RENAME, ScenarioCase, frozen_layout_data, scenario


DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30


MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'


GUARD = 'Steering | LS: Entry Guard'


DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))


SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))


STICK_MODIFIERS = tuple(side[2] for side in SIDES)


MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')


FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)


EDGE_CHORDS = (*(d[1] for d in DRIVERS), *STICK_MODIFIERS, MARKER, COVER, *(side[4] for side in SIDES), *MODIFIER_2)


RIGHT_PAD = ('RTP: Entry Point', 'RTP: Tap Cover')


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


__all__ = ['COVER', 'DEFLECT', 'DRIVERS', 'EDGE_CHORDS', 'FAMILY', 'GUARD', 'Layout', 'MARKER', 'MODIFIER_2', 'RENAME', 'RIGHT_PAD', 'SIDES', 'STICK_MODIFIERS', 'ScenarioCase', 'actions', 'entries', 'frozen_layout_data', 'map_title', 'scenario', 'unittest', 'wheels']
