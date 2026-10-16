"""The required cleanups (R169 to R171): where a layer must have a cleanup function.

Tiny layouts, one rule per test, then the frozen 90.23 snapshots and the working layouts. The rules are
the author's of 2026-10-04; the record is findings/2026-10-04-required-cleanups/README.md.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.required_cleanups import *

class WorkingLayoutTests(unittest.TestCase):
    def test_the_working_layouts_have_every_required_cleanup(self):
        """It failed on 90.23 on purpose: the rules were enforced before the layouts followed them. 90.24
        applied the fixes (findings/2026-10-04-required-cleanups/README.md)."""
        config = exceptions.load_config()
        for variant in ("default", "alternative"):
            path = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
            report = required.audit(Cleanups(Layout(json.loads(path.read_text(encoding="utf-8")))), config)
            with self.subTest(variant):
                self.assertEqual(dict(zip(required.CHECKS, counts(report))), dict.fromkeys(required.CHECKS, 0))
                self.assertEqual(report["stale_decisions"], [])


if __name__ == "__main__":
    unittest.main()
