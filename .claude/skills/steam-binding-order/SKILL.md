---
name: steam-binding-order
description: Rules for Steam Input `binding` arrays that hold several controller_action commands (add_layer, remove_layer, hold_layer). The array executes bottom to top, so cleanup removals go lower and the final add goes on top. Use this whenever you write, reorder, copy, or review a multi-command binding in a layout JSON, or when a layer ends up added or removed in the wrong order, gets stuck on, or disappears unexpectedly.
---

# Binding array execution order

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
