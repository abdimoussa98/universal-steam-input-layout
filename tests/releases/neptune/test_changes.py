"""The change report: what differs between two layouts, by layer and input (steam_layout/changes.py).

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.changes import *

class SnapshotTests(unittest.TestCase):
    def test_the_newest_snapshot_is_found_by_version_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            for version in ("90.9", "90.10", "90.2"):
                folder = Path(tmp, version)
                folder.mkdir()
                (folder / f"single-set-default_hold-gyro_{version}.json").write_text("{}")
            found = changes.newest_snapshot("single-set-default_hold-gyro_latest.json", Path(tmp))
            self.assertEqual(found.name, "single-set-default_hold-gyro_90.10.json")
            self.assertIsNone(changes.newest_snapshot("single-set-alternative_hold-gyro_latest.json", Path(tmp)))

    def test_90_12_to_90_13_shows_the_change_nobody_decided(self):
        # In 90.13 the window_routes fix changed the Steering stick windows; it was only noticed by diffing.
        def snapshot(version):
            path = ROOT / f"versions/neptune/{version}/single-set-default_hold-gyro_{version}.json"
            return json.loads(path.read_text(encoding="utf-8"))
        report = changes.diff(snapshot("90.12"), snapshot("90.13"))
        self.assertEqual((report["added"], report["removed"]), ([], []))
        self.assertIn("Steering", report["layers"])                           # the decided change: no turn assist
        self.assertIn("Steering | LS Up: Double Tap", report["layers"])       # the one the fix made on its own


if __name__ == "__main__":
    unittest.main()
