"""Scenarios for 90.72: stick-edge cleanups on the pad layers, and pad-click stand-ins for what they hide.

The record is findings/2026-10-14-pad-stick-edge-cleanups/README.md; the plan is
plans/2026-10-14-pad-stick-edge-cleanups.md.

- The pad click layers have a cleanup function on both stick edges, the four left-pad key layers on the left edge only:
  a copy of their stick-touch cleanup, guarded by the pad's touch (legacy chord IDs 16 and 17). With stick touch the
  touch cleanup clears a stuck pad layer first; the edges are for a controller without it (author, 2026-10-14).
- While a pad layer is on and its thumb is on the pad, the guard hides the stick edges below. A layer whose edge bind
  would be lost does it on the pad's click instead: the Steering stick layers add their cover, and the cover carries the
  click on into the Click Entry Point; the ramp layers remove themselves and add the left pad's Click Entry Point.
- The menu Entry Points and the two menu chord layers block both pad clicks; the left swipes type their keys (R172).
"""


import json


import unittest


from steam_layout.model import Layout, map_title


from tests.scenario import BACK, ROOT, VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario


CLICK_LAYERS = ("LTP: Click Entry Point", "LTP: Arrow Keys", "LTP: Middle Click",
                "RTP: Click Entry Point", "RTP: Mouse Buttons", "RTP: Middle Click")


KEY_LAYERS = ("Escape", "Tab", "Backspace", "Enter")


RAMPS = ("Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1")


MENU = ("Menu Left: Entry Point", "Menu Right: Entry Point", "Stateful | Menu Left: Entry Point",
        "Stateful | Menu Right: Entry Point", "Menu Left!Right: Enter", "Menu Right!Left: Backspace")


STAND_INS = ("Steering | LS Up: Modifier 1", "Steering | LS Down: Modifier 0", "Steering | LS Up: Scroll Up",
             "Steering | LS Down: Scroll Down", "Steering | LS: Tap Cover", "Steering | LS: Double Tap Cover")


RP = "right_trackpad"


def ramps(pad):
    return [t for t in RAMPS if pad.has(t)]


def pad_layers(pad):
    return [t for t in pad.names() if t in CLICK_LAYERS + KEY_LAYERS]


__all__ = ['BACK', 'CLICK_LAYERS', 'KEY_LAYERS', 'Layout', 'MENU', 'RAMPS', 'ROOT', 'RP', 'STAND_INS', 'ScenarioCase', 'VARIANTS', 'frozen_layout_data', 'json', 'layout_data', 'map_title', 'pad_layers', 'ramps', 'scenario', 'unittest']
