#!/usr/bin/env python3
"""
Update Modifier 2 Gyro Release Script

This script updates the release bindings in the Modifier 2 layers to toggle the Gyro layer:
- Non-gyro variants: Change empty_binding to add_layer {{Base::Gyro}} 1 1
- Gyro variants: Change empty_binding to remove_layer {{Base::Gyro}} 1 1

For Default Layout (L1/R1 as modifiers):
- L1!R1: Modifier 2, R1!L1: Modifier 2 -> add_layer Gyro on bumper release
- (Gyro) L1!R1: Modifier 2, (Gyro) R1!L1: Modifier 2 -> remove_layer Gyro on bumper release

For Alternative Layout (L2/R2 as modifiers):
- L2!R2: Modifier 2, R2!L2: Modifier 2 -> add_layer Gyro on trigger release
- (Gyro) L2!R2: Modifier 2, (Gyro) R2!L2: Modifier 2 -> remove_layer Gyro on trigger release

Usage:
    python3 update_modifier2_gyro_release.py                    # Process all neptune/ JSON files
    python3 update_modifier2_gyro_release.py file.json          # Process specific file
    python3 update_modifier2_gyro_release.py --dry-run          # Preview changes without modifying
"""

import json
import sys
import os
import glob
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Set

# The binding to replace
EMPTY_BINDING = "controller_action empty_binding, , "

# The replacement bindings
GYRO_ADD = "controller_action add_layer {{Base::Gyro}} 1 1, , "
GYRO_REMOVE = "controller_action remove_layer {{Base::Gyro}} 1 1, , "

# Default layout - Modifier 2 layer switches groups (L1/R1 modifiers, bumper release)
DEFAULT_NON_GYRO_GROUPS = ["599", "603"]  # L1!R1, R1!L1
DEFAULT_GYRO_GROUPS = ["12950", "12961"]  # (Gyro) L1!R1, (Gyro) R1!L1

# Alternative layout - Modifier 2 layer groups (L2/R2 modifiers, trigger release)
ALTERNATIVE_NON_GYRO_GROUPS = ["597", "598", "601", "602"]  # L2!R2, R2!L2
ALTERNATIVE_GYRO_GROUPS = ["12948", "12949", "12959", "12960"]  # (Gyro) L2!R2, (Gyro) R2!L2


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


def is_alternative_layout(file_path: str) -> bool:
    """Check if the file is an alternative layout."""
    return "alternative" in os.path.basename(file_path).lower()


def replace_empty_binding_in_list(binding_list: List[str], replacement: str) -> bool:
    """Replace empty_binding with the given replacement in a binding list."""
    for i, binding in enumerate(binding_list):
        if isinstance(binding, str) and EMPTY_BINDING in binding:
            binding_list[i] = replacement
            return True
    return False


def process_bumper_release(group: Dict, replacement: str, stats: Dict) -> bool:
    """Process bumper release bindings (for default layout)."""
    modified = False
    inputs = group.get("inputs", {})
    
    for bumper_name in ["left_bumper", "right_bumper"]:
        bumper = inputs.get(bumper_name, {})
        activators = bumper.get("activators", {})
        release = activators.get("release", {})
        
        if isinstance(release, dict):
            bindings_obj = release.get("bindings", {})
            binding = bindings_obj.get("binding")
            
            if isinstance(binding, list):
                if replace_empty_binding_in_list(binding, replacement):
                    stats["bindings_modified"] += 1
                    modified = True
            elif isinstance(binding, str) and EMPTY_BINDING in binding:
                bindings_obj["binding"] = replacement
                stats["bindings_modified"] += 1
                modified = True
    
    return modified


def process_trigger_release(group: Dict, replacement: str, stats: Dict) -> bool:
    """Process trigger edge release bindings (for alternative layout)."""
    modified = False
    inputs = group.get("inputs", {})
    
    edge = inputs.get("edge", {})
    activators = edge.get("activators", {})
    release = activators.get("release", {})
    
    if isinstance(release, dict):
        bindings_obj = release.get("bindings", {})
        binding = bindings_obj.get("binding")
        
        if isinstance(binding, list):
            if replace_empty_binding_in_list(binding, replacement):
                stats["bindings_modified"] += 1
                modified = True
        elif isinstance(binding, str) and EMPTY_BINDING in binding:
            bindings_obj["binding"] = replacement
            stats["bindings_modified"] += 1
            modified = True
    
    return modified


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, int]:
    """Process a single JSON file."""
    print(f"\nProcessing: {file_path}")
    
    # Determine layout type
    is_alt = is_alternative_layout(file_path)
    layout_type = "alternative" if is_alt else "default"
    print(f"  Layout type: {layout_type}")
    
    # Select the appropriate group IDs
    if is_alt:
        non_gyro_groups = set(ALTERNATIVE_NON_GYRO_GROUPS)
        gyro_groups = set(ALTERNATIVE_GYRO_GROUPS)
    else:
        non_gyro_groups = set(DEFAULT_NON_GYRO_GROUPS)
        gyro_groups = set(DEFAULT_GYRO_GROUPS)
    
    # Load the file
    data = load_json_file(file_path)
    
    # Get groups
    cm = data.get("controller_mappings", data)
    groups = cm.get("group", [])
    
    # Track statistics
    stats = {
        "bindings_modified": 0
    }
    
    modified = False
    
    for group in groups:
        group_id = group.get("id")
        
        # Process non-gyro groups (add Gyro layer)
        if group_id in non_gyro_groups:
            if is_alt:
                # Alternative: trigger edge release
                if process_trigger_release(group, GYRO_ADD, stats):
                    print(f"  Group {group_id}: Updated release to add_layer Gyro")
                    modified = True
            else:
                # Default: bumper release
                if process_bumper_release(group, GYRO_ADD, stats):
                    print(f"  Group {group_id}: Updated release to add_layer Gyro")
                    modified = True
        
        # Process gyro groups (remove Gyro layer)
        if group_id in gyro_groups:
            if is_alt:
                # Alternative: trigger edge release
                if process_trigger_release(group, GYRO_REMOVE, stats):
                    print(f"  Group {group_id}: Updated release to remove_layer Gyro")
                    modified = True
            else:
                # Default: bumper release
                if process_bumper_release(group, GYRO_REMOVE, stats):
                    print(f"  Group {group_id}: Updated release to remove_layer Gyro")
                    modified = True
    
    # Report results
    if stats["bindings_modified"] > 0:
        print(f"  Total bindings modified: {stats['bindings_modified']}")
        
        if dry_run:
            print(f"  [DRY RUN] Would save changes to: {file_path}")
        else:
            save_json_file(file_path, data)
    else:
        print(f"  No changes needed")
    
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
        description="Update Modifier 2 layers with Gyro release bindings"
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
    print("Update Modifier 2 Gyro Release Script")
    print("=" * 70)
    print("\nThis script updates Modifier 2 layer release bindings:")
    print("  - Non-gyro variants: add_layer {{Base::Gyro}} 1 1")
    print("  - Gyro variants: remove_layer {{Base::Gyro}} 1 1")
    
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
        "total_bindings_modified": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        if stats["bindings_modified"] > 0:
            total_stats["files_modified"] += 1
            total_stats["total_bindings_modified"] += stats["bindings_modified"]
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Total bindings modified: {total_stats['total_bindings_modified']}")
    
    if args.dry_run and total_stats["files_modified"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
