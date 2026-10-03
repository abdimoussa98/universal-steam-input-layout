---
name: steam-runtimeid-remap
description: Rewrite numeric runtime IDs in a Steam Input layout JSON from an explicit old-to-new mapping, with the two-pass replace_layer_ids_flexible.py. Use this when a numeric layout's layers were reordered, inserted or deleted without remapping and its `controller_action add_layer 32 0 0`-style IDs no longer match list order, when the user has a known old→new ID table to apply, or when migrating a layout between two layer orders.
---

# Remap runtime IDs from an explicit mapping

Rule IDs (R104 and so on) point at the [Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md#rule-tables), which holds each rule's full text, example and check.

**Prefer title tokens.** Day-to-day editing happens in `{{Base::Title}}` form (R105), where nothing needs remapping: see the `steam-layout-prep` skill. Use this skill only for a deliberate migration, or to repair a numeric file whose IDs no longer match its list order (R104). On such a file `to-titles` would mislabel every bind, so remap first.

## 1. Write the mapping

A JSON object with one entry per set or layer, each with `old_id` and `new_id`:

```json
{ "Preset_1000006": { "title": "L2", "old_id": 5, "new_id": 6 } }
```

`tools/id_replacement/old_to_new_ids.json` is an example, from the April migration. It does not describe the current layouts.

## 2. Dry run

```bash
python3 tools/id_replacement/replace_layer_ids_flexible.py -i path/to/layout.json -m path/to/mapping.json --dry-run
```

## 3. Write the result

```bash
python3 tools/id_replacement/replace_layer_ids_flexible.py -i path/to/layout.json -m path/to/mapping.json -o path/to/layout_updated.json
```

## 4. Review the diff

The only changes should be the numeric argument of `controller_action add_layer`, `remove_layer` and `hold_layer` commands. `CHANGE_PRESET` is not rewritten.

## How the two passes work

- Pass 1 rewrites each `OLD` to `OLD_NEW`, a placeholder no other ID can match.
- Pass 2 rewrites each `OLD_NEW` to `NEW`.

Without the placeholder, mapping 5 → 6 and 6 → 7 would turn every 5 into 7.

## Guardrails

- The script can't tell whether the mapping is right. Check it against the file's current `action_layers` order before running.
- Run the pre-flight check from the `steam-layout-prep` skill afterwards, then `to-titles` to read the result.

## References

- Script: `tools/id_replacement/replace_layer_ids_flexible.py`
- Background: `tools/id_replacement/README_replace_layer_ids.md`
