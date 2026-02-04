#!/usr/bin/env python3
"""
Clean Trigger and Ramp Up Additions Script

This script ensures:
1. When trigger layers are added in the Base set, we also remove Gyro Off and all Turning Ramp Up variants
2. When Turning Ramp Up is added on stick deflect in the Base set, we also add Gyro Off

Usage:
    python3 clean_trigger_and_rampup_additions.py                    # Process all neptune/ JSON files
    python3 clean_trigger_and_rampup_additions.py file.json          # Process specific file
    python3 clean_trigger_and_rampup_additions.py --dry-run          # Preview changes without modifying
"""

import json
import sys
import os
import glob
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Set, Optional

# Trigger layers for default layout (L2/R2 as triggers)
DEFAULT_TRIGGER_LAYERS = [
    "{{Base::L2}}",
    "{{Base::R2}}",
    "{{Base::(Gyro) L2}}",
    "{{Base::(Gyro) R2}}",
]

# Trigger layers for alternative layout (L1/R1 as triggers)
ALTERNATIVE_TRIGGER_LAYERS = [
    "{{Base::L1}}",
    "{{Base::R1}}",
    "{{Base::(Gyro) L1}}",
    "{{Base::(Gyro) R1}}",
]

# All Turning Ramp Up variants
RAMP_UP_VARIANTS = [
    "{{Base::Turning Ramp Up 0}}",
    "{{Base::Turning Ramp Up 1}}",
    "{{Base::(Gyro) Turning Ramp Up 0}}",
    "{{Base::(Gyro) Turning Ramp Up 1}}",
]

GYRO_OFF_LAYER = "{{Base::Gyro Off}}"

# Removal commands to add when adding trigger layers
def get_trigger_cleanup_removals() -> List[str]:
    """Get the removal commands to add when adding trigger layers."""
    removals = []
    # Remove Gyro Off
    removals.append(f"controller_action remove_layer {GYRO_OFF_LAYER} 0 0, , ")
    # Remove all Ramp Up variants
    for variant in RAMP_UP_VARIANTS:
        removals.append(f"controller_action remove_layer {variant} 0 0, , ")
    return removals

# Add Gyro Off command
GYRO_OFF_ADD = f"controller_action add_layer {GYRO_OFF_LAYER} 0 0, , "


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


def contains_trigger_layer_add(binding: str, trigger_layers: List[str]) -> bool:
    """Check if a binding adds a trigger layer."""
    for layer in trigger_layers:
        if f"controller_action add_layer {layer}" in binding:
            return True
    return False


def contains_ramp_up_add(binding: str) -> bool:
    """Check if a binding adds a Turning Ramp Up layer."""
    for variant in RAMP_UP_VARIANTS:
        if f"controller_action add_layer {variant}" in binding:
            return True
    return False


def get_base_preset_groups(data: Dict) -> Set[str]:
    """Get the group IDs that belong to the Base preset."""
    base_groups = set()
    
    # Data is nested under controller_mappings
    cm = data.get("controller_mappings", data)
    
    # Find preset section (singular, not plural)
    presets = cm.get("preset", [])
    for preset in presets:
        if preset.get("name") == "Preset_1000001":  # Base preset
            group_bindings = preset.get("group_source_bindings", {})
            for group_id in group_bindings.keys():
                base_groups.add(group_id)
            break
    
    return base_groups


def binding_list_contains(bindings: List[str], action: str) -> bool:
    """Check if a binding list already contains a specific action."""
    action_normalized = action.strip()
    for b in bindings:
        if isinstance(b, str) and action_normalized in b:
            return True
    return False


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


def process_binding_for_trigger_add(
    binding_value: Any,
    trigger_layers: List[str],
    stats: Dict[str, int]
) -> Tuple[Any, bool]:
    """
    Process a binding to add cleanup when adding trigger layers.
    """
    cleanup_removals = get_trigger_cleanup_removals()
    
    if isinstance(binding_value, str):
        if contains_trigger_layer_add(binding_value, trigger_layers):
            # Convert to array with cleanup actions first
            new_bindings = list(cleanup_removals)
            new_bindings.append(binding_value)
            new_bindings = remove_duplicates_preserve_order(new_bindings)
            stats["trigger_adds_modified"] += 1
            return new_bindings, True
        return binding_value, False
    
    elif isinstance(binding_value, list):
        has_trigger_add = any(
            contains_trigger_layer_add(b, trigger_layers)
            for b in binding_value if isinstance(b, str)
        )
        
        if not has_trigger_add:
            return binding_value, False
        
        # Check what's missing
        new_bindings = list(binding_value)
        modified = False
        
        for removal in cleanup_removals:
            if not binding_list_contains(new_bindings, removal.strip().rstrip(", , ")):
                # Insert at beginning
                new_bindings.insert(0, removal)
                modified = True
        
        if modified:
            new_bindings = remove_duplicates_preserve_order(new_bindings)
            stats["trigger_adds_modified"] += 1
        
        return new_bindings, modified
    
    return binding_value, False


