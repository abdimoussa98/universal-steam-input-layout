#!/usr/bin/env python3
"""
Fix Gyro Layer References Script for Steam Input Layouts

This script checks all layers that have "(Gyro)" in their title and ensures that
any add_layer commands within those layers reference the Gyro counterpart of a layer
(if one exists) instead of the non-Gyro version.

Problem this solves:
When Gyro layers were duplicated from their non-Gyro counterparts, the add_layer
commands inside them still reference the original non-Gyro layers. For example,
inside "(Gyro) L1" layer, an add_layer might reference "{{Base::L2: Modifier 0}}"
when it should reference "{{Base::(Gyro) L2: Modifier 0}}".

Logic:
1. Build a mapping of non-Gyro layer names → Gyro layer names
2. Find all Gyro layers (those with "(Gyro)" in the title)
3. For each Gyro layer, scan its preset bindings for add_layer commands
4. If an add_layer references a non-Gyro layer that has a Gyro counterpart,
   update the reference to point to the Gyro version

Usage:
    python3 fix_gyro_layer_references.py                    # Process all neptune/ JSON files
    python3 fix_gyro_layer_references.py file.json          # Process specific file
    python3 fix_gyro_layer_references.py --dry-run          # Preview changes without modifying
    python3 fix_gyro_layer_references.py file.json --dry-run
"""

import json
import sys
import os
import glob
import argparse
import re
from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Set, Optional


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
        print(f"  Saved: {file_path}")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)


def extract_layer_name_from_reference(reference: str) -> Optional[str]:
    """
    Extract the layer name from a layer reference like "{{Base::L2: Modifier 0}}".
    Returns "L2: Modifier 0" from "{{Base::L2: Modifier 0}}".
    """
    match = re.search(r'\{\{Base::([^}]+)\}\}', reference)
    if match:
        return match.group(1)
    return None


def build_layer_mapping(action_layers: Dict[str, Any]) -> Tuple[Dict[str, str], Set[str], Dict[str, str]]:
    """
    Build mappings for layer analysis.
    
    Returns:
        - non_gyro_to_gyro: Maps non-Gyro layer names to their Gyro counterparts
        - gyro_layer_preset_ids: Set of preset IDs for Gyro layers
        - preset_id_to_title: Maps preset IDs to layer titles
    """
    non_gyro_to_gyro = {}  # "L2: Modifier 0" -> "(Gyro) L2: Modifier 0"
    gyro_layer_preset_ids = set()  # Preset IDs of Gyro layers
    preset_id_to_title = {}  # "Preset_1000148" -> "(Gyro) L2: Modifier 0"
    
    # First pass: collect all layer titles and identify Gyro layers
    all_layer_titles = {}
    for preset_id, layer_info in action_layers.items():
        title = layer_info.get("title", "")
        all_layer_titles[preset_id] = title
        preset_id_to_title[preset_id] = title
        
        if "(Gyro)" in title:
            gyro_layer_preset_ids.add(preset_id)
    
    # Second pass: build non-Gyro to Gyro mapping
    for preset_id, title in all_layer_titles.items():
        if "(Gyro)" in title:
            # Extract the non-Gyro version of this title
            # "(Gyro) L2: Modifier 0" -> "L2: Modifier 0"
            non_gyro_title = title.replace("(Gyro) ", "")
            non_gyro_to_gyro[non_gyro_title] = title
    
    return non_gyro_to_gyro, gyro_layer_preset_ids, preset_id_to_title


def find_preset_by_name(presets: List[Dict], preset_name: str) -> Optional[Dict]:
    """Find a preset entry by its name field."""
    for preset in presets:
        if preset.get("name") == preset_name:
            return preset
    return None


def get_group_ids_from_preset(preset: Dict) -> List[str]:
    """Extract group IDs from a preset's group_source_bindings."""
    group_source_bindings = preset.get("group_source_bindings", {})
    return list(group_source_bindings.keys())


def find_groups_by_ids(groups: List[Dict], group_ids: List[str]) -> List[Dict]:
    """Find all groups matching the given IDs."""
    matching_groups = []
    for group in groups:
        if group.get("id") in group_ids:
            matching_groups.append(group)
    return matching_groups


