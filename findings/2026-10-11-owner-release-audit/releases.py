"""Every Release that removes layers, by size, and the ones with a whole-layout list.

    PYTHONPATH=. python3 findings/2026-10-11-owner-release-audit/releases.py

Read-only, on both working layouts. For each Release Press that removes at least one layer:
the input it is on, how many layers it removes, whether the Cleanup audit reads it as a
deliberate clear (it removes every layer that isn't stateful, so R132 leaves its list
alone), and how many of its layers the backward chains say can never be on the stack with
its host. The chains don't follow chords or delayed adds; walks.py asks the simulator.
"""
import json
from collections import Counter
from pathlib import Path

from steam_layout.cleanups import Cleanups, name
from steam_layout.model import Layout

ROOT = Path(__file__).resolve().parents[2]
STICKS, PADS = ("joystick", "right_joystick"), ("left_trackpad", "right_trackpad")


def where(control):
    source, inp = control
    if source in STICKS:
        return "stick touch" if inp == "touch" else "stick click" if inp == "click" else "stick"
    return "pad" if source in PADS else "button"


def rows(layout, cleanups):
    for host in layout.presets:
        if host == layout.base:
            continue
        present = cleanups.present(host) if cleanups.reached(host) else {host}
        for t in cleanups.inv.by_layer(host):
            removed = list(dict.fromkeys(x for op, x in t.ops if op == "remove_layer"))
            if t.role != "release" or not removed:
                continue
            yield {"host": host, "input": name(t.control), "where": where(t.control), "removes": len(removed),
                   "own": host in removed, "clear": cleanups.is_clear(removed),
                   "never": sum(1 for x in removed if x not in present),
                   "adds": [x for op, x in t.ops if op == "add_layer"]}


def main():
    for variant in ("default", "alternative"):
        data = json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text(encoding="utf-8"))
        layout = Layout(data)
        found = list(rows(layout, Cleanups(layout)))
        total = sum(r["removes"] for r in found)
        print(f"\n{variant}: {len(layout.presets) - 1} layers; {len(found)} Releases remove layers, {total} removes in all")
        for place, count in Counter(r["where"] for r in found).most_common():
            removes = sum(r["removes"] for r in found if r["where"] == place)
            print(f"  on a {place}: {count} Releases, {removes} removes")
        clears = [r for r in found if r["clear"]]
        print(f"\n  Whole-layout lists (read as deliberate clears): {len(clears)} Releases, "
              f"{sum(r['removes'] for r in clears)} removes")
        for r in clears:
            then = f"then adds {', '.join(r['adds'])}" if r["adds"] else "adds nothing"
            print(f"    {r['host']} | {r['input']}: removes {r['removes']}, {r['never']} never there by the chains; {then}")
        buttons = [r for r in found if r["where"] == "button"]
        print(f"\n  Button Releases by size ({len(buttons)}, {sum(r['removes'] for r in buttons)} removes):")
        for size, count in sorted(Counter(r["removes"] for r in buttons).items(), reverse=True):
            hosts = sorted({f"{r['host']} ({r['input']})" for r in buttons if r["removes"] == size})
            shown = "; ".join(hosts) if len(hosts) <= 4 else f"{len(hosts)} Releases"
            print(f"    {size:3d} removes x {count}: {shown}")


if __name__ == "__main__":
    main()
