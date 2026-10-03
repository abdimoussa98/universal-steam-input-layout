"""Firing one input and walking a sequence (steam_layout.stacks)."""
import json
from pathlib import Path
import unittest

from steam_layout.model import Layout
from steam_layout.stacks import fire, walk

from test_audit_inheritance import EMPTY, act, add, build, release, remove

ROOT = Path(__file__).resolve().parents[1]


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


class RockingTests(unittest.TestCase):
    """Author-confirmed Mod 2 rocking (default names; alternative uses L2/R2 triggers).

    With the combined cover applied, releasing one side removes only that side
    and both Mod 2 orders. The held side's modifier and its Tap Cover stay, in
    that order, so releasing it later exits cleanly (no Double Tap window) and
    pressing the other side again goes straight back to Mod 2.
    """

    def test_rock_between_mod_1_and_mod_2_without_passing_through_base(self):
        variants = {  # (layout, first-side input, second-side input, Base entry activation, L/R names)
            "default": (("switch", "left_bumper"), ("switch", "right_bumper"), "chord", ("L1", "R1")),
            "alternative": (("left_trigger", "edge"), ("right_trigger", "edge"), "Full_Press", ("L2", "R2")),
        }
        for variant, (L, R, entry, (l, r)) in variants.items():
            layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
            steps = walk(layout, [
                (*L, entry, "hold L"),
                (*R, "chord", "hold R too"),
                (*R, "chord", "keep both held 200 ms: combined cover"),
                (*L, "release", "let go of L"),
                (*L, "chord", "press L again"),
                (*L, "chord", "keep both held 200 ms: combined cover again (on the side pressed second)"),
                (*R, "release", "let go of R"),
            ])
            stacks = [s["stack"] for s in steps]
            with self.subTest(variant=variant):
                self.assertEqual([s["layer"] for s in steps], [
                    "Base", f"{l}: Modifier 0", f"{l}!{r}: Modifier 2", f"{l}&{r}: Tap Cover",
                    f"{r}: Modifier 1", f"{r}!{l}: Modifier 2", f"{l}&{r}: Tap Cover"])
                self.assertEqual(stacks[2], ("Base", f"{l}: Modifier 0", f"{l}: Tap Cover", f"{r}: Modifier 1",
                                             f"{r}: Tap Cover", f"{l}!{r}: Modifier 2", f"{l}&{r}: Tap Cover"))
                # Back on Mod 1 with its cover kept above it
                self.assertEqual(stacks[3], ("Base", f"{r}: Modifier 1", f"{r}: Tap Cover"))
                # Straight back to Mod 2, no Base or Double Tap window in between
                self.assertEqual(stacks[4], ("Base", f"{r}: Modifier 1", f"{r}: Tap Cover", f"{l}: Modifier 0",
                                             f"{l}: Tap Cover", f"{r}!{l}: Modifier 2"))
                self.assertEqual(stacks[6], ("Base", f"{l}: Modifier 0", f"{l}: Tap Cover"))  # rocked to Mod 0
                # The cover sits above its modifier, so the held side's release is the cover's clean exit.
                self.assertEqual(fire(layout, stacks[3], *R, "release")[1], f"{r}: Tap Cover")

if __name__ == "__main__":
    unittest.main()
