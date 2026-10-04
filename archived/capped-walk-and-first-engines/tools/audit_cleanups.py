#!/usr/bin/env python3
"""Cleanup audit: what the cleanup functions and the releases remove, against the six rules.

The author's rule: every layer takes care of itself and what is below it, and of
what is above it if it has that responsibility. A cleanup function removes only
layers its guard's buttons keep alive, in one step, and a list names only layers
that can be on the stack with it (findings/2026-10-02-cleanup-boundaries/README.md).

| Check | Fails when |
|---|---|
| Outside the guard | a cleanup removes a layer kept by another button, a stateful layer, a stick-touch helper or a window |
| Left below | a layer under the host has the same keeper and isn't removed |
| Left above | a layer on top has the same keeper, leaves the cleanup's input alone, and isn't removed |
| Hidden cleanup | a layer binds an input that has a cleanup below without carrying it |
| Never there | a cleanup, a release or a Modifier 2 quick tap removes a layer that can never be on the stack with it |
| Guard mismatch | one layer's cleanups have different guard buttons |
| Hidden exit | a layer that can land on top of another covers an exit on what keeps the lower layer alive, and doesn't remove it there |
| Exit to review | such a layer covers an exit that isn't on the keeper, and either layer changed since the baseline; fix it or accept it in the register |

The stacks are the backward chains (steam_layout/chains.py). Chords are ignored,
and timing and missed releases are not modelled. Deliberate clears and the
stick-touch release's fixed layers are exempt from "Never there". Layers that
only hold_layer adds are left out. A removal the author keeps is an exception
to R132 in the exceptions register (steam_layout/flow_config.json), with a reason.

`--walk N` reads the two exit checks from other stacks: every stack the bindings
can build with at most N layers on at once, in any order (steam_layout/walk.py).
It is complete up to N, the author's ceiling of 10 being the default. It runs in the
compiled engine (steam_layout/native.py, built with clang++ on first use): 6 s for 8
layers and 25 s and 4 GB for 10. Without a compiler, or with `--python`, it runs in
Python on every core: 71 s for 8 layers, 9 minutes for 10.
`--extras K` reads them from the chain walk with K extra presses per chain instead
(engines only): 3 s for 4, 15 s for 6, 50 s and 6 GB for 7, 8 minutes and 11 GB for 8.
`--memory GB` stops either; the audit then fails as not finished.

Read-only. One of the four audits in audit_build.py since 90.12; the
`cleanup_lists` fix (steam_layout/fixes) resolves its findings. Exit codes:
0 = clean, 1 = findings or a walk that didn't finish, 2 = invalid input.

    python3 -m tools.audit_cleanups neptune/single-set-default_hold-gyro_latest.json
    python3 -m tools.audit_cleanups <layout> --layer "L1: Modifier 0"
    python3 -m tools.audit_cleanups <layout> --check "never there" --json
    python3 -m tools.audit_cleanups <layout> --walk 8
    python3 -m tools.audit_cleanups <layout> --extras 4
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

from steam_layout import changes
from steam_layout.cleanups import CHECKS, ENFORCES, audit
from steam_layout.exceptions import load_config
from steam_layout.rules import tag
from steam_layout.walk import MAX_SIMULTANEOUS

RULES = Path(__file__).resolve().parents[1] / "steam_layout" / "flow_config.json"


def print_report(report, checks):
    lay, s = report["layout"], report["summary"]
    print(f"Layout: {lay['title']} ({lay['variant']})")
    print(f"{s['cleanup_functions']} cleanup functions on {s['layers_with_cleanup']} of {s['layers']} layers; "
          f"stateful: {', '.join(s['stateful']) or 'none'}")
    if report["omitted"]:
        print("Left out (only hold_layer adds them): " + ", ".join(report["omitted"]))
    w = report.get("walk")
    if w:
        what = (f"the chain walk with {w['extras']} extra presses" if w["extras"] is not None
                else f"the walk: every stack with at most {w['layers']} layers on at once")
        done = "settled" if w["extras"] is not None else f"settled after {w['presses']} presses"
        print(f"Exit checks read from {what}, {w['stacks']:,} stacks, "
              + (done if w["settled"] else f"NOT FINISHED: {w['stopped']}")
              + (" (compiled engine)" if w["engine"] else " (Python)"))
    print()
    for check in CHECKS:
        c = report["counts"][check]
        label = f"{check} {tag(ENFORCES[check])}"
        print(f"{'ok  ' if not c['findings'] else 'FAIL'}  {label:32} {c['findings']:4} finding(s) in {c['bindings']} binding(s)")
    for check in checks:
        rows = [f for f in report["findings"] if f["check"] == check]
        if not rows:
            continue
        print(f"\n== {check.capitalize()} {tag(ENFORCES[check])}")
        by_layer = defaultdict(list)
        for f in rows:
            by_layer[f["layer"]].append(f)
        for layer, found in by_layer.items():
            print(f"  {layer}")
            for f in found:
                where = f"{f['bindings']} {f['kind']} binding(s) on {', '.join(f['inputs'])}"
                guard = f", guard {' / '.join(f['guard'])}" if f["guard"] else ""
                if check == "guard mismatch":
                    print(f"    {f['reason']}: {where}")
                elif check == "hidden cleanup":
                    print(f"    hides the cleanup of {f['target']} on {', '.join(f['inputs'])}{guard}")
                elif check in ("hidden exit", "exit to review"):
                    print(f"    covers the exit of {f['target']} ({f['keeper']}) on {', '.join(f['inputs'])}: "
                          f"on {f['example']}")
                else:
                    verb = "leaves" if check.startswith("left") else "removes"
                    print(f"    {verb} {f['target']} ({f['keeper']}): {f['reason']}; {where}{guard}")
    if report["kept"]:
        print("\nKept by decision")
        for k in report["kept"]:
            print(f"  {k['layer']} removes {k['target']}: {k['why']}")
    if report["excepted"]:
        on_keeper = sum(1 for e in report["excepted"] if e["on_keeper"])
        print(f"\nSet aside by an exception {tag(ENFORCES['hidden exit'])}: {on_keeper} pair(s) that cover "
              f"a keeper's exit, {len(report['excepted']) - on_keeper} that cover another exit (--json lists them)")
    if report["information"]["hidden exit"]:
        print("\nInformation: covers an exit that isn't on the keeper, so the keeper's exit still works")
        for i in report["information"]["hidden exit"]:
            print(f"  {i['layer']} over {i['target']} ({i['keeper']}): {', '.join(i['inputs'])}")
    for stale in report["stale_decisions"]:
        print("\nStale decision (matches no finding): " + stale)
    if report["no_cleanup_reaches"]:
        print("\nInformation: no cleanup function removes these, and they have none of their own")
        print("  " + ", ".join(report["no_cleanup_reaches"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--rules", type=Path, default=RULES, help="decisions file (default: steam_layout/flow_config.json)")
    parser.add_argument("--baseline", type=Path, help="the layout to compare with, to find the changed layers "
                        "(default: a working layout's newest snapshot)")
    parser.add_argument("--layer", action="append", metavar="TITLE", help="only this layer's lists (repeatable)")
    parser.add_argument("--check", action="append", choices=CHECKS, metavar="CHECK", help="only print this check's findings")
    parser.add_argument("--walk", nargs="?", type=int, const=MAX_SIMULTANEOUS, metavar="N",
                        help="read the exit checks from every stack with at most N layers on at once "
                        f"(default N: {MAX_SIMULTANEOUS}, the ceiling)")
    parser.add_argument("--extras", type=int, metavar="K",
                        help="read the exit checks from the chain walk with K extra presses per chain (0 to 14); "
                        "needs the compiled engines")
    parser.add_argument("--python", action="store_true", help="run --walk in Python, not in the compiled engine")
    parser.add_argument("--memory", type=float, default=12.0, metavar="GB", help="stop the walk at this much memory")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.walk is not None and not 1 <= args.walk <= MAX_SIMULTANEOUS:
        parser.error(f"--walk takes 1 to {MAX_SIMULTANEOUS} layers")
    if args.extras is not None and (args.walk is not None or not 0 <= args.extras <= 14):
        parser.error("--extras takes 0 to 14 extra presses, and not together with --walk")

    def progress(presses, tested, new, total):
        print(f"  walk: {presses} presses, {total:,} stacks", file=sys.stderr, flush=True)

    try:
        data = json.loads(args.layout.read_text(encoding="utf-8"))
        config = load_config(args.rules)
        changed = changes.changed_since(data, changes.baseline_for(args.layout, args.baseline))
        walking = args.walk is not None or args.extras is not None
        report = audit(data, config, only=args.layer, changed=changed, walk=args.walk, extras=args.extras,
                       engine=False if args.python else None, memory=int(args.memory * 1024 ** 3),
                       progress=progress if walking and not args.json else None)
    except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 2
    if args.check:
        report["findings"] = [f for f in report["findings"] if f["check"] in args.check]
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report, args.check or CHECKS)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