def fix_add_layer_reference(binding: str, non_gyro_to_gyro: Dict[str, str]) -> Tuple[str, bool]:
    """
    Check if a binding contains an add_layer command that should be fixed.
    
    Returns:
        Tuple of (fixed_binding, was_fixed)
    """
    # Pattern to match: controller_action add_layer {{Base::LayerName}} ...
    pattern = r'controller_action add_layer \{\{Base::([^}]+)\}\}'
    
    match = re.search(pattern, binding)
    if not match:
        return binding, False
    
    layer_name = match.group(1)
    
    # Skip if already referencing a Gyro layer
    if "(Gyro)" in layer_name:
        return binding, False
    
    # Check if this non-Gyro layer has a Gyro counterpart
    if layer_name in non_gyro_to_gyro:
        gyro_layer_name = non_gyro_to_gyro[layer_name]
        old_ref = f"{{{{Base::{layer_name}}}}}"
        new_ref = f"{{{{Base::{gyro_layer_name}}}}}"
        fixed_binding = binding.replace(old_ref, new_ref)
        return fixed_binding, True
    
    return binding, False


def process_binding_value(binding_value: Any, non_gyro_to_gyro: Dict[str, str], 
                          context: str) -> Tuple[Any, List[Dict]]:
    """
    Process a binding value (string or list) and fix add_layer references.
    
    Returns:
        Tuple of (new_binding_value, list_of_changes)
    """
    changes = []
    
    if isinstance(binding_value, str):
        fixed_binding, was_fixed = fix_add_layer_reference(binding_value, non_gyro_to_gyro)
        if was_fixed:
            changes.append({
                "context": context,
                "old": binding_value,
                "new": fixed_binding
            })
        return fixed_binding, changes
    
    elif isinstance(binding_value, list):
        new_bindings = []
        for binding in binding_value:
            if isinstance(binding, str):
                fixed_binding, was_fixed = fix_add_layer_reference(binding, non_gyro_to_gyro)
                if was_fixed:
                    changes.append({
                        "context": context,
                        "old": binding,
                        "new": fixed_binding
                    })
                new_bindings.append(fixed_binding)
            else:
                new_bindings.append(binding)
        return new_bindings, changes
    
    return binding_value, changes


