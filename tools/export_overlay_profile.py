"""Export a read-only display profile plus its interpretation report."""
import argparse
import json
from pathlib import Path
from steam_layout.overlay_profile import export_profile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('layout', type=Path)
    p.add_argument('--controller', required=True, choices=['ibex'])
    p.add_argument('--version', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.resolve() == args.layout.resolve():
        p.error('Output must not overwrite the source layout')
    try:
        profile, report = export_profile(args.layout.read_bytes(), controller=args.controller, version=args.version)
    except (ValueError, OSError) as exc:
        p.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2, ensure_ascii=False)+'\n')
    report_path=args.output.with_suffix('.report.json')
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(f'{args.output}: {len(report["issues"])} unavailable/unsupported findings; report: {report_path}')


if __name__ == '__main__': main()
