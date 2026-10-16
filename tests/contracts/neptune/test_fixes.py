"""The post-install fix pipeline (steam_layout.fixes).

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.fixes import *

class MenuComboKeyTests(unittest.TestCase):
    """Author decision, 2026-10-01: Backspace/Enter are typed by the menu chords; no overlay layers."""

    def test_overlays_are_gone_and_nothing_references_them(self):
        from steam_layout.fixes import menu_combo_keys
        for variant in ("default", "alternative"):
            data = load(variant)
            cm = data["controller_mappings"]
            titles = [v["title"] for v in cm["action_layers"].values()]
            with self.subTest(variant=variant):
                self.assertFalse(set(menu_combo_keys.OVERLAYS) & set(titles))
                self.assertEqual([p["id"] for p in cm["preset"]], [str(i) for i in range(len(cm["preset"]))])
                self.assertEqual([p["name"] for p in cm["preset"]], list(cm["actions"]) + list(cm["action_layers"]))
                # Every layer command still resolves to an existing layer after the ID shift.
                from steam_layout.model import Layout, entries
                layout = Layout(data)
                for group in cm["group"]:
                    for value in group.get("inputs", {}).values():
                        for _, entry in entries(value.get("activators", {})):
                            for _, title in layout.layer_ops(entry):
                                self.assertIn(title, layout.presets)



if __name__ == "__main__":
    unittest.main()
