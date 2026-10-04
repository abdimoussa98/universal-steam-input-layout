#!/usr/bin/env python3
"""Trial of the suggested fixes for R169 to R171, on scratch copies of the working layouts.

Nothing here is installed. It copies each working layout, gives every input the Cleanup audit
names a cleanup function in the shape suggested-fixes.md describes, runs the `cleanup_lists`
fix so the new lists follow R127 to R132, writes the copy to a scratch folder and runs the four
audits on it. It prints what it changed and what the audits say.

    python3 findings/2026-10-04-required-cleanups/trial_fixes.py            # both layouts, a temporary folder
    python3 findings/2026-10-04-required-cleanups/trial_fixes.py --out DIR  # keep the scratch copies
    python3 findings/2026-10-04-required-cleanups/trial_fixes.py --delete-blocks # the option not chosen for decision 1

The shapes, by what the input holds today:

    nothing (open)              touch: the stick-touch Release, the guard chord, the cleanup
                                edge: the guard chord and the cleanup; the group states its edge radius
    a Release only              the guard chord and the cleanup beside it
    an owner chord already      the cleanup beside it (the menu Entry Points)
    an empty block              the guard chord and the cleanup; deleted when it covers nothing
    a Regular Press output      the output moves into the guard chord; the cleanup is the Regular Press
    a Regular Press and a Release (the Steering W and S layers' other driver)
                                the Regular Press becomes the guard chord; the cleanup is the Regular Press

The guard is one chord, Any, not interruptible: the buttons of the layer's other cleanup
functions, else the buttons that keep it on. The Steering stick layers take the drivers; the
stick modifiers' right edge takes their two "driver and left stick out" chords; the Entry Guard
and the Fallback Hold take the left stick being out.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from steam_layout import exceptions, required_cleanups as required          # noqa: E402
from steam_layout.cleanups import Cleanups                                  # noqa: E402
from steam_layout.model import Layout                                       # noqa: E402

spec = importlib.util.spec_from_file_location("required_cleanups_builder", Path(__file__).with_name("build_candidate.py"))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
Trial = builder.Fixes                    # the builder's fixes, here run on scratch copies of the working layouts

AUDITS = (("Budget", "tools.audit_command_budget", False), ("Window", "tools.audit_inheritance", False),
          ("Flow", "tools.audit_flow_inheritance", True), ("Cleanup", "tools.audit_cleanups", True))


def audits(path, baseline):
    found = {}
    for name, module, takes_baseline in AUDITS:
        command = [sys.executable, "-m", module, str(path)] + (["--baseline", str(baseline)] if takes_baseline else [])
        result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
        found[name] = (result.returncode, result.stdout + result.stderr)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, help="keep the scratch copies and the audits' output here")
    parser.add_argument("--delete-blocks", action="store_true",
                        help="delete a block that covers nothing (the option the author did not choose)")
    parser.add_argument("--no-audits", action="store_true", help="only apply the fixes and count what is left")
    args = parser.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix="required-cleanups-"))
    out.mkdir(parents=True, exist_ok=True)
    config = exceptions.load_config()
    for variant in ("default", "alternative"):
        working = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
        data = json.loads(working.read_text(encoding="utf-8"))
        version = data["controller_mappings"]["title"].rsplit(" ", 1)[-1]
        trial = Trial(data, not args.delete_blocks)
        inputs, lists = trial.run(config)
        path = out / working.name
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        (out / f"{variant}-changes.txt").write_text("\n".join(trial.log + ["", "cleanup_lists fix:"] + lists["changed"]) + "\n",
                                                    encoding="utf-8")
        after = required.audit(Cleanups(Layout(data)), config)
        left = {check: after["counts"][check]["bindings"] for check in required.CHECKS}
        skipped = [line for line in trial.log if "NOT TRIALLED" in line]
        print(f"{variant}: {inputs} inputs, {len(trial.log) - len(skipped)} changes, {len(skipped)} not trialled, "
              f"{len(lists['changed'])} list edits by the cleanup_lists fix ({lists['remaining']} left)")
        print(f"  required cleanups still missing: {left}")
        for line in skipped:
            print("  " + line)
        if args.no_audits:
            continue
        baseline = ROOT / f"versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json"
        for name, (code, text) in audits(path, baseline).items():
            (out / f"{variant}-{name.lower()}-audit.txt").write_text(text, encoding="utf-8")
            print(f"  {name} audit: {'pass' if code == 0 else f'FAIL (exit {code})'}")
    print(f"scratch copies and audit output: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
