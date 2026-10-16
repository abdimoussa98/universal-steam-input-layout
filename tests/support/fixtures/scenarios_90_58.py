"""90.58: 90.57 without the removes that never take a layer off. Nothing is added, and nothing plays differently."""


import hashlib


import importlib.util


import itertools


import json


import random


import sys


import unittest


from collections import Counter


from steam_layout.cleanups import Cleanups


from steam_layout.model import Layout, entries, map_title


from tests.scenario import RENAME, ROOT, VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario


BUILD = ROOT / 'findings/2026-10-12-removes-that-never-take-a-layer-off'


AUDIT = ROOT / 'findings/2026-10-12-remove-list-audit'


TAKEN = {'default': (4013, 1162, 2851), 'alternative': (4083, 1174, 2909)}      # 90.57, taken out, 90.58


MODES = ('Steering', 'Steering | LS: Entry Guard', 'Cursor Gyro', 'Gamepad')


HELD_PAD_LAYERS = {(host, stick, target) for host in ('RTP: Circular Scroll', 'RTP: Entry Point')
                   for stick in ('joystick', 'right_joystick') for target in ('RTP: Middle Click', 'RTP: Mouse Buttons')}


def built(variant):
    return json.loads((BUILD / f'{variant}-candidate.json').read_text(encoding='utf-8'))


def audit_script(name):
    """A script of the audit of every remove, which the proofs of this build ran on."""
    tests = str(ROOT / 'tests')
    if tests not in sys.path:
        sys.path.insert(0, tests)                                   # the scripts import `scenario` by that name
    spec = importlib.util.spec_from_file_location(f'remove_list_audit_{name}', AUDIT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def commands(value):
    return value if isinstance(value, list) else [value]


def differences(a, b, path, lists, other):
    if a == b:
        return
    if path and path[-1] == 'binding':
        lists.append((path, commands(a), commands(b)))
    elif isinstance(a, dict) and isinstance(b, dict):
        for key in a.keys() | b.keys():
            if key in a and key in b:
                differences(a[key], b[key], path + (key,), lists, other)
            else:
                other.append(path + (key,))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for index, (x, y) in enumerate(zip(a, b)):
            differences(x, y, path + (index,), lists, other)
    else:
        other.append(path)


def removes(layout):
    return [(title, source, name, kind, index, [t for op, t in layout.layer_ops(entry) if op == 'remove_layer'])
            for title in layout.presets for source, group in layout.active(title).items()
            for name, value in (group.get('inputs') or {}).items()
            for index, (kind, entry) in enumerate(entries(value.get('activators') or {}))]


__all__ = ['AUDIT', 'BUILD', 'Cleanups', 'Counter', 'HELD_PAD_LAYERS', 'Layout', 'MODES', 'RENAME', 'ROOT', 'ScenarioCase', 'TAKEN', 'VARIANTS', 'audit_script', 'built', 'commands', 'differences', 'entries', 'frozen_layout_data', 'hashlib', 'importlib', 'itertools', 'json', 'layout_data', 'map_title', 'random', 'removes', 'scenario', 'sys', 'unittest']
