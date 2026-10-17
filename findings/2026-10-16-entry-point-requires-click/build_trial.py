#!/usr/bin/env python3
"""Trial 90.76 for the Deck, off the line and not published: no `requires_click` on the Entry Points' sticks.

Reads the Neptune 90.75 snapshot and writes both variants into this folder, JSON and VDF. The stick groups of the
layers whose title has "Entry Point" lose `requires_click`, and the title says 90.76; nothing else changes. The
working layouts, the snapshots under versions/ and the tags are not touched (author, 2026-10-16: "i just wanna test
it so the 9076 layout should not be published").

    python3 findings/2026-10-16-entry-point-requires-click/build_trial.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE, VERSION = "90.75", "90.76"
STICKS = ("joystick", "right_joystick")


def build(data):
    """Take `requires_click` off the Entry Points' stick groups and set the version, in place; what changed."""
    cm = data["controller_mappings"]
    names = {key: value["title"] for section in ("actions", "action_layers") for key, value in cm[section].items()}
    groups = {group["id"]: group for group in cm["group"]}
    changed = []
    for preset in cm["preset"]:
        title = names[preset["name"]]
        if "Entry Point" not in title:
            continue
        for gid, state in preset["group_source_bindings"].items():
            source = state.split(" ")[0]
            settings = groups[gid].get("settings") or {}
            if source in STICKS and settings.pop("requires_click", None) is not None:
                changed.append(f"{title}: {source} (group {gid})")
    cm["title"] = cm["title"].rsplit(" :: ", 1)[0] + f" :: {VERSION}"
    return changed


def main():
    for variant in ("default", "alternative"):
        source = ROOT / f"versions/neptune/{SOURCE}/single-set-{variant}_hold-gyro_{SOURCE}.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        changed = build(data)
        output = HERE / f"single-set-{variant}_hold-gyro_{VERSION}.json"
        output.write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
        print(f"{output.relative_to(ROOT)}: {data['controller_mappings']['title']}, "
              f"requires_click off in {len(changed)} groups")
        for line in changed:
            print(f"  {line}")
        subprocess.run(["node", str(ROOT / "tools/convert_vdf.mjs"), str(output)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
