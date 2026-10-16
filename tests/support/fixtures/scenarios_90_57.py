"""90.57: in `Steering` the first driver's Release hands over, the second driver's Release removes only the Modifier 2 layer, and 264 removes are gone."""


import itertools


import json


import unittest


from steam_layout.model import Layout, entries, map_title


from tests.scenario import RENAME, ROOT, ScenarioCase, frozen_layout_data, layout_data, scenario


BUILD = ROOT / 'findings/2026-10-12-driver-handover-and-fewer-removes'


STEERING, GUARD = 'Steering', 'Steering | LS: Entry Guard'


W, S = 'Steering | R1: W Key', 'Steering | L1: S Key'


ORDERS = (('R1', W, 'W', 'L1', S, 'S', 'Steering | R1!L1: Modifier 2'),
          ('L1', S, 'S', 'R1', W, 'W', 'Steering | L1!R1: Modifier 2'))


MODIFIER_2 = tuple(order[6] for order in ORDERS)


COVERS = ('L1: Tap Cover', 'R1: Tap Cover', 'L1&R1: Tap Cover')


WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')


STICK = ('Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0', 'Steering | LS: Tap Cover',
         'Steering | LS: Double Tap Cover', 'Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down')


GYRO_MODIFIER_2 = ('Gyro | L1!R1: Modifier 2', 'Gyro | R1!L1: Modifier 2')


INPUT = {'default': {'R1': ('switch', 'right_bumper'), 'L1': ('switch', 'left_bumper')},
         'alternative': {'R1': ('right_trigger', 'edge'), 'L1': ('left_trigger', 'edge')}}


def home(gyro):
    return ('Base', 'Gyro') if gyro else ('Base',)


__all__ = ['BUILD', 'COVERS', 'GUARD', 'GYRO_MODIFIER_2', 'INPUT', 'Layout', 'MODIFIER_2', 'ORDERS', 'RENAME', 'ROOT', 'S', 'STEERING', 'STICK', 'ScenarioCase', 'W', 'WINDOWS', 'entries', 'frozen_layout_data', 'home', 'itertools', 'json', 'layout_data', 'map_title', 'scenario', 'unittest']
