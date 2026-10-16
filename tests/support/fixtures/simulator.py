"""The press simulator (steam_layout/simulator.py), on tiny made-up layouts.

One behaviour per test, each named with the Steam assumption it models
(resources/Steam Behaviour Assumptions.md).
"""


import unittest


from steam_layout.model import Layout


from steam_layout.simulator import Simulator, desktop


from tests.support.layouts import EMPTY, SW, add, build, on, press, release, remove


LB, RB = ("switch", "left_bumper"), ("switch", "right_bumper")


A, B, X = ("switch", "button_a"), ("switch", "button_b"), ("switch", "button_x")


EDGE = ("joystick", "edge")


def key(name, kind="Full_Press", **settings):
    return on(kind, f"key_press {name}, , ", **settings)


def sim(layers, **options):
    return Simulator(Layout(build(layers)), **options)


def hold():
    """Base's LB adds P; P ends on the LB Release."""
    return {"Base": {"switch": (SW, {"left_bumper": press(add("P")), "button_a": key("Q")})},
            "P": {"switch": (SW, {"left_bumper": release(remove("P")), "button_a": key("F")})}}


__all__ = ['A', 'B', 'EDGE', 'EMPTY', 'LB', 'Layout', 'RB', 'SW', 'Simulator', 'X', 'add', 'build', 'desktop', 'hold', 'key', 'on', 'press', 'release', 'remove', 'sim', 'unittest']
