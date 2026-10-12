"""Every short bumper sequence, on 90.57 and on the trial layout: is anything different?

    PYTHONPATH=.:tests:findings/2026-10-12-remove-list-audit python3 findings/2026-10-12-remove-list-audit/rocking.py <scratch dir> [length] [missed length]

`<scratch dir>` holds the trial layouts of trial.py. Not random: every sequence of a given length is played.

    rocking     each step is one of: L1 down or up, R1 down or up, a tap of A; then a gap of 20, 120 or 210 ms
                (inside one timer, inside a Double Tap window, past the 200 ms hold). From Base and from `Gyro`,
                with a bind exposed under a held button firing at once and at its next repeat (A9).
    missed      the same with a release that can also be missed (the Steam menu, A25) and a thumb going on or
                off the right stick, which is what a cleanup function needs to run. Gaps of 30 and 250 ms.

Both layouts play each sequence, and the whole log is compared: every key, wheel step, haptic and beep, and
every layer going on or off, with its time. The rocking tests (tests/test_modifier_rocking.py) are run on
the trial layout as well.
"""
import hashlib
import itertools
import json
import sys
import unittest
from multiprocessing import Pool
from pathlib import Path

from steam_layout.model import Layout
import scenario
from scenario import Pad

ROOT = Path(__file__).resolve().parents[2]
ROCK = ("L1", "R1", "A")
ROCK_GAPS = (20, 120, 210)
MISS = ("L1", "R1", "L1 missed", "R1 missed", "A", "RS")
MISS_GAPS = (30, 250)
DATA = {}


def play(variant, layout, start, exposed, steps):
    pad = Pad.__new__(Pad)
    pad.variant, pad.options, pad.layout = variant, {}, layout
    pad.sim = scenario.Simulator(layout, start=tuple(pad.title(t) for t in start), exposed_fires=exposed)
    pad._mark, pad._began = 0, tuple(pad.sim.stack)
    for action, gap in steps:
        name = action.split()[0]
        if name == "A":
            pad.tap("A")
        elif name == "RS":
            pad.lift("RS") if pad._held("RS", "touch") else pad.touch("RS")
        elif pad.control(name) in pad.sim.held:
            pad.miss(name) if action.endswith("missed") else pad.let_go(name)
        elif action.endswith("missed"):
            return None                                          # nothing to miss: the plain press covers it
        else:
            pad.hold(name)
        pad.wait(gap)
    for name in ("L1", "R1"):                                    # let go of what is left, and settle
        if pad.control(name) in pad.sim.held:
            pad.let_go(name)
    pad.lift("RS").wait(600)
    text = repr(pad.sim.log) + repr(pad.sim.stack)
    return hashlib.sha1(text.encode()).hexdigest(), any("Scroll" in str(d) or "mouse_wheel" in str(d) for _, w, d in pad.sim.log)


def init(data):
    DATA.update(data)


def batch(job):
    variant, kind, first, length = job
    actions, gaps = (ROCK, ROCK_GAPS) if kind == "rocking" else (MISS, MISS_GAPS)
    layouts = {label: Layout(json.loads(Path(path).read_text(encoding="utf-8"))) for label, path in DATA[variant].items()}
    played = same = different = scrolled = 0
    examples = []
    rest = list(itertools.product(itertools.product(actions, gaps), repeat=length - 1))
    for start in (("Base",), ("Base", "Gyro")):
        for exposed in (True, False):
            for tail in rest:
                steps = (first, *tail)
                try:
                    a = play(variant, layouts["90.57"], start, exposed, steps)
                    b = play(variant, layouts["trial"], start, exposed, steps)
                except (RuntimeError, NotImplementedError, ValueError):
                    continue
                if a is None or b is None:
                    continue
                played += 1
                scrolled += a[1]
                if a[0] == b[0]:
                    same += 1
                else:
                    different += 1
                    if len(examples) < 3:
                        examples.append((start, exposed, steps))
    return variant, kind, played, same, different, scrolled, examples


def rocking_tests(out):
    import tests.test_modifier_rocking as module
    def trial_layouts(cls):
        cls.layouts = {v: Layout(json.loads((out / f"{v}.json").read_text(encoding="utf-8"))) for v in module.VARIANTS}
    module.RockingTests.setUpClass = classmethod(trial_layouts)
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
    return result.testsRun, len(result.failures) + len(result.errors)


def main():
    out = Path(sys.argv[1])
    length = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    missed = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    for variant in scenario.VARIANTS:
        DATA[variant] = {"90.57": str(ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"),
                         "trial": str(out / f"{variant}.json")}
    ran, failed = rocking_tests(out)
    print(f"tests/test_modifier_rocking.py on the trial layouts: {ran} tests, {failed} fail")
    jobs = [(variant, kind, first, n) for variant in scenario.VARIANTS
            for kind, actions, gaps, n in (("rocking", ROCK, ROCK_GAPS, length), ("missed", MISS, MISS_GAPS, missed))
            for first in itertools.product(actions, gaps) if not first[0].endswith("missed")]
    with Pool(initializer=init, initargs=(DATA,)) as pool:
        found = pool.map(batch, jobs, chunksize=1)
    for variant in scenario.VARIANTS:
        for kind, n in (("rocking", length), ("missed", missed)):
            rows = [r for r in found if r[0] == variant and r[1] == kind]
            played, same, different, scrolled = (sum(r[i] for r in rows) for i in (2, 3, 4, 5))
            print(f"{variant}, {kind}, every sequence of {n} steps: {played} played; the whole log is the same in {same}, "
                  f"differs in {different}; {scrolled} of them scroll")
            for r in rows:
                for example in r[6][:1]:
                    print("    differs:", example)


if __name__ == "__main__":
    main()
