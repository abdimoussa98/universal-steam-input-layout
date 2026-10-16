"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/scenarios/dse/test_scenarios_dse_1_0.py.

Fixture responsibility: contracts/shared. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.convert import *

class BaseTests(unittest.TestCase):
    def test_ibex_is_built_and_the_others_are_converted_from_it(self):                    # R177
        neptune = load_json(controllers.NEPTUNE.snapshot("default", "90.74"))
        ibex = load_json(controllers.IBEX.snapshot("default", "1.0"))
        with self.assertRaisesRegex(ValueError, "base layout"):
            convert.convert(ibex, "ibex", "default", "1.1")
        with self.assertRaisesRegex(ValueError, "not an Ibex layout"):
            convert.convert(neptune, "dse", "default", "1.0")
        with self.assertRaisesRegex(ValueError, "reads a Neptune layout"):
            convert.bootstrap(ibex, "default", "1.0")


if __name__ == "__main__":
    unittest.main()
