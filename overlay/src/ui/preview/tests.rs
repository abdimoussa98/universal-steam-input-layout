use super::*;
use crate::core::{HostSettings, InputStatus, Mode, Phase, Preferences};

fn data(scale: u8) -> FrameData {
    FrameData {
        state: State {
            timing_scale: scale,
            ..Default::default()
        },
        profile: Profile::parse(crate::BUNDLED_PROFILE).unwrap(),
        settings: HostSettings::default(),
        preferences: Preferences::default(),
        native: false,
        remote: false,
        recovery_available: false,
        hud: false,
        companion_url: None,
        browser_connection: None,
        error: None,
    }
}

#[test]
fn every_control_is_independent_and_triggers_include_analog_travel() {
    let mut data = data(1);
    data.state.snapshot("physical", [false, true]);
    data.state.input.buttons[Control::R1 as usize] = true;
    let physical = data.state.clone();
    for control in Control::ALL {
        let mut preview = Preview::default();
        preview.set(control, true, &data, 1000);
        let state = preview.update(&data, 1000).unwrap();
        assert_eq!(state.status, InputStatus::Live);
        assert!(state.input.down(control));
        assert_eq!(state.input.buttons.iter().filter(|down| **down).count(), 1);
        assert_eq!(
            state.input.triggers,
            match control {
                Control::L2 => [1000, 0],
                Control::R2 => [0, 1000],
                _ => [0, 0],
            }
        );
        assert_eq!(data.state, physical);
        preview.set(control, false, &data, 1001);
        if let Some(state) = preview.update(&data, 1001) {
            assert!(!state.input.down(control));
            assert_eq!(state.input.triggers, [0, 0]);
        }
        assert!(preview.update(&data, 2000).is_none());
        assert!(!preview.active());
    }
}

#[test]
fn same_frame_tap_starts_window_and_second_press_reaches_cover_at_slow_speed() {
    let data = data(10);
    let mut preview = Preview::default();
    preview.set(Control::L1, true, &data, 1000);
    assert_eq!(
        preview.update(&data, 1000).unwrap().gestures.lanes[0].phase,
        Phase::Pressed
    );
    preview.set(Control::L1, false, &data, 1000);
    assert_eq!(
        preview.update(&data, 1489).unwrap().gestures.lanes[0].phase,
        Phase::Window
    );
    preview.set(Control::L1, true, &data, 1490);
    let state = preview.update(&data, 2989).unwrap();
    assert_eq!(state.gestures.lanes[0].phase, Phase::Second);
    assert!(
        !state
            .gestures
            .history
            .iter()
            .any(|mark| mark.label == "Expected Scroll down")
    );
    assert_eq!(
        preview.update(&data, 2990).unwrap().gestures.lanes[0].phase,
        Phase::Cover
    );
    preview.set(Control::L1, false, &data, 3010);
    assert!(preview.update(&data, 3010).is_none());
}

#[test]
fn slow_motion_applies_once_to_hold_and_release_deadlines() {
    for scale in [1, 5, 10] {
        let data = data(scale);
        let factor = u64::from(scale);
        let mut preview = Preview::default();
        preview.set(Control::R1, true, &data, 1000);
        let hold_at = 1000 + 200 * factor;
        assert_eq!(
            preview.update(&data, hold_at - 1).unwrap().gestures.lanes[1].phase,
            Phase::Pressed
        );
        assert_eq!(
            preview.update(&data, hold_at).unwrap().gestures.lanes[1].phase,
            Phase::Hold
        );
        preview.set(Control::R1, false, &data, hold_at);
        assert!(preview.update(&data, hold_at).is_none());
        preview.set(Control::R1, true, &data, 10_000);
        preview.set(Control::R1, false, &data, 10_000);
        let output_at = 10_000 + 50 * factor;
        let state = preview.update(&data, output_at - 1).unwrap();
        assert!(!state.gestures.lanes[1].output_seen);
        let state = preview.update(&data, output_at).unwrap();
        assert!(state.gestures.lanes[1].output_seen);
        let close_at = 10_000 + 150 * factor;
        assert!(preview.update(&data, close_at - 1).is_some());
        assert!(preview.update(&data, close_at).is_none());
    }
}

#[test]
fn multiple_buttons_use_the_core_modifier_consumption_rules() {
    let data = data(5);
    let mut preview = Preview::default();
    preview.set(Control::L1, true, &data, 0);
    preview.set(Control::A, true, &data, 100);
    let state = preview.update(&data, 100).unwrap();
    assert_eq!(state.held, [true, false]);
    assert!(state.input.down(Control::A));
    assert_eq!(state.gestures.lanes[0].phase, Phase::Consumed);
    preview.set(Control::A, false, &data, 200);
    assert!(preview.update(&data, 200).is_some());
    preview.set(Control::L1, false, &data, 300);
    assert!(preview.update(&data, 300).is_none());
}

#[test]
fn pinned_modifiers_support_combined_chords_and_independent_release() {
    let data = data(5);
    let mut preview = Preview::default();
    preview.set(Control::L1, true, &data, 1000);
    preview.set(Control::R1, true, &data, 1050);
    let state = preview.update(&data, 1050).unwrap();
    assert_eq!(state.held, [true, true]);
    assert!(
        state.gestures.lanes[..2]
            .iter()
            .all(|lane| lane.phase == Phase::Combined)
    );
    preview.set(Control::X, true, &data, 1100);
    let state = preview.update(&data, 1100).unwrap();
    assert_eq!(state.held, [true, true]);
    assert!(state.input.down(Control::X));
    preview.set(Control::X, false, &data, 1150);
    preview.set(Control::L1, false, &data, 1200);
    let state = preview.update(&data, 1200).unwrap();
    assert_eq!(state.held, [false, true]);
    assert_eq!(state.gestures.lanes[0].phase, Phase::Idle);
    assert_eq!(state.gestures.lanes[1].phase, Phase::Consumed);
    preview.set(Control::R1, false, &data, 1250);
    assert!(preview.update(&data, 1250).is_none());
}

#[test]
fn settings_changes_and_cancel_discard_held_input_and_pending_windows() {
    let original = data(1);
    let mut variants = [original.clone(), original.clone(), original.clone()];
    variants[0].state.mode = Mode::Menu;
    variants[1].state.timing_scale = 10;
    // Compare the full profile, including edits that keep the source digest.
    variants[2].profile.glyphs[0] = "South".into();
    for changed in variants {
        for down in [false, true] {
            let mut preview = Preview::default();
            preview.set(Control::L1, true, &original, 1000);
            preview.set(Control::L1, down, &original, 1000);
            assert!(preview.update(&changed, 1001).is_none());
            assert!(!preview.active());
            preview.set(Control::A, false, &changed, 1001);
            assert!(!preview.active());
        }
    }
    let mut preview = Preview::default();
    preview.set(Control::L1, true, &original, 1000);
    preview.cancel();
    assert!(preview.update(&original, 1001).is_none());
    preview.set(Control::L1, true, &original, 1002);
    assert_eq!(
        preview.update(&original, 1002).unwrap().gestures.lanes[0].phase,
        Phase::Pressed
    );
}
