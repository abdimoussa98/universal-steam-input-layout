#!/usr/bin/env python3
"""
Populate Gyro Layer Inputs Script

This script populates the empty input groups in the "Gyro" layer (Preset_1000152)
with gyro variants of trigger and ramp up layer additions, mirroring the Base set's structure.

For Default Layout:
- Groups 12980, 12981 (triggers): Add (Gyro) L2, (Gyro) R2 on Full_Press click
- Group 12976 (joystick): Add (Gyro) Turning Ramp Up 0 on edge/Soft_Press with Gyro Off

For Alternative Layout:
- Group 12974 (switches): Add (Gyro) L1, (Gyro) R1 on bumper Full_Press
- Group 12976 (joystick): Add (Gyro) Turning Ramp Up 0 on edge/Soft_Press with Gyro Off

Usage:
    python3 populate_gyro_layer_inputs.py                    # Process all neptune/ JSON files
    python3 populate_gyro_layer_inputs.py file.json          # Process specific file
    python3 populate_gyro_layer_inputs.py --dry-run          # Preview changes without modifying
"""

import json
import sys
import os
import glob
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Set

# Gyro layer group IDs
GYRO_LAYER_GROUPS = {
    "trigger_left": "12980",
    "trigger_right": "12981",
    "switches": "12974",
    "joystick": "12976",
}

