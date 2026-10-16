"""Release retry compatibility: pre-migration tags keep an explicit legacy gate.

Synthetic tagged selections and subprocess outcomes verify that neither failed
legacy shards nor legacy completion records can masquerade as modern evidence.
"""
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import test_compat


class TaggedTestCompatibility(unittest.TestCase):
    def test_legacy_merge_requires_commit_run_exact_partition_and_all_four_shards(self):
        root = Path("fixture")
        selected = lambda root, index, count: [f"tests.test_{index}"]
        def output(root, *args):
            return "commit" if args[:2] == ("git", "rev-parse") else " ".join(f"tests.test_{i}" for i in range(1, 5))
        with patch.object(test_compat, "modules", side_effect=selected), patch.object(test_compat, "output", side_effect=output):
            records = [test_compat.legacy_record(root, i, 4, "run", selected(root, i, 4)) for i in range(1, 5)]
            test_compat.validate_legacy(records, root, "run")
            mutations = [records[:-1], [records[0]] * 4]
            for field, value in (("head", "older"), ("run_id", "other"), ("successful", False),
                                 ("schema", 1), ("modules", ["tests.wrong"]), ("count", 3)):
                changed = copy.deepcopy(records)
                changed[0][field] = value
                mutations.append(changed)
            for changed in mutations:
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    test_compat.validate_legacy(changed, root, "run")

    def test_legacy_failure_writes_no_success_record(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            artifact = root / "part.json"
            with patch.object(test_compat, "modules", return_value=["tests.test_one"]), \
                    patch.object(test_compat.subprocess, "call", return_value=1):
                self.assertEqual(test_compat.main(["run", "--root", folder, "--shard", "1", "4",
                                                  "--evidence", str(artifact), "--run-id", "run"]), 1)
            self.assertFalse(artifact.exists())

    def test_successful_legacy_execution_records_only_its_assigned_modules(self):
        with tempfile.TemporaryDirectory() as folder:
            artifact = Path(folder) / "part.json"
            with patch.object(test_compat, "modules", return_value=["tests.test_one"]), \
                    patch.object(test_compat, "output", return_value="commit"), \
                    patch.object(test_compat.subprocess, "call", return_value=0) as execute:
                self.assertEqual(test_compat.main(["run", "--root", folder, "--shard", "1", "4",
                                                  "--evidence", str(artifact), "--run-id", "run"]), 0)
            self.assertEqual(execute.call_args.args[0][-3:], ["-m", "unittest", "tests.test_one"])
            record = json.loads(artifact.read_text())
            self.assertEqual((record["schema"], record["modules"], record["head"]),
                             ("legacy-unittest-1", ["tests.test_one"], "commit"))

    def test_modern_execution_delegates_to_the_evidence_runner(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tests").mkdir()
            (root / "tests/runner.py").touch()
            with patch.object(test_compat.subprocess, "call", return_value=3) as execute:
                self.assertEqual(test_compat.main(["run", "--root", folder, "--shard", "2", "4",
                                                  "--evidence", "part.json", "--run-id", "run"]), 3)
            self.assertEqual(execute.call_args.args[0][1:4], ["-m", "tests.runner", "--shard"])

    def test_artifact_paths_resolve_from_the_caller_for_both_tagged_trees(self):
        for modern in (False, True):
            with self.subTest(modern=modern), tempfile.TemporaryDirectory() as folder:
                root, caller = Path(folder) / "tagged", Path(folder) / "caller"
                root.mkdir()
                caller.mkdir()
                if modern:
                    (root / "tests").mkdir()
                    (root / "tests/runner.py").touch()
                previous = Path.cwd()
                try:
                    os.chdir(caller)
                    artifact = (caller / "artifacts/part.json").resolve()
                    with patch.object(test_compat, "modules", return_value=["tests.test_one"]), \
                            patch.object(test_compat, "output", return_value="commit"), \
                            patch.object(test_compat.subprocess, "call", return_value=0) as execute:
                        self.assertEqual(test_compat.main([
                            "run", "--root", str(root), "--shard", "1", "4",
                            "--evidence", "artifacts/part.json", "--run-id", "run"]), 0)
                    self.assertEqual(execute.call_args.kwargs["cwd"], root.resolve())
                    if modern:
                        command = execute.call_args.args[0]
                        self.assertEqual(command[command.index("--evidence") + 1], str(artifact))
                        artifact.parent.mkdir()
                        artifact.write_text('{"fixture": "modern"}')
                    else:
                        self.assertTrue(artifact.is_file())
                    self.assertFalse((root / "artifacts/part.json").exists())

                    with patch.object(test_compat, "validate_legacy") as validate, \
                            patch.object(test_compat.subprocess, "call", return_value=0) as execute, \
                            patch("sys.stdout", new_callable=io.StringIO):
                        self.assertEqual(test_compat.main([
                            "finalize", "artifacts/part.json", "--root", str(root), "--run-id", "run"]), 0)
                    if modern:
                        command = execute.call_args.args[0]
                        self.assertEqual(command[command.index("--finalize") + 1], str(artifact))
                        self.assertEqual(execute.call_args.kwargs["cwd"], root.resolve())
                        validate.assert_not_called()
                    else:
                        validate.assert_called_once_with([json.loads(artifact.read_text())], root.resolve(), "run")
                        execute.assert_not_called()
                finally:
                    os.chdir(previous)
