# Default 90.2: blocking in every layer

Source: [neptune/single-set-default_hold-gyro_latest.json](../../neptune/single-set-default_hold-gyro_latest.json); SHA-256 `78a128016a8cb7746a5785df68880923b87e1ad9b96741126fae4464be62039b`.

Read [AUDIT.md](AUDIT.md) for the purpose of each blocking family and the author's historical crash workaround. This catalog records every active source and activator, including ordinary outputs and the layers with zero explicit empties. It does not classify all ordinary outputs as intentional blocks. All inactive/unreferenced/conditional entries and source settings are in the CSV inventories.

**Types:** pure empties suppress an input/event; chord guards protect cleanup from firing during valid holds; mixed arrays still execute their real actions; output/mode replacements may intercept lower layer changes. A group with mode `disabled` is a source block; a group with no explicit inputs is not counted as one. The CSV contains complete payloads and sibling activators.

**Inheritance limit:** active source membership and explicit input replacement are structural evidence. They do not prove how every possible stale stack and cross-mode inherited input behaves on the Deck.

## 1. Base

Pure empty entries by activation: `{"Full_Press": 1, "chord": 1}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g10](../../neptune/single-set-default_hold-gyro_latest.json#L14553) / **switches** | button_escape, button_menu, left_bumper, right_bumper, button_back_left, button_back_right, button_back_left_upper, button_back_right_upper, left_trackpad_touch, right_trackpad_touch | `{}` |
| button_diamond | [g11](../../neptune/single-set-default_hold-gyro_latest.json#L584) / **four_buttons** | button_a, button_b, button_x, button_y | `{"button_size": "17994", "button_dist": "19994"}` |
| joystick | [g12](../../neptune/single-set-default_hold-gyro_latest.json#L636) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"requires_click": "0", "deadzone": "13276", "edge_binding_invert": "1"}` |
| left_trigger | [g13](../../neptune/single-set-default_hold-gyro_latest.json#L723) / **trigger** | edge | `{"deadzone_outer_radius": "32767", "deadzone_inner_radius": "0", "edge_binding_radius": "0", "adaptive_threshold": "0"}` |
| right_trigger | [g14](../../neptune/single-set-default_hold-gyro_latest.json#L747) / **trigger** | edge | `{"deadzone_outer_radius": "32767", "deadzone_inner_radius": "0", "edge_binding_radius": "0", "adaptive_threshold": "0"}` |
| right_joystick | [g15](../../neptune/single-set-default_hold-gyro_latest.json#L771) / **joystick_mouse** | click, edge, touch | `{"curve_exponent": "0", "custom_curve_exponent": "59", "edge_binding_radius": "32767", "output_joystick": "2", "deadzone_inner_radius": "3280", "deadzone_outer_radius": "32000", "deadzone_enable_type": "2", "sensitivity": "100"}` |
| dpad | [g16](../../neptune/single-set-default_hold-gyro_latest.json#L850) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"requires_click": "0", "layout": "0", "haptic_intensity_override": "0"}` |
| left_trackpad | [g190](../../neptune/single-set-default_hold-gyro_latest.json#L2286) / **2dscroll** | click, dpad_west, dpad_east, dpad_north, dpad_south | `{"sensitivity": "50"}` |
| right_trackpad | [g562](../../neptune/single-set-default_hold-gyro_latest.json#L3895) / **absolute_mouse** | click, touch | `{"haptic_intensity": "0", "friction": "3", "acceleration": "1"}` |
| gyro | [g576](../../neptune/single-set-default_hold-gyro_latest.json#L3936) / **gyro_to_mouse** | none explicitly defined | `{"gyro_natural_sensitivity": "300", "flickstick_rotation_sensitivity": "4653", "gyro_vertical_horizontal_ratio": "200", "gyro_precision_speed": "0", "gyro_ratchet_button_mask": "211109453778944", "gyro_ratchet_button_requireany_or_all": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g11 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L592) | output/mode replacement candidate | `{}` | key_press F |
| [g11 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L602) | output/mode replacement candidate | `{}` | key_press V |
| [g11 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L612) | output/mode replacement candidate | `{}` | key_press C |
| [g11 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L622) | output/mode replacement candidate | `{}` | key_press R |
| [g12 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L644) | output/mode replacement candidate | `{}` | key_press W |
| [g12 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L654) | output/mode replacement candidate | `{}` | key_press S |
| [g12 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L664) | output/mode replacement candidate | `{}` | key_press D |
| [g12 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L674) | output/mode replacement candidate | `{}` | key_press A |
| [g12 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L684) | press empty | `{}` | empty_binding |
| [g12 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L694) | output/mode replacement candidate | `{}` | key_press Q |
| [g12 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L704) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | add_layer LST: Entry Point |
| [g13 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L731) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g14 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L755) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g15 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L779) | output/mode replacement candidate | `{}` | key_press E |
| [g15 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L789) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0"}` | add_layer Gyro Off Ramp Up |
| [g15 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L799) | ordered layer operations | `{"hold_repeats": "1", "gyro_ratchet_button_mask": "50331651", "gyro_ratchet_button_requireany_or_all": "0"}` | add_layer Turning Ramp Up 0 |
| [g15 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L809) | conditional empty | `{"hold_repeats": "1", "interruptable": "0", "gyro_ratchet_button_mask": "12", "gyro_ratchet_button_requireany_or_all": "0"}` | empty_binding |
| [g15 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L826) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | add_layer RST: Entry Point |
| [g16 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L858) | output/mode replacement candidate | `{}` | key_press 1 |
| [g16 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L868) | output/mode replacement candidate | `{}` | key_press 3 |
| [g16 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L878) | output/mode replacement candidate | `{}` | key_press 2 |
| [g16 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L888) | output/mode replacement candidate | `{}` | key_press 4 |
| [g190 click Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2294) | ordered layer operations | `{"haptic_intensity": "3"}` | hold_layer LTP: Arrow Keys |
| [g190 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2307) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Escape |
| [g190 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2320) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Enter |
| [g190 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2333) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Tab |
| [g190 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2346) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Backspace |
| [g562 click Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3903) | ordered layer operations | `{"haptic_intensity": "3"}` | hold_layer RTP: Mouse Buttons |
| [g562 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3916) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "interruptable": "0"}` | add_layer RTP: Entry Point |
| [g10 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14561) | ordered layer operations | `{"chord_button": "14", "hold_repeats": "1", "interruptable": "0"}` | add_layer Menu Right: Entry Point |
| [g10 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14576) | ordered layer operations | `{"chord_button": "15", "hold_repeats": "1", "interruptable": "0"}` | add_layer Menu Left: Entry Point |
| [g10 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14591) | ordered layer operations | `{"chord_button": "1", "hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer L1: Modifier 0 |
| [g10 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14607) | ordered layer operations | `{"chord_button": "2", "hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer R1: Modifier 1 |
| [g10 button_back_left Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14623) | output/mode replacement candidate | `{}` | key_press LEFT_CONTROL |
| [g10 button_back_right Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14633) | output/mode replacement candidate | `{}` | key_press LEFT_ALT |
| [g10 button_back_left_upper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14643) | output/mode replacement candidate | `{}` | key_press LEFT_SHIFT |
| [g10 button_back_right_upper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14653) | output/mode replacement candidate | `{}` | key_press SPACE |
| [g10 left_trackpad_touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14664) | output/mode replacement candidate | `{}` | mode_shift dpad 1039 |
| [g10 left_trackpad_touch Full_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L14669) | output/mode replacement candidate | `{}` | mode_shift button_diamond 1043 |
| [g10 right_trackpad_touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14681) | output/mode replacement candidate | `{}` | mode_shift dpad 1039 |
| [g10 right_trackpad_touch Full_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L14686) | output/mode replacement candidate | `{}` | mode_shift button_diamond 1043 |

**Conditional mode-shift bindings** (not the default active mode):

| Exact activator | Classification | Settings | Payload |
|---|---|---|---|
| [g1039 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8793) | output/mode replacement candidate | `{}` | key_press 1, ,  |
| [g1039 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8803) | output/mode replacement candidate | `{}` | key_press 3, ,  |
| [g1039 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8813) | output/mode replacement candidate | `{}` | key_press 2, ,  |
| [g1039 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8823) | output/mode replacement candidate | `{}` | key_press 4, ,  |
| [g1043 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8846) | output/mode replacement candidate | `{}` | key_press F, ,  |
| [g1043 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8856) | output/mode replacement candidate | `{}` | key_press V, ,  |
| [g1043 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8866) | output/mode replacement candidate | `{}` | key_press C, ,  |
| [g1043 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8876) | output/mode replacement candidate | `{}` | key_press R, ,  |

## 2. Turning Ramp Up 0

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g412](../../neptune/single-set-default_hold-gyro_latest.json#L3465) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g413](../../neptune/single-set-default_hold-gyro_latest.json#L3475) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g414](../../neptune/single-set-default_hold-gyro_latest.json#L15063) / **switches** | left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g423](../../neptune/single-set-default_hold-gyro_latest.json#L3485) / **joystick_mouse** | edge, touch | `{"layer": "1", "sensitivity": "130", "sensitivity_vert_scale": "77"}` |
| joystick | [g737](../../neptune/single-set-default_hold-gyro_latest.json#L6389) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g423 edge Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3494) | ordered layer operations | `{"haptic_intensity": "0", "delay_start": "250", "activation_threshold": "29031", "interruptable": "0"}` | add_layer Turning Ramp Up 1 |
| [g423 edge Soft_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L3505) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "activation_threshold": "29031", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer Turning Ramp Up 0; remove_layer Turning Ramp Up 1; remove_layer Gyro Off Ramp Up |
| [g423 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3522) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "300", "interruptable": "0"}` | remove_layer Turning Ramp Up 1 |
| [g423 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3537) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g737 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6397) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g414 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15071) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 0; remove_layer Turning Ramp Up 1; remove_layer Gyro Off Ramp Up; empty_binding |
| [g414 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15090) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 0; remove_layer Turning Ramp Up 1; remove_layer Gyro Off Ramp Up; empty_binding |

## 3. Turning Ramp Up 1

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g540](../../neptune/single-set-default_hold-gyro_latest.json#L3817) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g541](../../neptune/single-set-default_hold-gyro_latest.json#L3827) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g542](../../neptune/single-set-default_hold-gyro_latest.json#L15152) / **switches** | left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g551](../../neptune/single-set-default_hold-gyro_latest.json#L3837) / **joystick_mouse** | edge, touch | `{"layer": "1", "sensitivity": "160", "sensitivity_vert_scale": "63"}` |
| joystick | [g738](../../neptune/single-set-default_hold-gyro_latest.json#L6417) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g551 edge Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3845) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "activation_threshold": "25807", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer Turning Ramp Up 1; remove_layer Turning Ramp Up 0; remove_layer Gyro Off Ramp Up |
| [g551 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3866) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g738 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6425) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g542 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15160) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 1; remove_layer Turning Ramp Up 0; remove_layer Gyro Off Ramp Up; empty_binding |
| [g542 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15179) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 1; remove_layer Turning Ramp Up 0; remove_layer Gyro Off Ramp Up; empty_binding |

## 4. L1: Modifier 0

Pure empty entries by activation: `{"chord": 3, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g59](../../neptune/single-set-default_hold-gyro_latest.json#L14737) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g60](../../neptune/single-set-default_hold-gyro_latest.json#L1159) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| right_joystick | [g64](../../neptune/single-set-default_hold-gyro_latest.json#L1300) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| dpad | [g65](../../neptune/single-set-default_hold-gyro_latest.json#L1402) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| left_trigger | [g256](../../neptune/single-set-default_hold-gyro_latest.json#L3161) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g257](../../neptune/single-set-default_hold-gyro_latest.json#L3182) / **trigger** | click | `{"layer": "1"}` |
| joystick | [g667](../../neptune/single-set-default_hold-gyro_latest.json#L5009) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g60 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1167) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g60 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1176) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press G; add_layer L1: Tap Cover |
| [g60 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1192) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g60 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1201) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press X; add_layer L1: Tap Cover |
| [g60 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1217) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g60 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1226) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press Z; add_layer L1: Tap Cover |
| [g60 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1242) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g60 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1251) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press T; add_layer L1: Tap Cover |
| [g64 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1308) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g64 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1317) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | mouse_button MIDDLE; add_layer L1: Tap Cover |
| [g64 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1333) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g64 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1342) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g64 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1359) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g64 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1371) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g64 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1380) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L1: Tap Cover |
| [g65 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1410) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g65 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1419) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press 9; add_layer L1: Tap Cover |
| [g65 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1435) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g65 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1444) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press DASH; add_layer L1: Tap Cover |
| [g65 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1460) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g65 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1469) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press 0; add_layer L1: Tap Cover |
| [g65 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1485) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g65 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1494) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press EQUALS; add_layer L1: Tap Cover |
| [g256 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3169) | press empty | `{}` | empty_binding |
| [g257 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3190) | press empty | `{}` | empty_binding |
| [g667 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5017) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g667 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5026) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press CAPSLOCK; add_layer L1: Tap Cover |
| [g667 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5042) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g667 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5054) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g667 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5063) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L1: Tap Cover |
| [g59 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14745) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g59 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14754) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press INSERT; add_layer L1: Tap Cover |
| [g59 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14770) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g59 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14779) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press DELETE; add_layer L1: Tap Cover |
| [g59 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14795) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer L1: Double Tap; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0 |
| [g59 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14807) | ordered layer operations | `{"chord_button": "1", "delay_start": "300", "interruptable": "0"}` | add_layer L1: Tap Cover |
| [g59 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14822) | held-state guard; ordered layer operations | `{"chord_button": "1", "hold_repeats": "1", "interruptable": "0"}` | add_layer L1!R1: Modifier 2; add_layer R1: Tap Cover; add_layer R1: Modifier 1; add_layer L1: Tap Cover |
| [g59 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14837) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |

## 5. R1: Modifier 1

Pure empty entries by activation: `{"chord": 3, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g157](../../neptune/single-set-default_hold-gyro_latest.json#L1704) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| switch | [g160](../../neptune/single-set-default_hold-gyro_latest.json#L14854) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g161](../../neptune/single-set-default_hold-gyro_latest.json#L1835) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g217](../../neptune/single-set-default_hold-gyro_latest.json#L2618) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| left_trigger | [g258](../../neptune/single-set-default_hold-gyro_latest.json#L3203) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g259](../../neptune/single-set-default_hold-gyro_latest.json#L3224) / **trigger** | click | `{"layer": "1"}` |
| joystick | [g668](../../neptune/single-set-default_hold-gyro_latest.json#L5084) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g157 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1712) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g157 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1721) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press H; add_layer R1: Tap Cover |
| [g157 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1737) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g157 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1746) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press N; add_layer R1: Tap Cover |
| [g157 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1762) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g157 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1771) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press B; add_layer R1: Tap Cover |
| [g157 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1787) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g157 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1796) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press Y; add_layer R1: Tap Cover |
| [g161 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1843) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g161 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1852) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 5; add_layer R1: Tap Cover |
| [g161 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1868) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g161 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1877) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 7; add_layer R1: Tap Cover |
| [g161 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1893) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g161 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1902) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 6; add_layer R1: Tap Cover |
| [g161 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1918) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g161 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L1927) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 8; add_layer R1: Tap Cover |
| [g217 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2626) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g217 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2635) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | mouse_button FORWARD; add_layer R1: Tap Cover |
| [g217 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2651) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g217 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2660) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g217 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2677) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g217 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2689) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g217 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2698) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer R1: Tap Cover |
| [g258 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3211) | press empty | `{}` | empty_binding |
| [g259 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3232) | press empty | `{}` | empty_binding |
| [g668 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5092) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g668 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5101) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | mouse_button BACK; add_layer R1: Tap Cover |
| [g668 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5117) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g668 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5129) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g668 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5138) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer R1: Tap Cover |
| [g160 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14862) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g160 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14871) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press HOME; add_layer R1: Tap Cover |
| [g160 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14887) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g160 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14896) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press END; add_layer R1: Tap Cover |
| [g160 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14912) | held-state guard; ordered layer operations | `{"chord_button": "2", "hold_repeats": "1", "interruptable": "0"}` | add_layer R1!L1: Modifier 2; add_layer L1: Tap Cover; add_layer L1: Modifier 0; add_layer R1: Tap Cover |
| [g160 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14927) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g160 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14941) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer R1: Double Tap; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1 |
| [g160 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14953) | ordered layer operations | `{"chord_button": "2", "delay_start": "300", "interruptable": "0"}` | add_layer R1: Tap Cover |

