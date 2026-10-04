"""The compiled walk engine (steam_layout/native.py) against the Python walks.

The Python walks are the reference. Every test here runs both and expects the same stacks and
the same findings. Skipped when no C++ compiler is installed.
Record: findings/2026-10-03-simultaneous-cap/README.md.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout import native
from steam_layout.chains import Chains
from steam_layout.cleanups import Cleanups, audit
from steam_layout.flow_model import resolve
from steam_layout.model import Layout, entries
from steam_layout.stacks import apply_ops
from steam_layout.walk import Walk
from tests.test_audit_inheritance import add, build, remove
from tests.test_chains import SW, press, release
from tests.test_walk import KEY, second_landing, two_buttons

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "versions/neptune/90.20/single-set-default_hold-gyro_90.20.json"


def shape(pairs):
    return {pair: (sorted(row["hidden"]), sorted(row["side"]), len(row["path"])) for pair, row in pairs.items()}


def both(data, layers):
    cleanups = Cleanups(Layout(data))
    python, slow = cleanups.walked_exits(layers, engine=False)
    engine, fast = cleanups.walked_exits(layers, engine=True)
    return (python, slow), (engine, fast)


def chain_reference(layout, extras):
    """The Python chain walk with `extras` arrivals: every visited stack and every landing past it, tested."""
    cleanups = Cleanups(layout)
    exits = {lower: found for lower in cleanups.layers if (found := cleanups.exits(lower))}
    keeping = {lower: cleanups.keeper_exits(lower, found) for lower, found in exits.items()}
    chains = Chains(layout, arrivals=extras, workers=os.cpu_count())
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


@unittest.skipUnless(native.available() and native.available(native.CHAIN), "no C++ compiler: the walk engines aren't built")
class EngineTests(unittest.TestCase):
    def same(self, data, layers):
        (python, slow), (engine, fast) = both(data, layers)
        self.assertEqual((fast.count, fast.presses, fast.longest, fast.settled),
                         (slow.count, slow.presses, slow.longest, slow.settled))
        self.assertEqual(shape(engine), shape(python))
        return engine, fast

    def test_the_same_stacks_on_tiny_layouts(self):
        for layers in (1, 2, 6):
            with self.subTest(layers=layers):
                _, walk = self.same(two_buttons(), layers)
        self.assertEqual((walk.count, walk.longest, walk.presses), (5, 2, 2))
        self.same(two_buttons(x={"button_b": press(KEY)}), 6)

    def test_the_same_findings_two_landings_away(self):
        pairs, _ = self.same(second_landing(), 6)
        row = pairs[("H2", "P")]
        self.assertEqual(row["hidden"], [("switch", "left_bumper")])
        self.assertEqual(row["stack"][-1], "H2")
        self.assertTrue(row["path"][-1].startswith("H switch/button_y"), row["path"])
        self.same(second_landing(), 3)
        self.same(second_landing(cover={"left_bumper": release(remove("P"), remove("H2"))}), 6)

    def test_the_same_charge_for_a_mode_block_and_a_disabled_source(self):
        data = build({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                      "P": {"switch": (SW, {"button_b": press(add("M")), "button_y": press(add("D"))}),
                            "joystick": ("dpad", {"click": release(remove("P"))})},
                      "M": {"switch": (SW, {"button_x": press(add("T"))}),
                            "joystick": ("joystick_move", {"touch": press(KEY)})},
                      "T": {"joystick": ("dpad", {"touch": press(KEY)})},
                      "D": {"joystick": ("disabled", {})}})
        pairs, _ = self.same(data, 5)
        self.assertIn(("M", "P"), pairs)
        self.assertIn(("D", "P"), pairs)

    def test_the_same_result_on_the_snapshot(self):
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        pairs, walk = self.same(data, 4)
        self.assertEqual(walk.count, 41050)
        self.assertGreater(len(pairs), 100)

    def test_the_memory_limit_stops_it_unsettled(self):
        layers = {"Base": {"switch": (SW, {f"button_{i}": press(add(f"T{i}")) for i in range(9)})}}
        for i in range(9):
            layers[f"T{i}"] = {"switch": (SW, {"left_bumper": release(remove(f"T{i}"))})}
        _, walk = Cleanups(Layout(build(layers))).walked_exits(9, memory=1, engine=True)
        self.assertFalse(walk.settled)
        self.assertIn("memory limit", walk.stopped)

    def test_the_chain_walk_has_the_chains_stacks_and_findings(self):
        layout = Layout(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        for extras in (0, 1):
            with self.subTest(extras=extras):
                count, reference = chain_reference(layout, extras)
                pairs, walk = Cleanups(layout).chained_exits(extras)
                self.assertTrue(walk.settled)
                self.assertEqual(walk.count, count)
                self.assertEqual({pair: (set(row["hidden"]), set(row["side"])) for pair, row in pairs.items()}, reference)

    def test_extra_presses_reach_the_cover_the_chain_check_misses(self):
        data = second_landing()
        hidden = lambda **options: {(f["layer"], f["target"]) for f in audit(data, {}, **options)["findings"]  # noqa: E731
                                    if f["check"] == "hidden exit"}
        self.assertEqual(hidden(), set())
        self.assertEqual(hidden(extras=2), {("H2", "P")})
        report = audit(data, {}, extras=2)
        self.assertEqual((report["walk"]["extras"], report["walk"]["engine"], report["walk"]["settled"]), (2, True, True))

    def test_the_chain_engine_matches_the_engine_that_keeps_paths(self):
        """chain_engine.cpp walks by cost and keeps (stack, chain layer) once; the stacks and findings are the same."""
        layout = Layout(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        cleanups = Cleanups(layout)
        for extras in (0, 1, 2, 3):
            with self.subTest(extras=extras):
                walk = Walk(layout, None, cleanups.inv)
                rows = cleanups._exit_rows(walk)
                first = cleanups._engine_exits(walk, rows, None, None, None, extras=extras, landings=True)
                count, longest = walk.count, walk.longest
                second = cleanups._engine_exits(walk, rows, None, None, None, extras=extras, landings=True,
                                                program=native.CHAIN)
                self.assertTrue(walk.settled)
                self.assertEqual((walk.count, walk.longest), (count, longest))
                self.assertEqual({pair: (sorted(row["hidden"]), sorted(row["side"])) for pair, row in second.items()},
                                 {pair: (sorted(row["hidden"]), sorted(row["side"])) for pair, row in first.items()})
                self.assertLessEqual(walk.engine["nodes"], count * len(layout.presets))
                self.assertTrue(all(row["cost"] <= extras for row in second.values()))

    def test_the_chain_engine_gives_the_same_answer_on_one_thread(self):
        layout = Layout(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        cleanups = Cleanups(layout)
        walk = Walk(layout, None, cleanups.inv)
        rows = cleanups._exit_rows(walk)
        results = []
        for threads in (1, None):
            pairs = cleanups._engine_exits(walk, rows, None, None, threads, extras=3, landings=True, program=native.CHAIN)
            results.append((walk.count, walk.engine["nodes"], walk.engine["levels"],
                            {pair: (row["hidden"], row["side"], row["stack"], row["cost"]) for pair, row in pairs.items()}))
        self.assertEqual(results[0], results[1])

    def test_past_four_extra_presses_the_paths_come_from_the_small_run(self):
        data = second_landing()
        cleanups = Cleanups(Layout(data))
        small, _ = cleanups.chained_exits(4)
        large, walk = cleanups.chained_exits(6)
        self.assertEqual(walk.engine["levels"][0] > 0, True)                    # the chain engine ran: states by cost
        self.assertEqual({pair: (row["hidden"], row["side"], row["stack"], row["path"]) for pair, row in large.items()},
                         {pair: (row["hidden"], row["side"], row["stack"], row["path"]) for pair, row in small.items()})
        self.assertIn("H switch/button_y", large[("H2", "P")]["path"][-1])        # a step or a landing, by H's button

    def test_the_chain_engine_stops_at_the_memory_limit(self):
        layers = {"Base": {"switch": (SW, {f"button_{i}": press(add(f"T{i}")) for i in range(9)})}}
        for i in range(9):
            layers[f"T{i}"] = {"switch": (SW, {"left_bumper": release(remove(f"T{i}"))})}
        cleanups = Cleanups(Layout(build(layers)))
        walk = Walk(cleanups.layout, None, cleanups.inv)
        cleanups._engine_exits(walk, cleanups._exit_rows(walk), 1, None, None, extras=9, landings=True, program=native.CHAIN)
        self.assertFalse(walk.settled)
        self.assertIn("memory limit", walk.stopped)

    def test_the_command_line_names_the_walk_it_ran(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "toy.json"
            path.write_text(json.dumps(second_landing()), encoding="utf-8")
            run = lambda *args: subprocess.run([sys.executable, "-m", "tools.audit_cleanups", str(path), *args],  # noqa: E731
                                               capture_output=True, text=True, cwd=ROOT)
            self.assertIn("(compiled engine)", run("--walk", "6").stdout)
            self.assertIn("(Python)", run("--walk", "6", "--python").stdout)
            chained = run("--extras", "2")
            self.assertEqual(chained.returncode, 1)
            self.assertIn("the chain walk with 2 extra presses", chained.stdout)
            self.assertIn("covers the exit of P", run("--extras", "6").stdout)
            self.assertEqual(run("--extras", "15").returncode, 2)
            self.assertEqual(run("--extras", "2", "--walk", "6").returncode, 2)


if __name__ == "__main__":
    unittest.main()
