#!/usr/bin/env python3
"""Inventory delayed applies and their same-input resets; never modify layouts.

Pass --readable-dir containing default.json and alternative.json made by the
repository's convert_runtime_ids.py to-titles --output command.
"""
import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.audit_command_budget import audit_layout
from tools.convert_runtime_ids import generate_lookup, titles_to_ids

spec = importlib.util.spec_from_file_location(
    "cleanup", ROOT / "findings/2026-09-28-neptune-cleanup-audit/build_inventory.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


def positive_delays(value, path=""):
    """Independently traverse raw JSON, including non-activator locations."""
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key == "delay_start" and float(child) > 0:
                found.add(pointer)
            found.update(positive_delays(child, pointer))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            found.update(positive_delays(child, path + "/" + str(i)))
    return found


def family(entry):
    if not entry["adds"]:
        assert entry["input"] == "always_on_action"
        return "Always On expiry" if entry["removes"] else "Always On output"
    assert len(entry["adds"]) == 1
    target = entry["adds"][0]
    if target == "Turning Ramp Up 1": return "Ramp stage 0 to 1"
    if target == "Turning Ramp Up 0": return "Gyro Off to ramp stage 0"
    if target.endswith(": Fn Layer"): return "Menu entry to Fn"
    if target.endswith(": Double Tap Cover"):
        return "Menu key to double-tap cover" if target.startswith("Menu ") else "Modifier scroll to double-tap cover"
    if target == "RTP: Tap Cover": return "RTP touch to tap cover"
    if target in ("LST: Tap Cover", "RST: Tap Cover"): return "Stick touch to tap cover"
    if target.endswith(": Tap Cover"):
        return "Combined modifier to tap cover" if "&" in target else "Single modifier to tap cover"
    raise ValueError(f"Unclassified delayed apply: {entry['id']} -> {target}")


RECOMMENDATIONS = {
    "Always On expiry": "Exclude: timed self-removal, not delayed addition",
    "Always On output": "Exclude: delayed output, not delayed addition",
    "Ramp stage 0 to 1": "Keep existing reset",
    "Menu entry to Fn": "Keep existing reset",
    "Combined modifier to tap cover": "Keep existing reset",
    "Single modifier to tap cover": "Include candidate: 350 ms reset; validate on Deck",
    "Stick touch to tap cover": "Include candidate: 200 ms reset; validate touch/gyro on Deck",
    "RTP touch to tap cover": "Keep excluded: author-confirmed momentum exception",
    "Modifier scroll to double-tap cover": "Defer: already 3 entries; preserve wheel repeat timing",
    "Menu key to double-tap cover": "Defer: already 3 entries; preserve held-key behavior",
    "Gyro Off to ramp stage 0": "Keep unchanged unless 5 ms handoff failure is reproduced",
}


def small(entry):
    keys = ("id", "group_id", "input", "bank", "activation", "status", "pointer",
            "line", "settings", "bindings", "commands", "owners", "mode_shift_owners")
    return {key: entry[key] for key in keys}


def inspect(variant, readable_dir):
    cleanup.TEMP = str(readable_dir)
    report = cleanup.extract(variant)
    raw = (ROOT / report["file"]).read_text()
    data = json.loads(raw)
    cm = data["controller_mappings"]
    order = list(cm["actions"]) + list(cm["action_layers"])
    layer_keys = [int(key.split("_")[1]) for key in cm["action_layers"]]
    assert layer_keys == sorted(layer_keys)
    assert [p["name"] for p in cm["preset"]] == order
    assert [p["id"] for p in cm["preset"]] == list(map(str, range(len(order))))
    lookup = generate_lookup(data)
    assert len(lookup["id_to_title"]) == len(lookup["title_to_id"])
    restored, count = titles_to_ids((readable_dir / (variant + ".json")).read_text(), lookup)
    assert restored == raw, "Readable copy is stale or conversion changed the source"
    budget = audit_layout(data, report["file"])
    assert not budget["violations"]
    entries = report["entries"]
    delayed = [e for e in entries if float(e["settings"].get("delay_start", 0)) > 0]
    assert positive_delays(data) == {e["pointer"] + "/settings/delay_start" for e in delayed}
    rows = []
    for entry in delayed:
        peers = cleanup.siblings(entry, entries)
        # Match the actual separate, unchorded, un-delayed repeat pattern. Inverse
        # edge cleanup or an unrelated family removal is not the apply reset.
        resets = [e for e in peers if entry["adds"] and
                  e["activation"] == "Full_Press" and len(e["bindings"]) == 1 and
                  e["removes"] == entry["adds"] and
                  e["settings"].get("hold_repeats") == "1" and
                  e["settings"].get("interruptable") == "0" and
                  float(e["settings"].get("delay_start", 0)) == 0 and
                  float(e["settings"].get("repeat_rate", 0)) > float(entry["settings"]["delay_start"])]
        sources = {o["source"] for o in cleanup.active_owners(entry)}
        replacements = [e for e in entries if e["bank"] == "activators" and
                        e["input"] == entry["input"] and any(
                            o["layer"] in entry["adds"] and o["source"] in sources
                            for o in cleanup.active_owners(e))]
        category = family(entry)
        row = small(entry)
        row.update(family=category, recommendation=RECOMMENDATIONS[category],
                   command_entries=len(peers) + 1, siblings=[small(e) for e in peers],
                   dedicated_resets=[small(e) for e in resets],
                   child_same_input_entries=[small(e) for e in replacements])
        rows.append(row)
    summary = dict(positive_delay_entries=len(rows),
                   delayed_add_entries=sum(bool(e["adds"]) for e in delayed),
                   applies_with_reset=sum(bool(row["dedicated_resets"]) for row in rows),
                   families=dict(collections.Counter(row["family"] for row in rows)),
                   delay_statuses=dict(collections.Counter(e["status"] for e in delayed)),
                   roundtrip_references=count, command_budget=budget["summary"])
    return dict(variant=variant, file=report["file"], sha256=report["sha256"],
                summary=summary, delayed_entries=rows,
                intrinsic_timing_entries=[small(e) for e in entries
                                          if e["activation"] in ("Long_Press", "Double_Press")])


def link(row, report):
    return f'[g{row["group_id"]} {row["activation"]}](../../{report["file"]}#L{row["line"]})'


def generate(reports, destination):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "inventory.json").write_text(json.dumps(reports, indent=2, ensure_ascii=False) + "\n")
    doc = ["# Delayed-apply inventory", "", "Generated by `build_inventory.py`; interpretation and recommendations: [AUDIT.md](AUDIT.md).",
           "", "Every positive Fire Start Delay is included. Counts are GUI entries on that group/input/bank, not binding subcommands. Child replacements show static ownership; they do not prove Steam cancels a pending parent repeat. Omitted settings remain omitted in the JSON evidence.", ""]
    for report in reports:
        doc += [f'## {report["variant"].title()}', "", f'Source SHA-256: `{report["sha256"]}`.', "",
                "| Parent layer / source / input | Delayed command | Delay ms | Dedicated reset / repeat ms | Entries | Child overrides same input | Recommendation |",
                "|---|---|---:|---|---:|---|---|"]
        for row in report["delayed_entries"]:
            owners = "; ".join(o["layer"] + " / " + o["source"] for o in row["owners"] if o["state"] == "active")
            targets = "; ".join(c["operation"] + " " + c["target"] for c in row["commands"]) or "; ".join(row["bindings"])
            resets = "; ".join(link(e, report) + " / " + e["settings"]["repeat_rate"] for e in row["dedicated_resets"]) or "None"
            children = "; ".join(link(e, report) for e in row["child_same_input_entries"]) or "—"
            cells = [owners + " / " + row["input"], link(row, report) + ": " + targets,
                     row["settings"]["delay_start"], resets, row["command_entries"], children, row["recommendation"]]
            doc.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |")
        doc += ["", "### Intrinsic activator timing (separate from Fire Start Delay)", ""]
        for row in report["intrinsic_timing_entries"]:
            doc.append(f'- {link(row, report)} — {row["status"]}; `{json.dumps(row["settings"])}`; bindings `{json.dumps(row["bindings"])}`.')
        doc.append("")
    (destination / "INVENTORY.md").write_text("\n".join(doc) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readable-dir", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    reports = [inspect(v, args.readable_dir) for v in ("default", "alternative")]
    generate(reports, args.output_dir)
    for report in reports:
        print(report["variant"], json.dumps(report["summary"]))
