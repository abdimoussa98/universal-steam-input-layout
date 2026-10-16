"""Scenarios for 90.71: the pad click layers on touch, the bump on the final layer's click.

The record is findings/2026-10-14-pad-click-touch-layers/README.md; the plan is
plans/2026-10-14-pad-click-touch-layers.md.

- `Base` (both pads) and `RTP: Circular Scroll` add the Click Entry Point with a repeating Soft Press, silent.
- The D-pad layers have Requires Click off. Each direction and the centre has a Release that removes the layer.
- The final layers' click is a `hold_layer` on themselves, High; the inverted repeating removal is gone.
- The Middle Click layers send their output on a Soft Press of its own, silent.
- The D-pad layout is Radial Without Overlap (`layout` 0): one direction at a time, so a slide on the ring lets the
  old direction go before the new one comes.

The final layer always lands on a click that is held, so its `hold_layer` and its bump don't run (A5): on the
simulator the click's release leaves the layer on until the thumb moves or lifts, and no gesture bumps. The Deck
says whether Steam does the same.
"""


import json


import unittest


from steam_layout.model import Layout, actions, entries, map_title


from tests.scenario import BACK, SOURCES, VARIANTS, ScenarioCase, frozen_layout_data, scenario


PADS = {"LP": ("LTP: Click Entry Point", "LTP: Arrow Keys", "LTP: Middle Click", "LEFT_ARROW", "UP_ARROW", "CAPSLOCK"),
        "RP": ("RTP: Click Entry Point", "RTP: Mouse Buttons", "RTP: Middle Click", "mouse_button BACK",
               "mouse_wheel SCROLL_UP", "mouse_button MIDDLE")}


PAD_LAYERS = {title for values in PADS.values() for title in values[:3]}


def ring_slide(pad, name, old, new):
    """Move a clicked thumb along the ring: the old direction lets go, then the new one presses (layout 0)."""
    source = SOURCES[name]
    pad.sim.release((source, old))
    pad.sim.press((source, new))
    return pad


def let_go_click(pad, name):
    pad.sim.release((SOURCES[name], "click"))
    return pad


def bumps(pad):
    return [detail for _, detail in pad.seen("haptic")]


def on_pad(pad):
    return {t for t in pad.names() if t in PAD_LAYERS}


__all__ = ['BACK', 'Layout', 'PADS', 'PAD_LAYERS', 'SOURCES', 'ScenarioCase', 'VARIANTS', 'actions', 'bumps', 'entries', 'frozen_layout_data', 'json', 'let_go_click', 'map_title', 'on_pad', 'ring_slide', 'scenario', 'unittest']
