#!/usr/bin/env python3
"""
Convert Runtime IDs to Titles (and vice versa) - Single Command

This script converts between runtime IDs and human-readable titles in Steam Input
layout JSON files. It generates the lookup internally from the file's own
actions/action_layers blocks - no separate lookup file needed.

Modes:
- to-titles: Replace numeric runtime IDs with readable titles
  e.g., "controller_action add_layer 5 0 0" -> "controller_action add_layer {{L2}} 0 0"

- to-ids: Replace titles back to numeric runtime IDs
  e.g., "controller_action add_layer {{L2}} 0 0" -> "controller_action add_layer 5 0 0"

Usage:
    python convert_runtime_ids.py <mode> <json_file> [--output <file>]

Examples:
    # Convert IDs to titles (modifies file in place)
    python convert_runtime_ids.py to-titles layout.json
    
    # Convert titles back to IDs (modifies file in place)
    python convert_runtime_ids.py to-ids layout.json
    
    # Output to a different file instead
    python convert_runtime_ids.py to-titles layout.json -o layout_readable.json
"""

import json
import sys
import os
import re
import argparse
from collections import OrderedDict
from typing import Dict, Any, List, Tuple


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


def load_text_file(file_path: str) -> str:
    """Load a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)


def save_file(file_path: str, content: str) -> None:
    """Save content to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved to: {file_path}")


def generate_lookup(layout_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate runtime ID lookup from the layout's actions and action_layers.
    
    Returns a dict with:
    - id_to_title: {runtime_id: full_title}
    - title_to_id: {full_title: runtime_id}
    - detailed: list of all entries with metadata
    """
    cm = layout_data.get("controller_mappings", {})
    actions = cm.get("actions", OrderedDict())
    action_layers = cm.get("action_layers", OrderedDict())
    
    detailed = []
    id_to_title = {}
    title_to_id = {}
    runtime_id = 1
    
    # Action sets first
    for preset_id, data in actions.items():
        title = data.get("title", "Unknown")
        detailed.append({
            "runtime_id": runtime_id,
            "preset_id": preset_id,
            "title": title,
            "type": "action_set",
            "parent_set": None
        })
        id_to_title[str(runtime_id)] = title
        title_to_id[title] = runtime_id
        runtime_id += 1
    
    # Build parent title map
    action_set_titles = {pid: data.get("title", "Unknown") for pid, data in actions.items()}
    
    # Action layers next
    for preset_id, data in action_layers.items():
        title = data.get("title", "Unknown")
        parent_preset_id = data.get("parent_set_name")
        parent_title = action_set_titles.get(parent_preset_id, parent_preset_id)
        
        # Full title includes parent for disambiguation
        full_title = f"{parent_title}::{title}"
        
        detailed.append({
            "runtime_id": runtime_id,
            "preset_id": preset_id,
            "title": title,
            "full_title": full_title,
            "type": "action_layer",
            "parent_set": parent_title
        })
        id_to_title[str(runtime_id)] = full_title
        title_to_id[full_title] = runtime_id
        runtime_id += 1
    
    return {
        "id_to_title": id_to_title,
        "title_to_id": title_to_id,
        "detailed": detailed
    }


def ids_to_titles(content: str, lookup: Dict[str, Any]) -> Tuple[str, int]:
    """Replace runtime IDs with human-readable titles using two-pass replacement."""
    id_to_title = lookup["id_to_title"]
    
    result = content
    total_replacements = 0
    
    # Commands that use runtime IDs
    commands = ['CHANGE_PRESET', 'add_layer', 'remove_layer', 'hold_layer']
    
    # PASS 1: Replace IDs with placeholders (sort descending to avoid partial matches)
    sorted_ids = sorted(id_to_title.keys(), key=lambda x: int(x), reverse=True)
    
    placeholders = {}
    for rid in sorted_ids:
        title = id_to_title[rid]
        placeholder = f"__TITLE_PLACEHOLDER_{rid}__"
        placeholders[placeholder] = f"{{{{{title}}}}}"  # {{Title}} format
        
        for cmd in commands:
            pattern = rf'(controller_action {cmd} ){rid}( \d+ \d+)'
            count = len(re.findall(pattern, result))
            if count > 0:
                result = re.sub(pattern, rf'\g<1>{placeholder}\g<2>', result)
                total_replacements += count
    
    # PASS 2: Replace placeholders with actual titles
    for placeholder, title in placeholders.items():
        result = result.replace(placeholder, title)
    
    return result, total_replacements


def titles_to_ids(content: str, lookup: Dict[str, Any]) -> Tuple[str, int]:
    """Replace human-readable titles back to runtime IDs."""
    title_to_id = lookup["title_to_id"]
    
    result = content
    total_replacements = 0
    
    # Commands that use runtime IDs
    commands = ['CHANGE_PRESET', 'add_layer', 'remove_layer', 'hold_layer']
    
    for cmd in commands:
        # Pattern to find {{Title}} or {{Parent::Title}} in commands
        pattern = rf'(controller_action {cmd} )\{{\{{([^}}]+)\}}\}}( \d+ \d+)'
        
        def replace_func(match):
            nonlocal total_replacements
            prefix = match.group(1)
            title = match.group(2)
            suffix = match.group(3)
            
            if title in title_to_id:
                total_replacements += 1
                return f"{prefix}{title_to_id[title]}{suffix}"
            else:
                print(f"  Warning: Could not find runtime ID for '{title}'")
                return match.group(0)
        
        result = re.sub(pattern, replace_func, result)
    
    return result, total_replacements


def main():
    parser = argparse.ArgumentParser(
        description="Convert runtime IDs to/from titles in Steam Input layout files"
    )
    parser.add_argument(
        "mode",
        choices=["to-titles", "to-ids"],
        help="Conversion mode: to-titles (IDs->titles) or to-ids (titles->IDs)"
    )
    parser.add_argument("json_file", help="Input layout JSON file")
    parser.add_argument(
        "--output", "-o",
        help="Output to a different file instead of modifying in place"
    )
    
    args = parser.parse_args()
    
    # Load the JSON to generate lookup
    print(f"Loading: {args.json_file}")
    layout_data = load_json_file(args.json_file)
    
    # Generate lookup from the file itself
    lookup = generate_lookup(layout_data)
    action_sets = sum(1 for i in lookup["detailed"] if i["type"] == "action_set")
    layers = sum(1 for i in lookup["detailed"] if i["type"] == "action_layer")
    print(f"Found {action_sets} action sets, {layers} layers")
    
    # Load file as text for replacement (preserves formatting)
    content = load_text_file(args.json_file)
    
    # Perform conversion
    if args.mode == "to-titles":
        result, count = ids_to_titles(content, lookup)
        print(f"Converted {count} runtime IDs to titles")
    else:
        result, count = titles_to_ids(content, lookup)
        print(f"Converted {count} titles to runtime IDs")
    
    # Determine output path (default: in-place)
    output_path = args.output if args.output else args.json_file
    
    # Save result
    save_file(output_path, result)
    print("Done!")


if __name__ == "__main__":
    main()
