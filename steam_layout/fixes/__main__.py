"""CLI: python3 -m steam_layout.fixes LAYOUT.json [...] [--only NAME] [--dry-run]"""
import argparse
import json
from pathlib import Path
import sys

from . import ENFORCES, PIPELINE, __doc__ as PIPELINE_DOC, apply_all
from ..rules import tag


def summarize(report):
    for key in ("changed", "removed_groups", "removed_inactive_slots"):
        if key in report:
            return f"{len(report[key])} {key.replace('_', ' ')}"
    return "done"


def main():
    parser = argparse.ArgumentParser(description=PIPELINE_DOC, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layouts", nargs="+", type=Path)
    parser.add_argument("--only", action="append", choices=[name for name, _ in PIPELINE],
                        help="run only this fix (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()
    for path in args.layouts:
        data = json.loads(path.read_text(encoding="utf-8"))
        reports = apply_all(data, args.only)
        if not args.dry_run:
            path.write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
        print(f"{path}{' (dry run)' if args.dry_run else ''}:")
        for name, report in reports.items():
            print(f"  {name} {tag(ENFORCES[name])}: {summarize(report)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
