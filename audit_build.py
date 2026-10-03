#!/usr/bin/env python3
"""Build audit: every layout audit on every working layout, as one gate.

Runs the four audits on each layout and prints one line per audit. A release
is clean only when every line passes (Layer Definition of Done, section 10).

| Audit | Script | Clean means |
|---|---|---|
| Budget audit | audit_command_budget.py | three entries per input, no banned activators, no inverted D-pad edge layer command |
| Window audit | audit_inheritance.py | no undecided layer command under an Always On window |
| Flow audit | audit_flow_inheritance.py | a chain of adding bindings reaches every layer, no open cover finding |
| Cleanup audit | audit_cleanups.py | every cleanup function and release follows the six cleanup rules; no hidden exit |

Read-only. Exit codes: 0 = every audit passed, 1 = at least one failed.

    python3 audit_build.py                      # both neptune/*_latest.json
    python3 audit_build.py path/to/layout.json  # one layout
    python3 audit_build.py --verbose            # show each failing audit's output
"""
import argparse
from pathlib import Path
import subprocess
import sys
import time

from steam_layout.rules import tag

ROOT = Path(__file__).resolve().parent
ENFORCES = {None: ("R150",)}               # the audit as a whole -> rules (Layer Definition of Done)
AUDITS = [
    ("Budget audit", "audit_command_budget.py"),
    ("Window audit", "audit_inheritance.py"),
    ("Flow audit", "audit_flow_inheritance.py"),
    ("Cleanup audit", "audit_cleanups.py"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layouts", nargs="*", type=Path, help="default: neptune/*_latest.json")
    parser.add_argument("--verbose", action="store_true", help="print the output of each failing audit")
    args = parser.parse_args()
    layouts = args.layouts or sorted((ROOT / "neptune").glob("*_latest.json"))
    if not layouts:
        print("Audit error: no layouts found", file=sys.stderr)
        return 1
    failed = 0
    for layout in layouts:
        print(layout.name)
        for name, script in AUDITS:
            start = time.monotonic()
            result = subprocess.run([sys.executable, str(ROOT / script), str(layout)],
                                    capture_output=True, text=True, cwd=ROOT)
            status = "pass" if result.returncode == 0 else f"FAIL (exit {result.returncode})"
            print(f"  {name:<13} {status:<15} {time.monotonic() - start:.1f}s")
            if result.returncode:
                failed += 1
                print(f"    rerun: python3 {script} {layout}")
                if args.verbose:
                    print((result.stdout + result.stderr).rstrip())
    print(f"Build audit {tag(ENFORCES[None])}:", "clean" if not failed else f"{failed} audit(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