## 6. L1!R1: Modifier 2

Pure empty entries by activation: `{"chord": 14, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g596](../../neptune/single-set-default_hold-gyro_latest.json#L4015) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g597](../../neptune/single-set-default_hold-gyro_latest.json#L4198) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g598](../../neptune/single-set-default_hold-gyro_latest.json#L4219) / **trigger** | click | `{"layer": "1"}` |
| switch | [g599](../../neptune/single-set-default_hold-gyro_latest.json#L15201) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g612](../../neptune/single-set-default_hold-gyro_latest.json#L4339) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g681](../../neptune/single-set-default_hold-gyro_latest.json#L5699) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g682](../../neptune/single-set-default_hold-gyro_latest.json#L5814) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g596 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4023) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g596 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4039) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press M; add_layer L1&R1: Tap Cover |
| [g596 button_a chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4051) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g596 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4066) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g596 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4082) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press P; add_layer L1&R1: Tap Cover |
| [g596 button_b chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4094) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g596 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4109) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g596 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4125) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press O; add_layer L1&R1: Tap Cover |
| [g596 button_x chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4137) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g596 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4152) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g596 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4168) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press U; add_layer L1&R1: Tap Cover |
| [g596 button_y chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4180) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g597 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4206) | press empty | `{}` | empty_binding |
| [g598 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4227) | press empty | `{}` | empty_binding |
| [g612 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4347) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g612 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4363) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press I; add_layer L1&R1: Tap Cover |
| [g612 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4375) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g612 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4390) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g612 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4406) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press K; add_layer L1&R1: Tap Cover |
| [g612 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4418) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g612 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4433) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g612 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4449) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press L; add_layer L1&R1: Tap Cover |
| [g612 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4461) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g612 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4476) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g612 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4492) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press J; add_layer L1&R1: Tap Cover |
| [g612 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4504) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g681 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5707) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g681 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5723) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press BACK_TICK; add_layer L1&R1: Tap Cover |
| [g681 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L5735) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g681 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5751) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g681 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L5760) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g681 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5770) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g681 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5793) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L1&R1: Tap Cover |
| [g682 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5822) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g682 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5838) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L1&R1: Tap Cover |
| [g682 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L5850) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g682 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5865) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L1&R1: Tap Cover |
| [g599 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15209) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g599 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15225) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press PAGE_UP; add_layer L1&R1: Tap Cover |
| [g599 button_escape chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15237) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g599 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15252) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g599 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15268) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L1&R1: Tap Cover |
| [g599 button_menu chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15280) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g599 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15295) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |
| [g599 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15321) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |
| [g599 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15342) | ordered layer operations | `{"chord_button": "1", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L1&R1: Tap Cover |
| [g599 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15352) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L1&R1: Tap Cover |

## 7. R1!L1: Modifier 2

Pure empty entries by activation: `{"Full_Press": 2, "chord": 14}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g601](../../neptune/single-set-default_hold-gyro_latest.json#L4291) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g602](../../neptune/single-set-default_hold-gyro_latest.json#L4315) / **trigger** | click | `{"layer": "1"}` |
| switch | [g603](../../neptune/single-set-default_hold-gyro_latest.json#L15370) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g817](../../neptune/single-set-default_hold-gyro_latest.json#L6941) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| dpad | [g818](../../neptune/single-set-default_hold-gyro_latest.json#L7124) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| joystick | [g819](../../neptune/single-set-default_hold-gyro_latest.json#L7307) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g820](../../neptune/single-set-default_hold-gyro_latest.json#L7379) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g601 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4299) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g602 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4323) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g817 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6949) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g817 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6965) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g817 button_a chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L6974) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press M; add_layer L1&R1: Tap Cover |
| [g817 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6992) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g817 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7008) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g817 button_b chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7017) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press P; add_layer L1&R1: Tap Cover |
| [g817 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7035) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g817 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7051) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g817 button_x chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7060) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press O; add_layer L1&R1: Tap Cover |
| [g817 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7078) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g817 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7094) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g817 button_y chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7103) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press U; add_layer L1&R1: Tap Cover |
| [g818 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7132) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g818 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7148) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g818 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7157) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press I; add_layer L1&R1: Tap Cover |
| [g818 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7175) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g818 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7191) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g818 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7200) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press K; add_layer L1&R1: Tap Cover |
| [g818 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7218) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g818 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7234) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g818 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7243) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press L; add_layer L1&R1: Tap Cover |
| [g818 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7261) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g818 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7277) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g818 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7286) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press J; add_layer L1&R1: Tap Cover |
| [g819 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7315) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g819 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7331) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g819 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7340) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L1&R1: Tap Cover |
| [g819 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7358) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L1&R1: Tap Cover |
| [g820 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7387) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g820 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7403) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g820 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7412) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press BACK_TICK; add_layer L1&R1: Tap Cover |
| [g820 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7431) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g820 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L7440) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g820 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7450) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g820 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7473) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L1&R1: Tap Cover |
| [g603 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15378) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g603 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15394) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press PAGE_UP; add_layer L1&R1: Tap Cover |
| [g603 button_escape chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15406) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g603 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15421) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g603 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15437) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L1&R1: Tap Cover |
| [g603 button_menu chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15449) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g603 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15464) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |
| [g603 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15485) | ordered layer operations | `{"chord_button": "2", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L1&R1: Tap Cover |
| [g603 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15495) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L1&R1: Tap Cover |
| [g603 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15510) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |

## 8. Gyro

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g12974](../../neptune/single-set-default_hold-gyro_latest.json#L18022) / **switches** | left_bumper, right_bumper | `{"layer": "1"}` |
| left_trigger | [g12980](../../neptune/single-set-default_hold-gyro_latest.json#L14092) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g12981](../../neptune/single-set-default_hold-gyro_latest.json#L14102) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| gyro | [g13035](../../neptune/single-set-default_hold-gyro_latest.json#L14483) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12974 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18030) | ordered layer operations | `{"chord_button": "1", "hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer Gyro \| L1: Modifier 0 |
| [g12974 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18046) | ordered layer operations | `{"chord_button": "2", "hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer Gyro \| R1: Modifier 1 |

## 9. Gyro | L1: Modifier 0

Pure empty entries by activation: `{"chord": 3, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g12911](../../neptune/single-set-default_hold-gyro_latest.json#L17450) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g12912](../../neptune/single-set-default_hold-gyro_latest.json#L11588) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| right_joystick | [g12916](../../neptune/single-set-default_hold-gyro_latest.json#L11729) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| dpad | [g12917](../../neptune/single-set-default_hold-gyro_latest.json#L11831) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| left_trigger | [g12922](../../neptune/single-set-default_hold-gyro_latest.json#L11985) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g12923](../../neptune/single-set-default_hold-gyro_latest.json#L12006) / **trigger** | click | `{"layer": "1"}` |
| joystick | [g12925](../../neptune/single-set-default_hold-gyro_latest.json#L12037) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13037](../../neptune/single-set-default_hold-gyro_latest.json#L14505) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12912 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11596) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12912 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11605) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press G; add_layer L1: Tap Cover |
| [g12912 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11621) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12912 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11630) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press X; add_layer L1: Tap Cover |
| [g12912 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11646) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12912 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11655) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press Z; add_layer L1: Tap Cover |
| [g12912 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11671) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12912 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11680) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press T; add_layer L1: Tap Cover |
| [g12916 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11737) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12916 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11746) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | mouse_button MIDDLE; add_layer L1: Tap Cover |
| [g12916 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11762) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12916 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11771) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12916 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11788) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12916 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11800) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12916 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11809) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L1: Tap Cover |
| [g12917 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11839) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12917 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11848) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press 9; add_layer L1: Tap Cover |
| [g12917 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11864) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12917 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11873) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press DASH; add_layer L1: Tap Cover |
| [g12917 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11889) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12917 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11898) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press 0; add_layer L1: Tap Cover |
| [g12917 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11914) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12917 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11923) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press EQUALS; add_layer L1: Tap Cover |
| [g12922 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11993) | press empty | `{}` | empty_binding |
| [g12923 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12014) | press empty | `{}` | empty_binding |
| [g12925 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12045) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12925 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12054) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press CAPSLOCK; add_layer L1: Tap Cover |
| [g12925 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12070) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12925 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12082) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12925 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12091) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L1: Tap Cover |
| [g12911 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17458) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12911 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17467) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press INSERT; add_layer L1: Tap Cover |
| [g12911 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17483) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |
| [g12911 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17492) | held-state guard; ordered layer operations | `{"chord_button": "1"}` | key_press DELETE; add_layer L1: Tap Cover |
| [g12911 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17508) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer L1: Double Tap; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0 |
| [g12911 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17520) | ordered layer operations | `{"chord_button": "1", "delay_start": "300", "interruptable": "0"}` | add_layer L1: Tap Cover |
| [g12911 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17535) | held-state guard; ordered layer operations | `{"chord_button": "1", "hold_repeats": "1", "interruptable": "0"}` | add_layer Gyro \| L1!R1: Modifier 2; add_layer R1: Tap Cover; add_layer Gyro \| R1: Modifier 1; add_layer L1: Tap Cover |
| [g12911 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17550) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |

