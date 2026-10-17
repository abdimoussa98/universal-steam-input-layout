"""Reviewed construct inventory. Unknown settings must never silently disappear."""

MODES = {'four_buttons', 'dpad', 'trigger', 'joystick_mouse', '2dscroll', 'single_button',
         'gyro_to_mouse', 'disabled', 'absolute_mouse', 'switches', 'scrollwheel', 'joystick_move'}
GROUP_SETTINGS = set('''deadzone deadzone_inner_radius deadzone_outer_radius edge_binding_radius
edge_binding_invert requires_click layout output_joystick output_trigger
gyro_ratchet_button_mask gyro_ratchet_button_requireany_or_all'''.split())
ANALOG = set('''acceleration adaptive_threshold analog_emulation_duty_cycle_pct curve_exponent
custom_curve_exponent deadzone_enable_type flickstick_haptic_bump_per_angle
flickstick_rotation_sensitivity friction gyro_natural_sensitivity gyro_precision_speed
gyro_speed_deadzone gyro_to_2d_conversion_style gyro_vertical_horizontal_ratio
mouse_move_threshold scroll_angle sensitivity sensitivity_vert_scale'''.split())
PRESENTATION = {'button_dist', 'button_size', 'layer'}
FEEDBACK = {'haptic_intensity', 'haptic_intensity_override'}
ENTRY_SETTINGS = set('''activation_threshold chord_button delay_start double_tap_time
edge_binding_invert gyro_ratchet_button_mask gyro_ratchet_button_requireany_or_all
hold_repeats interruptable long_press_time repeat_rate soft_press_sytle'''.split())
COMMANDS = set('add_layer remove_layer hold_layer empty key_press mouse_button xinput_button mouse_wheel mode_shift'.split())
SIMPLIFIED = {
    'acceleration': 'The browser pad uses direct relative movement, without Steam acceleration.',
    'friction': 'No trackball inertia after lift; browser motion stops with contact.',
    'curve_exponent': 'The browser stick uses a linear response after its deadzone.',
    'custom_curve_exponent': 'The browser stick uses a linear response after its deadzone.',
    'analog_emulation_duty_cycle_pct': 'Directional keys are held continuously; Steam duty-cycle modulation is not modeled.',
    'flickstick_haptic_bump_per_angle': 'Visual/audio ticks mark simulated threshold emissions, not physical haptic intervals.',
    'deadzone_enable_type': 'Browser deadzones use radial distance; Steam cross/ellipse variants are not modeled.',
    'scroll_angle': 'Uses tenths of a degree as a demo convention; exported units need Steam verification.',
}


def coverage(inventory):
    result = []
    allowed = {'mode': MODES, 'command': COMMANDS, 'activator': set('Full_Press Start_Press release chord Soft_Press Long_Press Double_Press'.split()),
               'group_setting': GROUP_SETTINGS | ANALOG | PRESENTATION | FEEDBACK,
               'entry_setting': ENTRY_SETTINGS | FEEDBACK}
    for category, counts in sorted(inventory.items()):
        for name, count in sorted(counts.items()):
            if name not in allowed[category]:
                raise ValueError(f'Unreviewed {category}: {name}')
            status, reason = 'implemented', 'Executable under the documented simulator assumptions.'
            if category == 'group_setting' and name in ANALOG:
                status, reason = 'approximation', SIMPLIFIED.get(name, 'Browser motion model; Steam transfer function/defaults require device comparison.')
            elif name in FEEDBACK:
                status, reason = 'visualized', 'Visible feedback; optional browser sound, not physical haptic equivalence.'
            elif category == 'group_setting' and name in PRESENTATION:
                status, reason = 'metadata', 'Retained source metadata; the demo uses its own geometry.'
            result.append(dict(category=category, name=name, count=count, status=status, reason=reason))
    return result
