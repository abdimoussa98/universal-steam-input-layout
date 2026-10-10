#!/usr/bin/env python3
"""Inventory live layer-command beep requests without changing either layout.

Run from any directory, optionally writing the report with --output. Layouts
are preflighted before their numeric IDs are converted to titles in memory.
The sibling VDF check compares ordered layer-command/flag tuples, not the
whole VDF structure. It does not regenerate VDF or assert audible behavior.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steam_layout.model import Layout, actions  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles  # noqa: E402

COMMAND = re.compile(r"controller_action (add_layer|remove_layer|hold_layer) "
                     r"(\{\{.+?\}\}|\d+) (\d+) (\d+)")
LAYER_PREFIX = re.compile(r"controller_action (?:add_layer|remove_layer|hold_layer)\b")
SHIFT = re.compile(r"mode_shift (\S+) (\d+)")
QUOTED = re.compile(r'"((?:\\[^\r\n]|[^"\\\r\n])*)"')
BANKS = ("activators", "disabled_activators")
CATEGORIES = ("active", "mode_shift_only", "inactive_only", "unreferenced")
FN = ("Menu Left: Fn Layer", "Menu Right: Fn Layer",
      "Stateful | Menu Left: Fn Layer", "Stateful | Menu Right: Fn Layer")


def pointer(parts):
    return "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, (*path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, (*path, index))
    elif isinstance(value, str):
        yield path, value


def layer_tuple(command):
    match = COMMAND.match(command)
    if not match:
        if LAYER_PREFIX.match(command):
            raise ValueError(f"Layer command missing explicit flags: {command}")
        return None
    return match.groups()


def preflight(data):
    cm = data["controller_mappings"]
    keys = [int(key.split("_")[1]) for key in cm["action_layers"]]
    titles = [item["title"] for item in cm["action_layers"].values()]
    checks = {
        "layer_order": keys == sorted(keys),
        "preset_block_order": [p["name"] for p in cm["preset"]]
        == list(cm["actions"]) + list(cm["action_layers"]),
        "sequential_preset_ids": [p["id"] for p in cm["preset"]]
        == [str(i) for i in range(len(cm["preset"]))],
        "unique_layer_titles": len(titles) == len(set(titles)),
    }
    if not all(checks.values()):
        raise ValueError(f"Preflight failed: {checks}")
    return checks


def counter_rows(counter):
    return [{"op": op, "target": target, "display": display, "beep": beep, "count": count}
            for (op, target, display, beep), count in sorted(counter.items())]


def audit(variant):
    path = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
    original_text = path.read_text()
    original = json.loads(original_text)
    checks = preflight(original)
    readable, _ = ids_to_titles(original_text, generate_lookup(original))
    data = json.loads(readable)
    layout = Layout(data)
    references = defaultdict(list)
    active = set()
    for index, preset in enumerate(layout.cm["preset"]):
        for gid, state in preset["group_source_bindings"].items():
            source, status = state.split(maxsplit=1)
            references[gid].append({
                "layer": layout.titles[preset["name"]], "source": source, "state": status,
                "path": pointer(("controller_mappings", "preset", index, "group_source_bindings", gid)),
            })
            if status == "active":
                active.add(gid)

    # Record every entry and every mode-shift reference before classifying groups.
    slots, shift_edges, shift_references = [], defaultdict(set), defaultdict(list)
    for index, group in enumerate(layout.cm["group"]):
        gid = group["id"]
        for name, slot in group.get("inputs", {}).items():
            for bank in BANKS:
                for kind, values in (slot.get(bank) or {}).items():
                    for offset, entry in enumerate(values if isinstance(values, list) else [values]):
                        parts = ("controller_mappings", "group", index, "inputs", name, bank, kind)
                        if isinstance(values, list):
                            parts += (offset,)
                        slots.append((gid, name, bank, kind, entry, parts))
                        for command in actions(entry):
                            if match := SHIFT.match(command):
                                target = match.group(2)
                                shift_references[target].append({"from_group": gid, "bank": bank,
                                                                 "entry_path": pointer(parts)})
                                if bank == "activators":
                                    shift_edges[gid].add(target)
    reachable = set(active)
    pending = list(active)
    while pending:
        for target in shift_edges[pending.pop()]:
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    categories = {gid: "active" if gid in active else "mode_shift_only" if gid in reachable
                  else "inactive_only" if references[gid] else "unreferenced" for gid in layout.groups}
    totals = Counter()
    bank_counts = {(category, bank): Counter() for category in CATEGORIES for bank in BANKS}
    group_counts = defaultdict(Counter)
    target_counts = defaultdict(Counter)
    flags = Counter()
    beep_entries, silent_clears, fn_adds = [], [], defaultdict(list)
    inspected_commands = []

    for gid, name, bank, kind, entry, parts in slots:
        commands = actions(entry)
        parsed = [item for command in commands if (item := layer_tuple(command))]
        inspected_commands.extend(parsed)
        for op, target_ref, display, beep in parsed:
            target = layout.resolve(target_ref)
            totals[op] += 1
            flags[f"{display} {beep}"] += 1
            target_counts[target][op] += 1
            bucket = bank_counts[(categories[gid], bank)]
            bucket["layer_commands"] += 1
            group_counts[gid]["layer_commands"] += 1
            if beep == "1":
                bucket["beep_commands"] += 1
                group_counts[gid]["beep_commands"] += 1
                target_counts[target][op + "_beep"] += 1
        beep_commands = [{"execution_index": index, "op": item[0],
                          "target": layout.resolve(item[1]), "display": item[2], "beep": item[3]}
                         for index, command in enumerate(reversed(commands))
                         if (item := layer_tuple(command)) and item[3] == "1"]
        row = {
            "path": pointer(parts), "group_id": gid, "group_category": categories[gid],
            "references": references[gid], "mode_shift_references": shift_references[gid],
            "input": name, "bank": bank, "activator": kind, "settings": entry.get("settings", {}),
            "commands_execution_order": list(reversed(commands)), "beep_commands": beep_commands,
        }
        if beep_commands:
            beep_entries.append(row)
        if (kind == "release" and any(r["layer"].startswith("Steering | ")
                                      and r["layer"].endswith(": Modifier 2") for r in references[gid])
                and ("remove_layer", "Steering") in layout.layer_ops(entry) and not beep_commands):
            silent_clears.append(row)
        for op, target_ref, display, beep in parsed:
            target = layout.resolve(target_ref)
            if op == "add_layer" and target in FN:
                fn_adds[target].append({"entry_path": pointer(parts), "group_id": gid,
                                       "bank": bank, "display": display, "beep": beep})

    # A recursive scan catches layer commands a future export puts outside these banks.
    all_readable = [item for _, text in leaves(data) if (item := layer_tuple(text))]
    if Counter(all_readable) != Counter(inspected_commands):
        raise ValueError("Layer commands exist outside the inspected input banks")
    numeric_commands = [item for _, text in leaves(original) if (item := layer_tuple(text))]
    vdf_path = path.with_suffix(".vdf")
    vdf_text = vdf_path.read_text()
    # Layer-command flags contain no escapes; labels are deliberately not part of this check.
    vdf_commands = [item for match in QUOTED.finditer(vdf_text)
                    if (item := layer_tuple(match.group(1)))]
    json_counter, vdf_counter = Counter(numeric_commands), Counter(vdf_commands)
    parity = {
        "scope": "Ordered layer op, numeric target, display flag, beep flag; not full VDF structure or labels",
        "json_commands": len(numeric_commands), "vdf_commands": len(vdf_commands),
        "ordered_match": numeric_commands == vdf_commands,
        "multiset_match": json_counter == vdf_counter,
        "beep_multiset_match": Counter(c for c in numeric_commands if c[3] == "1")
        == Counter(c for c in vdf_commands if c[3] == "1"),
        "json_only": counter_rows(json_counter - vdf_counter),
        "vdf_only": counter_rows(vdf_counter - json_counter),
    }
    if not parity["ordered_match"]:
        raise ValueError(f"JSON/VDF layer-command parity failed for {variant}: {parity}")
    return {
        "json": str(path.relative_to(ROOT)), "vdf": str(vdf_path.relative_to(ROOT)),
        "json_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "vdf_sha256": hashlib.sha256(vdf_path.read_bytes()).hexdigest(),
        "title": layout.cm["title"], "preflight": checks, "json_vdf_parity": parity,
        "total_layer_commands": sum(totals.values()), "commands_by_operation": dict(totals),
        "commands_by_flags": dict(flags), "group_categories": dict(Counter(categories.values())),
        "banks": [{"group_category": category, "bank": bank,
                   "layer_commands": counts["layer_commands"], "beep_commands": counts["beep_commands"]}
                  for (category, bank), counts in bank_counts.items()],
        "groups": [{"id": group["id"], "path": pointer(("controller_mappings", "group", index)),
                    "category": categories[group["id"]], "mode": group["mode"],
                    "references": references[group["id"]],
                    "mode_shift_references": shift_references[group["id"]],
                    "layer_commands": group_counts[group["id"]]["layer_commands"],
                    "beep_commands": group_counts[group["id"]]["beep_commands"]}
                   for index, group in enumerate(layout.cm["group"])],
        "targets": {title: dict(counts) for title, counts in sorted(target_counts.items())},
        "beep_entry_count": len(beep_entries), "beep_entries": beep_entries,
        "multiple_beep_entry_paths": [row["path"] for row in beep_entries if len(row["beep_commands"]) > 1],
        "silent_steering_mod2_clears": silent_clears,
        "fn": {title: {"adds": len(fn_adds[title]),
                       "beep_adds": sum(row["beep"] == "1" for row in fn_adds[title]),
                       "entries": fn_adds[title]} for title in FN},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write compact JSON to this audit artifact; otherwise stdout")
    args = parser.parse_args()
    report = {
        "schema_version": 1,
        "scope": "Stored add_layer/remove_layer/hold_layer flags in both live layouts; no audible-beep claim",
        "paths": "RFC 6901 JSON pointers into the named live JSON; binding arrays execute bottom to top",
        "caveat": "A49 identifies the second flag as beep. Whether absent-target removals beep is unverified; "
        "the current simulator logs flagged commands even when the target did not change.",
        "variants": {variant: audit(variant) for variant in ("default", "alternative")},
    }
    result = json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.output:
        args.output.write_text(result)
        for variant, data in report["variants"].items():
            print(f"{variant}: {data['total_layer_commands']} commands; {data['beep_entry_count']} beep entries; "
                  f"{sum(len(row['beep_commands']) for row in data['beep_entries'])} beep flags; "
                  "preflight and ordered JSON/VDF flag parity PASS")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
