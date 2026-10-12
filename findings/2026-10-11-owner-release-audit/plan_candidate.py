"""The revised two-driver plan as one trial layout, to check it as a whole. Not a release builder.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/plan_candidate.py <scratch dir>

Writes `<variant>.json` into the scratch directory (never into `neptune/`), from the 90.56 working layouts:

    part 1      the first driver's hand-over in the two Steering Modifier 2 layers (the plan's prototype.py)
    part 2      not built: the stick windows stay as they are in 90.56 (the author, 2026-10-12: "just dont touch
                the window for now and have it remove itself as today"). `plan_candidate.py <scratch dir> window`
                builds the earlier version instead, where the other driver's chord removes the window and a
                driver's Release in a window removes only its own layer
    part 3      the second driver's Release removes the Modifier 2 layer; no 200 ms timer, no reset, no add of
                the cover (cover_timer.py, "no cover")
    by hand     the removes the fix pipeline does not read: the cover out of part 1's Release, out of the W and S
                layers' Modifier 2 entry and out of `Steering`'s exit
    part 6      removes that can never take a layer off, because the layer named binds the same input and so
                answers it itself whenever it is on: the two stick windows out of the W and S layers' Modifier 2
                entry and four Releases, and the Modifier 2 layer out of those four Releases
    part 6      `Steering` and `Steering | LS: Entry Guard` out of the four bumper Releases of the two Gyro
                Modifier 2 layers (the author, 2026-10-12: "ok"). `Steering` binds both bumpers and sits above
                `Gyro`, so neither is on the stack when one of those Releases fires

Then run the fix pipeline and the build audit on the files:

    python3 -m steam_layout.fixes <scratch dir>/default.json <scratch dir>/alternative.json
    python3 -m tools.audit_build <scratch dir>/default.json --baseline versions/neptune/90.56/single-set-default_hold-gyro_90.56.json

and `plan_candidate.py <scratch dir> check` counts the removes against 90.56, runs the plan's 640-gesture sweep
and replays the audit's gestures on whatever the files then hold. `plan_candidate.py <scratch dir> tests` runs
every scenario test on them and lists the ones that fail: the tests that state what the
plan changes. About ten minutes.
"""
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from steam_layout.model import TARGET, Layout, actions, entries, map_title
import scenario
from scenario import Pad
import first_driver as base
import cover_timer as cover

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "findings/2026-10-11-two-drivers-in-steering"
WINDOWS = ("Steering | LS Up: Double Tap", "Steering | LS Down: Double Tap")
COVERS = ("L1: Tap Cover", "R1: Tap Cover")
GYRO_MOD2 = ("Gyro | L1!R1: Modifier 2", "Gyro | R1!L1: Modifier 2")


def drop(layout, title, control, kinds, targets):
    """Take the removes of `targets` out of the entries of these kinds on one input. Returns how many went."""
    source, inp = control
    gone = 0
    found = layout.active(title)[source]["inputs"][inp]["activators"]
    for kind, entry in entries(found):
        if kind not in kinds:
            continue
        kept = [a for a in actions(entry) if not ((m := TARGET.search(a)) and m.group(1) == "remove_layer"
                                                  and layout.resolve(m.group(2)) in targets)]
        gone += len(actions(entry)) - len(kept)
        if len(kept) != len(actions(entry)):
            entry["bindings"]["binding"] = kept if len(kept) != 1 else kept[0]
    return gone


def build(variant, window=False):
    spec = importlib.util.spec_from_file_location("two_driver_prototype", PLAN / "prototype.py")
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    working = scenario.layout_data(variant)
    text, _ = prototype.build(variant, ["handover", "window-leave"] if window else ["handover"])    # part 1
    scenario._layouts[variant] = json.loads(text)
    data = cover.build(variant, "no cover")                                           # part 3
    scenario._layouts[variant] = working
    layout = Layout(data)
    name = (lambda title: map_title(title, base.RENAME)) if variant == "alternative" else (lambda title: title)
    button = lambda driver: scenario.BUTTONS[scenario.ROLES[variant][driver]]
    report = Counter()
    for host, (first, second, cover_title, driver, _) in base.MOD2.items():
        covers, windows = {name(c) for c in COVERS}, {name(w) for w in WINDOWS}
        report["by hand"] += drop(layout, name(host), button(first), ("release",), covers)
        report["by hand"] += drop(layout, name(driver), button(second), ("chord",), covers)
        report["part 6"] += drop(layout, name(driver), button(second), ("chord",), windows)
        for which in (first, second):
            report["part 6"] += drop(layout, name(driver), button(which), ("release",), windows | {name(host)})
            report["by hand"] += drop(layout, name(driver), button(which), ("release",), covers)
    for direction in ("dpad_north", "dpad_south"):
        report["by hand"] += drop(layout, "Steering", ("joystick", direction), ("Soft_Press", "Full_Press", "chord"),
                                  {name(c) for c in COVERS})
    for title in GYRO_MOD2:                             # the Gyro Modifier 2 Releases stop naming Steering
        for driver in ("L1", "R1"):
            report["part 6, Gyro"] += drop(layout, name(title), button(driver), ("release",),
                                           {"Steering", "Steering | LS: Entry Guard"})
    for title in WINDOWS if window else ():             # a driver's Release in a window: the window and its own layer
        for host, (first, second, _, driver, _) in base.MOD2.items():
            report["the windows' Releases"] += drop(layout, name(title), button(second), ("release",), {name(driver)})
    return data, report


