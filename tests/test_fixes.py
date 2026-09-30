"""The post-install fix pipeline (steam_layout.fixes)."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.fixes import PIPELINE, apply_all

ROOT = Path(__file__).resolve().parents[1]


def load(variant):
    return json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text())


class PipelineTests(unittest.TestCase):
    def test_pipeline_order(self):
        self.assertEqual([name for name, _ in PIPELINE],
                         ["rtp_scroll", "dead_groups", "cover_resets", "transition_set_0",
                          "window_pads", "window_routes"])

    def test_working_layouts_are_a_fixed_point(self):
        # Every fix has already been applied: running the pipeline again changes nothing.
        for variant in ("default", "alternative"):
            data = load(variant)
            before = copy.deepcopy(data)
            with self.subTest(variant=variant):
                apply_all(data)
                self.assertEqual(data, before)

    def test_cli_dry_run_reports_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "layout.json")
            path.write_text(json.dumps(load("default")))
            before = path.read_text()
            out = subprocess.run([sys.executable, "-m", "steam_layout.fixes", str(path), "--dry-run"],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("window_routes", out.stdout)
            self.assertEqual(path.read_text(), before)


if __name__ == "__main__":
    unittest.main()
