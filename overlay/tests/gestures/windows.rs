use super::*;

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
