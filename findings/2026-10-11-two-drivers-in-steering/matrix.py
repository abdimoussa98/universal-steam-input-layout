"""Every two-driver gesture inside `Steering` with the left stick, on the press simulator: what goes wrong.

    PYTHONPATH=.:tests python3 findings/2026-10-11-two-drivers-in-steering/matrix.py [variant] [layout.json]

A gesture: hold one driver, bring the left stick to a state, press the other driver (100 or 400 ms),
optionally move the stick, let one driver go, then the other, then centre the stick. Each runs with a bind
exposed under a held button firing at once and on its next repeat (A9). 640 gestures per layout.

Flags: `Steering` gone while a driver is still held, both drive keys down together, the second driver
typing its drive key on the way to Modifier 2, no Modifier 2 after the second press, the held driver's key
not down, and layers or keys left at the end. The simulator holds a control or not, so "stick out" is the
stick at the rim.
"""
import itertools
import json
import sys
from collections import Counter, defaultdict

from scenario import Pad

DATA = {}
STATES = {
    "centre": lambda p, way: p,
    "out 100 ms": lambda p, way: p.push("LS", way).wait(100),
    "out 400 ms": lambda p, way: p.push("LS", way).wait(400),
    "window +20 ms": lambda p, way: p.flick("LS", way).wait(20),
    "window +100 ms": lambda p, way: p.flick("LS", way).wait(100),
    "scroll layer 60 ms": lambda p, way: p.flick("LS", way).wait(40).push("LS", way).wait(60),
    "scroll layer 400 ms": lambda p, way: p.flick("LS", way).wait(40).push("LS", way).wait(400),
    "window after scroll +20 ms": lambda p, way: p.flick("LS", way).wait(40).flick("LS", way).wait(20),
}
MOVES = {
    "stick as it is": lambda p, way: p,
    "stick pushed": lambda p, way: p.push("LS", way).wait(120),
    "stick centred": lambda p, way: p.recentre("LS").wait(120),
}
COLUMNS = ("A9 at once", "first driver", "stick way", "stick state", "second press ms", "move", "let go first")


def run(variant, options, first, way, state, press_ms, move, release_first):
    second = "L1" if first == "R1" else "R1"
    own, other = ("W", "S") if first == "R1" else ("S", "W")
    pad = Pad(variant, data=DATA.get(variant), **options)
    pad.enter_steering().lift("LS").wait(300)
    pad.hold(first).wait(500)
    STATES[state](pad, way)
    flags = []
    since = len(pad.sim.log)
    pad.hold(second).wait(press_ms)
    if other in pad.down() and own in pad.down():
        flags.append("W and S down together after the second press")
    if any(what == "down" and detail == other for _, what, detail in pad.sim.log[since:]):
        flags.append(f"the second driver typed {other} on its way to Modifier 2")
    if not any("Modifier 2" in t for t in pad.names()):
        flags.append("no Modifier 2 after the second press")
    MOVES[move](pad, way)
    out = any(pad._held("LS", part) for part in ("dpad_north", "dpad_south"))
    a, b = (first, second) if release_first == "first" else (second, first)
    pad.let_go(a).wait(120)
    if "Steering" not in pad.names():
        flags.append(f"Steering gone after the {release_first} driver was let go (stick {'out' if out else 'at centre'})")
    held_key = other if release_first == "first" else own
    if "Steering" in pad.names() and held_key not in pad.down():
        flags.append(f"{held_key} not down although its driver is still held")
    pad.let_go(b).wait(300)
    pad.lift("LS").wait(400)
    rest = [t for t in pad.names() if t not in ("Base", "Steering")]
    if "Steering" in pad.names() and rest:
        flags.append("left over at the end: " + ", ".join(rest))
    if pad.down():
        flags.append("keys down at the end: " + ", ".join(pad.down()))
    return flags


def main(variant="default"):
    seen, total = defaultdict(list), 0
    for exposed in (True, False):
        for first, way, state, press_ms, move, release_first in itertools.product(
                ("R1", "L1"), ("up", "down"), STATES, (100, 400), MOVES, ("first", "second")):
            if move == "stick pushed" and ("out" in state or "scroll layer" in state):
                continue                                                  # the stick is out already
            total += 1
            try:
                flags = run(variant, dict(exposed_fires=exposed), first, way, state, press_ms, move, release_first)
            except (NotImplementedError, RuntimeError, ValueError) as error:
                flags = [f"simulator stopped: {type(error).__name__} {error}"]
            for flag in flags:
                seen[flag].append((exposed, first, way, state, press_ms, move, release_first))
    print(f"{variant}: {total} gestures, {sum(len(c) for c in seen.values())} flags")
    for flag, cases in sorted(seen.items(), key=lambda item: -len(item[1])):
        print(f"\n  {len(cases):4d}  {flag}")
        for index, name in enumerate(COLUMNS):
            count = Counter(case[index] for case in cases)
            print(f"        {name}: " + ", ".join(f"{k} x{v}" for k, v in count.items()))


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "default"
    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as handle:
            DATA[variant] = json.load(handle)
    main(variant)
