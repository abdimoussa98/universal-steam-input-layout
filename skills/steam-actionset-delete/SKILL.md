---
name: steam-actionset-delete
description: Delete an action set from a Steam Input layout JSON with delete_action_set_complete.py, which also removes the set's layers, presets and groups and remaps every runtime ID that shifts. Use this whenever the user wants to remove, drop, or strip an action set (such as an old Gyro, Alt or Gamepad set) from a layout, or to collapse a multi-set layout towards a single set.
---

# Delete an action set safely

Rule IDs (R102 and so on) point at the [Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md#rule-tables), which holds each rule's full text, example and check.

The working layouts in `neptune/` have one action set, Base, and never switch sets (R102). So this is for older multi-set layouts (`archived/`) and for imports, not for the working layouts.

Deleting a set shifts the runtime ID of everything after it, because IDs are positional: sets first, then layers. `delete_action_set_complete.py` computes the old → new mapping and rewrites every `controller_action` in two passes.

## 1. Use a numeric file

The script rewrites numeric IDs. Run it on a file in numeric form. If the file is in `{{title}}` form, run `to-ids` first (`steam-layout-apply` skill), and run `to-titles` again afterwards.

## 2. Find the set

Look under `controller_mappings.actions` for the key to delete, such as `Preset_1000014`.

## 3. Delete it

```bash
python3 delete_action_set_complete.py path/to/layout.json Preset_1000014
```

It edits the file in place and writes `<file>_backup_before_delete_<preset>.json` next to it first.

What it removes:

- The set, from `actions`.
- Every layer whose `parent_set_name` is that set.
- The preset entries of the set and of those layers, and every group they reference.
- `group_source_bindings` in the remaining presets that point at a deleted group.

What it rewrites: the numeric ID in every `CHANGE_PRESET`, `add_layer`, `remove_layer` and `hold_layer` command.

## 4. Review the output

Check which layers and groups went and which IDs were remapped. A command that targeted a deleted layer now targets nothing useful; search for those by the old titles and remove them.

## 5. Re-check

Run the pre-flight check from the `steam-layout-prep` skill: `layer order` must be `OK` (R104) and titles unique (R105). Then finalize with the `steam-layout-apply` skill.

## Guardrails

- Never delete a set or a layer by hand in the JSON unless every affected `controller_action` ID is remapped too.
- The backup is not gitignored. Delete it, or don't commit it.

## References

- Script: `delete_action_set_complete.py`
- Runtime ID rules: `README.md`, `resources/Steam Input JSON Structure.md`
