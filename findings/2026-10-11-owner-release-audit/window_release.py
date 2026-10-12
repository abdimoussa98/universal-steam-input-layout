"""A driver's Release in a stick window: does it take off the layer of a driver that is still held?

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/window_release.py <dir> [<dir> ...]

Each directory holds `default.json` and `alternative.json` (the working layouts copied there, or the trial
layouts of plan_candidate.py). walks.py's random walks, 6,000 per layout and per rate of missed releases.
Counts the Releases of R1 or L1 that a stick window answers, and among them the ones where the other
driver's layer was on with that driver held, and the ones that took that layer off.
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
LABELS = ("a driver's Release answered by a stick window", "the other driver held, its layer on",
          "the held driver's layer taken off")


class Watcher(Simulator):
    def __init__(self, layout, info, **options):
        self.info, self.found = info, Counter()
        super().__init__(layout, **options)

    def _run(self, entry, act=None, tap=False, commands=True):
        watched = entry.kind == "release" and commands and entry.layer in self.info["windows"] \
            and entry.control in self.info["drivers"]
        held = False
        if watched:
            other, control = self.info["drivers"][entry.control]
            self.found[LABELS[0]] += 1
            held = other in self.stack and control in self.held
            self.found[LABELS[1]] += held
        result = super()._run(entry, act=act, tap=tap, commands=commands)
        if held and other not in self.stack:
            self.found[LABELS[2]] += 1
        return result


def batch(job):
    out, variant, seed, missed = job
    layout = Layout(json.loads((Path(out) / f"{variant}.json").read_text(encoding="utf-8")))
    name = (lambda title: map_title(title, base.RENAME)) if variant == "alternative" else (lambda title: title)
    button = lambda driver: scenario.BUTTONS[scenario.ROLES[variant][driver]]
    info = {"windows": {name(w) for w in WINDOWS},
            "drivers": {button("R1"): (name("Steering | L1: S Key"), button("L1")),
                        button("L1"): (name("Steering | R1: W Key"), button("R1"))}}
    rng, found = random.Random(seed), Counter()
    for _ in range(750):
        pad = Pad.__new__(Pad)
        pad.variant, pad.options, pad.layout = variant, {}, layout
        pad.sim = Watcher(layout, info, exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
        pad._mark, pad._began = 0, tuple(pad.sim.stack)
        state = rng.getstate()
        try:
            base.walk_events(pad, rng, missed)
        except (RuntimeError, NotImplementedError, ValueError):
            rng.setstate(state)
            for _ in range(2000):
                rng.random()
        found.update(pad.sim.found)
    return out, missed, found


def main():
    outs = sys.argv[1:]
    jobs = [(out, variant, seed, missed) for out in outs for variant in scenario.VARIANTS for seed in range(1, 9)
            for missed in (0.0, 0.10)]
    with Pool() as pool:
        done = pool.map(batch, jobs)
    for out in outs:
        for rate in (0.0, 0.10):
            total = Counter()
            for where, missed, found in done:
                if where == out and missed == rate:
                    total.update(found)
            print(f"{Path(out).name}, {int(rate * 100)}% of button releases missed: "
                  + "; ".join(f"{label} {total[label]}" for label in LABELS))


if __name__ == "__main__":
    main()
