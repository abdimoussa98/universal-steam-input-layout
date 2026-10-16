"""90.68: in the Entry Guard each driver's chord adds the driver's layer first, then removes the guard.

From 90.67. The author, 2026-10-13: "in the steering left stick guard change the execution order so that the first
thing that happens is we add either the W layer on the right bumper slash right trigger depending on the layout then
we remove the guard and then the same for the opposite side."

Between the two commands the stack is `Steering`, the guard and the driver's layer; on 90.67 it was `Steering` alone,
with its exit on up and down. The simulator runs a bind's commands with nothing in between, so it cannot tell the two
orders apart: the scenario states only that the hand-over still ends the same.

Fixture responsibility: scenarios/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_68 import *

class TheHandOver(ScenarioCase):

    @scenario('90.68 H1', rules=('R137',), rests=('A4',), either=('A9', 'A32'))
    def test_a_driver_pressed_in_the_guard_ends_with_its_layer_on_steering_and_no_guard(self):
        for driver, owner, key in DRIVERS:
            for direction in ('up', 'down', 'left', 'right'):
                for pad in self.each():
                    pad.push('LS', direction).enter_steering(settle=False)
                    self.assertTrue(pad.has('Steering', GUARD), direction)      # the stick was out through the entry
                    pad.hold(driver).wait(60)
                    self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD), (driver, direction))
                    self.assertEqual(pad.stack.index(pad.title('Steering')) + 1, pad.stack.index(pad.title(owner)))
                    self.assertIn(key, pad.down())


if __name__ == "__main__":
    unittest.main()
