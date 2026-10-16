"""90.54: 90.52 with one change, the stick modifiers' 200 ms hold timer on the left stick's edge."""


import unittest


from steam_layout.model import EMPTY, Layout, actions, entries


from tests.scenario import ScenarioCase, frozen_layout_data, scenario


DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30


MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'


DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))


SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))


FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


__all__ = ['COVER', 'DEFLECT', 'DRIVERS', 'EMPTY', 'FAMILY', 'Layout', 'MARKER', 'SIDES', 'ScenarioCase', 'actions', 'entries', 'frozen_layout_data', 'scenario', 'unittest', 'wheels']
