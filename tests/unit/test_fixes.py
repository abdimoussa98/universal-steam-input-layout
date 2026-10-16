"""The post-install fix pipeline (steam_layout.fixes).

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.fixes import *

class PipelineTests(unittest.TestCase):
    def test_pipeline_order(self):
        self.assertEqual([name for name, _ in PIPELINE],
                         ["rtp_scroll", "dead_groups", "cover_resets", "menu_combo_keys", "window_pads", "cleanup_lists",
                          "window_routes"])




class WindowRouteTests(unittest.TestCase):
    """window_routes blocks the routes the backward chains find, with no depth cap."""

    def test_a_route_three_inputs_deep_is_cleared(self):
        from steam_layout.fixes import window_routes
        from tests.support.layouts import EMPTY, deep_window
        data = deep_window()
        report = window_routes.fix(data, {"targets": {}})
        self.assertEqual(report["changed"], ["Win / switch/button_y (clear)"])
        own = data["controller_mappings"]["group"][3]["inputs"]["button_y"]["activators"]
        self.assertEqual(own["Full_Press"]["bindings"]["binding"], EMPTY)
        self.assertEqual(window_routes.fix(data, {"targets": {}})["changed"], [])  # idempotent

    def test_a_route_found_only_through_a_bystander_is_cleared(self):
        from steam_layout.fixes import window_routes
        from tests.support.layouts import bystander_window
        self.assertEqual(window_routes.fix(bystander_window(), {"targets": {}})["changed"],
                         ["Win / switch/button_2 (clear)"])


if __name__ == "__main__":
    unittest.main()
