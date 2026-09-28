## Skill: Finalize a Steam Input layout (titles → runtime IDs)

### When to use
- You’ve finished editing a “readable” layout that contains `{{...}}` title tokens.
- You need to produce a layout that Steam will load correctly (numeric runtime IDs in `controller_action`).

### Prereqs / constraints
- Input must be valid JSON layout format (converted from VDF externally if needed).
- The file must still contain consistent `controller_mappings.actions` and `controller_mappings.action_layers` blocks; runtime IDs are derived from their order.

### Steps
0. **Enforce the command budget before finalizing**
   - `python3 audit_command_budget.py path/to/layout.json` must exit 0. At most three GUI command entries per input, counted across activator types/list elements; binding-array subcommands may exceed three. All groups are scanned and disabled banks checked separately. Follow `steam-binding-order` to consolidate violations without deleting required cleanup.

1. **Convert titles back to IDs (in place)**
   - `python3 convert_runtime_ids.py to-ids path/to/layout.json`

2. **Or write to a new file**
   - `python3 convert_runtime_ids.py to-ids path/to/layout_readable.json --output path/to/layout_final.json`

3. **Sanity check for unresolved tokens**
   - Ensure there are no remaining `{{...}}` tokens in `controller_action` strings after conversion.
   - If the script warns it can’t find a runtime ID for some `{{Title}}`, it means the title no longer matches anything in `actions`/`action_layers`.

### Guardrails
- If you renamed an action set/layer title, you may need to re-run `to-titles` first (to regenerate tokens) before making sweeping edits.
- Avoid manual edits that change the order of `actions` / `action_layers` unless you understand the runtime ID implications.
- **Before running `to-ids`, confirm `action_layers` keys are in ascending `Preset_` numeric order.** If list order diverges from numeric key order, Steam's loader may resolve the generated runtime IDs against numeric key order and silently swap layers on a fresh load. Normalize the order first (reorder layers + matching `preset` blocks, resequence preset `id` fields) while still in `{{title}}` form. See `findings/2026-07-11-layer-order-swap/FINDINGS.md`.
- **Duplicate titles break `to-ids`**: layers sharing a title (e.g. two named `DEPRECATED`) all resolve to the last one. Rename them uniquely before round-tripping.

### References
- Converter script: `convert_runtime_ids.py`
- Runtime ID ordering rules: `README.md`, `resources/Steam Input JSON Structure.md`
