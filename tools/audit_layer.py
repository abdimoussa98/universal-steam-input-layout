#!/usr/bin/env python3
"""The three questions for one layer, and what its exits clean up.

For the layer named with --layer:

    Below      the layers that can be under it, each with the bindings that put it there
    Above      the layers that can be on top of it
    Inherited  the inputs it doesn't bind, with the layer and binding each comes from
    Exits      for each of its bindings that removes layers: what it removes that is
               present, what is present and left, and what it removes that is never there

Stacks come from the backward chains (steam_layout/chains.py): who adds the
layer, back to the action set, plus bystanders. Chords are ignored, and stale
layers left by a missed release are not modelled. The Exits lists are a report
for review, not a check (steam_layout/layer_report.py).

Read-only. Works with numeric IDs or title tokens. Exit codes: 0 = report
printed, 2 = invalid input or unknown layer. "Above" works out the stacks of
every layer, so a run takes a few seconds.

    python3 -m tools.audit_layer neptune/single-set-default_hold-gyro_latest.json --layer "L1: Modifier 0"
    python3 -m tools.audit_layer <layout> --layer "Menu Right: Fn Layer" --json
"""
import argparse
import json
from pathlib import Path
import re
import sys

from steam_layout.layer_report import report
from steam_layout.model import TARGET, Layout


def short(layout, binding):
    """A binding string without the boilerplate, with layer references shown as titles."""
    text = re.sub(r", , $", "", binding.replace("controller_action ", "")).strip()
    match = TARGET.search(binding)
    return re.sub(r"_layer \S+ \d+ \d+", f"_layer {layout.resolve(match.group(2))}", text) if match else text


def print_report(layout, result):
    print(f"Layer: {result['layer']}")
    if not result["reached"]:
        print("not reached: no chain of adding bindings leads to it (hold_layer and mode shifts aren't followed)")
        return
    print(f"\nBelow ({len(result['below']['stacks'])} stack(s)): the layers that can be under it")
    for layer, reason in result["below"]["layers"].items():
        print(f"  {layer}")
        for line in reason:
            print(f"      because: {line}")
    print("\nAbove: the layers that can be on top of it")
    for layer in result["above"] or ["(none)"]:
        print(f"  {layer}")
    print("\nInherited inputs: what it doesn't bind, and where each comes from")
    for row in result["inherited"] or []:
        for provider in row["providers"]:
            flag = "  [changes layers]" if provider["changes_layers"] else ""
            print(f"  {row['source']}/{row['input']} from {', '.join(provider['layers'])}: "
                  f"{' | '.join(short(layout, b) for b in provider['bindings'])}{flag}")
    print("\nExits: its bindings that remove layers (for review; not a check)")
    groups = {}   # bindings with the same removals and the same lists are shown once
    for row in result["exits"]:
        key = json.dumps([row["role"], row["removes"], row["present_and_removed"], row["present_not_removed"],
                          row["intercepted_by"], row["removed_never_present"]])
        groups.setdefault(key, []).append(row)
    for same in groups.values():
        row = same[0]
        if len(same) == 1:
            print(f"  {row['binding']}")
        else:
            print(f"  {len(same)} {row['role']} bindings removing: {', '.join(row['removes'])}")
            print(f"    on: {', '.join(r['input'] for r in same)}")
        left = row["present_not_removed"]
        print(f"    present and removed: {', '.join(row['present_and_removed']) or '-'}")
        print(f"    present, not removed: below: {', '.join(left['below']) or '-'}; above: {', '.join(left['above']) or '-'}")
        if row["intercepted_by"]:
            print(f"    intercepted by (binds this input, above): {', '.join(row['intercepted_by'])}")
        print(f"    removed, never present: {', '.join(row['removed_never_present']) or '-'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--layer", required=True, metavar="TITLE")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        layout = Layout(json.loads(args.layout.read_text(encoding="utf-8")))
        result = report(layout, args.layer)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(layout, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
