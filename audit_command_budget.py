#!/usr/bin/env python3
"""Check the repo's maximum of three GUI command entries per input.

Each activator object is one command entry. A binding array contains subcommands
inside that entry and does not consume additional entries. Scans every group,
including inactive/unreferenced groups, and reports disabled entries separately.
Read-only: works with numeric IDs or readable title tokens.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

MAX_COMMANDS = 3


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def command_entries(activators, path):
    if not isinstance(activators, dict):
        raise ValueError(f"{path}: expected an activator object")
    entries = []
    for kind, value in activators.items():
        values = value if isinstance(value, list) else [value]
        for index, entry in enumerate(values):
            entry_path = f"{path}/{kind}" + (f"/{index}" if isinstance(value, list) else "")
            if not isinstance(entry, dict):
                raise ValueError(f"{entry_path}: expected a command object")
            bindings = entry.get("bindings", {})
            if not isinstance(bindings, dict):
                raise ValueError(f"{entry_path}/bindings: expected an object")
            binding = bindings.get("binding", [])
            actions = binding if isinstance(binding, list) else [binding]
            if not all(isinstance(action, str) for action in actions):
                raise ValueError(f"{entry_path}/bindings/binding: expected string(s)")
            entries.append({"path": entry_path, "activation": kind,
                            "actions": actions, "settings": entry.get("settings", {})})
    return entries


def audit_layout(data, source="<memory>"):
    cm = data["controller_mappings"]
    names = {key: value["title"] for section in ("actions", "action_layers")
             for key, value in cm[section].items()}
    owners = defaultdict(list)
    for preset in cm["preset"]:
        for gid, state in preset.get("group_source_bindings", {}).items():
            owners[gid].append({"preset": preset["name"],
                                "title": names[preset["name"]], "source_state": state})
    inputs = []
    violations = []
    group_ids = set()
    for group_index, group in enumerate(cm["group"]):
        gid = group["id"]
        if gid in group_ids:
            raise ValueError(f"Duplicate group ID: {gid}")
        group_ids.add(gid)
        for input_name, value in group.get("inputs", {}).items():
            # JSON Pointer escaping also handles any future input names containing / or ~.
            pointer_name = input_name.replace("~", "~0").replace("/", "~1")
            path = f"/controller_mappings/group/{group_index}/inputs/{pointer_name}"
            enabled = command_entries(value.get("activators", {}), path + "/activators")
            disabled = command_entries(value.get("disabled_activators", {}),
                                       path + "/disabled_activators")
            row = {"group_id": gid, "input": input_name, "path": path,
                   "owners": owners[gid], "commands": len(enabled),
                   "disabled_commands": len(disabled),
                   "binding_actions": sum(len(entry["actions"]) for entry in enabled),
                   "max_actions_in_one_command": max(
                       (len(entry["actions"]) for entry in enabled), default=0)}
            inputs.append(row)
            # Disabled banks are checked too, but never added to the enabled count.
            for bank, entries in (("activators", enabled), ("disabled_activators", disabled)):
                if len(entries) > MAX_COMMANDS:
                    violations.append({**row, "bank": bank, "count": len(entries),
                                       "entries": entries})
    missing = sorted(set(owners) - group_ids)
    if missing:
        raise ValueError(f"Preset references missing groups: {', '.join(missing)}")
    summary = {"action_sets": len(cm["actions"]), "layers": len(cm["action_layers"]),
               "groups": len(group_ids), "unreferenced_groups": sum(not owners[g] for g in group_ids),
               "inputs": len(inputs), "commands": sum(row["commands"] for row in inputs),
               "disabled_commands": sum(row["disabled_commands"] for row in inputs),
               "command_histogram": dict(sorted(Counter(row["commands"] for row in inputs).items())),
               "max_commands": max((row["commands"] for row in inputs), default=0),
               "max_actions_in_one_command": max(
                   (row["max_actions_in_one_command"] for row in inputs), default=0),
               "violations": len(violations)}
    return {"file": source, "limit": MAX_COMMANDS, "summary": summary,
            "violations": violations, "inputs": inputs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit the complete input inventory as JSON")
    args = parser.parse_args()
    reports = []
    try:
        for path in args.files:
            raw = path.read_bytes()
            data = json.loads(raw, object_pairs_hook=unique_object)
            report = audit_layout(data, str(path))
            report["sha256"] = hashlib.sha256(raw).hexdigest()
            reports.append(report)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            s = report["summary"]
            status = "FAIL" if s["violations"] else "PASS"
            print(f"{report['file']}: {status}; {s['groups']} groups, {s['inputs']} inputs, "
                  f"{s['violations']} violation(s), max {s['max_commands']} enabled commands")
            for row in report["violations"]:
                labels = "; ".join(f"{owner['title']} ({owner['source_state']})" for owner in row["owners"])
                print(f"  group {row['group_id']} / {row['input']}: {row['count']} "
                      f"{row['bank']} entries — {labels or 'unreferenced'}")
                print(f"  {row['path']}/{row['bank']}")
    return 1 if any(report["violations"] for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
