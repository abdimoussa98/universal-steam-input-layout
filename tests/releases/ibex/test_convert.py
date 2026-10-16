"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/scenarios/dse/test_scenarios_dse_1_0.py.

Fixture responsibility: releases/ibex. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.convert import *

class WholePadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ibex = load_json(controllers.IBEX.snapshot("default", "1.0"))
        cls.data = convert.readable(cls.ibex)
        cls.report = convert.Report()
        convert.whole_pad(cls.data, cls.report)
        cls.layout = Layout(cls.data)

    def test_the_left_pads_binds_go_to_the_whole_pad(self):                                # R183
        states = [state for p in self.data["controller_mappings"]["preset"]
                  for state in p["group_source_bindings"].values()]
        self.assertFalse([s for s in states if s.startswith("left_trackpad ")])
        self.assertEqual(sum(s.startswith("center_trackpad ") for s in states),
                         sum(s.startswith("left_trackpad ") for p in self.ibex["controller_mappings"]["preset"]
                             for s in p["group_source_bindings"].values()))

    def test_the_six_layers_are_the_whole_pads_in_their_models_places(self):              # R183, R104
        before = [v["title"] for v in self.ibex["controller_mappings"]["action_layers"].values()]
        after = [v["title"] for v in self.data["controller_mappings"]["action_layers"].values()]
        self.assertEqual(after, [convert.WHOLE_PAD_LAYERS.get(title, title) for title in before])
        named = {target for g in self.data["controller_mappings"]["group"] for _, _, e in convert.activators(g)
                 for _, target in convert.COMMAND.findall(" ".join(actions(e)))}
        self.assertFalse(named & set(convert.WHOLE_PAD_LAYERS))

    def test_the_click_entry_point_has_a_ring_press_and_no_centre_press(self):           # R183
        pad = self.layout.active("CTP: Click Entry Point")["center_trackpad"]
        self.assertEqual(pad["settings"]["edge_binding_radius"], "23000")
        (kind, ring), = entries(pad["inputs"]["edge"]["activators"])
        self.assertEqual(kind, "Full_Press")
        self.assertEqual(ring["settings"], {"hold_repeats": "1", "repeat_rate": "50", "haptic_intensity": "0",
                                            "delay_start": "5", "interruptable": "0"})
        self.assertEqual(self.layout.layer_ops(ring), [("add_layer", "CTP: Arrow Keys"),
                                                       ("remove_layer", "CTP: Click Entry Point")])

    def test_every_click_on_the_whole_pad_is_a_regular_press(self):                       # R183
        clicks = [kind for title, p in self.layout.presets.items() for gid, state in p["group_source_bindings"].items()
                  if state.startswith("center_trackpad") and title != "LTP: Middle Click"
                  for name, value in (self.layout.groups[gid].get("inputs") or {}).items()
                  for kind, _ in entries(value.get("activators") or {}) if name == "click"]
        self.assertTrue(clicks)
        self.assertNotIn("Soft_Press", clicks)


if __name__ == "__main__":
    unittest.main()
