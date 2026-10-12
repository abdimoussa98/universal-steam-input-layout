"""The walks and the chains side by side, for the modifier button Releases of the Steering layers.

    PYTHONPATH=. python3 findings/2026-10-11-owner-release-audit/summary.py

Reads walks-4.txt, walks-20.txt and walks-short.txt (walks.py), adds both layouts together under
the default layout's names, and compares the two whole-layout lists with the chains' "can be on
the stack". Writes lists-L1.json and lists-R1.json: each list split into the layers either
measure found on the stack and the layers neither did.
"""
import json
import re
from pathlib import Path

from steam_layout.cleanups import Cleanups
from steam_layout.model import Layout, map_title

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BACK = {"L2": "L1", "R2": "R1"}
BUTTON = {"left_bumper": "L1", "right_bumper": "R1", "left_trigger/edge": "L1", "right_trigger/edge": "R1"}
QUICK = {"Steering | L1!R1: Modifier 2": "R1", "Steering | R1!L1: Modifier 2": "L1"}


def read(path, rows):
    variant = key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if found := re.match(r"(default|alternative): ", line):
            variant = found.group(1)
        elif found := re.match(r"  (.+) \| (\S+): fired (\d+) times", line):
            name = (lambda title: map_title(title, BACK)) if variant == "alternative" else (lambda title: title)
            key = (name(found.group(1)), BUTTON[found.group(2)])
            row = rows.setdefault(key, {"fired": 0, "on": set()})
            row["fired"] += int(found.group(3))
        elif found := re.match(r"    lists (\d+);", line):
            rows[key]["lists"] = int(found.group(1))
        elif found := re.match(r"    on the stack: (.*)", line):
            rows[key]["on"] |= {name(title) for title in found.group(1).split(", ") if title != "none"}


def main():
    rows = {}
    for path in sorted(HERE.glob("walks-*.txt")):
        read(path, rows)
    print("Modifier button Releases, both layouts, all walks:")
    for (layer, button), row in sorted(rows.items()):
        print(f"  {layer} | {button}: lists {row['lists']}, fired {row['fired']}, on the stack at least once {len(row['on'])}")
    layout = Layout(json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text(encoding="utf-8")))
    cleanups = Cleanups(layout)
    for host, button in QUICK.items():
        listed = [x for t in cleanups.inv.by_layer(host) if t.role == "release" and t.source == "switch"
                  for op, x in t.ops if op == "remove_layer"]
        chains, walked = set(listed) & cleanups.present(host), rows[(host, button)]["on"] & set(listed)
        either = [x for x in listed if x in chains | walked]
        print(f"\n{host} | {button}: lists {len(listed)}; on the stack by the chains {len(chains)}, in the walks {len(walked)}, "
              f"by either {len(either)}, by neither {len(listed) - len(either)}")
        print(f"  chains only: {', '.join(sorted(chains - walked))}")
        print(f"  walks only: {', '.join(sorted(walked - chains))}")
        for title in either:
            kind, keep = cleanups.keeper(title)
            print(f"    {title}: kept on by {kind}{' ' + '+'.join(sorted(keep)) if keep else ''}")
        (HERE / f"lists-{button}.json").write_text(json.dumps(
            {"either": either, "neither": [x for x in listed if x not in either]}, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
