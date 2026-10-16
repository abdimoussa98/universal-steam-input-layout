"""Scenarios for 90.74: the right stick in the four Fn layers.

The record is findings/2026-10-15-fn-right-stick/README.md; the plan is
plans/2026-10-14-key-layer-click-and-fn-right-stick.md, part 2.

- On the Deck the right stick in the Fn layer gave no bump and not its keys, while the left stick worked (author,
  2026-10-14 and 2026-10-15). The two groups had the same shape; only the right one stated `deadzone` 13276 and
  `requires_click` 0. Since 90.74 the right stick's group has the left stick's settings, and keeps its own keys
  (`;` up, `'` down, `.` right, `,` left, the author's), its R3 guard and its cleanups, each key with a Low bump.
"""


import unittest


from steam_layout.model import Layout


from tests.scenario import VARIANTS, ScenarioCase, layout_data, scenario


FN_LAYERS = ("Menu Left: Fn Layer", "Menu Right: Fn Layer", "Stateful | Menu Left: Fn Layer",
             "Stateful | Menu Right: Fn Layer")


KEYS = {"up": "SEMICOLON", "down": "SINGLE_QUOTE", "right": "PERIOD", "left": "COMMA"}


PARTS = {"up": "dpad_north", "down": "dpad_south", "right": "dpad_east", "left": "dpad_west"}


MENU = {"Menu Left": "Select", "Menu Right": "Start"}


__all__ = ['FN_LAYERS', 'KEYS', 'Layout', 'MENU', 'PARTS', 'ScenarioCase', 'VARIANTS', 'layout_data', 'scenario', 'unittest']
