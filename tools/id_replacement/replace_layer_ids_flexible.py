#!/usr/bin/env python3
"""
Flexible script to replace old layer IDs with new IDs in Steam Controller layout JSON files.
Uses a two-pass approach to safely handle ID replacements.
Accepts command-line arguments for file paths.
"""

import json
import re
import os
import argparse
import sys
from pathlib import Path

def load_id_mapping(mapping_file):
    """Load the old to new ID mapping from JSON file."""
    try:
        with open(mapping_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: ID mapping file not found: {mapping_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in ID mapping file: {e}")
        return None

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
    
    replacements_made = 0
    
    def replace_func(match):
        nonlocal replacements_made
        action_part = match.group(1)  # controller_action add_layer/remove_layer/hold_layer
        old_id = int(match.group(2))  # the layer ID
        rest = match.group(3)         # remaining parameters
        
        if old_id in reverse_mapping:
            new_id = reverse_mapping[old_id]
            # Replace with old_id_new_id format
            replacement = f"{action_part}{old_id}_{new_id}{rest}"
            print(f"  Replacing: {old_id} -> {old_id}_{new_id}")
            replacements_made += 1
            return replacement
        else:
            # No mapping found, keep as is
            print(f"  No mapping found for ID: {old_id}, keeping unchanged")
            return match.group(0)
    
    # Apply the replacement
    modified_content = re.sub(pattern, replace_func, content)
    
    print(f"First pass completed. {replacements_made} replacements made.")
    return modified_content

def second_pass_cleanup(content):
    """
    Second pass: Remove the prepended old_id + "_" part, keeping only the new_id
    """
    print("Starting second pass: removing prepended old_id_ prefix...")
    
    # Pattern to match the old_id_new_id format we created in first pass
    # Matches: controller_action (add_layer|remove_layer|hold_layer) <old_id>_<new_id> <rest>
    pattern = r'(controller_action\s+(?:add_layer|remove_layer|hold_layer)\s+)(\d+)_(\d+)(\s+\d+\s+\d+[,\s]*)'
    
    replacements_made = 0
    
    def replace_func(match):
        nonlocal replacements_made
        action_part = match.group(1)  # controller_action add_layer/remove_layer/hold_layer
        old_id = match.group(2)       # the old ID part
        new_id = match.group(3)       # the new ID part
        rest = match.group(4)         # remaining parameters
        
        # Keep only the new_id
        replacement = f"{action_part}{new_id}{rest}"
        print(f"  Final replacement: {old_id}_{new_id} -> {new_id}")
        replacements_made += 1
        return replacement
    
    # Apply the replacement
    modified_content = re.sub(pattern, replace_func, content)
    
    print(f"Second pass completed. {replacements_made} replacements made.")
    return modified_content

def process_json_file(input_file, output_file, id_mapping_file, dry_run=False):
    """Process the JSON file through both passes."""
    print(f"Processing file: {input_file}")
    print(f"Using ID mapping from: {id_mapping_file}")
    if dry_run:
        print("DRY RUN MODE - No files will be modified")
    else:
        print(f"Output will be saved to: {output_file}")
    print("-" * 60)
    
    # Load the ID mapping
    id_mapping = load_id_mapping(id_mapping_file)
    if id_mapping is None:
        return False
    
    reverse_mapping = create_reverse_mapping(id_mapping)
    print(f"Loaded {len(reverse_mapping)} ID mappings")
    
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
    
    if dry_run:
        print("DRY RUN MODE - Skipping file write")
        return True
    
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
    parser = argparse.ArgumentParser(
        description="Replace old layer IDs with new IDs in Steam Controller layout JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default files
  python3 replace_layer_ids_flexible.py
  
  # Specify custom files
  python3 replace_layer_ids_flexible.py -i input.json -m mapping.json -o output.json
  
  # Dry run to see what would be changed
  python3 replace_layer_ids_flexible.py --dry-run
  
  # Process alternative layout file
  python3 replace_layer_ids_flexible.py -i "neptune/universal-layout-alternative  hold-gyro  latest.json"
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        default="neptune/universal-layout-default  hold-gyro  latest.json",
        help='Input JSON file to process (default: neptune/universal-layout-default  hold-gyro  latest.json)'
    )
    
    parser.add_argument(
        '-m', '--mapping',
        default="resources/old_to_new_ids.json",
        help='ID mapping JSON file (default: resources/old_to_new_ids.json)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file (default: input_filename_updated.json)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without writing files'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Allow overwriting existing output file'
    )
    
    args = parser.parse_args()
    
    # Set default output filename if not specified
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_updated{input_path.suffix}")
    
    # Check if input files exist
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    if not os.path.exists(args.mapping):
        print(f"Error: ID mapping file not found: {args.mapping}")
        sys.exit(1)
    
    # Check if output file exists and handle overwrite
    if os.path.exists(args.output) and not args.dry_run and not args.overwrite:
        print(f"Error: Output file already exists: {args.output}")
        print("Use --overwrite to allow overwriting, or specify a different output file with -o")
        sys.exit(1)
    
    # Process the file
    success = process_json_file(args.input, args.output, args.mapping, args.dry_run)
    
    if success:
        if args.dry_run:
            print(f"\n✅ DRY RUN completed for {args.input}")
            print("Review the output above to see what would be changed.")
        else:
            print(f"\n✅ Successfully processed {args.input}")
            print(f"📁 Updated file saved as: {args.output}")
            print("\nYou can now review the changes and replace the original file if satisfied.")
    else:
        print(f"\n❌ Failed to process {args.input}")
        sys.exit(1)

if __name__ == "__main__":
    main() 