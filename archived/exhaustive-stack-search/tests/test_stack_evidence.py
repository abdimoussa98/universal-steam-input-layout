"""Only matching concrete held searches supply lower-bound evidence."""
import bisect
import copy
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from steam_layout.held_model import HeldModel, explore
from steam_layout.model import Layout
from steam_layout.stack_evidence import Evidence, EvidenceError
from steam_layout.stackdb import LEVEL_META, StackDB, Value, build_engine
from test_audit_inheritance import EMPTY, act, add, build


def layout():
    return Layout(build({
        "Base": {
            "switch": ("switches", {"left_bumper": act(add("Lower")), "right_bumper": act(add("X"))}),
            "joystick": ("dpad", {"dpad_north": act("key_press W, , ")}),
            "left_trackpad": ("dpad", {"click": act("key_press L, , ")}),
        },
        "Lower": {"joystick": ("disabled", {})},
        "X": {
            "switch": ("switches", {"left_bumper": act(EMPTY), "right_bumper": act(add("Above"))}),
            "left_trackpad": ("disabled", {}),
        },
        "Above": {"right_trackpad": ("dpad", {"touch": act("key_press R, , ")})},
    }))


class NoDatabaseTests(unittest.TestCase):
    def test_start_only_and_no_claimed_facts_without_a_search(self):
        model = HeldModel(layout())
        evidence = Evidence(model)
        self.assertEqual(list(evidence.seed_states()), [model.start()])
        facts = evidence.facts("X")
        self.assertEqual(facts["below"], {})
        self.assertEqual(facts["above"], {})
        self.assertTrue(all(not values for values in facts["inherited"].values()))
        self.assertNotIn(("switch", "left_bumper"), facts["inherited"])
        self.assertNotIn(("left_trackpad", "click"), facts["inherited"])
        with self.assertRaisesRegex(ValueError, "unknown layer"):
            evidence.facts("Missing")
        with self.assertRaisesRegex(EvidenceError, "No search database"):
            evidence.witness(0)


