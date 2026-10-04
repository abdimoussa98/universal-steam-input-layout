#!/usr/bin/env python3
"""Install the Gamepad candidates into the working Neptune layouts.

Run build_candidate.py first. For each variant this:

1. Loads the numeric candidate export (built from the frozen pre-steering copy).
2. Keeps the working layout's release title and description, optionally
   setting a new release version (`--version 91.0`).
3. Runs the post-install fix pipeline (`steam_layout.fixes`), because the
   frozen source predates every later fix. It also derives the blocks the
   Always On windows need over the new layers.
4. Writes neptune/*_latest.json, exports the sibling VDF and records hashes in
   neptune-installation.json.

`--deck` does steps 1 to 3 and writes the result to deck/ in this folder
instead, with " | gamepad candidate" on the title. The working layouts and
the record are left alone. Use it for the Deck gates before the real install.

Review the description against the final layout before publishing; this script
only carries it forward. Saving the versions/ snapshot stays a separate step.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.fixes import apply_all  # noqa: E402

RECORD = HERE / "neptune-installation.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", help="release suffix for controller_mappings.title, e.g. 91.0")
    parser.add_argument("--deck", action="store_true", help="write a Deck candidate to deck/, not the working layouts")
    args = parser.parse_args()
    if args.version and not re.fullmatch(r"\d+(\.\d+)+", args.version):
        parser.error(f"bad version {args.version!r}")
    if args.version and args.deck:
        parser.error("--deck keeps the working release title; drop --version")
    record = json.loads(RECORD.read_text()) if RECORD.exists() else {"files": {}}
    for variant in ("default", "alternative"):
        working = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
        current = json.loads(working.read_text(encoding="utf-8"))["controller_mappings"]
        candidate_path = HERE / f"{variant}-gamepad.json"
        data = json.loads(candidate_path.read_text(encoding="utf-8"))
        cm = data["controller_mappings"]
        title = current["title"]
        if args.version:
            title = title.rsplit(" :: ", 1)[0] + " :: " + args.version
        if args.deck:
            title += " | gamepad candidate"
        cm["title"], cm["description"] = title, current["description"]
        reports = apply_all(data)
        target = HERE / "deck" / f"single-set-{variant}_hold-gyro_candidate.json" if args.deck else working
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
        subprocess.run(["node", str(ROOT / "tools" / "convert_vdf.mjs"), str(target)], check=True)
        changed = {name: len(r.get("changed", r.get("removed_groups", []))) for name, r in reports.items()}
        print(f"{target.relative_to(ROOT)}: {title}; fixes {changed}")
        if args.deck:
            continue
        version = title.rsplit(" :: ", 1)[-1]
        for path in (target, target.with_suffix(".vdf")):
            rel = str(path.relative_to(ROOT))
            entry = record["files"].setdefault(rel, {})
            entry["sha256"] = sha(path)
            entry["version_snapshot"] = f"versions/neptune/{version}/" + path.name.replace("_latest", "_" + version)
        record["release"] = version
        record.setdefault("candidates", {})[variant] = {"path": str(candidate_path.relative_to(ROOT)),
                                                        "sha256": sha(candidate_path)}
    if not args.deck:
        record["metadata_note"] = ("sha256 is after install_neptune.py: candidate + release title/description, "
                                   "the steam_layout.fixes pipeline.")
        RECORD.write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
