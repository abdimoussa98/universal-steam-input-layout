"""The transition inventory, what a layer inherits per lower stack, and the Flow audit.

The Flow audit (audit_flow_inheritance.py) runs on backward chains (steam_layout/chains.py,
covers.py). The family walk it first ran on is deprecated; its tests are in
archived/depth-search-and-family-walk/.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.flow_inheritance import *

class NeptuneFlowTests(unittest.TestCase):

    def test_the_reused_entry_guard_is_reachable_without_a_dormant_exemption(self):
        from tools.audit_flow_inheritance import run
        for variant in ("default", "alternative"):
            with self.subTest(variant=variant):
                live = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
                report = run(live, baseline=live)
                self.assertEqual(report["dormant"], [])
                self.assertIn("Steering | LS: Entry Guard", report["targets"])
                self.assertNotIn("Steering | LS: Fallback Guard", report["targets"])
                self.assertEqual(report["unreached"], [])
                self.assertTrue(report["clean"], report["needs_review"])

    def test_cli_runs_without_out_and_reports_json(self):
        for variant in ("default", "alternative"):
            run = subprocess.run([sys.executable, "-m", "tools.audit_flow_inheritance",
                                  str(ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"), "--json"],
                                 capture_output=True, text=True, cwd="/", env={**os.environ, "PYTHONPATH": str(ROOT)})
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(run.stdout)
            self.assertNotIn("families", report)
            self.assertEqual(report["view"]["contexts"], [["Base"], ["Base", "Gyro"]])
            self.assertEqual(report["layout"]["variant"], variant)
            self.assertEqual(report["unreached"], [])
            self.assertEqual(report["legacy_only"], [])                 # the pad layers left hold_layer in 90.14
            self.assertEqual(report["unsupported"], [])
            self.assertEqual(report["stale_decisions"], [])
            layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
            # R145: a chain reaches every layer, except the ones only hold_layer adds.
            self.assertEqual(set(report["targets"]), set(layout.presets) - {layout.base} - set(report["legacy_only"])
                             - {row["layer"] for row in report["dormant"]})
            # R144: every cover-type layer is cover-checked, and nothing else is.
            checked = {c["cover"] for c in report["covers"]}
            self.assertEqual(checked, {title for title, row in report["targets"].items() if row["cover"]})
            modifier = "L2" if variant == "alternative" else "L1"
            self.assertLessEqual({f"{modifier}: Tap Cover", "Gyro Off Ramp Up"}, checked)   # by suffix, and by title
            self.assertNotIn("LST: Tap Cover", checked)                                     # a stick-touch helper
            self.assertLess(report["view"]["seconds"], 5)
            # Inherited bindings that vary between stacks are listed, and don't decide the result.
            self.assertTrue([i for x in report["targets"].values() for i in x["inputs"] if i["finding"] == "varies"])
            self.assertFalse([i for x in report["targets"].values() for i in x["inputs"] if i["finding"] == "conflict"])
            open_covers = {c["cover"] for c in report["covers"] for f in c["findings"] if not f["allowed"]}
            self.assertEqual(open_covers, set())
            self.assertTrue(report["clean"])


if __name__ == "__main__":
    unittest.main()