## 10. Gyro | R1: Modifier 1

Pure empty entries by activation: `{"chord": 3, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g12928](../../neptune/single-set-default_hold-gyro_latest.json#L12112) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| switch | [g12931](../../neptune/single-set-default_hold-gyro_latest.json#L17567) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g12932](../../neptune/single-set-default_hold-gyro_latest.json#L12243) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g12934](../../neptune/single-set-default_hold-gyro_latest.json#L12366) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| left_trigger | [g12940](../../neptune/single-set-default_hold-gyro_latest.json#L12519) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g12941](../../neptune/single-set-default_hold-gyro_latest.json#L12540) / **trigger** | click | `{"layer": "1"}` |
| joystick | [g12944](../../neptune/single-set-default_hold-gyro_latest.json#L12583) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13038](../../neptune/single-set-default_hold-gyro_latest.json#L14517) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12928 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12120) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12928 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12129) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press H; add_layer R1: Tap Cover |
| [g12928 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12145) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12928 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12154) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press N; add_layer R1: Tap Cover |
| [g12928 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12170) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12928 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12179) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press B; add_layer R1: Tap Cover |
| [g12928 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12195) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12928 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12204) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press Y; add_layer R1: Tap Cover |
| [g12932 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12251) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12932 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12260) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 5; add_layer R1: Tap Cover |
| [g12932 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12276) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12932 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12285) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 7; add_layer R1: Tap Cover |
| [g12932 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12301) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12932 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12310) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 6; add_layer R1: Tap Cover |
| [g12932 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12326) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12932 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12335) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press 8; add_layer R1: Tap Cover |
| [g12934 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12374) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12934 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12383) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | mouse_button FORWARD; add_layer R1: Tap Cover |
| [g12934 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12399) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12934 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12408) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12934 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12425) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12934 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12437) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12934 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12446) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer R1: Tap Cover |
| [g12940 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12527) | press empty | `{}` | empty_binding |
| [g12941 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12548) | press empty | `{}` | empty_binding |
| [g12944 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12591) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12944 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12600) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | mouse_button BACK; add_layer R1: Tap Cover |
| [g12944 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12616) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12944 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12628) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12944 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12637) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer R1: Tap Cover |
| [g12931 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17575) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12931 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17584) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press HOME; add_layer R1: Tap Cover |
| [g12931 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17600) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12931 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17609) | held-state guard; ordered layer operations | `{"chord_button": "2"}` | key_press END; add_layer R1: Tap Cover |
| [g12931 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17625) | held-state guard; ordered layer operations | `{"chord_button": "2", "hold_repeats": "1", "interruptable": "0"}` | add_layer Gyro \| R1!L1: Modifier 2; add_layer L1: Tap Cover; add_layer Gyro \| L1: Modifier 0; add_layer R1: Tap Cover |
| [g12931 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17640) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |
| [g12931 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17654) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer R1: Double Tap; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1 |
| [g12931 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17666) | ordered layer operations | `{"chord_button": "2", "delay_start": "300", "interruptable": "0"}` | add_layer R1: Tap Cover |

## 11. Gyro | L1!R1: Modifier 2

Pure empty entries by activation: `{"chord": 14, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g12947](../../neptune/single-set-default_hold-gyro_latest.json#L12658) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g12948](../../neptune/single-set-default_hold-gyro_latest.json#L12841) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g12949](../../neptune/single-set-default_hold-gyro_latest.json#L12862) / **trigger** | click | `{"layer": "1"}` |
| switch | [g12950](../../neptune/single-set-default_hold-gyro_latest.json#L17684) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g12951](../../neptune/single-set-default_hold-gyro_latest.json#L12883) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g12952](../../neptune/single-set-default_hold-gyro_latest.json#L13066) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g12953](../../neptune/single-set-default_hold-gyro_latest.json#L13181) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13039](../../neptune/single-set-default_hold-gyro_latest.json#L14529) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12947 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12666) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12947 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12682) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press M; add_layer L1&R1: Tap Cover |
| [g12947 button_a chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L12694) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12947 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12709) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12947 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12725) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press P; add_layer L1&R1: Tap Cover |
| [g12947 button_b chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L12737) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12947 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12752) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12947 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12768) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press O; add_layer L1&R1: Tap Cover |
| [g12947 button_x chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L12780) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12947 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12795) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12947 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12811) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press U; add_layer L1&R1: Tap Cover |
| [g12947 button_y chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L12823) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12948 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12849) | press empty | `{}` | empty_binding |
| [g12949 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12870) | press empty | `{}` | empty_binding |
| [g12951 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12891) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12951 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12907) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press I; add_layer L1&R1: Tap Cover |
| [g12951 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L12919) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12951 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12934) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12951 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12950) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press K; add_layer L1&R1: Tap Cover |
| [g12951 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L12962) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12951 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12977) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12951 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L12993) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press L; add_layer L1&R1: Tap Cover |
| [g12951 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13005) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12951 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13020) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12951 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13036) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press J; add_layer L1&R1: Tap Cover |
| [g12951 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13048) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12952 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13074) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12952 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13090) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press BACK_TICK; add_layer L1&R1: Tap Cover |
| [g12952 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13102) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12952 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13118) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12952 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13127) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12952 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13137) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12952 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13160) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L1&R1: Tap Cover |
| [g12953 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13189) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12953 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13205) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L1&R1: Tap Cover |
| [g12953 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13217) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12953 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13232) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L1&R1: Tap Cover |
| [g12950 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17692) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12950 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17708) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press PAGE_UP; add_layer L1&R1: Tap Cover |
| [g12950 button_escape chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17720) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12950 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17735) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12950 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17751) | held-state guard; ordered layer operations | `{"chord_button": "1", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L1&R1: Tap Cover |
| [g12950 button_menu chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17763) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12950 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17778) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |
| [g12950 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17804) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |
| [g12950 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17825) | ordered layer operations | `{"chord_button": "1", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L1&R1: Tap Cover |
| [g12950 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17835) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L1&R1: Tap Cover |

## 12. Gyro | R1!L1: Modifier 2

Pure empty entries by activation: `{"Full_Press": 2, "chord": 14}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g12959](../../neptune/single-set-default_hold-gyro_latest.json#L13304) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g12960](../../neptune/single-set-default_hold-gyro_latest.json#L13328) / **trigger** | click | `{"layer": "1"}` |
| switch | [g12961](../../neptune/single-set-default_hold-gyro_latest.json#L17853) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g12965](../../neptune/single-set-default_hold-gyro_latest.json#L13457) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| dpad | [g12966](../../neptune/single-set-default_hold-gyro_latest.json#L13640) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| joystick | [g12967](../../neptune/single-set-default_hold-gyro_latest.json#L13823) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g12968](../../neptune/single-set-default_hold-gyro_latest.json#L13895) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| gyro | [g13040](../../neptune/single-set-default_hold-gyro_latest.json#L14541) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12959 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13312) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g12960 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13336) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g12965 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13465) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12965 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13481) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12965 button_a chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13490) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press M; add_layer L1&R1: Tap Cover |
| [g12965 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13508) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12965 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13524) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12965 button_b chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13533) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press P; add_layer L1&R1: Tap Cover |
| [g12965 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13551) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12965 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13567) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12965 button_x chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13576) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press O; add_layer L1&R1: Tap Cover |
| [g12965 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13594) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12965 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13610) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12965 button_y chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13619) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press U; add_layer L1&R1: Tap Cover |
| [g12966 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13648) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12966 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13664) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13673) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press I; add_layer L1&R1: Tap Cover |
| [g12966 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13691) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12966 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13707) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13716) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press K; add_layer L1&R1: Tap Cover |
| [g12966 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13734) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12966 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13750) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13759) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press L; add_layer L1&R1: Tap Cover |
| [g12966 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13777) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12966 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13793) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13802) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press J; add_layer L1&R1: Tap Cover |
| [g12967 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13831) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12967 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13847) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12967 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13856) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L1&R1: Tap Cover |
| [g12967 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13874) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L1&R1: Tap Cover |
| [g12968 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13903) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12968 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13919) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12968 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13928) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press BACK_TICK; add_layer L1&R1: Tap Cover |
| [g12968 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13947) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12968 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L13956) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g12968 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13966) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12968 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L13989) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L1&R1: Tap Cover |
| [g12961 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17861) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12961 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17877) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press PAGE_UP; add_layer L1&R1: Tap Cover |
| [g12961 button_escape chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17889) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12961 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17904) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |
| [g12961 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17920) | held-state guard; ordered layer operations | `{"chord_button": "2", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L1&R1: Tap Cover |
| [g12961 button_menu chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17932) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g12961 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17947) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |
| [g12961 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17968) | ordered layer operations | `{"chord_button": "2", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L1&R1: Tap Cover |
| [g12961 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17978) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L1&R1: Tap Cover |
| [g12961 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17993) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Gyro 1 1; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer L1: Tap Cover; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover; remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2 |

## 13. LST: Temporary Gyro

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g208](../../neptune/single-set-default_hold-gyro_latest.json#L15023) / **switches** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g210](../../neptune/single-set-default_hold-gyro_latest.json#L2571) / **dpad** | touch | `{"layer": "1"}` |
| left_trigger | [g262](../../neptune/single-set-default_hold-gyro_latest.json#L3265) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g263](../../neptune/single-set-default_hold-gyro_latest.json#L3275) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| gyro | [g881](../../neptune/single-set-default_hold-gyro_latest.json#L7743) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "70368744177664"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g210 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2579) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Entry Point |

## 14. RST: Temporary Gyro

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g200](../../neptune/single-set-default_hold-gyro_latest.json#L15013) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g203](../../neptune/single-set-default_hold-gyro_latest.json#L2492) / **joystick_mouse** | touch | `{"layer": "1"}` |
| left_trigger | [g260](../../neptune/single-set-default_hold-gyro_latest.json#L3245) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g261](../../neptune/single-set-default_hold-gyro_latest.json#L3255) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| gyro | [g880](../../neptune/single-set-default_hold-gyro_latest.json#L7732) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "140737488355328"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g203 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2500) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Entry Point |

## 15. Gyro Off Ramp Up

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g13029](../../neptune/single-set-default_hold-gyro_latest.json#L18075) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g13030](../../neptune/single-set-default_hold-gyro_latest.json#L14406) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g13031](../../neptune/single-set-default_hold-gyro_latest.json#L14431) / **trigger** | edge | `{"layer": "1"}` |
| gyro | [g13034](../../neptune/single-set-default_hold-gyro_latest.json#L14474) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g13041](../../neptune/single-set-default_hold-gyro_latest.json#L18085) / **joystick_mouse** | edge | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13030 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14414) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Gyro Off Ramp Up |
| [g13031 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L14439) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Gyro Off Ramp Up |
| [g13041 edge Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18094) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "activation_threshold": "25807", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer Gyro Off Ramp Up |
| [g13041 edge Soft_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L18106) | ordered layer operations | `{"haptic_intensity": "0", "delay_start": "5", "activation_threshold": "29031", "interruptable": "0"}` | add_layer Turning Ramp Up 0 |

## 16. LTP: Arrow Keys

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g250](../../neptune/single-set-default_hold-gyro_latest.json#L15043) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g251](../../neptune/single-set-default_hold-gyro_latest.json#L3053) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click | `{"layer": "1", "layout": "0", "deadzone": "23000", "edge_binding_invert": "1", "haptic_intensity_override": "3"}` |
| left_trigger | [g266](../../neptune/single-set-default_hold-gyro_latest.json#L3305) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g267](../../neptune/single-set-default_hold-gyro_latest.json#L3315) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g671](../../neptune/single-set-default_hold-gyro_latest.json#L5249) / **dpad** | touch | `{"layer": "1"}` |
| right_joystick | [g672](../../neptune/single-set-default_hold-gyro_latest.json#L5294) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g251 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3061) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press UP_ARROW |
| [g251 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3074) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press DOWN_ARROW |
| [g251 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3087) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press RIGHT_ARROW |
| [g251 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3100) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press LEFT_ARROW |
| [g251 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3113) | output/mode replacement candidate | `{"chord_button": "18", "haptic_intensity": "3"}` | SHOW_KEYBOARD |
| [g251 click Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3128) | ordered layer operations | `{"haptic_intensity": "0", "interruptable": "0"}` | hold_layer LTP: Arrow Keys |
| [g251 click Soft_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L3137) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer LTP: Arrow Keys |
| [g671 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5257) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer LTP: Arrow Keys |
| [g671 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5265) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g671 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5274) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g672 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5302) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer LTP: Arrow Keys |
| [g672 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5310) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g672 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5319) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 17. RTP: Mouse Buttons

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g240](../../neptune/single-set-default_hold-gyro_latest.json#L15033) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g242](../../neptune/single-set-default_hold-gyro_latest.json#L2850) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click | `{"layer": "1", "layout": "0", "deadzone": "23000", "edge_binding_invert": "1", "haptic_intensity_override": "3"}` |
| left_trigger | [g264](../../neptune/single-set-default_hold-gyro_latest.json#L3285) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g265](../../neptune/single-set-default_hold-gyro_latest.json#L3295) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g669](../../neptune/single-set-default_hold-gyro_latest.json#L5159) / **dpad** | touch | `{"layer": "1"}` |
| right_joystick | [g670](../../neptune/single-set-default_hold-gyro_latest.json#L5204) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g242 dpad_north Long_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2858) | output/mode replacement candidate | `{"hold_repeats": "1", "long_press_time": "150", "haptic_intensity": "0"}` | mouse_wheel SCROLL_UP |
| [g242 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2868) | output/mode replacement candidate | `{"haptic_intensity": "0", "interruptable": "0"}` | mouse_wheel SCROLL_UP |
| [g242 dpad_south Long_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2882) | output/mode replacement candidate | `{"hold_repeats": "1", "long_press_time": "150", "haptic_intensity": "0"}` | mouse_wheel SCROLL_DOWN |
| [g242 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2892) | output/mode replacement candidate | `{"haptic_intensity": "0", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |
| [g242 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2906) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | mouse_button FORWARD |
| [g242 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2919) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | mouse_button BACK |
| [g242 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2932) | output/mode replacement candidate | `{"chord_button": "19", "haptic_intensity": "3"}` | mouse_button MIDDLE |
| [g242 click Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L2947) | ordered layer operations | `{"haptic_intensity": "0", "interruptable": "0"}` | hold_layer RTP: Mouse Buttons |
| [g242 click Soft_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L2956) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer RTP: Mouse Buttons |
| [g669 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5167) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Mouse Buttons |
| [g669 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5175) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g669 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5184) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g670 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5212) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Mouse Buttons |
| [g670 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5220) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g670 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5229) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 18. RTP: Circular Scroll

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g368](../../neptune/single-set-default_hold-gyro_latest.json#L3377) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g369](../../neptune/single-set-default_hold-gyro_latest.json#L3387) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g370](../../neptune/single-set-default_hold-gyro_latest.json#L15053) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g721](../../neptune/single-set-default_hold-gyro_latest.json#L6147) / **scrollwheel** | scroll_clockwise, scroll_counterclockwise, click, touch | `{"layer": "1", "scroll_angle": "145", "haptic_intensity": "0"}` |
| joystick | [g722](../../neptune/single-set-default_hold-gyro_latest.json#L6209) / **dpad** | touch | `{"layer": "1"}` |
| right_joystick | [g723](../../neptune/single-set-default_hold-gyro_latest.json#L6257) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g721 scroll_clockwise Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6155) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g721 scroll_counterclockwise Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6165) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g721 click Soft_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6175) | ordered layer operations | `{"haptic_intensity": "0"}` | hold_layer RTP: Mouse Buttons |
| [g721 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6188) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Circular Scroll; remove_layer RTP: Mouse Buttons |
| [g722 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6217) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Circular Scroll; remove_layer RTP: Mouse Buttons |
| [g722 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6228) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g722 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6237) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g723 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6265) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Circular Scroll; remove_layer RTP: Mouse Buttons |
| [g723 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6276) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g723 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6285) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 19. L1: Scroll Down

