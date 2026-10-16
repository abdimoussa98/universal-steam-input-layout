"""The press simulator (steam_layout/simulator.py), on tiny made-up layouts.

One behaviour per test, each named with the Steam assumption it models
(resources/Steam Behaviour Assumptions.md).

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.simulator import *

class WalkCrossCheck(unittest.TestCase):
    """The simulator, given physical presses, reaches the stacks `stacks.walk` reaches when it is told
    which activator fires. Both working layouts, with Gyro off and on (the sequences of test_modifier_rocking)."""

    @classmethod
    def setUpClass(cls):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        cls.layouts = {v: Layout(json.loads((root / f"neptune/single-set-{v}_hold-gyro_latest.json").read_text()))
                       for v in ("default", "alternative")}

    def cases(self):
        from tests.support.fixtures.modifier_rocking import VARIANTS, Names
        for variant, (L, R, entry, sides) in VARIANTS.items():
            for gyro in (False, True):
                yield f"{variant}{', Gyro' if gyro else ''}", self.layouts[variant], L, R, entry, Names(sides, gyro)

    def compare(self, layout, n, pairs, **options):
        """pairs: (the walk step this physical action stands for, or None; the action)."""
        from steam_layout.stacks import walk
        expected = iter(walk(layout, [step for step, _ in pairs if step], start=n.base))
        s = Simulator(layout, start=n.base, **options)
        for step, (what, value) in pairs:
            getattr(s, what)(value)
            if step:
                self.assertEqual(s.stack, next(expected)["stack"], step[-1])
        return s

    def test_rocking_in_both_directions(self):
        for label, layout, L, R, entry, n in self.cases():
            for first, second in ((L, R), (R, L)):
                with self.subTest(label, first=first):
                    s = self.compare(layout, n, [
                        ((*first, entry, "hold the first side"), ("press", first)),
                        ((*second, "chord", "hold the second side"), ("press", second)),
                        ((*second, "chord", "200 ms: the combined cover"), ("wait", 200)),
                        ((*first, "release", "let go of the first"), ("release", first)),
                        ((*first, "chord", "press it again"), ("press", first)),
                        ((*first, "chord", "200 ms: the combined cover"), ("wait", 200)),
                        ((*second, "release", "let go of the second"), ("release", second)),
                        ((*first, "release", "let go of the first"), ("release", first))])
                    self.assertEqual(s.stack, n.base)
                    self.assertEqual(s.typed(), [])                       # no scroll at any point

    def test_the_quick_tap_inside_200_ms(self):
        """Modifier 2's own release clears every modifier and toggles Gyro. `walk` stops there. The simulator
        knows the other side is still held: its modifier comes back in the new mode within 50 ms, on the
        repeating entry of Base or Gyro, whichever way a removal treats an exposed command (A9). When the
        release turns Gyro on, Gyro lands on the held button and its repeating entry fires at once (A6)."""
        from tests.support.fixtures.modifier_rocking import Names
        for label, layout, L, R, entry, n in self.cases():
            other = Names((n.l, n.r), not n.g)
            for let_go, held in ((L, n.r), (R, n.l)):
                with self.subTest(label, let_go=let_go):
                    steps = [((*L, entry, "hold L"), ("press", L)), ((*R, "chord", "press R"), ("press", R))]
                    last = ((*let_go, "release", "let go inside 200 ms"), ("release", let_go))
                    if n.g:                           # Gyro goes off: Base is exposed, and waits for its repeat if A9 is false
                        waits = self.compare(layout, n, steps + [last], exposed_fires=False)
                    else:                             # Gyro lands on the held button: back at once
                        waits = self.compare(layout, n, steps, exposed_fires=False).release(let_go)
                        self.assertEqual(waits.stack, other.base + (other.mod(held),))
                    self.assertEqual(waits.wait(50).stack, other.base + (other.mod(held),))
                    fires = Simulator(layout, start=n.base, exposed_fires=True)
                    fires.press(L).press(R).release(let_go).wait(50)
                    self.assertEqual(fires.stack, other.base + (other.mod(held),))

    def test_a_double_tap_a_used_bumper_and_the_cursor(self):
        from tests.support.fixtures.modifier_rocking import A
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                s = self.compare(layout, n, [((*L, entry, "press L"), ("press", L)),
                                             ((*L, "release", "let go"), ("release", L)),
                                             ((*L, "Full_Press", "press again inside 150 ms"), ("press", L))])
                self.assertEqual(len(s.typed()), 1)                       # the scroll
                self.compare(layout, n, [((*L, entry, "press L"), ("press", L)),
                                         ((*A, "chord", "press A with L held"), ("press", A)),
                                         (None, ("release", A)),
                                         ((*L, "release", "let go of L"), ("release", L)),
                                         ((*L, entry, "press L again at once"), ("press", L))])
                self.compare(layout, n, [((*L, entry, "press L"), ("press", L)),
                                         ((*L, "chord", "hold L 300 ms"), ("wait", 300)),
                                         ((*L, "release", "let go of L"), ("release", L))])


if __name__ == "__main__":
    unittest.main()
