"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/scenarios/dse/test_scenarios_dse_1_0.py.

Fixture responsibility: contracts/dse. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.convert import *

class ConversionTests(unittest.TestCase):
    """Current DSE default/alternative: C5 pad-model equivalence, structure, mute and gyro.

    Read-only projections of frozen Ibex 1.0 and current DSE sources are
    shared within this class.
    """

    @classmethod
    def setUpClass(cls):
        cls.ibex = {v: load_json(controllers.IBEX.snapshot(v, "1.0"))
                    for v in controllers.VARIANTS}
        cls.dse = {v: load_json(controllers.DSE.working_json(v))
                   for v in controllers.VARIANTS}
        cls.ibex_layouts = {v: Layout(convert.readable(data)) for v, data in cls.ibex.items()}
        cls.dse_layouts = {v: Layout(convert.readable(data)) for v, data in cls.dse.items()}




    def test_c5_the_whole_pads_layers_are_their_models_with_only_the_tables_changes(self):  # R183
        for variant in controllers.VARIANTS:
            model, made = self.ibex_layouts[variant], self.dse_layouts[variant]
            for old, new in convert.WHOLE_PAD_LAYERS.items():
                with self.subTest(variant, layer=new):
                    self.assertEqual(differences(model, old, made, new), [])

    def test_what_the_edge_has_and_lacks(self):                                           # R178, R180, R182, R183
        for variant, data in self.dse.items():
            layout = self.dse_layouts[variant]
            titles = list(layout.presets)
            with self.subTest(variant):
                self.assertEqual(len(titles), 75)
                self.assertFalse([t for t in titles if t.startswith(("LST:", "RST:", "LTP:", "RTP:"))])
                self.assertEqual(sorted(t for t in titles if t.startswith("CTP:")),
                                 sorted(convert.WHOLE_PAD_LAYERS.values()))
                states = [s for p in layout.presets.values() for s in p["group_source_bindings"].values()]
                self.assertFalse([s for s in states if s.split(" ")[0] in ("left_trackpad", "right_trackpad")])
                for title, preset in layout.presets.items():
                    for gid, state in preset["group_source_bindings"].items():
                        g = layout.groups[gid]
                        if state.split(" ")[0] in ("joystick", "right_joystick"):
                            self.assertNotIn("touch", g.get("inputs", {}), title)
                        for name, kind, entry in convert.activators(g):
                            settings = entry.get("settings") or {}
                            self.assertNotIn(settings.get("chord_button"), ("16", "17", "23", "24"), title)
                            bits = int(settings.get("gyro_ratchet_button_mask", 0))
                            self.assertFalse(bits & (1 << 19 | 1 << 20 | 1 << 46 | 1 << 47), title)
                            for op, target in layout.layer_ops(entry):
                                self.assertIn(target, layout.presets, f"{title} {name} names a deleted layer")
                cm = data["controller_mappings"]
                self.assertEqual((cm["controller_type"], cm["title"].rsplit(" :: ", 1)[-1]), ("controller_ps5_edge", "1.0"))

    def test_mute_and_gyro_on_the_edge(self):                                            # R184, R185, R180
        for variant, data in self.dse.items():
            layout = self.dse_layouts[variant]
            with self.subTest(variant):
                capture = [t for t in layout.presets if "button_capture" in (layout.active(t).get("switch") or {}).get("inputs", {})]
                self.assertEqual(capture, ["Base"])
                self.assertEqual(layout.active("Base")["switch"]["inputs"]["button_capture"]["activators"],
                                 act("mouse_button MIDDLE, , "))
                gyros = {t: layout.active(t)["gyro"] for t in layout.presets
                         if layout.active(t).get("gyro", {}).get("mode") == "gyro_to_mouse"}
                self.assertEqual(len(gyros), 9)                       # the two Temporary Gyro layers are gone
                masked = {t for t, g in gyros.items() if "gyro_ratchet_button_mask" in g["settings"]}
                self.assertEqual(masked, {"Base"})
                # Base keeps its mask, with the stick touches dropped: each needs that stick's deflection too (R178 d)
                self.assertEqual((gyros["Base"]["settings"]["gyro_ratchet_button_mask"],
                                  gyros["Base"]["settings"]["gyro_ratchet_button_requireany_or_all"]),
                                 (str(1 << 12 | 1 << 14 | 1 << 30 | 1 << 31), "1"))
                for g in gyros.values():
                    self.assertEqual(g["settings"]["gyro_to_2d_conversion_style"], "4")
                self.assertEqual(layout.active("Gyro Off Ramp Up")["gyro"]["mode"], "disabled")


if __name__ == "__main__":
    unittest.main()
