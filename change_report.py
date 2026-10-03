#!/usr/bin/env python3
"""Change report: what differs between two layouts, by layer and input.

Read it before shipping (Layer Definition of Done, section 10). A fix or a
builder can change a binding nobody decided; this is where it shows. Every
layer's live groups are compared: mode, settings and each input's activators,
with layer commands compared by title, so a shifted runtime ID is not a change
(steam_layout/changes.py).

Read-only. Exit codes: 0 = report printed, 2 = invalid input.

    python3 change_report.py                         # each working layout against its newest snapshot
    python3 change_report.py BEFORE.json AFTER.json  # any two layouts
    python3 change_report.py --out findings/<date>-<slug>/   # also write <name>-changes.txt there
    python3 change_report.py --json
"""
import argparse
import json
from pathlib import Path
import sys

from steam_layout import changes

ROOT = Path(__file__).resolve().parent


def pairs(files):
    """[(before, after)] paths: the two given, or each working layout with its newest snapshot."""
    if files:
        if len(files) != 2:
            raise ValueError("give two layouts, or none to compare the working layouts with their newest snapshots")
        return [(files[0], files[1])]
    found = []
    for working in sorted((ROOT / "neptune").glob("*_latest.json")):
        snapshot = changes.newest_snapshot(working.name)
        if snapshot is None:
            raise ValueError(f"no snapshot of {working.name} under versions/neptune/")
        found.append((snapshot, working))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layouts", nargs="*", type=Path, help="BEFORE AFTER (default: newest snapshot, working layout)")
    parser.add_argument("--out", type=Path, help="folder to write <after name>-changes.txt into")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    reports = []
    try:
        for before, after in pairs(args.layouts):
            report = changes.diff(json.loads(before.read_text(encoding="utf-8")),
                                  json.loads(after.read_text(encoding="utf-8")))
            report["before"], report["after"] = str(before), str(after)
            reports.append(report)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(f"Report error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    for report in reports:
        shown = changes.text(report, Path(report["before"]).name, Path(report["after"]).name)
        if not args.json:
            print(shown + "\n")
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / f"{Path(report['after']).stem}-changes.txt").write_text(shown + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
