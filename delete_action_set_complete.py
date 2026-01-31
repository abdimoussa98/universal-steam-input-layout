#!/usr/bin/env python3
"""
Steam Input Action Set Complete Deletion Script

This script deletes an entire action set and ALL its associations from a Steam controller layout JSON file.

What gets deleted:
1. The action set from the 'actions' section
2. All action layers that have parent_set_name referencing this action set
3. All preset entries (in 'preset' array) for the action set and its child layers
4. All groups referenced in those deleted preset's group_source_bindings
5. All group_source_bindings in remaining presets that reference deleted groups

What gets updated (CRITICAL):
6. All controller_action commands (CHANGE_PRESET, add_layer, remove_layer) that reference
   runtime IDs that have shifted due to the deletion

Runtime ID System:
- Runtime IDs are assigned based on ORDER of appearance in the JSON
- Action sets are numbered first (starting at 1)
- Action layers are numbered after all action sets
- Deleting an action set shifts ALL subsequent IDs down
- This script uses a two-pass replacement to safely update all IDs

Usage:
    python delete_action_set_complete.py <json_file> <preset_id>

Example:
    python delete_action_set_complete.py "neptune/universal-layout-default__hold-gyro__latest.json" "Preset_1000014"
"""

import json
import sys
import os
import re
from typing import Dict, List, Set, Any, Tuple
from collections import OrderedDict


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file, preserving key order."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{file_path}': {e}")
        sys.exit(1)


def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file with proper formatting."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent='\t', ensure_ascii=False)
        print(f"Successfully saved to '{file_path}'")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)


def calculate_runtime_ids(actions: Dict, action_layers: Dict) -> Dict[str, int]:
    """
    Calculate runtime IDs for all action sets and layers based on their order.
    
    Runtime ID assignment:
    1. Action sets are numbered first, starting at 1
    2. Action layers continue the sequence after all action sets
    
    Returns:
        Dict mapping Preset_ID (e.g., "Preset_1000001") to runtime ID (e.g., 1)
    """
    runtime_ids = {}
    position = 1
    
    # Action sets first
    for action_key in actions.keys():
        runtime_ids[action_key] = position
        position += 1
    
    # Action layers next
    for layer_key in action_layers.keys():
        runtime_ids[layer_key] = position
        position += 1
    
    return runtime_ids


def find_layers_to_delete(action_layers: Dict, target_action_set: str) -> List[str]:
    """Find all action layers that belong to the target action set."""
    layers_to_delete = []
    for layer_id, layer_data in action_layers.items():
        if layer_data.get("parent_set_name") == target_action_set:
            layers_to_delete.append(layer_id)
    return layers_to_delete


def find_groups_to_delete(presets: List[Dict], preset_names_to_delete: Set[str]) -> Set[str]:
    """
    Find all group IDs that need to be deleted based on the presets being deleted.
    These are the groups referenced in the group_source_bindings of deleted presets.
    """
    groups_to_delete = set()
    
    for preset in presets:
        if preset.get("name") in preset_names_to_delete:
            group_source_bindings = preset.get("group_source_bindings", {})
            groups_to_delete.update(group_source_bindings.keys())
    
    return groups_to_delete


def build_runtime_id_mapping(
    old_runtime_ids: Dict[str, int],
    new_runtime_ids: Dict[str, int],
    deleted_preset_ids: Set[str]
) -> Dict[int, int]:
    """
    Build a mapping of old runtime IDs to new runtime IDs for items that weren't deleted.
    
    Returns:
        Dict mapping old runtime ID to new runtime ID
    """
    id_mapping = {}
    
    # For each item that still exists, map its old ID to its new ID
    for preset_id, old_id in old_runtime_ids.items():
        if preset_id not in deleted_preset_ids:
            if preset_id in new_runtime_ids:
                new_id = new_runtime_ids[preset_id]
                if old_id != new_id:
                    id_mapping[old_id] = new_id
    
    return id_mapping


