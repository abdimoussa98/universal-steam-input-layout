"""The compiled chain engine (steam_layout/native.py) against the Python chains.

chains.py is the reference. `reference()` walks it with the same number of extra presses
(arrivals), tests every stack it visits and every stack one landing past it, and the engine
must give the same stacks and the same pairs. The engine is built on first use; without a
C++ compiler these tests fail, as the audit does.
Record: findings/2026-10-03-simultaneous-cap/README.md.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from steam_layout import native
from steam_layout.chains import Chains
from steam_layout.cleanups import DEFAULT_EXTRAS, Cleanups, audit
from steam_layout.flow_model import resolve
from steam_layout.model import Layout, entries
from steam_layout.stacks import apply_ops
from tests.support.layouts import SW, add, build, press, release, remove

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "versions/neptune/90.20/single-set-default_hold-gyro_90.20.json"
KEY = "key_press K, , "


def second_landing(cover=None):
    """A cover that needs two landings. S is a mode; entering it clears the stack. Base's LB adds E, and E's
    button_b turns into P, which ends on the LB Release. S's button_x adds H (it ends on RB), and H's button_y
    adds H2 (it ends on Start), which takes LB. E binds button_x and button_y, so neither lands over E. P takes
    two steps to arrive, so it is in none of H2's chains, and H2 is two bindings past any stack that one extra
    press builds with P in it."""
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


def nine_buttons():
    """Nine buttons that each add a layer: 986,410 stacks with every one in every order."""
    layers = {"Base": {"switch": (SW, {f"button_{i}": press(add(f"T{i}")) for i in range(9)})}}
    for i in range(9):
        layers[f"T{i}"] = {"switch": (SW, {"left_bumper": release(remove(f"T{i}"))})}
    return build(layers)


def reference(layout, extras):
    """(stacks, {pair: (exits on the keeper, other exits)}) from chains.py with `extras` arrivals."""
    cleanups = Cleanups(layout)
    exits = {lower: found for lower in cleanups.layers if (found := cleanups.exits(lower))}
    keeping = {lower: cleanups.keeper_exits(lower, found) for lower, found in exits.items()}
    chains = Chains(layout, arrivals=extras)
    pairs = {}

    def test(stack):
        for lower in stack:
            for control in exits.get(lower, ()):
                kind, layer, acts, _ = resolve(layout, stack, *control)
                if kind == "binding" and layer == lower:
                    continue
                if kind == "mode":
                    mine = layout.active(lower)[control[0]]["mode"]
                    layer = next((t for t in stack[stack.index(lower) + 1:]
                                  if (g := layout.active(t).get(control[0])) and g["mode"] != mine), layer)
                if acts and any(("remove_layer", lower) in layout.layer_ops(e) for _, e in entries(acts)):
                    continue
                pairs.setdefault((layer, lower), (set(), set()))[0 if control in keeping[lower] else 1].add(control)

    for stack in list(chains.stacks()):
        test(stack)
        for t in (t for layer in stack for t in chains._adding.get(layer, ())):
            if chains.fires(t, stack):
                after = apply_ops(stack, t.ops, layout.base)
                if after != stack:
                    test(after)
    return len(chains.stacks()), pairs


def shape(pairs):
    return {pair: (set(row["hidden"]), set(row["side"])) for pair, row in pairs.items()}


def replays(layout, row):
    """True if the path's bindings fire one after the other from the action set and end on the pair's stack."""
    chains = Chains.of(layout)
    by_text = {t.describe(): t for t in chains.inventory.transitions}
    stack = (layout.base,)
    for step in row["path"]:
        binding = by_text[step.split(": ", 1)[1] if step.startswith(("settle: ", "arrival: ", "landing: ")) else step]
        if not chains.fires(binding, stack):
            return False
        stack = apply_ops(stack, binding.ops, layout.base)
    return stack == row["stack"]


class EngineTests(unittest.TestCase):
    """Tiny layouts: what the engine finds, and what it says."""

    def test_extra_presses_reach_a_cover_two_landings_away(self):
        layout = Layout(second_landing())
        for extras, expected in ((0, set()), (1, set()), (2, {("H2", "P")}), (6, {("H2", "P")})):
            with self.subTest(extras=extras):
                cleanups = Cleanups(layout)
                pairs = cleanups.covered_exits(extras)
                self.assertEqual({pair for pair, row in pairs.items() if row["hidden"]}, expected)
                self.assertEqual(shape(pairs), {p: (set(a), set(b)) for p, (a, b) in reference(layout, extras)[1].items()})
                self.assertEqual((cleanups.walked["extras"], cleanups.walked["settled"]), (extras, True))

    def test_a_pair_has_its_smallest_stack_its_path_and_its_cost(self):
        layout = Layout(second_landing())
        row = Cleanups(layout).covered_exits(2)[("H2", "P")]
        self.assertEqual(row["hidden"], [("switch", "left_bumper")])
        self.assertEqual(row["stack"], ("Base", "S", "P", "H2"))                     # the smallest: H has left again
        self.assertEqual(row["cost"], sum(step.startswith("arrival: ") for step in row["path"]))
        self.assertLessEqual(row["cost"], 2)
        self.assertTrue(any("H switch/button_y" in step for step in row["path"]))    # H's binding adds H2
        self.assertTrue(replays(layout, row))

    def test_a_cover_that_removes_the_lower_layer_there_is_fine(self):
        carried = second_landing(cover={"left_bumper": release(remove("P"), remove("H2"))})
        self.assertNotIn(("H2", "P"), Cleanups(Layout(carried)).covered_exits(2))

    def test_a_mode_block_and_a_disabled_source_are_charged_like_the_reference(self):
        data = build({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                      "P": {"switch": (SW, {"button_b": press(add("M")), "button_y": press(add("D"))}),
                            "joystick": ("dpad", {"click": release(remove("P"))})},
                      "M": {"switch": (SW, {"button_x": press(add("T"))}),
                            "joystick": ("joystick_move", {"touch": press(KEY)})},
                      "T": {"joystick": ("dpad", {"touch": press(KEY)})},
                      "D": {"joystick": ("disabled", {})}})
        layout = Layout(data)
        pairs = Cleanups(layout).covered_exits(1)
        self.assertEqual(shape(pairs), {p: (set(a), set(b)) for p, (a, b) in reference(layout, 1)[1].items()})
        self.assertIn(("M", "P"), pairs)                                               # not T, which only sits on top
        self.assertIn(("D", "P"), pairs)

    def test_the_memory_limit_stops_it_unsettled(self):
        cleanups = Cleanups(Layout(nine_buttons()))
        cleanups.covered_exits(9, memory=1)
        self.assertFalse(cleanups.walked["settled"])
        self.assertIn("memory limit", cleanups.walked["stopped"])
        report = audit(nine_buttons(), {}, extras=9, memory=1)
        self.assertEqual((report["ok"], report["walk"]["settled"]), (False, False))

    def test_the_audit_reads_five_extra_presses_unless_told(self):
        self.assertEqual(DEFAULT_EXTRAS, 5)
        report = audit(second_landing(), {})
        self.assertEqual(report["walk"]["extras"], 5)
        self.assertEqual({(f["layer"], f["target"]) for f in report["findings"] if f["check"] == "hidden exit"}, {("H2", "P")})
        self.assertEqual({f["check"] for f in audit(second_landing(), {}, extras=1)["findings"]}, set())
        skipped = audit(second_landing(), {}, extras=None)                             # the cleanup fix asks for this
        self.assertEqual((skipped["walk"], skipped["ok"]), (None, True))

    def test_past_the_paths_limit_the_stack_and_path_come_from_a_second_run(self):
        layout = Layout(second_landing())
        whole = Cleanups(layout).covered_exits(native.PATHS_UP_TO)
        with mock.patch.object(native, "PATHS_UP_TO", 3):
            split = Cleanups(layout).covered_exits(5)
        self.assertEqual(split, whole)
        with mock.patch.object(native, "PATHS_UP_TO", 1):                              # too few for H2 over P
            row = Cleanups(layout).covered_exits(5)[("H2", "P")]
        self.assertEqual(row["path"], ["no path kept: this stack needs 2 extra presses"])
        self.assertEqual(row["stack"], whole[("H2", "P")]["stack"])

    def test_without_a_compiler_the_audit_stops_with_a_message(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(native, "_checked", None), \
                mock.patch.object(native, "BINARY", Path(folder) / "chain_engine"), \
                mock.patch.object(native.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "needs a C\\+\\+ compiler"):
                audit(second_landing(), {})
            self.assertEqual(audit(second_landing(), {}, extras=None)["ok"], True)     # nothing else needs it

    def test_the_command_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "toy.json"
            path.write_text(json.dumps(second_landing()), encoding="utf-8")
            run = lambda *args: subprocess.run([sys.executable, "-m", "tools.audit_cleanups", str(path), "--no-required", *args],  # noqa: E731
                                               capture_output=True, text=True, cwd=ROOT)
            usual = run()
            self.assertEqual(usual.returncode, 1)
            self.assertIn("Exit checks: the chain walk with 5 extra presses", usual.stdout)
            self.assertIn("covers the exit of P", usual.stdout)
            self.assertEqual(run("--extras", "1").returncode, 0)
            self.assertEqual(run("--extras", "15").returncode, 2)


class SnapshotTests(unittest.TestCase):
    """The frozen 90.20 snapshot: the engine against chains.py, and against itself run other ways."""

    @classmethod
    def setUpClass(cls):
        cls.layout = Layout(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        cls._default_result = None
        cls._covered_observation = None

    @classmethod
    def tearDownClass(cls):
        del cls.layout, cls._default_result, cls._covered_observation

    def default_result(self):
        """One raw default run at extras=3 on this class's frozen, unmodified snapshot."""
        cls = type(self)
        if cls._default_result is None:
            result = self.run_engine(3)
            self.assertTrue(result["settled"])
            cls._default_result = copy.deepcopy(result)
        return copy.deepcopy(cls._default_result)

    def covered_pairs(self):
        """Pairs and walk summary from one decoded wrapper run, separate from the raw baseline."""
        cls = type(self)
        if cls._covered_observation is None:
            cleanups = Cleanups(self.layout)
            pairs = cleanups.covered_exits(3)
            self.assertTrue(cleanups.walked["settled"])
            cls._covered_observation = copy.deepcopy((pairs, cleanups.walked))
        pairs, walked = copy.deepcopy(cls._covered_observation)
        self.assertTrue(walked["settled"])
        return pairs

    def run_engine(self, extras, **options):
        cleanups = Cleanups(self.layout)
        tables = native.Tables(self.layout, cleanups.inv)
        table, number = {}, 0
        for lower in cleanups.layers:
            found = cleanups.exits(lower)
            keeping = cleanups.keeper_exits(lower, found) if found else ()
            modes = {source: mode for source, mode, _ in tables.groups[tables.ident[lower]]}
            for control in found:
                table.setdefault(tables.ident[lower], []).append(
                    (number, tables.control(*control), control[0], control in keeping, modes[control[0]]))
                number += 1
        return native.run(tables, table, extras, **options)

    def test_the_same_stacks_and_pairs_as_the_chains(self):
        for extras in (0, 1, 2):
            with self.subTest(extras=extras):
                count, pairs = reference(self.layout, extras)
                cleanups = Cleanups(self.layout)
                found = cleanups.covered_exits(extras)
                self.assertTrue(cleanups.walked["settled"])
                self.assertEqual(cleanups.walked["stacks"], count)
                self.assertEqual(shape(found), {p: (set(a), set(b)) for p, (a, b) in pairs.items()})

    def test_every_path_replays_in_python(self):
        for pair, row in self.covered_pairs().items():
            with self.subTest(pair=pair):
                self.assertTrue(replays(self.layout, row), row["path"])
                self.assertEqual(row["cost"], sum(step.startswith("arrival: ") for step in row["path"]))

    def test_the_result_does_not_depend_on_the_threads(self):
        one, many = self.run_engine(3, threads=1), self.default_result()
        for key in ("states", "stacks", "longest", "by_cost", "pairs"):               # the pairs carry their paths
            self.assertEqual(one[key], many[key], key)

    def test_keeping_paths_and_small_batches_change_nothing_else(self):
        """The waiting states of a cost are taken up in batches; a batch must not pick up what the cost just added."""
        usual = self.default_result()
        strip = lambda result: [{k: v for k, v in pair.items() if k != "path"} for pair in result["pairs"]]  # noqa: E731
        for label, other in (("no paths", self.run_engine(3, paths=False)), ("small batches", self.run_engine(3, batch=500)),
                             ("both", self.run_engine(3, paths=False, batch=500))):
            with self.subTest(label):
                for key in ("states", "stacks", "longest", "by_cost"):
                    self.assertEqual(other[key], usual[key], key)
                self.assertEqual(strip(other), strip(usual))

    def test_it_finds_the_tap_cover_over_a_pad_layer(self):
        """The gap that started this: the chain check with one extra press tested one stack per pair and missed it."""
        pairs = self.covered_pairs()
        row = pairs[("Menu Left: Entry Point", "RST: Entry Point")]
        self.assertEqual(row["hidden"], [("right_joystick", "touch")])
        self.assertEqual(row["stack"][-1], "Menu Buttons: Tap Cover")
        self.assertIn(("Menu Right: Entry Point", "RST: Entry Point"), pairs)


if __name__ == "__main__":
    unittest.main()
