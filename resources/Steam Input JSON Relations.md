 # Steam Input JSON relations (VDF -> JSON)
 
 This note documents how key sections in the Steam Input JSON layout relate to each other. The JSON is a conversion from Valve KeyValues (VDF) and follows the same conceptual model as Steam Input action sets and action set layers.
 
 References:
 - Steam Input action sets and layers overview: https://partner.steamgames.com/doc/features/steam_controller/iga_file
 - Action set layers behavior (overlay/stacking): https://partner.steamgames.com/doc/features/steam_controller/action_set_layers
 
 ## Key relations in this layout
 
 ### Action sets (`actions`) -> presets (`preset`)
 
 - The `actions` block defines action sets keyed by a string ID (e.g., `Preset_1000001`) and includes a human-readable `title`.
 - Each action set has a corresponding entry in the `preset` list with `name` matching the action set key. That preset entry carries the default group bindings for that action set.
 
 Example action set definition:
 ```16:32:neptune/universal-layout-default__hold-gyro__latest.json
 		"actions": {
 			"Preset_1000001": {
 				"title": "Base",
 				"legacy_set": "1"
 			},
 			"Preset_1000014": {
 				"title": "Gyro",
 				"legacy_set": "1"
 			},
 			// ...
 		},
 ```
 
 Matching preset entry (same `name`):
 ```41307:41323:neptune/universal-layout-default__hold-gyro__latest.json
 		"preset": [
 			{
 				"id": "0",
 				"name": "Preset_1000001",
 				"group_source_bindings": {
 					"10": "switch active",
 					"11": "button_diamond active",
 					// ...
 				}
 			},
 ```
 
 ### Action layers (`action_layers`) -> parent action set
 
 - The `action_layers` block defines action layers.
 - Each action layer includes `parent_set_name`, which references the action set key in `actions`.
 - This means every action layer is explicitly associated with a single action set.
 
 Example action layer (note `parent_set_name`):
 ```34:57:neptune/universal-layout-default__hold-gyro__latest.json
 		"action_layers": {
 			"Preset_1000006": {
 				"title": "L2",
 				"legacy_set": "1",
 				"set_layer": "1",
 				"parent_set_name": "Preset_1000001"
 			},
 			"Preset_1000007": {
 				"title": "R2",
 				"legacy_set": "1",
 				"set_layer": "1",
 				"parent_set_name": "Preset_1000001"
 			},
 ```
 
 Steam Input context: action set layers are overlays applied on top of an active action set, rather than a full replacement. They can add/override bindings and are stacked in order. (Steamworks docs: action set layers.)
 
 ### Action layers -> presets (`preset`)
 
 - Action layers also have corresponding entries in the `preset` list.
 - These entries contain the layer-specific group bindings that are overlaid on top of the base action set bindings.
 
 Example (layer preset):
 ```41396:41406:neptune/universal-layout-default__hold-gyro__latest.json
 			{
 				"id": "4",
 				"name": "Preset_1000006",
 				"group_source_bindings": {
 					"24": "left_trigger inactive",
 					// ...
 				}
 			},
 ```
 
 ### Preset `group_source_bindings` -> `group` list
 
 - Each `preset` has a `group_source_bindings` map whose keys are group IDs (as strings).
 - Those IDs correspond to entries in the `group` list (each `group` object has an `id`).
 - The `group_source_bindings` values describe whether that input group is active/inactive and any modeshift flags.
 
 Example `group` entry:
 ```32892:32901:neptune/universal-layout-default__hold-gyro__latest.json
 			{
 				"id": "10",
 				"mode": "switches",
 				"name": "",
 				"description": "",
 				"inputs": {
 					"button_escape": {
 						"activators": {
 ```
 
 Matching `group_source_bindings` key (same ID `10`):
 ```41309:41316:neptune/universal-layout-default__hold-gyro__latest.json
 			{
 				"id": "0",
 				"name": "Preset_1000001",
 				"group_source_bindings": {
 					"10": "switch active",
 					"11": "button_diamond active",
 ```
 
 ## Practical interpretation
 
 - `actions` is the canonical list of action sets (IDs + titles).
 - `action_layers` extends those action sets and points to the base set via `parent_set_name`.
 - `preset` is the binding snapshot list. It includes entries for every action set and every action layer.
 - When a layer is applied, its preset bindings are overlaid on top of the active action set preset, consistent with Steam Input layer behavior.
 - `group` is the shared list of input groups. Preset bindings reference group IDs, which makes the binding list reusable across sets/layers.
 
