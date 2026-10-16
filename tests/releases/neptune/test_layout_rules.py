"""Static checks for rules that nothing checked before (rule registry plan, phase 15).

Each asks what the layouts hold, with no presses. The rule is named beside the test, and the test is named
under that rule's "Checked by" in resources/Layer Definition of Done.md.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.layout_rules import *

class LayoutRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {v: Layout(layout_data(v)) for v in VARIANTS}








    def test_every_snapshot_holds_both_layouts_under_its_own_version(self):                 # R151
        folders = [folder for folder in changes.VERSIONS.iterdir() if folder.is_dir() and changes.version(folder.name)]
        self.assertTrue(folders)
        for folder in folders:
            for variant in VARIANTS:
                with self.subTest(folder.name, variant=variant):
                    # A named testing candidate has its own filename lineage;
                    # saving it must not advance the live layout's baseline.
                    snapshots = list(folder.glob(f"single-set-{variant}*_hold-gyro_{folder.name}.json"))
                    self.assertTrue(snapshots)
                    for snapshot in snapshots:
                        self.assertTrue(snapshot.with_suffix('.vdf').exists())
                        title = json.loads(snapshot.read_text(encoding="utf-8"))["controller_mappings"]["title"]
                        self.assertEqual(title.rsplit(" :: ", 1)[-1], folder.name)
        for variant in VARIANTS:
            working = layout_data(variant)["controller_mappings"]["title"]
            with self.subTest(variant):
                newest = changes.newest_snapshot(f"single-set-{variant}_hold-gyro_latest.json")
                self.assertGreaterEqual(changes.version(working), changes.version(newest.parent.name))


if __name__ == "__main__":
    unittest.main()
