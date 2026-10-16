"""90.51: the ring pads bump by their own binds; the stick modifiers have no cleanup on their own direction."""


import unittest


from steam_layout.model import Layout, entries


from tests.scenario import ScenarioCase, frozen_layout_data, layout_data, scenario


MODIFIERS = (('Steering | LS Up: Modifier 1', 'up', 'dpad_north'), ('Steering | LS Down: Modifier 0', 'down', 'dpad_south'))


__all__ = ['Layout', 'MODIFIERS', 'ScenarioCase', 'entries', 'frozen_layout_data', 'layout_data', 'scenario', 'unittest']
