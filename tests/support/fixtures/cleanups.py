"""The Cleanup audit: what a cleanup function and a release may remove.

Tiny layouts, one rule per test, then the frozen 90.10 snapshots. The rules are in
findings/2026-10-02-cleanup-boundaries/README.md; the plan is plans/2026-10-02-cleanup-audit.md.
"""


import copy


import importlib.util


import json


from pathlib import Path


import subprocess


import sys


import tempfile


import unittest


from steam_layout.chains import Chains


from steam_layout.cleanups import Cleanups, audit, kept, release_of


from steam_layout.fixes import cleanup_lists


from steam_layout.model import Layout, entries


from tests.support.cleanup_fixtures import guarded, owner


from tests.support.layouts import EMPTY, SW, add, build, on, press, release, remove


from tests.support.observations import finding_pairs


ROOT = Path(__file__).resolve().parents[3]


KEY = "key_press K, , "


HOLD = "controller_action hold_layer {{Base::%s}} 0 0, , "


def found(data, check=None, config=None):
    """{(check, layer, removed or hiding layer)} of the failing findings."""
    return finding_pairs(audit(data, config or {}), check)


def mask_chord(mask):
    return on("chord", EMPTY, gyro_ratchet_button_mask=mask, gyro_ratchet_button_requireany_or_all=0)


def removes(data, layer, source, inp, kind="Full_Press"):
    """The layers a binding removes, in execution order."""
    layout = Layout(data)
    activators = layout.active(layer)[source]["inputs"][inp]["activators"]
    return [t for k, e in entries(activators) if k == kind for op, t in layout.layer_ops(e) if op == "remove_layer"]


__all__ = ['Chains', 'Cleanups', 'EMPTY', 'HOLD', 'KEY', 'Layout', 'Path', 'ROOT', 'SW', 'add', 'audit', 'build', 'cleanup_lists', 'copy', 'entries', 'finding_pairs', 'found', 'guarded', 'importlib', 'json', 'kept', 'mask_chord', 'on', 'owner', 'press', 'release', 'release_of', 'remove', 'removes', 'subprocess', 'sys', 'tempfile', 'unittest']