## Runtime IDs for controller_action Commands (CRITICAL)

Steam Input assigns **runtime IDs** to action sets and layers based on their **order of appearance** in the JSON. These numeric IDs are used in `controller_action` binding commands and are **NOT** the same as the `Preset_*` string identifiers.

### ID Assignment Order

1. All **action sets** from `actions` block are numbered first, starting at **1**
2. All **action layers** from `action_layers` block are numbered next, continuing the sequence

### Example ID Calculation

```json
"actions": {
  "Preset_1000001": { "title": "Base" },      // Runtime ID: 1
  "Preset_1000014": { "title": "Gyro" },      // Runtime ID: 2
  "Preset_1000021": { "title": "Steering" },  // Runtime ID: 3
  "Preset_1000028": { "title": "Gamepad" }    // Runtime ID: 4
},
"action_layers": {
  "Preset_1000006": { "title": "L2", ... },   // Runtime ID: 5 (first layer)
  "Preset_1000007": { "title": "R2", ... },   // Runtime ID: 6
  "Preset_1000008": { "title": "L1: Modifier 0", ... }, // Runtime ID: 7
  // ...
}
```

### controller_action Command Examples

**Switch to Base action set (ID 1):**
```
binding: "controller_action CHANGE_PRESET 1 1 1, , "
                                          ↑
                            Runtime ID 1 = Preset_1000001 (Base)
```

**Remove L2 layer (ID 5):**
```
binding: "controller_action remove_layer 5 0 0, , "
                                         ↑
                         Runtime ID 5 = Preset_1000006 (L2 Layer)
```

**Add layer with ID 32:**
```
binding: "controller_action add_layer 32 0 0, , "
                                      ↑↑
              Runtime ID 32 = 32nd item in combined actions + action_layers order
```

**Hold layer while pressed (ID 13):**
```
binding: "controller_action hold_layer 13 0 0, , "
                                       ↑↑
               Runtime ID 13 = Layer active only while button is held
```

### ⚠️ CRITICAL: ID Shift on Deletion

**When you delete an action set or action layer, ALL runtime IDs for subsequent items shift down.**

**Before deleting Gyro (ID 2):**
```
1: Base (Preset_1000001)
2: Gyro (Preset_1000014)
3: Alt (Preset_1000021)
4: Gamepad (Preset_1000028)
5: L2 Layer (Preset_1000006)
6: R2 Layer (Preset_1000007)
```

**After deleting Gyro:**
```
1: Base (Preset_1000001)
2: Alt (Preset_1000021)       ← WAS ID 3
3: Gamepad (Preset_1000028)   ← WAS ID 4
4: L2 Layer (Preset_1000006)  ← WAS ID 5
5: R2 Layer (Preset_1000007)  ← WAS ID 6
```

**Consequence:** Any `controller_action` binding that referenced ID 5 (L2 Layer) would now incorrectly reference R2 Layer. **All controller_action bindings must be updated after deletion.**

### Runtime ID Calculation Algorithm

```python
def calculate_runtime_id(preset_name, actions_dict, action_layers_dict):
    """Calculate the runtime ID for a given Preset_* identifier."""
    position = 1
    
    # Check action sets first
    for action_key in actions_dict.keys():
        if action_key == preset_name:
            return position
        position += 1
    
    # Check action layers next
    for layer_key in action_layers_dict.keys():
        if layer_key == preset_name:
            return position
        position += 1
    
    return None  # Not found
```

## Notes for agent usage

- Always map set/layer IDs through the `actions` and `action_layers` objects first to find the human-readable `title`.
- Use `preset[].name` to locate the binding definition for an action set or layer.
- Use `group_source_bindings` keys to resolve which `group` entries are active and then inspect those `group` objects for actual input bindings.
- **CRITICAL:** When working with `controller_action` commands, calculate runtime IDs dynamically by counting position in the combined `actions` + `action_layers` ordered list.
- **CRITICAL:** After deleting any action set or layer, all `controller_action` binding commands with IDs ≥ the deleted position must be recalculated and updated.
- The runtime ID system is **order-dependent** - the sequence of items in the JSON directly determines the ID values.
