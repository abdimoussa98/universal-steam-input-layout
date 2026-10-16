"""90.58: 90.57 without the removes that never take a layer off. Nothing is added, and nothing plays differently.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_58 import *

class OnlyRemovesAreGone(unittest.TestCase):
    """The author, 2026-10-12: "I want to make sure that this is reductive and not additive. So we're not going
    to be adding any layer removals right now. We're just reducing them." """

    def test_every_bind_has_its_90_57_commands_less_some_removes_and_nothing_else_differs(self):
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                lists, other = [], []
                differences(frozen_layout_data(variant, '90.57'), built(variant), (), lists, other)
                self.assertEqual(other, [('controller_mappings', 'title')])
                gone = 0
                for path, old, new in lists:
                    lost, gained = Counter(old) - Counter(new), Counter(new) - Counter(old)
                    self.assertFalse(gained, path)
                    self.assertTrue(all('remove_layer' in command for command in lost), path)
                    rest = iter(old)
                    self.assertTrue(all(any(x == y for y in rest) for x in new), path)      # what stays keeps its order
                    self.assertTrue(new, path)
                    gone += sum(lost.values())
                self.assertEqual(gone, TAKEN[variant][1])

    def test_the_count_of_removes(self):
        for variant, (before, taken, after) in TAKEN.items():
            count = lambda data: sum(len(found[5]) for found in removes(Layout(data)))
            self.assertEqual(count(frozen_layout_data(variant, '90.57')), before)
            self.assertEqual(count(built(variant)), after)
            self.assertEqual(before - after, taken)

    def test_the_fourteen_clears_name_5_to_27_layers(self):
        # R163. Until 90.57 each named every layer but one, 89. They keep every layer that was on the stack at
        # least once when the clear fired, and every one the audit could not rule out.
        for variant in VARIANTS:
            old, new = Layout(frozen_layout_data(variant, '90.57')), Layout(built(variant))
            now = {found[:5]: found[5] for found in removes(new)}
            sizes = sorted(len(now[found[:5]]) for found in removes(old) if len(found[5]) == 89)
            self.assertEqual(sizes, [5, 5, 14, 14, 23, 23, 26, 26, 26, 26, 27, 27, 27, 27], variant)


class NothingPlaysDifferently(unittest.TestCase):
    """The proof of the build was 48,000 random walks and every bumper sequence of five steps a layout, with the
    whole log compared (findings/2026-10-12-remove-list-audit). These are samples of both, kept in the suite."""

    def test_seeded_walks_give_the_same_log_on_90_57_and_on_this_build(self):
        walk = audit_script('walk')
        for variant in VARIANTS:
            layouts = [Layout(frozen_layout_data(variant, '90.57')), Layout(built(variant))]
            finished = 0
            for index in range(120):
                missed = 0.10 if index % 2 else 0.0                 # half the walks miss one release in ten (A25)
                found = []
                for layout in layouts:
                    rng = random.Random(58_000 + index)             # the same walk on both
                    pad = walk.new_pad(variant, layout, rng, Counter(), Counter(), Counter())
                    how, left = walk.walk(pad, rng, missed)
                    text = repr(pad.sim.log) + repr(pad.sim.stack)
                    found.append((how, left, hashlib.sha1(text.encode()).hexdigest()))
                self.assertEqual(found[0], found[1], (variant, index))
                finished += found[0][0] == 'done'
            self.assertGreater(finished, 100, variant)

    def test_every_bumper_sequence_of_three_steps_gives_the_same_log(self):
        # L1 or R1 down or up, or a tap of A, then 20 or 210 ms (inside a timer, past the 200 ms hold). From Base
        # with a bind exposed under a held button firing at once, and from `Gyro` with it firing at its next
        # repeat (A9). The build's own sweep played every sequence of five steps, with a 120 ms gap as well.
        rocking = audit_script('rocking')
        steps = list(itertools.product(itertools.product(rocking.ROCK, (20, 210)), repeat=3))
        for variant in VARIANTS:
            layouts = [Layout(frozen_layout_data(variant, '90.57')), Layout(built(variant))]
            played = scrolled = 0
            for start, exposed in ((('Base',), True), (('Base', 'Gyro'), False)):
                for sequence in steps:
                    before, after = (rocking.play(variant, layout, start, exposed, sequence) for layout in layouts)
                    self.assertEqual(before, after, (variant, start, exposed, sequence))
                    played += 1
                    scrolled += before[1]
            self.assertEqual(played, 2 * 6 ** 3)
            self.assertGreater(scrolled, 40, variant)                 # the sequences do reach the scroll layers


if __name__ == "__main__":
    unittest.main()
