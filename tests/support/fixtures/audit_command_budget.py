import copy


import json


from pathlib import Path


import subprocess


import sys


import tempfile


import unittest


from tools.audit_command_budget import audit_layout, unique_object


def command(actions="controller_action empty_binding, , "):
    return {"bindings": {"binding": actions}}


def layout(activators, disabled=None):
    return {"controller_mappings": {
        "actions": {"Preset_1": {"title": "Base"}}, "action_layers": {},
        "preset": [{"name": "Preset_1", "group_source_bindings": {"1": "right_joystick active"}}],
        "group": [{"id": "1", "inputs": {"edge": {
            "activators": activators, "disabled_activators": disabled or {}}}}]}}


__all__ = ['Path', 'audit_layout', 'command', 'copy', 'json', 'layout', 'subprocess', 'sys', 'tempfile', 'unique_object', 'unittest']
