# Runtime IDs

Steam Input assigns runtime IDs based on the **order of appearance** in the JSON:

1. **Action sets** are numbered first, starting at **1**
2. **Action layers** are numbered after all action sets

Example:
```
actions:
  Preset_1000001 (Base)     -> Runtime ID 1
  
action_layers:
  Preset_1000006 (L2)       -> Runtime ID 2
  Preset_1000007 (R2)       -> Runtime ID 3
  ...
```

**Critical:** If you delete or reorder action sets/layers, all subsequent runtime IDs shift. Always use the provided scripts to handle this automatically.

## Load-time hazard: list order and Preset numbering (found 2026-07-11)

A layout file actually carries **two implicit orderings**, and Steam can resolve runtime IDs by either one:

1. **List order** — the order blocks appear in `actions` / `action_layers` (what the GUI shows, and what this repo's scripts use)
2. **Numeric key order** — the order of the `Preset_10000XX` numeric keys (creation/renumbering order)

Normally they match. If they diverge (observed after reordering layers in the Steam GUI), a layout that works perfectly in the live editing session can come back with **silently swapped layers on the next fresh VDF load** — Steam's loader resolved the positional runtime IDs against numeric key order while the binds were saved against list order.

**Before trusting or finalizing any exported layout, verify `action_layers` keys are in ascending numeric order.** If they aren't, normalize while the file is in `{{title}}` token form: reorder `action_layers` (and the matching `preset` blocks) into numeric order and resequence the preset `id` fields, then run `to-ids`.

Full case study with pre/post snapshots: [findings/2026-07-11-layer-order-swap](../findings/2026-07-11-layer-order-swap/FINDINGS.md). The rules are R103 to R105 in the [Layer Definition of Done](../resources/Layer%20Definition%20of%20Done.md#rule-tables), and the pre-flight check is in the [steam-layout-prep](../skills/steam-layout-prep/SKILL.md) skill.
