#!/usr/bin/env python3
"""
Ensure All Ramp Up Removals Script

This script ensures that whenever a Turning Ramp Up layer is removed via remove_layer,
all 4 variants are removed:
- Turning Ramp Up 0
- Turning Ramp Up 1
- (Gyro) Turning Ramp Up 0
- (Gyro) Turning Ramp Up 1

It also ensures no duplicates exist within each binding list.

Usage:
    python3 ensure_all_ramp_up_removals.py                    # Process all neptune/ JSON files
    python3 ensure_all_ramp_up_removals.py file.json          # Process specific file
    python3 ensure_all_ramp_up_removals.py --dry-run          # Preview changes without modifying
"""

import json
import sys
import os
import glob
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Set

# All Turning Ramp Up variants that should be removed together
RAMP_UP_VARIANTS = [
    "{{Base::Turning Ramp Up 0}}",
    "{{Base::Turning Ramp Up 1}}",
    "{{Base::(Gyro) Turning Ramp Up 0}}",
    "{{Base::(Gyro) Turning Ramp Up 1}}",
]

# The corresponding remove_layer commands
RAMP_UP_REMOVALS = [
    "controller_action remove_layer {{Base::Turning Ramp Up 0}} 0 0, , ",
    "controller_action remove_layer {{Base::Turning Ramp Up 1}} 0 0, , ",
    "controller_action remove_layer {{Base::(Gyro) Turning Ramp Up 0}} 0 0, , ",
    "controller_action remove_layer {{Base::(Gyro) Turning Ramp Up 1}} 0 0, , ",
]


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
    """Check if a binding contains a remove_layer for any Turning Ramp Up variant."""
    for variant in RAMP_UP_VARIANTS:
        if f"controller_action remove_layer {variant}" in binding:
            return True
    return False


def get_existing_ramp_up_removals(bindings: List[str]) -> Set[str]:
    """Get the set of Ramp Up removal commands already in the bindings."""
    existing = set()
    for binding in bindings:
        for removal in RAMP_UP_REMOVALS:
            if removal in binding or removal.strip() == binding.strip():
                existing.add(removal)
    return existing


def find_ramp_up_insertion_index(bindings: List[str]) -> int:
    """Find the index where the first Ramp Up removal appears."""
    for i, binding in enumerate(bindings):
        if contains_ramp_up_removal(binding):
            return i
    return 0


def remove_duplicates_preserve_order(bindings: List[str]) -> List[str]:
    """Remove duplicate bindings while preserving order."""
    seen = set()
    result = []
    for binding in bindings:
        normalized = binding.strip()
        if normalized not in seen:
            seen.add(normalized)
            result.append(binding)
    return result


def process_binding_value(binding_value: Any, stats: Dict[str, int]) -> Tuple[Any, bool]:
    """
    Process a binding value (string or list) and ensure all Ramp Up variants are removed.
    
    Returns:
        Tuple of (new_binding_value, was_modified)
    """
    if isinstance(binding_value, str):
        # Single string binding
        if contains_ramp_up_removal(binding_value):
            # Convert to array with all variants
            new_bindings = []
            # Add all ramp up removals first
            for removal in RAMP_UP_REMOVALS:
                new_bindings.append(removal)
            stats["bindings_modified"] += 1
            stats["removals_added"] += len(RAMP_UP_REMOVALS) - 1  # -1 because one was already there
            return new_bindings, True
        return binding_value, False
    
    elif isinstance(binding_value, list):
        # Check if any binding contains a Ramp Up removal
        has_ramp_up_removal = any(
            contains_ramp_up_removal(b) for b in binding_value if isinstance(b, str)
        )
        
        if not has_ramp_up_removal:
            return binding_value, False
        
        # Get existing removals
        existing_removals = get_existing_ramp_up_removals(binding_value)
        missing_removals = [r for r in RAMP_UP_REMOVALS if r not in existing_removals]
        
        if not missing_removals:
            # All variants already present, just remove duplicates
            new_bindings = remove_duplicates_preserve_order(binding_value)
            if len(new_bindings) != len(binding_value):
                stats["duplicates_removed"] += len(binding_value) - len(new_bindings)
                return new_bindings, True
            return binding_value, False
        
        # Find insertion point (after the first Ramp Up removal found)
        insert_index = find_ramp_up_insertion_index(binding_value) + 1
        
        # Build new bindings list
        new_bindings = list(binding_value)
        
        # Insert missing removals
        for i, removal in enumerate(missing_removals):
            new_bindings.insert(insert_index + i, removal)
            stats["removals_added"] += 1
        
        # Remove duplicates
        new_bindings = remove_duplicates_preserve_order(new_bindings)
        
        stats["bindings_modified"] += 1
        return new_bindings, True
    
    return binding_value, False


def process_object(obj: Any, stats: Dict[str, int]) -> Any:
    """
    Recursively process a JSON object, looking for 'binding' keys inside 'bindings' objects.
    """
    if isinstance(obj, dict):
        new_obj = OrderedDict() if isinstance(obj, OrderedDict) else {}
        
        for key, value in obj.items():
            if key == "binding" and isinstance(value, (str, list)):
                # Found a binding - process it
                new_value, was_modified = process_binding_value(value, stats)
                new_obj[key] = new_value
            else:
                # Recurse into nested objects
                new_obj[key] = process_object(value, stats)
        
        return new_obj
    
    elif isinstance(obj, list):
        return [process_object(item, stats) for item in obj]
    
    else:
        return obj


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, int]:
    """Process a single JSON file."""
    print(f"\nProcessing: {file_path}")
    
    # Load the file
    data = load_json_file(file_path)
    
    # Track statistics
    stats = {
        "bindings_modified": 0,
        "removals_added": 0,
        "duplicates_removed": 0
    }
    
    # Process the data
    processed_data = process_object(data, stats)
    
    # Report results
    total_changes = stats["bindings_modified"]
    if total_changes > 0:
        print(f"  Bindings modified: {stats['bindings_modified']}")
        print(f"  Removals added: {stats['removals_added']}")
        print(f"  Duplicates removed: {stats['duplicates_removed']}")
        
        if dry_run:
            print(f"  [DRY RUN] Would save changes to: {file_path}")
        else:
            save_json_file(file_path, processed_data)
    else:
        print(f"  No changes needed (all variants already present or no Ramp Up removals found)")
    
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
        description="Ensure all Turning Ramp Up variants are removed together"
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
    print("Ensure All Ramp Up Removals Script")
    print("=" * 70)
    print("\nThis script ensures that when any Turning Ramp Up layer is removed,")
    print("all 4 variants are removed:")
    for removal in RAMP_UP_REMOVALS:
        variant = removal.split("{{Base::")[1].split("}}")[0]
        print(f"  - {variant}")
    
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
        "total_bindings_modified": 0,
        "total_removals_added": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        if stats["bindings_modified"] > 0:
            total_stats["files_modified"] += 1
            total_stats["total_bindings_modified"] += stats["bindings_modified"]
            total_stats["total_removals_added"] += stats["removals_added"]
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Total bindings modified: {total_stats['total_bindings_modified']}")
    print(f"Total removals added: {total_stats['total_removals_added']}")
    
    if args.dry_run and total_stats["files_modified"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