def process_object_for_add_layers(obj: Any, non_gyro_to_gyro: Dict[str, str], 
                                   context: str = "") -> Tuple[Any, List[Dict]]:
    """
    Recursively process a JSON object, looking for 'binding' keys and fixing add_layer refs.
    
    Args:
        obj: The object to process
        non_gyro_to_gyro: Mapping of non-Gyro layer names to Gyro counterparts
        context: Current context path for reporting
    
    Returns:
        Tuple of (processed_object, list_of_changes)
    """
    all_changes = []
    
    if isinstance(obj, dict):
        new_obj = OrderedDict() if isinstance(obj, OrderedDict) else {}
        
        for key, value in obj.items():
            new_context = f"{context}.{key}" if context else key
            
            if key == "binding" and isinstance(value, (str, list)):
                # Found a binding - process it
                new_value, changes = process_binding_value(value, non_gyro_to_gyro, new_context)
                new_obj[key] = new_value
                all_changes.extend(changes)
            else:
                # Recurse into nested objects
                processed_value, changes = process_object_for_add_layers(value, non_gyro_to_gyro, new_context)
                new_obj[key] = processed_value
                all_changes.extend(changes)
        
        return new_obj, all_changes
    
    elif isinstance(obj, list):
        new_list = []
        for i, item in enumerate(obj):
            new_context = f"{context}[{i}]"
            processed_item, changes = process_object_for_add_layers(item, non_gyro_to_gyro, new_context)
            new_list.append(processed_item)
            all_changes.extend(changes)
        return new_list, all_changes
    
    else:
        return obj, all_changes


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Process a single JSON file, fixing add_layer references in Gyro layers.
    
    Args:
        file_path: Path to the JSON file
        dry_run: If True, don't actually save changes
    
    Returns:
        Dictionary with statistics about changes made
    """
    print(f"\nProcessing: {file_path}")
    
    # Load the file
    data = load_json_file(file_path)
    
    # Get the relevant sections
    controller_mappings = data.get("controller_mappings", {})
    action_layers = controller_mappings.get("action_layers", {})
    presets = controller_mappings.get("preset", [])
    groups = controller_mappings.get("group", [])
    
    if not action_layers:
        print("  No action_layers found in file")
        return {"fixes_made": 0, "gyro_layers_checked": 0}
    
    # Build the layer mappings
    non_gyro_to_gyro, gyro_layer_preset_ids, preset_id_to_title = build_layer_mapping(action_layers)
    
    print(f"  Found {len(gyro_layer_preset_ids)} Gyro layers")
    print(f"  Found {len(non_gyro_to_gyro)} non-Gyro to Gyro mappings")
    
    if not gyro_layer_preset_ids:
        print("  No Gyro layers to process")
        return {"fixes_made": 0, "gyro_layers_checked": 0}
    
    # Display the mappings
    print("\n  Non-Gyro → Gyro layer mappings:")
    for non_gyro, gyro in sorted(non_gyro_to_gyro.items()):
        print(f"    {non_gyro} → {gyro}")
    
    # Track all changes
    all_changes = []
    gyro_layers_checked = 0
    
    # Process each Gyro layer's preset
    print("\n  Checking Gyro layers for add_layer references...")
    for preset_id in gyro_layer_preset_ids:
        layer_title = preset_id_to_title.get(preset_id, "Unknown")
        
        # Find the preset for this Gyro layer
        preset = find_preset_by_name(presets, preset_id)
        if not preset:
            print(f"    Warning: No preset found for Gyro layer '{layer_title}' ({preset_id})")
            continue
        
        gyro_layers_checked += 1
        
        # Get the group IDs for this preset
        group_ids = get_group_ids_from_preset(preset)
        
        # Find and process the groups
        layer_groups = find_groups_by_ids(groups, group_ids)
        
        for group in layer_groups:
            group_id = group.get("id", "?")
            context = f"Gyro Layer '{layer_title}' -> Group {group_id}"
            
            # Process the group's inputs for add_layer references
            processed_group, changes = process_object_for_add_layers(
                group, non_gyro_to_gyro, context
            )
            
            if changes:
                all_changes.extend(changes)
                # Update the group in place
                group.clear()
                group.update(processed_group)
    
    # Report changes
    if all_changes:
        print(f"\n  Found {len(all_changes)} add_layer references to fix:")
        for change in all_changes:
            # Extract layer names for cleaner output
            old_layer = extract_layer_name_from_reference(change["old"]) or change["old"]
            new_layer = extract_layer_name_from_reference(change["new"]) or change["new"]
            print(f"    - {old_layer} → {new_layer}")
        
        if dry_run:
            print(f"\n  [DRY RUN] Would save changes to: {file_path}")
        else:
            save_json_file(file_path, data)
    else:
        print("\n  No add_layer references need fixing")
    
    return {
        "fixes_made": len(all_changes),
        "gyro_layers_checked": gyro_layers_checked
    }


def find_neptune_json_files() -> List[str]:
    """Find all JSON files in the neptune/ directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    neptune_dir = os.path.join(script_dir, "neptune")
    
    if not os.path.isdir(neptune_dir):
        print(f"Error: neptune/ directory not found at {neptune_dir}")
        sys.exit(1)
    
    json_files = glob.glob(os.path.join(neptune_dir, "*.json"))
    return sorted(json_files)


def main():
    parser = argparse.ArgumentParser(
        description="Fix add_layer references in Gyro layers to point to Gyro counterparts"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Specific JSON file to process (default: all files in neptune/)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview changes without modifying files"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Fix Gyro Layer References Script")
    print("=" * 70)
    print("\nThis script ensures that add_layer commands within Gyro layers")
    print("reference the Gyro counterpart of layers (when available).")
    
    if args.dry_run:
        print("\n[DRY RUN MODE - No files will be modified]")
    
    # Determine files to process
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        files_to_process = [args.file]
    else:
        files_to_process = find_neptune_json_files()
        print(f"\nFound {len(files_to_process)} JSON files in neptune/")
    
    # Process each file
    total_stats = {
        "files_processed": 0,
        "files_modified": 0,
        "total_fixes": 0,
        "total_gyro_layers_checked": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        total_stats["total_gyro_layers_checked"] += stats["gyro_layers_checked"]
        if stats["fixes_made"] > 0:
            total_stats["files_modified"] += 1
            total_stats["total_fixes"] += stats["fixes_made"]
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Gyro layers checked: {total_stats['total_gyro_layers_checked']}")
    print(f"Total add_layer references fixed: {total_stats['total_fixes']}")
    
    if args.dry_run and total_stats["total_fixes"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
