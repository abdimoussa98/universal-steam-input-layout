"""The capped walk (steam_layout/walk.py) and the Cleanup audit's walk option.

Tiny layouts first, one rule per test, then the frozen 90.20 snapshot.
Record: findings/2026-10-03-simultaneous-cap/README.md.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.cleanups import Cleanups, audit
from steam_layout.flow_model import resolve
from steam_layout.model import Layout, defined
from steam_layout.walk import MAX_SIMULTANEOUS, Walk
from tests.test_audit_inheritance import add, build, remove
from tests.test_chains import SW, press, release

ROOT = Path(__file__).resolve().parents[1]
KEY = "key_press K, , "


def two_buttons(x=None):
    """Base's button_a adds X and its button_b adds Y. Each leaves on its own button's Release."""
    return build({"Base": {"switch": (SW, {"button_a": press(add("X")), "button_b": press(add("Y"))})},
                  "X": {"switch": (SW, {"button_a": release(remove("X")), **(x or {})})},
                  "Y": {"switch": (SW, {"button_b": release(remove("Y"))})}})


def stacks(walk):
    return {walk.named(stack) for stack in walk.parents}


class WalkTests(unittest.TestCase):
    def test_it_builds_every_order(self):
        walk = Walk(Layout(two_buttons())).run()
        self.assertTrue(walk.settled)
        self.assertEqual(stacks(walk), {("Base",), ("Base", "X"), ("Base", "Y"), ("Base", "X", "Y"), ("Base", "Y", "X")})
        self.assertEqual((walk.count, walk.longest, walk.presses), (5, 2, 2))

    def test_the_cap_is_layers_on_at_once_without_the_action_set(self):
        walk = Walk(Layout(two_buttons()), max_layers=1).run()
        self.assertTrue(walk.settled)
        self.assertEqual(stacks(walk), {("Base",), ("Base", "X"), ("Base", "Y")})
        self.assertEqual(MAX_SIMULTANEOUS, 10)

    def test_a_binding_fires_only_when_its_layer_answers(self):
        # X binds button_b itself, so Base's button_b can't add Y on top of X.
        walk = Walk(Layout(two_buttons(x={"button_b": press(KEY)}))).run()
        self.assertEqual(stacks(walk), {("Base",), ("Base", "X"), ("Base", "Y"), ("Base", "Y", "X")})

    def test_a_stack_has_a_shortest_path(self):
        walk = Walk(Layout(two_buttons())).run()
        path = walk.path(walk.stack(("Base", "Y", "X")))
        self.assertEqual([step.split(":")[0] for step in path],
                         ["Base switch/button_b Full_Press#0", "Base switch/button_a Full_Press#0"])
        self.assertEqual(walk.path(walk.stack(("Base",))), [])

    def test_a_chain_longer_than_the_cap_is_not_built(self):
        layers = {"Base": {"switch": (SW, {"button_a": press(add("L1"))})}}
        for i in range(1, 13):
            layers[f"L{i}"] = {"switch": (SW, {"button_a": press(add(f"L{i + 1}"))} if i < 12 else {})}
        walk = Walk(Layout(build(layers))).run()
        self.assertEqual((walk.longest, walk.count), (10, 11))        # Base and ten layers; L11 and L12 never land

    def test_the_memory_limit_stops_it_unsettled(self):
        layers = {"Base": {"switch": (SW, {f"button_{i}": press(add(f"T{i}")) for i in range(9)})}}
        for i in range(9):
            layers[f"T{i}"] = {"switch": (SW, {"left_bumper": release(remove(f"T{i}"))})}
        walk = Walk(Layout(build(layers)), max_layers=9).run(memory=1)
        self.assertFalse(walk.settled)
        self.assertIn("memory limit", walk.stopped)

    def test_progress_is_told_once_per_press(self):
        seen = []
        Walk(Layout(two_buttons())).run(progress=lambda *row: seen.append(row))
        self.assertEqual(seen, [(0, 1, 2, 3), (1, 2, 2, 5), (2, 2, 0, 5)])


class LookupTests(unittest.TestCase):
    """The walk's own lookup against flow_model.resolve, which every other audit uses."""

    def test_it_answers_like_resolve_on_the_snapshot(self):
        layout = Layout(json.loads((ROOT / "versions/neptune/90.20/single-set-default_hold-gyro_90.20.json")
                                   .read_text(encoding="utf-8")))
        walk = Walk(layout, max_layers=3).run()
        self.assertTrue(walk.settled)
        bound = sorted({(source, name) for title in layout.presets for source, group in layout.active(title).items()
                        for name in group.get("inputs", {}) if defined(group, name)})
        checked = 0
        for stack in list(walk.parents)[::7]:
            found, _ = walk.answers(stack)
            named = walk.named(stack)
            for control in bound:
                kind, layer, _, _ = resolve(layout, named, *control)
                mine = found.get(walk.controls[control])
                self.assertEqual(mine if mine is None else walk.titles[mine], layer if kind == "binding" else None,
                                 (named, control))
            checked += 1
        self.assertGreater(checked, 500)


