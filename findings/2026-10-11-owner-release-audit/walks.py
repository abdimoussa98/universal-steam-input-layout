"""Random press sequences on the press simulator: what is on the stack when a modifier button's Release fires.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/walks.py [walks per seed] [seeds] [missed %] [short]

The backward chains don't follow chords or delayed adds, so their "can be on the stack"
misses layers (found on 2026-10-11). This asks the simulator. Each walk enters `Steering`
from Base (half with `Gyro` on, half with a thumb resting first), then plays 60 random
events: presses, releases, waits, stick and pad moves, and missed releases (a button let
go while the Steam menu is open, A25). Every time a Release that removes layers fires, the
stack just before it is kept. A fourth argument of 1 makes every wait 1 to 80 ms, for
presses that fall inside one timer.

For each Release on a modifier button in a Steering layer or a shared cover it prints how
often it fired, which of the layers it lists were on the stack at that moment at least
once, and which never were. "Never" is a sample's answer, not a proof.
"""
import random
import sys
from collections import defaultdict
from multiprocessing import Pool

from steam_layout.model import Layout
from steam_layout.simulator import Simulator
from scenario import DIRECTIONS, Pad, layout_data

VARIANTS = ("default", "alternative")
EVENTS = 60
BUTTONS = ("L1", "R1", "L1", "R1", "L1", "R1", "Start", "Select", "A", "Up", "LF", "RF")   # the modifiers weigh more
WAITS = (5, 20, 40, 60, 120, 160, 210, 260, 400)
SHORT_WAITS = (1, 3, 5, 10, 20, 30, 50, 80)
WAYS = ("up", "down", "left", "right")
OUT = ("edge", *DIRECTIONS.values())


class Recorder(Simulator):
    """A simulator that keeps the stack before every Release that removes layers."""

    def __init__(self, layout, seen, **options):
        self.seen = seen
        super().__init__(layout, **options)

    def _run(self, entry, act=None, tap=False, commands=True):
        if entry.kind == "release" and commands and any(op == "remove_layer" for op, _ in entry.ops):
            self.seen[(entry.layer, entry.control)].append(self.stack)
        return super()._run(entry, act=act, tap=tap, commands=commands)