def update_controller_action_ids_two_pass(json_str: str, id_mapping: Dict[int, int]) -> str:
    """
    Update controller_action command IDs using a two-pass approach.
    
    Pass 1: Replace "controller_action CMD OLD_ID" with "controller_action CMD __TEMP_OLD_NEW__"
    Pass 2: Replace "__TEMP_OLD_NEW__" with just "NEW_ID"
    
    This ensures uniqueness and prevents cascading replacements.
    
    Commands affected:
    - controller_action CHANGE_PRESET X Y Z
    - controller_action add_layer X Y Z  
    - controller_action remove_layer X Y Z
    """
    if not id_mapping:
        return json_str
    
    print(f"\n  Updating controller_action runtime IDs...")
    print(f"  ID mapping (old -> new): {id_mapping}")
    
    result = json_str
    
    # Patterns for controller_action commands
    # Format: "controller_action CMD ID PARAM1 PARAM2, ..."
    commands = ['CHANGE_PRESET', 'add_layer', 'remove_layer']
    
    # PASS 1: Replace old IDs with unique placeholders
    # Sort by old ID descending to avoid partial replacements (e.g., 10 before 1)
    sorted_mappings = sorted(id_mapping.items(), key=lambda x: x[0], reverse=True)
    
    for old_id, new_id in sorted_mappings:
        for cmd in commands:
            # Match the command with the old ID
            # Pattern: controller_action CMD OLD_ID followed by space and more params
            pattern = rf'(controller_action {cmd} ){old_id}( \d+ \d+)'
            placeholder = f'__RUNTIME_ID_{old_id}_TO_{new_id}__'
            replacement = rf'\g<1>{placeholder}\g<2>'
            
            count_before = len(re.findall(pattern, result))
            if count_before > 0:
                result = re.sub(pattern, replacement, result)
                print(f"    Pass 1: {cmd} {old_id} -> placeholder ({count_before} occurrences)")
    
    # PASS 2: Replace placeholders with actual new IDs
    for old_id, new_id in sorted_mappings:
        placeholder = f'__RUNTIME_ID_{old_id}_TO_{new_id}__'
        if placeholder in result:
            count = result.count(placeholder)
            result = result.replace(placeholder, str(new_id))
            print(f"    Pass 2: placeholder -> {new_id} ({count} occurrences)")
    
    return result


