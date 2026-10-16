"""The Cleanup audit: what a cleanup function and a release may remove.

Tiny layouts, one rule per test, then the frozen 90.10 snapshots. The rules are in
findings/2026-10-02-cleanup-boundaries/README.md; the plan is plans/2026-10-02-cleanup-audit.md.

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.cleanups import *

class ScriptTests(unittest.TestCase):
    def run_script(self, data, *args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layout.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return subprocess.run([sys.executable, "-m", "tools.audit_cleanups", str(path), "--no-required", *args],
                                  capture_output=True, text=True, cwd=ROOT)        # the toys show the list checks alone

    def test_exit_codes(self):
        self.assertEqual(self.run_script(owner()).returncode, 0)
        self.assertEqual(self.run_script(owner({"button_a": guarded(remove("P"))})).returncode, 1)
        self.assertEqual(self.run_script({"not": "a layout"}).returncode, 2)

    def test_json_and_layer_filter(self):
        data = owner({"button_a": guarded(remove("P"))})
        report = json.loads(self.run_script(data, "--json").stdout)
        self.assertEqual([(f["check"], f["layer"], f["target"]) for f in report["findings"]], [("left above", "P", "C")])
        self.assertEqual(json.loads(self.run_script(data, "--json", "--layer", "C").stdout)["findings"], [])

    def test_the_text_names_the_binding_and_the_reason(self):
        text = self.run_script(owner({"button_a": guarded(remove("P"))})).stdout
        self.assertIn("left above", text.lower())
        self.assertIn("C", text)
        self.assertIn("LB", text)

    def test_the_text_names_the_rule_each_check_enforces(self):
        text = self.run_script(owner({"button_a": guarded(remove("P"))})).stdout
        self.assertIn("FAIL  left above [R129]", text)
        self.assertIn("ok    outside the guard [R127, R131]", text)
        self.assertIn("== Left above [R129]", text)


if __name__ == "__main__":
    unittest.main()
