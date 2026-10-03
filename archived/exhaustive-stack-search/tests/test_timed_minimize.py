"""Logical reduction must preserve hypotheses without manufacturing a proof."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from test_audit_inheritance import act, add, build

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.invariants import Candidate
    from steam_layout.timed_audit import load_certificate, save_certificate
    from steam_layout.timed_minimize import main, minimize_hypotheses
    from steam_layout.timed_predicates import RequiresBelowAny, RequiresBetweenAny
    from steam_layout.timed_proof import TimedProof


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedMinimizeTests(unittest.TestCase):
    def proof(self, live=False):
        base = {"switch": ("switches", {"left_bumper": act(add("A"))})} if live else {}
        return TimedProof(TimedModel(Layout(build({"Base": base, "A": {}, "B": {}, "C": {}}))))

    def test_reduces_mixed_predicates_and_preserves_the_conjunction(self):
        proof = self.proof()
        original = (Candidate("requires", 3, 1), Candidate("requires", 3, 2),
                    RequiresBelowAny(3, (1,)), RequiresBelowAny(3, (2,)),
                    RequiresBetweenAny(3, 0, (1, 2)), Candidate("not_below", 3, 1))
        proof.invariants = original
        reduced, stats = minimize_hypotheses(proof, timeout_ms=1000)
        self.assertLess(len(reduced), len(original))
        self.assertEqual(proof.invariants, original)
        self.assertFalse(proof.finished)
        before = z3.And([p.formula(proof.symbolic.ranks, proof.symbolic.held) for p in original])
        after = z3.And([p.formula(proof.symbolic.ranks, proof.symbolic.held) for p in reduced])
        solver = z3.Solver()
        solver.add(proof.symbolic.domain, z3.Xor(before, after))
        self.assertEqual(solver.check(), z3.unsat)
        self.assertEqual(stats["retained"], len(reduced))

    def test_false_hypotheses_still_fail_induction_after_reduction(self):
        proof = self.proof(live=True)
        proof.invariants = (Candidate("absent", 1), Candidate("excludes", 1, 2))
        proof.invariants, _ = minimize_hypotheses(proof, timeout_ms=1000)
        proof.finished = True
        with self.assertRaisesRegex(ValueError, "certificate failed"):
            proof.validate()

    def test_unknown_entailment_keeps_every_candidate(self):
        proof = self.proof()
        proof.invariants = (Candidate("absent", 1), Candidate("excludes", 1, 2))
        solver = z3.Solver()
        solver.check = lambda *args: z3.unknown
        with patch("steam_layout.timed_minimize.z3.Solver", return_value=solver):
            reduced, stats = minimize_hypotheses(proof)
        self.assertEqual(reduced, proof.invariants)
        self.assertEqual(stats["unknown_checks"], len(proof.invariants))

    def test_empty_hypotheses_and_invalid_timeouts(self):
        proof = self.proof()
        self.assertEqual(minimize_hypotheses(proof)[0], ())
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                minimize_hypotheses(proof, timeout_ms=value)

    def test_cli_rechecks_in_place_certificate_and_protects_layout(self):
        data = build({"Base": {}, "A": {}, "B": {}})
        model = TimedModel(Layout(data))
        proof = TimedProof(model).run()
        with tempfile.TemporaryDirectory() as directory:
            layout = Path(directory) / "layout.json"
            certificate = Path(directory) / "proof.json"
            layout.write_text(json.dumps(data))
            original = layout.read_bytes()
            save_certificate(proof, certificate)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(layout), str(certificate), str(certificate)]), 0)
                self.assertEqual(main([str(layout), str(certificate), str(layout)]), 2)
            self.assertEqual(layout.read_bytes(), original)
            checked = load_certificate(model, certificate)
            self.assertTrue(checked.validate()["verified"])