def new_pad(variant, layout, rng, seen):
    pad = Pad.__new__(Pad)                                       # Pad without reading the layout again
    pad.variant, pad.options, pad.layout = variant, {}, layout
    pad.sim = Recorder(layout, seen, exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
    pad._mark, pad._began = 0, tuple(pad.sim.stack)
    return pad


def step(pad, rng, missed, waits):
    """One random physical event that is possible now."""
    sim, roll = pad.sim, rng.random()
    if roll < 0.28:
        return pad.wait(rng.choice(waits))
    if roll < 0.60:
        name = rng.choice(BUTTONS)
        if pad.control(name) in sim.held:
            return pad.miss(name) if rng.random() < missed else pad.let_go(name)
        return pad.hold(name)
    if roll < 0.76:                                              # the left stick
        if not pad._held("LS", "touch"):
            return pad.touch("LS")
        choice = rng.random()
        if not any(pad._held("LS", part) for part in OUT):
            return pad.push("LS", rng.choice(WAYS)) if choice < 0.75 else pad.lift("LS")
        if choice < 0.55:
            return pad.recentre("LS")
        if choice < 0.75:
            return pad.lift("LS")
        free = [way for way in WAYS if not pad._held("LS", DIRECTIONS[way])]
        return pad.roll("LS", rng.choice(free)) if free else pad.recentre("LS")
    if roll < 0.85:                                              # the right stick
        if not pad._held("RS", "touch"):
            return pad.touch("RS")
        choice = rng.random()
        if pad._held("RS", "edge"):
            return pad.recentre("RS") if choice < 0.6 else pad.lift("RS")
        return pad.push("RS") if choice < 0.5 else pad.lift("RS")
    which = rng.choice(("LP", "RP"))                             # the pads: rest, swipe, click in the centre or outside
    if pad._held(which, "click"):
        return pad.let_go_pad(which, lift=rng.random() < 0.5)
    if not pad._held(which, "touch"):
        return pad.touch(which)
    choice = rng.random()
    if any(pad._held(which, part) for part in OUT):
        return pad.lift(which)
    if choice < 0.30:
        return pad.press_pad(which, "centre")
    if choice < 0.50:
        return pad.press_pad(which, rng.choice(WAYS))
    if choice < 0.60:
        return pad.press_pad(which, "ring " + rng.choice(WAYS))
    if choice < 0.80:                                            # a swipe: the thumb out to one side
        sim.press((pad.control(which + " edge")))
        return sim.press(pad.control(which + " " + DIRECTIONS[rng.choice(WAYS)]))
    return pad.lift(which)


def walk(variant, layout, rng, seen, missed, waits=WAITS):
    pad = new_pad(variant, layout, rng, seen)
    try:
        if rng.random() < 0.5:                                   # Gyro on: the Modifier 2 quick tap in Base
            pad.hold("L1").wait(20).hold("R1").wait(40).let_go("R1").wait(20).let_go("L1").wait(400)
        if rng.random() < 0.5:                                   # a thumb resting before the entry
            pad.touch("RS").wait(20)
        pad.hold("Start").click("LS").let_go("Start")
        if rng.random() < 0.7:
            pad.flick("LS", "left").wait(300)
        if rng.random() < 0.5:
            pad.lift("LS").wait(50)
        for _ in range(EVENTS):
            step(pad, rng, missed, waits)
    except NotImplementedError:                                  # a bind the simulator doesn't model
        return "stopped"
    except RuntimeError:                                         # binds that keep firing without time passing
        return "looped"
    return "done"


def batch(job):
    variant, seed, walks, missed, waits = job
    layout, rng, seen = Layout(layout_data(variant)), random.Random(seed), defaultdict(list)
    ends = defaultdict(int)
    for _ in range(walks):
        ends[walk(variant, layout, rng, seen, missed, waits)] += 1
    return variant, {key: (len(stacks), {t for stack in stacks for t in stack}) for key, stacks in seen.items()}, dict(ends)


def is_modifier(control):
    return control[1] in ("left_bumper", "right_bumper") or control[0] in ("left_trigger", "right_trigger")


def main(walks=1000, seeds=8, missed=4, short=0):
    waits = SHORT_WAITS if short else WAITS
    jobs = [(variant, seed, walks, missed / 100, waits) for variant in VARIANTS for seed in range(1, seeds + 1)]
    with Pool() as pool:
        found = pool.map(batch, jobs)
    for variant in VARIANTS:
        layout = Layout(layout_data(variant))
        reader = Simulator(layout)
        fired, on, ends = defaultdict(int), defaultdict(set), defaultdict(int)
        for name, seen, ended in found:
            if name != variant:
                continue
            for key, (count, layers) in seen.items():
                fired[key] += count
                on[key] |= layers
            for how, count in ended.items():
                ends[how] += count
        print(f"\n{variant}: {walks * seeds} walks of {EVENTS} events, waits of {waits[0]} to {waits[-1]} ms, "
              f"{missed}% of button releases missed; {dict(ends)}")
        for (layer, control), count in sorted(fired.items(), key=lambda item: (item[0][0], item[0][1])):
            if not is_modifier(control) or not (layer.startswith("Steering") or layer.endswith(": Tap Cover")):
                continue
            listed = list(dict.fromkeys(t for e in reader._entries_of(layer, *control) if e.kind == "release"
                                        for op, t in e.ops if op == "remove_layer"))
            hit = [t for t in listed if t in on[(layer, control)]]
            miss = [t for t in listed if t not in on[(layer, control)]]
            print(f"\n  {layer} | {control[1] if control[0] == 'switch' else '/'.join(control)}: fired {count} times")
            print(f"    lists {len(listed)}; on the stack at least once: {len(hit)}; never: {len(miss)}")
            print("    on the stack: " + (", ".join(hit) or "none"))
            if len(miss) <= 12:
                print("    never: " + (", ".join(miss) or "none"))
            print("    on the stack and left: " + (", ".join(sorted(on[(layer, control)] - set(listed) - {layout.base})) or "none"))


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:]])
