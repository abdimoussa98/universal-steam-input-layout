#!/usr/bin/env python3
"""
Duplicate Action Layer Script for Steam Input Layouts

This script duplicates an action layer along with all its children relationships:
1. Copies the layer definition from action_layers with a new Preset ID
2. Copies the corresponding preset entry with updated references
3. Copies all groups referenced in group_source_bindings with new IDs
4. Updates all internal references to use the new IDs

The duplicated layer is added to the END of action_layers to preserve
runtime ID ordering (critical for controller_action commands).

Usage:
    python duplicate_layer.py <json_file> <source_layer_id> [new_title]

Examples:
    # Duplicate a layer with auto-generated title
    python duplicate_layer.py layout.json Preset_1000006

    # Duplicate with a custom title
    python duplicate_layer.py layout.json Preset_1000006 "L2 Copy"
"""

import json
import sys
import os
import re
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Set


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


def find_max_preset_id(actions: Dict, action_layers: Dict) -> int:
    """Find the maximum Preset_XXXXXXX number used."""
    max_id = 0
    for key in list(actions.keys()) + list(action_layers.keys()):
        if key.startswith("Preset_"):
            try:
                num = int(key.split("_")[1])
                max_id = max(max_id, num)
            except (IndexError, ValueError):
                pass
    return max_id


def find_max_group_id(groups: List[Dict]) -> int:
    """Find the maximum group ID used."""
    max_id = 0
    for group in groups:
        try:
            group_id = int(group.get("id", 0))
            max_id = max(max_id, group_id)
        except ValueError:
            pass
    return max_id


def find_max_preset_array_id(presets: List[Dict]) -> int:
    """Find the maximum preset array id (the 'id' field in preset entries)."""
    max_id = 0
    for preset in presets:
        try:
            preset_id = int(preset.get("id", 0))
            max_id = max(max_id, preset_id)
        except ValueError:
            pass
    return max_id


