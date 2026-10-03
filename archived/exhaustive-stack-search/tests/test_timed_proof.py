"""Proof bounds must meet replayed witnesses before a fact report is complete."""
import unittest
import importlib.util
from unittest.mock import patch

from steam_layout.model import Layout
from steam_layout.timed_facts import FactCatalogue, FactWitnesses
from steam_layout.timed_model import TimedModel
from test_audit_inheritance import act, add, build, remove

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.invariants import Candidate
    from steam_layout.timed_proof import TimedProof


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedProofTests(unittest.TestCase):
    def make(self, layers):
        model = TimedModel(Layout(build(layers)))
        catalogue = FactCatalogue(model)
        return model, catalogue, FactWitnesses(model, catalogue)

    def test_complete_bounds_include_a_delayed_witness_and_exclude_unreachable_layer(self):
        model, catalogue, witnesses = self.make({
            "Base": {"switch": ("switches", {"left_bumper": act(add("Late"), delay_start="3")})},
            "Late": {}, "Unreachable": {}})
        witnesses.add_trace([{"press": ["switch", "left_bumper"]}, {"wait_ms": 3}])
        proof = TimedProof(model, witnesses.node_states.values()).run()
        self.assertTrue(proof.validate()["verified"])
        result = proof.classify(catalogue, witnesses)
        self.assertTrue(result["complete_for_model"])
        self.assertFalse(result["possible"])
        self.assertEqual(result["proven"] | result["excluded"], set(catalogue.facts))
        self.assertFalse(result["proven"] & result["excluded"])

    def test_initial_always_on_adds_are_part_of_initialization(self):
        model, _, _ = self.make({
            "Base": {"switch": ("switches", {"always_on_action": act(add("Initial"))})},
            "Initial": {}})
        self.assertEqual({state.stack for state in model.start()}, {(0, 1)})
        # Deliberately inject a false hypothesis; initialization must remove it
        # even if no later physical transition can add this layer again.
        proof = TimedProof(model)
        proof.candidates = (Candidate("absent", 1),)
        proof.run()
        self.assertNotIn(Candidate("absent", 1), proof.invariants)
        self.assertTrue(proof.validate()["verified"])

    def test_unknown_queries_leave_alternatives_open(self):
        model, catalogue, witnesses = self.make({"Base": {}, "Dead": {}})
        proof = TimedProof(model).run()
        solver = proof.query_solver()
        solver.check = lambda *args: z3.unknown
        with patch.object(proof, "query_solver", return_value=solver):
            result = proof.classify(catalogue, witnesses)
        self.assertFalse(result["complete_for_model"])
        self.assertFalse(result["excluded"])
        self.assertTrue(result["unknown_queries"])

    def test_certificate_rejects_invalid_invariant(self):
        model, _, _ = self.make({"Base": {"switch": ("switches", {
            "left_bumper": act(add("Live"))})}, "Live": {}})
        proof = TimedProof(model).run()
        proof.invariants = (Candidate("absent", 1),)
        with self.assertRaisesRegex(ValueError, "certificate failed"):
            proof.validate()

    def test_requires_finished_proof(self):
        model, catalogue, witnesses = self.make({"Base": {}, "Dead": {}})
        proof = TimedProof(model)
        with self.assertRaises(ValueError):
            proof.validate()
        with self.assertRaises(ValueError):
            proof.classify(catalogue, witnesses)

    def test_compaction_preserves_the_entire_invariant_conjunction(self):
        model, _, _ = self.make({"Base": {}, "A": {}, "B": {}, "Dead": {}})
        proof = TimedProof(model)
        proof.invariants = (Candidate("absent", 3), Candidate("requires", 3, 1),
                            Candidate("excludes", 1, 3), Candidate("not_below", 3, 2),
                            Candidate("excludes", 1, 2), Candidate("not_below", 1, 2),
                            Candidate("not_below", 2, 1))
        before = z3.And([c.formula(proof.symbolic.ranks, proof.symbolic.held)
                         for c in proof.invariants])
        proof.compact()
        self.assertEqual(proof.invariants, (Candidate("absent", 3), Candidate("excludes", 1, 2)))
        after = z3.And([c.formula(proof.symbolic.ranks, proof.symbolic.held)
                        for c in proof.invariants])
        solver = z3.Solver()
        solver.add(z3.Xor(before, after))
        self.assertEqual(solver.check(), z3.unsat)

    def test_refinement_preserves_verified_base_when_new_checks_are_unknown(self):
        model, _, _ = self.make({"Base": {"switch": ("switches", {
            "left_bumper": act(add("Live"))})}, "Live": {}, "Dead": {}})
        proof = TimedProof(model)
        proof.candidates = (Candidate("absent", 2),)
        proof.run().validate()
        original_solver = z3.Solver

        def unknown_solver():
            solver = original_solver()
            solver.check = lambda *args: z3.unknown
            return solver

        with patch("steam_layout.timed_proof.z3.Solver", side_effect=unknown_solver):
            refined = proof.refine([Candidate("absent", 1)])
        self.assertEqual(refined.invariants, proof.invariants)
        self.assertEqual(refined.stats["baseline_invariants"], len(proof.invariants))
        self.assertTrue(refined.validate()["verified"])

    def test_refinement_accepts_a_checked_family_disjunction(self):
        from steam_layout.timed_predicates import RequiresBelowAny
        model, _, _ = self.make({"Base": {"switch": ("switches", {
            "left_bumper": act([add("X"), add("A")]),
            "right_bumper": act([add("X"), add("B")])})}, "A": {}, "B": {}, "X": {}})
        proof = TimedProof(model)
        proof.candidates = ()
        proof.run().validate()
        predicate = RequiresBelowAny(3, (1, 2))
        refined = proof.refine([predicate])
        self.assertIn(predicate, refined.invariants)
        self.assertTrue(refined.validate()["verified"])

    def test_refinement_rejects_a_forged_base_before_using_it(self):
        model, _, _ = self.make({"Base": {"switch": ("switches", {
            "left_bumper": act(add("Live"))})}, "Live": {}})
        proof = TimedProof(model).run()
        proof.invariants = (Candidate("absent", 1),)
        with self.assertRaisesRegex(ValueError, "certificate failed"):
            proof.refine([])

    def test_direct_query_rejects_changed_fact_context_even_after_cached_validation(self):
        from dataclasses import replace
        from steam_layout.timed_predicates import FactExclusion
        model, catalogue, witnesses = self.make({"Base": {"switch": ("switches", {
            "left_bumper": act("key_press SPACE, , ")})}, "Dead": {}})
        fact = next(f for f in catalogue.facts if f.kind == "inherit" and f.x == 1 and f.y == 0)
        proof = TimedProof(model)
        proof.invariants = (FactExclusion(fact),)
        proof.finished = True
        proof.validate()
        forged = replace(fact, definers=(0, 1))
        # Fact identity deliberately ignores catalogue context; the proof API
        # must verify that context separately before trusting a cached check.
        self.assertEqual(forged, fact)
        proof.invariants = (FactExclusion(forged),)
        with self.assertRaisesRegex(ValueError, "noncanonical definer"):
            proof.classify(catalogue, witnesses)

    def test_classification_rejects_catalogue_and_witnesses_from_another_model(self):
        layers = {"Base": {}, "Dead": {}}
        model, catalogue, witnesses = self.make(layers)
        _, other_catalogue, other_witnesses = self.make(layers)
        proof = TimedProof(model).run()
        with self.assertRaisesRegex(ValueError, "same TimedModel"):
            proof.classify(other_catalogue, other_witnesses)
        with self.assertRaisesRegex(ValueError, "same TimedModel"):
            proof.classify(catalogue, other_witnesses)
        with self.assertRaisesRegex(ValueError, "same TimedModel"):
            proof.classify(other_catalogue, witnesses)

    def test_classification_rejects_different_catalogue_for_the_same_model(self):
        model, catalogue, _ = self.make({"Base": {}, "Dead": {}})
        other_catalogue = FactCatalogue(model)
        other_witnesses = FactWitnesses(model, other_catalogue)
        proof = TimedProof(model).run()
        with self.assertRaisesRegex(ValueError, "this fact catalogue"):
            proof.classify(catalogue, other_witnesses)

    def test_unknown_individual_induction_checks_discard_every_unproved_candidate(self):
        model, _, _ = self.make({"Base": {"switch": ("switches", {
            "left_bumper": act(add("Live"))})}, "Live": {},
            "Dead": {"switch": ("switches", {"left_bumper": act(add("Dead"))})}})
        proof = TimedProof(model)
        proof.candidates = (Candidate("absent", 1), Candidate("held", 1, 0),
                            Candidate("absent", 2), Candidate("held", 2, 0))
        original_solver = z3.Solver

        def unknown_solver():
            solver = original_solver()
            solver.check = lambda *args: z3.unknown
            return solver

        with patch("steam_layout.timed_proof.z3.Solver", side_effect=unknown_solver):
            proof.run()
        self.assertEqual(proof.invariants, ())
        # Both dependency groups must split their disjunction before dropping
        # the two unresolved singletons, rather than accepting an unknown.
        self.assertGreaterEqual(proof.stats["unknown_checks"], 6)
        self.assertTrue(proof.validate()["verified"])

    def test_unknown_batch_is_split_and_independently_provable_singletons_survive(self):
        model, _, _ = self.make({"Base": {"switch": ("switches", {
            "left_bumper": act("key_press SPACE, , ")})},
            "Dead": {"switch": ("switches", {"left_bumper": act(add("Dead"))})}})
        proof = TimedProof(model)
        proof.candidates = (Candidate("absent", 1), Candidate("held", 1, 0))
        original_solver = z3.Solver

        def one_unknown_solver():
            solver = original_solver()
            original_check = solver.check
            calls = []

            def check(*args):
                calls.append(None)
                return z3.unknown if len(calls) == 1 else original_check(*args)

            solver.check = check
            return solver

        with patch("steam_layout.timed_proof.z3.Solver", side_effect=one_unknown_solver):
            proof.run()
        self.assertEqual(proof.stats["invariants_before_compaction"], len(proof.candidates))
        self.assertEqual(proof.invariants, (Candidate("absent", 1),))
        self.assertEqual(proof.stats["unknown_checks"], 1)
        self.assertTrue(proof.validate()["verified"])

    def test_removed_dependency_invalidates_an_earlier_cached_unsat_core(self):
        # B is checked before A. Initially B absent can rely on A absent;
        # dropping A absent must invalidate that proof in the following round.
        model, _, _ = self.make({
            "Base": {"switch": ("switches", {"left_bumper": act(add("A"))})},
            "B": {},
            "A": {"switch": ("switches", {"right_bumper": act(add("B"))})}})
        proof = TimedProof(model)
        proof.candidates = (Candidate("absent", 1), Candidate("absent", 2))
        proof.run()
        self.assertFalse(proof.invariants)
        self.assertGreaterEqual(proof.stats["rounds"], 3)
        self.assertTrue(proof.validate()["verified"])


if __name__ == "__main__":
    unittest.main()
