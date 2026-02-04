
#!/usr/bin/env python3
"""
Duplicate Gyro Actions Script for Steam Input Layouts

This script finds all controller_action remove_layer commands that reference specific
trigger layers and duplicates them for the equivalent "(Gyro)" prefixed layers.

This ensures that when a trigger layer is removed/deactivated, the corresponding
gyro variant is also removed/deactivated.

Layer Mappings (trigger layers only):
  Default layout (L2/R2):
    {{Base::L2}}  -> {{Base::(Gyro) L2}}
    {{Base::R2}}  -> {{Base::(Gyro) R2}}

  Alternative layout (L1/R1):
    {{Base::L1}}  -> {{Base::(Gyro) L1}}
    {{Base::R1}}  -> {{Base::(Gyro) R1}}

Usage:
    python3 duplicate_gyro_actions.py                    # Process all neptune/ JSON files
    python3 duplicate_gyro_actions.py file.json          # Process specific file
    python3 duplicate_gyro_actions.py --dry-run          # Preview changes without modifying
    python3 duplicate_gyro_actions.py file.json --dry-run
"""

import json
import sys
import os
import glob
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple

# Trigger layer mappings only (modifier layers already processed separately)
LAYER_MAPPING = {
    # Default layout - trigger layers (L2/R2)
    "{{Base::L2}}": "{{Base::(Gyro) L2}}",
    "{{Base::R2}}": "{{Base::(Gyro) R2}}",
    # Alternative layout - trigger layers (L1/R1)
    "{{Base::L1}}": "{{Base::(Gyro) L1}}",
    "{{Base::R1}}": "{{Base::(Gyro) R1}}",
}

# Controller action commands that reference layers (only remove_layer)
CONTROLLER_ACTION_COMMANDS = ['remove_layer']


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


def is_matching_controller_action(binding: str) -> Tuple[bool, str, str]:
    """
    Check if a binding string contains a controller_action for one of the mapped layers.
    
    Returns:
        Tuple of (is_match, original_layer, gyro_layer)
    """
    for original_layer, gyro_layer in LAYER_MAPPING.items():
        for cmd in CONTROLLER_ACTION_COMMANDS:
            if f"controller_action {cmd} {original_layer}" in binding:
                return True, original_layer, gyro_layer
    return False, "", ""


def create_gyro_duplicate(binding: str, original_layer: str, gyro_layer: str) -> str:
    """Create a duplicate binding with the gyro layer instead of the original."""
    return binding.replace(original_layer, gyro_layer)


def gyro_version_exists(bindings: List[str], gyro_binding: str) -> bool:
    """Check if the gyro version of a binding already exists in the list."""
    return gyro_binding in bindings


def process_binding_value(binding_value: Any) -> Tuple[Any, int]:
    """
    Process a binding value (string or list) and add gyro duplicates where needed.
    
    Returns:
        Tuple of (new_binding_value, count_of_duplicates_added)
    """
    duplicates_added = 0
    
    if isinstance(binding_value, str):
        # Single string binding
        is_match, original_layer, gyro_layer = is_matching_controller_action(binding_value)
        if is_match:
            gyro_binding = create_gyro_duplicate(binding_value, original_layer, gyro_layer)
            # Check if gyro version is already there (shouldn't be for single string, but check anyway)
            if binding_value != gyro_binding:
                # Convert to array with original + gyro duplicate
                duplicates_added = 1
                return [binding_value, gyro_binding], duplicates_added
        return binding_value, duplicates_added
    
    elif isinstance(binding_value, list):
        # Array of bindings
        new_bindings = []
        for binding in binding_value:
            new_bindings.append(binding)
            
            if isinstance(binding, str):
                is_match, original_layer, gyro_layer = is_matching_controller_action(binding)
                if is_match:
                    gyro_binding = create_gyro_duplicate(binding, original_layer, gyro_layer)
                    # Only add if not already present
                    if not gyro_version_exists(binding_value, gyro_binding) and not gyro_version_exists(new_bindings, gyro_binding):
                        new_bindings.append(gyro_binding)
                        duplicates_added += 1
        
        return new_bindings, duplicates_added
    
    return binding_value, duplicates_added


def process_object(obj: Any, stats: Dict[str, int]) -> Any:
    """
    Recursively process a JSON object, looking for 'binding' keys inside 'bindings' objects.
    
    Args:
        obj: The object to process
        stats: Dictionary to track statistics
    
    Returns:
        The processed object with gyro duplicates added
    """
    if isinstance(obj, dict):
        new_obj = OrderedDict() if isinstance(obj, OrderedDict) else {}
        
        for key, value in obj.items():
            if key == "binding" and isinstance(value, (str, list)):
                # Found a binding - process it
                new_value, duplicates_added = process_binding_value(value)
                new_obj[key] = new_value
                stats["duplicates_added"] += duplicates_added
                if duplicates_added > 0:
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
    Process a single JSON file, adding gyro duplicate actions.
    
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
        "duplicates_added": 0,
        "bindings_modified": 0
    }
    
    # Process the data
    processed_data = process_object(data, stats)
    
    # Report results
    if stats["duplicates_added"] > 0:
        print(f"  Found {stats['bindings_modified']} bindings to modify")
        print(f"  Added {stats['duplicates_added']} gyro duplicate actions")
        
        if dry_run:
            print(f"  [DRY RUN] Would save changes to: {file_path}")
        else:
            save_json_file(file_path, processed_data)
    else:
        print(f"  No changes needed (gyro duplicates may already exist)")
    
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
        description="Add gyro duplicate actions to Steam Input layout files"
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
    print("Duplicate Gyro Actions Script")
    print("=" * 60)
    
    if args.dry_run:
        print("[DRY RUN MODE - No files will be modified]")
    
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
        "total_duplicates_added": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        if stats["duplicates_added"] > 0:
            total_stats["files_modified"] += 1
            total_stats["total_duplicates_added"] += stats["duplicates_added"]
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Total gyro duplicates added: {total_stats['total_duplicates_added']}")
    
    if args.dry_run and total_stats["total_duplicates_added"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
