## Skill: Prep a Steam Input layout for editing (VDF → JSON → readable titles)

### When to use
- You’re about to edit a Steam Input layout from this repo.
- You see lots of `controller_action add_layer 32 0 0` style numeric runtime IDs and want it readable.
- You’ve exported or copied a `.vdf` template and need to get to an editable JSON workflow.

### Prereqs / constraints
- **You must start from a JSON layout file** (this repo’s scripts expect JSON).
- **VDF ↔ JSON conversion is external**: use the VSCode extension `pfwobcke.vscode-vdf` to convert a `.vdf` layout to `.json` before running any scripts here.
- Runtime IDs are assigned by **order of appearance**: action sets first (`controller_mappings.actions`), then layers (`controller_mappings.action_layers`). Reordering those blocks will shift IDs.

### Steps
1. **Convert VDF to JSON (external)**
   - In VSCode, use the VDF extension (`pfwobcke.vscode-vdf`) to convert your `*.vdf` to `*.json`.
   - Keep the original `.vdf` around; treat it as the “source export”.

2. **Make the JSON readable (IDs → titles)**
   - Run:
     - `python3 convert_runtime_ids.py to-titles path/to/layout.json`
   - Or write to a separate file:
     - `python3 convert_runtime_ids.py to-titles path/to/layout.json --output path/to/layout_readable.json`

3. **Confirm the title token format**
   - Action sets appear as `{{Base}}`, `{{Gyro}}`, etc.
   - Layers appear as `{{Base::L2}}`, `{{Base::RST: Temporary Gyro}}`, etc.
   - If you see `{{Parent::Title}}`, that’s intentional: it disambiguates duplicate layer names across sets.

### Guardrails
- **Do not hand-edit numeric runtime IDs** in `controller_action` commands. Convert to titles first.
- **Do not reorder** keys in `controller_mappings.actions` or `controller_mappings.action_layers` unless you also plan to remap runtime IDs.
- Prefer `--output` when you’re experimenting so you can diff/rollback easily.

### References
- Repo overview & script usage: `README.md`
- Converter script: `convert_runtime_ids.py`
- Why runtime IDs are fragile: `resources/Steam Input JSON Structure.md`

