"""Modifier rocking: hold both modifiers, let go of one, press it again, without ever scrolling.

Author-confirmed, 2026-09-30 and 2026-10-02. The author relies on this to type fast
and calls the add order "very sensitive". Written up in
resources/Steam Input JSON Structure.md, "Rocking Between Modifiers 0, 1 and 2".

The rule behind it: a release fires on the topmost layer that binds that bumper. A
Double Tap window (and so a scroll) only opens from a single modifier's own release,
which happens only when the bumper was tapped without being used. Using a bumper puts
its Tap Cover directly above its modifier, and the cover's release is a clean exit.

Replayed with steam_layout.stacks.walk on the working layouts, default (L1/R1 bumpers)
and alternative (L2/R2 trigger soft pulls), with Gyro off and on.
"""


import json


from pathlib import Path


import unittest


from steam_layout.model import Layout


from steam_layout.stacks import walk


ROOT = Path(__file__).resolve().parents[3]


VARIANTS = {  # first-side input, second-side input, Base entry activation, side names
    "default": (("switch", "left_bumper"), ("switch", "right_bumper"), "chord", ("L1", "R1")),
    "alternative": (("left_trigger", "edge"), ("right_trigger", "edge"), "Full_Press", ("L2", "R2")),
}


A = ("button_diamond", "button_a")


class Names:
    """Layer titles for one variant, with or without Gyro."""

    def __init__(self, sides, gyro):
        self.l, self.r = sides
        self.g = "Gyro | " if gyro else ""
        self.base = ("Base", "Gyro") if gyro else ("Base",)

    def mod(self, side):
        return f"{self.g}{side}: Modifier {0 if side == self.l else 1}"

    def cover(self, side):
        return f"{side}: Tap Cover"

    def mod2(self, first):
        second = self.r if first == self.l else self.l
        return f"{self.g}{first}!{second}: Modifier 2"

    @property
    def both(self):
        return f"{self.l}&{self.r}: Tap Cover"


__all__ = [name for name in globals() if not name.startswith("__")]