def removes(data):
    layout = Layout(data)
    total, steering = 0, 0
    for title in layout.presets:
        for group in layout.active(title).values():
            for value in group.get("inputs", {}).values():
                for _, entry in entries(value.get("activators") or {}):
                    count = sum(1 for op, _ in layout.layer_ops(entry) if op == "remove_layer")
                    total += count
                    steering += count if title.startswith("Steering") else 0
    return total, steering


def check(out):
    for variant in scenario.VARIANTS:
        data = json.loads((out / f"{variant}.json").read_text(encoding="utf-8"))
        before, after = removes(scenario.layout_data(variant)), removes(data)
        print(f"\n{variant}: removes in the layout {before[0]} -> {after[0]}; in the Steering layers {before[1]} -> {after[1]}")
        shown = subprocess.run([sys.executable, str(PLAN / "matrix.py"), variant, str(out / f"{variant}.json")],
                               capture_output=True, text=True, cwd=ROOT).stdout
        total = re.search(r"(\d+) gestures, (\d+) flags", shown)
        print(f"  the plan's sweep: {total.group(2)} flags in {total.group(1)} gestures"
              + "".join(f"\n      {count}  {what}" for count, what in re.findall(r"^ +(\d+)  (.+)$", shown, flags=re.M)))
        layout = Layout(data)
        name = (lambda title: map_title(title, base.RENAME)) if variant == "alternative" else (lambda title: title)
        for host, (first, second, _, driver, _) in base.MOD2.items():
            for title, control in ((host, second), (host, first), (driver, first), (driver, second)):
                source, inp = scenario.BUTTONS[scenario.ROLES[variant][control]]
                found = layout.active(name(title))[source]["inputs"][inp]["activators"]
                shown = "; ".join(f"{kind}: " + ", ".join(("+" if op == "add_layer" else "-") + map_title(t, {"L2": "L1", "R2": "R1"})
                                                          for op, t in layout.layer_ops(entry)) or f"{kind}: a key"
                                  for kind, entry in entries(found))
                if variant == "default":
                    print(f"  {title} | {control}: {shown}")
        for label, gesture in cover.GESTURES:
            seen = Counter()
            for exposed in (True, False):
                for host, (first, second, _, _, key) in base.MOD2.items():
                    pad = base.steering(Pad(variant, data=data, exposed_fires=exposed))
                    seen[gesture(pad, first, second, key).replace(first, "first").replace(second, "second")
                         .replace("W Key", "drive key").replace("S Key", "drive key").replace(f"'{key}'", "'drive key'")
                         .replace(f"{key} ", "the drive key ").replace("L2", "L1").replace("R2", "R1")] += 1
            for result, count in seen.most_common():
                print(f"  {label[:40]:40s} {count} of 4: {result}")


def scenario_tests(out):
    import unittest
    from tests import scenario as registered                 # the scenario tests import it under this name
    for variant in registered.VARIANTS:
        registered._layouts[variant] = json.loads((out / f"{variant}.json").read_text(encoding="utf-8"))
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in registered.modules())
    result = unittest.TestResult()
    suite.run(result)
    print(f"{result.testsRun} scenario tests on the trial layout: {len(result.failures)} fail, {len(result.errors)} error, "
          f"{len(result.expectedFailures)} expected failures, {len(result.unexpectedSuccesses)} unexpected successes")
    for kind in ("failures", "errors", "unexpectedSuccesses"):
        for item in getattr(result, kind):
            test, shown = (item[0], item[1].strip().splitlines()[-1][:200]) if isinstance(item, tuple) else (item, "")
            print(f"  {kind[:-1]}: {test.id().split('.', 1)[1]}\n      {shown}")


def main():
    out = Path(sys.argv[1])
    assert out.resolve() != (ROOT / "neptune").resolve(), "write somewhere else"
    out.mkdir(parents=True, exist_ok=True)
    if "check" in sys.argv:
        return check(out)
    if "tests" in sys.argv:
        return scenario_tests(out)
    for variant in scenario.VARIANTS:
        data, report = build(variant, window="window" in sys.argv)
        (out / f"{variant}.json").write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
        print(variant, dict(report))


if __name__ == "__main__":
    main()
