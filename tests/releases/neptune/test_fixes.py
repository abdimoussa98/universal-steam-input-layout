"""The post-install fix pipeline (steam_layout.fixes).

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.fixes import *

class MenuComboKeyTests(unittest.TestCase):
    """Author decision, 2026-10-01: Backspace/Enter are typed by the menu chords; no overlay layers."""


    def test_fix_rewrites_a_layout_that_still_has_the_overlays(self):
        from steam_layout.fixes import menu_combo_keys
        from steam_layout.model import Layout
        source = ROOT / "versions/neptune/90.7/single-set-default_hold-gyro_90.7.json"
        data = json.loads(source.read_text())
        before = Layout(copy.deepcopy(data))
        report = menu_combo_keys.fix(data)
        self.assertIn("removed layer Menu Left: Backspace", report["changed"])
        after = Layout(data)
        self.assertEqual(len(after.presets), len(before.presets) - 2)
        chord = after.active("Menu Right: Fn Layer")["switch"]["inputs"]["button_menu"]["activators"]["chord"]
        self.assertEqual(chord["bindings"]["binding"][0], "key_press BACKSPACE, , ")
        # A layer after the removed ones keeps its meaning: Steering still commits from Transition Set 1.
        release = after.active("Transition Set 1")["switch"]["inputs"]["button_escape"]["activators"]["release"]
        self.assertIn(("add_layer", "Steering"), after.layer_ops(release))
        self.assertEqual(menu_combo_keys.fix(data)["changed"], [])  # idempotent


if __name__ == "__main__":
    unittest.main()
