"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/scenarios/dse/test_scenarios_dse_1_0.py.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.convert import *

class ConversionTests(unittest.TestCase):
    """C3 historical round trip, both variants: frozen Ibex 1.0 to Neptune 90.74.

    Each conversion runs independently; only source parsing is shared.
    The comparison removes gyro-style fields from private outputs.
    """

    @classmethod
    def setUpClass(cls):
        cls.ibex = {v: load_json(controllers.IBEX.snapshot(v, "1.0"))
                    for v in controllers.VARIANTS}



    def test_c3_ibex_converts_back_to_neptune_90_74_but_for_the_gyro_style(self):         # R179
        for variant in controllers.VARIANTS:
            with self.subTest(variant):
                made, _ = convert.convert(self.ibex[variant], "neptune", variant, "90.74")
                deck = load_json(controllers.NEPTUNE.snapshot(variant, "90.74"))
                styles = 0
                for kept, old in zip(made["controller_mappings"]["group"], deck["controller_mappings"]["group"]):
                    if kept["mode"] == "gyro_to_mouse":
                        self.assertEqual(kept["settings"].pop("gyro_to_2d_conversion_style"), "2")
                        styles += old["settings"].pop("gyro_to_2d_conversion_style", None) is not None or 1
                self.assertEqual(styles, 11)
                self.assertEqual(made, deck)





if __name__ == "__main__":
    unittest.main()
