# Alternative haptic settings

Source: `neptune/single-set-alternative_hold-gyro_latest.json`, single-set-alternative :: always-gyro :: 90.40.

Every explicit setting is listed below, including Off. Rows combine inputs only when their owner, activator, level and timing match. CSV files retain each individual binding and path.

## Mode settings

| owners | mode | setting | value | level |
|---|---|---|---|---|
| Base: dpad active | dpad | haptic_intensity_override | 0 | Off |
| Base: dpad inactive modeshift | dpad | haptic_intensity_override | 0 | Off |
| L2: Temp Cursor Gyro: gyro active | gyro_to_mouse | haptic_intensity | 0 | Off |
| L2: Temp Cursor Gyro: gyro active | gyro_to_mouse | flickstick_haptic_bump_per_angle | 1 | Angle parameter, not intensity |
| R2: Temp Cursor Gyro: gyro active | gyro_to_mouse | haptic_intensity | 0 | Off |
| R2: Temp Cursor Gyro: gyro active | gyro_to_mouse | flickstick_haptic_bump_per_angle | 1 | Angle parameter, not intensity |
| LTP: Arrow Keys: left_trackpad active | dpad | haptic_intensity_override | 3 | High |
| LTP: Click Entry Point: left_trackpad active | dpad | haptic_intensity_override | 0 | Off |
| Base: right_trackpad active | absolute_mouse | haptic_intensity | 0 | Off |
| RTP: Mouse Buttons: right_trackpad active | dpad | haptic_intensity_override | 3 | High |
| RTP: Click Entry Point: right_trackpad active | dpad | haptic_intensity_override | 0 | Off |
| RTP: Circular Scroll: right_trackpad active | scrollwheel | haptic_intensity | 1 | Low |
| Cursor Gyro: gyro active | gyro_to_mouse | haptic_intensity | 0 | Off |
| Cursor Gyro: gyro active | gyro_to_mouse | flickstick_haptic_bump_per_angle | 1 | Angle parameter, not intensity |
| Gamepad: dpad active | dpad | haptic_intensity_override | 0 | Off |
| Menu Left!Right: Double Tap: dpad active | dpad | haptic_intensity_override | 0 | Off |
| Menu Right!Left: Double Tap: dpad active | dpad | haptic_intensity_override | 0 | Off |
| Menu Keys: dpad active | dpad | haptic_intensity_override | 0 | Off |

## Activator settings

