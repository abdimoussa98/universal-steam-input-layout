"""90.58: 90.57 without the removes that never take a layer off. Nothing is added, and nothing plays differently.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_58 import *

class Clears(unittest.TestCase):
    def test_a_clear_names_every_layer_that_is_on_the_stack_when_it_fires(self):
        # R163, since 90.58: a clear names every layer that can be on the stack there. A whole list could not go
        # stale when a layer was added; a short one can, and this is the guard. The fourteen clears are the binds
        # that had 89 removes in 90.57; each kept one layer, `Gyro` or `Menu Keys`.
        walk = audit_script('walk')
        for variant in VARIANTS:
            old, layout = Layout(frozen_layout_data(variant, '90.57')), Layout(layout_data(variant))
            keeps = {(title, (source, name), kind, index): set(old.presets) - set(found) - {'Base'}
                     for title, source, name, kind, index, found in removes(old) if len(found) == 89}
            self.assertEqual(len(keeps), 14)
            self.assertTrue(all(len(keep) == 1 for keep in keeps.values()))
            fired, left = Counter(), []

            class Watching(walk.Watcher):
                def _run(sim, entry, act=None, tap=False, commands=True):
                    key = (entry.layer, entry.control, entry.kind, entry.index)
                    if commands and key in keeps:
                        named = {target for op, target in entry.ops if op == 'remove_layer'}
                        fired[key] += 1
                        extra = set(sim.stack[1:]) - named - keeps[key]
                        if extra:
                            left.append((key, sorted(extra)))
                    return super()._run(entry, act=act, tap=tap, commands=commands)

            for index in range(240):
                rng = random.Random(163_000 + index)
                pad = walk.Pad.__new__(walk.Pad)
                pad.variant, pad.options, pad.layout = variant, {}, layout
                pad.sim = Watching(layout, Counter(), Counter(), Counter(), exposed_fires=rng.random() < 0.5,
                                   reverse_ties=rng.random() < 0.5)
                pad._mark, pad._began = 0, tuple(pad.sim.stack)
                walk.walk(pad, rng, 0.10 if index % 2 else 0.0)
            self.assertEqual(left, [], variant)
            self.assertEqual(len(fired), 14, variant)                 # every one of the fourteen fired
            self.assertGreater(sum(fired.values()), 300, variant)


class CleanupFunctions(unittest.TestCase):
    def test_no_cleanup_function_names_a_layer_its_rules_do_not_ask_for(self):
        # R132 as tightened in 90.57, for cleanup functions. The cleanup rules ask for the host, what is below it
        # inside the guard, and a layer above it that leaves the input alone (R128, R129). A layer above that binds
        # the input answers it first, so the host's bind does not run while it is on. 172 such removes (184 in the
        # alternative) went in 90.58; this keeps them out.
        for variant in VARIANTS:
            layout = Layout(layout_data(variant))
            c = Cleanups(layout)
            name = lambda title: map_title(title, RENAME) if variant == 'alternative' else title
            extra = set()
            for host in layout.presets:
                if host == c.base:
                    continue
                for t in c.inv.by_layer(host):
                    if t.role != 'recovery':
                        continue
                    asked = {x for x, _ in c.left(host, t, c.guard(host, t.source, t.input), frozenset())} | {host}
                    extra |= {(host, t.source, target) for op, target in t.ops
                              if op == 'remove_layer' and target not in asked}
            self.assertEqual(extra, {(name(h), s, name(t)) for h, s, t in HELD_PAD_LAYERS}, variant)


if __name__ == "__main__":
    unittest.main()