Pure empty entries by activation: `{"Full_Press": 2, "chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g899](../../neptune/single-set-default_hold-gyro_latest.json#L7880) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g900](../../neptune/single-set-default_hold-gyro_latest.json#L7904) / **trigger** | click | `{"layer": "1"}` |
| switch | [g901](../../neptune/single-set-default_hold-gyro_latest.json#L16368) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g944](../../neptune/single-set-default_hold-gyro_latest.json#L8189) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g945](../../neptune/single-set-default_hold-gyro_latest.json#L8260) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g899 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7888) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g900 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7912) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g944 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8197) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g944 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8206) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L1: Scroll Down; remove_layer L1: Double Tap Cover |
| [g944 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8222) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L1: Double Tap Cover |
| [g944 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8235) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Scroll Down; remove_layer L1: Double Tap Cover |
| [g944 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8243) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g945 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8268) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L1: Double Tap Cover |
| [g945 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8281) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L1: Scroll Down; remove_layer L1: Double Tap Cover |
| [g945 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8289) | conditional empty; held-state guard | `{"chord_button": "1", "interruptable": "0"}` | empty_binding |
| [g901 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16376) | output/mode replacement candidate | `{}` | mouse_button MIDDLE |
| [g901 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16386) | output/mode replacement candidate | `{}` | key_press BACK_TICK |
| [g901 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16396) | output/mode replacement candidate | `{"hold_repeats": "1", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |
| [g901 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16405) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer L1: Double Tap; remove_layer L1: Scroll Down |
| [g901 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16416) | ordered layer operations | `{"chord_button": "1", "delay_start": "150", "interruptable": "0"}` | add_layer L1: Double Tap Cover |
| [g901 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16431) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |

## 20. R1: Scroll Up

Pure empty entries by activation: `{"Full_Press": 2, "chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g903](../../neptune/single-set-default_hold-gyro_latest.json#L7938) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g904](../../neptune/single-set-default_hold-gyro_latest.json#L7962) / **trigger** | click | `{"layer": "1"}` |
| switch | [g905](../../neptune/single-set-default_hold-gyro_latest.json#L16444) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g946](../../neptune/single-set-default_hold-gyro_latest.json#L8306) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g947](../../neptune/single-set-default_hold-gyro_latest.json#L8377) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g903 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7946) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g904 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7970) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g946 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8314) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g946 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8323) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R1: Scroll Up; remove_layer R1: Double Tap Cover |
| [g946 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8339) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer R1: Double Tap Cover |
| [g946 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8352) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Scroll Up; remove_layer R1: Double Tap Cover |
| [g946 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8360) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g947 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8385) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer R1: Double Tap Cover |
| [g947 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8398) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R1: Scroll Up; remove_layer R1: Double Tap Cover |
| [g947 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8406) | conditional empty; held-state guard | `{"chord_button": "2", "interruptable": "0"}` | empty_binding |
| [g905 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16452) | output/mode replacement candidate | `{}` | mouse_button MIDDLE |
| [g905 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16462) | output/mode replacement candidate | `{}` | key_press BACK_TICK |
| [g905 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16472) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g905 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16482) | output/mode replacement candidate | `{"hold_repeats": "1", "interruptable": "0"}` | mouse_wheel SCROLL_UP |
| [g905 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16491) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer R1: Double Tap; remove_layer R1: Scroll Up |
| [g905 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16502) | ordered layer operations | `{"chord_button": "2", "delay_start": "150", "interruptable": "0"}` | add_layer R1: Double Tap Cover |

## 21. Escape

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g488](../../neptune/single-set-default_hold-gyro_latest.json#L3629) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g489](../../neptune/single-set-default_hold-gyro_latest.json#L3639) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g490](../../neptune/single-set-default_hold-gyro_latest.json#L15132) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g529](../../neptune/single-set-default_hold-gyro_latest.json#L3743) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g677](../../neptune/single-set-default_hold-gyro_latest.json#L5519) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g678](../../neptune/single-set-default_hold-gyro_latest.json#L5564) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g529 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3751) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press ESCAPE |
| [g529 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3759) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Escape |
| [g677 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5527) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Escape |
| [g677 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5535) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g677 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5544) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g678 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5572) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Escape |
| [g678 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5580) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g678 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5589) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 22. Tab

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g480](../../neptune/single-set-default_hold-gyro_latest.json#L3569) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g481](../../neptune/single-set-default_hold-gyro_latest.json#L3579) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g482](../../neptune/single-set-default_hold-gyro_latest.json#L15112) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g527](../../neptune/single-set-default_hold-gyro_latest.json#L3679) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g673](../../neptune/single-set-default_hold-gyro_latest.json#L5339) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g674](../../neptune/single-set-default_hold-gyro_latest.json#L5384) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g527 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3687) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press TAB |
| [g527 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3695) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Tab |
| [g673 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5347) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Tab |
| [g673 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5355) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g673 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5364) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g674 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5392) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Tab |
| [g674 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5400) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g674 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5409) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 23. Backspace

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g484](../../neptune/single-set-default_hold-gyro_latest.json#L3599) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g485](../../neptune/single-set-default_hold-gyro_latest.json#L3609) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g486](../../neptune/single-set-default_hold-gyro_latest.json#L15122) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g528](../../neptune/single-set-default_hold-gyro_latest.json#L3711) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g675](../../neptune/single-set-default_hold-gyro_latest.json#L5429) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g676](../../neptune/single-set-default_hold-gyro_latest.json#L5474) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g528 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3719) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press BACKSPACE |
| [g528 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3727) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Backspace |
| [g675 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5437) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Backspace |
| [g675 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5445) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g675 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5454) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g676 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5482) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Backspace |
| [g676 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5490) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g676 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5499) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 24. Enter

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g492](../../neptune/single-set-default_hold-gyro_latest.json#L3659) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g493](../../neptune/single-set-default_hold-gyro_latest.json#L3669) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g494](../../neptune/single-set-default_hold-gyro_latest.json#L15142) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g530](../../neptune/single-set-default_hold-gyro_latest.json#L3775) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g679](../../neptune/single-set-default_hold-gyro_latest.json#L5609) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g680](../../neptune/single-set-default_hold-gyro_latest.json#L5654) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g530 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3783) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press RETURN |
| [g530 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L3791) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Enter |
| [g679 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5617) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Enter |
| [g679 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5625) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g679 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5634) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g680 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5662) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Enter |
| [g680 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5670) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g680 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5679) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 25. Menu Left: Escape

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1112](../../neptune/single-set-default_hold-gyro_latest.json#L9062) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1113](../../neptune/single-set-default_hold-gyro_latest.json#L9072) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g1114](../../neptune/single-set-default_hold-gyro_latest.json#L9096) / **trigger** | click | `{"layer": "1"}` |
| switch | [g1115](../../neptune/single-set-default_hold-gyro_latest.json#L16907) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g1169](../../neptune/single-set-default_hold-gyro_latest.json#L9560) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1170](../../neptune/single-set-default_hold-gyro_latest.json#L9599) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g1203](../../neptune/single-set-default_hold-gyro_latest.json#L9723) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1113 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9080) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1114 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9104) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1169 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9568) | press empty | `{}` | empty_binding |
| [g1169 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9578) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Left: Double Tap Cover |
| [g1170 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9607) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Left: Double Tap Cover |
| [g1115 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16915) | press empty | `{}` | empty_binding |
| [g1115 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16925) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press ESCAPE |
| [g1115 button_menu release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16933) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Left: Double Tap; remove_layer Menu Left: Escape |
| [g1115 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16944) | ordered layer operations | `{"chord_button": "15", "delay_start": "150", "interruptable": "0"}` | add_layer Menu Left: Double Tap Cover |
| [g1115 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16959) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1115 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16969) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |

## 26. Menu Left: Backspace

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g13048](../../neptune/single-set-default_hold-gyro_latest.json#L18405) / **switches** | button_menu | `{"layer": "1"}` |
| gyro | [g13049](../../neptune/single-set-default_hold-gyro_latest.json#L18437) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13048 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18413) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press BACKSPACE |
| [g13048 button_menu release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18421) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Left: Backspace |

## 27. Menu Left: Fn Layer

Pure empty entries by activation: `{"Full_Press": 2, "chord": 12}`. Mixed entries containing empty subcommands: **1**. Chord-protected cleanup entries: **19**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g624](../../neptune/single-set-default_hold-gyro_latest.json#L4573) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g625](../../neptune/single-set-default_hold-gyro_latest.json#L4728) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g626](../../neptune/single-set-default_hold-gyro_latest.json#L4785) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g627](../../neptune/single-set-default_hold-gyro_latest.json#L15539) / **switches** | button_escape, button_menu, left_bumper, right_bumper, button_back_left, button_back_right, button_back_left_upper, button_back_right_upper, left_stick_click, right_stick_click | `{"layer": "1"}` |
| dpad | [g636](../../neptune/single-set-default_hold-gyro_latest.json#L4845) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| gyro | [g639](../../neptune/single-set-default_hold-gyro_latest.json#L5000) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g684](../../neptune/single-set-default_hold-gyro_latest.json#L5969) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "layout": "0", "edge_binding_radius": "21000", "edge_binding_invert": "0"}` |
| right_joystick | [g1289](../../neptune/single-set-default_hold-gyro_latest.json#L10193) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "requires_click": "0", "layout": "0", "deadzone": "13276", "edge_binding_radius": "21000"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g624 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4581) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4593) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F3 |
| [g624 button_a chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4602) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F3 |
| [g624 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4617) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4629) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F2 |
| [g624 button_b chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4638) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F2 |
| [g624 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4653) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4665) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F4 |
| [g624 button_x chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4674) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F4 |
| [g624 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4689) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4701) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F1 |
| [g624 button_y chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4710) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F1 |
| [g625 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4736) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g625 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4748) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F12 |
| [g625 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4757) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F12 |
| [g625 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4772) | press empty | `{}` | empty_binding |
| [g626 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4793) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g626 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4805) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F11 |
| [g626 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4814) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F11 |
| [g626 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4829) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g636 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4853) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4865) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F5 |
| [g636 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4874) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F5 |
| [g636 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4889) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4901) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F7 |
| [g636 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4910) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F7 |
| [g636 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4925) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4937) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F6 |
| [g636 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4946) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F6 |
| [g636 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4961) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L4973) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F8 |
| [g636 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L4982) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F8 |
| [g684 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L5978) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press BACKSLASH |
| [g684 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L5986) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6002) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press FORWARD_SLASH |
| [g684 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L6010) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6026) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press RIGHT_BRACKET |
| [g684 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L6034) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6050) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press LEFT_BRACKET |
| [g684 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L6058) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6074) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g684 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L6083) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g684 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6093) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g684 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6109) | ordered layer operations | `{"chord_button": "15", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 1 |
| [g684 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6124) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g1289 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10202) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press SEMICOLON |
| [g1289 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10210) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10226) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press SINGLE_QUOTE |
| [g1289 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10234) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10250) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press PERIOD |
| [g1289 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10258) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10274) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press COMMA |
| [g1289 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10282) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10298) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1289 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10307) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1289 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10317) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g1289 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10333) | ordered layer operations | `{"chord_button": "15", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 0 |
| [g1289 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10348) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g627 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15547) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15558) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "15"}` | add_layer Menu Right: Enter; empty_binding; empty_binding |
| [g627 button_menu release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15575) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15591) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15603) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F10 |
| [g627 left_bumper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15612) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F10 |
| [g627 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15627) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15639) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F9 |
| [g627 right_bumper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15648) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F9 |
| [g627 button_back_left chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15664) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g627 button_back_left chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15673) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g627 button_back_left Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15683) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_back_right chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15700) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g627 button_back_right chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15709) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g627 button_back_right Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15719) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_back_left_upper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15736) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g627 button_back_left_upper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15745) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g627 button_back_left_upper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15755) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_back_right_upper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15772) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g627 button_back_right_upper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L15781) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g627 button_back_right_upper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15791) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 left_stick_click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15807) | output/mode replacement candidate | `{}` | mode_shift joystick 1291 |
| [g627 right_stick_click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15817) | output/mode replacement candidate | `{}` | mode_shift right_joystick 1290 |

**Conditional mode-shift bindings** (not the default active mode):

| Exact activator | Classification | Settings | Payload |
|---|---|---|---|
| [g1290 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10380) | output/mode replacement candidate | `{}` | key_press SEMICOLON, ,  |
| [g1290 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10390) | output/mode replacement candidate | `{}` | key_press SINGLE_QUOTE, ,  |
| [g1290 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10400) | output/mode replacement candidate | `{}` | key_press PERIOD, ,  |
| [g1290 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10410) | output/mode replacement candidate | `{}` | key_press COMMA, ,  |
| [g1290 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10420) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1290 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10430) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1290 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10440) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1291 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10464) | output/mode replacement candidate | `{}` | key_press BACKSLASH, ,  |
| [g1291 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10474) | output/mode replacement candidate | `{}` | key_press FORWARD_SLASH, ,  |
| [g1291 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10484) | output/mode replacement candidate | `{}` | key_press RIGHT_BRACKET, ,  |
| [g1291 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10494) | output/mode replacement candidate | `{}` | key_press LEFT_BRACKET, ,  |
| [g1291 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10504) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1291 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10514) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1291 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10524) | press empty | `{}` | controller_action empty_binding, ,  |

## 28. Menu Right: Tab

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1116](../../neptune/single-set-default_hold-gyro_latest.json#L9120) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1117](../../neptune/single-set-default_hold-gyro_latest.json#L9130) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g1118](../../neptune/single-set-default_hold-gyro_latest.json#L9154) / **trigger** | click | `{"layer": "1"}` |
| switch | [g1119](../../neptune/single-set-default_hold-gyro_latest.json#L16982) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g1171](../../neptune/single-set-default_hold-gyro_latest.json#L9628) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1172](../../neptune/single-set-default_hold-gyro_latest.json#L9667) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g1204](../../neptune/single-set-default_hold-gyro_latest.json#L9732) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1117 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9138) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1118 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9162) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1171 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9636) | press empty | `{}` | empty_binding |
| [g1171 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9646) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Right: Double Tap Cover |
| [g1172 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9675) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Right: Double Tap Cover |
| [g1119 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16990) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press TAB |
| [g1119 button_escape release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16998) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Right: Double Tap; remove_layer Menu Right: Tab |
| [g1119 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17009) | ordered layer operations | `{"chord_button": "14", "delay_start": "150", "interruptable": "0"}` | add_layer Menu Right: Double Tap Cover |
| [g1119 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17024) | press empty | `{}` | empty_binding |
| [g1119 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17034) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1119 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17044) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |

## 29. Menu Right: Enter

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g13050](../../neptune/single-set-default_hold-gyro_latest.json#L18446) / **switches** | button_escape | `{"layer": "1"}` |
| gyro | [g13051](../../neptune/single-set-default_hold-gyro_latest.json#L18478) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13050 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18454) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press RETURN |
| [g13050 button_escape release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18462) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Right: Enter |

## 30. Menu Right: Fn Layer

Pure empty entries by activation: `{"Full_Press": 2, "chord": 12}`. Mixed entries containing empty subcommands: **1**. Chord-protected cleanup entries: **19**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1317](../../neptune/single-set-default_hold-gyro_latest.json#L10795) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g1318](../../neptune/single-set-default_hold-gyro_latest.json#L10950) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1319](../../neptune/single-set-default_hold-gyro_latest.json#L11007) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1320](../../neptune/single-set-default_hold-gyro_latest.json#L17159) / **switches** | button_escape, button_menu, left_bumper, right_bumper, button_back_left, button_back_right, button_back_left_upper, button_back_right_upper, left_stick_click, right_stick_click | `{"layer": "1"}` |
| dpad | [g1329](../../neptune/single-set-default_hold-gyro_latest.json#L11067) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| joystick | [g1330](../../neptune/single-set-default_hold-gyro_latest.json#L11222) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "layout": "0", "edge_binding_radius": "21000", "edge_binding_invert": "0"}` |
| right_joystick | [g1331](../../neptune/single-set-default_hold-gyro_latest.json#L11400) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "requires_click": "0", "layout": "0", "deadzone": "13276", "edge_binding_radius": "21000"}` |
| gyro | [g1332](../../neptune/single-set-default_hold-gyro_latest.json#L11579) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1317 button_a Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10803) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_a chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10815) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F3 |
| [g1317 button_a chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10824) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F3 |
| [g1317 button_b Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10839) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_b chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10851) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F2 |
| [g1317 button_b chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10860) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F2 |
| [g1317 button_x Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10875) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_x chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10887) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F4 |
| [g1317 button_x chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10896) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F4 |
| [g1317 button_y Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10911) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_y chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10923) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F1 |
| [g1317 button_y chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10932) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F1 |
| [g1318 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10958) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1318 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10970) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F12 |
| [g1318 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10979) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F12 |
| [g1318 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10994) | press empty | `{}` | empty_binding |
| [g1319 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11015) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1319 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11027) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F11 |
| [g1319 click chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11036) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F11 |
| [g1319 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11051) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1329 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11075) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11087) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F5 |
| [g1329 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11096) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F5 |
| [g1329 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11111) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11123) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F7 |
| [g1329 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11132) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F7 |
| [g1329 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11147) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11159) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F6 |
| [g1329 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11168) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F6 |
| [g1329 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11183) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11195) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F8 |
| [g1329 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11204) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F8 |
| [g1330 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11231) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press BACKSLASH |
| [g1330 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11239) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11255) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press FORWARD_SLASH |
| [g1330 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11263) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11279) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press RIGHT_BRACKET |
| [g1330 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11287) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11303) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press LEFT_BRACKET |
| [g1330 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11311) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11327) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1330 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11336) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1330 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11346) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1330 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11362) | ordered layer operations | `{"chord_button": "14", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 1 |
| [g1330 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11377) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g1331 dpad_north chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11409) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press SEMICOLON |
| [g1331 dpad_north chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11417) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 dpad_south chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11433) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press SINGLE_QUOTE |
| [g1331 dpad_south chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11441) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 dpad_east chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11457) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press PERIOD |
| [g1331 dpad_east chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11465) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 dpad_west chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11481) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press COMMA |
| [g1331 dpad_west chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11489) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11505) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1331 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L11514) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1331 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11524) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1331 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11540) | ordered layer operations | `{"chord_button": "14", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 0 |
| [g1331 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L11555) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g1320 button_escape release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17167) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17183) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17194) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "14"}` | add_layer Menu Left: Backspace; empty_binding; empty_binding |
| [g1320 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17211) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 left_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17223) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F10 |
| [g1320 left_bumper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17232) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F10 |
| [g1320 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17247) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 right_bumper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17259) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F9 |
| [g1320 right_bumper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17268) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F9 |
| [g1320 button_back_left chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17284) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g1320 button_back_left chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17293) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g1320 button_back_left Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17303) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_back_right chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17320) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g1320 button_back_right chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17329) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g1320 button_back_right Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17339) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_back_left_upper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17356) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g1320 button_back_left_upper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17365) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g1320 button_back_left_upper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17375) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_back_right_upper chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17392) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g1320 button_back_right_upper chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L17401) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g1320 button_back_right_upper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17411) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 left_stick_click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17427) | output/mode replacement candidate | `{}` | mode_shift joystick 12910 |
| [g1320 right_stick_click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17437) | output/mode replacement candidate | `{}` | mode_shift right_joystick 12900 |

**Conditional mode-shift bindings** (not the default active mode):

| Exact activator | Classification | Settings | Payload |
|---|---|---|---|
| [g12900 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10547) | output/mode replacement candidate | `{}` | key_press SEMICOLON, ,  |
| [g12900 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10557) | output/mode replacement candidate | `{}` | key_press SINGLE_QUOTE, ,  |
| [g12900 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10567) | output/mode replacement candidate | `{}` | key_press PERIOD, ,  |
| [g12900 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10577) | output/mode replacement candidate | `{}` | key_press COMMA, ,  |
| [g12900 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10587) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12900 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10597) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12900 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10607) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12910 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10631) | output/mode replacement candidate | `{}` | key_press BACKSLASH, ,  |
| [g12910 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10641) | output/mode replacement candidate | `{}` | key_press FORWARD_SLASH, ,  |
| [g12910 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10651) | output/mode replacement candidate | `{}` | key_press RIGHT_BRACKET, ,  |
| [g12910 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10661) | output/mode replacement candidate | `{}` | key_press LEFT_BRACKET, ,  |
| [g12910 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10671) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12910 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10681) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12910 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10691) | press empty | `{}` | controller_action empty_binding, ,  |

## 31. LST: Entry Point

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g829](../../neptune/single-set-default_hold-gyro_latest.json#L7524) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g830](../../neptune/single-set-default_hold-gyro_latest.json#L7534) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g831](../../neptune/single-set-default_hold-gyro_latest.json#L7544) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g832](../../neptune/single-set-default_hold-gyro_latest.json#L16105) / **switches** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g851](../../neptune/single-set-default_hold-gyro_latest.json#L7601) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g851 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7609) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer LST: Double Tap; remove_layer LST: Entry Point |
| [g851 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7620) | ordered layer operations | `{"chord_button": "23", "delay_start": "150", "interruptable": "0"}` | add_layer LST: Tap Cover |

## 32. RST: Entry Point

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g825](../../neptune/single-set-default_hold-gyro_latest.json#L7494) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g826](../../neptune/single-set-default_hold-gyro_latest.json#L7504) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g827](../../neptune/single-set-default_hold-gyro_latest.json#L7514) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g828](../../neptune/single-set-default_hold-gyro_latest.json#L16095) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g849](../../neptune/single-set-default_hold-gyro_latest.json#L7554) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g849 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7562) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer RST: Double Tap; remove_layer RST: Entry Point |
| [g849 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7573) | ordered layer operations | `{"chord_button": "24", "delay_start": "150", "interruptable": "0"}` | add_layer RST: Tap Cover |

## 33. RTP: Entry Point

Pure empty entries by activation: `{"chord": 1}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **1**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g983](../../neptune/single-set-default_hold-gyro_latest.json#L8493) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g984](../../neptune/single-set-default_hold-gyro_latest.json#L8503) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g985](../../neptune/single-set-default_hold-gyro_latest.json#L16594) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1032](../../neptune/single-set-default_hold-gyro_latest.json#L8720) / **absolute_mouse** | touch | `{"layer": "1"}` |
| right_joystick | [g1163](../../neptune/single-set-default_hold-gyro_latest.json#L9341) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1164](../../neptune/single-set-default_hold-gyro_latest.json#L9395) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1032 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8728) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer RTP: Double Tap; remove_layer RTP: Entry Point |
| [g1032 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8739) | ordered layer operations | `{"chord_button": "17", "haptic_intensity": "0", "delay_start": "150", "interruptable": "0"}` | add_layer RTP: Tap Cover |
| [g1163 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9349) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g1163 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9358) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Entry Point; remove_layer RTP: Tap Cover |
| [g1163 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9374) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer RTP: Tap Cover |
| [g1164 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9403) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer RTP: Tap Cover |

## 34. Menu Left: Entry Point

Pure empty entries by activation: `{"Full_Press": 2, "chord": 3}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g869](../../neptune/single-set-default_hold-gyro_latest.json#L7684) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g870](../../neptune/single-set-default_hold-gyro_latest.json#L7708) / **trigger** | click | `{"layer": "1"}` |
| switch | [g871](../../neptune/single-set-default_hold-gyro_latest.json#L16115) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g1161](../../neptune/single-set-default_hold-gyro_latest.json#L9214) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g1162](../../neptune/single-set-default_hold-gyro_latest.json#L9290) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13033](../../neptune/single-set-default_hold-gyro_latest.json#L14465) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g869 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7692) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g870 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7716) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1161 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9222) | ordered layer operations | `{"chord_button": "15"}` | add_layer Menu Left: Fn Layer |
| [g1161 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9235) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1161 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9244) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g1161 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9260) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Left: Fn Layer |
| [g1161 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9273) | conditional empty | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1162 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9298) | ordered layer operations | `{"chord_button": "15"}` | add_layer Menu Left: Fn Layer |
| [g1162 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9311) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Left: Fn Layer |
| [g1162 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9324) | conditional empty | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g871 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16123) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "15", "interruptable": "0"}` | add_layer Menu Right: Enter; add_layer Menu Left: Fn Layer; empty_binding |
| [g871 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16136) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Entry Point |
| [g871 button_menu release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16149) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Left: Double Tap; remove_layer Menu Left: Entry Point |
| [g871 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16160) | mixed empty + real commands; ordered layer operations | `{"chord_button": "15", "delay_start": "300"}` | add_layer Menu Left: Fn Layer 0 1; empty_binding |
| [g871 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16172) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "350", "interruptable": "0"}` | remove_layer Menu Left: Fn Layer |
| [g871 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16187) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g871 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16197) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |

## 35. Menu Right: Entry Point

Pure empty entries by activation: `{"Full_Press": 2, "chord": 3}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g13042](../../neptune/single-set-default_hold-gyro_latest.json#L18126) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g13043](../../neptune/single-set-default_hold-gyro_latest.json#L18150) / **trigger** | click | `{"layer": "1"}` |
| switch | [g13044](../../neptune/single-set-default_hold-gyro_latest.json#L18174) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g13045](../../neptune/single-set-default_hold-gyro_latest.json#L18269) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g13046](../../neptune/single-set-default_hold-gyro_latest.json#L18345) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13047](../../neptune/single-set-default_hold-gyro_latest.json#L18396) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13042 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18134) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g13043 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18158) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g13044 button_escape release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18182) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Right: Double Tap; remove_layer Menu Right: Entry Point |
| [g13044 button_escape chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18193) | mixed empty + real commands; ordered layer operations | `{"chord_button": "14", "delay_start": "300"}` | add_layer Menu Right: Fn Layer 0 1; empty_binding |
| [g13044 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18205) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "350", "interruptable": "0"}` | remove_layer Menu Right: Fn Layer |
| [g13044 button_menu chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18220) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "14", "interruptable": "0"}` | add_layer Menu Left: Backspace; add_layer Menu Right: Fn Layer; empty_binding |
| [g13044 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18233) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Entry Point |
| [g13044 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18246) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g13044 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18256) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g13045 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18277) | ordered layer operations | `{"chord_button": "14"}` | add_layer Menu Right: Fn Layer |
| [g13045 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18290) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g13045 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18299) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g13045 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18315) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Right: Fn Layer |
| [g13045 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18328) | conditional empty | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g13046 click chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18353) | ordered layer operations | `{"chord_button": "14"}` | add_layer Menu Right: Fn Layer |
| [g13046 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18366) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Right: Fn Layer |
| [g13046 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L18379) | conditional empty | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |

## 36. L1: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g891](../../neptune/single-set-default_hold-gyro_latest.json#L7764) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g892](../../neptune/single-set-default_hold-gyro_latest.json#L7788) / **trigger** | click | `{"layer": "1"}` |
| switch | [g893](../../neptune/single-set-default_hold-gyro_latest.json#L16210) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g922](../../neptune/single-set-default_hold-gyro_latest.json#L7986) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g923](../../neptune/single-set-default_hold-gyro_latest.json#L8025) / **dpad** | touch | `{"layer": "1"}` |
| right_trackpad | [g925](../../neptune/single-set-default_hold-gyro_latest.json#L8075) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g927](../../neptune/single-set-default_hold-gyro_latest.json#L8094) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g891 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7772) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g892 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7796) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g922 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7994) | press empty | `{}` | empty_binding |
| [g922 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8004) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer L1: Double Tap |
| [g923 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8033) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer L1: Double Tap |
| [g893 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16218) | press empty | `{}` | empty_binding |
| [g893 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16228) | press empty | `{}` | empty_binding |
| [g893 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16238) | ordered layer operations | `{}` | add_layer L1: Scroll Down; remove_layer L1: Double Tap |
| [g893 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16251) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g893 always_on_action Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16262) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer L1: Double Tap |
| [g893 always_on_action Full_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L16271) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |

**Always On ordering:** 3 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`D:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 923 |
| right_joystick / edge (`D:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 922 |
| right_joystick / edge (`D:15:edge:activators:chord:0`) | input explicitly redefined; groups 922 |
| right_joystick / touch (`D:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 922 |
| left_trackpad / click (`D:190:click:activators:Soft_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_west (`D:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_east (`D:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_north (`D:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_south (`D:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 927 |
| right_trackpad / click (`D:562:click:activators:Soft_Press:0`) | source disabled; groups 925 |
| right_trackpad / touch (`D:562:touch:activators:Full_Press:0`) | source disabled; groups 925 |
| switch / button_escape (`D:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 893 |
| switch / button_menu (`D:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 893 |
| switch / left_bumper (`D:10:left_bumper:activators:chord:0`) | input explicitly redefined; groups 893 |
| switch / right_bumper (`D:10:right_bumper:activators:chord:0`) | input explicitly redefined; groups 893 |

## 37. R1: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g895](../../neptune/single-set-default_hold-gyro_latest.json#L7822) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g896](../../neptune/single-set-default_hold-gyro_latest.json#L7846) / **trigger** | click | `{"layer": "1"}` |
| switch | [g897](../../neptune/single-set-default_hold-gyro_latest.json#L16289) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g928](../../neptune/single-set-default_hold-gyro_latest.json#L8103) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g929](../../neptune/single-set-default_hold-gyro_latest.json#L8142) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g930](../../neptune/single-set-default_hold-gyro_latest.json#L8171) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g931](../../neptune/single-set-default_hold-gyro_latest.json#L8180) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g895 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7830) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g896 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L7854) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g928 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8111) | press empty | `{}` | empty_binding |
| [g928 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8121) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer R1: Double Tap |
| [g929 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8150) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer R1: Double Tap |
| [g897 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16297) | press empty | `{}` | empty_binding |
| [g897 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16307) | press empty | `{}` | empty_binding |
| [g897 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16317) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g897 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16327) | ordered layer operations | `{}` | add_layer R1: Scroll Up; remove_layer R1: Double Tap |
| [g897 always_on_action Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16341) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer R1: Double Tap |
| [g897 always_on_action Full_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L16350) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | mouse_wheel SCROLL_UP |

**Always On ordering:** 3 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`D:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 929 |
| right_joystick / edge (`D:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 928 |
| right_joystick / edge (`D:15:edge:activators:chord:0`) | input explicitly redefined; groups 928 |
| right_joystick / touch (`D:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 928 |
| left_trackpad / click (`D:190:click:activators:Soft_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_west (`D:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_east (`D:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_north (`D:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_south (`D:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 930 |
| right_trackpad / click (`D:562:click:activators:Soft_Press:0`) | source disabled; groups 931 |
| right_trackpad / touch (`D:562:touch:activators:Full_Press:0`) | source disabled; groups 931 |
| switch / button_escape (`D:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 897 |
| switch / button_menu (`D:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 897 |
| switch / left_bumper (`D:10:left_bumper:activators:chord:0`) | input explicitly redefined; groups 897 |
| switch / right_bumper (`D:10:right_bumper:activators:chord:0`) | input explicitly redefined; groups 897 |

## 38. LST: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g751](../../neptune/single-set-default_hold-gyro_latest.json#L6507) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g752](../../neptune/single-set-default_hold-gyro_latest.json#L6528) / **trigger** | click | `{"layer": "1"}` |
| switch | [g753](../../neptune/single-set-default_hold-gyro_latest.json#L15895) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g763](../../neptune/single-set-default_hold-gyro_latest.json#L6587) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g769](../../neptune/single-set-default_hold-gyro_latest.json#L6655) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g858](../../neptune/single-set-default_hold-gyro_latest.json#L7656) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g859](../../neptune/single-set-default_hold-gyro_latest.json#L7665) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g751 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6515) | press empty | `{}` | empty_binding |
| [g752 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6536) | press empty | `{}` | empty_binding |
| [g763 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6595) | press empty | `{}` | empty_binding |
| [g763 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6605) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer LST: Double Tap |
| [g769 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6663) | ordered layer operations | `{"haptic_intensity": "3"}` | add_layer LST: Temporary Gyro; add_layer LST: Entry Point; remove_layer LST: Double Tap |
| [g753 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15903) | press empty | `{}` | empty_binding |
| [g753 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15913) | press empty | `{}` | empty_binding |
| [g753 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15923) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g753 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15933) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g753 always_on_action Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15943) | ordered layer operations; Always On | `{"delay_start": "200", "interruptable": "0"}` | remove_layer LST: Double Tap |

**Always On ordering:** 1 incoming bindings add this layer last; 3 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`D:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 769 |
| right_joystick / edge (`D:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 763 |
| right_joystick / edge (`D:15:edge:activators:chord:0`) | input explicitly redefined; groups 763 |
| right_joystick / touch (`D:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 763 |
| left_trackpad / click (`D:190:click:activators:Soft_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_west (`D:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_east (`D:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_north (`D:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_south (`D:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 858 |
| right_trackpad / click (`D:562:click:activators:Soft_Press:0`) | source disabled; groups 859 |
| right_trackpad / touch (`D:562:touch:activators:Full_Press:0`) | source disabled; groups 859 |
| switch / button_escape (`D:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 753 |
| switch / button_menu (`D:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 753 |
| switch / left_bumper (`D:10:left_bumper:activators:chord:0`) | input explicitly redefined; groups 753 |
| switch / right_bumper (`D:10:right_bumper:activators:chord:0`) | input explicitly redefined; groups 753 |

## 39. RST: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g747](../../neptune/single-set-default_hold-gyro_latest.json#L6455) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g748](../../neptune/single-set-default_hold-gyro_latest.json#L6476) / **trigger** | click | `{"layer": "1"}` |
| switch | [g749](../../neptune/single-set-default_hold-gyro_latest.json#L15830) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g762](../../neptune/single-set-default_hold-gyro_latest.json#L6549) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g768](../../neptune/single-set-default_hold-gyro_latest.json#L6626) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g856](../../neptune/single-set-default_hold-gyro_latest.json#L7638) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g857](../../neptune/single-set-default_hold-gyro_latest.json#L7647) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g747 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6463) | press empty | `{}` | empty_binding |
| [g748 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6484) | press empty | `{}` | empty_binding |
| [g762 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6557) | press empty | `{}` | empty_binding |
| [g762 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6567) | ordered layer operations | `{"haptic_intensity": "3"}` | add_layer RST: Temporary Gyro; add_layer RST: Entry Point; remove_layer RST: Double Tap |
| [g768 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6634) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer RST: Double Tap |
| [g749 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15838) | press empty | `{}` | empty_binding |
| [g749 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15848) | press empty | `{}` | empty_binding |
| [g749 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15858) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g749 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15868) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g749 always_on_action Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15878) | ordered layer operations; Always On | `{"delay_start": "200", "interruptable": "0"}` | remove_layer RST: Double Tap |

**Always On ordering:** 1 incoming bindings add this layer last; 3 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`D:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 768 |
| right_joystick / edge (`D:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 762 |
| right_joystick / edge (`D:15:edge:activators:chord:0`) | input explicitly redefined; groups 762 |
| right_joystick / touch (`D:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 762 |
| left_trackpad / click (`D:190:click:activators:Soft_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_west (`D:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_east (`D:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_north (`D:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_south (`D:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 856 |
| right_trackpad / click (`D:562:click:activators:Soft_Press:0`) | source disabled; groups 857 |
| right_trackpad / touch (`D:562:touch:activators:Full_Press:0`) | source disabled; groups 857 |
| switch / button_escape (`D:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 749 |
| switch / button_menu (`D:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 749 |
| switch / left_bumper (`D:10:left_bumper:activators:chord:0`) | input explicitly redefined; groups 749 |
| switch / right_bumper (`D:10:right_bumper:activators:chord:0`) | input explicitly redefined; groups 749 |

## 40. RTP: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g987](../../neptune/single-set-default_hold-gyro_latest.json#L8523) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g988](../../neptune/single-set-default_hold-gyro_latest.json#L8544) / **trigger** | click | `{"layer": "1"}` |
| switch | [g989](../../neptune/single-set-default_hold-gyro_latest.json#L16604) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g1023](../../neptune/single-set-default_hold-gyro_latest.json#L8595) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1024](../../neptune/single-set-default_hold-gyro_latest.json#L8634) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g1027](../../neptune/single-set-default_hold-gyro_latest.json#L8711) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1298](../../neptune/single-set-default_hold-gyro_latest.json#L10706) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge | `{"layer": "1", "requires_click": "0", "layout": "0", "deadzone": "18190", "edge_binding_radius": "22250", "edge_binding_invert": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g987 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8531) | press empty | `{}` | empty_binding |
| [g988 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8552) | press empty | `{}` | empty_binding |
| [g1023 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8603) | press empty | `{}` | empty_binding |
| [g1023 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8613) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer RTP: Double Tap |
| [g1024 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8642) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer RTP: Double Tap |
| [g1298 dpad_north Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10714) | ordered layer operations | `{"haptic_intensity": "3", "interruptable": "0"}` | add_layer RTP: Circular Scroll; remove_layer RTP: Double Tap |
| [g1298 dpad_south Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10731) | ordered layer operations | `{"haptic_intensity": "3", "interruptable": "0"}` | add_layer RTP: Circular Scroll; remove_layer RTP: Double Tap |
| [g1298 dpad_east Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10748) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Double Tap |
| [g1298 dpad_west Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10761) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Double Tap |
| [g1298 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10774) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Double Tap |
| [g989 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16612) | press empty | `{}` | empty_binding |
| [g989 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16622) | press empty | `{}` | empty_binding |
| [g989 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16632) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g989 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16642) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g989 always_on_action Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16652) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer RTP: Double Tap |

**Always On ordering:** 1 incoming bindings add this layer last; 8 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`D:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1024 |
| right_joystick / edge (`D:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1023 |
| right_joystick / edge (`D:15:edge:activators:chord:0`) | input explicitly redefined; groups 1023 |
| right_joystick / touch (`D:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1023 |
| left_trackpad / click (`D:190:click:activators:Soft_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_west (`D:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_east (`D:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_north (`D:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_south (`D:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 1027 |
| right_trackpad / click (`D:562:click:activators:Soft_Press:0`) | source mode replaced; runtime inheritance check; groups 1298 |
| right_trackpad / touch (`D:562:touch:activators:Full_Press:0`) | source mode replaced; runtime inheritance check; groups 1298 |
| switch / button_escape (`D:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 989 |
| switch / button_menu (`D:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 989 |
| switch / left_bumper (`D:10:left_bumper:activators:chord:0`) | input explicitly redefined; groups 989 |
| switch / right_bumper (`D:10:right_bumper:activators:chord:0`) | input explicitly redefined; groups 989 |

## 41. Menu Left: Double Tap

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1044](../../neptune/single-set-default_hold-gyro_latest.json#L8886) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1045](../../neptune/single-set-default_hold-gyro_latest.json#L8896) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g1046](../../neptune/single-set-default_hold-gyro_latest.json#L8920) / **trigger** | click | `{"layer": "1"}` |
| switch | [g1047](../../neptune/single-set-default_hold-gyro_latest.json#L16679) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| left_trackpad | [g1148](../../neptune/single-set-default_hold-gyro_latest.json#L9196) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1149](../../neptune/single-set-default_hold-gyro_latest.json#L9205) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g1165](../../neptune/single-set-default_hold-gyro_latest.json#L9424) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1166](../../neptune/single-set-default_hold-gyro_latest.json#L9463) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g13032](../../neptune/single-set-default_hold-gyro_latest.json#L14456) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1045 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8904) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1046 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8928) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1165 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9432) | press empty | `{}` | empty_binding |
| [g1165 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9442) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer Menu Left: Double Tap |
| [g1166 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9471) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer Menu Left: Double Tap |
| [g1047 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16687) | press empty | `{}` | empty_binding |
| [g1047 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16697) | ordered layer operations | `{}` | add_layer Menu Left: Escape; remove_layer Menu Left: Double Tap |
| [g1047 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16710) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1047 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16720) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1047 always_on_action Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16731) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer Menu Left: Double Tap |
| [g1047 always_on_action Full_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L16740) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | key_press ESCAPE |

**Always On ordering:** 2 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`D:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1166 |
| right_joystick / edge (`D:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1165 |
| right_joystick / edge (`D:15:edge:activators:chord:0`) | input explicitly redefined; groups 1165 |
| right_joystick / touch (`D:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1165 |
| left_trackpad / click (`D:190:click:activators:Soft_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_west (`D:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_east (`D:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_north (`D:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_south (`D:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 1148 |
| right_trackpad / click (`D:562:click:activators:Soft_Press:0`) | source disabled; groups 1149 |
| right_trackpad / touch (`D:562:touch:activators:Full_Press:0`) | source disabled; groups 1149 |
| switch / button_escape (`D:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 1047 |
| switch / button_menu (`D:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 1047 |
| switch / left_bumper (`D:10:left_bumper:activators:chord:0`) | input explicitly redefined; groups 1047 |
| switch / right_bumper (`D:10:right_bumper:activators:chord:0`) | input explicitly redefined; groups 1047 |

## 42. Menu Right: Double Tap

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1048](../../neptune/single-set-default_hold-gyro_latest.json#L8944) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1049](../../neptune/single-set-default_hold-gyro_latest.json#L8954) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g1050](../../neptune/single-set-default_hold-gyro_latest.json#L8978) / **trigger** | click | `{"layer": "1"}` |
| switch | [g1051](../../neptune/single-set-default_hold-gyro_latest.json#L16758) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| left_trackpad | [g1144](../../neptune/single-set-default_hold-gyro_latest.json#L9178) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1145](../../neptune/single-set-default_hold-gyro_latest.json#L9187) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g1167](../../neptune/single-set-default_hold-gyro_latest.json#L9492) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1168](../../neptune/single-set-default_hold-gyro_latest.json#L9531) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g1200](../../neptune/single-set-default_hold-gyro_latest.json#L9696) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1049 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8962) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1050 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8986) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1167 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9500) | press empty | `{}` | empty_binding |
| [g1167 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9510) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer Menu Right: Double Tap |
| [g1168 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9539) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer Menu Right: Double Tap |
| [g1051 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16766) | ordered layer operations | `{}` | add_layer Menu Right: Tab; remove_layer Menu Right: Double Tap |
| [g1051 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16779) | press empty | `{}` | empty_binding |
| [g1051 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16789) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1051 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16799) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1051 always_on_action Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16810) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer Menu Right: Double Tap |
| [g1051 always_on_action Full_Press[1]](../../neptune/single-set-default_hold-gyro_latest.json#L16819) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | key_press TAB |

**Always On ordering:** 2 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`D:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1168 |
| right_joystick / edge (`D:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1167 |
| right_joystick / edge (`D:15:edge:activators:chord:0`) | input explicitly redefined; groups 1167 |
| right_joystick / touch (`D:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1167 |
| left_trackpad / click (`D:190:click:activators:Soft_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_west (`D:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_east (`D:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_north (`D:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_south (`D:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 1144 |
| right_trackpad / click (`D:562:click:activators:Soft_Press:0`) | source disabled; groups 1145 |
| right_trackpad / touch (`D:562:touch:activators:Full_Press:0`) | source disabled; groups 1145 |
| switch / button_escape (`D:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 1051 |
| switch / button_menu (`D:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 1051 |
| switch / left_bumper (`D:10:left_bumper:activators:chord:0`) | input explicitly redefined; groups 1051 |
| switch / right_bumper (`D:10:right_bumper:activators:chord:0`) | input explicitly redefined; groups 1051 |

## 43. L1: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g775](../../neptune/single-set-default_hold-gyro_latest.json#L6693) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g776](../../neptune/single-set-default_hold-gyro_latest.json#L6703) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g777](../../neptune/single-set-default_hold-gyro_latest.json#L15960) / **switches** | left_bumper | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g777 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15968) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; remove_layer L1: Tap Cover |

## 44. R1: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g779](../../neptune/single-set-default_hold-gyro_latest.json#L6723) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g780](../../neptune/single-set-default_hold-gyro_latest.json#L6733) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g781](../../neptune/single-set-default_hold-gyro_latest.json#L15988) / **switches** | right_bumper | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g781 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L15996) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; remove_layer R1: Tap Cover |

## 45. L1&R1: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g810](../../neptune/single-set-default_hold-gyro_latest.json#L6921) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g811](../../neptune/single-set-default_hold-gyro_latest.json#L6931) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g812](../../neptune/single-set-default_hold-gyro_latest.json#L16036) / **switches** | left_bumper, right_bumper | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g812 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16044) | mixed empty + real commands; ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; remove_layer L1: Modifier 0; remove_layer Gyro \| L1: Modifier 0; empty_binding; remove_layer L1: Tap Cover; empty_binding; remove_layer L1&R1: Tap Cover |
| [g812 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16068) | mixed empty + real commands; ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer L1!R1: Modifier 2; remove_layer Gyro \| L1!R1: Modifier 2; remove_layer R1!L1: Modifier 2; remove_layer Gyro \| R1!L1: Modifier 2; empty_binding; remove_layer R1: Modifier 1; remove_layer Gyro \| R1: Modifier 1; empty_binding; remove_layer R1: Tap Cover; remove_layer L1&R1: Tap Cover |

## 46. LST: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g797](../../neptune/single-set-default_hold-gyro_latest.json#L6837) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g798](../../neptune/single-set-default_hold-gyro_latest.json#L6847) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g799](../../neptune/single-set-default_hold-gyro_latest.json#L16026) / **switches** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g801](../../neptune/single-set-default_hold-gyro_latest.json#L6884) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g801 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6892) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 47. RST: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g783](../../neptune/single-set-default_hold-gyro_latest.json#L6753) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g784](../../neptune/single-set-default_hold-gyro_latest.json#L6763) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g785](../../neptune/single-set-default_hold-gyro_latest.json#L16016) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g800](../../neptune/single-set-default_hold-gyro_latest.json#L6857) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g800 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L6865) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 48. RTP: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g991](../../neptune/single-set-default_hold-gyro_latest.json#L8575) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g992](../../neptune/single-set-default_hold-gyro_latest.json#L8585) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g993](../../neptune/single-set-default_hold-gyro_latest.json#L16669) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1033](../../neptune/single-set-default_hold-gyro_latest.json#L8758) / **absolute_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1033 touch release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L8766) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Entry Point; remove_layer RTP: Tap Cover |

## 49. L1: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g949](../../neptune/single-set-default_hold-gyro_latest.json#L8433) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g950](../../neptune/single-set-default_hold-gyro_latest.json#L8443) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g951](../../neptune/single-set-default_hold-gyro_latest.json#L16520) / **switches** | left_bumper | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g951 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16528) | output/mode replacement candidate | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |
| [g951 left_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16538) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer L1: Scroll Down; remove_layer L1: Double Tap Cover |

## 50. R1: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g953](../../neptune/single-set-default_hold-gyro_latest.json#L8463) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g954](../../neptune/single-set-default_hold-gyro_latest.json#L8473) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g955](../../neptune/single-set-default_hold-gyro_latest.json#L16557) / **switches** | right_bumper | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g955 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16565) | output/mode replacement candidate | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | mouse_wheel SCROLL_UP |
| [g955 right_bumper release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16575) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer R1: Scroll Up; remove_layer R1: Double Tap Cover |

## 51. Menu Left: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1052](../../neptune/single-set-default_hold-gyro_latest.json#L9002) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1053](../../neptune/single-set-default_hold-gyro_latest.json#L9012) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g1054](../../neptune/single-set-default_hold-gyro_latest.json#L9022) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g1055](../../neptune/single-set-default_hold-gyro_latest.json#L16837) / **switches** | button_menu | `{"layer": "1"}` |
| gyro | [g1201](../../neptune/single-set-default_hold-gyro_latest.json#L9705) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1055 button_menu Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16845) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press ESCAPE |
| [g1055 button_menu release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16853) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Left: Escape; remove_layer Menu Left: Double Tap Cover |

## 52. Menu Right: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1056](../../neptune/single-set-default_hold-gyro_latest.json#L9032) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1057](../../neptune/single-set-default_hold-gyro_latest.json#L9042) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g1058](../../neptune/single-set-default_hold-gyro_latest.json#L9052) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g1059](../../neptune/single-set-default_hold-gyro_latest.json#L16872) / **switches** | button_escape | `{"layer": "1"}` |
| gyro | [g1202](../../neptune/single-set-default_hold-gyro_latest.json#L9714) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1059 button_escape Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16880) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press TAB |
| [g1059 button_escape release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L16888) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Right: Tab; remove_layer Menu Right: Double Tap Cover |

## 53. Transition Set 0

Pure empty entries by activation: `{"Full_Press": 4, "chord": 6, "release": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g1218](../../neptune/single-set-default_hold-gyro_latest.json#L9751) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g1219](../../neptune/single-set-default_hold-gyro_latest.json#L9775) / **trigger** | click | `{"layer": "1"}` |
| switch | [g1220](../../neptune/single-set-default_hold-gyro_latest.json#L17057) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| joystick | [g1233](../../neptune/single-set-default_hold-gyro_latest.json#L9799) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g1234](../../neptune/single-set-default_hold-gyro_latest.json#L9853) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| gyro | [g1241](../../neptune/single-set-default_hold-gyro_latest.json#L9940) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1274](../../neptune/single-set-default_hold-gyro_latest.json#L10175) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g1275](../../neptune/single-set-default_hold-gyro_latest.json#L10184) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1218 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9759) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1219 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9783) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1233 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9807) | press empty | `{}` | empty_binding |
| [g1233 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9818) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1233 touch chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L9827) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1233 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9837) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 0 |
| [g1234 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9861) | press empty | `{}` | empty_binding |
| [g1234 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9872) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1234 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L9881) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1234 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9891) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 0 |
| [g1234 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9905) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1234 touch chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L9914) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1234 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9924) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 0 |
| [g1220 button_escape release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17065) | release empty | `{}` | empty_binding |
| [g1220 button_menu release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17075) | release empty | `{}` | empty_binding |
| [g1220 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17085) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1220 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17095) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |

## 54. Transition Set 1

Pure empty entries by activation: `{"Full_Press": 4, "chord": 6, "release": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g1245](../../neptune/single-set-default_hold-gyro_latest.json#L9959) / **trigger** | click | `{"layer": "1"}` |
| right_trigger | [g1246](../../neptune/single-set-default_hold-gyro_latest.json#L9983) / **trigger** | click | `{"layer": "1"}` |
| switch | [g1247](../../neptune/single-set-default_hold-gyro_latest.json#L17108) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| joystick | [g1260](../../neptune/single-set-default_hold-gyro_latest.json#L10007) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g1261](../../neptune/single-set-default_hold-gyro_latest.json#L10061) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| gyro | [g1271](../../neptune/single-set-default_hold-gyro_latest.json#L10148) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g1272](../../neptune/single-set-default_hold-gyro_latest.json#L10157) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1273](../../neptune/single-set-default_hold-gyro_latest.json#L10166) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1245 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9967) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1246 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L9991) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1260 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10015) | press empty | `{}` | empty_binding |
| [g1260 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10026) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1260 touch chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10035) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1260 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10045) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 1 |
| [g1261 click Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10069) | press empty | `{}` | empty_binding |
| [g1261 edge chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10080) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1261 edge chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10089) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1261 edge Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10099) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 1 |
| [g1261 touch chord[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10113) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1261 touch chord[1]](../../neptune/single-set-default_hold-gyro_latest.json#L10122) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1261 touch Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L10132) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 1 |
| [g1247 button_escape release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17116) | release empty | `{}` | empty_binding |
| [g1247 button_menu release[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17126) | release empty | `{}` | empty_binding |
| [g1247 left_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17136) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1247 right_bumper Full_Press[0]](../../neptune/single-set-default_hold-gyro_latest.json#L17146) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
