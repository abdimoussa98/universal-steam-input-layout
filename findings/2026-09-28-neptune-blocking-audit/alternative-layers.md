# Alternative 90.2: blocking in every layer

Source: [neptune/single-set-alternative_hold-gyro_latest.json](../../neptune/single-set-alternative_hold-gyro_latest.json); SHA-256 `cf51a89b8ecf7ccbc8ee83b6cf5c916cf863fb9d8ffb9b67370032dbf0cf5ce0`.

Read [AUDIT.md](AUDIT.md) for the purpose of each blocking family and the author's historical crash workaround. This catalog records every active source and activator, including ordinary outputs and the layers with zero explicit empties. It does not classify all ordinary outputs as intentional blocks. All inactive/unreferenced/conditional entries and source settings are in the CSV inventories.

**Types:** pure empties suppress an input/event; chord guards protect cleanup from firing during valid holds; mixed arrays still execute their real actions; output/mode replacements may intercept lower layer changes. A group with mode `disabled` is a source block; a group with no explicit inputs is not counted as one. The CSV contains complete payloads and sibling activators.

**Inheritance limit:** active source membership and explicit input replacement are structural evidence. They do not prove how every possible stale stack and cross-mode inherited input behaves on the Deck.

## 1. Base

Pure empty entries by activation: `{"Full_Press": 1, "chord": 1}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g10](../../neptune/single-set-alternative_hold-gyro_latest.json#L15425) / **switches** | button_escape, button_menu, left_bumper, right_bumper, button_back_left, button_back_right, button_back_left_upper, button_back_right_upper, left_trackpad_touch, right_trackpad_touch | `{}` |
| button_diamond | [g11](../../neptune/single-set-alternative_hold-gyro_latest.json#L584) / **four_buttons** | button_a, button_b, button_x, button_y | `{"button_size": "17994", "button_dist": "19994"}` |
| joystick | [g12](../../neptune/single-set-alternative_hold-gyro_latest.json#L636) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"requires_click": "0", "deadzone": "13276", "edge_binding_invert": "1"}` |
| left_trigger | [g13](../../neptune/single-set-alternative_hold-gyro_latest.json#L723) / **trigger** | edge | `{"deadzone_inner_radius": "0", "adaptive_threshold": "0"}` |
| right_trigger | [g14](../../neptune/single-set-alternative_hold-gyro_latest.json#L750) / **trigger** | edge | `{"deadzone_inner_radius": "0", "adaptive_threshold": "0"}` |
| right_joystick | [g15](../../neptune/single-set-alternative_hold-gyro_latest.json#L777) / **joystick_mouse** | click, edge, touch | `{"curve_exponent": "0", "custom_curve_exponent": "59", "edge_binding_radius": "32767", "output_joystick": "2", "deadzone_inner_radius": "3280", "deadzone_outer_radius": "32000", "deadzone_enable_type": "2", "sensitivity": "100"}` |
| dpad | [g16](../../neptune/single-set-alternative_hold-gyro_latest.json#L856) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"requires_click": "0", "layout": "0", "haptic_intensity_override": "0"}` |
| left_trackpad | [g190](../../neptune/single-set-alternative_hold-gyro_latest.json#L2292) / **2dscroll** | click, dpad_west, dpad_east, dpad_north, dpad_south | `{"sensitivity": "50"}` |
| right_trackpad | [g562](../../neptune/single-set-alternative_hold-gyro_latest.json#L4086) / **absolute_mouse** | click, touch | `{"haptic_intensity": "0", "friction": "3", "acceleration": "1"}` |
| gyro | [g576](../../neptune/single-set-alternative_hold-gyro_latest.json#L4127) / **gyro_to_mouse** | none explicitly defined | `{"gyro_natural_sensitivity": "300", "flickstick_rotation_sensitivity": "4653", "gyro_vertical_horizontal_ratio": "200", "gyro_precision_speed": "0", "gyro_ratchet_button_mask": "211109453778944", "gyro_ratchet_button_requireany_or_all": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g11 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L592) | output/mode replacement candidate | `{}` | key_press F |
| [g11 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L602) | output/mode replacement candidate | `{}` | key_press V |
| [g11 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L612) | output/mode replacement candidate | `{}` | key_press C |
| [g11 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L622) | output/mode replacement candidate | `{}` | key_press R |
| [g12 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L644) | output/mode replacement candidate | `{}` | key_press W |
| [g12 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L654) | output/mode replacement candidate | `{}` | key_press S |
| [g12 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L664) | output/mode replacement candidate | `{}` | key_press D |
| [g12 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L674) | output/mode replacement candidate | `{}` | key_press A |
| [g12 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L684) | press empty | `{}` | empty_binding |
| [g12 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L694) | output/mode replacement candidate | `{}` | key_press Q |
| [g12 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L704) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | add_layer LST: Entry Point |
| [g13 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L731) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer L2: Modifier 0 |
| [g14 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L758) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer R2: Modifier 1 |
| [g15 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L785) | output/mode replacement candidate | `{}` | key_press E |
| [g15 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L795) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0"}` | add_layer Gyro Off Ramp Up |
| [g15 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L805) | ordered layer operations | `{"hold_repeats": "1", "gyro_ratchet_button_mask": "12", "gyro_ratchet_button_requireany_or_all": "0"}` | add_layer Turning Ramp Up 0 |
| [g15 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L815) | conditional empty | `{"hold_repeats": "1", "interruptable": "0", "gyro_ratchet_button_mask": "50331651", "gyro_ratchet_button_requireany_or_all": "0"}` | empty_binding |
| [g15 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L832) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | add_layer RST: Entry Point |
| [g16 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L864) | output/mode replacement candidate | `{}` | key_press 1 |
| [g16 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L874) | output/mode replacement candidate | `{}` | key_press 3 |
| [g16 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L884) | output/mode replacement candidate | `{}` | key_press 2 |
| [g16 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L894) | output/mode replacement candidate | `{}` | key_press 4 |
| [g190 click Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2300) | ordered layer operations | `{"haptic_intensity": "3"}` | hold_layer LTP: Arrow Keys |
| [g190 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2313) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Escape |
| [g190 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2326) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Enter |
| [g190 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2339) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Tab |
| [g190 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2352) | ordered layer operations | `{"haptic_intensity": "1"}` | add_layer Backspace |
| [g562 click Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4094) | ordered layer operations | `{"haptic_intensity": "3"}` | hold_layer RTP: Mouse Buttons |
| [g562 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4107) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "interruptable": "0"}` | add_layer RTP: Entry Point |
| [g10 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15433) | ordered layer operations | `{"chord_button": "14", "hold_repeats": "1", "interruptable": "0"}` | add_layer Menu Right: Entry Point |
| [g10 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15448) | ordered layer operations | `{"chord_button": "15", "hold_repeats": "1", "interruptable": "0"}` | add_layer Menu Left: Entry Point |
| [g10 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15463) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g10 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15473) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g10 button_back_left Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15483) | output/mode replacement candidate | `{}` | key_press LEFT_CONTROL |
| [g10 button_back_right Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15493) | output/mode replacement candidate | `{}` | key_press LEFT_ALT |
| [g10 button_back_left_upper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15503) | output/mode replacement candidate | `{}` | key_press LEFT_SHIFT |
| [g10 button_back_right_upper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15513) | output/mode replacement candidate | `{}` | key_press SPACE |
| [g10 left_trackpad_touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15524) | output/mode replacement candidate | `{}` | mode_shift dpad 1039 |
| [g10 left_trackpad_touch Full_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15529) | output/mode replacement candidate | `{}` | mode_shift button_diamond 1043 |
| [g10 right_trackpad_touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15541) | output/mode replacement candidate | `{}` | mode_shift dpad 1039 |
| [g10 right_trackpad_touch Full_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15546) | output/mode replacement candidate | `{}` | mode_shift button_diamond 1043 |

**Conditional mode-shift bindings** (not the default active mode):

| Exact activator | Classification | Settings | Payload |
|---|---|---|---|
| [g1039 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9365) | output/mode replacement candidate | `{}` | key_press 1, ,  |
| [g1039 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9375) | output/mode replacement candidate | `{}` | key_press 3, ,  |
| [g1039 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9385) | output/mode replacement candidate | `{}` | key_press 2, ,  |
| [g1039 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9395) | output/mode replacement candidate | `{}` | key_press 4, ,  |
| [g1043 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9418) | output/mode replacement candidate | `{}` | key_press F, ,  |
| [g1043 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9428) | output/mode replacement candidate | `{}` | key_press V, ,  |
| [g1043 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9438) | output/mode replacement candidate | `{}` | key_press C, ,  |
| [g1043 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9448) | output/mode replacement candidate | `{}` | key_press R, ,  |

## 2. Turning Ramp Up 0

Pure empty entries by activation: `{"Full_Press": 2}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g412](../../neptune/single-set-alternative_hold-gyro_latest.json#L3536) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g413](../../neptune/single-set-alternative_hold-gyro_latest.json#L3576) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g414](../../neptune/single-set-alternative_hold-gyro_latest.json#L15851) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g423](../../neptune/single-set-alternative_hold-gyro_latest.json#L3616) / **joystick_mouse** | edge, touch | `{"layer": "1", "sensitivity": "130", "sensitivity_vert_scale": "77"}` |
| joystick | [g737](../../neptune/single-set-alternative_hold-gyro_latest.json#L6703) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g412 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3544) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 0; remove_layer Turning Ramp Up 1; remove_layer Gyro Off Ramp Up; empty_binding |
| [g412 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3563) | press empty | `{}` | empty_binding |
| [g413 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3584) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 0; remove_layer Turning Ramp Up 1; remove_layer Gyro Off Ramp Up; empty_binding |
| [g413 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3603) | press empty | `{}` | empty_binding |
| [g423 edge Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3625) | ordered layer operations | `{"haptic_intensity": "0", "delay_start": "250", "activation_threshold": "29031", "interruptable": "0"}` | add_layer Turning Ramp Up 1 |
| [g423 edge Soft_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3636) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "activation_threshold": "29031", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer Turning Ramp Up 0; remove_layer Turning Ramp Up 1; remove_layer Gyro Off Ramp Up |
| [g423 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3653) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "300", "interruptable": "0"}` | remove_layer Turning Ramp Up 1 |
| [g423 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3668) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g737 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6711) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 3. Turning Ramp Up 1

Pure empty entries by activation: `{"Full_Press": 2}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g540](../../neptune/single-set-alternative_hold-gyro_latest.json#L3948) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g541](../../neptune/single-set-alternative_hold-gyro_latest.json#L3988) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g542](../../neptune/single-set-alternative_hold-gyro_latest.json#L15901) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g551](../../neptune/single-set-alternative_hold-gyro_latest.json#L4028) / **joystick_mouse** | edge, touch | `{"layer": "1", "sensitivity": "160", "sensitivity_vert_scale": "63"}` |
| joystick | [g738](../../neptune/single-set-alternative_hold-gyro_latest.json#L6731) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g540 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3956) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 1; remove_layer Turning Ramp Up 0; remove_layer Gyro Off Ramp Up; empty_binding |
| [g540 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3975) | press empty | `{}` | empty_binding |
| [g541 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3996) | mixed empty + real commands; ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Turning Ramp Up 1; remove_layer Turning Ramp Up 0; remove_layer Gyro Off Ramp Up; empty_binding |
| [g541 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4015) | press empty | `{}` | empty_binding |
| [g551 edge Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4036) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "activation_threshold": "25807", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer Turning Ramp Up 1; remove_layer Turning Ramp Up 0; remove_layer Gyro Off Ramp Up |
| [g551 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4057) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g738 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6739) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 4. L2: Modifier 0

Pure empty entries by activation: `{"chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g59](../../neptune/single-set-alternative_hold-gyro_latest.json#L15597) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g60](../../neptune/single-set-alternative_hold-gyro_latest.json#L1165) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| right_joystick | [g64](../../neptune/single-set-alternative_hold-gyro_latest.json#L1306) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| dpad | [g65](../../neptune/single-set-alternative_hold-gyro_latest.json#L1408) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| left_trigger | [g256](../../neptune/single-set-alternative_hold-gyro_latest.json#L3167) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g257](../../neptune/single-set-alternative_hold-gyro_latest.json#L3202) / **trigger** | edge | `{"layer": "1"}` |
| joystick | [g667](../../neptune/single-set-alternative_hold-gyro_latest.json#L5323) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g60 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1173) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g60 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1182) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press G; add_layer L2: Tap Cover |
| [g60 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1198) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g60 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1207) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press X; add_layer L2: Tap Cover |
| [g60 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1223) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g60 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1232) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press Z; add_layer L2: Tap Cover |
| [g60 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1248) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g60 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1257) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press T; add_layer L2: Tap Cover |
| [g64 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1314) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g64 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1323) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | mouse_button MIDDLE; add_layer L2: Tap Cover |
| [g64 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1339) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g64 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1348) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g64 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1365) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g64 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1377) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g64 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1386) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L2: Tap Cover |
| [g65 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1416) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g65 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1425) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press 9; add_layer L2: Tap Cover |
| [g65 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1441) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g65 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1450) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press DASH; add_layer L2: Tap Cover |
| [g65 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1466) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g65 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1475) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press 0; add_layer L2: Tap Cover |
| [g65 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1491) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g65 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1500) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press EQUALS; add_layer L2: Tap Cover |
| [g256 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3175) | ordered layer operations | `{}` | add_layer L2: Double Tap; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0 |
| [g256 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3184) | ordered layer operations | `{"chord_button": "7", "delay_start": "300", "interruptable": "0"}` | add_layer L2: Tap Cover |
| [g257 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3210) | held-state guard; ordered layer operations | `{"chord_button": "7", "hold_repeats": "1", "interruptable": "0"}` | add_layer L2!R2: Modifier 2; add_layer R2: Tap Cover; add_layer R2: Modifier 1; add_layer L2: Tap Cover |
| [g257 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3225) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g667 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5331) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g667 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5340) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press CAPSLOCK; add_layer L2: Tap Cover |
| [g667 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5356) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g667 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5368) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g667 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5377) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L2: Tap Cover |
| [g59 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15605) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g59 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15614) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press INSERT; add_layer L2: Tap Cover |
| [g59 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15630) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g59 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15639) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press DELETE; add_layer L2: Tap Cover |
| [g59 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15655) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g59 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15665) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 5. R2: Modifier 1

Pure empty entries by activation: `{"chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g157](../../neptune/single-set-alternative_hold-gyro_latest.json#L1710) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| switch | [g160](../../neptune/single-set-alternative_hold-gyro_latest.json#L15678) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g161](../../neptune/single-set-alternative_hold-gyro_latest.json#L1841) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g217](../../neptune/single-set-alternative_hold-gyro_latest.json#L2624) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| left_trigger | [g258](../../neptune/single-set-alternative_hold-gyro_latest.json#L3242) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g259](../../neptune/single-set-alternative_hold-gyro_latest.json#L3281) / **trigger** | edge | `{"layer": "1"}` |
| joystick | [g668](../../neptune/single-set-alternative_hold-gyro_latest.json#L5398) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g157 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1718) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g157 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1727) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press H; add_layer R2: Tap Cover |
| [g157 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1743) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g157 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1752) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press N; add_layer R2: Tap Cover |
| [g157 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1768) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g157 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1777) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press B; add_layer R2: Tap Cover |
| [g157 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1793) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g157 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1802) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press Y; add_layer R2: Tap Cover |
| [g161 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1849) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g161 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1858) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 5; add_layer R2: Tap Cover |
| [g161 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1874) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g161 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1883) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 7; add_layer R2: Tap Cover |
| [g161 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1899) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g161 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1908) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 6; add_layer R2: Tap Cover |
| [g161 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1924) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g161 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L1933) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 8; add_layer R2: Tap Cover |
| [g217 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2632) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g217 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2641) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | mouse_button FORWARD; add_layer R2: Tap Cover |
| [g217 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2657) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g217 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2666) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g217 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2683) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g217 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2695) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g217 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2704) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer R2: Tap Cover |
| [g258 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3250) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | add_layer R2!L2: Modifier 2; add_layer L2: Tap Cover; add_layer L2: Modifier 0; add_layer R2: Tap Cover |
| [g258 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3264) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g259 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3289) | ordered layer operations | `{}` | add_layer R2: Double Tap; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1 |
| [g259 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3298) | ordered layer operations | `{"chord_button": "8", "delay_start": "300", "interruptable": "0"}` | add_layer R2: Tap Cover |
| [g668 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5406) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g668 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5415) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | mouse_button BACK; add_layer R2: Tap Cover |
| [g668 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5431) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g668 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5443) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g668 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5452) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer R2: Tap Cover |
| [g160 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15686) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g160 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15695) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press HOME; add_layer R2: Tap Cover |
| [g160 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15711) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g160 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15720) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press END; add_layer R2: Tap Cover |
| [g160 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15736) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g160 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15746) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 6. L2!R2: Modifier 2

