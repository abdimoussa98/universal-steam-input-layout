use super::*;

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn steering_position_selects_inherited_clicks_and_cover() {
    let mut s = State::default();
    s.select_mode(Mode::Steering);
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::R1, true);
    i.stick_positions[0] = Some([0, -800]);
    step(&mut s, &i, 10);
    assert_eq!(s.control_labels(&profile())[10], "Mouse back");
    assert_eq!(s.control_labels(&profile())[11], "Mouse forward");
    assert_eq!(s.control_labels(&profile())[0], "H");
    step(&mut s, &i, 210);
    assert_eq!(s.control_labels(&profile())[10], "Mouse back");
    i.stick_positions[0] = Some([0, 800]);
    step(&mut s, &i, 220);
    assert_eq!(s.control_labels(&profile())[10], "CAPSLOCK");
    assert_eq!(s.control_labels(&profile())[11], "Mouse middle");
    press(&mut i, Control::R1, false);
    step(&mut s, &i, 230);
    assert_eq!(s.control_labels(&profile())[10], "Q");
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn steering_center_sideways_combo_and_double_tap_boundaries() {
    let mut s = State::default();
    s.select_mode(Mode::Steering);
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    i.stick_positions[0] = Some([900, 0]);
    step(&mut s, &i, 10);
    assert_eq!(s.control_labels(&profile())[10], "Q");
    i.stick_positions[0] = Some([0, -405]);
    step(&mut s, &i, 20);
    assert_eq!(s.gestures.steering_lane.phase, Phase::Idle);
    i.stick_positions[0] = Some([0, -800]);
    step(&mut s, &i, 30);
    assert_eq!(s.control_labels(&profile())[11], "Mouse forward");
    i.stick_positions[0] = Some([0, 0]);
    step(&mut s, &i, 100);
    assert_eq!(s.gestures.steering_lane.phase, Phase::Window);
    i.stick_positions[0] = Some([0, -800]);
    step(&mut s, &i, 249);
    assert_eq!(s.gestures.steering_lane.phase, Phase::Second);
    step(&mut s, &i, 399);
    assert_eq!(s.gestures.steering_lane.phase, Phase::Cover);
    press(&mut i, Control::R1, true);
    step(&mut s, &i, 400);
    assert_eq!(s.gestures.steering_lane.phase, Phase::Idle);
    assert_eq!(s.control_labels(&profile())[0], "M");
    s.unavailable(InputStatus::Disconnected);
    assert_eq!(s.input.stick_positions, [None, None]);
    assert_eq!(s.input.pads, [None, None]);
}
