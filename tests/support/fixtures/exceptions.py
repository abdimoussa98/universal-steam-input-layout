"""The exceptions register: every accepted finding in one list (steam_layout/exceptions.py)."""


import copy


import json


from pathlib import Path


import unittest


from steam_layout import exceptions, rules


ROOT = Path(__file__).resolve().parents[3]


def entry(rule="R139", scope=None, **changes):
    row = {"rule": rule, "scope": scope or {"layers": ["P"], "inputs": ["switch/button_a"]}, "status": "allow",
           "why": "by design", "decided": "Author, 2026-10-02", "todo": None}
    row.update(changes)
    return row


def layout(controller, titles, variant="default"):
    """A layout header and layer list: what the controller view reads."""
    cm = {"title": f"single-set-{variant} :: always-gyro :: 1.0", "controller_type": controller,
          "actions": {"Preset_1000001": {"title": "Base"}},
          "action_layers": {f"Preset_{1000002 + i}": {"title": t} for i, t in enumerate(titles)}}
    return {"controller_mappings": cm}


__all__ = ['Path', 'ROOT', 'copy', 'entry', 'exceptions', 'json', 'layout', 'rules', 'unittest']