Pure empty entries by activation: `{"chord": 14, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g596](../../neptune/single-set-alternative_hold-gyro_latest.json#L4206) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g597](../../neptune/single-set-alternative_hold-gyro_latest.json#L4389) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g598](../../neptune/single-set-alternative_hold-gyro_latest.json#L4433) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g599](../../neptune/single-set-alternative_hold-gyro_latest.json#L15911) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g612](../../neptune/single-set-alternative_hold-gyro_latest.json#L4656) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g681](../../neptune/single-set-alternative_hold-gyro_latest.json#L6013) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g682](../../neptune/single-set-alternative_hold-gyro_latest.json#L6128) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g596 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4214) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g596 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4230) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press M; add_layer L2&R2: Tap Cover |
| [g596 button_a chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4242) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g596 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4257) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g596 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4273) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press P; add_layer L2&R2: Tap Cover |
| [g596 button_b chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4285) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g596 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4300) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g596 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4316) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press O; add_layer L2&R2: Tap Cover |
| [g596 button_x chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4328) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g596 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4343) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g596 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4359) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press U; add_layer L2&R2: Tap Cover |
| [g596 button_y chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4371) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g597 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4397) | press empty | `{}` | empty_binding |
| [g597 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4407) | ordered layer operations | `{}` | add_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g598 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4441) | press empty | `{}` | empty_binding |
| [g598 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4451) | ordered layer operations | `{}` | add_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g598 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4469) | ordered layer operations | `{"chord_button": "7", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L2&R2: Tap Cover |
| [g598 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4479) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L2&R2: Tap Cover |
| [g612 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4664) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g612 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4680) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press I; add_layer L2&R2: Tap Cover |
| [g612 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4692) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g612 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4707) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g612 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4723) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press K; add_layer L2&R2: Tap Cover |
| [g612 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4735) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g612 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4750) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g612 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4766) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press L; add_layer L2&R2: Tap Cover |
| [g612 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4778) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g612 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4793) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g612 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4809) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press J; add_layer L2&R2: Tap Cover |
| [g612 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4821) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g681 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6021) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g681 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6037) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press BACK_TICK; add_layer L2&R2: Tap Cover |
| [g681 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6049) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g681 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6065) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g681 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6074) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g681 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6084) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g681 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6107) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L2&R2: Tap Cover |
| [g682 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6136) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g682 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6152) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L2&R2: Tap Cover |
| [g682 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6164) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g682 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6179) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L2&R2: Tap Cover |
| [g599 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15919) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g599 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15935) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press PAGE_UP; add_layer L2&R2: Tap Cover |
| [g599 button_escape chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15947) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g599 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15962) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g599 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15978) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L2&R2: Tap Cover |
| [g599 button_menu chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15990) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g599 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16005) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g599 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16015) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 7. R2!L2: Modifier 2

Pure empty entries by activation: `{"Full_Press": 2, "chord": 14}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g601](../../neptune/single-set-alternative_hold-gyro_latest.json#L4548) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g602](../../neptune/single-set-alternative_hold-gyro_latest.json#L4612) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g603](../../neptune/single-set-alternative_hold-gyro_latest.json#L16028) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g817](../../neptune/single-set-alternative_hold-gyro_latest.json#L7381) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| dpad | [g818](../../neptune/single-set-alternative_hold-gyro_latest.json#L7564) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| joystick | [g819](../../neptune/single-set-alternative_hold-gyro_latest.json#L7747) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g820](../../neptune/single-set-alternative_hold-gyro_latest.json#L7819) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g601 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4556) | press empty | `{}` | empty_binding |
| [g601 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4566) | ordered layer operations | `{}` | add_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g601 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4584) | ordered layer operations | `{"chord_button": "8", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L2&R2: Tap Cover |
| [g601 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4594) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L2&R2: Tap Cover |
| [g602 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4620) | press empty | `{}` | empty_binding |
| [g602 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4630) | ordered layer operations | `{}` | add_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g817 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7389) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g817 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7405) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g817 button_a chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7414) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press M; add_layer L2&R2: Tap Cover |
| [g817 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7432) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g817 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7448) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g817 button_b chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7457) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press P; add_layer L2&R2: Tap Cover |
| [g817 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7475) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g817 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7491) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g817 button_x chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7500) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press O; add_layer L2&R2: Tap Cover |
| [g817 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7518) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g817 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7534) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g817 button_y chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7543) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press U; add_layer L2&R2: Tap Cover |
| [g818 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7572) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g818 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7588) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g818 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7597) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press I; add_layer L2&R2: Tap Cover |
| [g818 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7615) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g818 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7631) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g818 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7640) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press K; add_layer L2&R2: Tap Cover |
| [g818 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7658) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g818 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7674) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g818 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7683) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press L; add_layer L2&R2: Tap Cover |
| [g818 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7701) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g818 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7717) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g818 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7726) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press J; add_layer L2&R2: Tap Cover |
| [g819 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7755) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g819 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7771) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g819 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7780) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L2&R2: Tap Cover |
| [g819 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7798) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L2&R2: Tap Cover |
| [g820 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7827) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g820 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7843) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g820 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7852) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press BACK_TICK; add_layer L2&R2: Tap Cover |
| [g820 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7871) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g820 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7880) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g820 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7890) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g820 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7913) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L2&R2: Tap Cover |
| [g603 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16036) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g603 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16052) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press PAGE_UP; add_layer L2&R2: Tap Cover |
| [g603 button_escape chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16064) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g603 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16079) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g603 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16095) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L2&R2: Tap Cover |
| [g603 button_menu chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16107) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g603 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16122) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g603 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16132) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 8. Gyro

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g12974](../../neptune/single-set-alternative_hold-gyro_latest.json#L18278) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g12980](../../neptune/single-set-alternative_hold-gyro_latest.json#L14990) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g12981](../../neptune/single-set-alternative_hold-gyro_latest.json#L15016) / **trigger** | edge | `{"layer": "1"}` |
| gyro | [g13033](../../neptune/single-set-alternative_hold-gyro_latest.json#L15365) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12980 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14998) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer Gyro \| L2: Modifier 0 |
| [g12981 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L15024) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | add_layer Gyro \| R2: Modifier 1 |

## 9. Gyro | L2: Modifier 0

Pure empty entries by activation: `{"chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g12911](../../neptune/single-set-alternative_hold-gyro_latest.json#L17882) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g12912](../../neptune/single-set-alternative_hold-gyro_latest.json#L12295) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| right_joystick | [g12916](../../neptune/single-set-alternative_hold-gyro_latest.json#L12436) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| dpad | [g12917](../../neptune/single-set-alternative_hold-gyro_latest.json#L12538) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| left_trigger | [g12922](../../neptune/single-set-alternative_hold-gyro_latest.json#L12692) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g12923](../../neptune/single-set-alternative_hold-gyro_latest.json#L12727) / **trigger** | edge | `{"layer": "1"}` |
| joystick | [g12925](../../neptune/single-set-alternative_hold-gyro_latest.json#L12777) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13034](../../neptune/single-set-alternative_hold-gyro_latest.json#L15377) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12912 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12303) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12912 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12312) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press G; add_layer L2: Tap Cover |
| [g12912 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12328) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12912 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12337) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press X; add_layer L2: Tap Cover |
| [g12912 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12353) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12912 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12362) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press Z; add_layer L2: Tap Cover |
| [g12912 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12378) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12912 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12387) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press T; add_layer L2: Tap Cover |
| [g12916 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12444) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12916 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12453) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | mouse_button MIDDLE; add_layer L2: Tap Cover |
| [g12916 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12469) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12916 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12478) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12916 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12495) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12916 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12507) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12916 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12516) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L2: Tap Cover |
| [g12917 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12546) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12917 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12555) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press 9; add_layer L2: Tap Cover |
| [g12917 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12571) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12917 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12580) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press DASH; add_layer L2: Tap Cover |
| [g12917 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12596) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12917 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12605) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press 0; add_layer L2: Tap Cover |
| [g12917 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12621) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12917 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12630) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press EQUALS; add_layer L2: Tap Cover |
| [g12922 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12700) | ordered layer operations | `{}` | add_layer L2: Double Tap; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0 |
| [g12922 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12709) | ordered layer operations | `{"chord_button": "7", "delay_start": "300", "interruptable": "0"}` | add_layer L2: Tap Cover |
| [g12923 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12735) | held-state guard; ordered layer operations | `{"chord_button": "7", "hold_repeats": "1", "interruptable": "0"}` | add_layer Gyro \| L2!R2: Modifier 2; add_layer R2: Tap Cover; add_layer Gyro \| R2: Modifier 1; add_layer L2: Tap Cover |
| [g12923 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12750) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12925 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12785) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12925 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12794) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press CAPSLOCK; add_layer L2: Tap Cover |
| [g12925 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12810) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12925 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12822) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12925 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12831) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L2: Tap Cover |
| [g12911 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17890) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12911 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17899) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press INSERT; add_layer L2: Tap Cover |
| [g12911 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17915) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |
| [g12911 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17924) | held-state guard; ordered layer operations | `{"chord_button": "7"}` | key_press DELETE; add_layer L2: Tap Cover |
| [g12911 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17940) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g12911 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17950) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 10. Gyro | R2: Modifier 1

Pure empty entries by activation: `{"chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **16**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g12928](../../neptune/single-set-alternative_hold-gyro_latest.json#L12852) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| switch | [g12931](../../neptune/single-set-alternative_hold-gyro_latest.json#L17963) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g12932](../../neptune/single-set-alternative_hold-gyro_latest.json#L12983) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g12934](../../neptune/single-set-alternative_hold-gyro_latest.json#L13106) / **joystick_mouse** | click, edge, touch | `{"layer": "1", "sensitivity": "75"}` |
| left_trigger | [g12940](../../neptune/single-set-alternative_hold-gyro_latest.json#L13259) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g12941](../../neptune/single-set-alternative_hold-gyro_latest.json#L13298) / **trigger** | edge | `{"layer": "1"}` |
| joystick | [g12944](../../neptune/single-set-alternative_hold-gyro_latest.json#L13355) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13035](../../neptune/single-set-alternative_hold-gyro_latest.json#L15389) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12928 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12860) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12928 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12869) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press H; add_layer R2: Tap Cover |
| [g12928 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12885) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12928 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12894) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press N; add_layer R2: Tap Cover |
| [g12928 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12910) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12928 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12919) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press B; add_layer R2: Tap Cover |
| [g12928 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12935) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12928 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12944) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press Y; add_layer R2: Tap Cover |
| [g12932 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12991) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12932 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13000) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 5; add_layer R2: Tap Cover |
| [g12932 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13016) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12932 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13025) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 7; add_layer R2: Tap Cover |
| [g12932 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13041) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12932 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13050) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 6; add_layer R2: Tap Cover |
| [g12932 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13066) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12932 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13075) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press 8; add_layer R2: Tap Cover |
| [g12934 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13114) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12934 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13123) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | mouse_button FORWARD; add_layer R2: Tap Cover |
| [g12934 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13139) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12934 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13148) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12934 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13165) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12934 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13177) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12934 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13186) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer R2: Tap Cover |
| [g12940 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13267) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | add_layer Gyro \| R2!L2: Modifier 2; add_layer L2: Tap Cover; add_layer Gyro \| L2: Modifier 0; add_layer R2: Tap Cover |
| [g12940 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13281) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12941 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13306) | ordered layer operations | `{}` | add_layer R2: Double Tap; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1 |
| [g12941 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13315) | ordered layer operations | `{"chord_button": "8", "delay_start": "300", "interruptable": "0"}` | add_layer R2: Tap Cover |
| [g12944 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13363) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12944 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13372) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | mouse_button BACK; add_layer R2: Tap Cover |
| [g12944 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13388) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12944 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13400) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12944 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13409) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer R2: Tap Cover |
| [g12931 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17971) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12931 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17980) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press HOME; add_layer R2: Tap Cover |
| [g12931 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17996) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |
| [g12931 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18005) | held-state guard; ordered layer operations | `{"chord_button": "8"}` | key_press END; add_layer R2: Tap Cover |
| [g12931 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18021) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g12931 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18031) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 11. Gyro | L2!R2: Modifier 2

