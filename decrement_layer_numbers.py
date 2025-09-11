#!/usr/bin/env python3
"""
Script to find all values matching the regex `_layer [0-9]+ 0 0` 
and decrement the captured number by 3.

Usage:
    python decrement_layer_numbers.py <input_file> [output_file]
    
If output_file is not specified, the input file will be modified in place.
"""

import re
import sys
import os
from typing import List, Tuple

def find_and_replace_layer_numbers(content: str, decrement_by: int = 3) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Find all layer number patterns and decrement them by the specified amount.
    
    Args:
        content: The file content to process
        decrement_by: Amount to decrement the layer numbers by (default: 3)
    
    Returns:
        Tuple of (modified_content, list_of_changes)
    """
    # Pattern to match "_layer [number] 0 0" where number is captured
    pattern = r'_layer (\d+) 0 0'
    
    changes = []
    
    def replace_func(match):
        original_number = int(match.group(1))
        new_number = original_number - decrement_by
        
        # Ensure the number doesn't go below 0
        if new_number < 0:
            new_number = 0
            
        old_text = match.group(0)
        new_text = f'_layer {new_number} 0 0'
        
        changes.append((old_text, new_text))
        return new_text
    
    # Replace all matches
    modified_content = re.sub(pattern, replace_func, content)
    
    return modified_content, changes

def process_file(input_file: str, output_file: str = None, decrement_by: int = 3):
    """
    Process a file to decrement layer numbers.
    
    Args:
        input_file: Path to the input file
        output_file: Path to the output file (if None, modifies input file in place)
        decrement_by: Amount to decrement layer numbers by
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return False
    
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Processing file: {input_file}")
        print(f"Decrementing layer numbers by: {decrement_by}")
        
        # Process the content
        modified_content, changes = find_and_replace_layer_numbers(content, decrement_by)
        
        if not changes:
            print("No layer number patterns found matching '_layer [0-9]+ 0 0'")
            return True
        
        print(f"Found {len(changes)} layer number patterns to modify:")
        for old_text, new_text in changes:
            print(f"  {old_text} -> {new_text}")
        
        # Determine output file
        if output_file is None:
            output_file = input_file
        
        # Write the modified content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        if output_file == input_file:
            print(f"Successfully modified file in place: {input_file}")
        else:
            print(f"Successfully wrote modified content to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python decrement_layer_numbers.py <input_file> [output_file]")
        print("       python decrement_layer_numbers.py <input_file> [--decrement N] [output_file]")
        print("\nExamples:")
        print("  python decrement_layer_numbers.py file.vdf")
        print("  python decrement_layer_numbers.py file.vdf output.vdf")
        print("  python decrement_layer_numbers.py file.vdf --decrement 5 output.vdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    decrement_by = 3
    
    # Parse arguments
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--decrement':
            if i + 1 < len(args):
                try:
                    decrement_by = int(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"Error: Invalid decrement value '{args[i + 1]}'. Must be an integer.")
                    sys.exit(1)
            else:
                print("Error: --decrement requires a value")
                sys.exit(1)
        else:
            if output_file is None:
                output_file = args[i]
            i += 1
    
    # Process the file
    success = process_file(input_file, output_file, decrement_by)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
