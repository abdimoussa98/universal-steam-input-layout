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

ROOT = Path(__file__).resolve().parents[1]
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


class RockingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {v: Layout(json.loads((ROOT / f"neptune/single-set-{v}_hold-gyro_latest.json").read_text()))
                       for v in VARIANTS}

    def cases(self):
        """(label, layout, L input, R input, Base entry activation, Names), with Gyro off and on."""
        for variant, (L, R, entry, sides) in VARIANTS.items():
            for gyro in (False, True):
                yield f"{variant}{', Gyro' if gyro else ''}", self.layouts[variant], L, R, entry, Names(sides, gyro)

    def play(self, layout, n, steps):
        return walk(layout, steps, start=n.base)

    def assert_no_window(self, steps):
        for s in steps:
            self.assertFalse([t for t in s["stack"] if t.endswith(": Double Tap") or t.endswith(": Scroll Down")
                              or t.endswith(": Scroll Up")], s["label"])

    def assert_covers_above_their_modifiers(self, steps, n):
        for s in steps:
            for side in (n.l, n.r):
                if n.cover(side) in s["stack"] and n.mod(side) in s["stack"]:
                    self.assertGreater(s["stack"].index(n.cover(side)), s["stack"].index(n.mod(side)), s["label"])

    # --- one bumper ------------------------------------------------------------------------

    def test_a_double_tap_scrolls(self):
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                steps = self.play(layout, n, [(*L, entry, "press L"), (*L, "release", "let go"),
                                              (*L, "Full_Press", "press again inside 150 ms")])
                self.assertEqual([s["stack"][len(n.base):] for s in steps],
                                 [(n.mod(n.l),), (f"{n.l}: Double Tap",), (f"{n.l}: Scroll Down",)])

    def test_a_used_bumper_exits_cleanly_without_a_window(self):
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                steps = self.play(layout, n, [(*L, entry, "press L"), (*A, "chord", "press A with L held"),
                                              (*L, "release", "let go of L"), (*L, entry, "press L again at once")])
                self.assertEqual(steps[1]["stack"][len(n.base):], (n.mod(n.l), n.cover(n.l)))
                self.assertEqual(steps[2]["layer"], n.cover(n.l))       # the cover's release, not the modifier's
                self.assertEqual(steps[2]["stack"], n.base)
                self.assertEqual(steps[3]["stack"][len(n.base):], (n.mod(n.l),))   # a new press, not a scroll

    def test_the_cursor_exits_cleanly_without_a_window(self):
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                steps = self.play(layout, n, [(*L, entry, "press L"), (*L, "chord", "hold L 300 ms"),
                                              (*L, "release", "let go of L")])
                self.assertEqual(steps[1]["stack"][len(n.base):], (n.mod(n.l), f"{n.l}: Temp Cursor Gyro"))
                self.assertEqual(steps[2]["layer"], f"{n.l}: Temp Cursor Gyro")
                self.assertEqual(steps[2]["stack"], n.base)

    # --- the Modifier 2 entry ----------------------------------------------------------------

    def test_the_modifier_2_entry_adds_in_this_exact_order(self):
        """First side's cover, second modifier, second side's cover, Modifier 2 last."""
        for label, layout, L, R, entry, n in self.cases():
            for first, second, inp in ((n.l, n.r, R), (n.r, n.l, L)):
                with self.subTest(label, first=first):
                    steps = self.play(layout, n, [(*(L if first == n.l else R), entry, "press the first side"),
                                                  (*inp, "chord", "press the second side")])
                    added = steps[1]["stack"][len(n.base):]
                    self.assertEqual(added, (n.mod(first), n.cover(first), n.mod(second), n.cover(second),
                                             n.mod2(first)))

    def test_inside_200_ms_letting_go_of_either_side_is_the_quick_tap(self):
        """No combined cover yet: Modifier 2's own release clears every modifier and toggles Gyro."""
        for label, layout, L, R, entry, n in self.cases():
            for let_go in (L, R):
                with self.subTest(label, let_go=let_go):
                    steps = self.play(layout, n, [(*L, entry, "hold L"), (*R, "chord", "press R"),
                                                  (*let_go, "release", "let go inside 200 ms")])
                    self.assertEqual(steps[2]["layer"], n.mod2(n.l))
                    self.assertEqual(steps[2]["stack"], ("Base",) if n.g else ("Base", "Gyro"))

    # --- rocking -----------------------------------------------------------------------------

    def test_rock_from_left_to_right_and_back_out_without_a_window(self):
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                steps = self.play(layout, n, [
                    (*L, entry, "hold L"),
                    (*R, "chord", "hold R too"),
                    (*R, "chord", "keep both 200 ms: combined cover"),
                    (*L, "release", "let go of L"),
                    (*L, "chord", "press L again"),
                    (*L, "chord", "keep both 200 ms: combined cover, on the side pressed second"),
                    (*R, "release", "let go of R"),
                    (*L, "release", "let go of L"),
                ])
                stacks = [s["stack"][len(n.base):] for s in steps]
                self.assertEqual([s["layer"] for s in steps], [
                    n.base[-1], n.mod(n.l), n.mod2(n.l), n.both, n.mod(n.r), n.mod2(n.r), n.both, n.cover(n.l)])
                self.assertEqual(stacks[2], (n.mod(n.l), n.cover(n.l), n.mod(n.r), n.cover(n.r), n.mod2(n.l), n.both))
                self.assertEqual(stacks[3], (n.mod(n.r), n.cover(n.r)))               # on the right modifier
                self.assertEqual(stacks[4], (n.mod(n.r), n.cover(n.r), n.mod(n.l), n.cover(n.l), n.mod2(n.r)))
                self.assertEqual(stacks[6], (n.mod(n.l), n.cover(n.l)))               # on the left modifier
                self.assertEqual(stacks[7], ())                                       # out, cleanly
                self.assert_no_window(steps)
                self.assert_covers_above_their_modifiers(steps, n)

    def test_rock_from_right_to_left_and_back_out_without_a_window(self):
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                steps = self.play(layout, n, [
                    (*R, entry, "hold R"),
                    (*L, "chord", "hold L too"),
                    (*L, "chord", "keep both 200 ms: combined cover"),
                    (*R, "release", "let go of R"),
                    (*R, "chord", "press R again"),
                    (*R, "chord", "keep both 200 ms: combined cover"),
                    (*L, "release", "let go of L"),
                    (*R, "release", "let go of R"),
                ])
                stacks = [s["stack"][len(n.base):] for s in steps]
                self.assertEqual(stacks[3], (n.mod(n.l), n.cover(n.l)))
                self.assertEqual(stacks[4], (n.mod(n.l), n.cover(n.l), n.mod(n.r), n.cover(n.r), n.mod2(n.l)))
                self.assertEqual(stacks[6], (n.mod(n.r), n.cover(n.r)))
                self.assertEqual(steps[7]["layer"], n.cover(n.r))
                self.assertEqual(stacks[7], ())
                self.assert_no_window(steps)
                self.assert_covers_above_their_modifiers(steps, n)

    def test_rock_back_and_forth_several_times(self):
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                rock = [(*L, "release", "let go of L"), (*L, "chord", "press L again"), (*L, "chord", "200 ms"),
                        (*R, "release", "let go of R"), (*R, "chord", "press R again"), (*R, "chord", "200 ms")]
                steps = self.play(layout, n, [(*L, entry, "hold L"), (*R, "chord", "hold R"), (*R, "chord", "200 ms")]
                                  + rock * 3)
                self.assertEqual(steps[-1]["stack"][len(n.base):],
                                 (n.mod(n.l), n.cover(n.l), n.mod(n.r), n.cover(n.r), n.mod2(n.l), n.both))
                self.assert_no_window(steps)
                self.assert_covers_above_their_modifiers(steps, n)

    def test_the_combined_cover_releases_only_its_side_and_both_orders(self):
        """The rocking lists. Both Modifier 2 orders stay in them: the cover can sit on either."""
        for variant, (L, R, entry, (l, r)) in VARIANTS.items():
            layout = self.layouts[variant]
            for side, inp in ((l, L), (r, R)):
                other = r if side == l else l
                with self.subTest(variant, side=side):
                    activators = layout.active(f"{l}&{r}: Tap Cover")[inp[0]]["inputs"][inp[1]]["activators"]
                    removed = {t for op, t in layout.layer_ops(activators["release"]) if op == "remove_layer"}
                    orders = {f"{g}{l}!{r}: Modifier 2" for g in ("", "Gyro | ")} | {f"{g}{r}!{l}: Modifier 2" for g in ("", "Gyro | ")}
                    self.assertTrue(orders <= removed)
                    self.assertIn(f"{side}: Tap Cover", removed)
                    self.assertFalse({t for t in removed if t.startswith(f"{other}:") or t.startswith(f"Gyro | {other}:")})


if __name__ == "__main__":
    unittest.main()
