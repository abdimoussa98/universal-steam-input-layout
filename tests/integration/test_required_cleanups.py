"""The required cleanups (R169 to R171): where a layer must have a cleanup function.

Tiny layouts, one rule per test, then the frozen 90.23 snapshots and the working layouts. The rules are
the author's of 2026-10-04; the record is findings/2026-10-04-required-cleanups/README.md.

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.required_cleanups import *

class CommandTests(unittest.TestCase):
    def run_audit(self, data, *args):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "layout.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return subprocess.run([sys.executable, "-m", "tools.audit_cleanups", str(path), "--extras", "0", *args],
                                  capture_output=True, text=True, cwd=ROOT)

    def test_the_cleanup_audit_fails_on_a_missing_cleanup_and_names_the_rule(self):
        result = self.run_audit(layout(touches=False))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAIL  touch without cleanup [R169]", result.stdout)
        self.assertIn("left-stick touch, right-stick touch: it leaves this touch to the layer below", result.stdout)
        self.assertIn("ok    button without cleanup [R171]", result.stdout)

    def test_it_passes_when_every_required_cleanup_is_there(self):
        result = self.run_audit(layout())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_json_carries_the_three_checks(self):
        report = json.loads(self.run_audit(layout(touches=False), "--json").stdout)
        self.assertEqual(report["counts"][TOUCH], {"findings": 1, "bindings": 2})
        self.assertFalse(report["ok"])
        self.assertEqual(report["required"], {"excepted": [], "left_out": {}})


if __name__ == "__main__":
    unittest.main()
