"""90.55: the Steering stick's four timers are Soft Presses on the left stick's edge, the left edge cleans up with one inverted chord, and the unnecessary removes are gone."""


import unittest


from steam_layout.model import Layout, actions, entries, map_title


from tests.scenario import RENAME, ScenarioCase, frozen_layout_data, layout_data, scenario


DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30


THRESHOLD = '13276'                                       # the timers' Soft Press: the stick's D-pad deadzone


MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'


DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))


SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))


STICK_MODIFIERS = tuple(side[2] for side in SIDES)


SCROLLS = tuple(side[4] for side in SIDES)


MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')


FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)


EDGE_CHORDS = (*(d[1] for d in DRIVERS), *STICK_MODIFIERS, MARKER, COVER, *SCROLLS, *MODIFIER_2)


TIMERS = tuple((side[2], side[1], MARKER, '200', '250') for side in SIDES) + tuple((side[4], side[1], COVER, '150', '200') for side in SIDES)


RIGHT_PAD = ('RTP: Entry Point', 'RTP: Tap Cover')


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


__all__ = ['COVER', 'DEFLECT', 'DRIVERS', 'EDGE_CHORDS', 'FAMILY', 'Layout', 'MARKER', 'MODIFIER_2', 'RENAME', 'RIGHT_PAD', 'SCROLLS', 'SIDES', 'STICK_MODIFIERS', 'ScenarioCase', 'THRESHOLD', 'TIMERS', 'actions', 'entries', 'frozen_layout_data', 'layout_data', 'map_title', 'scenario', 'unittest', 'wheels']
