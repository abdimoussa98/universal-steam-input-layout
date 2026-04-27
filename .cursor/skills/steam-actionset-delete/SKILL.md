## Skill: Delete an action set safely (and fix shifted runtime IDs)

### When to use
- You want to remove an action set (and all its associated layers/presets/groups) from a layout.
- You want to avoid breaking `controller_action CHANGE_PRESET` / `add_layer` / `remove_layer` / `hold_layer` references after deletion.

### Prereqs / constraints
- Works on **JSON** layout files.
- Deleting an action set shifts runtime IDs for everything that follows in the `actions` + `action_layers` ordering.
- This repo’s script handles that by computing an **old→new runtime ID mapping** and doing a two-pass update.

### Steps
1. **Identify the action set Preset_* ID**
   - Look under `controller_mappings.actions` for the key you want to delete (e.g. `Preset_1000014`).

2. **Run the deletion script**
   - `python3 delete_action_set_complete.py path/to/layout.json Preset_1000014`

3. **Review output**
   - Confirm:
     - which layers were deleted (those with `parent_set_name` = the action set)
     - which groups/presets were removed
     - which runtime IDs were remapped
   - The script creates a backup file named like:
     - `*_backup_before_delete_<preset>.json`

### Guardrails
- Never delete sets/layers “by hand” in JSON unless you also remap all affected `controller_action` runtime IDs.
- If you’re working in titles mode (`{{...}}`), consider converting to IDs first for deletion work, or be prepared to re-run `to-titles` after structural changes.

### References
- Script: `delete_action_set_complete.py`
- Runtime ID rules: `README.md`, `resources/Steam Input JSON Structure.md`

