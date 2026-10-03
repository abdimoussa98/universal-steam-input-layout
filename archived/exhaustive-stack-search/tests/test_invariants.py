"""Induction must survive unseen events and may not turn unknown into proof."""
import unittest
from unittest.mock import patch

try:
    import z3
except ImportError:
    z3 = None

from steam_layout.held_model import HeldModel, explore
from steam_layout.model import Layout
from test_audit_inheritance import act, add, build, remove

if z3 is not None:
    from steam_layout.invariants import Candidate, InvariantProof, candidates_from_states
    from steam_layout.stack_report import layer_report


@unittest.skipIf(z3 is None, "optional z3-solver proof dependency is not installed")
class InvariantTests(unittest.TestCase):
    def model(self, layers):
        return HeldModel(Layout(build(layers)))

    def test_mutually_supporting_invariants_are_proved_together(self):
        model = self.model({"Base": {"switch": ("switches", {
            "button_a": act([add("B"), add("A")]),
            "button_b": act([remove("A"), remove("B")])})}, "A": {}, "B": {}})
        candidates = [Candidate("requires", 1, 2), Candidate("requires", 2, 1)]
        proof = InvariantProof(model, candidates).run()
        self.assertEqual(set(proof.invariants), set(candidates))
        for stack, held, _ in explore(model):
            ranks = [stack.index(i) + 1 if i in stack else 0 for i in range(3)]
            self.assertTrue(all(c.holds(ranks, []) for c in proof.invariants))

    def test_dropped_assumptions_are_rechecked_until_fixed_point(self):
        # The A -> B event is visited before the Base -> A event. An early
        # check of 'B absent' may rely on 'A absent', which will be dropped.
        model = self.model({"Base": {"switch": ("switches", {"z": act(add("A"))})},
                            "A": {"switch": ("switches", {"a": act(add("B"))})}, "B": {}})
        proof = InvariantProof(model, [Candidate("absent", 1), Candidate("absent", 2)]).run()
        self.assertEqual(proof.invariants, ())
        self.assertGreaterEqual(proof.stats["rounds"], 3)

    def test_initially_false_candidates_never_become_assumptions(self):
        model = self.model({"Base": {}, "A": {}})
        proof = InvariantProof(model, [Candidate("absent", 0)]).run()
        self.assertEqual(proof.invariants, ())
        with self.assertRaises(ValueError):
            InvariantProof(model, []).query_solver()

    def test_unknown_discards_affected_candidates(self):
        model = self.model({"Base": {"switch": ("switches", {"a": act(add("A"))})}, "A": {}})
        real_solver = z3.Solver

        def unknown_solver():
            solver = real_solver()
            solver.check = lambda *args: z3.unknown
            return solver

        with patch("steam_layout.invariants.z3.Solver", side_effect=unknown_solver):
            proof = InvariantProof(model, [Candidate("absent", 1)]).run()
        self.assertEqual(proof.invariants, ())
        self.assertGreater(proof.stats["unknown_checks"], 0)

    def test_unseen_does_not_mean_impossible_and_queries_remain_open(self):
        model = self.model({"Base": {"switch": ("switches", {"a": act(add("A"))})}, "A": {}, "Dead": {}})
        proof = InvariantProof(model, candidates_from_states(model, [model.start()])).run()
        self.assertNotIn(Candidate("absent", 1), proof.invariants)
        self.assertIn(Candidate("absent", 2), proof.invariants)
        report = layer_report(proof, "A")
        self.assertIn("Dead", report["excluded"]["below"])
        self.assertEqual(report["below"][0]["layer"], "Base")
        self.assertEqual(report["below"][0]["status"], "possible")
        self.assertFalse(report["complete_for_model"])

    def test_unknown_queries_never_exclude_facts(self):
        model = self.model({"Base": {}, "A": {}})
        proof = InvariantProof(model, []).run()
        solver = proof.query_solver()
        solver.check = lambda *args: z3.unknown
        with patch.object(proof, "query_solver", return_value=solver):
            report = layer_report(proof, "A")
        self.assertEqual(report["excluded"]["below"], [])
        self.assertEqual(report["below"][0]["status"], "possible")
        self.assertGreater(report["counts"]["unknown_queries"], 0)

    def test_evidence_from_another_model_is_rejected(self):
        from steam_layout.stack_evidence import Evidence
        model = self.model({"Base": {}, "A": {}})
        other = self.model({"Base": {}, "A": {}})
        proof = InvariantProof(model, []).run()
        with self.assertRaisesRegex(ValueError, "same HeldModel"):
            layer_report(proof, "A", Evidence(other))

    def test_abstract_top_model_is_rejected(self):
        from steam_layout.held_model import TopModel
        model = TopModel(Layout(build({"Base": {}, "A": {}})), 1)
        with self.assertRaisesRegex(ValueError, "HeldModel"):
            InvariantProof(model, [])

    def test_grouped_updates_preserve_all_successor_states(self):
        from steam_layout.invariants import induction_transitions
        from steam_layout.symbolic import SymbolicModel
        from test_held_model import guarded_layout
        model = HeldModel(Layout(guarded_layout()))
        symbolic = SymbolicModel(model)
        merged = induction_transitions(symbolic)
        for state in explore(model):
            actual = {n for n, _ in symbolic.successor_states(state, merged)}
            expected = {n for n, _ in model.successors(state)}
            self.assertEqual(actual, expected)

    def test_all_proved_templates_hold_on_complete_pad_state_space(self):
        from test_held_model import pad_layout
        model = HeldModel(Layout(pad_layout()))
        # Deliberately seed from only Base; all other samples are unavailable.
        proof = InvariantProof(model, candidates_from_states(model, [model.start()])).run()
        self.assertGreater(len(proof.invariants), 0)
        for stack, held, _ in explore(model):
            ranks = [stack.index(i) + 1 if i in stack else 0 for i in range(len(model.layer_names))]
            buttons = [c in held for c in range(len(model.controls))]
            for candidate in proof.invariants:
                self.assertTrue(candidate.holds(ranks, buttons), (candidate, stack, held))

    def test_order_guesses_survive_as_alternatives_to_coexistence_guesses(self):
        model = self.model({"Base": {}, "A": {}, "B": {}})
        candidates = candidates_from_states(model, [model.start()])
        self.assertIn(Candidate("excludes", 1, 2), candidates)
        self.assertIn(Candidate("not_below", 1, 2), candidates)
        self.assertIn(Candidate("not_below", 2, 1), candidates)


if __name__ == "__main__":
    unittest.main()
