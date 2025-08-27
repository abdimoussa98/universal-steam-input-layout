#!/usr/bin/env python3
"""
Steam Controller Layout Actions Preset Deletion Script

This script deletes an entire actions preset and all its associations from a Steam controller layout JSON file.
It removes:
1. The preset from the 'actions' section
2. All action layers that reference the preset as parent_set_name
3. The preset configuration from the 'preset' section
4. All groups referenced in the preset's group_source_bindings
5. All group_source_bindings that reference the deleted groups

Usage:
    python delete_action_set.py <json_file> <preset_id>

Example:
    python delete_action_set.py "neptune/universal-layout-default  hold-gyro  latest.json" "Preset_1000014"
"""

import json
import sys
import os
from typing import Dict, List, Set, Any


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
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
        print(f"Successfully saved updated layout to '{file_path}'")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)


def find_groups_to_delete(preset_data: Dict[str, Any], preset_name: str) -> Set[str]:
    """Find all group IDs that need to be deleted based on the preset's group_source_bindings."""
    groups_to_delete = set()
    
    # Find the preset in the preset array
    if "controller_mappings" in preset_data and "preset" in preset_data["controller_mappings"]:
        for preset in preset_data["controller_mappings"]["preset"]:
            if preset.get("name") == preset_name:
                # Get all group IDs from group_source_bindings
                group_source_bindings = preset.get("group_source_bindings", {})
                groups_to_delete.update(group_source_bindings.keys())
                break
    
    return groups_to_delete


def delete_action_set(layout_data: Dict[str, Any], preset_id: str) -> Dict[str, Any]:
    """
    Delete an entire actions preset and all its associations.
    
    Args:
        layout_data: The parsed JSON layout data
        preset_id: The ID of the preset to delete (e.g., "Preset_1000014")
    
    Returns:
        Updated layout data with the preset and all associations removed
    """
    print(f"Deleting actions preset: {preset_id}")
    
    # Create a copy to avoid modifying the original
    updated_data = layout_data.copy()
    
    # 1. Delete the preset from the 'actions' section
    if "controller_mappings" in updated_data and "actions" in updated_data["controller_mappings"]:
        if preset_id in updated_data["controller_mappings"]["actions"]:
            deleted_preset = updated_data["controller_mappings"]["actions"].pop(preset_id)
            print(f"  - Deleted preset '{preset_id}' from actions section")
            print(f"    Title: {deleted_preset.get('title', 'Unknown')}")
        else:
            print(f"  - Warning: Preset '{preset_id}' not found in actions section")
    else:
        print(f"  - Warning: Actions section not found in controller_mappings")
    
    # 2. Find and delete all action layers that reference this preset
    layers_to_delete = []
    if "controller_mappings" in updated_data and "action_layers" in updated_data["controller_mappings"]:
        for layer_id, layer_data in updated_data["controller_mappings"]["action_layers"].items():
            if layer_data.get("parent_set_name") == preset_id:
                layers_to_delete.append(layer_id)
        
        for layer_id in layers_to_delete:
            deleted_layer = updated_data["controller_mappings"]["action_layers"].pop(layer_id)
            print(f"  - Deleted action layer '{layer_id}' (parent: {preset_id})")
            print(f"    Title: {deleted_layer.get('title', 'Unknown')}")
    else:
        print(f"  - Warning: Action layers section not found in controller_mappings")
    
    # 3. Find and delete the preset configuration from the 'preset' section
    preset_index_to_delete = None
    if "controller_mappings" in updated_data and "preset" in updated_data["controller_mappings"]:
        for i, preset in enumerate(updated_data["controller_mappings"]["preset"]):
            if preset.get("name") == preset_id:
                preset_index_to_delete = i
                break
        
        if preset_index_to_delete is not None:
            deleted_preset_config = updated_data["controller_mappings"]["preset"].pop(preset_index_to_delete)
            print(f"  - Deleted preset configuration '{preset_id}' from preset section")
            print(f"    ID: {deleted_preset_config.get('id', 'Unknown')}")
        else:
            print(f"  - Warning: Preset configuration '{preset_id}' not found in preset section")
    else:
        print(f"  - Warning: Preset section not found in controller_mappings")
    
    # 4. Find groups to delete based on the preset's group_source_bindings
    groups_to_delete = find_groups_to_delete(updated_data, preset_id)
    
    # 5. Delete groups and update group_source_bindings
    if groups_to_delete:
        print(f"  - Found {len(groups_to_delete)} groups to delete: {sorted(groups_to_delete)}")
        
        # Delete groups from the group array
        if "controller_mappings" in updated_data and "group" in updated_data["controller_mappings"]:
            groups_kept = []
            for group in updated_data["controller_mappings"]["group"]:
                if group.get("id") not in groups_to_delete:
                    groups_kept.append(group)
                else:
                    print(f"    - Deleted group {group.get('id')} ({group.get('mode', 'Unknown')})")
            
            updated_data["controller_mappings"]["group"] = groups_kept
        
        # Remove group_source_bindings that reference deleted groups
        if "controller_mappings" in updated_data and "preset" in updated_data["controller_mappings"]:
            for preset in updated_data["controller_mappings"]["preset"]:
                group_source_bindings = preset.get("group_source_bindings", {})
                bindings_to_remove = []
                
                for group_id in group_source_bindings:
                    if group_id in groups_to_delete:
                        bindings_to_remove.append(group_id)
                
                for group_id in bindings_to_remove:
                    group_source_bindings.pop(group_id)
                    print(f"    - Removed group_source_binding for group {group_id} from preset {preset.get('name')}")
    
    # 6. Update preset IDs to maintain sequential numbering
    if "controller_mappings" in updated_data and "preset" in updated_data["controller_mappings"]:
        for i, preset in enumerate(updated_data["controller_mappings"]["preset"]):
            preset["id"] = str(i)
    
    print(f"Successfully deleted actions preset '{preset_id}' and all associations")
    return updated_data


def main():
    """Main function to handle command line arguments and execute the deletion."""
    if len(sys.argv) != 3:
        print("Usage: python delete_action_set.py <json_file> <preset_id>")
        print("Example: python delete_action_set.py 'neptune/universal-layout-default  hold-gyro  latest.json' 'Preset_1000014'")
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
    
    # Delete the action set
    updated_layout = delete_action_set(layout_data, preset_id)
    
    # Create backup filename
    backup_file = json_file.replace('.json', f'_backup_{preset_id}.json')
    
    # Save backup
    print(f"Creating backup: {backup_file}")
    save_json_file(backup_file, layout_data)
    
    # Save updated layout
    print(f"Saving updated layout: {json_file}")
    save_json_file(json_file, updated_layout)
    
    print(f"\nOperation completed successfully!")
    print(f"Backup saved to: {backup_file}")
    print(f"Updated layout saved to: {json_file}")


if __name__ == "__main__":
    main() 