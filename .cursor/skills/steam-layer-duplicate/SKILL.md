## Skill: Duplicate an action layer safely (preserve existing runtime IDs)

### When to use
- You want to create a new variant of an existing layer (e.g. tweak bindings) without breaking other `controller_action` references.
- You need a “backup copy” of a complex layer before experimenting.

### Prereqs / constraints
- Works on **JSON** layout files.
- Duplicating is safest when it **appends to the end** of `controller_mappings.action_layers` (this repo’s script does that), so existing runtime IDs don’t shift.

### Steps
1. **List layers**
   - `python3 duplicate_layer.py path/to/layout.json --list`

2. **Duplicate a layer by Preset_* ID**
   - Auto title:
     - `python3 duplicate_layer.py path/to/layout.json Preset_1000006`
   - Custom title:
     - `python3 duplicate_layer.py path/to/layout.json Preset_1000006 "My Custom Layer"`

3. **Prefer non-destructive output when iterating**
   - `python3 duplicate_layer.py path/to/layout.json Preset_1000006 --output path/to/layout_with_copy.json`

4. **Backups**
   - By default, the script writes a backup file unless `--output` is used.
   - Use `--no-backup` only when you’re confident in your workflow.

### Guardrails
- Do not manually insert the duplicated layer “in the middle” of `action_layers`; that can shift runtime IDs for everything after it.
- If your file currently uses `{{...}}` tokens, you can keep working in titles mode; just remember to run `convert_runtime_ids.py to-ids` before exporting back to Steam.

### References
- Script: `duplicate_layer.py`
- Runtime ID rules: `README.md`, `resources/Steam Input JSON Structure.md`

