#!/usr/bin/env python3
"""Prove a cleanup changed no live binding except the ones it was meant to.

Compares every live slot (`active`, or containing `modeshift`) of every preset,
input by input, plus mode-shift targets, layer order/titles and preset order.
Pass --allow LAYER|SLOT|INPUT for each intended change. Exit 1 on any other
difference. Works on numeric-ID files (layer IDs are compared as-is, which is
valid because the cleanup never renumbers layers).
"""
import argparse
import json
import re
import sys


def live(path):
    cm = json.load(open(path, encoding="utf-8"))["controller_mappings"]
    titles = {k: v["title"] for k, v in {**cm["actions"], **cm["action_layers"]}.items()}
    groups = {g["id"]: g for g in cm["group"]}
    targets = set(re.findall(r"mode_shift \S+ (\d+)", json.dumps(cm["group"])))
    slots = {}
    for p in cm["preset"]:
        for gid, state in p["group_source_bindings"].items():
            if state.split(" ", 1)[-1] == "inactive" and gid not in targets:
                continue
            g = groups[gid]
            slots[(titles[p["name"]], state, "(mode+settings)")] = json.dumps(
                [gid, g.get("mode"), g.get("settings", {})], sort_keys=True)
            for name, binding in g.get("inputs", {}).items():
                slots[(titles[p["name"]], state, name)] = json.dumps(binding, sort_keys=True)
    for gid in targets:
        slots[("(mode_shift target)", gid, "")] = json.dumps(groups[gid], sort_keys=True)
    meta = {"layers": [(k, v["title"]) for k, v in cm["action_layers"].items()],
            "actions": list(cm["actions"]), "presets": [(p["id"], p["name"]) for p in cm["preset"]]}
    return slots, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--allow", action="append", default=[], help="LAYER|SLOT|INPUT")
    args = parser.parse_args()
    allowed = {tuple(a.rsplit("|", 2)) for a in args.allow}  # titles may contain "|"
    a, am = live(args.before)
    b, bm = live(args.after)
    problems = [f"{k} differs" for k in am if am[k] != bm[k]]
    seen = set()
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            if key in allowed:
                seen.add(key)
            else:
                problems.append(f"unexpected change: {key}")
    problems += [f"expected change missing: {k}" for k in allowed - seen]
    print(f"{args.after}: {len(a)} live slot inputs compared; {len(seen)} allowed change(s)")
    for p in problems:
        print("  " + p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