def second_landing(cover=None):
    """A cover that needs two landings. S is a mode; entering it clears the stack. Base's LB adds E, and E's
    button_b turns into P, which ends on the LB Release. S's button_x adds H (it ends on RB), and H's button_y
    adds H2 (it ends on Start), which takes LB. E binds button_x and button_y, so neither lands over E. P takes
    two steps to arrive, so it is in none of H2's chains, and H2 is two bindings past any stack the chains
    build with P in it."""
    clear = press(remove("E"), remove("P"), remove("H"), remove("H2"), add("S"))
    return build({"Base": {"switch": (SW, {"button_a": clear, "left_bumper": press(add("E"))})},
                  "S": {"switch": (SW, {"button_a": press(remove("H"), remove("H2"), remove("S")),
                                        "button_x": press(add("H"))})},
                  "E": {"switch": (SW, {"left_bumper": release(remove("E")), "button_b": press(remove("E"), add("P")),
                                        "button_x": press(KEY), "button_y": press(KEY)})},
                  "P": {"switch": (SW, {"left_bumper": release(remove("P"))})},
                  "H": {"switch": (SW, {"right_bumper": release(remove("H")), "button_y": press(add("H2"))})},
                  "H2": {"switch": (SW, {"button_escape": release(remove("H2")),
                                         **(cover or {"left_bumper": press(KEY)})})}})


def hidden(data, **options):
    return {(f["layer"], f["target"]) for f in audit(data, {}, **options)["findings"] if f["check"] == "hidden exit"}


