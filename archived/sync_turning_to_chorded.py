#!/usr/bin/env python3
"""
Sync Turning Ramp Up to Chorded Ramp Up Script

This script modifies Turning Ramp Up layers to match the controller action patterns
of Chorded Ramp Up layers (the "gold standard").

Key Changes:
1. Make trigger inputs EMPTY in Turning Ramp Up layers (like Chorded)
2. Add trigger layer removal to modifier inputs (like Chorded)

Default Layout (L2/R2 are triggers, L1/R1 are modifiers):
- Groups 412, 413 (L2/R2 triggers) in Turning Ramp Up 0: Make empty
- Groups 540, 541 (L2/R2 triggers) in Turning Ramp Up 1: Make empty
- Groups 414, 542 (L1/R1 switches): Add removal of L2, (Gyro) L2, R2, (Gyro) R2

Alternative Layout (L1/R1 are triggers, L2/R2 are modifiers):
- Groups 414, 542 (L1/R1 switches) in Turning Ramp Up: Make empty
- Groups 412, 413, 540, 541 (L2/R2 triggers): Add removal of L1, (Gyro) L1, R1, (Gyro) R1

Usage:
    python3 sync_turning_to_chorded.py                    # Process all neptune/ JSON files
    python3 sync_turning_to_chorded.py file.json          # Process specific file
    python3 sync_turning_to_chorded.py --dry-run          # Preview changes without modifying
"""

import json
import sys
import os
import glob
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Optional

# Group IDs for each layer
TURNING_RAMP_UP_0_GROUPS = {
    "button_diamond": "411",
    "left_trigger": "412",
    "right_trigger": "413",
    "switches": "414",
    "right_joystick": "423",
    "gyro": "554",
    "joystick": "737"
}

TURNING_RAMP_UP_1_GROUPS = {
    "button_diamond": "539",
    "left_trigger": "540",
    "right_trigger": "541",
    "switches": "542",
    "right_joystick": "551",
    "gyro": "555",
    "joystick": "738"
}

# Layers to remove based on layout type
DEFAULT_TRIGGER_LAYERS_TO_REMOVE = [
    "controller_action remove_layer {{Base::L2}} 0 0, , ",
    "controller_action remove_layer {{Base::(Gyro) L2}} 0 0, , ",
    "controller_action remove_layer {{Base::R2}} 0 0, , ",
    "controller_action remove_layer {{Base::(Gyro) R2}} 0 0, , "
]