Pure empty entries by activation: `{"chord": 14, "Full_Press": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g12947](../../neptune/single-set-alternative_hold-gyro_latest.json#L13430) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g12948](../../neptune/single-set-alternative_hold-gyro_latest.json#L13613) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g12949](../../neptune/single-set-alternative_hold-gyro_latest.json#L13657) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g12950](../../neptune/single-set-alternative_hold-gyro_latest.json#L18044) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| dpad | [g12951](../../neptune/single-set-alternative_hold-gyro_latest.json#L13721) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| right_joystick | [g12952](../../neptune/single-set-alternative_hold-gyro_latest.json#L13904) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g12953](../../neptune/single-set-alternative_hold-gyro_latest.json#L14019) / **dpad** | click, touch | `{"layer": "1"}` |
| gyro | [g13036](../../neptune/single-set-alternative_hold-gyro_latest.json#L15401) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12947 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13438) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12947 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13454) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press M; add_layer L2&R2: Tap Cover |
| [g12947 button_a chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13466) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12947 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13481) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12947 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13497) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press P; add_layer L2&R2: Tap Cover |
| [g12947 button_b chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13509) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12947 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13524) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12947 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13540) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press O; add_layer L2&R2: Tap Cover |
| [g12947 button_x chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13552) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12947 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13567) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12947 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13583) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press U; add_layer L2&R2: Tap Cover |
| [g12947 button_y chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13595) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12948 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13621) | press empty | `{}` | empty_binding |
| [g12948 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13631) | ordered layer operations | `{}` | remove_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g12949 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13665) | press empty | `{}` | empty_binding |
| [g12949 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13675) | ordered layer operations | `{}` | remove_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g12949 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13693) | ordered layer operations | `{"chord_button": "7", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L2&R2: Tap Cover |
| [g12949 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13703) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L2&R2: Tap Cover |
| [g12951 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13729) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12951 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13745) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press I; add_layer L2&R2: Tap Cover |
| [g12951 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13757) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12951 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13772) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12951 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13788) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press K; add_layer L2&R2: Tap Cover |
| [g12951 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13800) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12951 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13815) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12951 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13831) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press L; add_layer L2&R2: Tap Cover |
| [g12951 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13843) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12951 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13858) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12951 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13874) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press J; add_layer L2&R2: Tap Cover |
| [g12951 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13886) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12952 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13912) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12952 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13928) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press BACK_TICK; add_layer L2&R2: Tap Cover |
| [g12952 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13940) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12952 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13956) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12952 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13965) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12952 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13975) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12952 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L13998) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L2&R2: Tap Cover |
| [g12953 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14027) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12953 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14043) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L2&R2: Tap Cover |
| [g12953 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14055) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12953 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14070) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L2&R2: Tap Cover |
| [g12950 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18052) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12950 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18068) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press PAGE_UP; add_layer L2&R2: Tap Cover |
| [g12950 button_escape chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18080) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12950 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18095) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12950 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18111) | held-state guard; ordered layer operations | `{"chord_button": "7", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L2&R2: Tap Cover |
| [g12950 button_menu chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18123) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12950 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18138) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g12950 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18148) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 12. Gyro | R2!L2: Modifier 2

Pure empty entries by activation: `{"Full_Press": 2, "chord": 14}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **13**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g12959](../../neptune/single-set-alternative_hold-gyro_latest.json#L14142) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g12960](../../neptune/single-set-alternative_hold-gyro_latest.json#L14206) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g12961](../../neptune/single-set-alternative_hold-gyro_latest.json#L18161) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| button_diamond | [g12965](../../neptune/single-set-alternative_hold-gyro_latest.json#L14355) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| dpad | [g12966](../../neptune/single-set-alternative_hold-gyro_latest.json#L14538) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| joystick | [g12967](../../neptune/single-set-alternative_hold-gyro_latest.json#L14721) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g12968](../../neptune/single-set-alternative_hold-gyro_latest.json#L14793) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| gyro | [g13037](../../neptune/single-set-alternative_hold-gyro_latest.json#L15413) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "211109453758464", "gyro_ratchet_button_requireany_or_all": "0"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g12959 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14150) | press empty | `{}` | empty_binding |
| [g12959 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14160) | ordered layer operations | `{}` | remove_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g12959 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14178) | ordered layer operations | `{"chord_button": "8", "haptic_intensity": "3", "delay_start": "200"}` | add_layer L2&R2: Tap Cover |
| [g12959 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14188) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"}` | remove_layer L2&R2: Tap Cover |
| [g12960 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14214) | press empty | `{}` | empty_binding |
| [g12960 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14224) | ordered layer operations | `{}` | remove_layer Gyro 1 1; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover; remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2 |
| [g12965 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14363) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12965 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14379) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12965 button_a chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14388) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press M; add_layer L2&R2: Tap Cover |
| [g12965 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14406) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12965 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14422) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12965 button_b chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14431) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press P; add_layer L2&R2: Tap Cover |
| [g12965 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14449) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12965 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14465) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12965 button_x chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14474) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press O; add_layer L2&R2: Tap Cover |
| [g12965 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14492) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12965 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14508) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12965 button_y chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14517) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press U; add_layer L2&R2: Tap Cover |
| [g12966 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14546) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12966 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14562) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14571) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press I; add_layer L2&R2: Tap Cover |
| [g12966 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14589) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12966 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14605) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14614) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press K; add_layer L2&R2: Tap Cover |
| [g12966 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14632) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12966 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14648) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14657) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press L; add_layer L2&R2: Tap Cover |
| [g12966 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14675) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12966 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14691) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12966 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14700) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press J; add_layer L2&R2: Tap Cover |
| [g12967 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14729) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12967 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14745) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12967 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14754) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press NUM_LOCK; add_layer L2&R2: Tap Cover |
| [g12967 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14772) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L2&R2: Tap Cover |
| [g12968 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14801) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12968 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14817) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12968 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14826) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press BACK_TICK; add_layer L2&R2: Tap Cover |
| [g12968 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14845) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12968 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14854) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g12968 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14864) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12968 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L14887) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L2&R2: Tap Cover |
| [g12961 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18169) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12961 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18185) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press PAGE_UP; add_layer L2&R2: Tap Cover |
| [g12961 button_escape chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18197) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12961 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18212) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer L2: Tap Cover; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g12961 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18228) | held-state guard; ordered layer operations | `{"chord_button": "8", "interruptable": "0"}` | key_press PAGE_DOWN; add_layer L2&R2: Tap Cover |
| [g12961 button_menu chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18240) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g12961 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18255) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g12961 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18265) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 13. LST: Temporary Gyro

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g208](../../neptune/single-set-alternative_hold-gyro_latest.json#L15811) / **switches** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g210](../../neptune/single-set-alternative_hold-gyro_latest.json#L2577) / **dpad** | touch | `{"layer": "1"}` |
| left_trigger | [g262](../../neptune/single-set-alternative_hold-gyro_latest.json#L3336) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g263](../../neptune/single-set-alternative_hold-gyro_latest.json#L3346) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| gyro | [g881](../../neptune/single-set-alternative_hold-gyro_latest.json#L8203) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "70368744177664"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g210 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2585) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Entry Point |

## 14. RST: Temporary Gyro

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g200](../../neptune/single-set-alternative_hold-gyro_latest.json#L15801) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g203](../../neptune/single-set-alternative_hold-gyro_latest.json#L2498) / **joystick_mouse** | touch | `{"layer": "1"}` |
| left_trigger | [g260](../../neptune/single-set-alternative_hold-gyro_latest.json#L3316) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g261](../../neptune/single-set-alternative_hold-gyro_latest.json#L3326) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| gyro | [g880](../../neptune/single-set-alternative_hold-gyro_latest.json#L8192) / **gyro_to_mouse** | none explicitly defined | `{"layer": "1", "gyro_ratchet_button_mask": "140737488355328"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g203 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2506) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Entry Point |

## 15. Gyro Off Ramp Up

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g13029](../../neptune/single-set-alternative_hold-gyro_latest.json#L18298) / **switches** | left_bumper, right_bumper | `{"layer": "1"}` |
| left_trigger | [g13030](../../neptune/single-set-alternative_hold-gyro_latest.json#L15336) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g13031](../../neptune/single-set-alternative_hold-gyro_latest.json#L15346) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| gyro | [g13032](../../neptune/single-set-alternative_hold-gyro_latest.json#L15356) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g13038](../../neptune/single-set-alternative_hold-gyro_latest.json#L18337) / **joystick_mouse** | edge | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13029 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18306) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Gyro Off Ramp Up |
| [g13029 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18320) | ordered layer operations | `{"hold_repeats": "1", "interruptable": "0"}` | remove_layer Gyro Off Ramp Up |
| [g13038 edge Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18346) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "activation_threshold": "25807", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer Gyro Off Ramp Up |
| [g13038 edge Soft_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18358) | ordered layer operations | `{"haptic_intensity": "0", "delay_start": "5", "activation_threshold": "29031", "interruptable": "0"}` | add_layer Turning Ramp Up 0 |

## 16. LTP: Arrow Keys

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g250](../../neptune/single-set-alternative_hold-gyro_latest.json#L15831) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g251](../../neptune/single-set-alternative_hold-gyro_latest.json#L3059) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click | `{"layer": "1", "layout": "0", "deadzone": "23000", "edge_binding_invert": "1", "haptic_intensity_override": "3"}` |
| left_trigger | [g266](../../neptune/single-set-alternative_hold-gyro_latest.json#L3376) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g267](../../neptune/single-set-alternative_hold-gyro_latest.json#L3386) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g671](../../neptune/single-set-alternative_hold-gyro_latest.json#L5563) / **dpad** | touch | `{"layer": "1"}` |
| right_joystick | [g672](../../neptune/single-set-alternative_hold-gyro_latest.json#L5608) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g251 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3067) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press UP_ARROW |
| [g251 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3080) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press DOWN_ARROW |
| [g251 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3093) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press RIGHT_ARROW |
| [g251 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3106) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | key_press LEFT_ARROW |
| [g251 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3119) | output/mode replacement candidate | `{"chord_button": "18", "haptic_intensity": "3"}` | SHOW_KEYBOARD |
| [g251 click Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3134) | ordered layer operations | `{"haptic_intensity": "0", "interruptable": "0"}` | hold_layer LTP: Arrow Keys |
| [g251 click Soft_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3143) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer LTP: Arrow Keys |
| [g671 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5571) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer LTP: Arrow Keys |
| [g671 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5579) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g671 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5588) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g672 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5616) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer LTP: Arrow Keys |
| [g672 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5624) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g672 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5633) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 17. RTP: Mouse Buttons

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g240](../../neptune/single-set-alternative_hold-gyro_latest.json#L15821) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g242](../../neptune/single-set-alternative_hold-gyro_latest.json#L2856) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click | `{"layer": "1", "layout": "0", "deadzone": "23000", "edge_binding_invert": "1", "haptic_intensity_override": "3"}` |
| left_trigger | [g264](../../neptune/single-set-alternative_hold-gyro_latest.json#L3356) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g265](../../neptune/single-set-alternative_hold-gyro_latest.json#L3366) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g669](../../neptune/single-set-alternative_hold-gyro_latest.json#L5473) / **dpad** | touch | `{"layer": "1"}` |
| right_joystick | [g670](../../neptune/single-set-alternative_hold-gyro_latest.json#L5518) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g242 dpad_north Long_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2864) | output/mode replacement candidate | `{"hold_repeats": "1", "long_press_time": "150", "haptic_intensity": "0"}` | mouse_wheel SCROLL_UP |
| [g242 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2874) | output/mode replacement candidate | `{"haptic_intensity": "0", "interruptable": "0"}` | mouse_wheel SCROLL_UP |
| [g242 dpad_south Long_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2888) | output/mode replacement candidate | `{"hold_repeats": "1", "long_press_time": "150", "haptic_intensity": "0"}` | mouse_wheel SCROLL_DOWN |
| [g242 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2898) | output/mode replacement candidate | `{"haptic_intensity": "0", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |
| [g242 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2912) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | mouse_button FORWARD |
| [g242 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2925) | output/mode replacement candidate | `{"haptic_intensity": "3"}` | mouse_button BACK |
| [g242 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2938) | output/mode replacement candidate | `{"chord_button": "19", "haptic_intensity": "3"}` | mouse_button MIDDLE |
| [g242 click Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2953) | ordered layer operations | `{"haptic_intensity": "0", "interruptable": "0"}` | hold_layer RTP: Mouse Buttons |
| [g242 click Soft_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L2962) | ordered layer operations | `{"hold_repeats": "1", "haptic_intensity": "0", "interruptable": "0", "edge_binding_invert": "1"}` | remove_layer RTP: Mouse Buttons |
| [g669 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5481) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Mouse Buttons |
| [g669 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5489) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g669 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5498) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g670 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5526) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Mouse Buttons |
| [g670 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5534) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g670 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5543) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 18. RTP: Circular Scroll

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g368](../../neptune/single-set-alternative_hold-gyro_latest.json#L3448) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g369](../../neptune/single-set-alternative_hold-gyro_latest.json#L3458) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g370](../../neptune/single-set-alternative_hold-gyro_latest.json#L15841) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g721](../../neptune/single-set-alternative_hold-gyro_latest.json#L6461) / **scrollwheel** | scroll_clockwise, scroll_counterclockwise, click, touch | `{"layer": "1", "scroll_angle": "145", "haptic_intensity": "0"}` |
| joystick | [g722](../../neptune/single-set-alternative_hold-gyro_latest.json#L6523) / **dpad** | touch | `{"layer": "1"}` |
| right_joystick | [g723](../../neptune/single-set-alternative_hold-gyro_latest.json#L6571) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g721 scroll_clockwise Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6469) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g721 scroll_counterclockwise Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6479) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g721 click Soft_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6489) | ordered layer operations | `{"haptic_intensity": "0"}` | hold_layer RTP: Mouse Buttons |
| [g721 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6502) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Circular Scroll; remove_layer RTP: Mouse Buttons |
| [g722 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6531) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Circular Scroll; remove_layer RTP: Mouse Buttons |
| [g722 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6542) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g722 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6551) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g723 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6579) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Circular Scroll; remove_layer RTP: Mouse Buttons |
| [g723 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6590) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g723 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6599) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 19. L2: Scroll Down

Pure empty entries by activation: `{"chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g899](../../neptune/single-set-alternative_hold-gyro_latest.json#L8334) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g900](../../neptune/single-set-alternative_hold-gyro_latest.json#L8380) / **trigger** | edge | `{"layer": "1"}` |
| switch | [g901](../../neptune/single-set-alternative_hold-gyro_latest.json#L16904) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g944](../../neptune/single-set-alternative_hold-gyro_latest.json#L8681) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g945](../../neptune/single-set-alternative_hold-gyro_latest.json#L8752) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g899 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8342) | output/mode replacement candidate | `{"hold_repeats": "1", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |
| [g899 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8351) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer L2: Double Tap; remove_layer L2: Scroll Down |
| [g899 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8362) | ordered layer operations | `{"chord_button": "7", "delay_start": "150", "interruptable": "0"}` | add_layer L2: Double Tap Cover |
| [g900 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8388) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g944 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8689) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g944 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8698) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer L2: Scroll Down; remove_layer L2: Double Tap Cover |
| [g944 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8714) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer L2: Double Tap Cover |
| [g944 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8727) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Scroll Down; remove_layer L2: Double Tap Cover |
| [g944 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8735) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g945 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8760) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer L2: Double Tap Cover |
| [g945 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8773) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer L2: Scroll Down; remove_layer L2: Double Tap Cover |
| [g945 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8781) | conditional empty; held-state guard | `{"chord_button": "7", "interruptable": "0"}` | empty_binding |
| [g901 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16912) | output/mode replacement candidate | `{}` | mouse_button MIDDLE |
| [g901 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16922) | output/mode replacement candidate | `{}` | key_press BACK_TICK |
| [g901 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16932) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g901 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16942) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 20. R2: Scroll Up

Pure empty entries by activation: `{"chord": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g903](../../neptune/single-set-alternative_hold-gyro_latest.json#L8411) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g904](../../neptune/single-set-alternative_hold-gyro_latest.json#L8432) / **trigger** | edge | `{"layer": "1"}` |
| switch | [g905](../../neptune/single-set-alternative_hold-gyro_latest.json#L16955) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g946](../../neptune/single-set-alternative_hold-gyro_latest.json#L8798) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g947](../../neptune/single-set-alternative_hold-gyro_latest.json#L8869) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g903 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8419) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g904 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8440) | output/mode replacement candidate | `{"hold_repeats": "1", "interruptable": "0"}` | mouse_wheel SCROLL_UP |
| [g904 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8449) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer R2: Double Tap; remove_layer R2: Scroll Up |
| [g904 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8460) | ordered layer operations | `{"chord_button": "8", "delay_start": "150", "interruptable": "0"}` | add_layer R2: Double Tap Cover |
| [g946 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8806) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g946 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8815) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer R2: Scroll Up; remove_layer R2: Double Tap Cover |
| [g946 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8831) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer R2: Double Tap Cover |
| [g946 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8844) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Scroll Up; remove_layer R2: Double Tap Cover |
| [g946 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8852) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g947 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8877) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer R2: Double Tap Cover |
| [g947 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8890) | cleanup protected by sibling chord; ordered layer operations | `{}` | remove_layer R2: Scroll Up; remove_layer R2: Double Tap Cover |
| [g947 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8898) | conditional empty; held-state guard | `{"chord_button": "8", "interruptable": "0"}` | empty_binding |
| [g905 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16963) | output/mode replacement candidate | `{}` | mouse_button MIDDLE |
| [g905 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16973) | output/mode replacement candidate | `{}` | key_press BACK_TICK |
| [g905 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16983) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g905 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16993) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 21. Escape

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g488](../../neptune/single-set-alternative_hold-gyro_latest.json#L3760) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g489](../../neptune/single-set-alternative_hold-gyro_latest.json#L3770) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g490](../../neptune/single-set-alternative_hold-gyro_latest.json#L15881) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g529](../../neptune/single-set-alternative_hold-gyro_latest.json#L3874) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g677](../../neptune/single-set-alternative_hold-gyro_latest.json#L5833) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g678](../../neptune/single-set-alternative_hold-gyro_latest.json#L5878) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g529 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3882) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press ESCAPE |
| [g529 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3890) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Escape |
| [g677 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5841) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Escape |
| [g677 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5849) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g677 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5858) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g678 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5886) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Escape |
| [g678 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5894) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g678 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5903) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 22. Tab

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g480](../../neptune/single-set-alternative_hold-gyro_latest.json#L3700) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g481](../../neptune/single-set-alternative_hold-gyro_latest.json#L3710) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g482](../../neptune/single-set-alternative_hold-gyro_latest.json#L15861) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g527](../../neptune/single-set-alternative_hold-gyro_latest.json#L3810) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g673](../../neptune/single-set-alternative_hold-gyro_latest.json#L5653) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g674](../../neptune/single-set-alternative_hold-gyro_latest.json#L5698) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g527 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3818) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press TAB |
| [g527 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3826) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Tab |
| [g673 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5661) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Tab |
| [g673 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5669) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g673 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5678) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g674 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5706) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Tab |
| [g674 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5714) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g674 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5723) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 23. Backspace

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g484](../../neptune/single-set-alternative_hold-gyro_latest.json#L3730) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g485](../../neptune/single-set-alternative_hold-gyro_latest.json#L3740) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g486](../../neptune/single-set-alternative_hold-gyro_latest.json#L15871) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g528](../../neptune/single-set-alternative_hold-gyro_latest.json#L3842) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g675](../../neptune/single-set-alternative_hold-gyro_latest.json#L5743) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g676](../../neptune/single-set-alternative_hold-gyro_latest.json#L5788) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g528 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3850) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press BACKSPACE |
| [g528 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3858) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Backspace |
| [g675 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5751) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Backspace |
| [g675 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5759) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g675 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5768) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g676 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5796) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Backspace |
| [g676 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5804) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g676 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5813) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 24. Enter

Pure empty entries by activation: `{"chord": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g492](../../neptune/single-set-alternative_hold-gyro_latest.json#L3790) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g493](../../neptune/single-set-alternative_hold-gyro_latest.json#L3800) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g494](../../neptune/single-set-alternative_hold-gyro_latest.json#L15891) / **switches** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g530](../../neptune/single-set-alternative_hold-gyro_latest.json#L3906) / **single_button** | touch | `{"layer": "1"}` |
| right_joystick | [g679](../../neptune/single-set-alternative_hold-gyro_latest.json#L5923) / **joystick_mouse** | touch | `{"layer": "1"}` |
| joystick | [g680](../../neptune/single-set-alternative_hold-gyro_latest.json#L5968) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g530 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3914) | output/mode replacement candidate | `{"haptic_intensity": "0"}` | key_press RETURN |
| [g530 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L3922) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Enter |
| [g679 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5931) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Enter |
| [g679 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5939) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g679 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5948) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g680 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5976) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Enter |
| [g680 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5984) | conditional empty; held-state guard | `{"chord_button": "16", "interruptable": "0"}` | empty_binding |
| [g680 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5993) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 25. Menu Left: Escape

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1112](../../neptune/single-set-alternative_hold-gyro_latest.json#L9674) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1113](../../neptune/single-set-alternative_hold-gyro_latest.json#L9684) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1114](../../neptune/single-set-alternative_hold-gyro_latest.json#L9718) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1115](../../neptune/single-set-alternative_hold-gyro_latest.json#L17339) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g1169](../../neptune/single-set-alternative_hold-gyro_latest.json#L10221) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1170](../../neptune/single-set-alternative_hold-gyro_latest.json#L10260) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g1203](../../neptune/single-set-alternative_hold-gyro_latest.json#L10393) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1113 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9692) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1113 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9705) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1114 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9726) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1114 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9739) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1169 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10229) | press empty | `{}` | empty_binding |
| [g1169 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10239) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Left: Double Tap Cover |
| [g1170 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10268) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Left: Double Tap Cover |
| [g1115 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17347) | press empty | `{}` | empty_binding |
| [g1115 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17357) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press ESCAPE |
| [g1115 button_menu release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17365) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Left: Double Tap; remove_layer Menu Left: Escape |
| [g1115 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17376) | ordered layer operations | `{"chord_button": "15", "delay_start": "150", "interruptable": "0"}` | add_layer Menu Left: Double Tap Cover |
| [g1115 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17391) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g1115 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17401) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 26. Menu Left: Backspace

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g13045](../../neptune/single-set-alternative_hold-gyro_latest.json#L18677) / **switches** | button_menu | `{"layer": "1"}` |
| gyro | [g13046](../../neptune/single-set-alternative_hold-gyro_latest.json#L18709) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13045 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18685) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press BACKSPACE |
| [g13045 button_menu release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18693) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Left: Backspace |

## 27. Menu Left: Fn Layer

Pure empty entries by activation: `{"Full_Press": 2, "chord": 12}`. Mixed entries containing empty subcommands: **1**. Chord-protected cleanup entries: **19**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g624](../../neptune/single-set-alternative_hold-gyro_latest.json#L4890) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g625](../../neptune/single-set-alternative_hold-gyro_latest.json#L5045) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g626](../../neptune/single-set-alternative_hold-gyro_latest.json#L5102) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g627](../../neptune/single-set-alternative_hold-gyro_latest.json#L16145) / **switches** | button_escape, button_menu, left_bumper, right_bumper, button_back_left, button_back_right, button_back_left_upper, button_back_right_upper, left_stick_click, right_stick_click | `{"layer": "1"}` |
| dpad | [g636](../../neptune/single-set-alternative_hold-gyro_latest.json#L5159) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| gyro | [g639](../../neptune/single-set-alternative_hold-gyro_latest.json#L5314) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g684](../../neptune/single-set-alternative_hold-gyro_latest.json#L6283) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "layout": "0", "edge_binding_radius": "21000", "edge_binding_invert": "0"}` |
| right_joystick | [g1289](../../neptune/single-set-alternative_hold-gyro_latest.json#L10903) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "requires_click": "0", "layout": "0", "deadzone": "13276", "edge_binding_radius": "21000"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g624 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4898) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4910) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F3 |
| [g624 button_a chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4919) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F3 |
| [g624 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4934) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4946) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F2 |
| [g624 button_b chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4955) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F2 |
| [g624 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4970) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4982) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F4 |
| [g624 button_x chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L4991) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F4 |
| [g624 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5006) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g624 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5018) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F1 |
| [g624 button_y chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5027) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F1 |
| [g625 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5053) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g625 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5065) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F12 |
| [g625 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5074) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F12 |
| [g625 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5089) | press empty | `{}` | empty_binding |
| [g626 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5110) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g626 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5122) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F11 |
| [g626 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5131) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F11 |
| [g626 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5146) | press empty | `{}` | empty_binding |
| [g636 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5167) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5179) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F5 |
| [g636 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5188) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F5 |
| [g636 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5203) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5215) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F7 |
| [g636 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5224) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F7 |
| [g636 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5239) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5251) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F6 |
| [g636 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5260) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F6 |
| [g636 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5275) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g636 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5287) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F8 |
| [g636 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L5296) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F8 |
| [g684 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6292) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press BACKSLASH |
| [g684 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6300) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6316) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press FORWARD_SLASH |
| [g684 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6324) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6340) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press RIGHT_BRACKET |
| [g684 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6348) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6364) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press LEFT_BRACKET |
| [g684 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6372) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g684 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6388) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g684 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6397) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g684 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6407) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g684 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6423) | ordered layer operations | `{"chord_button": "15", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 1 |
| [g684 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6438) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g1289 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10912) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press SEMICOLON |
| [g1289 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10920) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10936) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press SINGLE_QUOTE |
| [g1289 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10944) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10960) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press PERIOD |
| [g1289 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10968) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10984) | output/mode replacement candidate | `{"chord_button": "15"}` | key_press COMMA |
| [g1289 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10992) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1289 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11008) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1289 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11017) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1289 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11027) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g1289 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11043) | ordered layer operations | `{"chord_button": "15", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 0 |
| [g1289 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11058) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g627 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16153) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16164) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "15"}` | add_layer Menu Right: Enter; empty_binding; empty_binding |
| [g627 button_menu release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16181) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16197) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 left_bumper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16209) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F10 |
| [g627 left_bumper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16218) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F10 |
| [g627 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16233) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 right_bumper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16245) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F9 |
| [g627 right_bumper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16254) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F9 |
| [g627 button_back_left chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16270) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g627 button_back_left chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16279) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g627 button_back_left Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16289) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_back_right chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16306) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g627 button_back_right chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16315) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g627 button_back_right Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16325) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_back_left_upper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16342) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g627 button_back_left_upper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16351) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g627 button_back_left_upper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16361) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 button_back_right_upper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16378) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g627 button_back_right_upper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16387) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g627 button_back_right_upper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16397) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g627 left_stick_click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16413) | output/mode replacement candidate | `{}` | mode_shift joystick 1291 |
| [g627 right_stick_click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16423) | output/mode replacement candidate | `{}` | mode_shift right_joystick 1290 |

**Conditional mode-shift bindings** (not the default active mode):

| Exact activator | Classification | Settings | Payload |
|---|---|---|---|
| [g1290 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11090) | output/mode replacement candidate | `{}` | key_press SEMICOLON, ,  |
| [g1290 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11100) | output/mode replacement candidate | `{}` | key_press SINGLE_QUOTE, ,  |
| [g1290 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11110) | output/mode replacement candidate | `{}` | key_press PERIOD, ,  |
| [g1290 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11120) | output/mode replacement candidate | `{}` | key_press COMMA, ,  |
| [g1290 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11130) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1290 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11140) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1290 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11150) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1291 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11174) | output/mode replacement candidate | `{}` | key_press BACKSLASH, ,  |
| [g1291 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11184) | output/mode replacement candidate | `{}` | key_press FORWARD_SLASH, ,  |
| [g1291 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11194) | output/mode replacement candidate | `{}` | key_press RIGHT_BRACKET, ,  |
| [g1291 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11204) | output/mode replacement candidate | `{}` | key_press LEFT_BRACKET, ,  |
| [g1291 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11214) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1291 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11224) | press empty | `{}` | controller_action empty_binding, ,  |
| [g1291 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11234) | press empty | `{}` | controller_action empty_binding, ,  |

## 28. Menu Right: Tab

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1116](../../neptune/single-set-alternative_hold-gyro_latest.json#L9752) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1117](../../neptune/single-set-alternative_hold-gyro_latest.json#L9762) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1118](../../neptune/single-set-alternative_hold-gyro_latest.json#L9796) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1119](../../neptune/single-set-alternative_hold-gyro_latest.json#L17414) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| right_joystick | [g1171](../../neptune/single-set-alternative_hold-gyro_latest.json#L10289) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1172](../../neptune/single-set-alternative_hold-gyro_latest.json#L10328) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g1204](../../neptune/single-set-alternative_hold-gyro_latest.json#L10402) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1117 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9770) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1117 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9783) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1118 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9804) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1118 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9817) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1171 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10297) | press empty | `{}` | empty_binding |
| [g1171 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10307) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Right: Double Tap Cover |
| [g1172 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10336) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Right: Double Tap Cover |
| [g1119 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17422) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press TAB |
| [g1119 button_escape release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17430) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Right: Double Tap; remove_layer Menu Right: Tab |
| [g1119 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17441) | ordered layer operations | `{"chord_button": "14", "delay_start": "150", "interruptable": "0"}` | add_layer Menu Right: Double Tap Cover |
| [g1119 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17456) | press empty | `{}` | empty_binding |
| [g1119 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17466) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g1119 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17476) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 29. Menu Right: Enter

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| switch | [g13047](../../neptune/single-set-alternative_hold-gyro_latest.json#L18718) / **switches** | button_escape | `{"layer": "1"}` |
| gyro | [g13048](../../neptune/single-set-alternative_hold-gyro_latest.json#L18750) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13047 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18726) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press RETURN |
| [g13047 button_escape release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18734) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Right: Enter |

## 30. Menu Right: Fn Layer

Pure empty entries by activation: `{"Full_Press": 2, "chord": 12}`. Mixed entries containing empty subcommands: **1**. Chord-protected cleanup entries: **19**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1317](../../neptune/single-set-alternative_hold-gyro_latest.json#L11505) / **four_buttons** | button_a, button_b, button_x, button_y | `{"layer": "1"}` |
| left_trigger | [g1318](../../neptune/single-set-alternative_hold-gyro_latest.json#L11660) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1319](../../neptune/single-set-alternative_hold-gyro_latest.json#L11717) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1320](../../neptune/single-set-alternative_hold-gyro_latest.json#L17591) / **switches** | button_escape, button_menu, left_bumper, right_bumper, button_back_left, button_back_right, button_back_left_upper, button_back_right_upper, left_stick_click, right_stick_click | `{"layer": "1"}` |
| dpad | [g1329](../../neptune/single-set-alternative_hold-gyro_latest.json#L11774) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west | `{"layer": "1"}` |
| joystick | [g1330](../../neptune/single-set-alternative_hold-gyro_latest.json#L11929) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "layout": "0", "edge_binding_radius": "21000", "edge_binding_invert": "0"}` |
| right_joystick | [g1331](../../neptune/single-set-alternative_hold-gyro_latest.json#L12107) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge, click, touch | `{"layer": "1", "requires_click": "0", "layout": "0", "deadzone": "13276", "edge_binding_radius": "21000"}` |
| gyro | [g1332](../../neptune/single-set-alternative_hold-gyro_latest.json#L12286) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1317 button_a Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11513) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_a chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11525) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F3 |
| [g1317 button_a chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11534) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F3 |
| [g1317 button_b Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11549) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_b chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11561) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F2 |
| [g1317 button_b chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11570) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F2 |
| [g1317 button_x Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11585) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_x chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11597) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F4 |
| [g1317 button_x chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11606) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F4 |
| [g1317 button_y Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11621) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1317 button_y chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11633) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F1 |
| [g1317 button_y chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11642) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F1 |
| [g1318 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11668) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1318 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11680) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F12 |
| [g1318 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11689) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F12 |
| [g1318 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11704) | press empty | `{}` | empty_binding |
| [g1319 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11725) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1319 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11737) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F11 |
| [g1319 click chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11746) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F11 |
| [g1319 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11761) | press empty | `{}` | empty_binding |
| [g1329 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11782) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11794) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F5 |
| [g1329 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11803) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F5 |
| [g1329 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11818) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11830) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F7 |
| [g1329 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11839) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F7 |
| [g1329 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11854) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11866) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F6 |
| [g1329 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11875) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F6 |
| [g1329 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11890) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1329 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11902) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F8 |
| [g1329 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11911) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F8 |
| [g1330 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11938) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press BACKSLASH |
| [g1330 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11946) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11962) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press FORWARD_SLASH |
| [g1330 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11970) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11986) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press RIGHT_BRACKET |
| [g1330 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11994) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12010) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press LEFT_BRACKET |
| [g1330 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12018) | conditional empty | `{"chord_button": "9", "interruptable": "0"}` | empty_binding |
| [g1330 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12034) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1330 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12043) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1330 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12053) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1330 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12069) | ordered layer operations | `{"chord_button": "14", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 1 |
| [g1330 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12084) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point |
| [g1331 dpad_north chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12116) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press SEMICOLON |
| [g1331 dpad_north chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12124) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 dpad_south chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12140) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press SINGLE_QUOTE |
| [g1331 dpad_south chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12148) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 dpad_east chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12164) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press PERIOD |
| [g1331 dpad_east chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12172) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 dpad_west chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12188) | output/mode replacement candidate | `{"chord_button": "14"}` | key_press COMMA |
| [g1331 dpad_west chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12196) | conditional empty | `{"chord_button": "20", "interruptable": "0"}` | empty_binding |
| [g1331 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12212) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1331 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12221) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1331 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12231) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1331 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12247) | ordered layer operations | `{"chord_button": "14", "hold_repeats": "1", "interruptable": "0"}` | add_layer Transition Set 0 |
| [g1331 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L12262) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point |
| [g1320 button_escape release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17599) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17615) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17626) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "14"}` | add_layer Menu Left: Backspace; empty_binding; empty_binding |
| [g1320 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17643) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 left_bumper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17655) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F10 |
| [g1320 left_bumper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17664) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F10 |
| [g1320 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17679) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 right_bumper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17691) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press F9 |
| [g1320 right_bumper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17700) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press F9 |
| [g1320 button_back_left chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17716) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g1320 button_back_left chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17725) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_CONTROL |
| [g1320 button_back_left Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17735) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_back_right chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17752) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g1320 button_back_right chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17761) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_ALT |
| [g1320 button_back_right Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17771) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_back_left_upper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17788) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g1320 button_back_left_upper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17797) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press RIGHT_SHIFT |
| [g1320 button_back_left_upper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17807) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 button_back_right_upper chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17824) | held-state guard; output/mode replacement candidate | `{"chord_button": "15", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g1320 button_back_right_upper chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17833) | held-state guard; output/mode replacement candidate | `{"chord_button": "14", "interruptable": "0"}` | key_press LEFT_WINDOWS |
| [g1320 button_back_right_upper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17843) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g1320 left_stick_click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17859) | output/mode replacement candidate | `{}` | mode_shift joystick 12910 |
| [g1320 right_stick_click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17869) | output/mode replacement candidate | `{}` | mode_shift right_joystick 12900 |

**Conditional mode-shift bindings** (not the default active mode):

| Exact activator | Classification | Settings | Payload |
|---|---|---|---|
| [g12900 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11257) | output/mode replacement candidate | `{}` | key_press SEMICOLON, ,  |
| [g12900 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11267) | output/mode replacement candidate | `{}` | key_press SINGLE_QUOTE, ,  |
| [g12900 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11277) | output/mode replacement candidate | `{}` | key_press PERIOD, ,  |
| [g12900 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11287) | output/mode replacement candidate | `{}` | key_press COMMA, ,  |
| [g12900 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11297) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12900 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11307) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12900 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11317) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12910 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11341) | output/mode replacement candidate | `{}` | key_press BACKSLASH, ,  |
| [g12910 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11351) | output/mode replacement candidate | `{}` | key_press FORWARD_SLASH, ,  |
| [g12910 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11361) | output/mode replacement candidate | `{}` | key_press RIGHT_BRACKET, ,  |
| [g12910 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11371) | output/mode replacement candidate | `{}` | key_press LEFT_BRACKET, ,  |
| [g12910 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11381) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12910 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11391) | press empty | `{}` | controller_action empty_binding, ,  |
| [g12910 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11401) | press empty | `{}` | controller_action empty_binding, ,  |

## 31. LST: Entry Point

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g829](../../neptune/single-set-alternative_hold-gyro_latest.json#L7964) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g830](../../neptune/single-set-alternative_hold-gyro_latest.json#L7974) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g831](../../neptune/single-set-alternative_hold-gyro_latest.json#L7984) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g832](../../neptune/single-set-alternative_hold-gyro_latest.json#L16647) / **switches** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g851](../../neptune/single-set-alternative_hold-gyro_latest.json#L8041) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g851 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8049) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer LST: Double Tap; remove_layer LST: Entry Point |
| [g851 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8060) | ordered layer operations | `{"chord_button": "23", "delay_start": "150", "interruptable": "0"}` | add_layer LST: Tap Cover |

## 32. RST: Entry Point

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g825](../../neptune/single-set-alternative_hold-gyro_latest.json#L7934) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g826](../../neptune/single-set-alternative_hold-gyro_latest.json#L7944) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g827](../../neptune/single-set-alternative_hold-gyro_latest.json#L7954) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g828](../../neptune/single-set-alternative_hold-gyro_latest.json#L16637) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g849](../../neptune/single-set-alternative_hold-gyro_latest.json#L7994) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g849 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8002) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer RST: Double Tap; remove_layer RST: Entry Point |
| [g849 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8013) | ordered layer operations | `{"chord_button": "24", "delay_start": "150", "interruptable": "0"}` | add_layer RST: Tap Cover |

## 33. RTP: Entry Point

Pure empty entries by activation: `{"chord": 1}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **1**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g983](../../neptune/single-set-alternative_hold-gyro_latest.json#L9039) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g984](../../neptune/single-set-alternative_hold-gyro_latest.json#L9049) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g985](../../neptune/single-set-alternative_hold-gyro_latest.json#L17026) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1032](../../neptune/single-set-alternative_hold-gyro_latest.json#L9292) / **absolute_mouse** | touch | `{"layer": "1"}` |
| right_joystick | [g1163](../../neptune/single-set-alternative_hold-gyro_latest.json#L10002) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1164](../../neptune/single-set-alternative_hold-gyro_latest.json#L10056) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1032 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9300) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer RTP: Double Tap; remove_layer RTP: Entry Point |
| [g1032 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9311) | ordered layer operations | `{"chord_button": "17", "haptic_intensity": "0", "delay_start": "150", "interruptable": "0"}` | add_layer RTP: Tap Cover |
| [g1163 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10010) | conditional empty; held-state guard | `{"chord_button": "17", "interruptable": "0"}` | empty_binding |
| [g1163 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10019) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer RTP: Entry Point; remove_layer RTP: Tap Cover |
| [g1163 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10035) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer RTP: Tap Cover |
| [g1164 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10064) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer RTP: Tap Cover |

## 34. Menu Left: Entry Point

Pure empty entries by activation: `{"Full_Press": 2, "chord": 3}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g869](../../neptune/single-set-alternative_hold-gyro_latest.json#L8124) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g870](../../neptune/single-set-alternative_hold-gyro_latest.json#L8158) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g871](../../neptune/single-set-alternative_hold-gyro_latest.json#L16657) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| gyro | [g1158](../../neptune/single-set-alternative_hold-gyro_latest.json#L9866) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g1161](../../neptune/single-set-alternative_hold-gyro_latest.json#L9875) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g1162](../../neptune/single-set-alternative_hold-gyro_latest.json#L9951) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g869 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8132) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g869 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8145) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g870 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8166) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g870 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8179) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1161 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9883) | ordered layer operations | `{"chord_button": "15"}` | add_layer Menu Left: Fn Layer |
| [g1161 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9896) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1161 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9905) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Fn Layer; remove_layer Menu Left: Entry Point |
| [g1161 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9921) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Left: Fn Layer |
| [g1161 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9934) | conditional empty | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1162 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9959) | ordered layer operations | `{"chord_button": "15"}` | add_layer Menu Left: Fn Layer |
| [g1162 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9972) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Left: Fn Layer |
| [g1162 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9985) | conditional empty | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g871 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16665) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "15", "interruptable": "0"}` | add_layer Menu Right: Enter; add_layer Menu Left: Fn Layer; empty_binding |
| [g871 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16678) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Left: Entry Point |
| [g871 button_menu release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16691) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Left: Double Tap; remove_layer Menu Left: Entry Point |
| [g871 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16702) | mixed empty + real commands; ordered layer operations | `{"chord_button": "15", "delay_start": "300"}` | add_layer Menu Left: Fn Layer 0 1; empty_binding |
| [g871 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16714) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "350", "interruptable": "0"}` | remove_layer Menu Left: Fn Layer |
| [g871 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16729) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g871 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16739) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 35. Menu Right: Entry Point

Pure empty entries by activation: `{"Full_Press": 2, "chord": 3}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **2**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g13039](../../neptune/single-set-alternative_hold-gyro_latest.json#L18378) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g13040](../../neptune/single-set-alternative_hold-gyro_latest.json#L18412) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g13041](../../neptune/single-set-alternative_hold-gyro_latest.json#L18446) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| gyro | [g13042](../../neptune/single-set-alternative_hold-gyro_latest.json#L18541) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g13043](../../neptune/single-set-alternative_hold-gyro_latest.json#L18550) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| joystick | [g13044](../../neptune/single-set-alternative_hold-gyro_latest.json#L18626) / **dpad** | click, touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g13039 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18386) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g13039 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18399) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g13040 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18420) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g13040 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18433) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g13041 button_escape release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18454) | ordered layer operations | `{"haptic_intensity": "0"}` | add_layer Menu Right: Double Tap; remove_layer Menu Right: Entry Point |
| [g13041 button_escape chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18465) | mixed empty + real commands; ordered layer operations | `{"chord_button": "14", "delay_start": "300"}` | add_layer Menu Right: Fn Layer 0 1; empty_binding |
| [g13041 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18477) | ordered layer operations | `{"hold_repeats": "1", "repeat_rate": "350", "interruptable": "0"}` | remove_layer Menu Right: Fn Layer |
| [g13041 button_menu chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18492) | mixed empty + real commands; held-state guard; ordered layer operations | `{"chord_button": "14", "interruptable": "0"}` | add_layer Menu Left: Backspace; add_layer Menu Right: Fn Layer; empty_binding |
| [g13041 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18505) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Entry Point |
| [g13041 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18518) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g13041 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18528) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g13043 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18558) | ordered layer operations | `{"chord_button": "14"}` | add_layer Menu Right: Fn Layer |
| [g13043 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18571) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g13043 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18580) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Menu Right: Fn Layer; remove_layer Menu Right: Entry Point |
| [g13043 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18596) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; add_layer Menu Right: Fn Layer |
| [g13043 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18609) | conditional empty | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g13044 click chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18634) | ordered layer operations | `{"chord_button": "14"}` | add_layer Menu Right: Fn Layer |
| [g13044 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18647) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; add_layer Menu Right: Fn Layer |
| [g13044 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L18660) | conditional empty | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |

