"""Scenarios for 90.34: Steering base opens its stick edges and adds the fallback at once.

The record is findings/2026-10-05-steering-four-way-and-open-edges/README.md, the author's design
of 2026-10-05. "R1" and "L1" are the modifier pair, which are also Steering's drivers; "RF" is the
right firing button.

E2 and E3 preserve the retired fallback route on the frozen 90.41 builder;
E1 continues to check the working Steering layout.

- `Steering` no longer blocks the stick edges, so in Steering base and in the fallback guard the
  right stick at the rim starts turn assist, as in Base. A driver's layer still binds the edge.
- The add of the fallback guard and the order rule are 90.33 G1 and G3, rewritten there.
- The four-way left stick in Steering base is a setting the simulator does not read; its check is
  in test_steering_four_way_and_open_edges.py, and how it feels is a Deck check.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

GUARD = "Steering | LS: Fallback Guard"
RAMP = ("Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1")


class OpenEdges(ScenarioCase):
    @scenario("90.34 E1", rules=("R114",), rests=("A6",), either=("A9",))
    def test_in_steering_base_turn_assist_runs_and_a_driver_ends_it_and_drives(self):
        for pad in self.each(start="steering"):
            pad.push("RS").wait(400)
            self.assertTrue(pad.has(*RAMP) and pad.gyro_off())
            pad.hold("R1").wait(100)
            if pad.variant == "alternative":
                # The ramp stages block a trigger's pull, as they do in Base: only the full pull ends them.
                self.assertTrue(pad.has(*RAMP) and pad.lacks("Steering | R1: W Key"))
                pad.hold("RT full").wait(100)
            self.assertTrue(pad.lacks(*RAMP))
            self.assertEqual((pad.top, pad.down(), pad.gyro_off()), ("Steering | R1: W Key", ["W"], False))
            pad.let_go("R1").lift("RS").wait(300)
            if pad.variant == "alternative":
                pad.let_go("RT full")
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.34 E2", rules=("R136",), rests=("A10",), frozen="90.41")
    def test_in_the_fallback_turn_assist_runs_and_leaves_nothing_behind(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(200).push("RS").wait(400)
            self.assertTrue(pad.has(GUARD, *RAMP))
            self.assertEqual((pad.down(), pad.gyro_off()), (["W"], True))
            pad.lift("RS").wait(200)
            self.assertEqual((pad.top, pad.down()), (GUARD, ["W"]))
            self.assertTrue(pad.lacks(*RAMP))

    @scenario("90.34 E3", rules=("R136",), rests=("A10", "A36"), frozen="90.41")
    def test_the_guard_can_land_over_a_ramp_stage_and_everything_unwinds(self):
        # Firing while the right stick is at the rim, then the left stick goes up: the guard lands on the ramp stage.
        for pad in self.each(start="steering"):
            pad.push("RS").wait(100).hold("RF").wait(300)
            self.assertTrue(pad.has("Turning Ramp Up 0"))
            pad.push("LS", "up").wait(100)
            self.assertEqual(pad.top, GUARD)
            self.assertIn("W", pad.down())
            pad.hold("L1").wait(100)                                        # the guard's bind answers, over the stage
            self.assertTrue(pad.has("Gyro | L1: Modifier 0"))
            pad.let_go("L1").wait(500).let_go("RF").lift("RS").wait(300)
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", GUARD), ["W"]))      # since 90.35 without Steering
            pad.lift("LS").wait(300).touch("LS").wait(200)
            self.assertEqual(pad.names()[:2], ("Base", "Steering"))
            self.assertTrue(pad.lacks(GUARD, *RAMP))


if __name__ == "__main__":
    unittest.main()
