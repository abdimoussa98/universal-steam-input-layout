"""Fresh cleanup-owner fixtures shared by cleanup audit tests."""
from tests.support.layouts import EMPTY, SW, add, build, on, press, release, remove


def guarded(*removes, chord=1):
    """A cleanup function: a chord with the owner's button (1 = LB, 2 = RB) beside a repeating removal."""
    return {**on("chord", EMPTY, chord_button=chord), **press(*removes, hold_repeats=1)}


def owner(p_inputs=None, cover=None, base=None, extra=None):
    """Base's LB adds P. P's button_b adds the cover C, which only binds LB. P ends on the LB release."""
    p = {"left_bumper": release(remove("P")), "button_b": press(add("C")),
         "button_a": guarded(remove("P"), remove("C"))}
    p.update(p_inputs or {})
    layers = {"Base": {"switch": (SW, {"left_bumper": press(add("P")), **(base or {})})},
              "P": {"switch": (SW, p)},
              "C": {"switch": (SW, cover or {"left_bumper": release(remove("P"), remove("C"))})}}
    layers.update(extra or {})
    return build(layers)
