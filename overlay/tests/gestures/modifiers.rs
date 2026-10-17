use super::*;

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
fn combined_switch_label_disappears_when_cover_cancels_release() {
    for first in [Control::L1, Control::R1] {
        let mut s = State::default();
        let mut i = InputFrame::default();
        step(&mut s, &i, 0);
        press(&mut i, first, true);
        step(&mut s, &i, 10);
        press(&mut i, Control::L1, true);
        press(&mut i, Control::R1, true);
        step(&mut s, &i, 40);
        assert_eq!(
            &s.control_labels(&profile())[12..14],
            &["Mod 2 :: Base / Gyro", "Mod 2 :: Base / Gyro"]
        );
        step(&mut s, &i, 240);
        assert_eq!(s.gestures.lanes[0].phase, Phase::CombinedCover);
        assert_eq!(&s.control_labels(&profile())[12..14], &["Mod 2", "Mod 2"]);
    }
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
    let legacy = Profile::parse(include_str!("../fixtures/profile.json")).unwrap();
    assert_eq!(
        s.control_labels(&legacy)[Control::L3 as usize],
        "Unavailable"
    );
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn fn_hold_exposes_full_pull_trigger_bindings_and_release_restores_base() {
    for mode in Mode::ALL {
        for owner in [Control::Select, Control::Start] {
            let mut s = State::default();
            s.select_mode(mode);
            let mut i = InputFrame::default();
            step(&mut s, &i, 0);
            let original = s.control_labels(&profile());
            press(&mut i, owner, true);
            step(&mut s, &i, 10);
            step(&mut s, &i, 210);
            let labels = s.control_labels(&profile());
            assert_eq!(labels[Control::L2 as usize], "Full: F12");
            assert_eq!(labels[Control::R2 as usize], "Full: F11");
            press(&mut i, owner, false);
            step(&mut s, &i, 220);
            let labels = s.control_labels(&profile());
            assert_eq!(labels[Control::L2 as usize], original[Control::L2 as usize]);
            assert_eq!(labels[Control::R2 as usize], original[Control::R2 as usize]);
        }
    }
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
