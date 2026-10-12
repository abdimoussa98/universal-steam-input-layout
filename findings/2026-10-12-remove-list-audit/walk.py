"""Random press sequences over the whole pad, and what is on the stack each time a bind with removes fires.

The walks of the owner release audit (findings/2026-10-11-owner-release-audit/walks.py) start in `Steering`
and never click a stick again, so they never fire a transition entry. These start in Base and use every
control: the four menu-plus-stick-click gestures, both menu buttons held (the way into `Menu Keys`), stick
clicks on their own, the face buttons, the D-pad, the back buttons, both triggers, both sticks and both pads.
A walk therefore passes through `Steering`, `Cursor Gyro`, `Gamepad` and `Menu Keys` and out again.

`Watcher` counts, for every bind that removes layers: how often it fired, and for each layer it names how
often that layer was on the stack at that moment. Given `pairs` (a layer -> layers its binds name), it also
counts how often such a layer was already on the stack when the first one was added, that is, under it.
"Never" is a sample's answer, not a proof.
"""
import hashlib
import random
from collections import Counter

from steam_layout.simulator import Simulator
import scenario
from scenario import DIRECTIONS, Pad

EVENTS = 90
BUTTONS = ("L1", "R1", "L1", "R1", "L1", "R1", "Start", "Select", "Start", "Select", "A", "B", "X", "Y",
           "Up", "Down", "Left", "Right", "LF", "RF", "L4", "L5", "R4", "R5")
WAITS = (5, 20, 40, 60, 120, 160, 210, 260, 400)
WAYS = ("up", "down", "left", "right")
OUT = ("edge", *DIRECTIONS.values())
MODES = ("Base", "Gyro", "Steering", "Cursor Gyro", "Gamepad", "Menu Keys")


class Watcher(Simulator):
    pairs = {}                                                   # host -> the layers to look for under it

    def __init__(self, layout, fired, on, modes, added=None, under=None, **options):
        self.fired, self.on, self.modes = fired, on, modes
        self.added, self.under = added if added is not None else Counter(), under if under is not None else Counter()
        super().__init__(layout, **options)

    def _note(self, what, detail):
        if what == "add" and detail in self.pairs:
            self.added[detail] += 1
            for target in self.pairs[detail]:
                if target in self.stack:
                    self.under[(detail, target)] += 1
        return super()._note(what, detail)

    def _run(self, entry, act=None, tap=False, commands=True):
        if commands:
            targets = [t for op, t in entry.ops if op == "remove_layer"]
            if targets:
                key = (entry.layer, entry.control, entry.kind, entry.index)
                self.fired[key] += 1
                stack = set(self.stack)
                for target in targets:
                    if target in stack:
                        self.on[(*key, target)] += 1
        result = super()._run(entry, act=act, tap=tap, commands=commands)
        for title in self.stack:
            if title in MODES:
                self.modes[title] += 1
        return result