| owners | inputs | activator | level | delay_start | long_press_time | hold_repeats | repeat_rate |
|---|---|---|---|---|---|---|---|
| Base: left_trackpad active | click | Soft_Press[0] | High |  |  |  |  |
| Base: right_trackpad active | click | Soft_Press[0] | High |  |  |  |  |
| Gyro \| L2!R2: Modifier 2: right_trigger active | edge | chord[0] | High | 200 |  |  |  |
| Gyro \| L2: Modifier 0: left_trigger active | edge | chord[0] | High | 200 |  |  |  |
| Gyro \| R2!L2: Modifier 2: left_trigger active | edge | chord[0] | High | 200 |  |  |  |
| Gyro \| R2: Modifier 1: right_trigger active | edge | chord[0] | High | 200 |  |  |  |
| L2!R2: Modifier 2: right_trigger active | edge | chord[0] | High | 200 |  |  |  |
| L2: Modifier 0: left_trigger active | edge | chord[0] | High | 200 |  |  |  |
| LST: Double Tap: joystick active | touch | Full_Press[0] | High |  |  |  |  |
| LTP: Arrow Keys: left_trackpad active | dpad_north, dpad_south, dpad_east, dpad_west | Full_Press[0] | High |  |  |  |  |
| LTP: Middle Click: left_trackpad active | click | Full_Press[0] | High |  |  |  |  |
| Menu Left!Right: Entry Point: switch active | button_escape | chord[0] | High | 200 |  |  |  |
| Menu Right!Left: Entry Point: switch active | button_menu | chord[0] | High | 200 |  |  |  |
| R2!L2: Modifier 2: left_trigger active | edge | chord[0] | High | 200 |  |  |  |
| R2: Modifier 1: right_trigger active | edge | chord[0] | High | 200 |  |  |  |
| RST: Double Tap: right_joystick active | touch | Full_Press[0] | High |  |  |  |  |
| RTP: Double Tap: right_trackpad active | dpad_north, dpad_south | Full_Press[0] | High |  |  |  |  |
| RTP: Middle Click: right_trackpad active | click | Full_Press[0] | High |  |  |  |  |
| RTP: Mouse Buttons: right_trackpad active | dpad_east, dpad_west | Full_Press[0] | High |  |  |  |  |
| Steering \| L2!R2: Modifier 2: right_trigger active | edge | chord[0] | High | 200 |  |  |  |
| Steering \| LS: Fallback Guard: left_trigger active | edge | Full_Press[0] | High |  |  | 1 | 50 |
| Steering \| LS: Fallback Guard: right_trigger active | edge | Full_Press[0] | High |  |  | 1 | 50 |
| Steering \| R2!L2: Modifier 2: left_trigger active | edge | chord[0] | High | 200 |  |  |  |
| Steering: joystick active | dpad_north, dpad_south | Soft_Press[0] | High |  |  | 1 | 50 |
| Transition Set 0: switch active | button_escape, button_menu | release[0] | High |  |  |  |  |
| Transition Set 1: switch active | button_escape, button_menu | release[0] | High |  |  |  |  |
| Transition Set 2: switch active | button_escape, button_menu | release[0] | High |  |  |  |  |
| LST: Double Tap: left_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| LST: Double Tap: right_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Left!Right: Double Tap: left_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Left!Right: Double Tap: right_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Left: Double Tap: left_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Left: Double Tap: right_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Left: Fn Layer: joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| Menu Left: Fn Layer: right_joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| Menu Right!Left: Double Tap: left_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Right!Left: Double Tap: right_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Right: Double Tap: left_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Right: Double Tap: right_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Menu Right: Fn Layer: joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| Menu Right: Fn Layer: right_joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| RST: Double Tap: left_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| RST: Double Tap: right_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| RTP: Double Tap: left_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| RTP: Double Tap: right_trigger active | click | Full_Press[0] | Medium |  |  |  |  |
| Stateful \| Menu Left: Fn Layer: joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| Stateful \| Menu Left: Fn Layer: right_joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| Stateful \| Menu Right: Fn Layer: joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| Stateful \| Menu Right: Fn Layer: right_joystick active | dpad_north, dpad_south, dpad_east, dpad_west | chord[0] | Medium |  |  |  |  |
| Base: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Gamepad: switch active | button_escape, button_menu | Long_Press[0] | Low |  | 200 |  |  |
| L2: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| LST: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Menu Left!Right: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Menu Left: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Menu Right!Left: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Menu Right: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| R2: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| RST: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| RTP: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Steering \| LS Down: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Steering \| LS Up: Double Tap: left_trackpad active | dpad_west, dpad_east, dpad_north, dpad_south | Full_Press[0] | Low |  |  |  |  |
| Backspace: joystick active | touch | release[0] | Off |  |  |  |  |
| Backspace: left_trackpad active | touch | Full_Press[0] | Off |  |  |  |  |
| Backspace: left_trackpad active | touch | release[0] | Off |  |  |  |  |
| Backspace: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Base: joystick active | edge | Soft_Press[0] | Off |  |  |  |  |
| Base: right_joystick active | edge | Full_Press[0] | Off |  |  | 1 |  |
| Base: right_trackpad active | touch | Full_Press[0] | Off |  |  | 1 |  |
| Cursor Gyro: joystick active | edge | chord[0] | Off |  |  | 1 |  |
| Cursor Gyro: right_joystick active | edge | chord[0] | Off |  |  | 1 |  |
| Enter: joystick active | touch | release[0] | Off |  |  |  |  |
| Enter: left_trackpad active | touch | Full_Press[0] | Off |  |  |  |  |
| Enter: left_trackpad active | touch | release[0] | Off |  |  |  |  |
| Enter: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Escape: joystick active | touch | release[0] | Off |  |  |  |  |
| Escape: left_trackpad active | touch | Full_Press[0] | Off |  |  |  |  |
| Escape: left_trackpad active | touch | release[0] | Off |  |  |  |  |
| Escape: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro Off Ramp Up: right_joystick active | edge | Soft_Press[0] | Off |  |  | 1 |  |
| Gyro Off Ramp Up: right_joystick active | edge | Soft_Press[1] | Off | 5 |  |  |  |
| Gyro \| L2!R2: Modifier 2: joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| L2!R2: Modifier 2: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| L2: Modifier 0: button_diamond active | button_a, button_b, button_x, button_y | chord[1] | Off |  |  | 1 |  |
| Gyro \| L2: Modifier 0: dpad active | dpad_north, dpad_south, dpad_east, dpad_west | chord[1] | Off |  |  | 1 |  |
| Gyro \| L2: Modifier 0: joystick active | click | chord[1] | Off |  |  | 1 |  |
| Gyro \| L2: Modifier 0: joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| L2: Modifier 0: right_joystick active | click | chord[1] | Off |  |  | 1 |  |
| Gyro \| L2: Modifier 0: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| L2: Modifier 0: switch active | button_escape, button_menu | chord[1] | Off |  |  | 1 |  |
| Gyro \| R2!L2: Modifier 2: joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| R2!L2: Modifier 2: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| R2: Modifier 1: button_diamond active | button_a, button_b, button_x, button_y | chord[1] | Off |  |  | 1 |  |
| Gyro \| R2: Modifier 1: dpad active | dpad_north, dpad_south, dpad_east, dpad_west | chord[1] | Off |  |  | 1 |  |
| Gyro \| R2: Modifier 1: joystick active | click | chord[1] | Off |  |  | 1 |  |
| Gyro \| R2: Modifier 1: joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| R2: Modifier 1: right_joystick active | click | chord[1] | Off |  |  | 1 |  |
| Gyro \| R2: Modifier 1: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Gyro \| R2: Modifier 1: switch active | button_escape, button_menu | chord[1] | Off |  |  | 1 |  |
| L2!R2: Modifier 2: joystick active | touch | release[0] | Off |  |  |  |  |
| L2!R2: Modifier 2: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2&R2: Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| L2&R2: Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Double Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Double Tap Cover: left_trigger active | edge | release[0] | Off |  |  |  |  |
| L2: Double Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| L2: Modifier 0: button_diamond active | button_a, button_b, button_x, button_y | chord[1] | Off |  |  | 1 |  |
| L2: Modifier 0: dpad active | dpad_north, dpad_south, dpad_east, dpad_west | chord[1] | Off |  |  | 1 |  |
| L2: Modifier 0: joystick active | click | chord[1] | Off |  |  | 1 |  |
| L2: Modifier 0: joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Modifier 0: right_joystick active | click | chord[1] | Off |  |  | 1 |  |
| L2: Modifier 0: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Modifier 0: switch active | button_escape, button_menu | chord[1] | Off |  |  | 1 |  |
| L2: Scroll Down: joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Scroll Down: left_trigger active | edge | release[0] | Off |  |  |  |  |
| L2: Scroll Down: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Temp Cursor Gyro: button_diamond active | button_a, button_b, button_x, button_y | Full_Press[0] | Off |  |  | 1 |  |
| L2: Temp Cursor Gyro: dpad active | dpad_north, dpad_south, dpad_east, dpad_west | Full_Press[0] | Off |  |  | 1 |  |
| L2: Temp Cursor Gyro: joystick active | click | Full_Press[0] | Off |  |  | 1 |  |
| L2: Temp Cursor Gyro: joystick active | edge | chord[1] | Off |  |  | 1 |  |
| L2: Temp Cursor Gyro: joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Temp Cursor Gyro: right_joystick active | click | Full_Press[0] | Off |  |  | 1 |  |
| L2: Temp Cursor Gyro: right_joystick active | edge | chord[1] | Off |  |  | 1 |  |
| L2: Temp Cursor Gyro: right_joystick active | touch | release[0] | Off |  |  |  |  |
| L2: Temp Cursor Gyro: right_trigger active | edge | Full_Press[0] | Off |  |  | 1 |  |
| L2: Temp Cursor Gyro: switch active | button_escape, button_menu | Full_Press[0] | Off |  |  | 1 |  |
| LST: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| LST: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| LST: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| LST: Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| LST: Temporary Gyro: joystick active | touch | release[0] | Off |  |  |  |  |
| LTP: Arrow Keys: joystick active | touch | release[0] | Off |  |  |  |  |
| LTP: Arrow Keys: left_trackpad active | click | Soft_Press[0] | Off |  |  |  |  |
| LTP: Arrow Keys: left_trackpad active | click | Soft_Press[1] | Off |  |  | 1 |  |
| LTP: Arrow Keys: left_trackpad active | touch | release[0] | Off |  |  |  |  |
| LTP: Arrow Keys: right_joystick active | touch | release[0] | Off |  |  |  |  |
| LTP: Click Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| LTP: Click Entry Point: left_trackpad active | touch | Full_Press[0] | Off |  |  | 1 | 55 |
| LTP: Click Entry Point: left_trackpad active | edge | Soft_Press[0] | Off |  |  | 1 | 50 |
| LTP: Click Entry Point: left_trackpad active | edge | Soft_Press[1] | Off | 5 |  | 1 | 50 |
| LTP: Click Entry Point: left_trackpad active | touch | release[0] | Off |  |  |  |  |
| LTP: Click Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| LTP: Middle Click: joystick active | touch | release[0] | Off |  |  |  |  |
| LTP: Middle Click: left_trackpad active | click | Soft_Press[0] | Off |  |  |  |  |
| LTP: Middle Click: left_trackpad active | click | Soft_Press[1] | Off |  |  | 1 |  |
| LTP: Middle Click: left_trackpad active | touch | release[0] | Off |  |  |  |  |
| LTP: Middle Click: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Buttons: Left Stick Guard: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Buttons: Left Stick Guard: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Buttons: Left Stick Guard: switch active | button_menu, button_escape | release[0] | Off |  |  |  |  |
| Menu Buttons: Right Stick Guard: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Buttons: Right Stick Guard: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Buttons: Right Stick Guard: switch active | button_menu, button_escape | release[0] | Off |  |  |  |  |
| Menu Buttons: Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Buttons: Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Keys: joystick active | edge | chord[0] | Off |  |  | 1 |  |
| Menu Keys: right_joystick active | edge | chord[0] | Off |  |  | 1 |  |
| Menu Left!Right: Double Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Double Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Double Tap Cover: switch active | button_escape | release[0] | Off |  |  |  |  |
| Menu Left!Right: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Double Tap: switch active | button_menu | release[0] | Off |  |  |  |  |
| Menu Left!Right: Enter: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Enter: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Enter: switch active | button_escape, button_menu | release[0] | Off |  |  |  |  |
| Menu Left!Right: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left!Right: Entry Point: switch active | button_escape | release[0] | Off |  |  |  |  |
| Menu Left: Double Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Double Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Double Tap Cover: switch active | button_menu | release[0] | Off |  |  |  |  |
| Menu Left: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Entry Point: switch active | button_menu | release[0] | Off |  |  |  |  |
| Menu Left: Escape: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Escape: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Escape: switch active | button_menu | release[0] | Off |  |  |  |  |
| Menu Left: Fn Layer: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Fn Layer: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Left: Fn Layer: switch active | button_menu | release[0] | Off |  |  |  |  |
| Menu Right!Left: Backspace: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Backspace: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Backspace: switch active | button_escape, button_menu | release[0] | Off |  |  |  |  |
| Menu Right!Left: Double Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Double Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Double Tap Cover: switch active | button_menu | release[0] | Off |  |  |  |  |
| Menu Right!Left: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Double Tap: switch active | button_escape | release[0] | Off |  |  |  |  |
| Menu Right!Left: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right!Left: Entry Point: switch active | button_menu | release[0] | Off |  |  |  |  |
| Menu Right: Double Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Double Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Double Tap Cover: switch active | button_escape | release[0] | Off |  |  |  |  |
| Menu Right: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Entry Point: switch active | button_escape | release[0] | Off |  |  |  |  |
| Menu Right: Fn Layer: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Fn Layer: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Fn Layer: switch active | button_escape | release[0] | Off |  |  |  |  |
| Menu Right: Tab: joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Tab: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Menu Right: Tab: switch active | button_escape | release[0] | Off |  |  |  |  |
| R2!L2: Modifier 2: joystick active | touch | release[0] | Off |  |  |  |  |
| R2!L2: Modifier 2: right_joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Double Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Double Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Double Tap Cover: right_trigger active | edge | release[0] | Off |  |  |  |  |
| R2: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| R2: Modifier 1: button_diamond active | button_a, button_b, button_x, button_y | chord[1] | Off |  |  | 1 |  |
| R2: Modifier 1: dpad active | dpad_north, dpad_south, dpad_east, dpad_west | chord[1] | Off |  |  | 1 |  |
| R2: Modifier 1: joystick active | click | chord[1] | Off |  |  | 1 |  |
| R2: Modifier 1: joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Modifier 1: right_joystick active | click | chord[1] | Off |  |  | 1 |  |
| R2: Modifier 1: right_joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Modifier 1: switch active | button_escape, button_menu | chord[1] | Off |  |  | 1 |  |
| R2: Scroll Up: joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Scroll Up: right_joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Scroll Up: right_trigger active | edge | release[0] | Off |  |  |  |  |
| R2: Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Temp Cursor Gyro: button_diamond active | button_a, button_b, button_x, button_y | Full_Press[0] | Off |  |  | 1 |  |
| R2: Temp Cursor Gyro: dpad active | dpad_north, dpad_south, dpad_east, dpad_west | Full_Press[0] | Off |  |  | 1 |  |
| R2: Temp Cursor Gyro: joystick active | click | Full_Press[0] | Off |  |  | 1 |  |
| R2: Temp Cursor Gyro: joystick active | edge | chord[1] | Off |  |  | 1 |  |
| R2: Temp Cursor Gyro: joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Temp Cursor Gyro: left_trigger active | edge | Full_Press[0] | Off |  |  | 1 |  |
| R2: Temp Cursor Gyro: right_joystick active | click | Full_Press[0] | Off |  |  | 1 |  |
| R2: Temp Cursor Gyro: right_joystick active | edge | chord[1] | Off |  |  | 1 |  |
| R2: Temp Cursor Gyro: right_joystick active | touch | release[0] | Off |  |  |  |  |
| R2: Temp Cursor Gyro: switch active | button_escape, button_menu | Full_Press[0] | Off |  |  | 1 |  |
| RST: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| RST: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| RST: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RST: Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RST: Temporary Gyro: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Circular Scroll: joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Circular Scroll: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Circular Scroll: right_trackpad active | click | Soft_Press[0] | Off |  |  |  |  |
| RTP: Circular Scroll: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| RTP: Click Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Click Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Click Entry Point: right_trackpad active | touch | Full_Press[0] | Off |  |  | 1 | 55 |
| RTP: Click Entry Point: right_trackpad active | edge | Soft_Press[0] | Off |  |  | 1 | 50 |
| RTP: Click Entry Point: right_trackpad active | edge | Soft_Press[1] | Off | 5 |  | 1 | 50 |
| RTP: Click Entry Point: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| RTP: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Double Tap: left_trigger active | edge | release[0] | Off |  |  |  |  |
| RTP: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Double Tap: right_trackpad active | dpad_east, dpad_west, edge | Full_Press[0] | Off |  |  |  |  |
| RTP: Double Tap: right_trigger active | edge | release[0] | Off |  |  |  |  |
| RTP: Double Tap: switch active | button_escape, button_menu | release[0] | Off |  |  |  |  |
| RTP: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Entry Point: right_trackpad active | touch | chord[0] | Off | 150 |  |  |  |
| RTP: Entry Point: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| RTP: Middle Click: joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Middle Click: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Middle Click: right_trackpad active | click | Soft_Press[0] | Off |  |  |  |  |
| RTP: Middle Click: right_trackpad active | click | Soft_Press[1] | Off |  |  | 1 |  |
| RTP: Middle Click: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| RTP: Mouse Buttons: joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Mouse Buttons: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Mouse Buttons: right_trackpad active | dpad_north, dpad_south | Full_Press[0] | Off |  |  |  |  |
| RTP: Mouse Buttons: right_trackpad active | click | Soft_Press[0] | Off |  |  |  |  |
| RTP: Mouse Buttons: right_trackpad active | click | Soft_Press[1] | Off |  |  | 1 |  |
| RTP: Mouse Buttons: right_trackpad active | dpad_north, dpad_south | chord[0] | Off | 150 |  | 1 |  |
| RTP: Mouse Buttons: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| RTP: Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| RTP: Tap Cover: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Left: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Left: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Left: Entry Point: switch active | button_menu | release[0] | Off |  |  |  |  |
| Stateful \| Menu Left: Fn Layer: joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Left: Fn Layer: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Left: Fn Layer: switch active | button_menu | release[0] | Off |  |  |  |  |
| Stateful \| Menu Right: Entry Point: joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Right: Entry Point: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Right: Entry Point: switch active | button_escape | release[0] | Off |  |  |  |  |
| Stateful \| Menu Right: Fn Layer: joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Right: Fn Layer: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Stateful \| Menu Right: Fn Layer: switch active | button_escape | release[0] | Off |  |  |  |  |
| Steering \| L2!R2: Modifier 2: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| L2!R2: Modifier 2: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| L2!R2: Modifier 2: right_trigger active | edge | release[0] | Off |  |  |  |  |
| Steering \| L2: S Key: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| L2: S Key: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Down: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Down: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Down: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Down: Modifier 0: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Down: Modifier 0: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Up: Double Tap: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Up: Double Tap: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Up: Double Tap: right_trackpad active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Up: Modifier 1: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS Up: Modifier 1: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS: Double Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS: Double Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS: Fallback Guard: joystick active | edge | chord[0] | Off |  |  | 1 |  |
| Steering \| LS: Fallback Guard: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS: Fallback Guard: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS: Tap Cover: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| LS: Tap Cover: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| R2!L2: Modifier 2: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| R2!L2: Modifier 2: left_trigger active | edge | release[0] | Off |  |  |  |  |
| Steering \| R2!L2: Modifier 2: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| R2: W Key: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering \| R2: W Key: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Steering: joystick active | touch | release[0] | Off |  |  |  |  |
| Steering: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Tab: joystick active | touch | release[0] | Off |  |  |  |  |
| Tab: left_trackpad active | touch | Full_Press[0] | Off |  |  |  |  |
| Tab: left_trackpad active | touch | release[0] | Off |  |  |  |  |
| Tab: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Transition Set 0: joystick active | touch | release[0] | Off |  |  |  |  |
| Transition Set 0: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Transition Set 1: joystick active | touch | release[0] | Off |  |  |  |  |
| Transition Set 1: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Transition Set 2: joystick active | touch | release[0] | Off |  |  |  |  |
| Transition Set 2: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Turning Ramp Up 0: joystick active | touch | release[0] | Off |  |  |  |  |
| Turning Ramp Up 0: right_joystick active | edge | Soft_Press[0] | Off | 250 |  |  |  |
| Turning Ramp Up 0: right_joystick active | edge | Soft_Press[1] | Off |  |  | 1 |  |
| Turning Ramp Up 0: right_joystick active | touch | release[0] | Off |  |  |  |  |
| Turning Ramp Up 1: joystick active | touch | release[0] | Off |  |  |  |  |
| Turning Ramp Up 1: right_joystick active | edge | Soft_Press[0] | Off |  |  | 1 |  |
| Turning Ramp Up 1: right_joystick active | touch | release[0] | Off |  |  |  |  |
