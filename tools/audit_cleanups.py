#!/usr/bin/env python3
"""Cleanup audit: what the cleanup functions and the releases remove, and where a layer must have one.

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
| Touch without cleanup | a layer has no cleanup function on a stick touch (R169) |
| Edge without cleanup | a layer binds or blocks a stick edge, or a face, D-pad, menu or back button, and has no cleanup function on that edge (R170) |
| Button without cleanup | a layer retypes or blocks a button and has no cleanup function on it (R171) |

The last three are the required cleanups (author, 2026-10-04; steam_layout/required_cleanups.py).
They read each layer on its own. Windows, stateful layers and ramp layers are left out, the
stick-touch helpers are left out of the touch check, and a layer's own button and a cancellation
pass the button check. An accepted input is an exception to R169, R170 or R171 in the register.

The stacks are the backward chains (steam_layout/chains.py). Chords are ignored,
and timing and missed releases are not modelled. Deliberate clears and the
stick-touch release's fixed layers are exempt from "Never there". Layers that
only hold_layer adds are left out. A removal the author keeps is an exception
to R132 in the exceptions register (steam_layout/flow_config.json), with a reason.

The two exit checks read the chain walk with 6 extra presses per chain: one layer's
chain with up to six arrivals, every stack tested, and every stack one landing past
it. `--extras K` changes the number (0 to 14). A compiled engine does the walk
(steam_layout/native.py builds steam_layout/engine/chain_engine.cpp on first use), so
the audit needs a C++ compiler and stops with a message without one. On 90.23 it adds
about 15 s and 2 GB per layout; 7 extra presses take 50 s and 6 GB, 8 take 8 minutes
and 11 GB. `--memory GB` stops the walk; the audit then fails as not finished.

Read-only. One of the four audits in audit_build.py since 90.12; the
`cleanup_lists` fix (steam_layout/fixes) resolves its findings. Exit codes:
0 = clean, 1 = findings or a walk that didn't finish, 2 = invalid input or no C++ compiler.

    python3 -m tools.audit_cleanups neptune/single-set-default_hold-gyro_latest.json
    python3 -m tools.audit_cleanups <layout> --layer "L1: Modifier 0"
    python3 -m tools.audit_cleanups <layout> --check "never there" --json
    python3 -m tools.audit_cleanups <layout> --extras 4
    python3 -m tools.audit_cleanups <toy layout> --no-required      # the list and exit checks alone
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

from steam_layout import changes, required_cleanups
from steam_layout.cleanups import DEFAULT_EXTRAS, run
from steam_layout import cleanups
from steam_layout.exceptions import load_config
from steam_layout.rules import tag

RULES = Path(__file__).resolve().parents[1] / "steam_layout" / "flow_config.json"
CHECKS = cleanups.CHECKS + required_cleanups.CHECKS
ENFORCES = {**cleanups.ENFORCES, **required_cleanups.ENFORCES}


def audit(data, config=None, only=None, required=True, **walk):
    """The Cleanup audit's whole report: the list and exit checks (cleanups.py), then the three required-cleanup
    checks on the same stacks (required_cleanups.py). `walk` is passed to `cleanups.run`. `required=False`
    leaves the three out, for a toy layout that only shows a list or an exit."""
    report, stacks = run(data, config, only, **walk)
    if not required:
        report["counts"].update({check: {"findings": 0, "bindings": 0} for check in required_cleanups.CHECKS})
        report["required"] = {"excepted": [], "left_out": {}}
        return report
    found = required_cleanups.audit(stacks, config, only)
    report["findings"] += found["findings"]
    report["counts"].update(found["counts"])
    report["stale_decisions"] += found["stale_decisions"]
    report["ok"] = report["ok"] and found["ok"]
    report["required"] = {"excepted": found["excepted"], "left_out": found["left_out"]}
    return report


def print_report(report, checks):
    lay, s = report["layout"], report["summary"]
    print(f"Layout: {lay['title']} ({lay['variant']})")
    print(f"{s['cleanup_functions']} cleanup functions on {s['layers_with_cleanup']} of {s['layers']} layers; "
          f"stateful: {', '.join(s['stateful']) or 'none'}")
    if report["omitted"]:
        print("Left out (only hold_layer adds them): " + ", ".join(report["omitted"]))
    w = report.get("walk")
    if w:
        print(f"Exit checks: the chain walk with {w['extras']} extra presses, {w['stacks']:,} stacks, "
              + ("settled" if w["settled"] else f"NOT FINISHED: {w['stopped']}"))
    print()
    for check in CHECKS:
        c = report["counts"][check]
        label = f"{check} {tag(ENFORCES[check])}"
        unit = "input(s)" if check in required_cleanups.CHECKS else "binding(s)"
        print(f"{'ok  ' if not c['findings'] else 'FAIL'}  {label:32} {c['findings']:4} finding(s) in {c['bindings']} {unit}")
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
                if check in required_cleanups.CHECKS:
                    print(f"    {', '.join(f['inputs'])}: {f['reason']}")
                elif check == "guard mismatch":
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
    required = report["required"]
    if required["excepted"]:
        print("\nSet aside by an exception to a required cleanup")
        for e in required["excepted"]:
            print(f"  {e['layer']} / {e['input']} {tag(ENFORCES[e['check']])}: {e['why']}")
    if required["left_out"]:
        print("\nLeft out of the required cleanups: " + "; ".join(
            f"{len(layers)} {kind} layer(s)" + (" (the touch check only)" if kind == "helper" else "")
            for kind, layers in required["left_out"].items()))
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
    parser.add_argument("--extras", type=int, default=DEFAULT_EXTRAS, metavar="K",
                        help=f"extra presses per chain in the two exit checks, 0 to 14 (default: {DEFAULT_EXTRAS})")
    parser.add_argument("--memory", type=float, default=12.0, metavar="GB", help="stop the walk at this much memory")
    parser.add_argument("--no-required", action="store_true",
                        help="leave out the three required-cleanup checks (R169 to R171); the build audit never does")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.extras <= 14:
        parser.error("--extras takes 0 to 14 extra presses")

    def progress(extras, states):
        print(f"  walk: {extras} extra presses, {states:,} states", file=sys.stderr, flush=True)

    try:
        data = json.loads(args.layout.read_text(encoding="utf-8"))
        config = load_config(args.rules)
        changed = changes.changed_since(data, changes.baseline_for(args.layout, args.baseline))
        report = audit(data, config, only=args.layer, required=not args.no_required, changed=changed, extras=args.extras,
                       memory=int(args.memory * 1024 ** 3), progress=None if args.json else progress)
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