def deep_copy_ordered(obj: Any) -> Any:
    """Deep copy an object while preserving OrderedDict structure."""
    if isinstance(obj, OrderedDict):
        return OrderedDict((k, deep_copy_ordered(v)) for k, v in obj.items())
    elif isinstance(obj, dict):
        return {k: deep_copy_ordered(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_copy_ordered(item) for item in obj]
    else:
        return obj


def get_groups_for_preset(presets: List[Dict], preset_name: str) -> Dict[str, str]:
    """Get the group_source_bindings for a given preset name."""
    for preset in presets:
        if preset.get("name") == preset_name:
            return preset.get("group_source_bindings", {})
    return {}


def find_group_by_id(groups: List[Dict], group_id: str) -> Dict[str, Any]:
    """Find a group by its ID."""
    for group in groups:
        if group.get("id") == group_id:
            return group
    return None


def calculate_runtime_ids(actions: Dict, action_layers: Dict) -> Dict[str, int]:
    """
    Calculate runtime IDs for all action sets and layers based on their order.
    Action sets come first (starting at 1), then action layers.
    """
    runtime_ids = {}
    position = 1
    
    for action_key in actions.keys():
        runtime_ids[action_key] = position
        position += 1
    
    for layer_key in action_layers.keys():
        runtime_ids[layer_key] = position
        position += 1
    
    return runtime_ids


def duplicate_layer(
    layout_data: Dict[str, Any],
    source_layer_id: str,
    new_title: str = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Duplicate an action layer with all its children relationships.
    
    Args:
        layout_data: The parsed JSON layout data
        source_layer_id: The Preset ID of the layer to duplicate (e.g., "Preset_1000006")
        new_title: Optional custom title for the new layer
    
    Returns:
        Tuple of (updated layout data, duplication info)
    """
    print(f"\n{'='*60}")
    print(f"Duplicating Layer: {source_layer_id}")
    print(f"{'='*60}")
    
    cm = layout_data.get("controller_mappings", {})
    actions = cm.get("actions", OrderedDict())
    action_layers = cm.get("action_layers", OrderedDict())
    presets = cm.get("preset", [])
    groups = cm.get("group", [])
    
    # Verify the source layer exists
    if source_layer_id not in action_layers:
        print(f"Error: Layer '{source_layer_id}' not found in action_layers.")
        print(f"Available layers: {list(action_layers.keys())[:10]}...")
        sys.exit(1)
    
    source_layer = action_layers[source_layer_id]
    source_title = source_layer.get("title", "Unknown")
    print(f"Source layer: '{source_title}'")
    
    # Calculate current runtime IDs
    old_runtime_ids = calculate_runtime_ids(actions, action_layers)
    source_runtime_id = old_runtime_ids[source_layer_id]
    print(f"Source runtime ID: {source_runtime_id}")
    
    # Generate new Preset ID
    max_preset_id = find_max_preset_id(actions, action_layers)
    new_preset_id = f"Preset_{max_preset_id + 1}"
    print(f"\n[Step 1] Generating new Preset ID: {new_preset_id}")
    
    # Determine new title
    if new_title is None:
        new_title = f"{source_title} (Copy)"
    print(f"New layer title: '{new_title}'")
    
    # Get source preset's group_source_bindings
    source_gsb = get_groups_for_preset(presets, source_layer_id)
    if not source_gsb:
        print(f"Warning: No group_source_bindings found for {source_layer_id}")
    print(f"\n[Step 2] Found {len(source_gsb)} groups to duplicate")
    
    # Generate new group IDs and create mapping
    max_group_id = find_max_group_id(groups)
    group_id_mapping = {}  # old_id -> new_id
    
    print(f"\n[Step 3] Duplicating groups...")
    new_groups = []
    for old_group_id in source_gsb.keys():
        new_group_id = str(max_group_id + 1)
        max_group_id += 1
        group_id_mapping[old_group_id] = new_group_id
        
        # Find and copy the original group
        original_group = find_group_by_id(groups, old_group_id)
        if original_group:
            new_group = deep_copy_ordered(original_group)
            new_group["id"] = new_group_id
            new_groups.append(new_group)
            print(f"  Group {old_group_id} -> {new_group_id} (mode: {original_group.get('mode', 'Unknown')})")
        else:
            print(f"  Warning: Group {old_group_id} not found in groups array")
    
    # Create new group_source_bindings with updated group IDs
    new_gsb = OrderedDict()
    for old_id, binding_value in source_gsb.items():
        new_id = group_id_mapping.get(old_id, old_id)
        new_gsb[new_id] = binding_value
    
    # Create new preset entry
    max_preset_array_id = find_max_preset_array_id(presets)
    new_preset_entry = OrderedDict([
        ("id", str(max_preset_array_id + 1)),
        ("name", new_preset_id),
        ("group_source_bindings", new_gsb)
    ])
    print(f"\n[Step 4] Created new preset entry with id: {new_preset_entry['id']}")
    
    # Create new layer definition (copy from source)
    new_layer = deep_copy_ordered(source_layer)
    new_layer["title"] = new_title
    print(f"\n[Step 5] Created new layer definition")
    print(f"  Parent set: {new_layer.get('parent_set_name')}")
    
    # Add everything to the layout
    print(f"\n[Step 6] Adding to layout...")
    
    # Add new layer at the END of action_layers (preserves runtime ID ordering)
    action_layers[new_preset_id] = new_layer
    print(f"  Added layer to end of action_layers")
    
    # Add new groups to the end of groups array
    groups.extend(new_groups)
    print(f"  Added {len(new_groups)} groups to groups array")
    
    # Add new preset entry to the end of preset array
    presets.append(new_preset_entry)
    print(f"  Added preset entry to preset array")
    
    # Calculate new runtime IDs
    new_runtime_ids = calculate_runtime_ids(actions, action_layers)
    new_runtime_id = new_runtime_ids[new_preset_id]
    print(f"\n[Step 7] New layer runtime ID: {new_runtime_id}")
    
    # Update references if needed
    # (In this case, since we're adding to the end, no existing references need updating)
    
    info = {
        "source_layer_id": source_layer_id,
        "source_title": source_title,
        "source_runtime_id": source_runtime_id,
        "new_preset_id": new_preset_id,
        "new_title": new_title,
        "new_runtime_id": new_runtime_id,
        "groups_duplicated": len(new_groups),
        "group_id_mapping": group_id_mapping
    }
    
    return layout_data, info


def list_layers(layout_data: Dict[str, Any]) -> None:
    """List all available action layers."""
    cm = layout_data.get("controller_mappings", {})
    actions = cm.get("actions", OrderedDict())
    action_layers = cm.get("action_layers", OrderedDict())
    
    runtime_ids = calculate_runtime_ids(actions, action_layers)
    
    print("\nAvailable Action Layers:")
    print("-" * 80)
    print(f"{'Preset ID':<20} {'Runtime ID':<12} {'Title':<30} {'Parent Set'}")
    print("-" * 80)
    
    for layer_id, layer_data in action_layers.items():
        title = layer_data.get("title", "Unknown")[:28]
        parent = layer_data.get("parent_set_name", "")
        parent_title = ""
        if parent in actions:
            parent_title = actions[parent].get("title", "")
        runtime_id = runtime_ids.get(layer_id, "?")
        print(f"{layer_id:<20} {runtime_id:<12} {title:<30} {parent_title}")


def main():
    parser = argparse.ArgumentParser(
        description="Duplicate an action layer in a Steam Input layout file"
    )
    parser.add_argument("json_file", help="Input layout JSON file")
    parser.add_argument(
        "source_layer_id",
        nargs="?",
        help="Preset ID of the layer to duplicate (e.g., Preset_1000006)"
    )
    parser.add_argument(
        "new_title",
        nargs="?",
        help="Optional: Custom title for the duplicated layer"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available action layers and exit"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output to a different file instead of modifying in place"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup file"
    )
    
    args = parser.parse_args()
    
    # Load the JSON file
    print(f"Loading layout file: {args.json_file}")
    layout_data = load_json_file(args.json_file)
    
    # Validate the layout structure
    if "controller_mappings" not in layout_data:
        print("Error: Invalid layout file. Expected 'controller_mappings' at root level.")
        sys.exit(1)
    
    # List mode
    if args.list:
        list_layers(layout_data)
        sys.exit(0)
    
    # Require source_layer_id for duplication
    if not args.source_layer_id:
        print("Error: source_layer_id is required for duplication.")
        print("Use --list to see available layers.")
        parser.print_help()
        sys.exit(1)
    
    # Create backup (unless disabled or outputting to different file)
    if not args.no_backup and not args.output:
        backup_file = args.json_file.replace('.json', '_backup_before_duplicate.json')
        print(f"Creating backup: {backup_file}")
        save_json_file(backup_file, layout_data)
    
    # Perform the duplication
    updated_layout, info = duplicate_layer(
        layout_data,
        args.source_layer_id,
        args.new_title
    )
    
    # Determine output path
    output_path = args.output if args.output else args.json_file
    
    # Save the result
    print(f"\n[Step 8] Saving layout...")
    save_json_file(output_path, updated_layout)
    
    # Print summary
    print(f"\n{'='*60}")
    print("DUPLICATION SUMMARY")
    print(f"{'='*60}")
    print(f"Source Layer: {info['source_layer_id']} ('{info['source_title']}')")
    print(f"Source Runtime ID: {info['source_runtime_id']}")
    print(f"")
    print(f"New Layer: {info['new_preset_id']} ('{info['new_title']}')")
    print(f"New Runtime ID: {info['new_runtime_id']}")
    print(f"Groups Duplicated: {info['groups_duplicated']}")
    print(f"")
    print(f"Group ID Mapping (old -> new):")
    for old_id, new_id in info['group_id_mapping'].items():
        print(f"  {old_id} -> {new_id}")
    print(f"\nSaved to: {output_path}")
    print(f"\nOperation completed successfully!")


if __name__ == "__main__":
    main()
