"""The compiled stack-search engine (tools/stack_search) and its index reader (steam_layout.stackdb)."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from steam_layout.held_model import HeldModel, explore
from steam_layout.model import Layout
from steam_layout.search_model import SearchModel
from steam_layout.stackdb import StackDB, build_engine
from steam_layout.stacks import StackSpace, definer
from test_search_model import synthetic

ROOT = Path(__file__).resolve().parents[1]


def python_indexes(model, stacks):
    """The facts the engine's indexes must contain, computed directly from stacks (names)."""
    layout = model.layout
    under, top, below_top = set(), set(), set()
    for stack in stacks:
        for i, x in enumerate(stack):
            for y in stack[1:i]:
                under.add((y, x))
        for j in model.inputs:
            owner = _top(model, stack, j)
            top.add((j, owner, None))
            for y in stack[1:]:
                if y != owner:
                    top.add((j, owner, y))
            for p in range(1, len(stack)):
                below_top.add((stack[p], j, _top(model, stack[:p], j)))
    return under, top, below_top


def _top(model, stack, j):
    """Topmost layer binding or blocking input j (None if none)."""
    jid = model.input_index[j]
    for title in reversed(stack):
        lid = model.index[title]
        if jid in model.blocks.get(lid, set()) or jid in model.binds.get(lid, set()):
            return title
    return None


