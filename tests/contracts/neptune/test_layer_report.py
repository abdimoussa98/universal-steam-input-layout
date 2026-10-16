"""The per-layer report: the three questions and the cleanup lists (plan step 6).

Plan: plans/2026-10-01-backward-chain-audit.md.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.layer_report import *

class NeptuneReportTests(unittest.TestCase):
    def test_a_modifier_on_the_default_layout(self):
        layout = Layout(json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text()))
        result = report(layout, "L1: Modifier 0")
        self.assertIn("LST: Entry Point", result["below"]["layers"])
        # Since 90.46 a bumper pressed in `Gyro Off Ramp Up` removes the ramps, so no ramp layer is under a
        # bumper modifier. Until 90.45 this test named that ramp layer as one that is.
        self.assertEqual([title for title in result["below"]["layers"] if "Ramp Up" in title], [])
        self.assertIn("L1: Temp Cursor Gyro", result["above"])
        release_exit = next(e for e in result["exits"] if e["input"] == "switch/left_bumper" and e["role"] == "release")
        self.assertIn("L1: Temp Cursor Gyro", release_exit["present_and_removed"])
        # Since 90.12 no list names a layer that can never be on the stack with it (cleanup rule 6);
        # the release used to remove the Gyro twin. The tiny layouts above cover the report itself.
        self.assertEqual(release_exit["removed_never_present"], [])


if __name__ == "__main__":
    unittest.main()
