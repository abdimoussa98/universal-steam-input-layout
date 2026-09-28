---
name: steam-binding-order
description: Enforce the maximum of three GUI command entries per input and bottom-to-top execution of binding subcommand arrays. Use when writing, copying, consolidating, or reviewing activators, chords, and layer cleanup bindings in this repo.
---

# Binding array execution order

## Maximum three command entries per input

This is a hard requirement from the layout author. Count **activator objects across all
activation types on one input**, not the strings in `bindings.binding`:

- A single `Full_Press` object counts as one command entry.
- A `chord` list of six objects counts as six entries. Adding one `Full_Press` makes seven, even though `activators` has only two keys.
- A `binding` array is subcommands within one entry. Arrays with more than three subcommands are allowed; preserve their execution order.
- Count each `group.inputs.<input>` separately, including edge, touch, click, and trigger pulls. Scan inactive groups, mode-shift groups, and unreferenced groups too. Check disabled activator banks separately before restoring them.

Run `python3 audit_command_budget.py path/to/layout.json` after edits. A nonzero exit
means the file is not ready to finalize (1 = over budget, 2 = malformed input).

To consolidate identical chord outputs/settings, use one multi-button chord with **Any**
semantics rather than one command per possible button. Modern selectors use
`gyro_ratchet_button_mask` and `gyro_ratchet_button_requireany_or_all`; legacy
`chord_button` IDs are not bitmasks. Keep different outputs, delays, repeat settings,
and interruption behavior distinct. Do not merge independent conditions into an
unconditional subcommand array or move overflow into disabled entries.

See [the counting rule and chord format](../../../resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget)
and [the Neptune consolidation plan](../../../plans/2026-09-27-neptune-command-budget.md).

## The rule

When `"binding"` is an array, the commands execute **from bottom to top**. The top entry runs last, so it decides the final state.

Example (comments are only for illustration; JSON doesn't allow them):

```json
"binding": [
  "controller_action add_layer {{Base::Turning Ramp Up 0}} 0 0, , ",      // runs LAST
  "controller_action remove_layer {{Base::Turning Ramp Up 1}} 0 0, , ",
  "controller_action remove_layer {{Base::Gyro Off Ramp Up}} 0 0, , "     // runs FIRST
]
```

## Checklist

- Put cleanup `remove_layer` commands **below** the main action so they run first.
- Put the command that sets the final state (usually `add_layer` or `hold_layer`) **above** the removals so it runs last.
- For "remove, then add" semantics, the add goes **above** the removal.

## Guardrails

- Edit these arrays in `{{title}}` form so every target is readable. Use the `steam-layout-prep` skill to convert first.
- After copying binds from another layer, re-read every target title. A copy-paste retarget is the most common bug found in audits. For example, RTP: Mouse Buttons' center release removes LTP: Arrow Keys instead of itself (see `findings/2026-09-27-exploratory-layout-audit/AUDIT.md`).
- When you add a new layer, update the cleanup lists too. Every bind that clears related layers, such as the ramp-up and modifier cleanups, needs a matching `remove_layer`.
- `CHANGE_PRESET` switches the whole action set and invalidates assumptions about which layers are active. The current layouts are single-set, so it only matters for multi-set files in `archived/`.

## References

- Explanation and example: `resources/Steam Input JSON Structure.md` (section "Binding Execution Order")
- Title ↔ ID conversion: `convert_runtime_ids.py`
