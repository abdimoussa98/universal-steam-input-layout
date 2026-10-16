"""The required cleanups (R169 to R171): where a layer must have a cleanup function.

Tiny layouts, one rule per test, then the frozen 90.23 snapshots and the working layouts. The rules are
the author's of 2026-10-04; the record is findings/2026-10-04-required-cleanups/README.md.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.required_cleanups import *

class SnapshotTests(unittest.TestCase):
    """The frozen 90.23 snapshots: what the three checks found when they were written (2026-10-04)."""
    HELPERS = [f"{stick}: {part}" for part in ("Temporary Gyro", "Entry Point", "Tap Cover") for stick in ("LST", "RST")]
    FULL_PULL = {"LT full pull", "RT full pull"}

    @classmethod
    def setUpClass(cls):
        config = exceptions.load_config()
        cls.reports = {}
        for variant in ("default", "alternative"):
            path = ROOT / f"versions/neptune/90.23/single-set-{variant}_hold-gyro_90.23.json"
            cleanups = Cleanups(Layout(json.loads(path.read_text(encoding="utf-8"))))
            cls.reports[variant] = required.audit(cleanups, config)

    def test_the_inputs_without_a_cleanup_function(self):
        self.assertEqual(counts(self.reports["default"]), (48, 42, 84))
        self.assertEqual(counts(self.reports["alternative"]), (48, 42, 106))

    def test_the_layers_left_out(self):
        for variant, report in self.reports.items():
            with self.subTest(variant):
                left = report["left_out"]
                self.assertEqual(left["ramp"], ["Turning Ramp Up 0", "Turning Ramp Up 1", "Gyro Off Ramp Up"])
                self.assertEqual(left["stateful"], ["Gyro", "Steering", "Cursor Gyro", "Gamepad"])
                self.assertEqual(left["helper"], self.HELPERS)
                self.assertEqual(len(left["window"]), 9)
                self.assertTrue(all(title.endswith(": Double Tap") for title in left["window"]))

    def test_the_four_inputs_the_author_accepted(self):
        for variant, report in self.reports.items():
            with self.subTest(variant):
                self.assertEqual({(e["layer"], e["input"]) for e in report["excepted"]}, {
                    ("Menu Buttons: Left Stick Guard", "right-stick edge"), ("Menu Buttons: Right Stick Guard", "left-stick edge"),
                    ("Steering | LS: Entry Guard", "left-stick edge"), ("Steering | LS: Fallback Hold", "left-stick edge")})
                self.assertEqual(report["stale_decisions"], [])

    def test_24_layers_lack_a_touch_cleanup_and_ten_of_them_are_covers(self):
        for variant, report in self.reports.items():
            with self.subTest(variant):
                touch = [f for f in report["findings"] if f["check"] == TOUCH]
                self.assertEqual((len(touch), {f["bindings"] for f in touch}), (24, {2}))
                inherit = [f["layer"] for f in touch if f["reason"] == "it leaves this touch to the layer below"]
                covers = [title for title in inherit if "Cover" in title or "Temp Cursor Gyro" in title]
                self.assertEqual((len(covers), set(inherit) - set(covers)), (10, {"Steering | LS: Fallback Hold"}))

    def test_every_full_pull_block_in_the_default_layout_covers_nothing(self):
        nothing = [f for f in self.reports["default"]["findings"] if f["reason"] == required.NOTHING]
        self.assertEqual((len(nothing), sum(f["bindings"] for f in nothing)), (19, 38))
        self.assertTrue(all(set(f["inputs"]) == self.FULL_PULL for f in nothing))

    def test_the_modifiers_the_pad_layers_and_the_single_tap_covers_pass(self):
        for variant, report in self.reports.items():
            failing = {f["layer"] for f in report["findings"] if f["reason"] != required.NOTHING}
            side = "L1" if variant == "default" else "L2"
            with self.subTest(variant):
                for title in (f"{side}: Tap Cover", "LTP: Arrow Keys", "RTP: Mouse Buttons", "RTP: Circular Scroll", "Escape",
                              "LTP: Click Entry Point", "RTP: Middle Click"):
                    self.assertNotIn(title, failing)


if __name__ == "__main__":
    unittest.main()
