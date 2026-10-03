# Layer ID Replacement Script

This script (`replace_layer_ids.py`) is designed to safely replace old layer IDs with new IDs in Steam Controller layout JSON files. It uses a two-pass approach to ensure all instances are properly updated without conflicts.

## How It Works

### Two-Pass Approach

1. **First Pass**: Replaces all old IDs with a temporary format: `old_id_new_id`
   - This ensures we can safely identify and replace all instances
   - Example: `add_layer 78` becomes `add_layer 78_32`

2. **Second Pass**: Removes the prepended old ID part, keeping only the new ID
   - Example: `add_layer 78_32` becomes `add_layer 32`

### Why Two Passes?

This approach prevents issues where:
- Multiple replacements could interfere with each other
- Partial replacements could leave some instances unchanged
- Complex ID patterns could cause replacement conflicts

## Usage

```bash
python3 replace_layer_ids.py
```

### Configuration

The script is configured to work with these default file paths:
- **Input**: `neptune/universal-layout-default  hold-gyro  latest.json`
- **ID Mapping**: `resources/old_to_new_ids.json`
- **Output**: `neptune/universal-layout-default  hold-gyro  latest_updated.json`

### Customization

To use with different files, modify the paths in the `main()` function:

```python
input_file = "path/to/your/input.json"
id_mapping_file = "path/to/your/id_mapping.json"
output_file = "path/to/your/output.json"
```

## ID Mapping Format

The script expects the ID mapping file to have this structure:

```json
{
  "Preset_1000001": {
    "title": "Base",
    "old_id": 1,
    "new_id": 1
  },
  "Preset_1000060": {
    "title": "L1!R1: Modifier 2",
    "old_id": 56,
    "new_id": 9,
    "parent_set_name": "Preset_1000001"
  }
}
```

## What Gets Replaced

The script finds and replaces layer IDs in these binding patterns:
- `controller_action add_layer <id> <rest>`
- `controller_action remove_layer <id> <rest>`
- `controller_action hold_layer <id> <rest>`

Where `<id>` is the layer ID number and `<rest>` are the remaining parameters.

## Safety Features

- **Backup**: Original file is never modified
- **Validation**: Checks file existence before processing
- **Error Handling**: Graceful error handling with informative messages
- **Progress Tracking**: Shows each replacement as it happens

## Example Output

```
Processing file: neptune/universal-layout-default  hold-gyro  latest.json
Using ID mapping from: resources/old_to_new_ids.json
Output will be saved to: neptune/universal-layout-default  hold-gyro  latest_updated.json
------------------------------------------------------------
Loaded 123 ID mappings
Successfully read input file (42020 characters)
Starting first pass: replacing old_id with old_id_new_id format...
  Replacing: 78 -> 78_32
  Replacing: 5 -> 5_5
  Replacing: 6 -> 6_6
First pass completed.
Starting second pass: removing prepended old_id_ prefix...
  Final replacement: 78_32 -> 32
  Final replacement: 5_5 -> 5
  Final replacement: 6_6 -> 6
Second pass completed.
Successfully wrote output file: neptune/universal-layout-default  hold-gyro  latest_updated.json
------------------------------------------------------------
Processing completed successfully!
```

## Verification

After running the script, you can:
1. Review the output file to ensure all replacements are correct
2. Compare specific lines between original and updated files
3. Use grep to search for specific ID patterns

## Troubleshooting

- **File not found**: Check file paths in the script
- **Permission errors**: Ensure write permissions for output directory
- **JSON parsing errors**: Verify the ID mapping file is valid JSON
- **No replacements**: Check if the ID mapping contains the expected old_id values

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
- Read access to input JSON file
- Write access to output directory 