def process_binding_for_rampup_add(
    binding_value: Any,
    stats: Dict[str, int]
) -> Tuple[Any, bool]:
    """
    Process a binding to add Gyro Off when adding Turning Ramp Up.
    """
    if isinstance(binding_value, str):
        if contains_ramp_up_add(binding_value):
            # Check if Gyro Off add is already there
            if f"add_layer {GYRO_OFF_LAYER}" in binding_value:
                return binding_value, False
            # Convert to array with Gyro Off add
            new_bindings = [GYRO_OFF_ADD, binding_value]
            stats["rampup_adds_modified"] += 1
            return new_bindings, True
        return binding_value, False
    
    elif isinstance(binding_value, list):
        has_ramp_up_add = any(
            contains_ramp_up_add(b)
            for b in binding_value if isinstance(b, str)
        )
        
        if not has_ramp_up_add:
            return binding_value, False
        
        # Check if Gyro Off add is already there
        has_gyro_off_add = any(
            f"add_layer {GYRO_OFF_LAYER}" in b
            for b in binding_value if isinstance(b, str)
        )
        
        if has_gyro_off_add:
            return binding_value, False
        
        # Add Gyro Off add at the beginning
        new_bindings = [GYRO_OFF_ADD] + list(binding_value)
        new_bindings = remove_duplicates_preserve_order(new_bindings)
        stats["rampup_adds_modified"] += 1
        return new_bindings, True
    
    return binding_value, False


def is_edge_soft_press_in_base_joystick(
    obj: Dict,
    group_id: Optional[str],
    base_groups: Set[str],
    path: List[str]
) -> bool:
    """Check if we're in an edge/Soft_Press activator in a Base set joystick group."""
    # Check if the group is in Base set
    if group_id and group_id not in base_groups:
        return False
    
    # Check if the path indicates edge -> Soft_Press
    path_str = "/".join(path)
    return "edge" in path_str and "Soft_Press" in path_str


def is_trigger_click_in_base(
    group_id: Optional[str],
    base_groups: Set[str],
    path: List[str],
    group_mode: Optional[str]
) -> bool:
    """Check if we're in a click activator for a trigger group in Base set."""
    if group_id and group_id not in base_groups:
        return False
    
    # Check if this is a trigger mode group
    if group_mode != "trigger":
        return False
    
    # Check if the path indicates click
    path_str = "/".join(path)
    return "click" in path_str


def process_activator_for_trigger(
    activator: Any,
    trigger_layers: List[str],
    stats: Dict[str, int]
) -> bool:
    """Process a single activator for trigger layer additions."""
    modified = False
    if isinstance(activator, dict):
        bindings_obj = activator.get("bindings", {})
        if "binding" in bindings_obj:
            new_binding, was_modified = process_binding_for_trigger_add(
                bindings_obj["binding"],
                trigger_layers,
                stats
            )
            if was_modified:
                bindings_obj["binding"] = new_binding
                modified = True
    elif isinstance(activator, list):
        for act in activator:
            if isinstance(act, dict):
                bindings_obj = act.get("bindings", {})
                if "binding" in bindings_obj:
                    new_binding, was_modified = process_binding_for_trigger_add(
                        bindings_obj["binding"],
                        trigger_layers,
                        stats
                    )
                    if was_modified:
                        bindings_obj["binding"] = new_binding
                        modified = True
    return modified


