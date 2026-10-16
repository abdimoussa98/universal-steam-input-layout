"""Inheritance/blocking audit (Layer Definition of Done, section 8).

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.audit_inheritance import *

class CliTests(unittest.TestCase):
    def run_cli(self, data, cfg, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            layout, stacks, register = Path(tmp, "l.json"), Path(tmp, "s.json"), Path(tmp, "r.json")
            layout.write_text(json.dumps(data))
            stacks.write_text(json.dumps(cfg))
            register.write_text(json.dumps({"exceptions": []}))
            return subprocess.run([sys.executable, "-m", "tools.audit_inheritance", str(layout), "--stacks",
                                   str(stacks), "--register", str(register), *extra], capture_output=True, text=True, cwd=ROOT)

    def test_chains_are_the_default_and_print_the_reason(self):
        out = self.run_cli(deep_window(), {"targets": {}})
        self.assertEqual(out.returncode, 1)
        self.assertIn("1 stack(s) (1 from chains)", out.stdout)
        self.assertIn("switch/button_y from Owner", out.stdout)
        self.assertIn("open [R140]: switch/button_y", out.stdout)      # the rule the finding breaks
        self.assertIn("because: Owner switch/button_x Full_Press#0: +Win", out.stdout)

    def test_an_unreached_window_is_reported_and_fails(self):
        out = self.run_cli(build({"Base": {}, "Win": {"switch": ("switches", AOA)}}), {"targets": {}})
        self.assertEqual(out.returncode, 1)
        self.assertIn("Win: NOT CHECKED [R140]", out.stdout)

    def test_the_working_layout_passes_on_chains_alone(self):
        layout = ROOT / "neptune/single-set-default_hold-gyro_latest.json"
        out = subprocess.run([sys.executable, "-m", "tools.audit_inheritance", str(layout), "--json"],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertTrue(all(row["chain_stacks"] for row in report["targets"].values()))

    def test_exit_codes(self):
        clean = build({"Base": {}, "Win": {}})
        leaky = build({"Base": {"switch": ("switches", {"button_a": act(add("Win"))})}, "Win": {}})
        self.assertEqual(self.run_cli(clean, config([["Base"]])).returncode, 0)
        self.assertEqual(self.run_cli(leaky, config([["Base"]])).returncode, 1)
        self.assertEqual(self.run_cli(clean, config([["Base", "Nope"]])).returncode, 2)
        out = self.run_cli(leaky, config([["Base"]]), "--entries", "Win")
        self.assertEqual(out.returncode, 0)
        self.assertIn("button_a", out.stdout)


if __name__ == "__main__":
    unittest.main()
