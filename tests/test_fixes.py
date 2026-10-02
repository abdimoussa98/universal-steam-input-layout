"""The post-install fix pipeline (steam_layout.fixes)."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.fixes import PIPELINE, apply_all

ROOT = Path(__file__).resolve().parents[1]


def load(variant):
    return json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text())


class PipelineTests(unittest.TestCase):
    def test_pipeline_order(self):
        self.assertEqual([name for name, _ in PIPELINE],
                         ["rtp_scroll", "dead_groups", "cover_resets", "transition_set_0",
                          "menu_combo_keys", "window_pads", "window_routes"])

    def test_working_layouts_are_a_fixed_point(self):
        # Every fix has already been applied: running the pipeline again changes nothing.
        for variant in ("default", "alternative"):
            data = load(variant)
            before = copy.deepcopy(data)
            with self.subTest(variant=variant):
                apply_all(data)
                self.assertEqual(data, before)

    def test_cli_dry_run_reports_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "layout.json")
            path.write_text(json.dumps(load("default")))
            before = path.read_text()
            out = subprocess.run([sys.executable, "-m", "steam_layout.fixes", str(path), "--dry-run"],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("window_routes", out.stdout)
            self.assertEqual(path.read_text(), before)




class WindowRouteTests(unittest.TestCase):
    """window_routes blocks the routes the backward chains find, with no depth cap."""

    def test_a_route_three_inputs_deep_is_cleared(self):
        from steam_layout.fixes import window_routes
        from tests.test_audit_inheritance import EMPTY, deep_window
        data = deep_window()
        report = window_routes.fix(data, {"targets": {}})
        self.assertEqual(report["changed"], ["Win / switch/button_y (clear)"])
        own = data["controller_mappings"]["group"][3]["inputs"]["button_y"]["activators"]
        self.assertEqual(own["Full_Press"]["bindings"]["binding"], EMPTY)
        self.assertEqual(window_routes.fix(data, {"targets": {}})["changed"], [])  # idempotent

    def test_a_route_found_only_through_a_bystander_is_cleared(self):
        from steam_layout.fixes import window_routes
        from tests.test_audit_inheritance import bystander_window
        self.assertEqual(window_routes.fix(bystander_window(), {"targets": {}})["changed"],
                         ["Win / switch/button_2 (clear)"])


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
                self.assertEqual(len(titles), 69)
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
