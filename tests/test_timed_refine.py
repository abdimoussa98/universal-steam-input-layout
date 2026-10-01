"""Refinement uses checked facts, preserves scope, and never publishes guesses."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from steam_layout.model import Layout
from steam_layout.timed_discover import save_witnesses
from steam_layout.timed_facts import FactCatalogue, FactWitnesses
from steam_layout.timed_model import TimedModel
from steam_layout.timed_predicates import FactExclusion, RequiresBelowAny, RequiresBetweenAny
from test_audit_inheritance import act, add, build

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    from steam_layout.timed_audit import load_certificate, save_certificate
    from steam_layout.timed_proof import TimedProof
    from steam_layout.timed_refine import (CHECKPOINT_FORMAT, facts_for_layers,
                                          load_family_hypotheses, main, propose_exclusions)


ROOT = Path(__file__).resolve().parents[1]
LB = ["switch", "left_bumper"]


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedRefineTests(unittest.TestCase):
    def make(self, layers, events=()):
        data = build(layers)
        model = TimedModel(Layout(data))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        if events:
            witnesses.add_trace(events)
        # A valid but deliberately weak certificate leaves useful work for
        # exact fact hypotheses, independent of primitive candidate seeding.
        baseline = TimedProof(model, timeout_ms=3000)
        baseline.invariants, baseline.finished = (), True
        baseline.validate()
        return data, model, catalogue, witnesses, baseline

    def fixture(self, *, witness_live=True):
        return self.make({"Base": {"switch": ("switches", {
            "left_bumper": act(add("Live")), "right_bumper": act("key_press R, , ")})},
            "Live": {}, "Dead": {}}, [{"press": LB}] if witness_live else ())

    def write_inputs(self, folder, fixture):
        data, _, _, witnesses, baseline = fixture
        layout, archive, certificate = (folder / name for name in ("layout.json", "witness.sqlite", "base.json"))
        layout.write_text(json.dumps(data))
        save_witnesses(witnesses, archive)
        save_certificate(baseline, certificate)
        return [str(layout), str(archive), str(certificate), str(folder / "refined.json"), str(folder / "report.json")]

    def run_main(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_equivalent_raw_inputs_share_a_candidate_and_witnesses_are_never_negated(self):
        _, _, catalogue, witnesses, baseline = self.fixture()
        candidates, classification = propose_exclusions(baseline, catalogue, witnesses)
        inherited_dead = [candidate.fact for candidate in candidates
                          if candidate.fact.kind == "inherit" and candidate.fact.x == 2 and candidate.fact.y == 0]
        unresolved_dead = [fact for fact in classification["possible"]
                           if fact.kind == "inherit" and fact.x == 2 and fact.y == 0]
        self.assertEqual(len(unresolved_dead), 2)
        self.assertEqual(len(inherited_dead), 1)
        self.assertTrue(candidates)
        self.assertTrue(all(candidate.fact not in witnesses.facts for candidate in candidates))
        self.assertTrue(all(not candidate.fact.holds(state.stack) for candidate in candidates
                            for state in witnesses.node_states.values()))

    def test_different_definer_sets_do_not_merge(self):
        _, _, catalogue, witnesses, baseline = self.make({
            "Base": {"switch": ("switches", {
                "left_bumper": act("key_press L, , "), "right_bumper": act("key_press R, , ")})},
            "Override": {"switch": ("switches", {"left_bumper": act("key_press A, , ")})},
            "X": {}})
        candidates, _ = propose_exclusions(baseline, catalogue, witnesses, layers=["X"])
        inherited = [candidate.fact for candidate in candidates
                     if candidate.fact.kind == "inherit" and candidate.fact.x == 2 and candidate.fact.y == 0]
        self.assertEqual(len(inherited), 2)
        self.assertEqual({fact.definers for fact in inherited}, {(0,), (0, 1)})

    def test_layer_selection_includes_above_facts_and_rejects_invalid_selections(self):
        _, _, catalogue, witnesses, baseline = self.make({"Base": {}, "A": {}, "B": {}})
        candidates, _ = propose_exclusions(baseline, catalogue, witnesses, layers=["A"])
        pairs = {(candidate.fact.x, candidate.fact.y) for candidate in candidates}
        self.assertIn((1, 2), pairs)
        self.assertIn((2, 1), pairs)
        self.assertNotIn((2, 0), pairs)
        for layers in ([], ["A", "A"], ["Missing"]):
            with self.subTest(layers=layers), self.assertRaises(ValueError):
                facts_for_layers(catalogue, layers)

    def test_cli_reclassifies_refines_and_saves_a_loadable_complete_certificate(self):
        fixture = self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            args = self.write_inputs(folder, fixture)
            checkpoint = folder / "checkpoint.json"
            result = subprocess.run([sys.executable, "-m", "steam_layout.timed_refine", *args,
                                     "--timeout-ms", "3000", "--refine-timeout-ms", "1000",
                                     "--checkpoint", str(checkpoint)],
                                    cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            report = json.loads(Path(args[4]).read_text())
            self.assertTrue(output["complete_for_model"])
            self.assertTrue(output["global_complete_for_model"])
            self.assertTrue(output["selected_complete_for_model"])
            self.assertTrue(report["complete_for_model"])
            self.assertEqual(report["counts"]["possible"], 0)
            self.assertGreater(report["refinement"]["baseline_counts"]["possible"], 0)
            self.assertGreater(report["counts"]["proven"], 0)
            self.assertEqual(len(report["layers"]), 3)
            loaded = load_certificate(fixture[1], args[3], timeout_ms=3000)
            self.assertTrue(any(isinstance(predicate, FactExclusion) for predicate in loaded.invariants))
            saved = json.loads(checkpoint.read_text())
            self.assertEqual(saved["format"], CHECKPOINT_FORMAT)
            self.assertFalse(saved["verified"])
            self.assertEqual(saved["stage"], "fixed_point_unvalidated")
            with self.assertRaisesRegex(ValueError, "format"):
                load_certificate(fixture[1], checkpoint)

    def test_selected_completion_does_not_claim_the_full_catalogue_is_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.write_inputs(Path(folder), self.fixture(witness_live=False))
            code, stdout, stderr = self.run_main([*args, "--layer", "Dead", "--timeout-ms", "3000"])
            self.assertEqual(code, 0, stderr)
            output = json.loads(stdout)
            report = json.loads(Path(args[4]).read_text())
            self.assertTrue(output["selected_complete_for_model"])
            self.assertFalse(output["complete_for_model"])
            self.assertFalse(output["global_complete_for_model"])
            self.assertGreater(output["counts"]["possible"], 0)
            self.assertEqual(report["refinement"]["selected_layers"], ["Dead"])
            self.assertEqual({row["layer"] for row in report["layers"]}, {"Base", "Live", "Dead"})

    def test_unvalidated_checkpoint_survives_failed_final_validation_without_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            args = self.write_inputs(folder, self.fixture())
            checkpoint = folder / "checkpoint.json"
            with patch("steam_layout.timed_refine.save_certificate", side_effect=ValueError("validation unknown")):
                code, stdout, stderr = self.run_main([*args, "--checkpoint", str(checkpoint)])
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertIn("validation unknown", stderr)
            self.assertFalse(Path(args[3]).exists())
            self.assertFalse(Path(args[4]).exists())
            self.assertTrue(json.loads(checkpoint.read_text())["invariants"])
            self.assertFalse(json.loads(checkpoint.read_text())["verified"])

    def test_forged_baseline_cannot_seed_refinement_or_write_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            args = self.write_inputs(folder, self.fixture())
            baseline = json.loads(Path(args[2]).read_text())
            baseline["invariants"] = [{"kind": "absent", "x": 1, "y": -1}]
            baseline["validation"] = {"verified": True}
            Path(args[2]).write_text(json.dumps(baseline))
            code, stdout, stderr = self.run_main(args)
            self.assertEqual(code, 2)
            self.assertEqual(stdout, "")
            self.assertIn("certificate failed", stderr)
            self.assertFalse(Path(args[3]).exists())
            self.assertFalse(Path(args[4]).exists())

    def test_family_hypotheses_are_explicit_deduplicated_and_checked(self):
        fixture = self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            args = self.write_inputs(folder, fixture)
            path = folder / "families.json"
            good = RequiresBelowAny(1, (0,))
            bad = RequiresBelowAny(1, (2,))
            path.write_text(json.dumps({"candidates": [good.to_data(), good.to_data(), bad.to_data()]}))
            self.assertEqual(load_family_hypotheses(path, fixture[1]), (good, bad))
            code, stdout, stderr = self.run_main([*args, "--family-hypotheses", str(path)])
            self.assertEqual(code, 0, stderr)
            self.assertEqual(json.loads(stdout)["family_hypotheses"], 2)
            proof = load_certificate(fixture[1], args[3])
            self.assertIn(good, proof.invariants)
            self.assertNotIn(bad, proof.invariants)
            between = RequiresBetweenAny(2, 0, (1,))
            path.write_text(json.dumps({"candidates": [good.to_data(), between.to_data()]}))
            self.assertEqual(load_family_hypotheses(path, fixture[1]), (good, between))
            path.write_text(json.dumps({"candidates": [RequiresBelowAny(1, (999,)).to_data()]}))
            with self.assertRaisesRegex(ValueError, "unknown layer"):
                load_family_hypotheses(path, fixture[1])

    def test_output_aliases_and_invalid_timeouts_are_rejected_before_work(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.write_inputs(Path(folder), self.fixture())
            original = Path(args[2]).read_bytes()
            for argv in ([*args[:3], args[2], args[4]], [*args, "--checkpoint", args[1]],
                         [*args, "--timeout-ms", "0"], [*args, "--refine-timeout-ms", "0"]):
                with self.subTest(argv=argv):
                    code, stdout, stderr = self.run_main(argv)
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout, "")
                    self.assertTrue(stderr)
                    self.assertEqual(Path(args[2]).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
