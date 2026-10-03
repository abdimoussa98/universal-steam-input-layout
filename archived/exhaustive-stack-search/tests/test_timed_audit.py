"""Per-layer fact reports and independently checked certificate loading."""
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.timed_discover import save_witnesses
from steam_layout.timed_facts import Fact, FactCatalogue, FactWitnesses
from steam_layout.timed_model import TimedModel
from steam_layout.timed_predicates import FactExclusion, RequiresBelowAny, RequiresBetweenAny
from test_audit_inheritance import act, add, build, remove

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    from steam_layout.invariants import Candidate
    from steam_layout.timed_audit import (ALGORITHM_FILES, TimedAudit, format_report, load_certificate,
                                         proof_identity, save_certificate, validate_proof)
    from steam_layout.timed_proof import TimedProof


ROOT = Path(__file__).resolve().parents[1]
LB = ["switch", "left_bumper"]


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedAuditTests(unittest.TestCase):
    def refined_fixture(self):
        model = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": act([add("X"), add("A")]),
            "right_bumper": act([add("X"), add("B")])})},
            "A": {}, "B": {}, "X": {}, "Dead": {}})))
        catalogue = FactCatalogue(model)
        predicate = RequiresBelowAny(model.spec.index["X"],
                                     (model.spec.index["A"], model.spec.index["B"]))
        proof = TimedProof(model, timeout_ms=3000)
        proof.candidates = (Candidate("absent", model.spec.index["Dead"]),)
        proof.run().validate()
        proof = proof.refine([predicate])
        self.assertIn(predicate, proof.invariants)
        return model, catalogue, proof, predicate

    def fixture(self):
        data = build({"Base": {"switch": ("switches", {
            "left_bumper": {**act(add("A")),
                            "release": {"bindings": {"binding": remove("A")}}}
        })}, "A": {}, "Never": {}})
        model = TimedModel(Layout(data))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        witnesses.add_trace([{"press": LB}, {"release": LB}])
        proof = TimedProof(model, witnesses.node_states.values(), timeout_ms=3000).run()
        return data, model, catalogue, witnesses, proof

    def test_toy_complete_report_answers_below_above_and_original_inheritance(self):
        _, model, catalogue, witnesses, proof = self.fixture()
        audit = TimedAudit(proof, catalogue, witnesses)
        report = audit.layer_report("A")
        self.assertTrue(report["complete_for_model"])
        self.assertEqual([row["layer"] for row in report["below"]], ["Base"])
        self.assertEqual(report["above"], [])
        inherited = next(row for row in report["inherited"] if row["input"] == "left_bumper")
        self.assertEqual([value["owner"] for value in inherited["values"]], ["Base"])
        value = inherited["values"][0]
        original = model.layout.active("Base")["switch"]["inputs"]["left_bumper"]["activators"]
        self.assertEqual(value["activators"], original)
        self.assertEqual(report["witness_traces"][value["trace_id"]]["events"], [{"press": LB}])
        self.assertTrue(any(row["owner"] is None for row in report["excluded"]["inherited"]))
        self.assertEqual([row["layer"] for row in audit.layer_report("Base")["above"]], ["A"])
        self.assertIn("excluded by checked induction", format_report(report))
        self.assertIn("not a claim of Steam hardware equivalence", report["scope"])

    def test_unreachable_layer_has_all_alternatives_excluded(self):
        _, _, catalogue, witnesses, proof = self.fixture()
        report = TimedAudit(proof, catalogue, witnesses).layer_report("Never")
        self.assertTrue(report["complete_for_model"])
        self.assertEqual(report["counts"]["proven"], 0)
        self.assertEqual(report["counts"]["possible"], 0)
        self.assertGreater(report["counts"]["excluded"], 0)
        self.assertEqual(report["witness_traces"], {})

    def test_all_layer_report_deduplicates_fact_counts_and_traces(self):
        _, _, catalogue, witnesses, proof = self.fixture()
        audit = TimedAudit(proof, catalogue, witnesses)
        report = audit.report()
        self.assertTrue(report["complete_for_model"])
        self.assertTrue(report["global_complete_for_model"])
        self.assertEqual(sum(report["counts"].values()), len(catalogue.facts))
        self.assertEqual([row["layer"] for row in report["layers"]], list(catalogue.names))
        self.assertEqual(len(report["witness_traces"]), 1)
        for layer in report["layers"]:
            self.assertNotIn("witness_traces", layer)
        with self.assertRaisesRegex(ValueError, "distinct"):
            audit.report(["A", "A"])
        with self.assertRaisesRegex(ValueError, "Unknown layer"):
            audit.layer_report("Missing")

    def test_empty_sound_invariant_set_leaves_unwitnessed_alternatives_open(self):
        _, model, catalogue, _, _ = self.fixture()
        witnesses = FactWitnesses(model, catalogue)
        proof = TimedProof(model, timeout_ms=3000)
        proof.finished = True
        proof.invariants = ()
        report = TimedAudit(proof, catalogue, witnesses).report()
        self.assertFalse(report["complete_for_model"])
        self.assertGreater(report["counts"]["possible"], 0)

    def test_unresolved_above_relation_makes_base_report_incomplete(self):
        model = TimedModel(Layout(build({"Base": {}, "Unobserved": {}})))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        proof = TimedProof(model, timeout_ms=3000)
        proof.finished = True
        proof.invariants = ()
        audit = TimedAudit(proof, catalogue, witnesses)
        report = audit.layer_report("Base")
        self.assertFalse(report["complete_for_model"])
        self.assertEqual(report["below"], [])
        self.assertEqual([(row["layer"], row["status"]) for row in report["above"]],
                         [("Unobserved", "possible")])
        selected = audit.report(["Base"])
        self.assertFalse(selected["complete_for_model"])
        self.assertEqual(selected["counts"], {"proven": 0, "possible": 1, "excluded": 1})

    def test_initial_unbound_value_keeps_zero_witness_id_and_empty_trace(self):
        model = TimedModel(Layout(build({
            "Base": {}, "Unreachable": {"switch": ("switches", {
                "left_bumper": act("key_press SPACE, , ")})}})))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        proof = TimedProof(model).run()
        report = TimedAudit(proof, catalogue, witnesses).layer_report("Base")
        value = report["inherited"][0]["values"][0]
        self.assertEqual(value["status"], "proven")
        self.assertEqual(value["witness"], 0)
        self.assertEqual(value["trace_id"], "0")
        self.assertIsNone(value["owner"])
        self.assertEqual(report["witness_traces"]["0"]["events"], [])

    def test_certificate_round_trip_revalidates_then_matches_report(self):
        _, model, catalogue, witnesses, proof = self.fixture()
        expected = TimedAudit(proof, catalogue, witnesses).report()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            self.assertEqual(saved["identity"], proof_identity(model))
            # Serialized validation flags do not authorize exclusions.
            saved["validation"] = {"verified": False, "checks": -1}
            path.write_text(json.dumps(saved))
            loaded = load_certificate(model, path, timeout_ms=3000)
            actual = TimedAudit(loaded, catalogue, witnesses).report()
            self.assertTrue(actual["validation"]["verified"])
            self.assertGreater(actual["validation"]["checks"], 0)
            self.assertEqual(actual["layers"], expected["layers"])
            self.assertEqual(actual["counts"], expected["counts"])

    def test_stale_algorithm_or_scenario_certificate_is_rejected(self):
        _, model, _, _, proof = self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            saved["identity"]["algorithm_sha256"] = "0" * 64
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                load_certificate(model, path)
            save_certificate(proof, path)
            other = TimedModel(model.layout, default_repeat_ms=50)
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                load_certificate(other, path)

    def test_typed_family_predicate_round_trip_retains_checked_baseline(self):
        model, _, proof, predicate = self.refined_fixture()
        self.assertIn("timed_predicates.py", ALGORITHM_FILES)
        self.assertIn("timed_phase_envelope.py", ALGORITHM_FILES)
        self.assertIn("timed_progress_envelope.py", ALGORITHM_FILES)
        self.assertIn("timed_elapsed_envelope.py", ALGORITHM_FILES)
        self.assertIn("timed_analog_envelope.py", ALGORITHM_FILES)
        self.assertTrue(any(isinstance(item, Candidate) for item in proof.invariants))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            self.assertIn(predicate.to_data(), saved["invariants"])
            loaded = load_certificate(model, path, timeout_ms=3000)
            self.assertEqual(loaded.invariants, proof.invariants)
            self.assertTrue(validate_proof(loaded)["verified"])

    def test_family_member_tampering_cannot_claim_a_stronger_invariant(self):
        model, _, proof, predicate = self.refined_fixture()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            saved["invariants"] = [{**predicate.to_data(), "members": [model.spec.index["A"]]}]
            saved["validation"] = {"verified": True, "checks": 999999}
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "certificate failed"):
                load_certificate(model, path, timeout_ms=3000)
        # Cached validation also covers the complete members payload.
        proof.invariants = (RequiresBelowAny(predicate.x, (model.spec.index["A"],)),)
        with self.assertRaisesRegex(ValueError, "certificate failed"):
            validate_proof(proof)

    def test_between_round_trip_and_tampering_use_independent_validation(self):
        model, _, baseline, _ = self.refined_fixture()
        predicate = RequiresBetweenAny(model.spec.index["X"], 0,
                                       (model.spec.index["A"], model.spec.index["B"]))
        proof = baseline.refine((predicate,))
        self.assertIn(predicate, proof.invariants)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            self.assertIn(predicate.to_data(), saved["invariants"])
            self.assertEqual(load_certificate(model, path).invariants, proof.invariants)
            invalid = [{**predicate.to_data(), key: value} for key, value in (
                ("x", -1), ("x", True), ("y", -1), ("y", 999), ("y", predicate.x),
                ("members", []), ("members", [0]), ("members", [True]), ("members", [999]))]
            for row in invalid:
                with self.subTest(row=row):
                    saved["invariants"] = [row]
                    path.write_text(json.dumps(saved))
                    with self.assertRaisesRegex(ValueError, "invalid serialized"):
                        load_certificate(model, path)
            saved["invariants"] = [{**predicate.to_data(), "members": [model.spec.index["A"]]}]
            saved["validation"] = {"verified": True}
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "certificate failed"):
                load_certificate(model, path)

    def test_family_predicate_rejects_invalid_targets_members_and_extra_fields(self):
        model, _, proof, predicate = self.refined_fixture()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            invalid = [{**predicate.to_data(), "x": value} for value in (-1, True, 999)]
            invalid.extend({**predicate.to_data(), "members": value}
                           for value in ([], [-1], [True], [999], [predicate.x], "1"))
            invalid.append({**predicate.to_data(), "verified": True})
            for row in invalid:
                with self.subTest(row=row):
                    saved["invariants"] = [row]
                    path.write_text(json.dumps(saved))
                    with self.assertRaisesRegex(ValueError, "invalid serialized"):
                        load_certificate(model, path, timeout_ms=3000)

    def test_fact_exclusion_round_trip_restores_original_raw_alias_definers(self):
        # These names describe one physical click but are distinct raw inputs
        # for the inheritance question and must retain separate definers.
        model = TimedModel(Layout(build({
            "Base": {"switch": ("switches", {"left_bumper": act(add("X")),
                                               "left_stick_click": act("key_press SPACE, , ")})},
            "A": {"switch": ("switches", {"left_stick_click": act("key_press A, , ")})},
            "B": {"joystick": ("dpad", {"click": act("key_press B, , ")})},
            "X": {}})))
        catalogue = FactCatalogue(model)
        first = catalogue.controls.index(("switch", "left_stick_click"))
        second = catalogue.controls.index(("joystick", "click"))
        self.assertNotEqual(catalogue.definitions[first], catalogue.definitions[second])
        predicates = tuple(FactExclusion(catalogue._lookup[("inherit", 3, y, j)])
                           for y, j in ((1, first), (2, second)))
        proof = TimedProof(model, timeout_ms=3000)
        proof.candidates = (Candidate("absent", 1), Candidate("absent", 2))
        proof.run().validate()
        proof = proof.refine(predicates)
        self.assertTrue(set(predicates) <= set(proof.invariants))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            self.assertTrue(all(item.to_data() in saved["invariants"] for item in predicates))
            loaded = load_certificate(model, path, timeout_ms=3000)
            self.assertEqual(loaded.invariants, proof.invariants)
            for item in loaded.invariants:
                if not isinstance(item, FactExclusion):
                    continue
                expected = catalogue._lookup[(item.fact.kind, item.fact.x, item.fact.y, item.fact.j)]
                self.assertEqual(item.fact.definers, expected.definers)
            # A real reachable inheritance fact is a valid catalogue ID but
            # its negation must fail the independent proof check.
            saved["invariants"] = [FactExclusion(catalogue._lookup[("inherit", 3, 0, first)]).to_data()]
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "certificate failed"):
                load_certificate(model, path, timeout_ms=3000)

    def test_fact_exclusion_rejects_non_catalogue_ids_and_injected_context(self):
        _, model, catalogue, _, proof = self.fixture()
        j = catalogue.controls.index(("switch", "left_bumper"))
        original = FactExclusion(catalogue._lookup[("inherit", 1, -1, j)])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            invalid = [{**original.to_data()["fact"], key: value}
                       for key, value in (("x", -1), ("x", True), ("x", 999),
                                          ("y", -2), ("y", 999), ("j", -1),
                                          ("j", True), ("j", 999), ("definers", []))]
            # Base defines this input, so Base inheritance is not a catalogue
            # alternative even though both numeric IDs are individually valid.
            invalid.append({**original.to_data()["fact"], "x": 0})
            for fact in invalid:
                with self.subTest(fact=fact):
                    saved["invariants"] = [{"kind": "fact_exclusion", "fact": fact}]
                    path.write_text(json.dumps(saved))
                    with self.assertRaises(ValueError):
                        load_certificate(model, path, timeout_ms=3000)
        # Fact equality deliberately ignores context; the audit boundary must
        # compare it explicitly rather than caching only the wire identity.
        proof.invariants = (FactExclusion(Fact("inherit", 1, -1, j, ())),)
        with self.assertRaisesRegex(ValueError, "definer context"):
            validate_proof(proof)

    def test_forged_hypothesis_is_rejected_despite_positive_saved_validation(self):
        _, model, _, _, proof = self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            saved["invariants"] = [asdict(Candidate("absent", model.spec.index["A"]))]
            saved["validation"] = {"verified": True, "checks": 999999}
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "certificate failed"):
                load_certificate(model, path, timeout_ms=3000)

    def test_bad_invariant_indices_fail_before_formulas_use_python_negative_indexing(self):
        _, model, _, _, proof = self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            saved = save_certificate(proof, path)
            for candidate in (Candidate("absent", -1), Candidate("held", 1, -1),
                              Candidate("requires", 1, 999), Candidate("unknown", 1)):
                saved["invariants"] = [asdict(candidate)]
                path.write_text(json.dumps(saved))
                with self.assertRaisesRegex(ValueError, "invalid serialized"):
                    load_certificate(model, path, timeout_ms=3000)

    def test_cached_validation_cannot_survive_changed_invariants(self):
        _, model, _, _, proof = self.fixture()
        self.assertTrue(validate_proof(proof)["verified"])
        proof.invariants = (Candidate("absent", model.spec.index["A"]),)
        with self.assertRaisesRegex(ValueError, "certificate failed"):
            validate_proof(proof)

    def test_run_and_show_cli_use_checked_archive_and_certificate(self):
        data, _, _, witnesses, _ = self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            layout, archive = folder / "layout.json", folder / "witnesses.sqlite"
            certificate, report = folder / "certificate.json", folder / "report.json"
            layout.write_text(json.dumps(data))
            save_witnesses(witnesses, archive)
            command = [sys.executable, "-m", "steam_layout.timed_audit"]
            result = subprocess.run([*command, "run", str(layout), str(archive), str(certificate),
                                     str(report), "--timeout-ms", "3000"], cwd=ROOT,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["complete_for_model"])
            self.assertTrue(json.loads(report.read_text())["complete_for_model"])
            result = subprocess.run([*command, "show", str(layout), str(archive), str(certificate),
                                     "A", "--json", "--timeout-ms", "3000"], cwd=ROOT,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["complete_for_model"])
            forged = json.loads(certificate.read_text())
            forged["invariants"] = [asdict(Candidate("absent", 1))]
            certificate.write_text(json.dumps(forged))
            result = subprocess.run([*command, "show", str(layout), str(archive), str(certificate),
                                     "A", "--json", "--timeout-ms", "3000"], cwd=ROOT,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("certificate failed", result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
