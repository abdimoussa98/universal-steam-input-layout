"""The transition inventory, what a layer inherits per lower stack, and the Flow audit.

The Flow audit (audit_flow_inheritance.py) runs on backward chains (steam_layout/chains.py,
covers.py). The family walk it first ran on is deprecated; its tests are in
archived/depth-search-and-family-walk/.
"""


import json


import os


from pathlib import Path


import subprocess


import sys


import tempfile


import unittest


from steam_layout.flow_inheritance import inspect_target, nearest


from steam_layout.flow_model import Inventory


from steam_layout.model import Layout


from tests.support.flow_fixtures import EMPTY, add, cover_layout, entry, fixture, inp, rem, switches


ROOT = Path(__file__).resolve().parents[3]


L, R = ("switch", "left_bumper"), ("switch", "right_bumper")


__all__ = ['EMPTY', 'Inventory', 'L', 'Layout', 'Path', 'R', 'ROOT', 'add', 'cover_layout', 'entry', 'fixture', 'inp', 'inspect_target', 'json', 'nearest', 'os', 'rem', 'subprocess', 'switches', 'sys', 'tempfile', 'unittest']
