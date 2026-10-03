---
name: steam-layer-duplicate
description: Duplicate an action layer in a Steam Input layout JSON with duplicate_layer.py so existing runtime IDs stay stable, then fix what the script leaves pointing at the original layer (self-references and mode_shift group IDs) and wire the new layer in. Use this whenever the user wants to clone, copy, fork, or make a variant of a layer, such as a starred `*` copy of a modifier layer or a stateful-set version of an existing layer, or wants a backup copy before experimenting.
---

# Duplicate a layer safely

Rule IDs (R108 and so on) point at the [Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md#rule-tables), which holds each rule's full text, example and check.

`duplicate_layer.py` does three things:

- Copies the layer, its preset entry, and every group in its `group_source_bindings`, giving them fresh group IDs.
- Gives the new layer `Preset_<max+1>`.
- Appends the new layer to the **end** of `action_layers` (R103).

Because it appends, no existing runtime ID shifts. List order and `Preset_` numeric order also stay aligned, as long as they were aligned before.

## 1. Pre-flight

Run the check from the `steam-layout-prep` skill. `layer order` must be `OK`. Working in title form is easiest, because references in the copy show up as readable titles.

## 2. Find the source layer

```bash
python3 -m tools.duplicate_layer path/to/layout.json --list        # Preset ID, runtime ID, title
```

## 3. Duplicate it

Pick a unique title. The default is `<title> (Copy)`, and a duplicate title breaks `to-ids`.

```bash
python3 -m tools.duplicate_layer path/to/layout.json Preset_1000055 "New Title" --output path/to/out.json
```

- Without `--output`, the script edits in place and writes `<file>_backup_before_duplicate.json` alongside it. That backup is overwritten on every run and isn't gitignored.
- `--no-backup` skips the backup.
- Keep the printed **Group ID Mapping (old -> new)**; step 5 needs it.

## 4. List what the copy still references

```bash
python3 - path/to/out.json "New Title" <<'EOF'
import json, re, sys
cm = json.load(open(sys.argv[1]))["controller_mappings"]
key = next(k for k, v in cm["action_layers"].items() if v["title"] == sys.argv[2])
gsb = next(p for p in cm["preset"] if p["name"] == key)["group_source_bindings"]
groups = {g["id"]: g for g in cm["group"]}
for gid, state in gsb.items():
    if state.endswith("inactive"):
        continue
    for ref in re.findall(r'(?:add|remove|hold)_layer (?:\{\{[^}]+\}\}|\d+)|mode_shift \S+ \d+', json.dumps(groups[gid])):
        print(f"group {gid} ({state}): {ref}")
EOF
```

## 5. Fix what the script doesn't retarget

Edit only the copy's groups (the new IDs from the mapping).

- **Self-references.** Most layers remove themselves somewhere (53 of 58 in the Triton layout). In the copy, those binds still target the *source* layer, so retarget each `{{Base::<source title>}}` to `{{Base::New Title}}` wherever the intent is "this layer". Leave any that should keep targeting the source. For example, each `*` modifier layer deliberately removes both the regular and the starred copy.
- **Mode shifts.** Each `mode_shift <source> <old group id>` still points at the source layer's mode-shift group. The copy's own duplicated mode-shift groups exist but go unused. Rewrite each old ID to its new ID from the Group ID Mapping. For example, duplicating Split Stick maps 408 → 452, 409 → 453, and 416 → 458.

## 6. Wire the new layer in

Nothing adds it yet.

- Add the `add_layer` / `hold_layer` binds that should enter it.
- Add `remove_layer` binds wherever the original is cleaned up and the copy should be too.
- Follow the `steam-binding-order` skill for where each command goes in the array.

## 7. Re-check

Re-run step 4 and the pre-flight check, then finalize with the `steam-layout-apply` skill.
Run `python3 -m tools.audit_command_budget path/to/layout.json` after retargeting and wiring
the copy: each input may have at most three GUI command entries across activator
types (R109). `binding` array subcommands are allowed beyond three. Duplicating a layer
also duplicates any existing command-budget violations; do not carry them forward.

## Guardrails

- Never insert a copy mid-list in a numeric file, because every ID after it shifts. In title form you may move it, but move the matching preset block with it and resequence the preset `id` fields.
- A duplicate can inherit bugs from its source. Re-read targets after copying: a copy-paste retarget is how RTP: Mouse Buttons ended up removing LTP: Arrow Keys (see `findings/2026-09-27-exploratory-layout-audit/AUDIT.md`).

## References

- Script: `tools/duplicate_layer.py`
- Runtime ID rules: `README.md`, `resources/Steam Input JSON Structure.md`
