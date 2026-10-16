"""The exceptions register: every accepted finding in one list (steam_layout/exceptions.py).

Fixture responsibility: contracts/shared. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.exceptions import *

class ControllerViewTests(unittest.TestCase):
    """The register as it applies to one controller's layout (R178 g)."""
    EDGE = layout("controller_ps5_edge", ["CTP: Arrow Keys", "Menu Left!Right: Enter", "L2: Modifier 0"],
                  "alternative")

    def test_neptune_reads_the_register_as_written(self):
        rows = [entry("R169", {"layers": ["LST: Tap Cover"], "inputs": ["joystick/touch"]}),
                entry("R132", {"layers": ["P"], "removes": ["Q"], "until": "90.56"})]
        self.assertEqual(exceptions.for_layout(rows, layout("controller_neptune", ["P"])), rows)

    def test_an_entry_that_ended_on_neptunes_line_is_over_elsewhere(self):                 # R177
        row = entry("R132", {"layers": ["P"], "removes": ["Q"], "until": "90.56"})
        for controller in ("controller_triton", "controller_ps5_edge"):
            self.assertEqual(exceptions.for_layout([row], layout(controller, ["P", "Q"])), [], controller)

    def test_the_edge_renames_moves_and_leaves_out(self):                                  # R178 (g), R181, R183
        rows = [entry("R132", {"layers": ["Menu Left!Right: Enter"], "removes": ["LTP: Arrow Keys", "RTP: Mouse Buttons"]}),
                entry("R139", {"layers": ["L1: Modifier 0"],
                               "inputs": ["joystick/touch", "left_trackpad/click", "switch/button_back_left"]}),
                entry("R169", {"layers": ["L1: Modifier 0"], "inputs": ["joystick/touch"]}),
                entry("R139", {"layers": ["RTP: Mouse Buttons"], "inputs": ["switch/button_a"]}),
                entry("R140", {"target": "L1: Modifier 0", "source": "right_trackpad", "input": "click"})]
        kept = exceptions.for_layout(rows, self.EDGE)
        self.assertEqual([row["scope"] for row in kept], [
            {"layers": ["Menu Left!Right: Enter"], "removes": ["CTP: Arrow Keys"]},
            {"layers": ["L1: Modifier 0"], "inputs": ["center_trackpad/click", "switch/button_back_left_upper"]}])

    def test_the_window_audits_stacks_leave_out_what_the_edge_lacks(self):
        config = {"targets": {
            "LST: Double Tap": {"stacks": [{"layers": ["Base"], "why": "x"}]},
            "L1: Modifier 0": {"stacks": [
                {"layers": ["Base", "LTP: Arrow Keys"], "why": "x"},
                {"layers": ["Base"], "when_inherited": {"source": "joystick", "input": "touch", "from_layer": "Base"},
                 "why": "x"}]}}}
        view = exceptions.stacks_for_layout(config, self.EDGE)
        self.assertEqual(list(view["targets"]), ["L1: Modifier 0"])
        self.assertEqual([row["layers"] for row in view["targets"]["L1: Modifier 0"]["stacks"]],
                         [["Base", "CTP: Arrow Keys"]])


if __name__ == "__main__":
    unittest.main()
