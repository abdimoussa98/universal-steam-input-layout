## Skill: Avoid layer-management bugs caused by binding array execution order

### When to use
- You’re editing a group binding where `"binding"` is an array of multiple `controller_action ...` commands.
- You’re seeing surprising behavior where a layer is added/removed “in the wrong order”.

### Key rule (critical)
- In Steam Input JSON bindings, when `"binding"` is an array, the commands execute **from bottom to top**.
- **Maximum three GUI command entries per input.** Count every activator object across all types; a list of six chords plus one Regular Press is seven entries. Subcommands in a `binding` array share one entry and may exceed three.
- Consolidate identical chord outputs/settings using a multi-button **Any** selector, preserving timing and interruption behavior. Legacy `chord_button` IDs are not masks; modern mask selectors are not exclusive to Triton.
- Run `python3 audit_command_budget.py path/to/layout.json` after edits; it scans every group, including inactive/unreferenced groups, and checks disabled banks separately. Do not hide overflow in disabled entries.
- Counting details and selector rules: `resources/Steam Input JSON Structure.md`, section **Command Entry Budget**.

### Practical checklist for layer cleanup + apply
- Put cleanup `remove_layer` operations **lower in the array** so they execute **earlier**.
- Put the final “desired state” operation (often `add_layer` or `hold_layer`) **higher in the array** so it executes **last**.
- If you need “remove then add” semantics, ensure the `add_layer` is placed **above** removals in the array.

### Guardrails
- After editing these arrays, re-run `convert_runtime_ids.py to-titles` if you need to re-verify targets by name.
- Be careful mixing `CHANGE_PRESET` with add/remove layer commands; mode switches can invalidate assumptions about active layers.

### References
- Explanation and example: `resources/Steam Input JSON Structure.md`
- Title↔ID conversion helper: `convert_runtime_ids.py`
