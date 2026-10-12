"""Where the walks with and without the Steering Modifier 2 cover part ways, and after a second driver's
Release whether `Steering` is still on.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/cover_diverge.py

In memory only, on cover_timer.py's two versions ("leave it" and "no cover") and, for the second count, on
the layouts as they are. 3,000 walks per layout and per rate of missed releases (none, one in ten).

1. Each walk runs on both versions. The cover's own adds and removes and the timer's bump are set aside;
   the first other line where the two logs differ is sorted into:
     stale Modifier 2 cleared   "leave it" removes a Steering Modifier 2 layer there and "no cover" does not
     another timer              a layer added by a delay lands at a different time, or in one version only
     other                      anything else
2. Every Release of the second driver that a Steering Modifier 2 layer or its cover answers, and how often
   `Steering` is gone before the next press or release: with the other driver still held, and with none held.
"""
import random
from collections import Counter
from multiprocessing import Pool

from steam_layout.model import Layout, map_title
from steam_layout.simulator import Simulator
import scenario
from scenario import Pad
import first_driver as base
import cover_timer as cover

WALKS, SEEDS, RATES = 750, 4, (0.0, 0.10)
DRIVERS = {"default": (("switch", "left_bumper"), ("switch", "right_bumper")),
           "alternative": (("left_trigger", "edge"), ("right_trigger", "edge"))}


class Watcher(Simulator):
    """Counts the second driver's Releases out of a Steering Modifier 2, and `Steering` gone after one."""

    def __init__(self, layout, mod2, drivers, **options):
        self.mod2, self.drivers, self.hit, self.pending, self.found = mod2, drivers, False, None, Counter()
        super().__init__(layout, **options)

    def _run(self, entry, act=None, tap=False, commands=True):
        hosts = self.mod2.get(entry.control, ())
        if entry.kind == "release" and commands and any(t in self.stack for t in hosts) and "Steering" in self.stack \
                and (entry.layer in hosts or entry.layer.endswith(": Tap Cover")):
            self.hit = True
        return super()._run(entry, act=act, tap=tap, commands=commands)

    def _check(self):
        if self.pending is not None and "Steering" not in self.stack:
            self.found["gone, the other driver held" if self.pending else "gone, no driver held"] += 1
        self.pending = None

    def press(self, control):
        self._check()
        return super().press(control)

    def lose(self, control):
        self._check()
        return super().lose(control)

    def release(self, control):
        self._check()
        self.hit = False
        result = super().release(control)
        if self.hit:
            self.found["Releases"] += 1
            self.pending = any(d in self.held for d in self.drivers)
        return result


def run(variant, layout, state, missed, mod2=None):
    rng = random.Random()
    rng.setstate(state)
    pad = Pad.__new__(Pad)
    pad.variant, pad.options, pad.layout = variant, {}, layout
    options = {"exposed_fires": rng.random() < 0.5, "reverse_ties": rng.random() < 0.5}
    pad.sim = Watcher(layout, mod2, DRIVERS[variant], **options) if mod2 else Simulator(layout, **options)
    pad._mark, pad._began = 0, tuple(pad.sim.stack)
    try:
        base.walk_events(pad, rng, missed)
        base.settle(pad)
    except (RuntimeError, NotImplementedError, ValueError):
        return None, rng
    return pad, rng


def shared(log, covers):
    return [(ms, what, detail) for ms, what, detail in log
            if not (what in ("add", "remove") and detail in covers) and not (what == "haptic" and "Modifier 2" in detail)]


def batch(job):
    variant, seed, missed = job
    name = (lambda title: map_title(title, base.RENAME)) if variant == "alternative" else (lambda title: title)
    layouts = {version: Layout(cover.build(variant, version)) for version in cover.VERSIONS}
    layouts["today"] = Layout(scenario.layout_data(variant))
    covers = {name(c) for _, _, c, _, _ in base.MOD2.values()}
    hosts = {name(host) for host in base.MOD2}
    mod2 = {scenario.BUTTONS[scenario.ROLES[variant][second]]: {name(host)} for host, (_, second, *_) in base.MOD2.items()}
    rng, apart, ends = random.Random(seed), Counter(), {version: Counter() for version in layouts}
    for _ in range(WALKS):
        state = rng.getstate()
        pads = {}
        for version, layout in layouts.items():
            pads[version], after = run(variant, layout, state, missed, mod2)
            if pads[version]:
                ends[version].update(pads[version].sim.found)
        if pads["leave it"] is None:
            for _ in range(2000):
                rng.random()
            continue
        rng.setstate(after.getstate() if pads["today"] else run(variant, layouts["leave it"], state, missed)[1].getstate())
        a, b = pads["leave it"], pads["no cover"]
        if b is None:
            continue
        apart["walks"] += 1
        if tuple(a.sim.typed()) == tuple(b.sim.typed()) and a.sim.stack == b.sim.stack:
            continue
        la, lb = shared(a.sim.log, covers), shared(b.sim.log, covers)
        at = next((i for i, (x, y) in enumerate(zip(la, lb)) if x != y), min(len(la), len(lb)))
        x, y = (la[at] if at < len(la) else None), (lb[at] if at < len(lb) else None)
        if x and x[1] == "remove" and x[2] in hosts:
            apart["stale Modifier 2 cleared"] += 1
        elif any(line and line[1] == "add" for line in (x, y)):
            apart["another timer"] += 1
        else:
            apart["other"] += 1
    return missed, apart, ends


def main():
    jobs = [(variant, seed, missed) for variant in scenario.VARIANTS for seed in range(1, SEEDS + 1) for missed in RATES]
    with Pool() as pool:
        done = pool.map(batch, jobs)
    for rate in RATES:
        apart, ends = Counter(), {}
        for missed, found, ended in done:
            if missed == rate:
                apart.update(found)
                for version, counts in ended.items():
                    ends.setdefault(version, Counter()).update(counts)
        print(f"\n{int(rate * 100)}% of button releases missed, {WALKS * SEEDS} walks per layout:")
        differ = apart["stale Modifier 2 cleared"] + apart["another timer"] + apart["other"]
        print(f"  1. 'leave it' against 'no cover': {apart['walks']} walks finished on both, {differ} differ: "
              f"{apart['stale Modifier 2 cleared']} stale Modifier 2 cleared, {apart['another timer']} another timer, "
              f"{apart['other']} other")
        for version in ("today", *cover.VERSIONS):
            found = ends[version]
            print(f"  2. {version}: {found['Releases']} Releases of the second driver out of a Steering Modifier 2; "
                  f"Steering gone with the other driver held {found['gone, the other driver held']}, "
                  f"with no driver held {found['gone, no driver held']}")


if __name__ == "__main__":
    main()
