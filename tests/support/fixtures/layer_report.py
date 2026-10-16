"""The per-layer report: the three questions and the cleanup lists (plan step 6).

Plan: plans/2026-10-01-backward-chain-audit.md.
"""


import json


from pathlib import Path


import re


import subprocess


import sys


import tempfile


import unittest


from steam_layout.layer_report import report


from steam_layout.model import Layout


from tests.support.layouts import SW, add, build, press, release, remove


ROOT = Path(__file__).resolve().parents[3]


KEY_K, KEY_X = "key_press K, , ", "key_press X, , "


def family(cover=None, exit_ops=None):
    """Base adds P; P's button_b adds a cover C on top; releasing button_a is P's exit. Ghost is never added."""
    return build({"Base": {"switch": (SW, {"button_a": press(add("P")), "button_k": press(KEY_K)})},
                  "P": {"switch": (SW, {"button_b": press(add("C")),
                                        "button_a": release(*(exit_ops or (remove("P"), remove("C"), remove("Ghost"))))})},
                  "C": {"switch": (SW, cover or {"button_x": press(KEY_X)})}, "Ghost": {}})


def rows(result, key):
    return {(row["source"], row["input"]): row for row in result[key]}


__all__ = ['KEY_K', 'KEY_X', 'Layout', 'Path', 'ROOT', 'SW', 'add', 'build', 'family', 'json', 'press', 're', 'release', 'remove', 'report', 'rows', 'subprocess', 'sys', 'tempfile', 'unittest']
