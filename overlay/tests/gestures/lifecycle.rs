use super::*;

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

#[test]
fn slow_motion_scales_hold_window_output_and_second_hold_together() {
    let p = profile();
    for scale in [1, 2, 5, 10] {
        let mut s = State::default();
        s.set_timing_scale(scale);
        let t = |time| time * u64::from(scale);
        let mut input = InputFrame::default();
        s.sample_input("pad", input.clone(), &p, t(0));
        input.buttons[Control::L1 as usize] = true;
        s.sample_input("pad", input.clone(), &p, t(10));
        s.sample_input("pad", input.clone(), &p, t(209));
        assert_eq!(s.gestures.lanes[0].phase, Phase::Pressed);
        s.sample_input("pad", input.clone(), &p, t(210));
        assert_eq!(s.gestures.lanes[0].phase, Phase::Hold);
        input.buttons[Control::L1 as usize] = false;
        s.sample_input("pad", input.clone(), &p, t(220));
        assert_eq!(s.gestures.lanes[0].phase, Phase::Idle);
        input.buttons[Control::L1 as usize] = true;
        s.sample_input("pad", input.clone(), &p, t(300));
        input.buttons[Control::L1 as usize] = false;
        s.sample_input("pad", input.clone(), &p, t(350));
        assert_eq!(s.gestures.lanes[0].phase, Phase::Window);
        s.sample_input("pad", input.clone(), &p, t(399));
        assert!(!s.gestures.lanes[0].output_seen);
        s.sample_input("pad", input.clone(), &p, t(400));
        assert!(s.gestures.lanes[0].output_seen);
        input.buttons[Control::L1 as usize] = true;
        s.sample_input("pad", input.clone(), &p, t(450));
        assert_eq!(s.gestures.lanes[0].phase, Phase::Second);
        s.sample_input("pad", input.clone(), &p, t(599));
        assert_eq!(s.gestures.lanes[0].phase, Phase::Second);
        s.sample_input("pad", input.clone(), &p, t(600));
        assert_eq!(s.gestures.lanes[0].phase, Phase::Cover);
        assert_eq!(
            p.dashboard
                .as_ref()
                .unwrap()
                .recipe(Mode::Base, Control::L1)
                .unwrap()
                .hold_ms,
            200
        );
    }
}

#[test]
fn changing_preview_speed_requires_release_and_never_finishes_a_pending_gesture() {
    let p = profile();
    let mut s = State::default();
    let mut input = InputFrame::default();
    s.sample_input("pad", input.clone(), &p, 1000);
    input.buttons[Control::Select as usize] = true;
    s.sample_input("pad", input.clone(), &p, 1010);
    s.set_timing_scale(10);
    s.sample_input("pad", input.clone(), &p, 1100);
    assert_eq!(s.gestures.lanes[2].phase, Phase::Unknown);
    assert!(s.gestures.lanes[2].deadline_ms.is_none());
    input.buttons[Control::Select as usize] = false;
    s.sample_input("pad", input.clone(), &p, 1200);
    input.buttons[Control::Select as usize] = true;
    s.sample_input("pad", input.clone(), &p, 1300);
    s.sample_input("pad", input.clone(), &p, 3290);
    assert_eq!(s.gestures.lanes[2].phase, Phase::Pressed);
    s.sample_input("pad", input.clone(), &p, 3300);
    assert_eq!(s.gestures.lanes[2].phase, Phase::Hold);
    s.set_timing_scale(1);
    s.sample_input("pad", input, &p, 3400);
    assert_eq!(s.gestures.lanes[2].phase, Phase::Unknown);
    s.unavailable(InputStatus::Disconnected);
    assert_eq!(s.timing_scale(), 1);
    assert!(!s.gestures.animating());
}
