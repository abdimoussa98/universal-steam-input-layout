"""Inheritance/blocking audit (Layer Definition of Done, section 8)."""


import json


from pathlib import Path


import subprocess


import sys


import tempfile


import time


import unittest


from tools.audit_inheritance import Layout, always_on_layers, audit, entries, map_title


from tests.support.layouts import (EMPTY, act, add, build, bystander_window, deep_window,
                                  remove, stored_release as release)


from tests.support.observations import window_observation


ROOT = Path(__file__).resolve().parents[3]


def config(stacks, decisions=()):
    return {"variants": {"alternative": {"L1": "L2", "R1": "R2"}},
            "targets": {"Win": {"stacks": [{"layers": s, "why": "test"} for s in stacks],
                                "decisions": list(decisions)}}}


def routes(report, status=None):
    rows = report["targets"]["Win"]["routes"]
    return {(r["source"], r["input"]) for r in rows if status is None or r["status"] == status}


AOA = {"always_on_action": act(remove("Win"))}


__all__ = ['AOA', 'EMPTY', 'Layout', 'Path', 'ROOT', 'act', 'add', 'always_on_layers', 'audit', 'build', 'bystander_window', 'config', 'deep_window', 'entries', 'json', 'map_title', 'release', 'remove', 'routes', 'subprocess', 'sys', 'tempfile', 'time', 'unittest', 'window_observation']
