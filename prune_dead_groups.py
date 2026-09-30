#!/usr/bin/env python3
"""Remove dead groups from a Steam Input layout JSON.

Steam never runs these, but they hide stale bindings and make audits noisy:

1. Plain-inactive source slots: `group_source_bindings` entries whose state is
   exactly `inactive`. Steam keeps these to remember an alternate source mode.
2. Unreferenced groups: groups that no preset slot and no `mode_shift` binding
   references after step 1.

Kept: `active` slots (including `disabled`-mode groups, which switch a source
off on purpose), every slot whose state contains `modeshift`, and any group a
`mode_shift` binding targets. Group IDs are never renumbered, and layers,
presets, `actions` and `action_layers` are never touched, so runtime layer IDs
cannot shift. Works with numeric IDs or readable title tokens. Idempotent.
"""
import argparse
import json
from pathlib import Path
import sys

from steam_layout.fixes.dead_groups import mode_shift_targets, prune  # noqa: F401  (re-exported)

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layouts", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = parser.parse_args()
    reports = {}
    for path in args.layouts:
        data = json.loads(path.read_text(encoding="utf-8"))
        report = prune(data)
        reports[str(path)] = report
        if not args.dry_run:
            path.write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
        if not args.json:
            verb = "would remove" if args.dry_run else "removed"
            print(f"{path}: {verb} {len(report['removed_inactive_slots'])} inactive slot(s) and "
                  f"{len(report['removed_groups'])} group(s); {report['remaining_groups']} group(s) remain")
    if args.json:
        json.dump(reports, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
