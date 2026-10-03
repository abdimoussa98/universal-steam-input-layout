"""Complete full-stack fact projection and positive timed witness checks."""
from dataclasses import replace
import importlib.util
import itertools
import unittest

from steam_layout.model import Layout
from steam_layout.timed_facts import Fact, FactCatalogue, FactWitnesses
from steam_layout.timed_model import TimedModel
from test_audit_inheritance import act, add, build
from test_timed_report import A, LB, RB, sample_model


class TimedFactTests(unittest.TestCase):
    def setUp(self):
        self.model = sample_model()
        self.catalogue = FactCatalogue(self.model)

    def test_catalogue_covers_every_static_relation_and_inheritance_choice(self):
        catalogue = self.catalogue
        n = len(catalogue.names)
        self.assertEqual(sum(f.kind == 'below' for f in catalogue.facts), n * (n - 1))
        self.assertEqual(len(set(catalogue.facts)), len(catalogue.facts))
        x = self.model.spec.index['X']
        controls = {catalogue.controls[f.j] for f in catalogue.facts
                    if f.kind == 'inherit' and f.x == x}
        self.assertNotIn(('dpad', 'dpad_east'), controls)
        self.assertNotIn(('left_trackpad', 'click'), controls)
        self.assertIn(A, controls)
        north = catalogue.controls.index(('dpad', 'dpad_north'))
        values = [catalogue.valuesmetadata(f) for f in catalogue.facts
                  if f.kind == 'inherit' and f.x == x and f.j == north]
        self.assertEqual({(v['owner'], v['blocked_by']) for v in values},
                         {('Base', None), ('Above', None), (None, 'Lower'), (None, None)})
        self.assertEqual(next(v['activators'] for v in values if v['owner'] == 'Base'),
                         act('key_press W, , '))

    def test_prefix_projection_matches_all_predicates_on_every_stack(self):
        n = len(self.catalogue.names)
        for length in range(n):
            for suffix in itertools.permutations(range(1, n), length):
                stack = (0, *suffix)
                expected = {f for f in self.catalogue.facts if f.holds(stack)}
                self.assertEqual(self.catalogue.facts_of(stack), expected)

    @unittest.skipUnless(importlib.util.find_spec('z3'), 'optional z3-solver is not installed')
    def test_symbolic_predicates_match_every_stack_with_rank_gaps(self):
        import z3
        n = len(self.catalogue.names)
        for length in range(n):
            for suffix in itertools.permutations(range(1, n), length):
                stack = (0, *suffix)
                ranks = tuple(z3.IntVal(3 * (stack.index(x) + 1) if x in stack else 0)
                              for x in range(n))
                for fact in self.catalogue.facts:
                    self.assertEqual(z3.is_true(z3.simplify(fact.formula(ranks))),
                                     fact.holds(stack), (fact, stack))

    def test_above_layer_does_not_change_lower_binding(self):
        ids = self.model.spec.index
        stack = (0, ids['Lower'], ids['X'], ids['Above'])
        north = self.catalogue.controls.index(('dpad', 'dpad_north'))
        fact = next(f for f in self.catalogue.facts_of(stack)
                    if f.kind == 'inherit' and f.x == ids['X'] and f.j == north)
        self.assertEqual(self.catalogue.valuesmetadata(fact)['blocked_by'], 'Lower')
        self.assertIn(Fact('below', ids['Above'], ids['X']), self.catalogue.facts_of(stack))

    def test_invalid_stack_and_metadata_requests_fail(self):
        for stack in ((), (1, 0), (0, 1, 1), (0, 900)):
            with self.assertRaises(ValueError):
                self.catalogue.facts_of(stack)
        with self.assertRaises(ValueError):
            self.catalogue.valuesmetadata(Fact('below', 1, 0))

    def test_witnesses_replay_paths_and_reject_fabricated_edges(self):
        witnesses = FactWitnesses(self.model, self.catalogue)
        final = witnesses.add_trace([{'press': list(RB)}, {'press': list(LB)}, {'press': list(A)}])
        self.assertEqual(len(final), 1)
        for fact in witnesses.facts:
            self.assertTrue(witnesses.verify(fact))
        ids = self.model.spec.index
        fact = Fact('below', ids['Above'], ids['X'])
        self.assertEqual(witnesses.trace(fact),
                         [{'press': list(RB)}, {'press': list(LB)}, {'press': list(A)}])
        root = witnesses.roots[0]
        invalid = replace(witnesses.node_states[root], stack=(0, ids['Unreachable']))
        with self.assertRaisesRegex(ValueError, 'does not replay'):
            witnesses.record(root, invalid, {'press': list(LB)})
        with self.assertRaisesRegex(ValueError, 'no timed witness'):
            witnesses.verify(Fact('below', ids['Unreachable'], 0))

    def test_witnesses_keep_all_command_order_branches(self):
        model = TimedModel(Layout(build({
            'Base': {'switch': ('switches', {'left_bumper': {'Full_Press': [
                {'bindings': {'binding': add('One')}},
                {'bindings': {'binding': add('Two')}}]}})}, 'One': {}, 'Two': {}})))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        final = witnesses.add_trace([{'press': list(LB)}])
        self.assertEqual({witnesses.node_states[n].stack for n in final}, {(0, 1, 2), (0, 2, 1)})
        for fact in (Fact('below', 1, 2), Fact('below', 2, 1)):
            self.assertIn(fact, witnesses.facts)
            self.assertTrue(witnesses.verify(fact))

    def test_timed_wait_trace_compaction_and_model_identity(self):
        model = TimedModel(Layout(build({
            'Base': {'switch': ('switches', {'left_bumper': {'Full_Press': {
                'bindings': {'binding': add('Delayed')}, 'settings': {'delay_start': '3'}}}})},
            'Delayed': {}})))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        witnesses.add_trace([{'press': list(LB)}, {'wait_ms': 1}, {'wait_ms': 2}])
        fact = Fact('below', 1, 0)
        self.assertEqual(witnesses.trace(fact), [{'press': list(LB)}, {'wait_ms': 3}])
        self.assertTrue(witnesses.verify(fact))
        with self.assertRaisesRegex(ValueError, 'same TimedModel'):
            FactWitnesses(self.model, catalogue)