def delete_action_set_complete(layout_data: Dict[str, Any], target_preset_id: str) -> Tuple[Dict[str, Any], Dict]:
    """
    Delete an action set and ALL its associations.
    
    Args:
        layout_data: The parsed JSON layout data
        target_preset_id: The ID of the action set to delete (e.g., "Preset_1000014")
    
    Returns:
        Tuple of (updated layout data, deletion stats)
    """
    print(f"\n{'='*60}")
    print(f"Deleting Action Set: {target_preset_id}")
    print(f"{'='*60}")
    
    stats = {
        "action_set_deleted": None,
        "layers_deleted": [],
        "presets_deleted": [],
        "groups_deleted": [],
        "group_bindings_removed": 0,
        "controller_action_ids_updated": 0
    }
    
    cm = layout_data.get("controller_mappings", {})
    actions = cm.get("actions", OrderedDict())
    action_layers = cm.get("action_layers", OrderedDict())
    presets = cm.get("preset", [])
    groups = cm.get("group", [])
    
    # Verify the target exists
    if target_preset_id not in actions:
        print(f"Error: Action set '{target_preset_id}' not found in actions.")
        print(f"Available action sets: {list(actions.keys())}")
        sys.exit(1)
    
    # STEP 1: Calculate BEFORE runtime IDs
    print(f"\n[Step 1] Calculating runtime IDs BEFORE deletion...")
    old_runtime_ids = calculate_runtime_ids(actions, action_layers)
    
    target_title = actions[target_preset_id].get("title", "Unknown")
    target_runtime_id = old_runtime_ids[target_preset_id]
    print(f"  Target: {target_preset_id} ('{target_title}') - Runtime ID: {target_runtime_id}")
    
    # STEP 2: Find all layers that belong to this action set
    print(f"\n[Step 2] Finding action layers with parent_set_name = '{target_preset_id}'...")
    layers_to_delete = find_layers_to_delete(action_layers, target_preset_id)
    print(f"  Found {len(layers_to_delete)} layers to delete:")
    for layer_id in layers_to_delete:
        layer_title = action_layers[layer_id].get("title", "Unknown")
        layer_runtime_id = old_runtime_ids[layer_id]
        print(f"    - {layer_id} ('{layer_title}') - Runtime ID: {layer_runtime_id}")
    
    # Collect all preset IDs to delete (action set + its layers)
    preset_ids_to_delete = {target_preset_id} | set(layers_to_delete)
    
    # STEP 3: Find groups to delete
    print(f"\n[Step 3] Finding groups referenced by deleted presets...")
    groups_to_delete = find_groups_to_delete(presets, preset_ids_to_delete)
    print(f"  Found {len(groups_to_delete)} groups to delete: {sorted(groups_to_delete, key=int)}")
    
    # STEP 4: Delete from actions
    print(f"\n[Step 4] Deleting action set from 'actions' block...")
    deleted_action = actions.pop(target_preset_id)
    stats["action_set_deleted"] = {"id": target_preset_id, "title": deleted_action.get("title")}
    print(f"  Deleted: {target_preset_id} ('{deleted_action.get('title')}')")
    
    # STEP 5: Delete action layers
    print(f"\n[Step 5] Deleting action layers from 'action_layers' block...")
    for layer_id in layers_to_delete:
        deleted_layer = action_layers.pop(layer_id)
        stats["layers_deleted"].append({"id": layer_id, "title": deleted_layer.get("title")})
        print(f"  Deleted: {layer_id} ('{deleted_layer.get('title')}')")
    
    # STEP 6: Calculate AFTER runtime IDs
    print(f"\n[Step 6] Calculating runtime IDs AFTER deletion...")
    new_runtime_ids = calculate_runtime_ids(actions, action_layers)
    
    # Build the ID mapping for controller_action updates
    id_mapping = build_runtime_id_mapping(old_runtime_ids, new_runtime_ids, preset_ids_to_delete)
    print(f"  Runtime IDs that need updating: {len(id_mapping)}")
    
    # STEP 7: Delete preset entries
    print(f"\n[Step 7] Deleting preset entries from 'preset' array...")
    presets_kept = []
    for preset in presets:
        preset_name = preset.get("name")
        if preset_name in preset_ids_to_delete:
            stats["presets_deleted"].append(preset_name)
            print(f"  Deleted preset: {preset_name} (id: {preset.get('id')})")
        else:
            presets_kept.append(preset)
    cm["preset"] = presets_kept
    
    # STEP 8: Delete groups
    print(f"\n[Step 8] Deleting groups from 'group' array...")
    groups_kept = []
    for group in groups:
        group_id = group.get("id")
        if group_id in groups_to_delete:
            stats["groups_deleted"].append(group_id)
            print(f"  Deleted group: {group_id} (mode: {group.get('mode', 'Unknown')})")
        else:
            groups_kept.append(group)
    cm["group"] = groups_kept
    
    # STEP 9: Remove group_source_bindings that reference deleted groups
    print(f"\n[Step 9] Removing orphaned group_source_bindings from remaining presets...")
    for preset in cm["preset"]:
        gsb = preset.get("group_source_bindings", {})
        keys_to_remove = [k for k in gsb.keys() if k in groups_to_delete]
        for key in keys_to_remove:
            gsb.pop(key)
            stats["group_bindings_removed"] += 1
            print(f"  Removed binding for group {key} from preset {preset.get('name')}")
    
    # STEP 10: Renumber preset IDs to maintain sequential order
    print(f"\n[Step 10] Renumbering preset IDs to maintain sequential order...")
    for i, preset in enumerate(cm["preset"]):
        old_preset_id = preset.get("id")
        preset["id"] = str(i)
        if old_preset_id != str(i):
            print(f"  Preset {preset.get('name')}: id {old_preset_id} -> {i}")
    
    # STEP 11: Update controller_action IDs (this needs to be done on the string representation)
    # We'll return the id_mapping for the caller to handle
    
    return layout_data, {"stats": stats, "id_mapping": id_mapping, "old_runtime_ids": old_runtime_ids, "new_runtime_ids": new_runtime_ids}


