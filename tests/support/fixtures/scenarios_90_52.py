"""90.52: the Steering stick deflect follows the bumper modifier lifecycle, with a scroll layer for the second deflect."""


import unittest


from steam_layout.model import Layout, entries


from tests.scenario import ScenarioCase, layout_data, scenario


DEFLECT = '1073741824'                                    # the left stick's deflect, bit 30


MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'


SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))


FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


__all__ = ['COVER', 'DEFLECT', 'FAMILY', 'Layout', 'MARKER', 'SIDES', 'ScenarioCase', 'entries', 'layout_data', 'scenario', 'unittest', 'wheels']
