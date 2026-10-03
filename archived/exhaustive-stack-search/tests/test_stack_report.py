"""Exercise the public report command with actual search evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from steam_layout.held_model import HeldModel
from steam_layout.stackdb import build_engine
from test_stack_evidence import layout


@unittest.skipUnless(importlib.util.find_spec("z3") and shutil.which("clang++"),
                     "needs optional z3-solver and clang++")
class ReportTests(unittest.TestCase):
    def test_cli_completes_small_layout_with_replayed_witnesses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            data = layout()
            layout_path = path / "layout.json"
            layout_path.write_text(json.dumps({"controller_mappings": data.cm}))
            model = HeldModel(data)
            model.write_held(path / "model.txt")
            subprocess.run([str(build_engine()), str(path / "model.txt"), directory,
                            "--held", "--threads", "1"], capture_output=True, check=True)
            command = [sys.executable, "-m", "steam_layout.stackdb", "show", "X",
                       "--layout", str(layout_path), "--search", directory, "--json"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["complete_for_model"])
            self.assertEqual(report["counts"]["possible"], 0)
            self.assertGreater(report["counts"]["excluded"], 0)
            self.assertEqual({r["layer"] for r in report["below"]}, {"Base", "Lower"})
            self.assertEqual({r["layer"] for r in report["above"]}, {"Above"})
            values = next(r["values"] for r in report["inherited"] if r["input"] == "dpad_north")
            self.assertEqual({(v["owner"], v["blocked_by"]) for v in values},
                             {("Base", None), (None, "Lower")})
            self.assertTrue(all(v["status"] == "proven" and v["witness"] is not None for v in values))


if __name__ == "__main__":
    unittest.main()
