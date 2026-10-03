#!/usr/bin/env python3
"""Check what a layer inherits from every stack that can sit beneath it.

Implements the check in resources/Layer Definition of Done.md, section 8
(Inheritance and blocking). Stacks come from the **backward chains**
(steam_layout/chains.py): start at the target, ask which bindings add it, then
which add those layers, back to the action set. Each chain gives one stack.
Other layers that leave the chain's inputs alone and aren't removed by it are
placed underneath as bystanders. There is no depth cap and no config, so a
layer many inputs from the action set (the Steering layers) is checked like
any other. Chords are ignored: a chain follows every adding binding, which can
add a stack that can't happen but never drops one that can.

`traced_stacks.json` can add extra stacks. The decisions are exceptions to R140
in the exceptions register (steam_layout/flow_config.json). A target no stack
reaches is **not checked**, which fails.

For every input the target doesn't define, the effective lower binding is the
topmost layer below that defines it. If that binding changes layers (`add_layer`, `remove_layer`,
`hold_layer`, or a `mode_shift` to a group that does), it is a **route**.

Each route is one of:
  open           nothing blocks it and nobody has decided it -> fails
  allowed        an exception in the register allows it, with a reason
  todo           a known gap recorded for the author's decision

Blocked inputs are reported as cleared (empty binding), replaced (other
output), disabled source, or mode replaced: a layer at or above the definer
binds that source in a different mode, which blocks inheritance (author rule,
2026-10-01). An empty `activators` object is not a block.

Each target also lists **untraced** candidates: inputs that some other layer
anywhere in the layout uses for a layer command, which the target leaves open
and which aren't already routes. They are a call-out for review (for example
Fn and menu-entry stick clicks), not a failure.

For each unblocked route, `blocks_needed` recommends the block: **replace**
with the underlying keybind when only one is possible across the stacks (for
example always E, or always middle mouse), otherwise **clear**, because a
hard-coded replacement would be wrong in some stack. A stack whose binding is
only a layer command adds no keybind.

Every Always On layer is audited automatically. Titles in the config use
default-layout names; `variants` maps them (L1 -> L2, R1 -> R2) for
the alternative layout, which is detected from controller_mappings.title.

Read-only. Works with numeric IDs or title tokens. Exit codes: 0 = ok,
1 = undecided routes or an unchecked target, 2 = invalid input.
`--entries TITLE` lists every binding that adds TITLE and the removals that run
before the add, to help trace stacks.
"""
import argparse
import json
from pathlib import Path
import sys

from steam_layout.inheritance import (  # noqa: F401  (re-exported for tools and tests)
    ENFORCES, STATUSES, audit, blocks_needed, changes_layers, check_stack, entries, strip_layer_api, untraced)
from steam_layout.model import (  # noqa: F401
    EMPTY, LAYER_COMMAND, MODE_SHIFT, TARGET, Layout, always_on_layers, bindings, defined, map_title)
from steam_layout import exceptions
from steam_layout.rules import tag
from steam_layout.stacks import effective_input  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def print_report(report, show_untraced=False):
    print(f"variant: {report['variant']}; {'PASS' if report['ok'] else 'FAIL'}")
    for title, row in report["targets"].items():
        if not row["checked"]:
            print(f"{title}: NOT CHECKED {tag(ENFORCES['unchecked window'])} (no chain or declared stack reaches it)")
            continue
        counts = {}
        for route in row["routes"]:
            counts[route["status"]] = counts.get(route["status"], 0) + 1
        print(f"{title}: {row['stacks']} stack(s) ({row['chain_stacks']} from chains), {len(row['blocked'])} blocked, "
              f"routes {counts or 'none'}")
        for need in row["blocks_needed"]:
            what = json.dumps(need["activators"]) if need["activators"] else ""
            print(f"  block needed {tag(ENFORCES['open routes'])}: {need['source']}/{need['input']} -> {need['action']} {what}")
        for route in row["routes"]:
            if route["status"] == "open":
                print(f"  {route['status']} {tag(ENFORCES['open routes'])}: {route['source']}/{route['input']} from {route['from_layer']} "
                      f"({route['via']}) under {' > '.join(route['stack'])}")
                for line in route["reason"]:
                    print(f"    because: {line}")
        if row["untraced"] and not show_untraced:
            print(f"  untraced: {len(row['untraced'])} input(s) used for layer commands elsewhere (--untraced)")
        for item in row["untraced"] if show_untraced else []:
            layers = ", ".join(item["layers"][:3]) + (f" +{len(item['layers']) - 3}" if len(item["layers"]) > 3 else "")
            print(f"  untraced: {item['source']}/{item['input']} used for layer commands by {layers}")
        for decision in row["stale_decisions"]:
            print(f"  stale decision: {decision['source']}/{decision['input']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--stacks", type=Path, default=ROOT / "traced_stacks.json")
    parser.add_argument("--register", type=Path, default=exceptions.REGISTER,
                        help="exceptions register (default: steam_layout/flow_config.json)")
    parser.add_argument("--entries", metavar="TITLE", help="list bindings that add TITLE, then exit")
    parser.add_argument("--untraced", action="store_true", help="list untraced candidates in full")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.layout.read_text(encoding="utf-8"))
        if args.entries:
            rows = entries(data, args.entries)
            if args.json:
                print(json.dumps(rows, indent=2))
            for row in rows:
                print(f"{row['layer']} [{row['source_state']}] {row['input']} {row['activation']}: "
                      f"removes first {row['removes_first'] or 'nothing'}")
            return 0
        config = exceptions.window(json.loads(args.stacks.read_text(encoding="utf-8")), exceptions.load(args.register))
        report = audit(data, config)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report, args.untraced)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
