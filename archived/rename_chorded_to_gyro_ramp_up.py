#!/usr/bin/env python3
"""
Rename Chorded Ramp Up to (Gyro) Turning Ramp Up Script

This script:
1. Renames "Chorded Ramp Up 0/1" layer titles to "(Gyro) Turning Ramp Up 0/1"
2. Updates all references from {{Base::Chorded Ramp Up X}} to {{Base::(Gyro) Turning Ramp Up X}}
3. Changes non-gyro trigger layer chord activators to add "Turning Ramp Up" instead

Default Layout:
- L2/R2 layers (non-gyro triggers): chord adds Turning Ramp Up
- (Gyro) L2/(Gyro) R2 layers: chord adds (Gyro) Turning Ramp Up

Alternative Layout:
- L1/R1 layers (non-gyro triggers): chord adds Turning Ramp Up
- (Gyro) L1/(Gyro) R1 layers: chord adds (Gyro) Turning Ramp Up

Usage:
    python3 rename_chorded_to_gyro_ramp_up.py                    # Process all neptune/ JSON files
    python3 rename_chorded_to_gyro_ramp_up.py file.json          # Process specific file
    python3 rename_chorded_to_gyro_ramp_up.py --dry-run          # Preview changes without modifying
"""

import json
import sys
import os
import glob
import re
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple

# Layer title renames
TITLE_RENAMES = {
    "Chorded Ramp Up 0": "(Gyro) Turning Ramp Up 0",
    "Chorded Ramp Up 1": "(Gyro) Turning Ramp Up 1",
}

# Reference renames (in binding strings)
REFERENCE_RENAMES = {
    "{{Base::Chorded Ramp Up 0}}": "{{Base::(Gyro) Turning Ramp Up 0}}",
    "{{Base::Chorded Ramp Up 1}}": "{{Base::(Gyro) Turning Ramp Up 1}}",
}

# Non-gyro trigger layers by layout type
# These layers should have their chord activators changed to add plain Turning Ramp Up
DEFAULT_NON_GYRO_TRIGGER_LAYERS = ["Preset_1000006", "Preset_1000007"]  # L2, R2
ALTERNATIVE_NON_GYRO_TRIGGER_LAYERS = ["Preset_1000008", "Preset_1000005"]  # L1: Modifier 0, R1: Modifier 1 (which are actually the trigger layers in alternative)

# For non-gyro trigger layers, change gyro ramp up back to plain ramp up
NON_GYRO_CHORD_CHANGES = {
    "{{Base::(Gyro) Turning Ramp Up 0}}": "{{Base::Turning Ramp Up 0}}",
    "{{Base::(Gyro) Turning Ramp Up 1}}": "{{Base::Turning Ramp Up 1}}",
}


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


def detect_layout_type(file_path: str) -> str:
    """Detect if this is a default or alternative layout based on filename."""
    if "alternative" in file_path.lower():
        return "alternative"
    return "default"


def rename_layer_titles(data: Dict[str, Any], stats: Dict[str, int]) -> None:
    """Rename layer titles in action_layers."""
    action_layers = data.get("controller_mappings", {}).get("action_layers", {})
    
    for preset_id, layer_data in action_layers.items():
        title = layer_data.get("title", "")
        if title in TITLE_RENAMES:
            layer_data["title"] = TITLE_RENAMES[title]
            stats["titles_renamed"] += 1
            print(f"    Renamed title: '{title}' -> '{TITLE_RENAMES[title]}'")


def replace_references_in_string(s: str, stats: Dict[str, int]) -> str:
    """Replace Chorded Ramp Up references in a string."""
    modified = s
    for old, new in REFERENCE_RENAMES.items():
        if old in modified:
            modified = modified.replace(old, new)
            stats["references_replaced"] += 1
    return modified


def replace_references_in_object(obj: Any, stats: Dict[str, int]) -> Any:
    """Recursively replace references in an object."""
    if isinstance(obj, str):
        return replace_references_in_string(obj, stats)
    elif isinstance(obj, dict):
        new_obj = OrderedDict() if isinstance(obj, OrderedDict) else {}
        for key, value in obj.items():
            new_obj[key] = replace_references_in_object(value, stats)
        return new_obj
    elif isinstance(obj, list):
        return [replace_references_in_object(item, stats) for item in obj]
    else:
        return obj


def get_non_gyro_trigger_groups(data: Dict[str, Any], layout_type: str) -> List[str]:
    """Get the group IDs used by non-gyro trigger layers."""
    presets = data.get("controller_mappings", {}).get("preset", [])
    
    if layout_type == "default":
        trigger_layers = DEFAULT_NON_GYRO_TRIGGER_LAYERS
    else:
        # For alternative, L1/R1 are the triggers
        # Need to find the actual preset names for L1 and R1 trigger layers
        trigger_layers = []
        action_layers = data.get("controller_mappings", {}).get("action_layers", {})
        for preset_id, layer_data in action_layers.items():
            title = layer_data.get("title", "")
            # In alternative, L1 and R1 are the trigger layers
            if title in ["L1", "R1"]:
                trigger_layers.append(preset_id)
    
    group_ids = []
    for preset in presets:
        if preset.get("name") in trigger_layers:
            gsb = preset.get("group_source_bindings", {})
            for group_id, binding in gsb.items():
                if "right_joystick active" in binding:
                    group_ids.append(group_id)
    
    return group_ids


