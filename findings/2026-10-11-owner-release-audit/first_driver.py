"""Decision 2, replayed: should the Steering Modifier 2 quick tap take off the first driver's layer?

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/first_driver.py            # the gestures
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/first_driver.py walks 750  # and the walks

In memory only. Four versions of the second driver's Release in the two Steering Modifier 2 layers:

    today          the 88 removes of 90.56
    leave it       the Modifier 2 layer and its cover
    take it off    the same, and the first driver's layer (the W or S layer)
    off and back   the same three, and the Release ends by adding the first driver's layer again

The last three leave `Gyro`, the helpers, the pad layers and the menu layers alone (decision 1 and the
proposed boundary). Part one replays named gestures on each, with a bind exposed under a held button firing
at once and on its next repeat (A9). Part two plays the same random walks on each (walks.py) and counts what
differs: the drive key let go at a quick tap, `Steering` gone by the next press or release, and layers left
on when everything has been let go.
"""
import copy
import random
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

from steam_layout.model import TARGET, Layout, actions, map_title
from steam_layout.simulator import Simulator
import scenario
from scenario import Pad
import walks as probe

RENAME = {"L1": "L2", "R1": "R2"}
MOD2 = {"Steering | L1!R1: Modifier 2": ("L1", "R1", "R1: Tap Cover", "Steering | L1: S Key", "S"),   # layer -> first driver,
        "Steering | R1!L1: Modifier 2": ("R1", "L1", "L1: Tap Cover", "Steering | R1: W Key", "W")}   # second, cover, first's layer, key
VERSIONS = ("today", "leave it", "take it off", "off and back")
MODES = {"Base", "Gyro", "Steering", "Cursor Gyro", "Gamepad", "Menu Keys"}


def build(variant, version):
    """A copy of the working layout with the two quick tap Releases in this version."""
    data = copy.deepcopy(scenario.layout_data(variant))
    if version == "today":
        return data
    layout = Layout(data)
    name = (lambda title: map_title(title, RENAME)) if variant == "alternative" else (lambda title: title)
    for host, (first, second, cover, driver, _) in MOD2.items():
        keep = {name(host), name(cover)} | ({name(driver)} if version != "leave it" else set())
        source, inp = scenario.BUTTONS[scenario.ROLES[variant][second]]
        release = layout.active(name(host))[source]["inputs"][inp]["activators"]["release"]
        found = [a for a in actions(release) if (m := TARGET.search(a)) and layout.resolve(m.group(2)) in keep]
        if version == "off and back":                    # stored first, so it runs last (arrays run bottom to top)
            number = layout.order.index(next(k for k, t in layout.titles.items() if t == name(driver))) + 1
            found = [f"controller_action add_layer {number} 0 0, , "] + found
        release["bindings"]["binding"] = found
    return data


# --- part one: named gestures ------------------------------------------------------------------------

def key_gap(pad, key):
    """How the drive key fared since the mark: "held", "let go and back in N ms", or "let go"."""
    gone, worst = None, None
    for ms, what, detail in pad.sim.log[pad._mark:]:
        if detail != key:
            continue
        if what in ("up", "handover"):
            gone = ms
        elif what == "down" and gone is not None:
            worst, gone = max(worst or 0, ms - gone), None
    if gone is not None:
        return "let go"
    return "held" if worst is None else f"let go and back in {worst} ms"


def steering(pad):
    pad.enter_steering().lift("LS").wait(300)
    return pad


def plain(pad, first, second, key):
    pad.hold(first).wait(400).mark().hold(second).wait(60).let_go(second).wait(300)
    return f"{key} {key_gap(pad, key)}; stack {' > '.join(pad.names()[1:])}"


def stick_out(pad, first, second, key):
    pad.hold(first).wait(100).hold(second).wait(30).push("LS", "up").wait(30).mark().let_go(second).wait(300)
    return f"Steering {'stays' if pad.has('Steering') else 'ENDS'}; {key} {key_gap(pad, key)}"


def thumbs(pad, first, second, key):
    pad.hold(first).wait(300).touch("LS").wait(300).touch("RS").wait(300)
    before = pad.names()
    pad.mark().hold(second).wait(60).let_go(second).wait(300)
    return "stack unchanged" if pad.names() == before else f"stack {' > '.join(before[2:])} becomes {' > '.join(pad.names()[2:])}"