class WalkedExitTests(unittest.TestCase):
    def test_the_walk_finds_a_cover_two_landings_away(self):
        data = second_landing()
        self.assertEqual(hidden(data), set())                              # the chain stacks never hold H2 over P
        self.assertEqual(hidden(data, walk=6), {("H2", "P")})
        finding = next(f for f in audit(data, {}, walk=6)["findings"] if f["check"] == "hidden exit")
        self.assertIn(finding["example"], ("Base > S > P > H > H2", "Base > S > H > P > H2"))
        self.assertEqual(finding["inputs"], ["LB"])
        self.assertTrue(finding["path"][-1].startswith("H switch/button_y"), finding["path"])

    def test_a_cover_that_removes_the_lower_layer_there_is_fine(self):
        carried = second_landing(cover={"left_bumper": release(remove("P"), remove("H2"))})
        self.assertEqual(hidden(carried, walk=6), set())

    def test_a_cap_below_the_stack_does_not_see_it(self):
        self.assertEqual(hidden(second_landing(), walk=3), set())          # S, P, H and H2 are four layers on

    def test_a_mode_block_is_charged_like_the_chain_check(self):
        data = build({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                      "P": {"switch": (SW, {"button_b": press(add("M"))}),
                            "joystick": ("dpad", {"click": release(remove("P"))})},
                      "M": {"switch": (SW, {"button_x": press(add("T"))}),
                            "joystick": ("joystick_move", {"touch": press(KEY)})},
                      "T": {"joystick": ("dpad", {"touch": press(KEY)})}})
        self.assertEqual(hidden(data), {("M", "P")})
        self.assertEqual(hidden(data, walk=4), {("M", "P")})

    def test_the_report_says_what_the_walk_did(self):
        report = audit(second_landing(), {}, walk=6)
        self.assertEqual(report["walk"], {"layers": 6, "extras": None, "stacks": report["walk"]["stacks"],
                                          "settled": True, "presses": report["walk"]["presses"], "longest": 4,
                                          "stopped": None, "engine": report["walk"]["engine"]})
        self.assertFalse(report["ok"])
        self.assertIsNone(audit(second_landing(), {})["walk"])

    def test_a_walk_that_did_not_finish_is_not_ok(self):
        data = two_buttons()
        self.assertTrue(audit(data, {}, walk=2)["ok"])
        layers = {"Base": {"switch": (SW, {f"button_{i}": press(add(f"T{i}")) for i in range(9)})}}
        for i in range(9):
            layers[f"T{i}"] = {"switch": (SW, {"left_bumper": release(remove(f"T{i}"))})}
        report = audit(build(layers), {}, walk=9, memory=1)
        self.assertEqual((report["ok"], report["walk"]["settled"]), (False, False))

    def test_the_command_line_takes_a_layer_count(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "toy.json"
            path.write_text(json.dumps(second_landing()), encoding="utf-8")
            run = lambda *args: subprocess.run([sys.executable, "-m", "tools.audit_cleanups", str(path), *args],  # noqa: E731
                                               capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(run().returncode, 0)
            walked = run("--walk", "6")
            self.assertEqual(walked.returncode, 1)
            self.assertIn("every stack with at most 6 layers on at once", walked.stdout)
            self.assertIn("covers the exit of P", walked.stdout)
            self.assertEqual(run("--walk", "11").returncode, 2)            # over the ceiling


class SnapshotTests(unittest.TestCase):
    """The frozen 90.20 snapshot. With five layers on at once the walk meets the gap the chain check missed:
    `Menu Buttons: Tap Cover` directly over a mouse-mode pad layer leaves the right-stick touch unanswered."""

    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "versions/neptune/90.20/single-set-default_hold-gyro_90.20.json")
                          .read_text(encoding="utf-8"))
        cls.cleanups = Cleanups(Layout(data))
        cls.pairs, cls.walk = cls.cleanups.walked_exits(5)

    def test_it_settles(self):
        self.assertTrue(self.walk.settled)
        self.assertEqual((self.walk.count, self.walk.longest), (239181, 5))

    def test_it_finds_the_tap_cover_over_a_pad_layer(self):
        row = self.pairs[("Menu Left: Entry Point", "RST: Entry Point")]
        self.assertEqual(row["hidden"], [("right_joystick", "touch")])
        self.assertEqual(row["stack"][-1], "Menu Buttons: Tap Cover")
        self.assertEqual(len(row["path"]), 5)
        self.assertIn(("Menu Right: Entry Point", "RST: Entry Point"), self.pairs)

    def test_every_other_pair_on_a_keeper_is_a_touchpad_pair(self):
        pads = self.cleanups.touchpad_layers()
        rest = {pair for pair, row in self.pairs.items() if row["hidden"]
                and not (pair[0] in pads or pair[1] in pads or any(source.endswith("trackpad") for source, _ in row["hidden"]))}
        self.assertEqual(rest, {("Menu Left: Entry Point", "RST: Entry Point"), ("Menu Right: Entry Point", "RST: Entry Point")})


if __name__ == "__main__":
    unittest.main()
