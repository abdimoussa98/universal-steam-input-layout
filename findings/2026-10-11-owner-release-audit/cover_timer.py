"""The 200 ms timer of the Steering Modifier 2 layers: what is left for it to do once the quick tap is short?

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/cover_timer.py             # the gestures
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/cover_timer.py walks 750   # and the same walks
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/cover_timer.py trial       # and the scenario tests

In memory only. Two versions of the two Steering Modifier 2 layers:

    leave it    the quick tap removes the Modifier 2 layer and its cover (decisions 1 and 2 of the audit);
                the 200 ms timer, its reset and every add of the cover are as in 90.56
    no cover    the cover is never added: no 200 ms timer, no reset, no add of the cover in the twelve
                command binds or the two stick touch Releases; the second driver's Release removes the
                Modifier 2 layer

Part one replays gestures on both. Part two plays the same random walks on both (walks.py) and compares,
walk by walk, everything typed and the stack left when all is let go. Part three runs every scenario test
on each and lists the tests that tell the two apart.
"""
import random
import sys
import unittest
from collections import Counter
from multiprocessing import Pool

from steam_layout.model import TARGET, Layout, actions, entries, map_title
from steam_layout.simulator import Simulator
import scenario
from scenario import Pad
import first_driver as base
import walks as probe

VERSIONS = ("leave it", "no cover")


def build(variant, version):
    data = base.build(variant, "leave it")
    if version == "leave it":
        return data
    layout = Layout(data)
    name = (lambda title: map_title(title, base.RENAME)) if variant == "alternative" else (lambda title: title)
    for host, (first, second, cover, driver, _) in base.MOD2.items():
        button = scenario.BUTTONS[scenario.ROLES[variant][second]]
        for source, group in layout.active(name(host)).items():
            for inp, value in group.get("inputs", {}).items():
                found = value.get("activators") or {}
                if (source, inp) == button:                       # the second driver: only the Release is left
                    release = found["release"]
                    release["bindings"]["binding"] = [a for a in actions(release) if layout.resolve(TARGET.search(a).group(2)) == name(host)]
                    value["activators"] = {"release": release}
                    continue
                for _, entry in entries(found):                   # everywhere else: no add of the cover
                    kept = [a for a in actions(entry) if not ((m := TARGET.search(a)) and m.group(1) == "add_layer"
                                                              and layout.resolve(m.group(2)) == name(cover))]
                    if len(kept) != len(actions(entry)):
                        entry["bindings"]["binding"] = kept
    return data


# --- part one ---------------------------------------------------------------------------------------

def ends(pad, first, key):
    """What is typed and on the stack now, and after the first driver is let go as well."""
    now = f"{key} {base.key_gap(pad, key)}; on: {', '.join(pad.names()[2:]) or 'nothing'}"
    pad.let_go(first).wait(400)
    return f"{now}; all let go: {', '.join(pad.names()[1:])}; keys {pad.down() or 'none'}"


def quick(pad, first, second, key):
    pad.hold(first).wait(400).mark().hold(second).wait(60).let_go(second).wait(300)
    return ends(pad, first, key)


def held(pad, first, second, key):
    pad.hold(first).wait(400).mark().hold(second).wait(500).let_go(second).wait(300)
    return ends(pad, first, key)


def used(pad, first, second, key):
    pad.hold(first).wait(400).mark().hold(second).wait(60).tap("A").wait(40).let_go(second).wait(300)
    return f"typed {pad.typed()}; " + ends(pad, first, key)


def thumb(pad, first, second, key):
    pad.touch("RS").wait(300).hold(first).wait(400).mark().hold(second).wait(60).lift("RS").wait(40).let_go(second).wait(300)
    return ends(pad, first, key)


def first_goes_first(pad, first, second, key):
    pad.hold(first).wait(400).mark().hold(second).wait(500).let_go(first).wait(300)
    now = f"on: {', '.join(pad.names()[2:]) or 'nothing'}; keys {pad.down() or 'none'}"
    pad.let_go(second).wait(400)
    return f"{now}; all let go: {', '.join(pad.names()[1:])}"


def stick_out(pad, first, second, key):
    pad.hold(first).wait(100).hold(second).wait(400).push("LS", "up").wait(100).mark().let_go(second).wait(300)
    return f"Steering {'stays' if pad.has('Steering') else 'ENDS'}; {key} {base.key_gap(pad, key)}"


def missed_second(pad, first, second, key):
    """Both held, the second let go unseen in the Steam menu, then a face button."""
    pad.hold(first).wait(100).hold(second).wait(500).miss(second).wait(500)
    stale = pad.names()[2:]
    pad.tap(second).wait(400)
    return f"stale: {', '.join(stale)}; after a tap of {second}: {', '.join(pad.names()[2:])}; keys {pad.down() or 'none'}"


GESTURES = (("1. First driver held, the second tapped for 60 ms", quick),
            ("2. First driver held, the second held 500 ms and let go", held),
            ("3. First driver held, the second down, A tapped, the second let go", used),
            ("4. A thumb lifted off the right stick while both are held, then the second let go", thumb),
            ("5. Both held 500 ms, the first let go first", first_goes_first),
            ("6. Both held, stick pushed fully up, the second let go after 500 ms", stick_out),
            ("7. Both held, the second let go unseen, then tapped", missed_second))


