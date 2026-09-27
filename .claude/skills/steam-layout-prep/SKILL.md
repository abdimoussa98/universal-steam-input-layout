---
name: steam-layout-prep
description: Prepare a Steam Input layout in this repo for editing or analysis. Gets it into JSON, runs pre-flight checks (layer list order vs. Preset_ numbering, preset block order, duplicate layer titles), and converts numeric runtime IDs into readable {{Base::Title}} tokens with convert_runtime_ids.py to-titles. Use this whenever you're about to read, audit, diff, or edit a layout (neptune/, findings/, archived/), when a file shows `controller_action add_layer 32 0 0`-style numeric IDs, or when the user reports layers being swapped or mis-targeted after loading into Steam.
---

# Prep a layout for editing

Runtime IDs in `controller_action` commands are positional: action sets are numbered first (from 1), then layers, in the order they appear. That makes numeric IDs fragile, so all editing happens in `{{title}}` token form.

## 1. Get to JSON

The scripts only read JSON. VDF ↔ JSON conversion happens outside this repo, in the VS Code extension `pfwobcke.vscode-vdf`. If you only have a `.vdf`, ask the user to convert it, and keep the `.vdf` as the source export.

## 2. Run the pre-flight check

```bash
python3 - path/to/layout.json <<'EOF'
import json, sys, collections
cm = json.load(open(sys.argv[1]))["controller_mappings"]
order = list(cm["actions"]) + list(cm["action_layers"])
keys = [int(k.split("_")[1]) for k in cm["action_layers"]]
dups = [t for t, n in collections.Counter(v["title"] for v in cm["action_layers"].values()).items() if n > 1]
print("layer order:  ", "OK" if keys == sorted(keys) else "OUT OF ORDER (list order != Preset_ numeric order)")
print("preset blocks:", "OK" if [p["name"] for p in cm["preset"]] == order else "MISMATCH (not in actions + layers order)")
print("preset ids:   ", "OK" if [p["id"] for p in cm["preset"]] == [str(i) for i in range(len(cm["preset"]))] else "not sequential 0..N")
print("dup titles:   ", dups or "none")
print("title form:   ", "yes" if "controller_action add_layer {{" in open(sys.argv[1]).read() else "no (numeric IDs)")
EOF
```

What each result means:

- **dup titles** (for example the two `DEPRECATED` layers): rename them so each title is unique *before* step 3. `to-titles` turns both IDs into the same token, and after that they can't be told apart. `to-ids` resolves every duplicate token to the last layer with that title.
- **layer order OUT OF ORDER**: the `action_layers` list order and the `Preset_` numeric order disagree. On a fresh VDF load Steam can resolve runtime IDs by either order, which silently swaps layers. This is the July 2026 bug; see `findings/2026-07-11-layer-order-swap/FINDINGS.md`. Fix it after step 3, while the file is in title form:
  1. Reorder `action_layers` into numeric key order.
  2. Move the matching `preset` blocks the same way.
  3. Resequence the preset `id` fields to 0..N.

  The `neptune/` files are out of order too and have always loaded on the Deck. The Triton layout was the one that broke.
- **preset blocks MISMATCH / preset ids not sequential**: fix these together with the reorder above.
- **title form: yes**: the file is already readable (the `findings/` snapshots are), so skip step 3.

## 3. Convert IDs to titles

```bash
python3 convert_runtime_ids.py to-titles path/to/layout.json                                   # in place
python3 convert_runtime_ids.py to-titles path/to/layout.json --output path/to/layout_readable.json
```

Token format:
- Action sets: `{{Base}}`
- Layers: `{{Base::RST: Temporary Gyro}}`, where the `Parent::` prefix tells apart layers with the same name in different sets

## Reading the file

- **Chords are encoded per device.**
  - `controller_neptune` (Deck) uses `chord_button` IDs.
  - `controller_triton` uses `gyro_ratchet_button_mask` bitmasks.
  - The decode table is in the appendix of `findings/2026-09-27-exploratory-layout-audit/AUDIT.md`.
  - `button_escape` is the user's "Menu Right" and `button_menu` is "Menu Left".
- **Only some groups are live.** In `group_source_bindings`, groups marked `inactive` are dormant alternate modes. Only `active` groups and `mode_shift` targets affect behavior.

## Guardrails

- Never hand-edit numeric runtime IDs; convert to titles first.
- In a numeric file, don't reorder or insert entries in `actions` / `action_layers`, because every ID after the change shifts. In title form, reordering is safe as long as the `preset` blocks move in step.
- Use `--output` while experimenting so you can diff and roll back.
- Watch out for a numeric file whose layers were reordered or deleted without remapping. Its IDs no longer match list order, so `to-titles` would mislabel every bind. Either re-export from Steam, or remap using a known old→new mapping with the legacy `id_replacement/replace_layer_ids_flexible.py` (`-i`, `-m`, `-o`, `--dry-run`).

## References

- Script usage: `README.md`
- JSON structure and runtime ID rules: `resources/Steam Input JSON Structure.md`
- Converter: `convert_runtime_ids.py`
