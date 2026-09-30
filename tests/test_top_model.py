"""The top-K model (steam_layout.held_model.TopModel): the "possible" bound, exact about buttons."""
import json
from pathlib import Path
import unittest

from steam_layout.held_model import HeldModel, TopModel, explore
from steam_layout.model import Layout
from test_held_model import guarded_layout, pad_layout

ROOT = Path(__file__).resolve().parents[1]


def neptune(variant="default"):
    return Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))


class TopModelTests(unittest.TestCase):
    def test_with_k_above_the_tallest_stack_it_is_the_exact_model(self):
        for build in (guarded_layout, pad_layout):
            with self.subTest(layout=build.__name__):
                layout = Layout(build())
                exact = {((0,) + s[1:], h, m) for s, h, m in explore(HeldModel(layout))}
                top = {((0,) + a[1], h, m) for (a, h, m) in explore(TopModel(layout, k=20)) if a[0] == frozenset({0})}
                self.assertEqual(top, exact)
                self.assertTrue(all(a[0] == frozenset({0}) for a, _, _ in explore(TopModel(layout, k=20))))

    def test_every_real_state_is_covered_within_the_same_number_of_events(self):
        # the soundness property the "possible" answers rest on
        layout = neptune()
        real = explore(HeldModel(layout), 4)
        for k in (1, 2, 3):
            model = TopModel(layout, k)
            reached = explore(model, 4)
            index = {}
            for (a, h, m), d in reached.items():
                index.setdefault((h, m, a[1]), []).append((a, d))
            with self.subTest(k=k):
                for (stack, h, m), depth in real.items():
                    ok = any(model.covers(a, stack) and d <= depth
                             for n in range(0, k + 1) if len(stack) - n >= 1
                             for a, d in index.get((h, m, tuple(stack[len(stack) - n:])), []))
                    self.assertTrue(ok, (model.names_of((frozenset(stack), ())), h, m))

    def test_an_input_falling_into_the_deep_part_can_come_from_any_deep_binder(self):
        # Base: A adds Mod, B adds Other. With k=1 and both below the top, X's input
        # lookup falls into the deep set, so both deep binders are possible owners.
        from test_audit_inheritance import act, add, build
        layout = Layout(build({
            "Base": {"button_diamond": ("four_buttons", {"button_a": act(add("Mod")), "button_b": act(add("Other")),
                                                         "button_x": act(add("Top"))})},
            "Mod": {"button_diamond": ("four_buttons", {"button_y": act("key_press M, , ")})},
            "Other": {"button_diamond": ("four_buttons", {"button_y": act("key_press O, , ")})},
            "Top": {}}))
        model = TopModel(layout, k=1)
        y = model.cid[("button_diamond", "button_y")]
        idx = model.index
        state = (frozenset({0, idx["Mod"], idx["Other"]}), (idx["Top"],))
        owners = {found[0] for found in model._owners(state, y)}
        self.assertEqual(owners, {idx["Mod"], idx["Other"]})
        base_only = (frozenset({0}), (idx["Top"],))
        self.assertEqual({found[0] for found in model._owners(base_only, model.cid[("button_diamond", "button_a")])}, {0})


if __name__ == "__main__":
    unittest.main()


import shutil
import subprocess
import tempfile

from steam_layout.stackdb import StackDB, build_engine


@unittest.skipUnless(shutil.which("clang++"), "needs clang++")
class TopEngineTests(unittest.TestCase):
    """stack_search --held --top K agrees exactly with TopModel."""

    def run_top(self, layout, k, *args):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        TopModel(layout, k).write_held(Path(tmp, "model.txt"))
        out = subprocess.run([str(build_engine()), str(Path(tmp, "model.txt")), tmp, "--held", "--top", str(k),
                              "--threads", "4", *args], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        db = StackDB(tmp, layout)
        self.addCleanup(db.close)
        return db

    def expected(self, layout, k, depth=None):
        model = TopModel(layout, k)
        return {((frozenset(model.layer_names[i] for i in a[0]), tuple(model.layer_names[i] for i in a[1])),
                 frozenset(model.controls[c] for c in h), m) for a, h, m in explore(model, depth)}

    def test_small_layouts_to_completion(self):
        for build in (guarded_layout, pad_layout):
            for k in (1, 2):
                with self.subTest(layout=build.__name__, k=k):
                    layout = Layout(build())
                    db = self.run_top(layout, k)
                    self.assertTrue(db.complete)
                    self.assertEqual(set(db.all_states()), self.expected(layout, k))

    def test_real_layout_for_3_events(self):
        for k in (1, 3):
            with self.subTest(k=k):
                layout = neptune()
                db = self.run_top(layout, k, "--max-depth", "3")
                self.assertEqual(set(db.all_states()), self.expected(layout, k, 3))
