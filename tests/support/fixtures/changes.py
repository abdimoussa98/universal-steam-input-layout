"""The change report: what differs between two layouts, by layer and input (steam_layout/changes.py)."""


import copy


import json


from pathlib import Path


import subprocess


import sys


import tempfile


import unittest


from steam_layout import changes, controllers


from tests.support.layouts import EMPTY, act, add, build, remove


ROOT = Path(__file__).resolve().parents[3]


KEY = "key_press W, , "


def base():
    return build({"Base": {"switch": ("switches", {"button_a": act(add("P")), "button_b": act(KEY)})},
                  "P": {"switch": ("switches", {"button_a": act(remove("P"))})}})


def group(data, title, source="switch"):
    cm = data["controller_mappings"]
    names = {v["title"]: k for section in ("actions", "action_layers") for k, v in cm[section].items()}
    preset = next(p for p in cm["preset"] if p["name"] == names[title])
    gid = next(g for g, state in preset["group_source_bindings"].items() if state.startswith(source + " "))
    return next(g for g in cm["group"] if g["id"] == gid)


__all__ = ['EMPTY', 'KEY', 'Path', 'ROOT', 'act', 'add', 'base', 'build', 'changes', 'controllers', 'copy', 'group', 'json', 'remove', 'subprocess', 'sys', 'tempfile', 'unittest']