def missed_first(pad, first, second, key):
    """Both held, the Steam menu opens, the first driver is let go unseen, then the quick tap ends."""
    pad.hold(first).wait(100).hold(second).wait(60).miss(first).wait(40).let_go(second).wait(1000)
    after = pad.names()[2:]
    pad.tap(first).wait(400)
    return (f"left on: {', '.join(after) or 'nothing'}; keys {pad.down() or 'none'}; "
            f"after one tap of {first}: {', '.join(pad.names()[2:]) or 'nothing'}")


def missed_first_covered(pad, first, second, key):
    """The same with the second driver held past 200 ms first, so the cover's Release answers."""
    pad.hold(first).wait(100).hold(second).wait(300).miss(first).wait(40).let_go(second).wait(1000)
    return f"left on: {', '.join(pad.names()[2:]) or 'nothing'}; keys {pad.down() or 'none'}"


def missed_both(pad, first, second, key):
    """Both held, both let go unseen, then the second driver is tapped again."""
    pad.hold(first).wait(100).hold(second).wait(60).miss(first, second).wait(1000)
    stale = pad.names()[2:]
    pad.tap(second, 60).wait(400)
    after = pad.names()[2:]
    pad.tap(first).wait(400)
    return (f"stale: {', '.join(stale)}; after a tap of {second}: {', '.join(after) or 'nothing'}; "
            f"then a tap of {first}: {', '.join(pad.names()[2:]) or 'nothing'}")


GESTURES = (("1. Hold the first driver, tap the second (60 ms)", plain),
            ("2. Both drivers, stick pushed fully up, the second let go", stick_out),
            ("3. First driver held, both thumbs resting on the sticks, tap the second", thumbs),
            ("4. Both held, the first let go unseen (Steam menu), the second let go inside 200 ms", missed_first),
            ("5. The same, the second held past 200 ms first (the cover's Release answers)", missed_first_covered),
            ("6. Both held, both let go unseen, then the second tapped", missed_both))


def replay():
    for title, gesture in GESTURES:
        print(f"\n{title}")
        for version in VERSIONS:
            seen = Counter()
            for variant in scenario.VARIANTS:
                data = build(variant, version)
                for exposed in (True, False):
                    for host, (first, second, _, _, key) in MOD2.items():
                        pad = steering(Pad(variant, data=data, exposed_fires=exposed))
                        seen[gesture(pad, first, second, key).replace(first, "first").replace(second, "second")
                             .replace("W Key", "drive key").replace("S Key", "drive key")
                             .replace(f"{key} ", "the drive key ").replace("L2", "L1").replace("R2", "R1")] += 1
            for result, count in seen.most_common():
                print(f"  {version:13s} {count} of 8: {result}")


# --- part two: the same walks on each version ------------------------------------------------------

class Watcher(Simulator):
    """Counts what a quick tap does while the first driver is held and typing: the drive key let go, and
    `Steering` gone by the next press or release (nothing but the tap and timers can have ended it)."""
    LABELS = ("quick taps with the first driver held and typing", "the drive key let go and taken up at the same moment",
              "the drive key up after the tap", "Steering gone before the next press or release")

    def __init__(self, layout, quick, steering, **options):
        self.quick, self.steering, self.tapped, self.pending, self.found = quick, steering, None, None, Counter()
        super().__init__(layout, **options)

    def _run(self, entry, act=None, tap=False, commands=True):
        if entry.kind == "release" and commands and (entry.layer, entry.control) in self.quick:
            first, key = self.quick[(entry.layer, entry.control)]
            if first in self.held and key in self.down() and self.steering in self.stack:
                self.tapped = (first, key, len(self.log))
        return super()._run(entry, act=act, tap=tap, commands=commands)

    def _check(self):
        """At the next physical event: is `Steering` still on, with the first driver still held?"""
        if self.pending and self.pending in self.held and self.steering not in self.stack:
            self.found[self.LABELS[3]] += 1
        self.pending = None

    def press(self, control):
        self._check()
        return super().press(control)

    def lose(self, control):
        self._check()
        return super().lose(control)

    def release(self, control):
        self._check()
        self.tapped = None
        result = super().release(control)
        if self.tapped:
            first, key, since = self.tapped
            self.found[self.LABELS[0]] += 1
            if key not in self.down():
                self.found[self.LABELS[2]] += 1
            elif any(what in ("up", "handover") and detail == key for _, what, detail in self.log[since:]):
                self.found[self.LABELS[1]] += 1
            self.pending = first
        return result


