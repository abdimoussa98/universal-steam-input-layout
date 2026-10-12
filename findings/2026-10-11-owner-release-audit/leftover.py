"""Is anything left on the stack with fewer removes? 90.56 against the plan's trial layout, on the same walks.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/leftover.py <scratch dir> [walks per seed] [seeds]

`<scratch dir>` holds the trial layouts of plan_candidate.py after the fix pipeline. Both versions play the
same random walks (walks.py: the entry into `Steering`, then 60 random events), once with no release missed
and once with one button release in ten missed (let go while the Steam menu is open, A25). Then:

    let go      everything is let go as the layout sees it, both thumbs lifted, one second
    sticks      a thumb on each stick and off again: the stick touch cleanup functions
    drivers     a tap of each bumper (each trigger in the alternative layout)

After each step the layers on the stack that are not a mode (`Base`, `Gyro`, `Steering`, `Cursor Gyro`,
`Gamepad`, `Menu Keys`) are counted as left over.

The second half is the tightened R132 of the plan's part 4, across the whole layout. A "same-input remove" is
a remove whose target answers the bind's own input when it sits above the host: if the target is on top, the
host's bind does not run. The count is an upper bound of what the rule could trim, since a target that can sit
BELOW its host is taken off by the remove and stays listed. The walks split them: on the stack at least once
when the bind fired, never, or the bind never fired.
"""
import json
import random
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

from steam_layout.flow_model import resolve
from steam_layout.model import Layout
from steam_layout.simulator import Simulator
import scenario
from scenario import Pad
import first_driver as base

VERSIONS = ("90.56", "plan")
MISSED = (0.0, 0.10)


def same_input(layout):
    """{(layer, control, kind, index): [targets]} for removes whose target answers the bind's input over the host."""
    reader, found = Simulator(layout), {}
    for layer in layout.presets:
        for source, group in layout.active(layer).items():
            for name in group.get("inputs", {}):
                for entry in reader._entries_of(layer, source, name):
                    targets = [t for op, t in entry.ops if op == "remove_layer" and t != layer
                               and resolve(layout, (layer, t), source, name)[1] == t]
                    if targets:
                        found[(layer, (source, name), entry.kind, entry.index)] = targets
    return found


class Watcher(Simulator):
    def __init__(self, layout, watched, fired, on, **options):
        self.watched, self.fired, self.on = watched, fired, on
        super().__init__(layout, **options)

    def _run(self, entry, act=None, tap=False, commands=True):
        key = (entry.layer, entry.control, entry.kind, entry.index)
        if commands and key in self.watched:
            for target in self.watched[key]:
                self.fired[(*key, target)] += 1
                self.on[(*key, target)] += target in self.stack
        return super()._run(entry, act=act, tap=tap, commands=commands)


def left(pad):
    return tuple(t for t in pad.sim.stack if t not in base.MODES)


def batch(job):
    variant, version, data, seed, count, missed = job
    layout = Layout(data)
    watched, fired, on = same_input(layout), Counter(), Counter()
    ends = []
    for index in range(count):
        rng = random.Random(seed * 100003 + index)               # the same walk for both versions
        pad = Pad.__new__(Pad)
        pad.variant, pad.options, pad.layout = variant, {}, layout
        pad.sim = Watcher(layout, watched, fired, on, exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
        pad._mark, pad._began = 0, tuple(pad.sim.stack)
        try:
            base.walk_events(pad, rng, missed)
            base.settle(pad)
            first = left(pad)
            pad.touch("LS").wait(50).lift("LS").wait(300).touch("RS").wait(50).lift("RS").wait(500)
            second = left(pad)
            pad.tap("L1").wait(500).tap("R1").wait(500)
            ends.append((first, second, left(pad)))
        except (RuntimeError, NotImplementedError, ValueError):
            ends.append(None)
    return variant, version, missed, ends, fired, on


def main():
    out = Path(sys.argv[1])
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 375
    seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    data = {variant: {"90.56": scenario.layout_data(variant),
                      "plan": json.loads((out / f"{variant}.json").read_text(encoding="utf-8"))}
            for variant in scenario.VARIANTS}
    jobs = [(variant, version, data[variant][version], seed, count, missed) for variant in scenario.VARIANTS
            for version in VERSIONS for missed in MISSED for seed in range(1, seeds + 1)]
    with Pool() as pool:
        found = pool.map(batch, jobs)
    ends, fired, on = defaultdict(list), defaultdict(Counter), defaultdict(Counter)
    for variant, version, missed, walk_ends, walk_fired, walk_on in found:      # the pool keeps the jobs' order
        ends[(variant, version, missed)] += walk_ends
        fired[(variant, version)].update(walk_fired)
        on[(variant, version)].update(walk_on)
    steps = ("let go", "sticks", "drivers")
    for variant in scenario.VARIANTS:
        for missed in MISSED:
            old, new = ends[(variant, "90.56", missed)], ends[(variant, "plan", missed)]
            both = [(a, b) for a, b in zip(old, new) if a is not None and b is not None]
            print(f"\n{variant}, {'one release in ten missed' if missed else 'no release missed'}: "
                  f"{len(both)} walks that finish on both versions ({len(old) - len(both)} do not)")
            for index, step in enumerate(steps):
                a = sum(1 for o, _ in both if o[index])
                b = sum(1 for _, n in both if n[index])
                only_new = sum(1 for o, n in both if n[index] and not o[index])
                only_old = sum(1 for o, n in both if o[index] and not n[index])
                print(f"  after {step:8s} walks with a layer left: 90.56 {a:5d}, plan {b:5d}; "
                      f"only on the plan {only_new}, only on 90.56 {only_old}")
            for version, column in (("90.56", 0), ("plan", 1)):
                for index, step in enumerate(steps):
                    layers = Counter(t for pair in both for t in pair[column][index])
                    if layers:
                        print(f"    {version}, left after {step}: "
                              + ", ".join(f"{t} ({n})" for t, n in layers.most_common(8)))
    print("\nSame-input removes (the tightened R132), per layout:")
    for variant in scenario.VARIANTS:
        for version in VERSIONS:
            layout = Layout(data[variant][version])
            watched = same_input(layout)
            total = sum(len(targets) for targets in watched.values())
            steering = sum(len(targets) for key, targets in watched.items() if key[0].startswith(("Steering", "Lenkung")))
            seen = Counter()
            for key, targets in watched.items():
                for target in targets:
                    full = (*key, target)
                    count_fired = fired[(variant, version)][full]
                    seen["never fired" if not count_fired else
                         "on the stack at least once" if on[(variant, version)][full] else "never on the stack"] += 1
            print(f"  {variant}, {version}: {total} in {len(watched)} binds ({steering} in Steering layers); "
                  + ", ".join(f"{label}: {seen[label]}" for label in ("never on the stack", "on the stack at least once", "never fired")))
            if variant == "default":
                rows = Counter()
                for key, targets in watched.items():
                    for target in targets:
                        full = (*key, target)
                        count_fired = fired[(variant, version)][full]
                        state = ("never fired" if not count_fired else
                                 "on" if on[(variant, version)][full] else "never on")
                        rows[(key[0], "/".join(key[1]), key[2], state)] += 1
                        rows[("fired", key[0], "/".join(key[1]), key[2])] = count_fired
                for (layer, control, kind, state), number in sorted((k, v) for k, v in rows.items() if k[0] != "fired"):
                    print(f"      {layer} | {control} {kind}: {number} {state} "
                          f"(fired {rows[('fired', layer, control, kind)]})")


if __name__ == "__main__":
    main()