# Cleanup removals for trigger/bumper additions
CLEANUP_REMOVALS = [
    "controller_action remove_layer {{Base::Gyro Off}} 0 0, , ",
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


def is_alternative_layout(file_path: str) -> bool:
    """Check if the file is an alternative layout."""
    return "alternative" in os.path.basename(file_path).lower()


def create_trigger_click_input(layer_name: str) -> OrderedDict:
    """Create the click input structure for a trigger group (for triggers adding trigger layers)."""
    bindings = [f"controller_action add_layer {layer_name} 0 0, , "] + CLEANUP_REMOVALS
    
    return OrderedDict([
        ("click", OrderedDict([
            ("activators", OrderedDict([
                ("Full_Press", OrderedDict([
                    ("bindings", OrderedDict([
                        ("binding", bindings)
                    ])),
                    ("settings", OrderedDict([
                        ("hold_repeats", "1"),
                        ("interruptable", "0")
                    ]))
                ]))
            ])),
            ("disabled_activators", OrderedDict())
        ]))
    ])


def create_trigger_edge_input(layer_name: str) -> OrderedDict:
    """Create the edge input structure for a trigger group (for modifiers in alternative layout)."""
    # Modifier layers don't need cleanup removals, just add the layer
    return OrderedDict([
        ("edge", OrderedDict([
            ("activators", OrderedDict([
                ("Full_Press", OrderedDict([
                    ("bindings", OrderedDict([
                        ("binding", f"controller_action add_layer {layer_name} 0 0, , ")
                    ])),
                    ("settings", OrderedDict([
                        ("hold_repeats", "1"),
                        ("interruptable", "0")
                    ]))
                ]))
            ])),
            ("disabled_activators", OrderedDict())
        ]))
    ])


def create_bumper_inputs_full_press(left_layer: str, right_layer: str) -> OrderedDict:
    """Create the bumper input structures for triggers using Full_Press (with cleanup)."""
    left_bindings = [f"controller_action add_layer {left_layer} 0 0, , "] + CLEANUP_REMOVALS
    right_bindings = [f"controller_action add_layer {right_layer} 0 0, , "] + CLEANUP_REMOVALS
    
    return OrderedDict([
        ("left_bumper", OrderedDict([
            ("activators", OrderedDict([
                ("Full_Press", OrderedDict([
                    ("bindings", OrderedDict([
                        ("binding", left_bindings)
                    ])),
                    ("settings", OrderedDict([
                        ("hold_repeats", "1"),
                        ("interruptable", "0")
                    ]))
                ]))
            ])),
            ("disabled_activators", OrderedDict())
        ])),
        ("right_bumper", OrderedDict([
            ("activators", OrderedDict([
                ("Full_Press", OrderedDict([
                    ("bindings", OrderedDict([
                        ("binding", right_bindings)
                    ])),
                    ("settings", OrderedDict([
                        ("hold_repeats", "1"),
                        ("interruptable", "0")
                    ]))
                ]))
            ])),
            ("disabled_activators", OrderedDict())
        ]))
    ])


def create_bumper_inputs_chord(left_layer: str, right_layer: str) -> OrderedDict:
    """Create the bumper input structures for modifiers using chord activator."""
    # Modifiers use chord activator with chord_button: 1 for left, 2 for right
    return OrderedDict([
        ("left_bumper", OrderedDict([
            ("activators", OrderedDict([
                ("chord", OrderedDict([
                    ("bindings", OrderedDict([
                        ("binding", f"controller_action add_layer {left_layer} 0 0, , ")
                    ])),
                    ("settings", OrderedDict([
                        ("chord_button", "1"),
                        ("hold_repeats", "1"),
                        ("interruptable", "0")
                    ]))
                ]))
            ])),
            ("disabled_activators", OrderedDict())
        ])),
        ("right_bumper", OrderedDict([
            ("activators", OrderedDict([
                ("chord", OrderedDict([
                    ("bindings", OrderedDict([
                        ("binding", f"controller_action add_layer {right_layer} 0 0, , ")
                    ])),
                    ("settings", OrderedDict([
                        ("chord_button", "2"),
                        ("hold_repeats", "1"),
                        ("interruptable", "0")
                    ]))
                ]))
            ])),
            ("disabled_activators", OrderedDict())
        ]))
    ])


def create_joystick_edge_input() -> OrderedDict:
    """Create the edge input structure for a joystick group with Gyro Turning Ramp Up."""
    bindings = [
        "controller_action add_layer {{Base::Gyro Off}} 0 0, , ",
        "controller_action add_layer {{Base::(Gyro) Turning Ramp Up 0}} 0 0, , "
    ]
    
    return OrderedDict([
        ("edge", OrderedDict([
            ("activators", OrderedDict([
                ("Soft_Press", OrderedDict([
                    ("bindings", OrderedDict([
                        ("binding", bindings)
                    ])),
                    ("settings", OrderedDict([
                        ("hold_repeats", "1"),
                        ("haptic_intensity", "0"),
                        ("activation_threshold", "32255")
                    ]))
                ]))
            ])),
            ("disabled_activators", OrderedDict())
        ]))
    ])


def process_file(file_path: str, dry_run: bool = False) -> Dict[str, int]:
    """Process a single JSON file."""
    print(f"\nProcessing: {file_path}")
    
    # Determine layout type
    is_alt = is_alternative_layout(file_path)
    layout_type = "alternative" if is_alt else "default"
    print(f"  Layout type: {layout_type}")
    
    # Load the file
    data = load_json_file(file_path)
    
    # Get groups
    cm = data.get("controller_mappings", data)
    groups = cm.get("group", [])
    
    # Track statistics
    stats = {
        "groups_modified": 0
    }
    
    modified = False
    
    for group in groups:
        group_id = group.get("id")
        
        # === DEFAULT LAYOUT ===
        if not is_alt:
            # Trigger groups add (Gyro) L2 / (Gyro) R2 on click
            if group_id == GYRO_LAYER_GROUPS["trigger_left"]:
                if not group.get("inputs") or group.get("inputs") == {}:
                    print(f"  Populating group {group_id} (left trigger) with (Gyro) L2 binding")
                    group["inputs"] = create_trigger_click_input("{{Base::(Gyro) L2}}")
                    stats["groups_modified"] += 1
                    modified = True
            
            if group_id == GYRO_LAYER_GROUPS["trigger_right"]:
                if not group.get("inputs") or group.get("inputs") == {}:
                    print(f"  Populating group {group_id} (right trigger) with (Gyro) R2 binding")
                    group["inputs"] = create_trigger_click_input("{{Base::(Gyro) R2}}")
                    stats["groups_modified"] += 1
                    modified = True
            
            # Switches group adds (Gyro) L1: Modifier 0 / (Gyro) R1: Modifier 1 on bumpers (chord)
            if group_id == GYRO_LAYER_GROUPS["switches"]:
                if not group.get("inputs") or group.get("inputs") == {}:
                    print(f"  Populating group {group_id} (switches) with (Gyro) L1/R1 Modifier chord bindings")
                    group["inputs"] = create_bumper_inputs_chord(
                        "{{Base::(Gyro) L1: Modifier 0}}",
                        "{{Base::(Gyro) R1: Modifier 1}}"
                    )
                    stats["groups_modified"] += 1
                    modified = True
        
        # === ALTERNATIVE LAYOUT ===
        else:
            # Switches group adds (Gyro) L1 / (Gyro) R1 on bumpers (triggers in alternative)
            if group_id == GYRO_LAYER_GROUPS["switches"]:
                if not group.get("inputs") or group.get("inputs") == {}:
                    print(f"  Populating group {group_id} (switches) with (Gyro) L1/R1 trigger bindings")
                    group["inputs"] = create_bumper_inputs_full_press(
                        "{{Base::(Gyro) L1}}",
                        "{{Base::(Gyro) R1}}"
                    )
                    stats["groups_modified"] += 1
                    modified = True
            
            # Trigger groups add (Gyro) L2: Modifier 0 / (Gyro) R2: Modifier 1 on edge (modifiers in alternative)
            if group_id == GYRO_LAYER_GROUPS["trigger_left"]:
                if not group.get("inputs") or group.get("inputs") == {}:
                    print(f"  Populating group {group_id} (left trigger) with (Gyro) L2: Modifier 0 binding")
                    group["inputs"] = create_trigger_edge_input("{{Base::(Gyro) L2: Modifier 0}}")
                    stats["groups_modified"] += 1
                    modified = True
            
            if group_id == GYRO_LAYER_GROUPS["trigger_right"]:
                if not group.get("inputs") or group.get("inputs") == {}:
                    print(f"  Populating group {group_id} (right trigger) with (Gyro) R2: Modifier 1 binding")
                    group["inputs"] = create_trigger_edge_input("{{Base::(Gyro) R2: Modifier 1}}")
                    stats["groups_modified"] += 1
                    modified = True
        
        # === BOTH LAYOUTS ===
        # Process joystick group for both layouts
        if group_id == GYRO_LAYER_GROUPS["joystick"]:
            if not group.get("inputs") or group.get("inputs") == {}:
                print(f"  Populating group {group_id} (joystick) with (Gyro) Turning Ramp Up binding")
                group["inputs"] = create_joystick_edge_input()
                stats["groups_modified"] += 1
                modified = True
    
    # Report results
    if stats["groups_modified"] > 0:
        print(f"  Groups modified: {stats['groups_modified']}")
        
        if dry_run:
            print(f"  [DRY RUN] Would save changes to: {file_path}")
        else:
            save_json_file(file_path, data)
    else:
        print(f"  No changes needed (groups already populated or not found)")
    
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
        description="Populate Gyro layer inputs with gyro trigger and ramp up bindings"
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
    print("Populate Gyro Layer Inputs Script")
    print("=" * 70)
    print("\nThis script populates the Gyro layer's empty input groups:")
    print("\nDefault Layout:")
    print("  - Trigger groups: Add (Gyro) L2, (Gyro) R2 on click")
    print("  - Switches group: Add (Gyro) L1: Modifier 0, (Gyro) R1: Modifier 1 on bumpers")
    print("  - Joystick group: Add (Gyro) Turning Ramp Up 0 with Gyro Off")
    print("\nAlternative Layout:")
    print("  - Switches group: Add (Gyro) L1, (Gyro) R1 on bumpers (triggers)")
    print("  - Trigger groups: Add (Gyro) L2: Modifier 0, (Gyro) R2: Modifier 1 on edge")
    print("  - Joystick group: Add (Gyro) Turning Ramp Up 0 with Gyro Off")
    
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
        "total_groups_modified": 0
    }
    
    for file_path in files_to_process:
        stats = process_file(file_path, args.dry_run)
        total_stats["files_processed"] += 1
        if stats["groups_modified"] > 0:
            total_stats["files_modified"] += 1
            total_stats["total_groups_modified"] += stats["groups_modified"]
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files modified: {total_stats['files_modified']}")
    print(f"Total groups modified: {total_stats['total_groups_modified']}")
    
    if args.dry_run and total_stats["files_modified"] > 0:
        print("\n[DRY RUN] Run without --dry-run to apply changes.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
