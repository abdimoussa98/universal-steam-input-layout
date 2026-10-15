"""C4 of the plan: the Deck's scenario tests on Ibex 1.0, and on the Edge conversion stopped after R180 to R182.

    python3 findings/2026-10-15-ibex-base/c4_scenarios.py            # both runs; writes c4-scenarios.txt here

Every `tests/test_scenarios_*.py` scenario that runs on the working layout runs once with Ibex 1.0's layouts in its
place, and once with a partial Edge layout: Ibex 1.0 with only R180 (the Edge's header), R181 (the grips trade
places) and R182 (no stick touch, R178), then R178 (f) and the fix pipeline. Its pads are still the Deck's two, so
the pad scenarios mean what they meant. The scenario helper presses a Deck grip where its bind is on the Edge
(`Pad.control`), so a scenario's L4 for Shift presses the Edge's L5. Frozen scenarios run on their frozen builds
either way and are left out.

Ibex 1.0 differs from Neptune 90.74 only in its header and gyro styles, which the simulator does not read, so every
scenario that passes on the Deck passes there. On the partial Edge a scenario can fail where it needs a stick touch.
The run records which tests pressed a stick touch on the simulator, and the file sorts each failure: it starts on a
stick-touch layer the Edge deletes, it pressed a stick touch, or it pressed nothing and reads the layout (a count or
a shape that includes the stick touches' binds), or none of these, which is the one to look into.
"""
import copy
from dataclasses import replace
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "tests"))

from steam_layout import controllers, convert  # noqa: E402
from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.simulator import Simulator  # noqa: E402
from tests import scenario  # noqa: E402

STICK_TOUCHES = {("joystick", "touch"), ("right_joystick", "touch")}
CURRENT = [None]                       # the test that is running
TOUCHED, PADS = set(), set()           # tests that pressed a stick touch; tests that made a Pad


class Result(unittest.TextTestResult):
    def startTest(self, test):
        CURRENT[0] = test.id()
        super().startTest(test)


def watch():
    """Record which test presses a stick touch, and which makes a Pad at all."""
    press, init = Simulator.press, scenario.Pad.__init__

    def pressed(self, control, *args, **kwargs):
        if control in STICK_TOUCHES:
            TOUCHED.add(CURRENT[0])
        return press(self, control, *args, **kwargs)

    def made(self, *args, **kwargs):
        PADS.add(CURRENT[0])
        return init(self, *args, **kwargs)
    Simulator.press, scenario.Pad.__init__ = pressed, made


def partial_edge(variant):
    """Ibex 1.0 converted by R180, R181 and R182 alone (then R178 f and the fix pipeline)."""
    ibex = json.loads(controllers.IBEX.snapshot(variant, "1.0").read_text(encoding="utf-8"))
    edge = replace(controllers.DSE, absent_sources=frozenset(), whole_pad=False, mute="", always_gyro=False)
    data = convert.readable(copy.deepcopy(ibex))
    report = convert.Report()
    convert.header(data, controllers.DSE, variant, "1.0")
    convert.swap_grips(data, edge)
    convert.drop_absent(data, edge, report)
    convert.delete_unreachable(data, report)
    apply_all(data)
    return json.loads(convert.dumps(data)), report


def run(layouts):
    """Run every scenario test on these layouts ({variant: data}); [(test id, outcome, message)] for each that did
    not pass, and the number run."""
    scenario._layouts.clear()
    for variant, data in layouts.items():
        scenario._layouts[(scenario.CONTROLLER, variant)] = data
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in scenario.modules())
    TOUCHED.clear()
    PADS.clear()
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0, resultclass=Result).run(suite)
    rows = [(test.id(), "fail", text) for test, text in result.failures] + \
           [(test.id(), "error", text) for test, text in result.errors] + \
           [(test.id(), "unexpected success", "") for test in result.unexpectedSuccesses]
    return sorted(rows), result.testsRun


def kind(test_id, text=""):
    """Why a test may fail on a layout without stick touch."""
    if "unknown layer: LST:" in text or "unknown layer: RST:" in text:
        return "starts on a stick-touch layer, which the Edge deletes"
    if test_id in TOUCHED:
        return "pressed a stick touch"
    if test_id not in PADS:
        return "pressed nothing: it reads the layout"
    return "PRESSED NO STICK TOUCH: look into it"


def main():
    watch()
    out = ["C4: the Deck's scenario tests on other controllers' layouts (plans/2026-10-15-controller-dirs-and-"
           "release-pipeline.md, part 4).", ""]
    ibex = {v: json.loads(controllers.IBEX.snapshot(v, "1.0").read_text(encoding="utf-8")) for v in controllers.VARIANTS}
    rows, count = run(ibex)
    out += [f"Ibex 1.0: {count} tests, {len(rows)} not passing"] + [f"  {t} ({o})" for t, o, _ in rows] + [""]
    edge = {v: partial_edge(v)[0] for v in controllers.VARIANTS}
    rows, count = run(edge)
    sorted_rows = sorted(rows, key=lambda row: (kind(row[0], row[2]), row[0]))
    kinds = {k: sum(1 for row in rows if kind(row[0], row[2]) == k)
             for k in dict.fromkeys(kind(row[0], row[2]) for row in sorted_rows)}
    out.append(f"Edge after R180 to R182: {count} tests, {len(rows)} not passing: "
               + ", ".join(f"{n} {k}" for k, n in kinds.items()))
    for test_id, outcome, text in sorted_rows:
        last = [line for line in text.strip().splitlines() if line.strip()][-1:] if text else []
        out.append(f"  {test_id} ({outcome}): {kind(test_id, text)}")
        out += [f"      {line[:200]}" for line in last]
    (HERE / "c4-scenarios.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:4]), f"... see {HERE.name}/c4-scenarios.txt")


if __name__ == "__main__":
    main()
