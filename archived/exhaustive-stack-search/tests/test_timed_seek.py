"""Target sampling proves positives only and checks all archived evidence."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from steam_layout.model import Layout
from steam_layout.timed_discover import load_witnesses
from steam_layout.timed_facts import Fact, FactCatalogue, FactWitnesses
from steam_layout.timed_model import TimedModel
from steam_layout.timed_seek import main, parse_targets, save_compact, seek
from test_audit_inheritance import act, add, build


def fixture():
    data = build({
        'Base': {'switch': ('switches', {
            'left_bumper': act(add('One')),
            'right_bumper': {'Full_Press': {'bindings': {'binding': add('Two')},
                                          'settings': {'delay_start': '3'}}}})},
        'One': {}, 'Two': {}, 'Never': {}})
    model = TimedModel(Layout(data))
    catalogue = FactCatalogue(model)
    return data, model, catalogue, FactWitnesses(model, catalogue)


class TimedSeekTests(unittest.TestCase):
    def setUp(self):
        self.data, self.model, self.catalogue, self.witnesses = fixture()

    def test_target_parser_is_strict_and_restores_definer_context(self):
        fact = next(f for f in self.catalogue.facts if f.kind == 'inherit' and f.x == 1)
        row = [fact.kind, fact.x, fact.y, fact.j]
        parsed = parse_targets(self.catalogue, {'facts': [row, row]})
        self.assertEqual(parsed, (fact,))
        self.assertIs(parsed[0], fact)
        self.assertEqual(parse_targets(self.catalogue, {'facts': [row], 'scope': 'search hints'}), parsed)
        bad = [None, {'facts': [], 'unexpected': True}, [['below', True, 0, -1]],
               [['below', 1, 0]], [['below', 1, 1, -1]], [['below', 900, 0, -1]],
               [['inherit', 0, 0, 0]], [['above', 1, 0, -1]], [['below', 1, 0, 0]]]
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                parse_targets(self.catalogue, payload)

    def test_delayed_target_uses_valid_wait_and_every_fact_replays(self):
        target = Fact('below', 2, 1)
        report = seek(self.witnesses, [target], max_events=200)
        self.assertEqual(report['targets'][0]['status'], 'witnessed')
        self.assertIn({'wait_ms': 3}, self.witnesses.trace(target))
        self.assertFalse(report['complete_for_model'])
        for fact in self.witnesses.facts:
            self.assertTrue(self.witnesses.verify(fact))

    def test_single_event_budget_retains_every_command_order_outcome(self):
        model = TimedModel(Layout(build({
            'Base': {'switch': ('switches', {'left_bumper': {'Full_Press': [
                {'bindings': {'binding': add('One')}},
                {'bindings': {'binding': add('Two')}}]}})}, 'One': {}, 'Two': {}})))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        report = seek(witnesses, [Fact('below', 1, 2)], max_events=1)
        self.assertEqual(report['sampled_events'], 1)
        for target in (Fact('below', 1, 2), Fact('below', 2, 1)):
            self.assertTrue(witnesses.verify(target))

    def test_unreachable_target_stays_unresolved_and_budget_is_exact(self):
        target = Fact('below', 3, 0)
        report = seek(self.witnesses, [target], max_events=7)
        self.assertEqual(report['sampled_events'], 7)
        self.assertEqual(report['targets'][0]['status'], 'unresolved')
        self.assertNotIn(target, self.witnesses.facts)
        self.assertFalse(report['complete_for_model'])
        self.assertNotIn('excluded', report)

    def test_missing_budget_and_bad_values_fail_before_search(self):
        for kwargs in ({}, {'seconds': 0}, {'seconds': True}, {'seconds': float('nan')},
                       {'seconds': float('inf')}, {'max_events': True}, {'max_events': 0},
                       {'max_events': 2, 'per_target_events': 0},
                       {'max_events': 2, 'max_frontier': -1},
                       {'max_events': 2, 'per_target_seconds': -1},
                       {'max_events': 2, 'seed_limit': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                seek(self.witnesses, [], **kwargs)
        with self.assertRaises(ValueError):
            seek(self.witnesses, [Fact('below', True, 0)], max_events=1)
        with self.assertRaises(ValueError):
            seek(self.witnesses, [['below', 1, 0, -1]], max_events=1)

    def test_inheritance_uses_closest_lower_definer_including_blockers(self):
        model = TimedModel(Layout(build({
            'Base': {'switch': ('switches', {'left_bumper': act(add('Lower')),
                                             'right_bumper': act(add('X'))}),
                     'dpad': ('dpad', {'dpad_north': act('key_press W, , ')})},
            'Lower': {'dpad': ('disabled', {})}, 'X': {}})))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        control = catalogue.controls.index(('dpad', 'dpad_north'))
        target = Fact('inherit', 2, 1, control)
        report = seek(witnesses, [target], max_events=200)
        self.assertEqual(report['targets'][0]['status'], 'witnessed')
        self.assertTrue(witnesses.verify(target))
        self.assertEqual(catalogue.valuesmetadata(target)['blocked_by'], 'Lower')

    def test_search_can_remove_an_intervening_definer_from_an_existing_seed(self):
        remove = 'controller_action remove_layer {{Blocker}}, , '
        model = TimedModel(Layout(build({
            'Base': {'switch': ('switches', {'left_bumper': act(add('Owner')),
                                             'right_bumper': act(add('Blocker'))}),
                     'button_diamond': ('four_buttons', {'button_a': act(add('X'))})},
            'Owner': {'dpad': ('dpad', {'dpad_north': act('key_press W, , ')})},
            'Blocker': {'dpad': ('disabled', {}),
                        'button_diamond': ('four_buttons', {'button_b': act(remove)})},
            'X': {}})))
        catalogue = FactCatalogue(model)
        witnesses = FactWitnesses(model, catalogue)
        witnesses.add_trace([{'press': ['switch', 'left_bumper']},
                             {'press': ['switch', 'right_bumper']},
                             {'press': ['button_diamond', 'button_a']}])
        j = catalogue.controls.index(('dpad', 'dpad_north'))
        target = Fact('inherit', 3, 1, j)
        self.assertNotIn(target, witnesses.facts)
        report = seek(witnesses, [target], max_events=1)
        self.assertEqual(report['targets'][0]['status'], 'witnessed')
        self.assertEqual(witnesses.trace(target)[-1], {'press': ['button_diamond', 'button_b']})
        self.assertTrue(witnesses.verify(target))

    def test_compact_archive_can_replace_itself_and_cli_resumes_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout, targets, archive = (root / name for name in ('layout.json', 'targets.json', 'proof.sqlite'))
            layout.write_text(json.dumps(self.data))
            targets.write_text(json.dumps({'facts': [['below', 2, 1, -1]]}))
            seek(self.witnesses, [Fact('below', 1, 0)], max_events=10)
            saved = save_compact(self.witnesses, archive)
            save_compact(saved, archive)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = main([str(layout), str(targets), str(archive), '--input-archive',
                               str(archive), '--max-events', '200'])
            self.assertEqual(result, 0)
            restored = load_witnesses(self.model, self.catalogue, archive)
            self.assertTrue(restored.verify(Fact('below', 2, 1)))
            report = json.loads(Path(str(archive) + '.summary.json').read_text())
            self.assertFalse(report['complete_for_model'])
            self.assertEqual(report['archive_states'], len(restored.node_states))
            self.assertFalse(list(root.glob('.timed-seek-*')))

    def test_cli_rejects_output_aliases_before_work_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout, targets = root / 'layout.json', root / 'targets.json'
            layout.write_text(json.dumps(self.data))
            targets.write_text('[]')
            symbolic, hard = root / 'symbolic.json', root / 'hard.json'
            symbolic.symlink_to(layout)
            os.link(targets, hard)
            before = {path: path.read_bytes() for path in (layout, targets, symbolic, hard)}
            for output in (layout, targets, symbolic, hard):
                with self.subTest(output=output), patch('steam_layout.timed_seek.TimedModel') as runtime:
                    errors = io.StringIO()
                    with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as stopped:
                        main([str(layout), str(targets), str(output), '--max-events', '1'])
                    self.assertEqual(stopped.exception.code, 2)
                    self.assertIn('output must not alias', errors.getvalue())
                    runtime.assert_not_called()
                    self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_cli_rejects_summary_aliases_including_default_before_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout, targets, archive, output = (root / name for name in
                                                ('layout.json', 'targets.json', 'input.sqlite', 'output.sqlite'))
            layout.write_text(json.dumps(self.data))
            targets.write_text('[]')
            archive.write_bytes(b'existing input archive')
            output.write_bytes(b'existing output archive')
            alias = root / 'summary.json'
            os.link(archive, alias)
            before = {path: path.read_bytes() for path in (layout, targets, archive, output, alias)}
            for summary in (layout, targets, archive, output, alias):
                with self.subTest(summary=summary), patch('steam_layout.timed_seek.TimedModel') as runtime:
                    errors = io.StringIO()
                    with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as stopped:
                        main([str(layout), str(targets), str(output), '--input-archive', str(archive),
                              '--summary', str(summary), '--max-events', '1'])
                    self.assertEqual(stopped.exception.code, 2)
                    self.assertIn('summary must not alias', errors.getvalue())
                    runtime.assert_not_called()
                    self.assertEqual({path: path.read_bytes() for path in before}, before)
            default_summary = Path(str(output) + '.summary.json')
            default_summary.symlink_to(archive)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stopped:
                main([str(layout), str(targets), str(output), '--input-archive', str(archive),
                      '--max-events', '1'])
            self.assertEqual(stopped.exception.code, 2)
            self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_corrupt_sqlite_archive_has_a_normal_cli_error_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout, targets, archive, output = (root / name for name in
                                                ('layout.json', 'targets.json', 'broken.sqlite', 'output.sqlite'))
            layout.write_text(json.dumps(self.data))
            targets.write_text('[]')
            archive.write_bytes(b'this is not a SQLite database')
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as stopped:
                main([str(layout), str(targets), str(output), '--input-archive', str(archive),
                      '--max-events', '1'])
            self.assertEqual(stopped.exception.code, 2)
            self.assertIn('error:', errors.getvalue())
            self.assertNotIn('Traceback', errors.getvalue())
            self.assertFalse(output.exists())
            self.assertEqual(archive.read_bytes(), b'this is not a SQLite database')