def new_pad(variant, layout, rng, fired, on, modes, added=None, under=None):
    pad = Pad.__new__(Pad)                                       # Pad without reading the layout again
    pad.variant, pad.options, pad.layout = variant, {}, layout
    pad.sim = Watcher(layout, fired, on, modes, added, under,
                      exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
    pad._mark, pad._began = 0, tuple(pad.sim.stack)
    return pad


def let_go(pad, rng, missed, control):
    return pad.sim.lose(control) if rng.random() < missed else pad.sim.release(control)


def stick(pad, rng, missed, which):
    source, held = scenario.SOURCES[which], pad._held
    if not held(which, "touch"):
        return pad.touch(which)
    choice = rng.random()
    if held(which, "click"):
        return let_go(pad, rng, missed, (source, "click"))
    if choice < 0.12:
        return pad.sim.press((source, "click"))
    if which == "RS":
        if held(which, "edge"):
            return pad.recentre(which) if choice < 0.65 else pad.lift(which)
        return pad.push(which) if choice < 0.6 else pad.lift(which)
    if not any(held(which, part) for part in OUT):
        return pad.push(which, rng.choice(WAYS)) if choice < 0.78 else pad.lift(which)
    if choice < 0.6:
        return pad.recentre(which)
    if choice < 0.78:
        return pad.lift(which)
    free = [way for way in WAYS if not held(which, DIRECTIONS[way])]
    return pad.roll(which, rng.choice(free)) if free else pad.recentre(which)


def trackpad(pad, rng, which):
    held, sim = pad._held, pad.sim
    if held(which, "click"):
        return pad.let_go_pad(which, lift=rng.random() < 0.5)
    if not held(which, "touch"):
        return pad.touch(which)
    choice = rng.random()
    if any(held(which, part) for part in OUT):
        return pad.lift(which)
    if choice < 0.30:
        return pad.press_pad(which, "centre")
    if choice < 0.50:
        return pad.press_pad(which, rng.choice(WAYS))
    if choice < 0.60:
        return pad.press_pad(which, "ring " + rng.choice(WAYS))
    if choice < 0.80:                                            # a swipe: the thumb out to one side
        sim.press(pad.control(which + " edge"))
        return sim.press(pad.control(which + " " + DIRECTIONS[rng.choice(WAYS)]))
    return pad.lift(which)


def menu_click(pad, rng):
    """One of the four menu-plus-stick-click gestures, whatever else is held."""
    menu, which = rng.choice(("Start", "Select")), rng.choice(("LS", "RS"))
    source = scenario.SOURCES[which]
    if pad.control(menu) in pad.sim.held or pad._held(which, "click"):
        return pad.wait(20)
    pad.hold(menu).wait(rng.choice((30, 60, 120, 250)))
    pad.touch(which)
    pad.sim.press((source, "click"))
    pad.wait(rng.choice((20, 40, 80)))
    if rng.random() < 0.8:                                       # the click first, then the menu button
        pad.sim.release((source, "click"))
        pad.wait(rng.choice((10, 40, 120))).let_go(menu)
    else:
        pad.let_go(menu).wait(rng.choice((10, 40, 120)))
        pad.sim.release((source, "click"))
    return pad.wait(rng.choice((20, 100, 300)))


def both_menus(pad, rng):
    """Both menu buttons held: 150 ms of it is the way into `Menu Keys`."""
    first, second = rng.sample(("Start", "Select"), 2)
    if any(pad.control(menu) in pad.sim.held for menu in (first, second)):
        return pad.wait(20)
    pad.hold(first).wait(rng.choice((20, 60))).hold(second).wait(rng.choice((60, 180, 300)))
    return pad.let_go(rng.choice((first, second))).wait(rng.choice((10, 60))).let_go(
        *[menu for menu in (first, second) if pad.control(menu) in pad.sim.held]).wait(100)


def step(pad, rng, missed):
    """One random physical event that is possible now."""
    sim, roll = pad.sim, rng.random()
    if roll < 0.22:
        return pad.wait(rng.choice(WAITS))
    if roll < 0.52:
        name = rng.choice(BUTTONS)
        if pad.control(name) in sim.held:
            return pad.miss(name) if rng.random() < missed else pad.let_go(name)
        return pad.hold(name)
    if roll < 0.66:
        return stick(pad, rng, missed, "LS")
    if roll < 0.76:
        return stick(pad, rng, missed, "RS")
    if roll < 0.86:
        return trackpad(pad, rng, rng.choice(("LP", "RP")))
    if roll < 0.96:
        return menu_click(pad, rng)
    return both_menus(pad, rng)


def settle(pad):
    """Let everything go, as the layout sees it, and wait."""
    for which in ("LP", "RP"):
        if pad._held(which, "click"):
            pad.let_go_pad(which)
        pad.lift(which)
    for which in ("LS", "RS"):
        if pad._held(which, "click"):
            pad.sim.release((scenario.SOURCES[which], "click"))
        pad.lift(which)
    for control in sorted(pad.sim.held):
        pad.sim.release(control)
    pad.wait(1000)


def left_over(pad):
    return tuple(t for t in pad.sim.stack if t not in MODES)


def walk(pad, rng, missed, events=EVENTS):
    """One walk. Returns how it ended and, if it finished, the layers left over after each step of letting go:
    everything let go, then a thumb on each stick and off again."""
    try:
        if rng.random() < 0.4:                                   # Gyro on: the Modifier 2 quick tap in Base
            pad.hold("L1").wait(20).hold("R1").wait(40).let_go("R1").wait(20).let_go("L1").wait(400)
        for _ in range(events):
            step(pad, rng, missed)
        settle(pad)
        first = left_over(pad)
        pad.touch("LS").wait(50).lift("LS").wait(300).touch("RS").wait(50).lift("RS").wait(500)
        return "done", (first, left_over(pad))
    except NotImplementedError:                                  # a bind the simulator doesn't model
        return "stopped", None
    except RuntimeError:                                         # binds that keep firing without time passing
        return "looped", None
    except ValueError:                                           # a press the pad can't make from here
        return "refused", None


def batch(job):
    """(variant, label, layout data, seed, walks, missed[, pairs]) -> counts for one process."""
    from steam_layout.model import Layout
    variant, label, data, seed, count, missed, *rest = job
    layout = Layout(data)
    Watcher.pairs = rest[0] if rest else {}
    fired, on, modes, ends, left = Counter(), Counter(), Counter(), Counter(), []
    added, under, digests = Counter(), Counter(), []
    for index in range(count):
        rng = random.Random(seed * 100003 + index)               # the same walk whatever the layout
        pad = new_pad(variant, layout, rng, fired, on, modes, added, under)
        how, found = walk(pad, rng, missed)
        ends[how] += 1
        left.append(found)
        # Everything the walk did that a player or a later bind can tell: keys, wheel, haptics, beeps, and
        # every layer going on or off, with its time.
        text = repr([(when, what, detail) for when, what, detail in pad.sim.log]) + repr(pad.sim.stack)
        digests.append(hashlib.sha1(text.encode()).hexdigest())
    return variant, label, missed, fired, on, modes, ends, left, added, under, digests
