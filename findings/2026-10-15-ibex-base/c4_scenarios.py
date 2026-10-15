"""C4 of the plan: the Deck's scenario tests on Ibex 1.0, and on the Edge conversion stopped after R180 to R182.

    python3 findings/2026-10-15-ibex-base/c4_scenarios.py            # both runs; writes c4-scenarios.txt here

Every `tests/test_scenarios_*.py` scenario that runs on the working layout runs once with Ibex 1.0's layouts in its
place, and once with a partial Edge layout: Ibex 1.0 with only R180 (the Edge's header), R181 (the grips trade
places) and R182 (no stick touch, R178), then R178 (f) and the fix pipeline. Its pads are still the Deck's two, so
the pad scenarios mean what they meant. The scenario helper presses a Deck grip where its bind is on the Edge
(`Pad.control`), so a scenario's L4 for Shift presses the Edge's L5. Frozen scenarios run on their frozen builds
either way and are left out.

Ibex 1.0 differs from Neptune 90.74 only in its header and gyro styles, which the simulator does not read, so every
scenario that passes on the Deck passes there. On the partial Edge, a scenario fails when it needs a stick touch;
the file lists each failure with the stick-touch layers its test names, for review.
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
from tests import scenario  # noqa: E402

TOUCH_LAYERS = ("LST:", "RST:", "Temporary Gyro", '"LS touch"', "touch(\"LS\")", "touch(\"RS\")", "lift(\"LS\")",
                "lift(\"RS\")")


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
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    rows = [(test.id(), "fail", text) for test, text in result.failures] + \
           [(test.id(), "error", text) for test, text in result.errors] + \
           [(test.id(), "unexpected success", "") for test in result.unexpectedSuccesses]
    return sorted(rows), result.testsRun


def needs_stick_touch(test_id):
    """The stick-touch names in the test's own source: what makes it a stick-touch scenario."""
    module, cls, name = test_id.rsplit(".", 2)
    source = Path(sys.modules[module].__file__).read_text(encoding="utf-8")
    start = source.find(f"def {name}(")
    end = source.find("\n    def ", start + 1)
    body = source[start:end if end > 0 else None]
    return sorted({word for word in TOUCH_LAYERS if word in body})


def main():
    out = ["C4: the Deck's scenario tests on other controllers' layouts (plans/2026-10-15-controller-dirs-and-"
           "release-pipeline.md, part 4).", ""]
    ibex = {v: json.loads(controllers.IBEX.snapshot(v, "1.0").read_text(encoding="utf-8")) for v in controllers.VARIANTS}
    rows, count = run(ibex)
    out += [f"Ibex 1.0: {count} tests, {len(rows)} not passing"] + [f"  {t} ({o})" for t, o, _ in rows] + [""]
    edge = {v: partial_edge(v)[0] for v in controllers.VARIANTS}
    rows, count = run(edge)
    out.append(f"Edge after R180 to R182: {count} tests, {len(rows)} not passing")
    for test_id, outcome, text in rows:
        names = needs_stick_touch(test_id)
        last = [line for line in text.strip().splitlines() if line.strip()][-1:] if text else []
        out.append(f"  {test_id} ({outcome}): " + (f"names {', '.join(names)}" if names else "NO STICK TOUCH NAMED"))
        out += [f"      {line[:200]}" for line in last]
    (HERE / "c4-scenarios.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:4]), f"... see {HERE.name}/c4-scenarios.txt")


if __name__ == "__main__":
    main()
