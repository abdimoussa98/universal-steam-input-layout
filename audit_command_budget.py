#!/usr/bin/env python3
"""Check the repo's maximum of three GUI command entries per input.

Also fails on banned activation types: Long Press and Double Press misbehave
with Steam's layer API (see resources/Steam Input JSON Structure.md, Allowed
Activation Types). Builders that only need the budget read `violations`; the
CLI fails on both lists.

One exception: a delayed-apply reset may be a 4th entry when it is the last
entry. Steam's desktop editor drops entries past the third, so the reset is
the only thing lost there (author decision, 2026-09-30). These are reported as
`allowed_fourth` rather than violations.

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
BANNED_ACTIVATORS = ("Long_Press", "Double_Press")
REMOVE = "controller_action remove_layer "


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


def droppable_fourth(entries):
    """True when entry 4 is the last entry and resets this input's own chorded delay.

    The reset is a Regular Press removing only the layer a same-input chord adds
    after `delay_start`, with Hold to Repeat and Interruptable off. Entry order is
    the serialized (VDF/GUI) order, which is what the desktop editor truncates.
    """
    if len(entries) != MAX_COMMANDS + 1:
        return False
    last = entries[-1]
    settings = last["settings"]
    if not (last["activation"] == "Full_Press" and settings.get("hold_repeats") == "1"
            and settings.get("interruptable") == "0" and len(last["actions"]) == 1
            and last["actions"][0].startswith(REMOVE)):
        return False
    target = last["actions"][0].replace("remove_layer", "add_layer", 1)
    return any(entry["activation"] == "chord" and entry["settings"].get("delay_start")
               and entry["actions"] == [target] for entry in entries[:-1])


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
    allowed = []
    banned = []
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
                    over = {**row, "bank": bank, "count": len(entries), "entries": entries}
                    if bank == "activators" and droppable_fourth(entries):
                        allowed.append(over)
                    else:
                        violations.append(over)
                for entry in entries:
                    if entry["activation"] in BANNED_ACTIVATORS:
                        banned.append({"group_id": gid, "input": input_name, "owners": owners[gid],
                                       "bank": bank, "activation": entry["activation"],
                                       "path": entry["path"]})
    missing = sorted(set(owners) - group_ids)
    if missing:
        raise ValueError(f"Preset references missing groups: {', '.join(missing)}")
    summary = {"action_sets": len(cm["actions"]), "layers": len(cm["action_layers"]),
               "groups": len(group_ids), "unreferenced_groups": sum(not owners[g] for g in group_ids),
               "plain_inactive_slots": sum(o["source_state"].split(" ", 1)[-1] == "inactive"
                                           for rows in owners.values() for o in rows),
               "inputs": len(inputs), "commands": sum(row["commands"] for row in inputs),
               "disabled_commands": sum(row["disabled_commands"] for row in inputs),
               "command_histogram": dict(sorted(Counter(row["commands"] for row in inputs).items())),
               "max_commands": max((row["commands"] for row in inputs), default=0),
               "max_actions_in_one_command": max(
                   (row["max_actions_in_one_command"] for row in inputs), default=0),
               "violations": len(violations), "allowed_fourth": len(allowed),
               "banned_activators": len(banned)}
    return {"file": source, "limit": MAX_COMMANDS, "summary": summary,
            "violations": violations, "allowed_fourth": allowed,
            "banned_activators": banned, "inputs": inputs}


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
            status = "FAIL" if s["violations"] or s["banned_activators"] else "PASS"
            print(f"{report['file']}: {status}; {s['groups']} groups, {s['inputs']} inputs, "
                  f"{s['violations']} violation(s), max {s['max_commands']} enabled commands, "
                  f"{s['banned_activators']} banned activator(s), {s['allowed_fourth']} allowed 4th-entry "
                  f"reset(s); {s['unreferenced_groups']} unreferenced "
                  f"group(s), {s['plain_inactive_slots']} plain-inactive slot(s)")
            for row in report["banned_activators"]:
                labels = "; ".join(f"{owner['title']} ({owner['source_state']})" for owner in row["owners"])
                print(f"  banned {row['activation']}: group {row['group_id']} / {row['input']} "
                      f"— {labels or 'unreferenced'}")
            for row in report["allowed_fourth"]:
                labels = "; ".join(owner["title"] for owner in row["owners"])
                print(f"  allowed 4th entry (reset, dropped on desktop): group {row['group_id']} / "
                      f"{row['input']} — {labels or 'unreferenced'}")
            for row in report["violations"]:
                labels = "; ".join(f"{owner['title']} ({owner['source_state']})" for owner in row["owners"])
                print(f"  group {row['group_id']} / {row['input']}: {row['count']} "
                      f"{row['bank']} entries — {labels or 'unreferenced'}")
                print(f"  {row['path']}/{row['bank']}")
    return 1 if any(report["violations"] or report["banned_activators"] for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
