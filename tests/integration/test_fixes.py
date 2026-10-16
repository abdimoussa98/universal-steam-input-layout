"""The post-install fix pipeline (steam_layout.fixes).

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.fixes import *

class PipelineTests(unittest.TestCase):


    def test_cli_dry_run_reports_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "layout.json")
            path.write_text(json.dumps(load("default")))
            before = path.read_text()
            out = subprocess.run([sys.executable, "-m", "steam_layout.fixes", str(path), "--dry-run"],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("window_routes [R140, R141]:", out.stdout)      # each fix names the rules it applies
            self.assertEqual(path.read_text(), before)


if __name__ == "__main__":
    unittest.main()
