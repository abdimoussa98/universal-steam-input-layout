# Universal Steam Input Layout

Custom Steam Input controller layouts with advanced layer management.

## Installation

Drop layout files in `/home/deck/.steam/steam/controller_base/templates/`

---

## Scripts

This repository includes several Python scripts for managing Steam Input layout JSON files.

### 1. `duplicate_layer.py` - Duplicate Action Layers

Duplicates an action layer along with all its children relationships (groups, bindings, etc.). The duplicated layer is added to the **end** of `action_layers` to preserve runtime ID ordering.

**Use Cases:**
- Create a variant of an existing layer with different bindings
- Clone a complex layer as a starting point for a new one
- Back up a layer before making experimental changes

**Usage:**

```bash
# List all available layers in a layout
python3 duplicate_layer.py layout.json --list

# Duplicate a layer (auto-generates title with " (Copy)" suffix)
python3 duplicate_layer.py layout.json Preset_1000006

# Duplicate with a custom title
python3 duplicate_layer.py layout.json Preset_1000006 "My Custom Layer"

# Output to a different file instead of modifying in-place
python3 duplicate_layer.py layout.json Preset_1000006 --output new_layout.json

# Skip creating a backup file
python3 duplicate_layer.py layout.json Preset_1000006 --no-backup
```

**What gets duplicated:**
- The layer definition in `action_layers`
- All groups referenced in `group_source_bindings`
- The preset entry with updated group references

**Important:** The new layer gets a new runtime ID (appended to the end), so existing `controller_action` commands remain unaffected.

---

### 2. `delete_action_set_complete.py` - Delete Action Sets

Deletes an entire action set and **all** its associations from a layout file. This includes child layers, presets, groups, and automatically updates all `controller_action` runtime ID references.

**Use Cases:**
- Remove an unused action set (e.g., "Gyro" or "Gamepad" mode)
- Clean up a layout by removing experimental sets
- Reduce layout complexity

**Usage:**

```bash
python3 delete_action_set_complete.py layout.json Preset_1000014
```

**What gets deleted:**
1. The action set from `actions`
2. All action layers with `parent_set_name` referencing this set
3. All preset entries for the set and its child layers
4. All groups referenced by those presets
5. All `group_source_bindings` in remaining presets that reference deleted groups

**What gets updated:**
- All `controller_action` commands (`CHANGE_PRESET`, `add_layer`, `remove_layer`, `hold_layer`) that reference runtime IDs affected by the deletion

**Warning:** Deleting an action set shifts all subsequent runtime IDs down. The script handles this automatically using a two-pass replacement to prevent cascading issues.

---

### 3. `convert_runtime_ids.py` - Convert Runtime IDs to Titles

Converts between numeric runtime IDs and human-readable titles in `controller_action` commands. Makes layouts easier to read and edit manually.

**Use Cases:**
- Make a layout human-readable for manual editing
- Debug which layers are being activated by `controller_action` commands
- Convert back to numeric IDs before using the layout in Steam

**Usage:**

```bash
# Convert numeric IDs to readable titles
# e.g., "controller_action add_layer 5 0 0" -> "controller_action add_layer {{L2}} 0 0"
python3 convert_runtime_ids.py to-titles layout.json

# Convert titles back to numeric IDs
# e.g., "controller_action add_layer {{L2}} 0 0" -> "controller_action add_layer 5 0 0"
python3 convert_runtime_ids.py to-ids layout.json

# Output to a different file instead of modifying in-place
python3 convert_runtime_ids.py to-titles layout.json --output readable_layout.json
```

**Title Format:**
- Action sets: `{{Base}}`, `{{Gyro}}`
- Action layers: `{{Base::L2}}`, `{{Base::RST: Temporary Gyro}}`

The `Parent::Title` format for layers ensures unique identification when multiple sets have layers with the same name.

---

## Runtime ID System

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

---

## Resources

See the `resources/` folder for additional documentation:
- `Steam Input JSON Structure.md` - Detailed explanation of the JSON format
- `Action Sets.md` - List of action set IDs
- `Layer Reverse Lookup.md` - Complete mapping of layer IDs to names

---

## File Formats

- `.json` - Human-readable format for editing with these scripts
- `.vdf` - Valve Data Format used by Steam (convert using external tools)