def process_groups(
    groups: List[Dict],
    base_groups: Set[str],
    trigger_layers: List[str],
    stats: Dict[str, int]
) -> bool:
    """Process groups array and modify bindings as needed."""
    modified = False
    
    for group in groups:
        group_id = group.get("id")
        group_mode = group.get("mode")
        
        inputs = group.get("inputs", {})
        
        # Skip if not a base group
        if group_id not in base_groups:
            continue
        
        # Process trigger click bindings (for default layout - trigger mode)
        if group_mode == "trigger":
            click_input = inputs.get("click", {})
            activators = click_input.get("activators", {})
            
            for activator_name, activator in activators.items():
                if process_activator_for_trigger(activator, trigger_layers, stats):
                    modified = True
        
        # Process switches mode groups for bumper inputs (for alternative layout)
        if group_mode == "switches":
            # Check left_bumper and right_bumper inputs
            for bumper_name in ["left_bumper", "right_bumper"]:
                bumper_input = inputs.get(bumper_name, {})
                activators = bumper_input.get("activators", {})
                
                for activator_name, activator in activators.items():
                    if process_activator_for_trigger(activator, trigger_layers, stats):
                        modified = True
        
        # Process edge/Soft_Press bindings for joystick groups (for adding Ramp Up)
        if group_mode in ["joystick_mouse", "joystick_move"]:
            edge_input = inputs.get("edge", {})
            activators = edge_input.get("activators", {})
            
            soft_press = activators.get("Soft_Press")
            if isinstance(soft_press, dict):
                bindings_obj = soft_press.get("bindings", {})
                if "binding" in bindings_obj:
                    new_binding, was_modified = process_binding_for_rampup_add(
                        bindings_obj["binding"],
                        stats
                    )
                    if was_modified:
                        bindings_obj["binding"] = new_binding
                        modified = True
            elif isinstance(soft_press, list):
                for sp in soft_press:
                    if isinstance(sp, dict):
                        bindings_obj = sp.get("bindings", {})
                        if "binding" in bindings_obj:
                            new_binding, was_modified = process_binding_for_rampup_add(
                                bindings_obj["binding"],
                                stats
                            )
                            if was_modified:
                                bindings_obj["binding"] = new_binding
                                modified = True
    
    return modified


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, int]:
    """Process a single JSON file."""
    print(f"\nProcessing: {file_path}")
    
    # Determine layout type
    is_alt = is_alternative_layout(file_path)
    trigger_layers = ALTERNATIVE_TRIGGER_LAYERS if is_alt else DEFAULT_TRIGGER_LAYERS
    layout_type = "alternative" if is_alt else "default"
    print(f"  Layout type: {layout_type}")
    print(f"  Trigger layers: {', '.join([l.split('::')[1].rstrip('}}') for l in trigger_layers])}")
    
    # Load the file
    data = load_json_file(file_path)
    
    # Get Base preset groups
    base_groups = get_base_preset_groups(data)
    print(f"  Base preset groups: {len(base_groups)} groups")
    
    # Track statistics
    stats = {
        "trigger_adds_modified": 0,
        "rampup_adds_modified": 0
    }
    
    # Process groups (nested under controller_mappings, key is "group" singular)
    cm = data.get("controller_mappings", data)
    groups = cm.get("group", [])
    modified = process_groups(groups, base_groups, trigger_layers, stats)
    
    # Report results
    total_changes = stats["trigger_adds_modified"] + stats["rampup_adds_modified"]
    if total_changes > 0:
        print(f"  Trigger add bindings modified: {stats['trigger_adds_modified']}")
        print(f"  Ramp Up add bindings modified: {stats['rampup_adds_modified']}")
        
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
        description="Clean up trigger and Ramp Up layer additions in Base set"
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
    print("Clean Trigger and Ramp Up Additions Script")
    print("=" * 70)
    print("\nThis script ensures:")
    print("1. When trigger layers are ADDED in Base set:")
    print("   - Remove Gyro Off")
    print("   - Remove all Turning Ramp Up variants")
    print("2. When Turning Ramp Up is ADDED on stick deflect in Base set:")
    print("   - Also add Gyro Off")
    
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
        "total_trigger_adds_modified": 0,
        "total_rampup_adds_modified": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        changes = stats["trigger_adds_modified"] + stats["rampup_adds_modified"]
        if changes > 0:
            total_stats["files_modified"] += 1
            total_stats["total_trigger_adds_modified"] += stats["trigger_adds_modified"]
            total_stats["total_rampup_adds_modified"] += stats["rampup_adds_modified"]
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Total trigger add bindings modified: {total_stats['total_trigger_adds_modified']}")
    print(f"Total Ramp Up add bindings modified: {total_stats['total_rampup_adds_modified']}")
    
    if args.dry_run and total_stats["files_modified"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