@unittest.skipUnless(shutil.which("clang++"), "needs clang++")
class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = layout()
        cls.model = HeldModel(cls.layout)
        cls.outputs = {}
        for name in ("stack_search", "stack_search_disk"):
            directory = tempfile.mkdtemp(prefix="test-stack-evidence-")
            cls.outputs[name] = directory
            cls.model.write_held(Path(directory, "model.txt"))
            flags = ["--held"] if name == "stack_search" else []
            subprocess.run([str(build_engine(name)), str(Path(directory, "model.txt")), directory,
                            *flags, "--threads", "2"], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        for directory in cls.outputs.values():
            shutil.rmtree(directory)

    def db(self, engine="stack_search", directory=None):
        db = StackDB(directory or self.outputs[engine], self.layout)
        self.addCleanup(db.close)
        return db

    def copy_output(self, engine="stack_search"):
        temporary = tempfile.TemporaryDirectory(prefix="test-stack-evidence-copy-")
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name, "search")
        shutil.copytree(self.outputs[engine], directory)
        return directory

    def test_facts_cover_middle_layers_and_distinguish_blocked_from_unbound(self):
        for engine in self.outputs:
            with self.subTest(engine=engine):
                db = self.db(engine)
                evidence = Evidence(self.model, db)
                facts = evidence.facts("X")
                self.assertEqual(set(facts["below"]), {"Base", "Lower"})
                self.assertEqual(set(facts["above"]), {"Above"})
                self.assertEqual(set(facts["inherited"][("joystick", "dpad_north")]),
                                 {Value(owner="Base"), Value(blocked_by="Lower")})
                self.assertEqual(set(facts["inherited"][("right_trackpad", "touch")]), {Value()})
                self.assertNotIn(("switch", "left_bumper"), facts["inherited"])
                self.assertNotIn(("left_trackpad", "click"), facts["inherited"])
                base = evidence.facts("Base")
                self.assertEqual(base["below"], {})
                self.assertEqual(set(base["above"]), {"Lower", "X", "Above"})
                self.assertEqual(set(base["inherited"][("right_trackpad", "touch")]), {Value()})
                for other, gid in facts["below"].items():
                    stack = db.stack(gid)
                    self.assertLess(stack.index(other), stack.index("X"))
                for other, gid in facts["above"].items():
                    trace = evidence.witness(gid)
                    self.assertLess(trace[-1][1].index("X"), trace[-1][1].index(other))
                self.assertFalse((db.dir / "stacks.sqlite").exists())

    def test_each_title_scans_once_and_returns_binding_details(self):
        db = self.db()
        evidence = Evidence(self.model, db)
        with patch.object(db, "distinct_stacks", wraps=db.distinct_stacks) as scan:
            first = evidence.facts("X")
            self.assertIs(evidence.facts("X"), first)
            self.assertEqual(scan.call_count, 1)
        owner = next(v for v in first["inherited"][("joystick", "dpad_north")] if v.owner)
        self.assertEqual(owner.activators,
                         self.layout.active("Base")["joystick"]["inputs"]["dpad_north"]["activators"])

    def test_seed_states_are_numeric_reachable_and_limit_does_not_limit_facts(self):
        expected = set(explore(self.model))
        for engine in self.outputs:
            with self.subTest(engine=engine):
                evidence = Evidence(self.model, self.db(engine))
                states = list(evidence.seed_states())
                self.assertEqual(states[0], self.model.start())
                self.assertEqual(len(states), len(set(states)))
                self.assertTrue(set(states) <= expected)
                self.assertGreater(len(states), 1)
                self.assertEqual(list(evidence.seed_states(limit=0)), [self.model.start()])
                self.assertLessEqual(len(list(evidence.seed_states(limit=1))), 2)
                self.assertEqual(set(evidence.facts("X")["above"]), {"Above"})

    def test_rejects_wrong_search_kinds_and_stale_model(self):
        for attribute, value, message in (("held", False, "--held"), ("top", 1, "Top-K")):
            db = self.db()
            setattr(db, attribute, value)
            with self.subTest(attribute=attribute), self.assertRaisesRegex(EvidenceError, message):
                Evidence(self.model, db)
        db = self.db()
        db.summary = {**db.summary, "missed": True}
        with self.assertRaisesRegex(EvidenceError, "missed"):
            Evidence(self.model, db)
        changed = copy.deepcopy(self.layout.cm)
        base_switch = next(g for g in changed["group"] if "left_bumper" in g.get("inputs", {}))
        base_switch["inputs"]["left_bumper"]["activators"] = act(add("Above"))
        model = HeldModel(Layout({"controller_mappings": changed}))
        with self.assertRaisesRegex(EvidenceError, "Stale or mismatched"):
            Evidence(model, self.db())

    def test_rejects_missing_or_truncated_state_artifacts(self):
        for engine, artifact in (("stack_search", "shard_0.meta"),
                                 ("stack_search_disk", "levels/level_000.rec")):
            directory = self.copy_output(engine)
            db = self.db(engine, directory)
            Path(directory, artifact).unlink()
            with self.subTest(engine=engine), self.assertRaisesRegex(EvidenceError, "Missing.*artifact"):
                Evidence(self.model, db)
        directory = self.copy_output("stack_search_disk")
        Path(directory, "levels/level_000.meta").write_bytes(b"truncated")
        with self.assertRaisesRegex(EvidenceError, "Truncated"):
            Evidence(self.model, self.db("stack_search_disk", directory))

    def test_reads_every_stack_even_if_not_in_the_indexes(self):
        db = self.db()
        db._under, db._top, db._below = {}, {}, {}
        evidence = Evidence(self.model, db)
        self.assertEqual(list(evidence.seed_states()), [self.model.start()])
        self.assertEqual(set(evidence.facts("X")["above"]), {"Above"})

    def test_rejects_a_fact_whose_witness_ends_at_a_different_stack(self):
        original = self.db("stack_search_disk")
        gid = Evidence(self.model, original).facts("X")["above"]["Above"]
        directory = self.copy_output("stack_search_disk")
        path = directory / "stacks.tsv"
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            columns = line.split("\t")
            if int(columns[2]) == gid:
                columns[2] = "0"  # The disk engine's root state has only Base.
                lines[index] = "\t".join(columns)
        path.write_text("\n".join(lines) + "\n")
        evidence = Evidence(self.model, self.db("stack_search_disk", directory))
        with self.assertRaisesRegex(EvidenceError, "different stack"):
            evidence.facts("X")

    def test_rejects_invalid_event_in_the_ancestry_of_a_fact_witness(self):
        original = self.db("stack_search_disk")
        gid = Evidence(self.model, original).facts("X")["above"]["Above"]
        _, _, parent, _ = original._locate(gid)
        self.assertNotEqual(parent, 0)  # Corrupt an ancestor, not only the final transition.
        level = bisect.bisect_right(original.starts, parent) - 1
        local = parent - original.starts[level]
        directory = self.copy_output("stack_search_disk")
        path = directory / f"levels/level_{level:03d}.meta"
        data = bytearray(path.read_bytes())
        grandparent, offset, _ = LEVEL_META.unpack_from(data, local * LEVEL_META.size)
        invalid_event = (len(self.model.controls) + 2) * 16 + 15
        LEVEL_META.pack_into(data, local * LEVEL_META.size, grandparent, offset, invalid_event)
        path.write_bytes(data)
        evidence = Evidence(self.model, self.db("stack_search_disk", directory))
        # Candidate observations remain guesses; facts and explicit witnesses require replay.
        self.assertTrue(list(evidence.seed_states()))
        with self.assertRaisesRegex(EvidenceError, "replay failed"):
            evidence.facts("X")
        with self.assertRaisesRegex(EvidenceError, "replay failed"):
            evidence.witness(gid)

    def test_witness_replay_reuses_verified_prefixes(self):
        db = self.db("stack_search_disk")
        evidence = Evidence(self.model, db)
        with patch.object(self.model, "successors", wraps=self.model.successors) as successors:
            facts = evidence.facts("X")
            self.assertGreater(successors.call_count, 0)
            calls = successors.call_count
            for gid in facts["below"].values():
                evidence.witness(gid)
            for gid in facts["above"].values():
                evidence.witness(gid)
            for values in facts["inherited"].values():
                for gid in values.values():
                    evidence.witness(gid)
            self.assertEqual(successors.call_count, calls)

    def test_matching_export_does_not_bypass_current_transition_semantics(self):
        evidence = Evidence(self.model, self.db())
        # Simulate a semantics-only implementation change: serialization still matches.
        with patch.object(self.model, "successors", return_value=set()):
            with self.assertRaisesRegex(EvidenceError, "replay failed"):
                evidence.facts("X")


if __name__ == "__main__":
    unittest.main()
