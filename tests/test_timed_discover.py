"""Witness sampling is replayable and resumable, without claiming completeness."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.timed_discover import (candidate_events, compact_archive, discover,
                                         discover_from_untimed, import_search,
                                         load_witnesses, save_witnesses)
from steam_layout.timed_facts import Fact, FactCatalogue, FactWitnesses
from steam_layout.timed_model import TimedModel
from steam_layout.timed_search import run_search
from steam_layout.timed_store import TimedStore
from test_audit_inheritance import act, add, build


def fixture():
    return TimedModel(Layout(build({
        'Base': {'switch': ('switches', {
            'left_bumper': act(add('One')),
            'right_bumper': {'Full_Press': {
                'bindings': {'binding': add('Two')}, 'settings': {'delay_start': '3'}}}})},
        'One': {}, 'Two': {}})))


class TimedDiscoverTests(unittest.TestCase):
    def setUp(self):
        self.model = fixture()
        self.catalogue = FactCatalogue(self.model)
        self.witnesses = FactWitnesses(self.model, self.catalogue)

    def test_sampled_facts_have_verified_witnesses_and_no_completion_claim(self):
        report = discover(self.witnesses, seconds=None, max_steps=120, seed=19)
        self.assertFalse(report['complete_for_model'])
        self.assertEqual(report['sampled_events'], 120)
        self.assertEqual(set(report['reached_layers']), {'Base', 'One', 'Two'})
        self.assertIn(Fact('below', 1, 0), self.witnesses.facts)
        self.assertIn(Fact('below', 2, 0), self.witnesses.facts)
        for fact in self.witnesses.facts:
            self.assertTrue(self.witnesses.verify(fact))

    def test_candidates_jump_to_delayed_add_and_just_before_it(self):
        nodes = self.witnesses.add_trace([{'press': ['switch', 'right_bumper']}])
        state = self.witnesses.node_states[next(iter(nodes))]
        events = list(candidate_events(self.witnesses, state))
        self.assertIn({'wait_ms': 3}, events)
        self.assertIn({'wait_ms': 2}, events)
        self.assertNotIn({'press': ['switch', 'right_bumper']}, events)
        self.assertIn({'release': ['switch', 'right_bumper']}, events)

    def test_transactional_save_resume_and_continue(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'witnesses.sqlite'
            discover(self.witnesses, seconds=None, max_steps=30)
            save_witnesses(self.witnesses, path)
            restored = load_witnesses(self.model, self.catalogue, path)
            self.assertEqual(restored.facts, self.witnesses.facts)
            self.assertEqual(dict(restored.node_states), dict(self.witnesses.node_states))
            discover(restored, seconds=None, max_steps=30, seed=2)
            save_witnesses(restored, path)
            resumed = load_witnesses(self.model, self.catalogue, path)
            self.assertEqual(resumed.facts, restored.facts)
            for fact in resumed.facts:
                self.assertTrue(resumed.verify(fact))

    def test_corrupt_event_and_wrong_model_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'witnesses.sqlite'
            self.witnesses.add_trace([{'press': ['switch', 'left_bumper']}])
            save_witnesses(self.witnesses, path)
            other = TimedModel(Layout(build({'Base': {}, 'Other': {}})))
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                load_witnesses(other, FactCatalogue(other), path)
            with sqlite3.connect(path) as connection:
                connection.execute('UPDATE nodes SET event = ? WHERE id = 1',
                                   (json.dumps({'wait_ms': 0}),))
            with self.assertRaisesRegex(ValueError, 'does not replay'):
                load_witnesses(self.model, self.catalogue, path)

    def test_compaction_preserves_facts_and_replays_needed_ancestors(self):
        with tempfile.TemporaryDirectory() as directory:
            original, compact = (Path(directory) / name for name in ('original.sqlite', 'compact.sqlite'))
            discover(self.witnesses, seconds=None, max_steps=200, seed=39)
            save_witnesses(self.witnesses, original)
            restored = compact_archive(self.model, self.catalogue, original, compact)
            self.assertEqual(restored.facts, self.witnesses.facts)
            self.assertLess(len(restored.node_states), len(self.witnesses.node_states))
            self.assertEqual(load_witnesses(self.model, self.catalogue, compact).facts, restored.facts)

    def test_import_existing_search_replays_all_parent_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'search.sqlite'
            quotient = self.witnesses.quotient
            with TimedStore(path, self.model, quotient.identity) as store:
                run_search(quotient, store, max_states=60)
                count = store.count
            imported = import_search(self.witnesses, path)
            self.assertEqual(imported, count)
            self.assertEqual(len(self.witnesses.node_states), count)
            for fact in self.witnesses.facts:
                self.assertTrue(self.witnesses.verify(fact))

    def test_resource_budget_required(self):
        with self.assertRaises(ValueError):
            discover(self.witnesses, seconds=None)
        for kwargs in ({'seconds': 0}, {'seconds': float('inf')}, {'seconds': float('nan')},
                       {'max_steps': 0}, {'fanout': 0}):
            with self.assertRaises(ValueError):
                discover(self.witnesses, **kwargs)

    def test_untimed_hints_gain_facts_only_through_concrete_timed_replay(self):
        class Hints:
            _under, _below, _top = {'suggestion': 0}, {}, {}

            def stack(self, gid):
                return ('Base', 'Two', 'One')

            def witness(self, gid):
                return [('start', ('Base',)),
                        ('press: switch/right_bumper', ('Base',)),
                        ('hold: switch/right_bumper', ('Base', 'Two')),
                        ('press: switch/left_bumper', ('Base', 'Two', 'One'))]

        result = discover_from_untimed(self.witnesses, Hints(), seconds=2)
        fact = Fact('below', 1, 2)
        self.assertGreater(result['new_facts'], 0)
        self.assertFalse(result['complete_for_model'])
        self.assertTrue(self.witnesses.verify(fact))
        self.assertEqual(self.witnesses.trace(fact), [
            {'press': ['switch', 'right_bumper']}, {'wait_ms': 3},
            {'press': ['switch', 'left_bumper']}])

    def test_unreplayable_old_claim_is_not_imported_as_a_fact(self):
        class Hints:
            _under, _below, _top = {'wrong-claim': 0}, {}, {}

            def stack(self, gid):
                return ('Base', 'Two')

            def witness(self, gid):
                return [('start', ('Base',)),
                        ('press: switch/left_bumper', ('Base', 'Two'))]

        discover_from_untimed(self.witnesses, Hints(), seconds=2)
        self.assertNotIn(Fact('below', 2, 0), self.witnesses.facts)
        self.assertIn(Fact('below', 1, 0), self.witnesses.facts)