def settle(pad):
    """Let everything go, as the layout sees it, and wait."""
    for which in ("LP", "RP"):
        if pad._held(which, "click"):
            pad.let_go_pad(which)
        pad.lift(which)
    for stick in ("LS", "RS"):
        if pad._held(stick, "click"):
            pad.sim.release((scenario.SOURCES[stick], "click"))
        pad.lift(stick)
    for control in sorted(pad.sim.held):
        pad.sim.release(control)
    pad.wait(1000)


def batch(job):
    variant, version, seed, count = job
    layout, rng = Layout(build(variant, version)), random.Random(seed)
    name = (lambda title: map_title(title, RENAME)) if variant == "alternative" else (lambda title: title)
    quick = {}
    for host, (first, second, _, _, key) in MOD2.items():
        control = scenario.BUTTONS[scenario.ROLES[variant][second]]
        quick[(name(host), control)] = (scenario.BUTTONS[scenario.ROLES[variant][first]], key)
    found, ends = Counter(), []
    for _ in range(count):
        pad = Pad.__new__(Pad)
        pad.variant, pad.options, pad.layout = variant, {}, layout
        pad.sim = Watcher(layout, quick, "Steering", exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
        pad._mark, pad._began = 0, tuple(pad.sim.stack)
        state = rng.getstate()
        try:
            walk_events(pad, rng)
            settle(pad)
            ends.append(tuple(t for t in pad.sim.stack if t not in MODES))
        except (RuntimeError, NotImplementedError, ValueError):
            ends.append(None)
            rng.setstate(state)                               # keep the versions on the same walks:
            for _ in range(2000):                             # move this walk's random numbers out of the way
                rng.random()
        found.update(pad.sim.found)
    return variant, version, found, ends


def walk_events(pad, rng, missed=0.10):
    """walks.py's walk on a pad that is already made: the entry into `Steering`, then 60 random events."""
    if rng.random() < 0.5:
        pad.hold("L1").wait(20).hold("R1").wait(40).let_go("R1").wait(20).let_go("L1").wait(400)
    if rng.random() < 0.5:
        pad.touch("RS").wait(20)
    pad.hold("Start").click("LS").let_go("Start")
    if rng.random() < 0.7:
        pad.flick("LS", "left").wait(300)
    if rng.random() < 0.5:
        pad.lift("LS").wait(50)
    for _ in range(probe.EVENTS):
        probe.step(pad, rng, missed, probe.WAITS)


def walks(count=750, seeds=8):
    jobs = [(variant, version, seed, count) for variant in scenario.VARIANTS for version in VERSIONS
            for seed in range(1, seeds + 1)]
    with Pool() as pool:
        done = pool.map(batch, jobs)
    print(f"\nThe same {count * seeds} walks per layout on each version (60 events, 10% of button releases missed), both layouts:")
    totals, ends = defaultdict(Counter), defaultdict(list)
    for variant, version, found, ended in done:
        totals[version].update(found)
        ends[version] += ended
    for version in VERSIONS:
        print(f"\n  {version}")
        for label in Watcher.LABELS:
            print(f"    {label}: {totals[version][label]}")
        finished = [e for e in ends[version] if e is not None]
        left = [e for e in finished if e]
        drivers = [e for e in left if any("W Key" in t or "S Key" in t for t in e)]
        print(f"    walks finished: {len(finished)}; with a layer left on at the end: {len(left)}; "
              f"with a W or S layer left on: {len(drivers)}")
    same = sum(1 for row in zip(*(ends[v] for v in VERSIONS)) if None not in row)
    for version in VERSIONS[1:]:
        worse = sum(1 for a, b in zip(ends["today"], ends[version]) if a is not None and b is not None and set(b) - set(a))
        better = sum(1 for a, b in zip(ends["today"], ends[version]) if a is not None and b is not None and set(a) - set(b))
        print(f"\n  {version} against today, walk by walk ({same} finished on all four): "
              f"{worse} end with a layer today's does not leave, {better} without one today's leaves")


if __name__ == "__main__":
    replay()
    if len(sys.argv) > 1 and sys.argv[1] == "walks":
        walks(*[int(a) for a in sys.argv[2:]])
