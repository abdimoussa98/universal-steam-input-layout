## Skill: Remap runtime IDs with an explicit mapping (two-pass replacement)

### When to use
- You have a known “old runtime ID → new runtime ID” mapping and need to rewrite `controller_action add_layer/remove_layer/hold_layer` numeric IDs at scale.
- You want a safe replacement strategy that avoids cascading replacements (e.g., `1` accidentally changing inside `10`).

### Prereqs / constraints
- This is **not** VDF ↔ JSON conversion; it operates on JSON text.
- You must have a mapping JSON that contains `old_id` and `new_id` values (see the repo’s example mapping).

### Recommended script
Use the flexible CLI script so you can choose input/output and do a dry run:
- `id_replacement/replace_layer_ids_flexible.py`

### Steps
1. **Dry run first**
   - `python3 id_replacement/replace_layer_ids_flexible.py -i path/to/layout.json -m id_replacement/old_to_new_ids.json --dry-run`

2. **Write an updated file**
   - `python3 id_replacement/replace_layer_ids_flexible.py -i path/to/layout.json -m id_replacement/old_to_new_ids.json -o path/to/layout_updated.json`

3. **Review diffs**
   - Confirm the only intended changes are within `controller_action add_layer/remove_layer/hold_layer ...` numeric arguments.

### How it works (guardrail reasoning)
- Pass 1 rewrites `OLD` → `OLD_NEW` (unique placeholder per ID)
- Pass 2 rewrites `OLD_NEW` → `NEW`
- This prevents accidental double-application and “partial match” problems.

### Guardrails
- This remaps numeric IDs, but it can’t validate semantic correctness (you must ensure the mapping matches the current layout’s ordering).
- Prefer the title-token workflow (`convert_runtime_ids.py to-titles`) for day-to-day editing. Use remap scripts when you’re doing a deliberate migration.

### References
- Script: `id_replacement/replace_layer_ids_flexible.py`
- Example mapping file: `id_replacement/old_to_new_ids.json`
- Background: `id_replacement/README_replace_layer_ids.md`