## 36. L2: Double Tap

Pure empty entries by activation: `{"Full_Press": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g891](../../neptune/single-set-alternative_hold-gyro_latest.json#L8224) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g892](../../neptune/single-set-alternative_hold-gyro_latest.json#L8248) / **trigger** | edge | `{"layer": "1"}` |
| switch | [g893](../../neptune/single-set-alternative_hold-gyro_latest.json#L16752) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g922](../../neptune/single-set-alternative_hold-gyro_latest.json#L8478) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g923](../../neptune/single-set-alternative_hold-gyro_latest.json#L8517) / **dpad** | touch | `{"layer": "1"}` |
| right_trackpad | [g925](../../neptune/single-set-alternative_hold-gyro_latest.json#L8567) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g927](../../neptune/single-set-alternative_hold-gyro_latest.json#L8586) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g891 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8232) | ordered layer operations | `{}` | add_layer L2: Scroll Down; remove_layer L2: Double Tap |
| [g892 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8256) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g922 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8486) | press empty | `{}` | empty_binding |
| [g922 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8496) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer L2: Double Tap |
| [g923 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8525) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer L2: Double Tap |
| [g893 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16760) | press empty | `{}` | empty_binding |
| [g893 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16770) | press empty | `{}` | empty_binding |
| [g893 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16780) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g893 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16790) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g893 always_on_action Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16801) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer L2: Double Tap |
| [g893 always_on_action Full_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16810) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |

**Always On ordering:** 3 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`A:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 923 |
| left_trigger / edge (`A:13:edge:activators:Full_Press:0`) | input explicitly redefined; groups 891 |
| right_trigger / edge (`A:14:edge:activators:Full_Press:0`) | input explicitly redefined; groups 892 |
| right_joystick / edge (`A:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 922 |
| right_joystick / edge (`A:15:edge:activators:chord:0`) | input explicitly redefined; groups 922 |
| right_joystick / touch (`A:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 922 |
| left_trackpad / click (`A:190:click:activators:Soft_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_west (`A:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_east (`A:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_north (`A:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 927 |
| left_trackpad / dpad_south (`A:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 927 |
| right_trackpad / click (`A:562:click:activators:Soft_Press:0`) | source disabled; groups 925 |
| right_trackpad / touch (`A:562:touch:activators:Full_Press:0`) | source disabled; groups 925 |
| switch / button_escape (`A:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 893 |
| switch / button_menu (`A:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 893 |

## 37. R2: Double Tap

Pure empty entries by activation: `{"Full_Press": 3}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g895](../../neptune/single-set-alternative_hold-gyro_latest.json#L8279) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g896](../../neptune/single-set-alternative_hold-gyro_latest.json#L8300) / **trigger** | edge | `{"layer": "1"}` |
| switch | [g897](../../neptune/single-set-alternative_hold-gyro_latest.json#L16828) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g928](../../neptune/single-set-alternative_hold-gyro_latest.json#L8595) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g929](../../neptune/single-set-alternative_hold-gyro_latest.json#L8634) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g930](../../neptune/single-set-alternative_hold-gyro_latest.json#L8663) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g931](../../neptune/single-set-alternative_hold-gyro_latest.json#L8672) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g895 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8287) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g896 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8308) | ordered layer operations | `{}` | add_layer R2: Scroll Up; remove_layer R2: Double Tap |
| [g928 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8603) | press empty | `{}` | empty_binding |
| [g928 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8613) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer R2: Double Tap |
| [g929 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8642) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer R2: Double Tap |
| [g897 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16836) | press empty | `{}` | empty_binding |
| [g897 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16846) | press empty | `{}` | empty_binding |
| [g897 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16856) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g897 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16866) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g897 always_on_action Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16877) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer R2: Double Tap |
| [g897 always_on_action Full_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16886) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | mouse_wheel SCROLL_UP |

**Always On ordering:** 3 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`A:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 929 |
| left_trigger / edge (`A:13:edge:activators:Full_Press:0`) | input explicitly redefined; groups 895 |
| right_trigger / edge (`A:14:edge:activators:Full_Press:0`) | input explicitly redefined; groups 896 |
| right_joystick / edge (`A:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 928 |
| right_joystick / edge (`A:15:edge:activators:chord:0`) | input explicitly redefined; groups 928 |
| right_joystick / touch (`A:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 928 |
| left_trackpad / click (`A:190:click:activators:Soft_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_west (`A:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_east (`A:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_north (`A:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 930 |
| left_trackpad / dpad_south (`A:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 930 |
| right_trackpad / click (`A:562:click:activators:Soft_Press:0`) | source disabled; groups 931 |
| right_trackpad / touch (`A:562:touch:activators:Full_Press:0`) | source disabled; groups 931 |
| switch / button_escape (`A:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 897 |
| switch / button_menu (`A:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 897 |

## 38. LST: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g751](../../neptune/single-set-alternative_hold-gyro_latest.json#L6847) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g752](../../neptune/single-set-alternative_hold-gyro_latest.json#L6881) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g753](../../neptune/single-set-alternative_hold-gyro_latest.json#L16501) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g763](../../neptune/single-set-alternative_hold-gyro_latest.json#L6953) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g769](../../neptune/single-set-alternative_hold-gyro_latest.json#L7021) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g858](../../neptune/single-set-alternative_hold-gyro_latest.json#L8096) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g859](../../neptune/single-set-alternative_hold-gyro_latest.json#L8105) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g751 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6855) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g751 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6868) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g752 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6889) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g752 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6902) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g763 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6961) | press empty | `{}` | empty_binding |
| [g763 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6971) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer LST: Double Tap |
| [g769 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7029) | ordered layer operations | `{"haptic_intensity": "3"}` | add_layer LST: Temporary Gyro; add_layer LST: Entry Point; remove_layer LST: Double Tap |
| [g753 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16509) | press empty | `{}` | empty_binding |
| [g753 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16519) | press empty | `{}` | empty_binding |
| [g753 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16529) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g753 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16539) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g753 always_on_action Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16549) | ordered layer operations; Always On | `{"delay_start": "200", "interruptable": "0"}` | remove_layer LST: Double Tap |

**Always On ordering:** 1 incoming bindings add this layer last; 3 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`A:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 769 |
| left_trigger / edge (`A:13:edge:activators:Full_Press:0`) | input explicitly redefined; groups 751 |
| right_trigger / edge (`A:14:edge:activators:Full_Press:0`) | input explicitly redefined; groups 752 |
| right_joystick / edge (`A:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 763 |
| right_joystick / edge (`A:15:edge:activators:chord:0`) | input explicitly redefined; groups 763 |
| right_joystick / touch (`A:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 763 |
| left_trackpad / click (`A:190:click:activators:Soft_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_west (`A:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_east (`A:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_north (`A:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 858 |
| left_trackpad / dpad_south (`A:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 858 |
| right_trackpad / click (`A:562:click:activators:Soft_Press:0`) | source disabled; groups 859 |
| right_trackpad / touch (`A:562:touch:activators:Full_Press:0`) | source disabled; groups 859 |
| switch / button_escape (`A:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 753 |
| switch / button_menu (`A:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 753 |

## 39. RST: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g747](../../neptune/single-set-alternative_hold-gyro_latest.json#L6769) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g748](../../neptune/single-set-alternative_hold-gyro_latest.json#L6803) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g749](../../neptune/single-set-alternative_hold-gyro_latest.json#L16436) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g762](../../neptune/single-set-alternative_hold-gyro_latest.json#L6915) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g768](../../neptune/single-set-alternative_hold-gyro_latest.json#L6992) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g856](../../neptune/single-set-alternative_hold-gyro_latest.json#L8078) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g857](../../neptune/single-set-alternative_hold-gyro_latest.json#L8087) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g747 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6777) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g747 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6790) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g748 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6811) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g748 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6824) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g762 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6923) | press empty | `{}` | empty_binding |
| [g762 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L6933) | ordered layer operations | `{"haptic_intensity": "3"}` | add_layer RST: Temporary Gyro; add_layer RST: Entry Point; remove_layer RST: Double Tap |
| [g768 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7000) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer RST: Double Tap |
| [g749 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16444) | press empty | `{}` | empty_binding |
| [g749 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16454) | press empty | `{}` | empty_binding |
| [g749 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16464) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g749 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16474) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g749 always_on_action Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16484) | ordered layer operations; Always On | `{"delay_start": "200", "interruptable": "0"}` | remove_layer RST: Double Tap |

**Always On ordering:** 1 incoming bindings add this layer last; 3 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`A:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 768 |
| left_trigger / edge (`A:13:edge:activators:Full_Press:0`) | input explicitly redefined; groups 747 |
| right_trigger / edge (`A:14:edge:activators:Full_Press:0`) | input explicitly redefined; groups 748 |
| right_joystick / edge (`A:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 762 |
| right_joystick / edge (`A:15:edge:activators:chord:0`) | input explicitly redefined; groups 762 |
| right_joystick / touch (`A:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 762 |
| left_trackpad / click (`A:190:click:activators:Soft_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_west (`A:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_east (`A:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_north (`A:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 856 |
| left_trackpad / dpad_south (`A:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 856 |
| right_trackpad / click (`A:562:click:activators:Soft_Press:0`) | source disabled; groups 857 |
| right_trackpad / touch (`A:562:touch:activators:Full_Press:0`) | source disabled; groups 857 |
| switch / button_escape (`A:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 749 |
| switch / button_menu (`A:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 749 |

## 40. RTP: Double Tap

Pure empty entries by activation: `{"Full_Press": 5}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g987](../../neptune/single-set-alternative_hold-gyro_latest.json#L9069) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g988](../../neptune/single-set-alternative_hold-gyro_latest.json#L9103) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g989](../../neptune/single-set-alternative_hold-gyro_latest.json#L17036) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| right_joystick | [g1023](../../neptune/single-set-alternative_hold-gyro_latest.json#L9167) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1024](../../neptune/single-set-alternative_hold-gyro_latest.json#L9206) / **dpad** | touch | `{"layer": "1"}` |
| left_trackpad | [g1027](../../neptune/single-set-alternative_hold-gyro_latest.json#L9283) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1298](../../neptune/single-set-alternative_hold-gyro_latest.json#L11416) / **dpad** | dpad_north, dpad_south, dpad_east, dpad_west, edge | `{"layer": "1", "requires_click": "0", "layout": "0", "deadzone": "18190", "edge_binding_radius": "22250", "edge_binding_invert": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g987 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9077) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g987 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9090) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g988 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9111) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g988 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9124) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1023 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9175) | press empty | `{}` | empty_binding |
| [g1023 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9185) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer RTP: Double Tap |
| [g1024 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9214) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer RTP: Double Tap |
| [g1298 dpad_north Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11424) | ordered layer operations | `{"haptic_intensity": "3", "interruptable": "0"}` | add_layer RTP: Circular Scroll; remove_layer RTP: Double Tap |
| [g1298 dpad_south Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11441) | ordered layer operations | `{"haptic_intensity": "3", "interruptable": "0"}` | add_layer RTP: Circular Scroll; remove_layer RTP: Double Tap |
| [g1298 dpad_east Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11458) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Double Tap |
| [g1298 dpad_west Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11471) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Double Tap |
| [g1298 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L11484) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Double Tap |
| [g989 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17044) | press empty | `{}` | empty_binding |
| [g989 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17054) | press empty | `{}` | empty_binding |
| [g989 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17064) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g989 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17074) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g989 always_on_action Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17084) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer RTP: Double Tap |

**Always On ordering:** 1 incoming bindings add this layer last; 8 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`A:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1024 |
| left_trigger / edge (`A:13:edge:activators:Full_Press:0`) | input explicitly redefined; groups 987 |
| right_trigger / edge (`A:14:edge:activators:Full_Press:0`) | input explicitly redefined; groups 988 |
| right_joystick / edge (`A:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1023 |
| right_joystick / edge (`A:15:edge:activators:chord:0`) | input explicitly redefined; groups 1023 |
| right_joystick / touch (`A:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1023 |
| left_trackpad / click (`A:190:click:activators:Soft_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_west (`A:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_east (`A:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_north (`A:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 1027 |
| left_trackpad / dpad_south (`A:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 1027 |
| right_trackpad / click (`A:562:click:activators:Soft_Press:0`) | source mode replaced; runtime inheritance check; groups 1298 |
| right_trackpad / touch (`A:562:touch:activators:Full_Press:0`) | source mode replaced; runtime inheritance check; groups 1298 |
| switch / button_escape (`A:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 989 |
| switch / button_menu (`A:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 989 |

## 41. Menu Left: Double Tap

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1044](../../neptune/single-set-alternative_hold-gyro_latest.json#L9458) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1045](../../neptune/single-set-alternative_hold-gyro_latest.json#L9468) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1046](../../neptune/single-set-alternative_hold-gyro_latest.json#L9502) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1047](../../neptune/single-set-alternative_hold-gyro_latest.json#L17111) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| left_trackpad | [g1148](../../neptune/single-set-alternative_hold-gyro_latest.json#L9848) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1149](../../neptune/single-set-alternative_hold-gyro_latest.json#L9857) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g1165](../../neptune/single-set-alternative_hold-gyro_latest.json#L10085) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1166](../../neptune/single-set-alternative_hold-gyro_latest.json#L10124) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g1199](../../neptune/single-set-alternative_hold-gyro_latest.json#L10357) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1045 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9476) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1045 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9489) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1046 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9510) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1046 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9523) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1165 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10093) | press empty | `{}` | empty_binding |
| [g1165 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10103) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer Menu Left: Double Tap |
| [g1166 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10132) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer Menu Left: Double Tap |
| [g1047 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17119) | press empty | `{}` | empty_binding |
| [g1047 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17129) | ordered layer operations | `{}` | add_layer Menu Left: Escape; remove_layer Menu Left: Double Tap |
| [g1047 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17142) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g1047 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17152) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g1047 always_on_action Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17163) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer Menu Left: Double Tap |
| [g1047 always_on_action Full_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17172) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | key_press ESCAPE |

**Always On ordering:** 2 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`A:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1166 |
| left_trigger / edge (`A:13:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1045 |
| right_trigger / edge (`A:14:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1046 |
| right_joystick / edge (`A:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1165 |
| right_joystick / edge (`A:15:edge:activators:chord:0`) | input explicitly redefined; groups 1165 |
| right_joystick / touch (`A:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1165 |
| left_trackpad / click (`A:190:click:activators:Soft_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_west (`A:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_east (`A:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_north (`A:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 1148 |
| left_trackpad / dpad_south (`A:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 1148 |
| right_trackpad / click (`A:562:click:activators:Soft_Press:0`) | source disabled; groups 1149 |
| right_trackpad / touch (`A:562:touch:activators:Full_Press:0`) | source disabled; groups 1149 |
| switch / button_escape (`A:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 1047 |
| switch / button_menu (`A:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 1047 |

## 42. Menu Right: Double Tap

Pure empty entries by activation: `{"Full_Press": 4}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **yes**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1048](../../neptune/single-set-alternative_hold-gyro_latest.json#L9536) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1049](../../neptune/single-set-alternative_hold-gyro_latest.json#L9546) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1050](../../neptune/single-set-alternative_hold-gyro_latest.json#L9580) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1051](../../neptune/single-set-alternative_hold-gyro_latest.json#L17190) / **switches** | button_escape, button_menu, left_bumper, right_bumper, always_on_action | `{"layer": "1"}` |
| left_trackpad | [g1144](../../neptune/single-set-alternative_hold-gyro_latest.json#L9830) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1145](../../neptune/single-set-alternative_hold-gyro_latest.json#L9839) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g1167](../../neptune/single-set-alternative_hold-gyro_latest.json#L10153) / **joystick_mouse** | edge, touch | `{"layer": "1"}` |
| joystick | [g1168](../../neptune/single-set-alternative_hold-gyro_latest.json#L10192) / **dpad** | touch | `{"layer": "1"}` |
| gyro | [g1200](../../neptune/single-set-alternative_hold-gyro_latest.json#L10366) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1049 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9554) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1049 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9567) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1050 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9588) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1050 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9601) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1167 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10161) | press empty | `{}` | empty_binding |
| [g1167 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10171) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Temporary Gyro; remove_layer RST: Tap Cover; remove_layer RST: Entry Point; remove_layer Menu Right: Double Tap |
| [g1168 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10200) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Temporary Gyro; remove_layer LST: Tap Cover; remove_layer LST: Entry Point; remove_layer Menu Right: Double Tap |
| [g1051 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17198) | ordered layer operations | `{}` | add_layer Menu Right: Tab; remove_layer Menu Right: Double Tap |
| [g1051 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17211) | press empty | `{}` | empty_binding |
| [g1051 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17221) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g1051 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17231) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
| [g1051 always_on_action Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17242) | ordered layer operations; Always On | `{"delay_start": "150", "interruptable": "0"}` | remove_layer Menu Right: Double Tap |
| [g1051 always_on_action Full_Press[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17251) | output/mode replacement candidate; Always On | `{"delay_start": "50", "interruptable": "0"}` | key_press TAB |

**Always On ordering:** 2 incoming bindings add this layer last; 4 directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.

| Base layer-changing route | Interception in this layer |
|---|---|
| joystick / touch (`A:12:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1168 |
| left_trigger / edge (`A:13:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1049 |
| right_trigger / edge (`A:14:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1050 |
| right_joystick / edge (`A:15:edge:activators:Full_Press:0`) | input explicitly redefined; groups 1167 |
| right_joystick / edge (`A:15:edge:activators:chord:0`) | input explicitly redefined; groups 1167 |
| right_joystick / touch (`A:15:touch:activators:Full_Press:0`) | input explicitly redefined; groups 1167 |
| left_trackpad / click (`A:190:click:activators:Soft_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_west (`A:190:dpad_west:activators:Full_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_east (`A:190:dpad_east:activators:Full_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_north (`A:190:dpad_north:activators:Full_Press:0`) | source disabled; groups 1144 |
| left_trackpad / dpad_south (`A:190:dpad_south:activators:Full_Press:0`) | source disabled; groups 1144 |
| right_trackpad / click (`A:562:click:activators:Soft_Press:0`) | source disabled; groups 1145 |
| right_trackpad / touch (`A:562:touch:activators:Full_Press:0`) | source disabled; groups 1145 |
| switch / button_escape (`A:10:button_escape:activators:chord:0`) | input explicitly redefined; groups 1051 |
| switch / button_menu (`A:10:button_menu:activators:chord:0`) | input explicitly redefined; groups 1051 |

## 43. L2: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g775](../../neptune/single-set-alternative_hold-gyro_latest.json#L7059) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g776](../../neptune/single-set-alternative_hold-gyro_latest.json#L7084) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g777](../../neptune/single-set-alternative_hold-gyro_latest.json#L16566) / **switches** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g775 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7067) | ordered layer operations | `{}` | remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; remove_layer L2: Tap Cover |

## 44. R2: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g779](../../neptune/single-set-alternative_hold-gyro_latest.json#L7104) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g780](../../neptune/single-set-alternative_hold-gyro_latest.json#L7114) / **trigger** | edge | `{"layer": "1"}` |
| switch | [g781](../../neptune/single-set-alternative_hold-gyro_latest.json#L16576) / **switches** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g780 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7122) | ordered layer operations | `{}` | remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; remove_layer R2: Tap Cover |

## 45. L2&R2: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **2**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g810](../../neptune/single-set-alternative_hold-gyro_latest.json#L7317) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g811](../../neptune/single-set-alternative_hold-gyro_latest.json#L7349) / **trigger** | edge | `{"layer": "1"}` |
| switch | [g812](../../neptune/single-set-alternative_hold-gyro_latest.json#L16606) / **switches** | left_bumper, right_bumper | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g810 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7325) | mixed empty + real commands; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; remove_layer L2: Modifier 0; remove_layer Gyro \| L2: Modifier 0; empty_binding; remove_layer L2: Tap Cover; empty_binding; remove_layer L2&R2: Tap Cover |
| [g811 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7357) | mixed empty + real commands; ordered layer operations | `{}` | remove_layer L2!R2: Modifier 2; remove_layer Gyro \| L2!R2: Modifier 2; remove_layer R2!L2: Modifier 2; remove_layer Gyro \| R2!L2: Modifier 2; empty_binding; remove_layer R2: Modifier 1; remove_layer Gyro \| R2: Modifier 1; empty_binding; remove_layer R2: Tap Cover; remove_layer L2&R2: Tap Cover |
| [g812 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16614) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g812 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L16624) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 46. LST: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g797](../../neptune/single-set-alternative_hold-gyro_latest.json#L7233) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g798](../../neptune/single-set-alternative_hold-gyro_latest.json#L7243) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g799](../../neptune/single-set-alternative_hold-gyro_latest.json#L16596) / **switches** | none explicitly defined | `{"layer": "1"}` |
| joystick | [g801](../../neptune/single-set-alternative_hold-gyro_latest.json#L7280) / **dpad** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g801 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7288) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer LST: Tap Cover; remove_layer LST: Entry Point |

## 47. RST: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g783](../../neptune/single-set-alternative_hold-gyro_latest.json#L7149) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g784](../../neptune/single-set-alternative_hold-gyro_latest.json#L7159) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g785](../../neptune/single-set-alternative_hold-gyro_latest.json#L16586) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_joystick | [g800](../../neptune/single-set-alternative_hold-gyro_latest.json#L7253) / **joystick_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g800 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L7261) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RST: Tap Cover; remove_layer RST: Entry Point |

## 48. RTP: Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g991](../../neptune/single-set-alternative_hold-gyro_latest.json#L9147) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g992](../../neptune/single-set-alternative_hold-gyro_latest.json#L9157) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g993](../../neptune/single-set-alternative_hold-gyro_latest.json#L17101) / **switches** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1033](../../neptune/single-set-alternative_hold-gyro_latest.json#L9330) / **absolute_mouse** | touch | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1033 touch release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9338) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer RTP: Entry Point; remove_layer RTP: Tap Cover |

## 49. L2: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g949](../../neptune/single-set-alternative_hold-gyro_latest.json#L8925) / **trigger** | edge | `{"layer": "1"}` |
| right_trigger | [g950](../../neptune/single-set-alternative_hold-gyro_latest.json#L8962) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g951](../../neptune/single-set-alternative_hold-gyro_latest.json#L17006) / **switches** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g949 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8933) | output/mode replacement candidate | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | mouse_wheel SCROLL_DOWN |
| [g949 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L8943) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer L2: Scroll Down; remove_layer L2: Double Tap Cover |

## 50. R2: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g953](../../neptune/single-set-alternative_hold-gyro_latest.json#L8982) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g954](../../neptune/single-set-alternative_hold-gyro_latest.json#L8992) / **trigger** | edge | `{"layer": "1"}` |
| switch | [g955](../../neptune/single-set-alternative_hold-gyro_latest.json#L17016) / **switches** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g954 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9000) | output/mode replacement candidate | `{"hold_repeats": "1", "repeat_rate": "50", "interruptable": "0"}` | mouse_wheel SCROLL_UP |
| [g954 edge release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L9010) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer R2: Scroll Up; remove_layer R2: Double Tap Cover |

## 51. Menu Left: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1052](../../neptune/single-set-alternative_hold-gyro_latest.json#L9614) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1053](../../neptune/single-set-alternative_hold-gyro_latest.json#L9624) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g1054](../../neptune/single-set-alternative_hold-gyro_latest.json#L9634) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g1055](../../neptune/single-set-alternative_hold-gyro_latest.json#L17269) / **switches** | button_menu | `{"layer": "1"}` |
| gyro | [g1201](../../neptune/single-set-alternative_hold-gyro_latest.json#L10375) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1055 button_menu Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17277) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press ESCAPE |
| [g1055 button_menu release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17285) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Left: Escape; remove_layer Menu Left: Double Tap Cover |

## 52. Menu Right: Double Tap Cover

Pure empty entries by activation: `{}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **0**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| button_diamond | [g1056](../../neptune/single-set-alternative_hold-gyro_latest.json#L9644) / **four_buttons** | none explicitly defined | `{"layer": "1"}` |
| left_trigger | [g1057](../../neptune/single-set-alternative_hold-gyro_latest.json#L9654) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| right_trigger | [g1058](../../neptune/single-set-alternative_hold-gyro_latest.json#L9664) / **trigger** | none explicitly defined | `{"layer": "1"}` |
| switch | [g1059](../../neptune/single-set-alternative_hold-gyro_latest.json#L17304) / **switches** | button_escape | `{"layer": "1"}` |
| gyro | [g1202](../../neptune/single-set-alternative_hold-gyro_latest.json#L10384) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1059 button_escape Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17312) | output/mode replacement candidate | `{"interruptable": "0"}` | key_press TAB |
| [g1059 button_escape release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17320) | ordered layer operations | `{"haptic_intensity": "0"}` | remove_layer Menu Right: Tab; remove_layer Menu Right: Double Tap Cover |

## 53. Transition Set 0

Pure empty entries by activation: `{"Full_Press": 4, "chord": 6, "release": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g1218](../../neptune/single-set-alternative_hold-gyro_latest.json#L10421) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1219](../../neptune/single-set-alternative_hold-gyro_latest.json#L10455) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1220](../../neptune/single-set-alternative_hold-gyro_latest.json#L17489) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| joystick | [g1233](../../neptune/single-set-alternative_hold-gyro_latest.json#L10489) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g1234](../../neptune/single-set-alternative_hold-gyro_latest.json#L10543) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| gyro | [g1241](../../neptune/single-set-alternative_hold-gyro_latest.json#L10630) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1274](../../neptune/single-set-alternative_hold-gyro_latest.json#L10885) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g1275](../../neptune/single-set-alternative_hold-gyro_latest.json#L10894) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1218 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10429) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1218 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10442) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1219 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10463) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1219 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10476) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1233 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10497) | press empty | `{}` | empty_binding |
| [g1233 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10508) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1233 touch chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10517) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1233 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10527) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 0 |
| [g1234 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10551) | press empty | `{}` | empty_binding |
| [g1234 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10562) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1234 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10571) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1234 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10581) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 0 |
| [g1234 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10595) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1234 touch chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10604) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1234 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10614) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 0 |
| [g1220 button_escape release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17497) | release empty | `{}` | empty_binding |
| [g1220 button_menu release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17507) | release empty | `{}` | empty_binding |
| [g1220 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17517) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g1220 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17527) | output/mode replacement candidate | `{}` | mouse_button RIGHT |

## 54. Transition Set 1

Pure empty entries by activation: `{"Full_Press": 4, "chord": 6, "release": 2}`. Mixed entries containing empty subcommands: **0**. Chord-protected cleanup entries: **3**. Always On owner: **no**.

| Active source | Group / mode | Explicit inputs | Source settings |
|---|---|---|---|
| left_trigger | [g1245](../../neptune/single-set-alternative_hold-gyro_latest.json#L10649) / **trigger** | click, edge | `{"layer": "1"}` |
| right_trigger | [g1246](../../neptune/single-set-alternative_hold-gyro_latest.json#L10683) / **trigger** | click, edge | `{"layer": "1"}` |
| switch | [g1247](../../neptune/single-set-alternative_hold-gyro_latest.json#L17540) / **switches** | button_escape, button_menu, left_bumper, right_bumper | `{"layer": "1"}` |
| joystick | [g1260](../../neptune/single-set-alternative_hold-gyro_latest.json#L10717) / **dpad** | click, touch | `{"layer": "1"}` |
| right_joystick | [g1261](../../neptune/single-set-alternative_hold-gyro_latest.json#L10771) / **joystick_mouse** | click, edge, touch | `{"layer": "1"}` |
| gyro | [g1271](../../neptune/single-set-alternative_hold-gyro_latest.json#L10858) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| left_trackpad | [g1272](../../neptune/single-set-alternative_hold-gyro_latest.json#L10867) / **disabled** | none explicitly defined | `{"layer": "1"}` |
| right_trackpad | [g1273](../../neptune/single-set-alternative_hold-gyro_latest.json#L10876) / **disabled** | none explicitly defined | `{"layer": "1"}` |

| Exact activator | Classification | Settings | Binding payload in storage order |
|---|---|---|---|
| [g1245 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10657) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1245 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10670) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_DOWN |
| [g1246 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10691) | press empty | `{"haptic_intensity": "2"}` | empty_binding |
| [g1246 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10704) | output/mode replacement candidate | `{}` | mouse_wheel SCROLL_UP |
| [g1260 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10725) | press empty | `{}` | empty_binding |
| [g1260 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10736) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1260 touch chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10745) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1260 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10755) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 1 |
| [g1261 click Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10779) | press empty | `{}` | empty_binding |
| [g1261 edge chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10790) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1261 edge chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10799) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1261 edge Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10809) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 1 |
| [g1261 touch chord[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10823) | conditional empty; held-state guard | `{"chord_button": "15", "interruptable": "0"}` | empty_binding |
| [g1261 touch chord[1]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10832) | conditional empty; held-state guard | `{"chord_button": "14", "interruptable": "0"}` | empty_binding |
| [g1261 touch Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L10842) | cleanup protected by sibling chord; ordered layer operations | `{"hold_repeats": "1"}` | remove_layer Transition Set 1 |
| [g1247 button_escape release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17548) | release empty | `{}` | empty_binding |
| [g1247 button_menu release[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17558) | release empty | `{}` | empty_binding |
| [g1247 left_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17568) | output/mode replacement candidate | `{}` | mouse_button LEFT |
| [g1247 right_bumper Full_Press[0]](../../neptune/single-set-alternative_hold-gyro_latest.json#L17578) | output/mode replacement candidate | `{}` | mouse_button RIGHT |
