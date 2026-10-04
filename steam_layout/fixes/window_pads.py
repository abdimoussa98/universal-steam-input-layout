"""Keep the trackpads off the layer API during the Always On Double Tap windows.

Author direction, 2026-09-30:

- **Left pad:** Base's swipe menu adds the Escape / Enter / Tab / Backspace key
  layers. Each window's left pad was a disabled source. It now swipes straight
  to those keys instead, with no layer command. The keys are read from the key
  layers Base adds, and the swipe settings are copied from Base. The pad click
  (Base: add_layer LTP: Click Entry Point; a hold_layer of LTP: Arrow Keys until
  90.13) and touch (the key layers' own touch-release cleanup, if one is ever
  below) are cleared.
- **Right pad:** it stays the mouse, so the cursor keeps moving during the
  window. The windows that disabled it now use Base's mode, with click (Base:
  add_layer RTP: Click Entry Point; a hold_layer of RTP: Mouse Buttons until
  90.13) and touch (Base: add_layer RTP: Entry Point) cleared. Settings are only `layer: "1"`, so the mouse feel inherits from Base.
  RTP Double Tap keeps its dpad-mode selection pad, clears `click`, and binds
  no touch: a second tap north or south goes to Circular Scroll, and anywhere
  else stays in mouse mode.

Idempotent; works with numeric IDs or title tokens.
"""
import copy

from ..model import TARGET, Layout, actions, always_on_layers, bindings

EMPTY = "controller_action empty_binding, , "
SWIPES = ("dpad_west", "dpad_east", "dpad_north", "dpad_south")
SWIPE_LAYER = "LTP: Entry Point"


def cleared():
    return {"activators": {"Full_Press": {"bindings": {"binding": EMPTY}}}, "disabled_activators": {}}


def swipe_keys(layout):
    """{direction: (key binding, settings)} from the left pad's swipe menu.

    The menu is Base's until 90.24. Since 90.25 Base's left pad is a D-pad that only binds the
    touch, and the swipes are in `LTP: Entry Point`, where each one also removes that layer.
    """
    base = layout.active(next(iter(layout.presets)))["left_trackpad"]
    if not all(direction in base.get("inputs", {}) for direction in SWIPES):
        base = layout.active(SWIPE_LAYER)["left_trackpad"]
    result = {}
    for direction in SWIPES:
        entry = base["inputs"][direction]["activators"]["Full_Press"]
        (added,) = [a for a in actions(entry) if a.startswith("controller_action add_layer ")]
        match = TARGET.search(added)
        key_layer = layout.resolve(match.group(2))
        keys = [b for g in layout.active(key_layer).values() for v in g.get("inputs", {}).values()
                for b in bindings(v.get("activators", {})) if b.startswith("key_press ")]
        if len(set(keys)) != 1:
            raise ValueError(f"{key_layer}: expected one key, found {keys}")
        result[direction] = (keys[0], copy.deepcopy(entry.get("settings", {})))
    return base, result


def fix(data):
    layout = Layout(data)
    base, keys = swipe_keys(layout)
    changed = []
    for title in always_on_layers(layout):
        groups = layout.active(title)
        left = groups["left_trackpad"]
        inputs = {"click": cleared(), "touch": cleared()}
        for direction, (key, settings) in keys.items():
            inputs[direction] = {"activators": {"Full_Press": {"bindings": {"binding": key}, "settings": settings}},
                                 "disabled_activators": {}}
        wanted = {"mode": base["mode"], "settings": {"layer": "1", **base.get("settings", {})}, "inputs": inputs}
        if any(left.get(k) != v for k, v in wanted.items()):
            if left["mode"] != "disabled" and left["mode"] != base["mode"]:
                raise ValueError(f"{title}: unexpected left pad mode {left['mode']}")
            left.update(copy.deepcopy(wanted))
            changed.append(f"{title} / left_trackpad")
        right = groups["right_trackpad"]
        mouse = layout.active(next(iter(layout.presets)))["right_trackpad"]["mode"]
        if right["mode"] == "disabled":
            right.update({"mode": mouse, "settings": {"layer": "1"},
                          "inputs": {"click": cleared(), "touch": cleared()}})
            changed.append(f"{title} / right_trackpad mouse")
        elif right["mode"] != mouse and "click" not in right.get("inputs", {}):
            right.setdefault("inputs", {})["click"] = cleared()
            changed.append(f"{title} / right_trackpad click")
    return {"changed": changed}
