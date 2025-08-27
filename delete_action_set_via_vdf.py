import sys
import re

def extract_block(text, start_index):
    """
    Extract and return the block of text starting at the given opening brace '{',
    including any nested braces.

    Returns a tuple (block, end_index) where block is the extracted text (including
    the outer braces) and end_index is the position just after the block.
    If no matching closing brace is found, returns (None, len(text)).
    """
    brace_count = 0
    for i in range(start_index, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return text[start_index:i+1], i+1
    return None, len(text)

def delete_blocks_by_name(text, block_name):
    """
    Delete all blocks in the text that start with the given block name.

    A block is defined by a key line that contains the block name (in quotes),
    optionally preceded by whitespace, followed immediately by an opening brace '{'.
    
    Returns the modified text with those blocks removed.
    """
    # Build a regex to match the block name (in quotes) at the beginning of a line
    # followed by optional whitespace and an opening brace.
    pattern = re.compile(r'(?m)^\s*"' + re.escape(block_name) + r'"\s*\{')
    removals = []

    for match in pattern.finditer(text):
        # Find the position of the opening brace within the matched text.
        brace_match = re.search(r'\{', match.group())
        if brace_match:
            block_start = match.start() + brace_match.start()
            block, end_index = extract_block(text, block_start)
            if block is not None:
                # Save the range to remove. We remove from the start of the match.
                removals.append((match.start(), end_index))
    
    # Remove the blocks in reverse order so that earlier deletions don't affect later indices.
    new_text = text
    for start, end in sorted(removals, reverse=True):
        new_text = new_text[:start] + new_text[end:]
    return new_text

def delete_action_set_from_vdf_text(vdf_text, action_set_id):
    """
    Demonstration: Delete blocks by name from the VDF text.
    
    In this example, we'll delete all blocks with the name "group".
    (You can easily change "group" to any other block name.)
    	"action_layers"
	{
		"Preset_1000015"
		{
			"title"		"L2"
			"legacy_set"		"1"
			"set_layer"		"1"
			"parent_set_name"		"Preset_1000014"
		}
        	"preset"
	{
		"id"		"0"
		"name"		"Preset_1000001"
		"group_source_bindings"
		{
			"10"		"switch active"
			"126"		"gyro inactive"
			"202"		"gyro inactive"
			"576"		"gyro active"
			"11"		"button_diamond active"
			"86"		"button_diamond inactive modeshift"
			"12"		"joystick active"
			"13"		"left_trigger active"
			"14"		"right_trigger active"
			"15"		"right_joystick active"
			"212"		"right_joystick inactive modeshift"
			"16"		"dpad active"
			"83"		"left_trackpad inactive"
			"84"		"left_trackpad inactive"
			"190"		"left_trackpad active"
			"194"		"left_trackpad inactive"
			"245"		"left_trackpad inactive"
			"246"		"left_trackpad inactive modeshift"
			"82"		"right_trackpad inactive"
			"189"		"right_trackpad inactive"
			"193"		"right_trackpad inactive"
			"195"		"right_trackpad inactive"
			"561"		"right_trackpad inactive"
			"562"		"right_trackpad active"
		}
	}
    """
    # within the actions block delete the block that begins with action_set_id in quotes
    # check action_layers block for blocks that contain parent_set_name that is equal to action_set_id
    # store the action_layers id as action_layers_id and look for preset block with "id" equal to action_layers_id
    # within the preset block group_source_bindings contains a list of group block ids "[0-9]+"
    # delete all group block that contain those ids

    # Delete "group" blocks
    modified_text = delete_blocks_by_name(vdf_text, "group")
    print("Deleted all 'group' blocks.")
    
    # (You could add additional deletion logic for action sets, action layers, etc. here.)
    return modified_text

def main():
    if len(sys.argv) != 3:
        print("Usage: python delete_action_set.py <input_file.vdf> <action_set_id>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    action_set_id = sys.argv[2]
    
    with open(input_file, 'r') as f:
        vdf_text = f.read()
    
    modified_vdf_text = delete_action_set_from_vdf_text(vdf_text, action_set_id)
    
    output_file = input_file + ".modified.vdf"
    with open(output_file, 'w') as f:
        f.write(modified_vdf_text)
    
    print(f"Modified VDF saved to {output_file}")

if __name__ == "__main__":
    main()