def replay():
    for title, gesture in GESTURES:
        print(f"\n{title}")
        for version in VERSIONS:
            seen = Counter()
            for variant in scenario.VARIANTS:
                data = build(variant, version)
                for exposed in (True, False):
                    for host, (first, second, _, _, key) in base.MOD2.items():
                        pad = base.steering(Pad(variant, data=data, exposed_fires=exposed))
                        seen[gesture(pad, first, second, key).replace(first, "first").replace(second, "second")
                             .replace("W Key", "drive key").replace("S Key", "drive key")
                             .replace(f"'{key}'", "'drive key'").replace(f"{key} ", "the drive key ")
                             .replace("L2", "L1").replace("R2", "R1")] += 1
            for result, count in seen.most_common():
                print(f"  {version:9s} {count} of 8: {result}")


# --- part two ---------------------------------------------------------------------------------------

def batch(job):
    variant, version, seed, count, missed = job
    layout, rng, rows = Layout(build(variant, version)), random.Random(seed), []
    for _ in range(count):
        pad = Pad.__new__(Pad)
        pad.variant, pad.options, pad.layout = variant, {}, layout
        pad.sim = Simulator(layout, exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
        pad._mark, pad._began = 0, tuple(pad.sim.stack)
        state = rng.getstate()
        try:
            base.walk_events(pad, rng, missed)
            base.settle(pad)
            bumps = sum(1 for _, what, detail in pad.sim.log if what == "haptic" and "Modifier 2" in detail
                        and detail.startswith("1 ") and "Steering | " in detail and detail.endswith(("bumper", "trigger/edge")))
            rows.append((tuple(pad.sim.typed()), tuple(t for t in pad.sim.stack if t not in base.MODES),
                         "Steering" in pad.sim.stack, bumps))
        except (RuntimeError, NotImplementedError, ValueError):
            rows.append(None)
            rng.setstate(state)
            for _ in range(2000):
                rng.random()
    return variant, version, seed, missed, rows


def walks(count=750, seeds=8):
    jobs = [(variant, version, seed, count, missed) for variant in scenario.VARIANTS for version in VERSIONS
            for seed in range(1, seeds + 1) for missed in (0.0, 0.10)]
    with Pool() as pool:
        done = {key[:4]: key[4] for key in pool.map(batch, jobs)}
    for missed in (0.0, 0.10):
        same = typed = stack = mode = both = bumps = 0
        for variant in scenario.VARIANTS:
            for seed in range(1, seeds + 1):
                for a, b in zip(done[(variant, "leave it", seed, missed)], done[(variant, "no cover", seed, missed)]):
                    if a is None or b is None:
                        continue
                    both += 1
                    bumps += a[3]
                    same += a[:3] == b[:3]
                    typed += a[0] != b[0]
                    stack += a[1] != b[1]
                    mode += a[2] != b[2]
        print(f"\nThe same {count * seeds} walks per layout on both versions (60 events, "
              f"{int(missed * 100)}% of button releases missed):")
        print(f"  finished on both: {both}; the same keys typed, the same layers left and Steering on or off alike: {same}")
        print(f"  different keys typed: {typed}; different layers left at the end: {stack}; "
              f"Steering on in one and off in the other: {mode}")
        print(f"  bumps of the 200 ms timer in the 'leave it' walks: {bumps}")


# --- part three --------------------------------------------------------------------------------------

def trial(version):
    from tests import scenario as registered                  # the scenario tests import it under this name
    if version is not None:
        for variant in registered.VARIANTS:
            registered._layouts[variant] = build(variant, version)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in registered.modules())
    result = unittest.TestResult()
    suite.run(result)
    outcome = {}
    for kind in ("failures", "errors", "expectedFailures", "unexpectedSuccesses"):
        for item in getattr(result, kind):
            outcome[(item[0] if isinstance(item, tuple) else item).id()] = kind
    return version, result.testsRun, outcome


def trials():
    with Pool(3) as pool:
        found = {version: (ran, outcome) for version, ran, outcome in pool.map(trial, [None, *VERSIONS])}
    ran, today = found[None]
    print(f"\n{ran} scenario tests")
    for version in VERSIONS:
        changed = sorted(t for t in set(today) | set(found[version][1]) if today.get(t) != found[version][1].get(t))
        print(f"  {version}: {len(changed)} differ from the layouts as they are")
    leave, without = found["leave it"][1], found["no cover"][1]
    apart = sorted(t for t in set(leave) | set(without) if leave.get(t) != without.get(t))
    print(f"  tests that tell 'leave it' and 'no cover' apart: {len(apart)}")
    for test in apart:
        print(f"    {test.split('.', 1)[1]}: {leave.get(test, 'passes')} -> {without.get(test, 'passes')}")


if __name__ == "__main__":
    replay()
    if "walks" in sys.argv:
        walks(*[int(a) for a in sys.argv[sys.argv.index("walks") + 1:] if a.isdigit()])
    if "trial" in sys.argv:
        trials()