def change_non_gyro_chord_activators(data: Dict[str, Any], layout_type: str, stats: Dict[str, int]) -> None:
    """Change chord activators in non-gyro trigger layers to add plain Turning Ramp Up."""
    groups = data.get("controller_mappings", {}).get("group", [])
    presets = data.get("controller_mappings", {}).get("preset", [])
    
    # Get the right_joystick group IDs for non-gyro trigger layers
    if layout_type == "default":
        trigger_layer_names = DEFAULT_NON_GYRO_TRIGGER_LAYERS
    else:
        # For alternative, find L1 and R1 layer preset IDs
        trigger_layer_names = []
        action_layers = data.get("controller_mappings", {}).get("action_layers", {})
        for preset_id, layer_data in action_layers.items():
            title = layer_data.get("title", "")
            if title in ["L1", "R1"]:
                trigger_layer_names.append(preset_id)
    
    # Find the right_joystick group IDs for these layers
    target_group_ids = set()
    for preset in presets:
        if preset.get("name") in trigger_layer_names:
            gsb = preset.get("group_source_bindings", {})
            for group_id, binding in gsb.items():
                if "right_joystick active" in binding:
                    target_group_ids.add(group_id)
    
    print(f"    Non-gyro trigger layer right_joystick groups: {target_group_ids}")
    
    # Find and modify these groups
    for group in groups:
        if group.get("id") not in target_group_ids:
            continue
        
        if group.get("mode") != "joystick_mouse":
            continue
        
        inputs = group.get("inputs", {})
        edge = inputs.get("edge", {})
        activators = edge.get("activators", {})
        chord = activators.get("chord", {})
        
        if not chord:
            continue
        
        bindings = chord.get("bindings", {})
        binding = bindings.get("binding", "")
        
        # Check if this is adding a gyro turning ramp up
        modified = False
        if isinstance(binding, str):
            for old, new in NON_GYRO_CHORD_CHANGES.items():
                if old in binding:
                    bindings["binding"] = binding.replace(old, new)
                    modified = True
                    stats["chord_activators_changed"] += 1
                    print(f"    Group {group.get('id')}: chord changed to add plain Turning Ramp Up")
        elif isinstance(binding, list):
            new_bindings = []
            for b in binding:
                new_b = b
                for old, new in NON_GYRO_CHORD_CHANGES.items():
                    if old in b:
                        new_b = b.replace(old, new)
                        modified = True
                        stats["chord_activators_changed"] += 1
                new_bindings.append(new_b)
            if modified:
                bindings["binding"] = new_bindings
                print(f"    Group {group.get('id')}: chord changed to add plain Turning Ramp Up")


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, int]:
    """Process a single JSON file."""
    print(f"\nProcessing: {file_path}")
    
    # Detect layout type
    layout_type = detect_layout_type(file_path)
    print(f"  Layout type: {layout_type}")
    
    # Load the file
    data = load_json_file(file_path)
    
    # Track statistics
    stats = {
        "titles_renamed": 0,
        "references_replaced": 0,
        "chord_activators_changed": 0
    }
    
    # Step 1: Rename layer titles
    print("  Step 1: Renaming layer titles...")
    rename_layer_titles(data, stats)
    
    # Step 2: Replace all references
    print("  Step 2: Replacing references...")
    data = replace_references_in_object(data, stats)
    
    # Step 3: Change non-gyro trigger layer chord activators
    print("  Step 3: Changing non-gyro trigger layer chord activators...")
    change_non_gyro_chord_activators(data, layout_type, stats)
    
    # Report results
    total_changes = sum(stats.values())
    if total_changes > 0:
        print(f"\n  Summary:")
        print(f"    Titles renamed: {stats['titles_renamed']}")
        print(f"    References replaced: {stats['references_replaced']}")
        print(f"    Chord activators changed: {stats['chord_activators_changed']}")
        
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
        description="Rename Chorded Ramp Up to (Gyro) Turning Ramp Up"
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
    print("Rename Chorded Ramp Up to (Gyro) Turning Ramp Up Script")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Rename 'Chorded Ramp Up 0/1' titles to '(Gyro) Turning Ramp Up 0/1'")
    print("  2. Update all {{Base::Chorded Ramp Up X}} references")
    print("  3. Change non-gyro trigger layers to add plain 'Turning Ramp Up' on chord")
    
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
        "total_titles_renamed": 0,
        "total_references_replaced": 0,
        "total_chord_changes": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        if sum(stats.values()) > 0:
            total_stats["files_modified"] += 1
            total_stats["total_titles_renamed"] += stats["titles_renamed"]
            total_stats["total_references_replaced"] += stats["references_replaced"]
            total_stats["total_chord_changes"] += stats["chord_activators_changed"]
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Total titles renamed: {total_stats['total_titles_renamed']}")
    print(f"Total references replaced: {total_stats['total_references_replaced']}")
    print(f"Total chord activators changed: {total_stats['total_chord_changes']}")
    
    if args.dry_run and total_stats["files_modified"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