@unittest.skipUnless(shutil.which("clang++"), "needs clang++")
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = build_engine()

    def run_engine(self, layout, *args):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        model = SearchModel(layout)
        model.write(Path(tmp, "model.txt"))
        out = subprocess.run([str(self.engine), str(Path(tmp, "model.txt")), tmp, "--threads", "4", "--dump", *args],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        return model, StackDB(tmp, layout), tmp

    def test_small_layout_matches_the_python_search_to_completion(self):
        layout = Layout(synthetic())
        model, db, _ = self.run_engine(layout)
        expected = set(StackSpace(layout, depth=20).stacks)
        self.assertTrue(db.complete)
        self.assertEqual(set(db.all_stacks()), expected)

    def test_real_layout_matches_the_python_search_for_4_events(self):
        for variant in ("default", "alternative"):
            layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
            with self.subTest(variant=variant):
                model, db, _ = self.run_engine(layout, "--max-depth", "4")
                self.assertEqual(set(db.all_stacks()), set(StackSpace(layout, depth=4).stacks))

    def test_indexes_match_the_stacks_and_every_witness_proves_its_fact(self):
        layout = Layout(synthetic())
        model, db, _ = self.run_engine(layout)
        under, top, below_top = python_indexes(model, db.all_stacks())
        self.assertEqual(db.under_pairs(), under)
        self.assertEqual(db.top_facts(), top)
        self.assertEqual(db.below_top_facts(), below_top)
        for (y, x), gid in db.under_witnesses().items():
            stack = db.stack(gid)
            self.assertLess(stack.index(y), stack.index(x))

    def test_queries_and_button_sequences(self):
        layout = Layout(synthetic())
        model, db, _ = self.run_engine(layout)
        self.assertEqual(db.under("Win"), {"H"})
        self.assertNotIn("R", db.under("Win"))  # L's release never fires with R (and M) present
        self.assertIn(("Base", model.layout.active("Base")["switch"]["inputs"]["right_bumper"]["activators"]),
                      db.inherited("Win", "switch", "right_bumper"))
        self.assertEqual(db.present_when("L", "switch", "left_bumper") - {"L"}, {"H"})
        path = db.witness(db.under_witnesses()[("H", "Win")])
        self.assertEqual(path[0], ("start", ("Base",)))
        self.assertEqual(path[-1][1][-1], "Win")


@unittest.skipUnless(shutil.which("clang++"), "needs clang++")
class HeldEngineTests(unittest.TestCase):
    """--held: the engine agrees exactly with steam_layout.held_model."""

    @classmethod
    def setUpClass(cls):
        cls.engine = build_engine()

    def run_held(self, layout, *args):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        model = HeldModel(layout, missed="--missed" in args)
        model.write_held(Path(tmp, "model.txt"))
        out = subprocess.run([str(self.engine), str(Path(tmp, "model.txt")), tmp, "--held", "--threads", "4", *args],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        return model, StackDB(tmp, layout)

    def expected(self, model, depth=None):
        return {(model.names_of(s), frozenset(model.controls[c] for c in h), m)
                for s, h, m in explore(model, depth)}

    def test_small_layout_matches_the_reference_to_completion(self):
        from test_held_model import guarded_layout
        model, db = self.run_held(Layout(guarded_layout()))
        self.assertTrue(db.complete)
        self.assertEqual(set(db.all_states()), self.expected(model))

    def test_pad_touch_tracking_and_hold_layer_release_match_the_reference(self):
        from test_held_model import pad_layout
        model, db = self.run_held(Layout(pad_layout()))
        self.assertTrue(db.complete)
        self.assertEqual(set(db.all_states()), self.expected(model))
        self.assertNotIn("Clicked", db.idle())  # nothing held: the hold layer is gone

    def test_missed_releases_only_with_the_flag(self):
        from test_held_model import guarded_layout
        for args in ((), ("--missed",)):
            with self.subTest(args=args):
                model, db = self.run_held(Layout(guarded_layout()), *args)
                states = set(db.all_states())
                self.assertEqual(states, self.expected(model))
                self.assertEqual(any(m for _, _, m in states), bool(args))
                self.assertEqual(db.summary["missed"], bool(args))

    def test_real_layout_matches_the_reference_for_3_events(self):
        for variant in ("default", "alternative"):
            layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
            with self.subTest(variant=variant):
                model, db = self.run_held(layout, "--max-depth", "3")
                self.assertEqual(set(db.all_states()), self.expected(model, 3))

    def test_idle_index_lists_what_can_remain_with_nothing_held(self):
        from test_held_model import guarded_layout
        model, db = self.run_held(Layout(guarded_layout()), "--missed")
        states = self.expected(model)
        clean = {y for stack, held, missed in states if not held and not missed for y in stack[1:]}
        after_missed = {y for stack, held, missed in states if not held and missed for y in stack[1:]}
        self.assertEqual(db.idle(missed=False), clean)
        self.assertEqual(db.idle(missed=True), after_missed)
        self.assertIn("Mod", db.idle(missed=True))  # a missed LB release leaves Mod behind
        gid = db.idle_witnesses(missed=True)["Mod"]
        labels = [label for label, _ in db.witness(gid)]
        self.assertTrue(any("missed" in label for label in labels), labels)


@unittest.skipUnless(shutil.which("clang++"), "needs clang++")
class StoreTests(unittest.TestCase):
    """Safe stopping, the distinct-stack store, and the robust inheritance query."""

    @classmethod
    def setUpClass(cls):
        cls.engine = build_engine()

    def run_held(self, layout, *args):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        HeldModel(layout).write_held(Path(tmp, "model.txt"))
        out = subprocess.run([str(self.engine), str(Path(tmp, "model.txt")), tmp, "--held", "--threads", "4", *args],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        return StackDB(tmp, layout), tmp

    def test_memory_limit_stops_cleanly_and_still_writes_everything(self):
        layout = Layout(json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text()))
        db, _ = self.run_held(layout, "--memory-limit", "0.005")
        self.assertFalse(db.complete)
        self.assertEqual(db.summary["stopped"], "memory limit")
        exact = db.summary["exact_depth"]
        self.assertGreaterEqual(exact, 1)
        expected = {model_stack for model_stack in _stacks_within(layout, exact)}
        self.assertLessEqual(expected, set(db.all_stacks()))

    def test_distinct_stacks_file_has_every_stack_with_depth_witness_and_clean_flag(self):
        from test_held_model import guarded_layout
        layout = Layout(guarded_layout())
        db, _ = self.run_held(layout)
        states = list(db.all_states())
        rows = {row["stack"]: row for row in db.distinct_stacks()}
        self.assertEqual(set(rows), {s for s, _, _ in states})
        for stack, row in rows.items():
            self.assertEqual(row["clean"], any(s == stack and not m for s, _, m in states))
            self.assertEqual(db.stack(row["witness"]), stack)
            self.assertEqual(row["top"], stack[-1])

    def test_inheritance_query_reads_the_layout_for_every_stack_with_the_layer_on_top(self):
        for variant in ("default", "alternative"):
            layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
            with self.subTest(variant=variant):
                db, _ = self.run_held(layout, "--max-depth", "6")
                db.build_sqlite()
                window = next(t for t in layout.presets if "Double Tap" in t and "Cover" not in t)
                j = ("switch", "left_bumper")
                got = db.inherited_values(window, *j)
                expected = {}
                for stack in db.distinct_stack_names():
                    if stack[-1] != window:
                        continue
                    found = definer(layout, stack[:-1], *j)
                    expected.setdefault(found[0] if found else None, set()).add(stack)
                self.assertEqual({k: set(v["stacks"]) for k, v in got.items()}, expected)
                for owner, info in got.items():
                    if owner:
                        self.assertEqual(info["activators"],
                                         layout.active(owner)[j[0]]["inputs"][j[1]]["activators"])


def _stacks_within(layout, depth):
    model = HeldModel(layout)
    return {model.names_of(s) for s, _, _ in explore(model, depth)}


if __name__ == "__main__":
    unittest.main()
