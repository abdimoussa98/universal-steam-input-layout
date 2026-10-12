"""A trial layout without the removes the audit found unnecessary, and the proof that nothing changes.

    PYTHONPATH=.:tests:findings/2026-10-12-remove-list-audit python3 findings/2026-10-12-remove-list-audit/trial.py <scratch dir> [walks per seed] [seeds]

Not a builder: it writes `<variant>.json` into the scratch directory, never into `neptune/`.

From `removes-<variant>.json` (audit.py) it takes out every remove whose verdict is "never there" or "answers
first", except the ones a rule fixes whatever the stack holds: a timer's reset (R120), the layer's own hold
target in one of its Releases (R120 to R122) and a stick touch Release's three helpers (R123). Then the working layout and the trial play the same random walks (walk.py),
and each walk's whole log is compared: every key, wheel step, haptic and beep, and every layer going on or
off, with its time. A remove that never takes a layer off and resets no timer leaves the log as it was.
"""
import copy
import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

from steam_layout.model import TARGET, Layout, actions, entries
import scenario
import walk

HERE = Path(__file__).resolve().parent
FIXED = ("a timer's reset (R120)", "a stick touch Release's helper (R123)",
         "the layer's own hold target, in a Release (R120 to R122)")
MISSED = (0.0, 0.10)


def trimmed(variant):
    data = copy.deepcopy(scenario.layout_data(variant))
    layout = Layout(data)
    rows = json.loads((HERE / f"removes-{variant}.json").read_text(encoding="utf-8"))
    gone = {}
    for row in rows:
        if row["verdict"] in ("never there", "answers first") and row["rule"] not in FIXED:
            gone.setdefault((row["layer"], row["input"], row["kind"], row["index"]), set()).add(row["target"])
    taken = Counter()
    for (title, control, kind, index), targets in gone.items():
        source, name = control.split("/")
        found = list(entries(layout.active(title)[source]["inputs"][name]["activators"]))
        found_kind, entry = found[index]
        assert found_kind == kind, (title, control, kind, index)
        kept = [a for a in actions(entry) if not ((m := TARGET.search(a)) and m.group(1) == "remove_layer"
                                                  and layout.resolve(m.group(2)) in targets)]
        assert kept and len(actions(entry)) - len(kept) == len(targets), (title, control, kind, len(kept))
        entry["bindings"]["binding"] = kept[0] if len(kept) == 1 else kept
        taken[next(r["rule"] for r in rows if r["layer"] == title and r["target"] in targets
                   and (r["input"], r["kind"], r["index"]) == (control, kind, index))] += len(targets)
    return data, sum(len(t) for t in gone.values()), len(gone), taken


def removes(data):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in (group.get("inputs") or {}).values() for _, entry in entries(value.get("activators") or {})
               for op, _ in layout.layer_ops(entry) if op == "remove_layer")


def main():
    out = Path(sys.argv[1])
    assert out.resolve() != (HERE.parents[1] / "neptune").resolve(), "write somewhere else"
    out.mkdir(parents=True, exist_ok=True)
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    for variant in scenario.VARIANTS:
        working = scenario.layout_data(variant)
        data, number, binds, taken = trimmed(variant)
        (out / f"{variant}.json").write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
        print(f"\n{variant}: {number} removes taken out of {binds} binds; removes in the layout {removes(working)} -> {removes(data)}")
        rules = Counter(row["rule"] for row in json.loads((HERE / f"removes-{variant}.json").read_text(encoding="utf-8"))
                        if row["verdict"] in ("never there", "answers first") and row["rule"] not in FIXED)
        for rule, n in rules.most_common():
            print(f"    {n:5d}  {rule}")
        jobs = [(variant, label, layout, seed, count, missed) for label, layout in (("working", working), ("trial", data))
                for missed in MISSED for seed in range(1, seeds + 1)]
        with Pool() as pool:
            found = pool.map(walk.batch, jobs)
        runs = {}
        for _, label, missed, fired, on, modes, ends, left, added, under, digests in found:
            runs.setdefault(label, []).append((ends, left, digests))
        same = different = unfinished = 0
        left_now = left_then = 0
        for (ends_a, left_a, dig_a), (ends_b, left_b, dig_b) in zip(runs["working"], runs["trial"]):
            for a, b, la, lb in zip(dig_a, dig_b, left_a, left_b):
                if la is None or lb is None:
                    unfinished += 1
                elif a == b:
                    same += 1
                else:
                    different += 1
                left_then += bool(la and la[0])
                left_now += bool(lb and lb[0])
        print(f"  {same + different + unfinished} walks, half with one release in ten missed: the whole log is the same in {same}, "
              f"differs in {different}; {unfinished} did not finish on one of the two")
        print(f"  walks with a layer left over after everything is let go: working {left_then}, trial {left_now}")


if __name__ == "__main__":
    main()
