"""Do the audit's decisions and the two-driver plan fit together? The plan's own sweep, on each and on both.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/with_two_driver_plan.py <scratch dir>

Writes trial layouts into the scratch directory (never into `neptune/`) and runs
`findings/2026-10-11-two-drivers-in-steering/matrix.py` on each: 640 two-driver gestures per layout, with a
flag for each thing that goes wrong (`Steering` gone while a driver is held, a stray drive key, no
Modifier 2). Then it holds the second driver for 500 ms and lists what happens to the first driver's key.

    audit only   decisions 1, 2 and 4: the second driver's Release removes the Modifier 2 layer, and the
                 200 ms timer and its cover are gone (cover_timer.py, "no cover")
    plan only    the plan's parts 1 and 2 on 90.56 (its prototype.py: handover, window)
    both         the plan's parts 1 and 2, then the audit's decisions
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import scenario
from scenario import Pad
import first_driver as base
import cover_timer as cover

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "findings/2026-10-11-two-drivers-in-steering"
VERSIONS = ("audit only", "plan only", "both")


def build(out):
    spec = importlib.util.spec_from_file_location("two_driver_prototype", PLAN / "prototype.py")
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    for variant in scenario.VARIANTS:
        working = scenario.layout_data(variant)
        text, _ = prototype.build(variant, ["handover", "window"])
        found = {"audit only": cover.build(variant, "no cover"), "plan only": json.loads(text)}
        scenario._layouts[variant] = found["plan only"]             # cover.build reads the layout from here
        found["both"] = cover.build(variant, "no cover")
        scenario._layouts[variant] = working
        for version, data in found.items():
            (out / f"{variant}-{version.replace(' ', '-')}.json").write_text(json.dumps(data), encoding="utf-8")


def main():
    out = Path(sys.argv[1])
    assert out.resolve() != (ROOT / "neptune").resolve(), "write somewhere else"
    out.mkdir(parents=True, exist_ok=True)
    build(out)
    for version in VERSIONS:
        print(f"\n{version}")
        for variant in scenario.VARIANTS:
            path = out / f"{variant}-{version.replace(' ', '-')}.json"
            shown = subprocess.run([sys.executable, str(PLAN / "matrix.py"), variant, str(path)], capture_output=True,
                                   text=True, cwd=ROOT).stdout
            flags = re.findall(r"^ +(\d+)  (.+)$", shown, flags=re.M)
            total = re.search(r"(\d+) gestures, (\d+) flags", shown)
            print(f"  {variant}: {total.group(2)} flags in {total.group(1)} gestures"
                  + "".join(f"\n      {count}  {what}" for count, what in flags))
        pad = base.steering(Pad("default", data=json.loads((out / f"default-{version.replace(' ', '-')}.json").read_text())))
        pad.hold("R1").wait(400).mark().hold("L1").wait(500).let_go("L1").wait(300)
        start = pad.sim.log[pad._mark][0]
        events = [f"{what} at {ms - start} ms" for ms, what, detail in pad.sim.log[pad._mark:]
                  if detail == "W" and what in ("up", "handover", "down")]
        print(f"  W through R1 held and L1 held for 500 ms: {', '.join(events) or 'never touched'}")


if __name__ == "__main__":
    main()
