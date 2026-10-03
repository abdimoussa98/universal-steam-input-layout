"""The disk-backed engine (tools/stack_search/stack_search_disk.cpp) and the query store (StackDB)."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from steam_layout.held_model import HeldModel, explore
from steam_layout.model import Layout
from steam_layout.stackdb import StackDB, Value, build_engine
from steam_layout.stacks import definer
from test_held_model import guarded_layout, pad_layout

ROOT = Path(__file__).resolve().parents[1]


def neptune(variant="default"):
    return Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))


def expected_value(layout, stack, j):
    """What the layout JSON says input j does in `stack` (the reference for stored profiles)."""
    for title in reversed(stack):
        group = layout.active(title).get(j[0])
        if group is None:
            continue
        if group["mode"] == "disabled":
            return Value(blocked_by=title)
        found = definer(layout, [title], *j)
        if found:
            return Value(owner=title)
    return Value()


@unittest.skipUnless(shutil.which("clang++"), "needs clang++")
class DiskEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.disk = build_engine("stack_search_disk")
        cls.memory = build_engine()

    def run_engine(self, engine, layout, *args, outdir=None):
        tmp = outdir or tempfile.mkdtemp()
        if outdir is None:
            self.addCleanup(shutil.rmtree, tmp)
        HeldModel(layout, missed="--missed" in args).write_held(Path(tmp, "model.txt"))
        extra = ["--held"] if engine == self.memory else []
        out = subprocess.run([str(engine), str(Path(tmp, "model.txt")), tmp, *extra, "--threads", "4", *args],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr + out.stdout)
        db = StackDB(tmp, layout)
        self.addCleanup(db.close)
        return db, tmp, out.stdout

    def reference(self, layout, depth=None, missed=False):
        model = HeldModel(layout, missed=missed)
        return {(model.names_of(s), frozenset(model.controls[c] for c in h), m) for s, h, m in explore(model, depth)}

    def test_small_layouts_match_the_reference_to_completion(self):
        for build in (guarded_layout, pad_layout):
            for args in ((), ("--missed",)):
                with self.subTest(layout=build.__name__, args=args):
                    layout = Layout(build())
                    db, _, _ = self.run_engine(self.disk, layout, *args)
                    self.assertTrue(db.complete)
                    self.assertEqual(db.summary["format"], "levels")
                    self.assertEqual(set(db.all_states()), self.reference(layout, missed=bool(args)))

    def test_real_layouts_match_the_in_memory_engine(self):
        for variant in ("default", "alternative"):
            with self.subTest(variant=variant):
                layout = neptune(variant)
                disk, _, _ = self.run_engine(self.disk, layout, "--max-depth", "4")
                memory, _, _ = self.run_engine(self.memory, layout, "--max-depth", "4")
                self.assertEqual(set(disk.all_states()), set(memory.all_states()))
                self.assertEqual(disk.summary["exact_depth"], 4)
                self.assertEqual({r["stack"]: (r["depth"], r["clean"], r["count"], r["idle"]) for r in disk.distinct_stacks()},
                                 {r["stack"]: (r["depth"], r["clean"], r["count"], r["idle"]) for r in memory.distinct_stacks()})

    def test_a_small_memory_budget_splits_into_groups_with_the_same_result(self):
        layout = neptune()
        whole, _, _ = self.run_engine(self.disk, layout, "--max-depth", "5")
        split, _, log = self.run_engine(self.disk, layout, "--max-depth", "5", "--memory", "0.003")
        self.assertRegex(log, r"level 5 done: .* \d+ groups")
        self.assertEqual(set(split.all_states()), set(whole.all_states()))

    def test_resume_continues_to_the_same_result(self):
        layout = neptune()
        fresh, _, _ = self.run_engine(self.disk, layout, "--max-depth", "5")
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        self.run_engine(self.disk, layout, "--max-depth", "3", outdir=tmp)
        resumed, _, log = self.run_engine(self.disk, layout, "--max-depth", "5", "--resume", outdir=tmp)
        self.assertIn("resumed", log)
        self.assertEqual(set(resumed.all_states()), set(fresh.all_states()))
        self.assertEqual(resumed.summary["level_starts"], fresh.summary["level_starts"])

    def test_every_state_traces_back_to_base(self):
        layout = Layout(pad_layout())
        db, _, _ = self.run_engine(self.disk, layout)
        model = HeldModel(layout)
        for gid in range(db.summary["states"]):
            path = db.witness(gid)
            self.assertEqual(path[0], ("start", ("Base",)))
            self.assertEqual(path[-1][1], db.stack(gid))
            self.assertEqual(len(path) - 1, next(d for d, s in enumerate(db.starts) if s > gid) - 1)
        self.assertTrue(model)


@unittest.skipUnless(shutil.which("clang++"), "needs clang++")
class QueryStoreTests(unittest.TestCase):
    """Every stored stack knows what each input does; SQL answers match the layout JSON."""

    @classmethod
    def setUpClass(cls):
        cls.layout = neptune()
        cls.dirs = {}
        for name in ("stack_search_disk", "stack_search"):
            tmp = tempfile.mkdtemp()
            HeldModel(cls.layout).write_held(Path(tmp, "model.txt"))
            extra = ["--held"] if name == "stack_search" else []
            subprocess.run([str(build_engine(name)), str(Path(tmp, "model.txt")), tmp, *extra, "--threads", "4",
                            "--max-depth", "5"], check=True, capture_output=True)
            cls.dirs[name] = tmp

    @classmethod
    def tearDownClass(cls):
        for tmp in cls.dirs.values():
            shutil.rmtree(tmp)

    def db(self, name="stack_search_disk"):
        db = StackDB(self.dirs[name], self.layout)
        self.addCleanup(db.close)
        return db

    def test_profiles_match_the_layout_for_every_stack_and_below_its_top(self):
        for name in self.dirs:
            db = self.db(name)
            with self.subTest(engine=name):
                for row in db.distinct_stacks():
                    whole, below = db.profile_values(row["profile"]), db.profile_values(row["below"])
                    for j in db.inputs:
                        self.assertEqual(whole[j], expected_value(self.layout, row["stack"], j), (row["stack"], j))
                        self.assertEqual(below[j], expected_value(self.layout, row["stack"][:-1], j), (row["stack"], j))

    def test_values_and_moment(self):
        db = self.db()
        row = max(db.distinct_stacks(), key=lambda r: len(r["stack"]))
        values = db.values(row["stack"])
        for j in db.inputs:
            self.assertEqual(values[j], expected_value(self.layout, row["stack"], j))
            if values[j].owner:
                self.assertEqual(values[j].activators, self.layout.active(values[j].owner)[j[0]]["inputs"][j[1]]["activators"])
        moment = db.moment(row["witness"])
        self.assertEqual(moment["stack"], row["stack"])
        self.assertEqual(moment["witness"][-1][1], row["stack"])
        self.assertEqual(moment["values"], values)
        unseen = ("Base", "L1: Double Tap", "R1: Double Tap")
        self.assertEqual(db.values(unseen), {j: expected_value(self.layout, unseen, j) for j in db.inputs})

    def test_inherited_values_and_inheritance_match_brute_force(self):
        db = self.db()
        db.build_sqlite()
        window = "L1: Double Tap"
        stacks = [s for s in db.distinct_stack_names() if s[-1] == window]
        self.assertTrue(stacks)
        for j in (("switch", "left_bumper"), ("switch", "button_menu"), ("left_trigger", "edge")):
            got = db.inherited_values(window, *j)
            expected = {}
            for stack in stacks:
                found = definer(self.layout, stack[:-1], *j)
                expected.setdefault(found[0] if found else None, set()).add(stack)
            self.assertEqual({k: set(v["stacks"]) for k, v in got.items()}, expected)
        table = db.inheritance(window)
        for j in db.inputs:
            counts = {}
            for stack in stacks:
                v = expected_value(self.layout, stack[:-1], j)
                counts[v] = counts.get(v, 0) + 1
            self.assertEqual(table[j], counts, j)

    def test_sql_views_list_every_input_with_its_binding_summary(self):
        db = self.db()
        db.build_sqlite()
        row = next(r for r in db.distinct_stacks() if len(r["stack"]) >= 3)
        rows = db.sql("SELECT source, name, owner, blocked_by, summary FROM stack_values WHERE stack = ?", (row["id"],))
        self.assertEqual(len(rows), len(db.inputs))
        values = db.values(row["stack"])
        for source, name, owner, blocked_by, summary in rows:
            self.assertEqual(Value(owner, blocked_by), values[(source, name)])
            self.assertEqual(summary is not None, owner is not None)
        below = db.sql("SELECT source, name, owner FROM inherited WHERE stack = ?", (row["id"],))
        self.assertEqual({(s, n): o for s, n, o in below},
                         {j: v.owner for j, v in db.values(row["stack"], below=True).items()})


if __name__ == "__main__":
    unittest.main()