def main():
    """Main function to handle command line arguments and execute the deletion."""
    if len(sys.argv) != 3:
        print("Usage: python delete_action_set_complete.py <json_file> <preset_id>")
        print("\nExample:")
        print("  python delete_action_set_complete.py 'neptune/universal-layout-default__hold-gyro__latest.json' 'Preset_1000014'")
        print("\nThis will delete:")
        print("  - The action set (Preset_1000014)")
        print("  - All action layers with parent_set_name = Preset_1000014")
        print("  - All preset entries for the above")
        print("  - All groups referenced by those presets")
        print("  - Update all controller_action runtime IDs")
        sys.exit(1)
    
    json_file = sys.argv[1]
    preset_id = sys.argv[2]
    
    # Validate file exists
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' does not exist.")
        sys.exit(1)
    
    # Load the JSON file
    print(f"Loading layout file: {json_file}")
    layout_data = load_json_file(json_file)
    
    # Validate the layout structure
    if "controller_mappings" not in layout_data:
        print("Error: Invalid layout file. Expected 'controller_mappings' at root level.")
        sys.exit(1)
    
    # Create backup
    backup_file = json_file.replace('.json', f'_backup_before_delete_{preset_id}.json')
    print(f"Creating backup: {backup_file}")
    save_json_file(backup_file, layout_data)
    
    # Perform the deletion
    updated_layout, deletion_info = delete_action_set_complete(layout_data, preset_id)
    
    # Convert to string for ID replacement
    print(f"\n[Step 11] Updating controller_action runtime IDs (two-pass)...")
    json_str = json.dumps(updated_layout, indent='\t', ensure_ascii=False)
    
    # Update controller_action IDs
    id_mapping = deletion_info["id_mapping"]
    if id_mapping:
        json_str = update_controller_action_ids_two_pass(json_str, id_mapping)
    else:
        print("  No runtime ID updates needed.")
    
    # Parse back to dict and save
    final_layout = json.loads(json_str, object_pairs_hook=OrderedDict)
    
    # Save updated layout
    print(f"\n[Step 12] Saving updated layout...")
    save_json_file(json_file, final_layout)
    
    # Print summary
    stats = deletion_info["stats"]
    print(f"\n{'='*60}")
    print("DELETION SUMMARY")
    print(f"{'='*60}")
    print(f"Action Set Deleted: {stats['action_set_deleted']}")
    print(f"Layers Deleted: {len(stats['layers_deleted'])}")
    for layer in stats['layers_deleted']:
        print(f"  - {layer['id']} ('{layer['title']}')")
    print(f"Presets Deleted: {len(stats['presets_deleted'])}")
    print(f"Groups Deleted: {len(stats['groups_deleted'])}")
    print(f"Group Bindings Removed: {stats['group_bindings_removed']}")
    print(f"Runtime IDs Remapped: {len(id_mapping)}")
    if id_mapping:
        print("  Old -> New:")
        for old_id, new_id in sorted(id_mapping.items()):
            print(f"    {old_id} -> {new_id}")
    
    print(f"\nBackup saved to: {backup_file}")
    print(f"Updated layout saved to: {json_file}")
    print(f"\nOperation completed successfully!")


if __name__ == "__main__":
    main()
