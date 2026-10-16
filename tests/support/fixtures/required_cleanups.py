"""The required cleanups (R169 to R171): where a layer must have a cleanup function.

Tiny layouts, one rule per test, then the frozen 90.23 snapshots and the working layouts. The rules are
the author's of 2026-10-04; the record is findings/2026-10-04-required-cleanups/README.md.
"""


import json


from pathlib import Path


import subprocess


import sys


import tempfile


import unittest


from steam_layout import exceptions, required_cleanups as required


from steam_layout.cleanups import Cleanups


from steam_layout.model import Layout


from tests.support.cleanup_fixtures import guarded


from tests.support.layouts import EMPTY, SW, add, build, on, press, release, remove


ROOT = Path(__file__).resolve().parents[3]


KEY = "key_press K, , "


TOUCH, EDGE, BUTTON = required.CHECKS


CLEANUP = guarded(remove("P"))                      # a chord with LB beside a repeating removal of P


CANCEL = press(remove("P"), hold_repeats=1, interruptable=0)


LEFT, RIGHT = ("joystick", "dpad"), ("right_joystick", "joystick_mouse")


FACE, DPAD, TRIGGER = ("button_diamond", "four_buttons"), ("dpad", "dpad"), ("left_trigger", "trigger")


def layout(p=None, base=None, extra=None, touches=True):
    """Base's LB adds P and LB's Release removes it. P has a cleanup function on both stick touches.

    `p` and `base` add inputs: {(source, mode): {input: activators}}. `extra` adds whole layers."""
    def sources(start, more):
        found = {source: (mode, dict(inputs)) for (source, mode), inputs in start.items()}
        for (source, mode), inputs in (more or {}).items():
            found.setdefault(source, (mode, {}))[1].update(inputs)
        return found

    own = {("switch", SW): {"left_bumper": release(remove("P"))}}
    if touches:
        own.update({LEFT: {"touch": CLEANUP}, RIGHT: {"touch": CLEANUP}})
    layers = {"Base": sources({("switch", SW): {"left_bumper": press(add("P"))}}, base), "P": sources(own, p)}
    layers.update(extra or {})
    return build(layers)


def audit(data, config=None, only=None):
    return required.audit(Cleanups(Layout(data)), config, only)


def found(data, config=None):
    """{(check, layer, input, reason)} of the failing findings."""
    return {(f["check"], f["layer"], name, f["reason"])
            for f in audit(data, config)["findings"] for name in f["inputs"]}


def inputs(data, check, layer="P"):
    return {name for c, where, name, _ in found(data) if c == check and where == layer}


CLEANUP_T = guarded(remove("T"), chord=2)          # T's own cleanup function, guarded by RB


def counts(report):
    return tuple(report["counts"][check]["bindings"] for check in required.CHECKS)


__all__ = ['BUTTON', 'CANCEL', 'CLEANUP', 'CLEANUP_T', 'Cleanups', 'DPAD', 'EDGE', 'EMPTY', 'FACE', 'KEY', 'LEFT', 'Layout', 'Path', 'RIGHT', 'ROOT', 'SW', 'TOUCH', 'TRIGGER', 'add', 'audit', 'build', 'counts', 'exceptions', 'found', 'guarded', 'inputs', 'json', 'layout', 'on', 'press', 'release', 'remove', 'required', 'subprocess', 'sys', 'tempfile', 'unittest']
