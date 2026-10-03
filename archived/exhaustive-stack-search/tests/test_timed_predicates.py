"""Higher-order predicates are serializable hypotheses with checked semantics."""
import importlib.util
from itertools import permutations
from types import SimpleNamespace
import unittest

from steam_layout.model import Layout
from steam_layout.timed_facts import Fact, FactCatalogue
from steam_layout.timed_model import TimedModel
from steam_layout.timed_predicates import FactExclusion, RequiresBelowAny, RequiresBetweenAny
from test_audit_inheritance import act, add, build, remove

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.timed_envelope import TimedEnvelope


def catalogue_fixture():
    runtime = TimedModel(Layout(build({
        "Base": {"switch": ("switches", {"left_bumper": act(add("A"))})},
        "A": {"switch": ("switches", {"left_bumper": act(add("B"))})},
        "B": {"switch": ("switches", {"left_bumper": act(add("C"))})}, "C": {}})))
    return FactCatalogue(runtime)


class TimedPredicateDataTests(unittest.TestCase):
    def test_between_members_are_canonical_and_data_round_trips(self):
        predicate = RequiresBetweenAny(4, 1, [3, 2, 3])
        self.assertEqual(predicate.members, (2, 3))
        self.assertEqual(RequiresBetweenAny.from_data(predicate.to_data()), predicate)
        self.assertEqual(predicate.dependencies(), ({1, 2, 3, 4}, set()))
        self.assertIn("between", predicate.describe(SimpleNamespace(layer_names=("Base", "Y", "A", "B", "X"))))

    def test_between_condition_is_vacuous_without_the_ordered_pair(self):
        predicate = RequiresBetweenAny(4, 1, (2, 3))
        for ranks, expected in (((1, 2, 0, 0, 0), True), ((1, 0, 0, 0, 2), True),
                                ((1, 3, 0, 0, 2), True), ((1, 2, 0, 0, 3), False),
                                ((1, 2, 3, 0, 4), True), ((1, 2, 0, 3, 4), True),
                                ((1, 3, 2, 0, 4), False), ((1, 2, 4, 0, 3), False)):
            self.assertEqual(predicate.holds(ranks), expected, ranks)

    def test_between_rejects_malformed_endpoints_members_and_payloads(self):
        for x, y, members in ((True, 1, (2,)), (3, -1, (2,)), (3, 3, (2,)),
                              (3, 1, ()), (3, 1, (1,)), (3, 1, (3,)),
                              (3, 1, (False,)), (3, 1, (-1,)), (3, 1, "2")):
            with self.subTest(x=x, y=y, members=members), self.assertRaises(ValueError):
                RequiresBetweenAny(x, y, members)
        valid = RequiresBetweenAny(3, 0, (1, 2)).to_data()
        for payload in ({}, {**valid, "kind": "requires_below_any"}, {**valid, "verified": True}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                RequiresBetweenAny.from_data(payload)

    def test_members_are_canonical_and_serialization_round_trips(self):
        predicate = RequiresBelowAny(3, [2, 1, 2])
        self.assertEqual(predicate.members, (1, 2))
        self.assertEqual(RequiresBelowAny.from_data(predicate.to_data()), predicate)
        self.assertEqual(predicate.dependencies(), ({1, 2, 3}, set()))
        self.assertEqual(predicate.kind, "requires_below_any")
        self.assertEqual(predicate.describe(SimpleNamespace(layer_names=("Base", "A", "B", "C"))),
                         "C requires at least one of [A, B] below it")

    def test_presence_and_relative_order_are_both_required(self):
        predicate = RequiresBelowAny(3, (1, 2))
        for ranks, expected in (((1, 0, 0, 0), True), ((1, 2, 0, 3), True),
                                ((1, 0, 2, 3), True), ((1, 3, 0, 2), False),
                                ((1, 0, 0, 2), False), ((1, 3, 2, 4), True)):
            self.assertEqual(predicate.holds(ranks), expected)

    def test_malformed_predicates_fail_before_proof_use(self):
        for target, members in ((True, (1,)), (-1, (1,)), (3, ()), (3, "12"),
                                (3, (True,)), (3, (-1,)), (3, (3,))):
            with self.subTest(target=target, members=members), self.assertRaises(ValueError):
                RequiresBelowAny(target, members)
        for payload in ({}, {"kind": "absent", "x": 1, "members": [2]},
                        {"kind": "requires_below_any", "x": 1, "members": [2], "proved": True}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                RequiresBelowAny.from_data(payload)

    def test_fact_exclusion_resolves_canonical_definers_on_round_trip(self):
        catalogue = catalogue_fixture()
        j = catalogue.controls.index(("switch", "left_bumper"))
        original = catalogue._lookup[("inherit", 3, 1, j)]
        predicate = FactExclusion(original)
        restored = FactExclusion.from_data(predicate.to_data(), catalogue)
        self.assertIs(restored.fact, original)
        self.assertEqual(restored.x, 3)
        self.assertEqual(restored.dependencies(), ({0, 1, 2, 3}, set()))
        self.assertFalse(restored.holds((1, 2, 0, 3)))
        self.assertTrue(restored.holds((1, 2, 3, 4)))
        below = FactExclusion(catalogue._lookup[("below", 3, 1, -1)])
        self.assertEqual(below.dependencies(), ({1, 3}, set()))

    def test_fact_exclusion_rejects_malformed_or_non_catalogue_identities(self):
        catalogue = catalogue_fixture()
        for fact in ({"kind": "below", "x": True, "y": 1, "j": -1},
                     {"kind": "below", "x": 99, "y": 1, "j": -1},
                     {"kind": "inherit", "x": 3, "y": 1, "j": 99},
                     {"kind": "inherit", "x": 3, "y": 1, "j": 0, "definers": []}):
            with self.subTest(fact=fact), self.assertRaises(ValueError):
                FactExclusion.from_data({"kind": "fact_exclusion", "fact": fact}, catalogue)
        with self.assertRaises(ValueError):
            FactExclusion(Fact("inherit", 3, 1, 0))
        with self.assertRaises(ValueError):
            FactExclusion(object())


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedPredicateProofTests(unittest.TestCase):
    def test_between_formula_matches_every_small_ordered_stack(self):
        predicate = RequiresBetweenAny(4, 1, (2, 3))
        ranks = tuple(z3.Int(f"between_r_{i}") for i in range(5))
        for size in range(5):
            for suffix in permutations((1, 2, 3, 4), size):
                stack = (0, *suffix)
                values = tuple(3 * (stack.index(i) + 1) if i in stack else 0 for i in range(5))
                actual = z3.simplify(z3.substitute(predicate.formula(ranks),
                    *((rank, z3.IntVal(value)) for rank, value in zip(ranks, values))))
                self.assertEqual(z3.is_true(actual), predicate.holds(values), stack)

    def test_between_refinement_proves_family_and_rejects_missing_alternative(self):
        from steam_layout.timed_proof import TimedProof
        runtime = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": act([add("X"), add("A"), add("Y")]),
            "right_bumper": act([add("X"), add("B"), add("Y")])})},
            "Y": {}, "A": {}, "B": {}, "X": {}})))
        proof = TimedProof(runtime)
        proof.run().validate()
        good, bad = RequiresBetweenAny(4, 1, (2, 3)), RequiresBetweenAny(4, 1, (2,))
        refined = proof.refine((good, bad))
        self.assertIn(good, refined.invariants)
        self.assertNotIn(bad, refined.invariants)
        self.assertTrue(refined.validate()["verified"])
        for invalid in (RequiresBetweenAny(99, 1, (2,)), RequiresBetweenAny(4, 99, (2,)),
                        RequiresBetweenAny(4, 1, (99,))):
            with self.assertRaisesRegex(ValueError, "unknown layer"):
                proof.refine((invalid,))

    def test_formula_matches_every_small_ordered_stack(self):
        predicate = RequiresBelowAny(3, (1, 2))
        ranks = tuple(z3.Int(f"r_{i}") for i in range(4))
        for size in range(4):
            for suffix in permutations((1, 2, 3), size):
                stack = (0, *suffix)
                values = tuple(stack.index(i) + 1 if i in stack else 0 for i in range(4))
                actual = z3.simplify(z3.substitute(predicate.formula(ranks),
                                                  *((rank, z3.IntVal(value)) for rank, value in zip(ranks, values))))
                self.assertEqual(z3.is_true(actual), predicate.holds(values))

    def test_fact_exclusion_formula_matches_every_small_ordered_stack(self):
        catalogue = catalogue_fixture()
        j = catalogue.controls.index(("switch", "left_bumper"))
        ranks = tuple(z3.Int(f"fact_r_{i}") for i in range(4))
        for key in (("inherit", 3, 1, j), ("inherit", 3, -1, j), ("below", 3, 1, -1)):
            predicate = FactExclusion(catalogue._lookup[key])
            for size in range(4):
                for suffix in permutations((1, 2, 3), size):
                    stack = (0, *suffix)
                    values = tuple(stack.index(i) + 1 if i in stack else 0 for i in range(4))
                    actual = z3.simplify(z3.substitute(predicate.formula(ranks),
                                                      *((rank, z3.IntVal(value)) for rank, value in zip(ranks, values))))
                    self.assertEqual(z3.is_true(actual), predicate.holds(values), (key, stack))

    def test_swap_family_predicate_has_checked_initialization_and_preservation(self):
        data = build({"Base": {"switch": ("switches", {
            "always_on_action": act([add("C"), add("A")]),
            "left_bumper": act([add("C"), add("A")]),
            "right_bumper": act([add("C"), add("B"), remove("A"), remove("C")])})},
            "A": {}, "B": {}, "C": {}})
        runtime = TimedModel(Layout(data))
        envelope = TimedEnvelope(runtime)
        predicate = RequiresBelowAny(3, (1, 2))
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.start, z3.Not(predicate.formula(envelope.ranks)))
        self.assertEqual(solver.check(), z3.unsat)
        self.assertTrue(any(3 in state.stack for state in runtime.start()))
        for transition in envelope.project_transitions(predicate.dependencies()[0]):
            solver = z3.Solver()
            solver.add(envelope.domain, predicate.formula(envelope.ranks), transition.guard,
                       z3.Not(predicate.formula(transition.ranks)))
            self.assertEqual(solver.check(), z3.unsat, transition.label)

    def test_bad_family_predicate_is_rejected_by_inductive_check(self):
        runtime = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": act(add("C"))})}, "A": {}, "B": {}, "C": {}})))
        envelope = TimedEnvelope(runtime)
        predicate = RequiresBelowAny(3, (1, 2))
        transition = next(t for t in envelope.project_transitions({1, 2, 3}) if t.label == "press")
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.start, transition.guard,
                   z3.Not(predicate.formula(transition.ranks)))
        self.assertEqual(solver.check(), z3.sat)


if __name__ == "__main__":
    unittest.main()
