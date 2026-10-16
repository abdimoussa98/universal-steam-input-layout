use keybind_overlay::{BUNDLED_PROFILE, core::*};
#[cfg(target_arch = "wasm32")]
use wasm_bindgen_test::wasm_bindgen_test;
#[cfg(target_arch = "wasm32")]
wasm_bindgen_test::wasm_bindgen_test_configure!(run_in_browser);
fn profile() -> Profile {
    Profile::parse(BUNDLED_PROFILE).unwrap()
}
fn step(s: &mut State, input: &InputFrame, t: u64) {
    s.sample_input("pad", input.clone(), &profile(), t);
}
fn press(input: &mut InputFrame, c: Control, down: bool) {
    input.buttons[c as usize] = down;
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn release_window_has_independent_scroll_and_close_deadlines() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 1000);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 1010);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Pressed);
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 1100);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Window);
    step(&mut s, &i, 1149);
    assert!(
        !s.gestures
            .history
            .iter()
            .any(|e| e.label == "Expected Scroll down")
    );
    step(&mut s, &i, 1150);
    assert_eq!(
        s.gestures
            .history
            .iter()
            .filter(|e| e.label == "Expected Scroll down")
            .count(),
        1
    );
    step(&mut s, &i, 1249);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Window);
    step(&mut s, &i, 1250);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Idle);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn early_second_press_cancels_pending_scroll_and_cover_has_its_own_clock() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::R1, true);
    step(&mut s, &i, 10);
    press(&mut i, Control::R1, false);
    step(&mut s, &i, 100);
    press(&mut i, Control::R1, true);
    step(&mut s, &i, 140);
    step(&mut s, &i, 289);
    assert_eq!(s.gestures.lanes[1].phase, Phase::Second);
    assert!(
        !s.gestures
            .history
            .iter()
            .any(|e| e.label == "Expected Scroll up")
    );
    step(&mut s, &i, 290);
    assert_eq!(s.gestures.lanes[1].phase, Phase::Cover);
    press(&mut i, Control::R1, false);
    step(&mut s, &i, 300);
    assert_eq!(s.gestures.lanes[1].phase, Phase::Idle);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn hold_boundary_used_modifier_and_touch_completion_prevent_tap_scroll() {
    for (action, t) in [(None, 210), (Some(Control::A), 50)] {
        let mut s = State::default();
        let mut i = InputFrame::default();
        step(&mut s, &i, 0);
        press(&mut i, Control::L1, true);
        step(&mut s, &i, 10);
        if let Some(c) = action {
            press(&mut i, c, true);
        }
        step(&mut s, &i, t);
        assert_eq!(
            s.gestures.lanes[0].phase,
            if action.is_some() {
                Phase::Consumed
            } else {
                Phase::Hold
            }
        );
        press(&mut i, Control::L1, false);
        step(&mut s, &i, t + 1);
        assert_eq!(s.gestures.lanes[0].phase, Phase::Idle);
    }
    let mut s = State::default();
    let mut i = InputFrame {
        touches: [Some(true), Some(false)],
        ..Default::default()
    };
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    i.touches[0] = Some(false);
    step(&mut s, &i, 50);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Hold);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn combined_release_preserves_other_side_without_starting_a_tap() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    press(&mut i, Control::R1, true);
    step(&mut s, &i, 40);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Combined);
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 60);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Idle);
    assert_eq!(s.gestures.lanes[1].phase, Phase::Consumed);
    assert_eq!(s.held, [false, true]);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn reconnect_and_mode_switch_never_invent_a_tap_from_an_already_held_button() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 100);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Unknown);
    s.unavailable(InputStatus::Disconnected);
    assert!(s.gestures.history.is_empty());
    step(&mut s, &i, 200);
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 220);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Idle);
    s.select_mode(Mode::Steering);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 230);
    step(&mut s, &i, 500);
    assert_ne!(s.gestures.lanes[0].phase, Phase::Hold);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn menu_hold_changes_all_labels_and_legacy_profiles_do_not_invent_controls() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::Select, true);
    step(&mut s, &i, 10);
    step(&mut s, &i, 210);
    assert_eq!(s.gestures.lanes[2].phase, Phase::Hold);
    assert_eq!(s.control_labels(&profile()).len(), 16);
    let legacy = Profile::parse(include_str!("fixtures/profile.json")).unwrap();
    assert_eq!(
        s.control_labels(&legacy)[Control::L3 as usize],
        "Unavailable"
    );
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn touch_release_cancels_the_pending_window_output() {
    let mut s = State::default();
    let mut i = InputFrame {
        touches: [Some(true), Some(false)],
        ..Default::default()
    };
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 50);
    i.touches[0] = Some(false);
    step(&mut s, &i, 70);
    step(&mut s, &i, 300);
    assert!(
        !s.gestures
            .history
            .iter()
            .any(|e| e.label == "Expected Scroll down")
    );
    assert_eq!(s.gestures.lanes[0].phase, Phase::Idle);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn modifier_menu_outputs_consume_the_bumper_without_starting_a_menu_gesture() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    press(&mut i, Control::Select, true);
    step(&mut s, &i, 50);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Consumed);
    assert!(s.gestures.uncertainty.is_none());
    assert_eq!(
        s.control_labels(&profile())[Control::Select as usize],
        "DELETE"
    );
    press(&mut i, Control::Select, false);
    step(&mut s, &i, 60);
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 80);
    step(&mut s, &i, 300);
    assert!(
        !s.gestures
            .history
            .iter()
            .any(|e| e.label.starts_with("Expected "))
    );
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn opposite_bumper_in_a_window_is_an_output_and_never_becomes_a_modifier() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 50);
    press(&mut i, Control::R1, true);
    step(&mut s, &i, 60);
    assert_eq!(
        s.control_labels(&profile())[Control::R1 as usize],
        "Scroll up"
    );
    step(&mut s, &i, 210);
    assert_eq!(s.control_labels(&profile())[Control::A as usize], "F");
    press(&mut i, Control::R1, false);
    step(&mut s, &i, 220);
    assert_eq!(s.gestures.lanes[1].phase, Phase::Idle);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn second_release_before_cover_reopens_the_window_but_at_deadline_it_ends() {
    for (release, expected) in [(249, Phase::Window), (250, Phase::Idle)] {
        let mut s = State::default();
        let mut i = InputFrame::default();
        step(&mut s, &i, 0);
        press(&mut i, Control::L1, true);
        step(&mut s, &i, 10);
        press(&mut i, Control::L1, false);
        step(&mut s, &i, 50);
        press(&mut i, Control::L1, true);
        step(&mut s, &i, 100);
        press(&mut i, Control::L1, false);
        step(&mut s, &i, release);
        assert_eq!(s.gestures.lanes[0].phase, expected);
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn queued_native_edges_preserve_a_tap_between_snapshots() {
    let p = profile();
    let mut s = State::default();
    let tracker = InputTracker {
        selected: Some("pad".into()),
    };
    let devices = [Device {
        id: "pad".into(),
        name: "Pad".into(),
        standard: true,
        held: [false; 2],
        input: InputFrame::default(),
    }];
    tracker.sample_timed(&mut s, &devices, &[], 0, &p);
    let events = [
        InputEvent {
            device: "pad".into(),
            at_ms: 10,
            change: InputChange::Button(Control::R1, true),
        },
        InputEvent {
            device: "pad".into(),
            at_ms: 20,
            change: InputChange::Button(Control::R1, false),
        },
    ];
    tracker.sample_timed(&mut s, &devices, &events, 25, &p);
    assert_eq!(s.gestures.lanes[1].phase, Phase::Window);
    assert_eq!(s.gestures.lanes[1].output_at_ms, Some(70));
    assert!(!s.input.down(Control::R1));
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn mode_change_and_disconnect_cancel_pending_outputs() {
    for disconnect in [false, true] {
        let mut s = State::default();
        let mut i = InputFrame::default();
        step(&mut s, &i, 0);
        press(&mut i, Control::L1, true);
        step(&mut s, &i, 10);
        press(&mut i, Control::L1, false);
        step(&mut s, &i, 20);
        if disconnect {
            s.unavailable(InputStatus::Disconnected);
        } else {
            s.select_mode(Mode::Menu);
        }
        step(&mut s, &i, 100);
        assert!(s.gestures.history.is_empty());
        assert!(!s.gestures.animating());
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn dashboard_validation_cannot_be_bypassed_with_a_legacy_schema_number() {
    let mut p = profile();
    p.schema_version = 1;
    p.dashboard.as_mut().unwrap().recipes[0].window_ms = 0;
    assert!(Profile::parse(&serde_json::to_string(&p).unwrap()).is_err());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn using_a_binding_after_hold_dismisses_the_cover_and_keeps_inherited_labels() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    step(&mut s, &i, 210);
    assert_eq!(s.control_labels(&profile())[Control::A as usize], "G");
    press(&mut i, Control::A, true);
    step(&mut s, &i, 250);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Consumed);
    assert_eq!(s.control_labels(&profile())[Control::A as usize], "G");
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn stick_movement_applies_the_inherited_tap_cover_without_interrupting_timing() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    i.sticks[0] = true;
    step(&mut s, &i, 30);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Pressed);
    i.sticks[1] = true;
    step(&mut s, &i, 40);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Consumed);
    assert!(s.gestures.uncertainty.is_none());
    assert_eq!(s.control_labels(&profile())[0], "G");
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 50);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Idle);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn uncertain_pad_timing_preserves_known_inherited_bindings_and_owner_release() {
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 10);
    press(&mut i, Control::A, true);
    step(&mut s, &i, 30);
    press(&mut i, Control::A, false);
    step(&mut s, &i, 40);
    i.pad_active = true;
    step(&mut s, &i, 50);
    assert_eq!(s.gestures.lanes[0].phase, Phase::Interrupted);
    assert_eq!(s.control_labels(&profile())[0], "G");
    press(&mut i, Control::L1, false);
    step(&mut s, &i, 60);
    assert_eq!(s.control_labels(&profile())[0], "F");
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn shared_timer_follows_the_gesture_not_an_opposite_output() {
    let p = profile();
    let mut s = State::default();
    let mut i = InputFrame::default();
    step(&mut s, &i, 0);
    press(&mut i, Control::R1, true);
    step(&mut s, &i, 10);
    press(&mut i, Control::R1, false);
    step(&mut s, &i, 50);
    press(&mut i, Control::L1, true);
    step(&mut s, &i, 60);
    assert_eq!(s.timer_owner(&p), Some(1));
    step(&mut s, &i, 210);
    assert_eq!(s.timer_owner(&p), Some(1));
    s.select_mode(Mode::Steering);
    assert_eq!(s.timer_owner(&p), Some(2));
}

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
