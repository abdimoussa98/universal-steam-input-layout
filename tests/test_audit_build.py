"""Candidate audits must receive their own rules and explicit baseline."""
import contextlib
import io
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from tools import audit_build


class AuditBuildOptions(unittest.TestCase):
    def test_each_audit_receives_only_its_supported_candidate_options(self):
        argv = ['audit_build', 'candidate.json', '--rules', 'candidate-rules.json', '--baseline', 'baseline.json']
        with patch('sys.argv', argv), patch.object(audit_build.subprocess, 'run', return_value=SimpleNamespace(
                returncode=0, stdout='', stderr='')) as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit_build.main(), 0)
        arguments = {c.args[0][2]: c.args[0][3:] for c in run.call_args_list}
        self.assertEqual(arguments['tools.audit_command_budget'], ['candidate.json'])
        self.assertEqual(arguments['tools.audit_inheritance'], ['candidate.json', '--register', 'candidate-rules.json'])
        self.assertEqual(arguments['tools.audit_flow_inheritance'],
                         ['candidate.json', '--config', 'candidate-rules.json', '--baseline', 'baseline.json'])
        self.assertEqual(arguments['tools.audit_cleanups'],
                         ['candidate.json', '--rules', 'candidate-rules.json', '--baseline', 'baseline.json'])

    def test_baseline_cannot_silently_apply_to_multiple_variants(self):
        with patch('sys.argv', ['audit_build', 'default.json', 'alternative.json', '--baseline', 'default-old.json']), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stopped:
            audit_build.main()
        self.assertEqual(stopped.exception.code, 2)
