#!/usr/bin/env python3
"""
Script to replace old layer IDs with new IDs in Steam Controller layout JSON files.
Uses a two-pass approach to safely handle ID replacements.
"""

import json
import re
import os
from pathlib import Path

def load_id_mapping(mapping_file):
    """Load the old to new ID mapping from JSON file."""
    with open(mapping_file, 'r') as f:
        return json.load(f)

def create_reverse_mapping(id_mapping):
    """Create a reverse mapping from old_id to new_id for quick lookup."""
    reverse_map = {}
    for preset_id, data in id_mapping.items():
        if 'old_id' in data and 'new_id' in data:
            reverse_map[data['old_id']] = data['new_id']
    return reverse_map

def first_pass_replace(content, reverse_mapping):
    """
    First pass: Replace old_id with old_id + "_" + new_id
    This ensures we can safely identify and replace all instances.
    """
    print("Starting first pass: replacing old_id with old_id_new_id format...")
    
    # Pattern to match controller_action commands with layer IDs
    # Matches: controller_action (add_layer|remove_layer|hold_layer) <id> <rest>
    pattern = r'(controller_action\s+(?:add_layer|remove_layer|hold_layer)\s+)(\d+)(\s+\d+\s+\d+[,\s]*)'
    
    def replace_func(match):
        action_part = match.group(1)  # controller_action add_layer/remove_layer/hold_layer
        old_id = int(match.group(2))  # the layer ID
        rest = match.group(3)         # remaining parameters
        
        if old_id in reverse_mapping:
            new_id = reverse_mapping[old_id]
            # Replace with old_id_new_id format
            replacement = f"{action_part}{old_id}_{new_id}{rest}"
            print(f"  Replacing: {old_id} -> {old_id}_{new_id}")
            return replacement
        else:
            # No mapping found, keep as is
            print(f"  No mapping found for ID: {old_id}, keeping unchanged")
            return match.group(0)
    
    # Apply the replacement
    modified_content = re.sub(pattern, replace_func, content)
    
    print(f"First pass completed.")
    return modified_content

def second_pass_cleanup(content):
    """
    Second pass: Remove the prepended old_id + "_" part, keeping only the new_id
    """
    print("Starting second pass: removing prepended old_id_ prefix...")
    
    # Pattern to match the old_id_new_id format we created in first pass
    # Matches: controller_action (add_layer|remove_layer|hold_layer) <old_id>_<new_id> <rest>
    pattern = r'(controller_action\s+(?:add_layer|remove_layer|hold_layer)\s+)(\d+)_(\d+)(\s+\d+\s+\d+[,\s]*)'
    
    def replace_func(match):
        action_part = match.group(1)  # controller_action add_layer/remove_layer/hold_layer
        old_id = match.group(2)       # the old ID part
        new_id = match.group(3)       # the new ID part
        rest = match.group(4)         # remaining parameters
        
        # Keep only the new_id
        replacement = f"{action_part}{new_id}{rest}"
        print(f"  Final replacement: {old_id}_{new_id} -> {new_id}")
        return replacement
    
    # Apply the replacement
    modified_content = re.sub(pattern, replace_func, content)
    
    print(f"Second pass completed.")
    return modified_content

def process_json_file(input_file, output_file, id_mapping_file):
    """Process the JSON file through both passes."""
    print(f"Processing file: {input_file}")
    print(f"Using ID mapping from: {id_mapping_file}")
    print(f"Output will be saved to: {output_file}")
    print("-" * 60)
    
    # Load the ID mapping
    try:
        id_mapping = load_id_mapping(id_mapping_file)
        reverse_mapping = create_reverse_mapping(id_mapping)
        print(f"Loaded {len(reverse_mapping)} ID mappings")
    except Exception as e:
        print(f"Error loading ID mapping file: {e}")
        return False
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Successfully read input file ({len(content)} characters)")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return False
    
    # First pass: Replace with old_id_new_id format
    content = first_pass_replace(content, reverse_mapping)
    
    # Second pass: Remove the prepended old_id_ part
    content = second_pass_cleanup(content)
    
    # Write the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully wrote output file: {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False
    
    print("-" * 60)
    print("Processing completed successfully!")
    return True

def main():
    """Main function to run the script."""
    # File paths
    input_file = "neptune/universal-layout-default  hold-gyro  latest.json"
    id_mapping_file = "resources/old_to_new_ids.json"
    output_file = "neptune/universal-layout-default  hold-gyro  latest_updated.json"
    
    # Check if input files exist
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return
    
    if not os.path.exists(id_mapping_file):
        print(f"Error: ID mapping file not found: {id_mapping_file}")
        return
    
    # Process the file
    success = process_json_file(input_file, output_file, id_mapping_file)
    
    if success:
        print(f"\n✅ Successfully processed {input_file}")
        print(f"📁 Updated file saved as: {output_file}")
        print("\nYou can now review the changes and replace the original file if satisfied.")
    else:
        print(f"\n❌ Failed to process {input_file}")

if __name__ == "__main__":
    main() 