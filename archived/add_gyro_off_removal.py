#!/usr/bin/env python3
"""
Add Gyro Off Removal Script for Steam Input Layouts

This script finds all controller_action remove_layer commands that reference Ramp Up
layers and adds a corresponding removal for the "Gyro Off" layer.

This ensures that when a Ramp Up layer is removed/deactivated, the Gyro Off layer
is also removed/deactivated.

Target Ramp Up Layers:
    {{Base::Turning Ramp Up 0}}
    {{Base::Turning Ramp Up 1}}
    {{Base::Chorded Ramp Up 0}}
    {{Base::Chorded Ramp Up 1}}

Added Layer Removal:
    {{Base::Gyro Off}}

Usage:
    python3 add_gyro_off_removal.py                    # Process all neptune/ JSON files
    python3 add_gyro_off_removal.py file.json          # Process specific file
    python3 add_gyro_off_removal.py --dry-run          # Preview changes without modifying
    python3 add_gyro_off_removal.py file.json --dry-run
"""

import json
import sys
import os
import glob
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple

# Ramp Up layers that trigger the Gyro Off removal
RAMP_UP_LAYERS = [
    "{{Base::Turning Ramp Up 0}}",
    "{{Base::Turning Ramp Up 1}}",
    "{{Base::Chorded Ramp Up 0}}",
    "{{Base::Chorded Ramp Up 1}}",
]

# The Gyro Off layer to add removal for
GYRO_OFF_LAYER = "{{Base::Gyro Off}}"
GYRO_OFF_REMOVAL = f"controller_action remove_layer {GYRO_OFF_LAYER} 0 0, , "


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


def contains_ramp_up_removal(binding: str) -> bool:
    """
    Check if a binding string contains a controller_action remove_layer for any Ramp Up layer.
    """
    for ramp_up_layer in RAMP_UP_LAYERS:
        if f"controller_action remove_layer {ramp_up_layer}" in binding:
            return True
    return False


def contains_gyro_off_removal(bindings: List[str]) -> bool:
    """Check if the Gyro Off removal already exists in the bindings list."""
    for binding in bindings:
        if f"controller_action remove_layer {GYRO_OFF_LAYER}" in binding:
            return True
    return False


def find_insertion_index(bindings: List[str]) -> int:
    """
    Find the best index to insert the Gyro Off removal.
    Insert right after the last Ramp Up removal found.
    """
    last_ramp_up_index = -1
    for i, binding in enumerate(bindings):
        if contains_ramp_up_removal(binding):
            last_ramp_up_index = i
    
    # Insert after the last Ramp Up removal
    return last_ramp_up_index + 1 if last_ramp_up_index >= 0 else 0


def process_binding_value(binding_value: Any) -> Tuple[Any, int]:
    """
    Process a binding value (string or list) and add Gyro Off removal where needed.
    
    Returns:
        Tuple of (new_binding_value, count_of_additions)
    """
    additions = 0
    
    if isinstance(binding_value, str):
        # Single string binding
        if contains_ramp_up_removal(binding_value):
            # Convert to array with original + Gyro Off removal
            additions = 1
            return [binding_value, GYRO_OFF_REMOVAL], additions
        return binding_value, additions
    
    elif isinstance(binding_value, list):
        # Array of bindings - check if any contain Ramp Up removal
        has_ramp_up_removal = any(
            contains_ramp_up_removal(b) for b in binding_value if isinstance(b, str)
        )
        
        if has_ramp_up_removal and not contains_gyro_off_removal(binding_value):
            # Need to add Gyro Off removal
            new_bindings = list(binding_value)
            insert_index = find_insertion_index(new_bindings)
            new_bindings.insert(insert_index, GYRO_OFF_REMOVAL)
            additions = 1
            return new_bindings, additions
        
        return binding_value, additions
    
    return binding_value, additions


def process_object(obj: Any, stats: Dict[str, int]) -> Any:
    """
    Recursively process a JSON object, looking for 'binding' keys inside 'bindings' objects.
    
    Args:
        obj: The object to process
        stats: Dictionary to track statistics
    
    Returns:
        The processed object with Gyro Off removals added
    """
    if isinstance(obj, dict):
        new_obj = OrderedDict() if isinstance(obj, OrderedDict) else {}
        
        for key, value in obj.items():
            if key == "binding" and isinstance(value, (str, list)):
                # Found a binding - process it
                new_value, additions = process_binding_value(value)
                new_obj[key] = new_value
                stats["additions"] += additions
                if additions > 0:
                    stats["bindings_modified"] += 1
            else:
                # Recurse into nested objects
                new_obj[key] = process_object(value, stats)
        
        return new_obj
    
    elif isinstance(obj, list):
        return [process_object(item, stats) for item in obj]
    
    else:
        return obj


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, int]:
    """
    Process a single JSON file, adding Gyro Off removal actions.
    
    Args:
        file_path: Path to the JSON file
        dry_run: If True, don't actually save changes
    
    Returns:
        Dictionary with statistics about changes made
    """
    print(f"\nProcessing: {file_path}")
    
    # Load the file
    data = load_json_file(file_path)
    
    # Track statistics
    stats = {
        "additions": 0,
        "bindings_modified": 0
    }
    
    # Process the data
    processed_data = process_object(data, stats)
    
    # Report results
    if stats["additions"] > 0:
        print(f"  Found {stats['bindings_modified']} bindings to modify")
        print(f"  Added {stats['additions']} Gyro Off removal actions")
        
        if dry_run:
            print(f"  [DRY RUN] Would save changes to: {file_path}")
        else:
            save_json_file(file_path, processed_data)
    else:
        print(f"  No changes needed (Gyro Off removals may already exist or no Ramp Up removals found)")
    
    return stats


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
        description="Add Gyro Off removal actions to Steam Input layout files"
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
    
    print("=" * 60)
    print("Add Gyro Off Removal Script")
    print("=" * 60)
    print(f"\nRamp Up layers that trigger Gyro Off removal:")
    for layer in RAMP_UP_LAYERS:
        print(f"  - {layer}")
    print(f"\nGyro Off removal to add:")
    print(f"  {GYRO_OFF_REMOVAL}")
    
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
        "total_additions": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        if stats["additions"] > 0:
            total_stats["files_modified"] += 1
            total_stats["total_additions"] += stats["additions"]
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Total Gyro Off removals added: {total_stats['total_additions']}")
    
    if args.dry_run and total_stats["total_additions"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
