"""90.47: inherited stick touches must not expose Steering clears in windows."""


import copy


import json


import unittest


from steam_layout import exceptions


from steam_layout.fixes.window_routes import fix as fix_windows


from steam_layout.inheritance import audit, declared_stacks


from steam_layout.model import Layout


from tests.scenario import ROOT, VARIANTS, frozen_layout_data, layout_data


from tests.support.layouts import EMPTY, act, add, build


WINDOWS = ('LST: Double Tap', 'RST: Double Tap')


DIRECTIONS = {'dpad_north': 'W', 'dpad_south': 'S'}


CONTEXTS = {('Base', 'Steering'), ('Base', 'Gyro', 'Steering')}


PREVIOUS = ROOT / 'findings/2026-10-10-ramp-menu-and-driver-chords'


def config():
    return exceptions.window(json.loads((ROOT / 'steam_layout/traced_stacks.json').read_text()),
                             exceptions.load())


__all__ = ['CONTEXTS', 'DIRECTIONS', 'EMPTY', 'Layout', 'PREVIOUS', 'ROOT', 'VARIANTS', 'WINDOWS', 'act', 'add', 'audit', 'build', 'config', 'copy', 'declared_stacks', 'exceptions', 'fix_windows', 'frozen_layout_data', 'json', 'layout_data', 'unittest']