ALTERNATIVE_TRIGGER_LAYERS_TO_REMOVE = [
    "controller_action remove_layer {{Base::L1}} 0 0, , ",
    "controller_action remove_layer {{Base::(Gyro) L1}} 0 0, , ",
    "controller_action remove_layer {{Base::R1}} 0 0, , ",
    "controller_action remove_layer {{Base::(Gyro) R1}} 0 0, , "
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


def detect_layout_type(file_path: str) -> str:
    """Detect if this is a default or alternative layout based on filename."""
    if "alternative" in file_path.lower():
        return "alternative"
    return "default"


def find_group_by_id(groups: List[Dict], group_id: str) -> Optional[Dict]:
    """Find a group by its ID."""
    for group in groups:
        if group.get("id") == group_id:
            return group
    return None


def make_trigger_empty(group: Dict, stats: Dict) -> bool:
    """Make a trigger group's click input empty."""
    if "inputs" not in group:
        return False
    
    inputs = group["inputs"]
    if "click" not in inputs:
        return False
    
    click = inputs["click"]
    if "activators" not in click:
        return False
    
    activators = click["activators"]
    if "Full_Press" not in activators:
        return False
    
    full_press = activators["Full_Press"]
    if "bindings" not in full_press:
        return False
    
    # Check if it's already empty
    bindings = full_press["bindings"]
    current_binding = bindings.get("binding", "")
    if isinstance(current_binding, str) and "empty_binding" in current_binding:
        return False
    if isinstance(current_binding, list) and len(current_binding) == 0:
        return False
    
    # Make it empty - remove the click input entirely to match Chorded style
    # Actually, looking at Chorded, the trigger groups just have empty inputs {}
    group["inputs"] = {}
    stats["triggers_emptied"] += 1
    return True


def make_switches_empty(group: Dict, stats: Dict) -> bool:
    """Make a switches group's bumper inputs empty."""
    if "inputs" not in group:
        return False
    
    inputs = group["inputs"]
    modified = False
    
    # Check if bumpers have content
    has_left = "left_bumper" in inputs and inputs["left_bumper"].get("activators", {})
    has_right = "right_bumper" in inputs and inputs["right_bumper"].get("activators", {})
    
    if has_left or has_right:
        # Make inputs empty
        group["inputs"] = {}
        stats["switches_emptied"] += 1
        modified = True
    
    return modified


def add_trigger_removals_to_switches(group: Dict, trigger_layers: List[str], stats: Dict) -> bool:
    """Add trigger layer removal commands to switches group bumper inputs."""
    if "inputs" not in group:
        return False
    
    inputs = group["inputs"]
    modified = False
    
    for bumper in ["left_bumper", "right_bumper"]:
        if bumper not in inputs:
            continue
        
        bumper_data = inputs[bumper]
        if "activators" not in bumper_data:
            continue
        
        activators = bumper_data["activators"]
        if "Full_Press" not in activators:
            continue
        
        full_press = activators["Full_Press"]
        if "bindings" not in full_press:
            continue
        
        bindings = full_press["bindings"]
        binding = bindings.get("binding", [])
        
        # Convert to list if string
        if isinstance(binding, str):
            binding = [binding]
        
        # Check if trigger removals already exist
        has_all_removals = all(
            any(removal in b for b in binding)
            for removal in trigger_layers
        )
        
        if has_all_removals:
            continue
        
        # Find the position after "remove Gyro Off" to insert trigger removals
        insert_index = None
        for i, b in enumerate(binding):
            if "remove_layer {{Base::Gyro Off}}" in b:
                insert_index = i + 1
                break
        
        if insert_index is None:
            # If no Gyro Off found, insert after the ramp up removals
            for i, b in enumerate(binding):
                if "remove_layer {{Base::Turning Ramp Up" in b:
                    insert_index = i + 1
            if insert_index is None:
                insert_index = 0
        
        # Insert the trigger layer removals
        for j, removal in enumerate(trigger_layers):
            if removal not in binding:
                binding.insert(insert_index + j, removal)
                modified = True
        
        bindings["binding"] = binding
    
    if modified:
        stats["switches_modified"] += 1
    
    return modified


def add_trigger_removals_to_triggers(group: Dict, trigger_layers: List[str], stats: Dict) -> bool:
    """Add trigger layer removal commands to trigger group click inputs."""
    if "inputs" not in group:
        return False
    
    inputs = group["inputs"]
    if "click" not in inputs:
        return False
    
    click = inputs["click"]
    if "activators" not in click:
        return False
    
    activators = click["activators"]
    if "Full_Press" not in activators:
        return False
    
    full_press = activators["Full_Press"]
    if "bindings" not in full_press:
        return False
    
    bindings = full_press["bindings"]
    binding = bindings.get("binding", [])
    
    # Convert to list if string
    if isinstance(binding, str):
        binding = [binding]
    
    # Check if trigger removals already exist
    has_all_removals = all(
        any(removal in b for b in binding)
        for removal in trigger_layers
    )
    
    if has_all_removals:
        return False
    
    # Find the position after "remove Gyro Off" to insert trigger removals
    insert_index = None
    for i, b in enumerate(binding):
        if "remove_layer {{Base::Gyro Off}}" in b:
            insert_index = i + 1
            break
    
    if insert_index is None:
        # If no Gyro Off found, insert after the ramp up removals
        for i, b in enumerate(binding):
            if "remove_layer {{Base::Turning Ramp Up" in b:
                insert_index = i + 1
        if insert_index is None:
            insert_index = 0
    
    # Insert the trigger layer removals
    modified = False
    for j, removal in enumerate(trigger_layers):
        if removal not in binding:
            binding.insert(insert_index + j, removal)
            modified = True
    
    if modified:
        bindings["binding"] = binding
        stats["triggers_modified"] += 1
    
    return modified


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, int]:
    """Process a single JSON file."""
    print(f"\nProcessing: {file_path}")
    
    # Detect layout type
    layout_type = detect_layout_type(file_path)
    print(f"  Layout type: {layout_type}")
    
    # Load the file
    data = load_json_file(file_path)
    
    # Get groups array
    groups = data.get("controller_mappings", {}).get("group", [])
    if not groups:
        print("  Warning: No groups found in file")
        return {"changes": 0}
    
    # Track statistics
    stats = {
        "triggers_emptied": 0,
        "switches_emptied": 0,
        "triggers_modified": 0,
        "switches_modified": 0
    }
    
    # Determine which groups to modify based on layout type
    if layout_type == "default":
        # Default: L2/R2 are triggers (make empty), L1/R1 are modifiers (add trigger removal)
        trigger_layers = DEFAULT_TRIGGER_LAYERS_TO_REMOVE
        
        # Turning Ramp Up 0
        for group_id in [TURNING_RAMP_UP_0_GROUPS["left_trigger"], TURNING_RAMP_UP_0_GROUPS["right_trigger"]]:
            group = find_group_by_id(groups, group_id)
            if group:
                make_trigger_empty(group, stats)
        
        group = find_group_by_id(groups, TURNING_RAMP_UP_0_GROUPS["switches"])
        if group:
            add_trigger_removals_to_switches(group, trigger_layers, stats)
        
        # Turning Ramp Up 1
        for group_id in [TURNING_RAMP_UP_1_GROUPS["left_trigger"], TURNING_RAMP_UP_1_GROUPS["right_trigger"]]:
            group = find_group_by_id(groups, group_id)
            if group:
                make_trigger_empty(group, stats)
        
        group = find_group_by_id(groups, TURNING_RAMP_UP_1_GROUPS["switches"])
        if group:
            add_trigger_removals_to_switches(group, trigger_layers, stats)
    
    else:  # alternative
        # Alternative: L1/R1 are triggers (make switches empty), L2/R2 are modifiers (add trigger removal)
        trigger_layers = ALTERNATIVE_TRIGGER_LAYERS_TO_REMOVE
        
        # Turning Ramp Up 0
        group = find_group_by_id(groups, TURNING_RAMP_UP_0_GROUPS["switches"])
        if group:
            make_switches_empty(group, stats)
        
        for group_id in [TURNING_RAMP_UP_0_GROUPS["left_trigger"], TURNING_RAMP_UP_0_GROUPS["right_trigger"]]:
            group = find_group_by_id(groups, group_id)
            if group:
                add_trigger_removals_to_triggers(group, trigger_layers, stats)
        
        # Turning Ramp Up 1
        group = find_group_by_id(groups, TURNING_RAMP_UP_1_GROUPS["switches"])
        if group:
            make_switches_empty(group, stats)
        
        for group_id in [TURNING_RAMP_UP_1_GROUPS["left_trigger"], TURNING_RAMP_UP_1_GROUPS["right_trigger"]]:
            group = find_group_by_id(groups, group_id)
            if group:
                add_trigger_removals_to_triggers(group, trigger_layers, stats)
    
    # Report results
    total_changes = sum(stats.values())
    if total_changes > 0:
        print(f"  Triggers emptied: {stats['triggers_emptied']}")
        print(f"  Switches emptied: {stats['switches_emptied']}")
        print(f"  Triggers modified (added removals): {stats['triggers_modified']}")
        print(f"  Switches modified (added removals): {stats['switches_modified']}")
        
        if dry_run:
            print(f"  [DRY RUN] Would save changes to: {file_path}")
        else:
            save_json_file(file_path, data)
    else:
        print(f"  No changes needed (already synced or not applicable)")
    
    return {"changes": total_changes, **stats}


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
        description="Sync Turning Ramp Up layers to match Chorded Ramp Up patterns"
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
    print("Sync Turning Ramp Up to Chorded Ramp Up Script")
    print("=" * 70)
    print("\nThis script modifies Turning Ramp Up layers to match Chorded patterns:")
    print("  - Makes trigger inputs EMPTY (like Chorded)")
    print("  - Adds trigger layer removal to modifier inputs (like Chorded)")
    
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
    total_changes = 0
    files_modified = 0
    
    for file_path in files_to_process:
        result = process_file(file_path, args.dry_run)
        if result["changes"] > 0:
            total_changes += result["changes"]
            files_modified += 1
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {len(files_to_process)}")
    print(f"Files modified: {files_modified}")
    print(f"Total changes made: {total_changes}")
    
    if args.dry_run and total_changes > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
