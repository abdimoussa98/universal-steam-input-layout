"""Does the trial layout only take removes out? Every difference from the working layout, counted.

    python3 findings/2026-10-12-remove-list-audit/reductive.py <scratch dir> [<piped dir>]

`<scratch dir>` holds the trial layouts of trial.py. The two files are compared as JSON, key by key. A
difference inside a bind's command list is counted by command: taken out, added, or left in another order.
Anything else that differs (a setting, a key, a layer) is counted as "other". With `<piped dir>`, the trial
layouts after the fix pipeline, the same comparison is made between the trial and that.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = ("default", "alternative")


def commands(value):
    return value if isinstance(value, list) else [value]


def kind(command):
    return next((op for op in ("remove_layer", "add_layer", "hold_layer") if op in command), "other")


def differences(a, b, path, lists, other):
    if a == b:
        return
    if path and path[-1] == "binding":
        lists.append((commands(a), commands(b)))
    elif isinstance(a, dict) and isinstance(b, dict):
        for key in a.keys() | b.keys():
            if key in a and key in b:
                differences(a[key], b[key], path + (key,), lists, other)
            else:
                other.append(path + (key,))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for index, (x, y) in enumerate(zip(a, b)):
            differences(x, y, path + (index,), lists, other)
    else:
        other.append(path)


def compare(before, after):
    lists, other = [], []
    differences(before, after, (), lists, other)
    gone, added, reordered = Counter(), Counter(), 0
    for old, new in lists:
        gone.update(kind(c) for c in (Counter(old) - Counter(new)).elements())
        added.update(kind(c) for c in (Counter(new) - Counter(old)).elements())
        rest = iter(old)
        reordered += not all(any(x == y for y in rest) for x in new)    # what stays keeps its order
    return len(lists), dict(gone), dict(added), reordered, len(other)


def main():
    out = Path(sys.argv[1])
    piped = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    for variant in VARIANTS:
        working = json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text(encoding="utf-8"))
        trial = json.loads((out / f"{variant}.json").read_text(encoding="utf-8"))
        pairs = [(f"{working['controller_mappings']['title']} -> trial", working, trial)]
        if piped:
            pairs.append(("trial -> trial after the fix pipeline", trial,
                          json.loads((piped / f"{variant}.json").read_text(encoding="utf-8"))))
        for label, before, after in pairs:
            binds, gone, added, reordered, other = compare(before, after)
            print(f"{variant}, {label}: {binds} binds differ; commands taken out {gone or 'none'}; "
                  f"commands added {added or 'none'}; binds whose remaining commands changed order {reordered}; "
                  f"any other difference {other}")


if __name__ == "__main__":
    main()
