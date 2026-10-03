"""Firing one input (steam_layout.stacks).

The modifier rocking replays, which use `walk`, are in test_modifier_rocking.py.
"""
import unittest

from steam_layout.model import Layout
from steam_layout.stacks import fire

from test_audit_inheritance import EMPTY, act, add, build, release, remove


def modifier_layout():
    """Base -> L1 Mod (+ optional Gyro below); Mod applies Cover on RS click; LB release exits to Win."""
    return build({
        "Base": {"switch": ("switches", {"left_bumper": act(add("Mod")), "button_a": act(add("Gyro"))})},
        "Gyro": {},
        "Mod": {"switch": ("switches", {"left_bumper": release([add("Win"), remove("Cover"), remove("Mod")])}),
                "right_joystick": ("joystick_mouse", {"click": act(add("Cover"))})},
        "Cover": {"right_joystick": ("joystick_mouse", {"click": act("key_press E, , ")})},
        "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")), "left_bumper": act(EMPTY),
                                        "button_a": act(EMPTY)})},
    })


class FireTests(unittest.TestCase):
    def test_fire_runs_the_topmost_definer_in_execution_order(self):
        layout = Layout(modifier_layout())
        stack, layer = fire(layout, ("Base", "Mod", "Cover"), "switch", "left_bumper", "release")
        self.assertEqual(layer, "Mod")
        self.assertEqual(stack, ("Base", "Win"))  # removals first, add last

    def test_fire_needs_a_matching_entry(self):
        with self.assertRaises(ValueError):
            fire(Layout(modifier_layout()), ("Base",), "switch", "left_bumper", "release")


if __name__ == "__main__":
    unittest.main()
