"""Shared expectations for current Neptune contracts, both variants.

These describe saved settings and command order, not device scheduling. Source
bundles are prepared once per exact file content and returned as private copies.
"""
from tests.support.sources import ROOT, neptune_bundle

EMPTY = "controller_action empty_binding, , "


def removal(title):
    return "controller_action remove_layer {{Base::" + title + "}} 0 0, , "


def addition(title):
    return "controller_action add_layer {{Base::" + title + "}} 0 0, , "


def load_layouts():
    return {variant: neptune_bundle(ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json")
            for variant in ("default", "alternative")}


CURSOR_PROFILE = {
    "gyro_precision_speed": "750",
    "haptic_intensity": "0",
    "flickstick_haptic_bump_per_angle": "1",
    "mouse_move_threshold": "5",
}


def owners(variant):
    buttons = ("L1", "R1") if variant == "default" else ("L2", "R2")
    selectors = ("1", "2") if variant == "default" else ("7", "8")
    for index, (button, selector) in enumerate(zip(buttons, selectors)):
        title = f"{button}: Modifier {index}"
        source, name = primary_input(variant, index)
        yield button, selector, title, source, name


def primary_input(variant, side):
    direction = ("left", "right")[side]
    return ("switch", direction + "_bumper") if variant == "default" else (direction + "_trigger", "edge")


def recovery_specs(variant):
    left, right, lc, rc = ("L1", "R1", "1", "2") if variant == "default" else ("L2", "R2", "7", "8")
    singles = [left + ": Modifier 0", right + ": Modifier 1"]
    covers = {left + ": Tap Cover", right + ": Tap Cover", left + "&" + right + ": Tap Cover"}
    # Cleanup rules (author, 2026-10-02; findings/2026-10-02-cleanup-boundaries): a list names only
    # layers that can be on the stack with its host. The Gyro and normal modifiers never are, and a
    # cursor is cancelled before Modifier 2 goes on, so neither is listed.
    # Until 90.57 a modifier's cleanup function also named its Temp Cursor Gyro. The cursor layer binds every
    # one of these inputs as a cancel (R135), so it answers them while it is on and the modifier's bind does not
    # run; 90.58 took the remove out (R132 as tightened in 90.57).
    specs = {}
    for name, button, selector in zip(singles, (left, right), (lc, rc)):
        for prefix in ("", "Gyro | "):
            specs[prefix + name] = ({selector}, {prefix + name, button + ": Tap Cover"})
    for name in (left + "!" + right + ": Modifier 2", right + "!" + left + ": Modifier 2"):
        for prefix in ("", "Gyro | "):
            specs[prefix + name] = ({lc, rc}, {prefix + name} | {prefix + single for single in singles} | covers)
    for side, selector in (("Left", "15"), ("Right", "14")):
        prefix = "Menu " + side
        specs[prefix + ": Entry Point"] = ({selector}, {prefix + ": Entry Point", prefix + ": Fn Layer"})
    for button, direction, selector in ((left, "Down", lc), (right, "Up", rc)):
        specs[button + ": Scroll " + direction] = ({selector}, {button + ": Scroll " + direction, button + ": Double Tap Cover"})
    parents = {"Menu " + side + ": " + kind for side in ("Left", "Right") for kind in ("Entry Point", "Fn Layer")}
    for title in ("Transition Set 0", "Transition Set 1", "Transition Set 2"):
        specs[title] = ({"14", "15"}, parents | {title})
    return specs
