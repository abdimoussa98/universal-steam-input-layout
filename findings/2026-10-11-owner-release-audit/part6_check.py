"""Part 6 of the two-driver plan, measured: are the layers it stops removing ever on when those binds fire?

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/part6_check.py <scratch dir>

Reads the trial layouts of plan_candidate.py (after the fix pipeline) and plays walks.py's random walks on them,
6,000 per layout and per rate of missed releases (none, one in ten). For the six binds of the W and S layers
that part 6 shortens (each layer's Modifier 2 entry on the other driver, and its Release on either driver), it
counts how often the bind fired and how often a stick window or a Steering Modifier 2 layer was on the stack at
that moment. Part 6 no longer removes those, so every such firing would leave one on.
"""
import json
import random
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

from steam_layout.model import Layout, map_title
from steam_layout.simulator import Simulator
import scenario
from scenario import Pad
import first_driver as base

WINDOWS = ("Steering | LS Up: Double Tap", "Steering | LS Down: Double Tap")


class Watcher(Simulator):
    def __init__(self, layout, watched, named, **options):
        self.watched, self.named, self.found = watched, named, Counter()
        super().__init__(layout, **options)

    def _run(self, entry, act=None, tap=False, commands=True):
        label = self.watched.get((entry.layer, entry.control, "release" if entry.kind == "release" else "entry"))
        if label and commands and (entry.kind == "release" or any(op == "add_layer" for op, _ in entry.ops)):
            self.found[label] += 1
            if any(t in self.stack for t in self.named["windows"]):
                self.found[label + ", a stick window on"] += 1
            if any(t in self.stack for t in self.named["mod2"]):
                self.found[label + ", a Steering Modifier 2 layer on"] += 1
        return super()._run(entry, act=act, tap=tap, commands=commands)


def batch(job):
    out, variant, seed, missed = job
    layout = Layout(json.loads((Path(out) / f"{variant}.json").read_text(encoding="utf-8")))
    name = (lambda title: map_title(title, base.RENAME)) if variant == "alternative" else (lambda title: title)
    button = lambda driver: scenario.BUTTONS[scenario.ROLES[variant][driver]]
    watched = {}
    for host, (first, second, _, driver, _) in base.MOD2.items():
        watched[(name(driver), button(second), "entry")] = "the Modifier 2 entry"
        watched[(name(driver), button(first), "release")] = "the driver's own Release"
        watched[(name(driver), button(second), "release")] = "the other driver's Release"
    named = {"windows": {name(w) for w in WINDOWS}, "mod2": {name(h) for h in base.MOD2}}
    rng, found = random.Random(seed), Counter()
    for _ in range(750):
        pad = Pad.__new__(Pad)
        pad.variant, pad.options, pad.layout = variant, {}, layout
        pad.sim = Watcher(layout, watched, named, exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
        pad._mark, pad._began = 0, tuple(pad.sim.stack)
        state = rng.getstate()
        try:
            base.walk_events(pad, rng, missed)
        except (RuntimeError, NotImplementedError, ValueError):
            rng.setstate(state)
            for _ in range(2000):
                rng.random()
        found.update(pad.sim.found)
    return missed, found


def main():
    out = sys.argv[1]
    jobs = [(out, variant, seed, missed) for variant in scenario.VARIANTS for seed in range(1, 9) for missed in (0.0, 0.10)]
    with Pool() as pool:
        done = pool.map(batch, jobs)
    for rate in (0.0, 0.10):
        total = Counter()
        for missed, found in done:
            if missed == rate:
                total.update(found)
        print(f"\n{int(rate * 100)}% of button releases missed, 6000 walks per layout, in the W and S layers:")
        for label in ("the Modifier 2 entry", "the driver's own Release", "the other driver's Release"):
            print(f"  {label}: fired {total[label]}; a stick window on {total[label + ', a stick window on']}; "
                  f"a Steering Modifier 2 layer on {total[label + ', a Steering Modifier 2 layer on']}")


if __name__ == "__main__":
    main()
