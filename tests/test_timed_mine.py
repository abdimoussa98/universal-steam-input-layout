"""Sample-derived family covers are minimal hypotheses, never proofs."""
import contextlib
import io
import itertools
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from steam_layout.model import Layout
from steam_layout.timed_discover import save_witnesses
from steam_layout.timed_facts import FactCatalogue, FactWitnesses
from steam_layout.timed_mine import (_Budget, _hitting_sets, _minimal_prefixes,
                                    main, mine_below_families)
from steam_layout.timed_model import TimedModel
from steam_layout.timed_predicates import RequiresBelowAny
from test_audit_inheritance import act, add, build


def fixture():
    data = build({
        'Base': {'switch': ('switches', {'left_bumper': act(add('A')),
                                         'right_bumper': act(add('B'))}),
                 'button_diamond': ('four_buttons', {'button_a': act(add('X'))})},
        'A': {}, 'B': {}, 'X': {}, 'Never': {}})
    model = TimedModel(Layout(data))
    witnesses = FactWitnesses(model, FactCatalogue(model))
    for control in ('left_bumper', 'right_bumper'):
        witnesses.add_trace([{'press': ['switch', control]},
                             {'press': ['button_diamond', 'button_a']}])
    return data, model, witnesses


def ranks(state, count):
    return tuple(state.stack.index(layer) + 1 if layer in state.stack else 0 for layer in range(count))


class TimedMineTests(unittest.TestCase):
    def test_alternative_lower_owners_form_one_minimal_family(self):
        _, model, witnesses = fixture()
        result = mine_below_families(witnesses)
        self.assertEqual(result.candidates, (RequiresBelowAny(3, (1, 2)),))
        for candidate in result.candidates:
            for state in witnesses.node_states.values():
                self.assertTrue(candidate.holds(ranks(state, len(model.spec.layer_names))))
        self.assertEqual(result.to_data()['validation'], 'unvalidated')
        self.assertFalse(result.to_data()['complete_for_model'])
        self.assertTrue(result.to_data()['enumeration_complete_for_samples'])
        self.assertFalse(mine_below_families(witnesses, max_members=1).candidates)

    def test_unseen_timed_trace_can_disprove_a_sampled_candidate(self):
        _, model, witnesses = fixture()
        candidate, = mine_below_families(witnesses).candidates
        final = witnesses.add_trace([{'press': ['button_diamond', 'button_a']}])
        self.assertTrue(any(not candidate.holds(ranks(witnesses.node_states[node], 5)) for node in final))
        refreshed = mine_below_families(witnesses)
        self.assertFalse(refreshed.candidates)
        self.assertFalse(refreshed.to_data()['complete_for_model'])

    def test_base_absent_layers_and_duplicate_prefixes_are_excluded(self):
        _, _, witnesses = fixture()
        first = mine_below_families(witnesses)
        witnesses.add_trace([{'press': ['switch', 'left_bumper']},
                             {'press': ['button_diamond', 'button_a']},
                             {'release': ['button_diamond', 'button_a']},
                             {'press': ['button_diamond', 'button_a']}])
        second = mine_below_families(witnesses)
        self.assertEqual(first.candidates, second.candidates)
        self.assertEqual(first.layers, second.layers)
        self.assertGreaterEqual(second.sampled_states, first.sampled_states)
        self.assertFalse(any(candidate.x in (0, 4) or 0 in candidate.members or
                             candidate.x in candidate.members for candidate in second.candidates))

    def test_hitting_set_generation_matches_independent_small_brute_force(self):
        masks = tuple(range(1, 16))
        for length in range(1, 4):
            for prefixes in itertools.combinations(masks, length):
                expected = {mask for mask in masks if bin(mask).count("1") <= 3 and
                            all(mask & prefix for prefix in prefixes) and
                            not any(other != mask and other & mask == other and
                                    all(other & prefix for prefix in prefixes) for other in masks)}
                found, complete = _hitting_sets(_minimal_prefixes(prefixes), 3, _Budget(10000, None))
                self.assertTrue(complete)
                self.assertEqual(set(found), expected, prefixes)

    def test_budget_stop_remains_unvalidated_and_keeps_only_minimal_covers(self):
        _, _, witnesses = fixture()
        stopped = mine_below_families(witnesses, max_search_nodes=1)
        self.assertEqual(stopped.search_nodes, 1)
        self.assertEqual(stopped.budget_exhausted, 'max_search_nodes')
        self.assertFalse(stopped.to_data()['enumeration_complete_for_samples'])
        self.assertFalse(stopped.to_data()['complete_for_model'])
        for limit in range(1, 10):
            found, _ = _hitting_sets((3, 6), 3, _Budget(limit, None))
            self.assertLessEqual(set(found), {2, 5})

    def test_payload_order_is_canonical_and_predicates_round_trip(self):
        _, _, witnesses = fixture()
        result = mine_below_families(witnesses)
        encoded = json.dumps(result.to_data(), sort_keys=True)
        self.assertEqual(encoded, json.dumps(mine_below_families(witnesses).to_data(), sort_keys=True))
        decoded = tuple(RequiresBelowAny.from_data(row) for row in json.loads(encoded)['candidates'])
        self.assertEqual(decoded, tuple(sorted(decoded)))
        self.assertEqual(decoded, result.candidates)

    def test_invalid_inputs_and_budgets_are_rejected(self):
        _, _, witnesses = fixture()
        with self.assertRaises(ValueError):
            mine_below_families([(0, 1)])
        for kwargs in ({'max_members': 0}, {'max_members': True}, {'max_search_nodes': 0},
                       {'max_search_nodes': 1.5}, {'seconds': 0}, {'seconds': True},
                       {'seconds': float('nan')}, {'seconds': float('inf')}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                mine_below_families(witnesses, **kwargs)

    def test_cli_replays_archive_and_rejects_input_aliases_before_work(self):
        data, _, witnesses = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout, archive, output = (root / name for name in ('layout.json', 'proof.sqlite', 'families.json'))
            layout.write_text(json.dumps(data))
            save_witnesses(witnesses, archive)
            before = {path: path.read_bytes() for path in (layout, archive)}
            alias = root / 'alias.json'
            os.link(archive, alias)
            for forbidden in (layout, archive, alias):
                with self.subTest(forbidden=forbidden), patch('steam_layout.timed_mine.TimedModel') as runtime:
                    with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stopped:
                        main([str(layout), str(archive), str(forbidden)])
                    self.assertEqual(stopped.exception.code, 2)
                    runtime.assert_not_called()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(layout), str(archive), str(output)]), 0)
            payload = json.loads(output.read_text())
            self.assertEqual(payload['validation'], 'unvalidated')
            self.assertEqual(payload['candidates'], [RequiresBelowAny(3, (1, 2)).to_data()])
            self.assertEqual({path: path.read_bytes() for path in before}, before)
            self.assertFalse(list(root.glob('.timed-mine-*')))
