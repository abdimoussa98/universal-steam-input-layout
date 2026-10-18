use super::*;
use crate::demo::Input;
fn button(e: &mut Engine, control: &str, down: bool) {
    e.input(&Input::Button {
        control: control.into(),
        down,
    });
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn executed_lifecycle_survives_hold_and_tracks_release_windows() {
    for layout in Layout::catalog().unwrap() {
        let control = if layout.variant == "alternative" {
            "left_trigger/edge"
        } else {
            "switch/left_bumper"
        };
        let mut e = Engine::new(layout);
        assert!(e.lifecycle().is_none());

        assert!(e.display_label(control).contains(" :: "));
        button(&mut e, control, true);
        let t = e.lifecycle().expect("initial hold");
        let due = t.deadline.expect("hold deadline");
        e.advance_to(due / 2);
        assert_eq!(e.lifecycle().unwrap().progress(e.now), 0.5);
        assert_eq!(t.remaining(e.now, 10), Some((due - e.now) * 10));
        e.advance_to(due);
        assert_eq!(
            e.lifecycle().unwrap().phase,
            lifecycle::LifecyclePhase::Held
        );
        button(&mut e, control, false);
        assert!(e.lifecycle().is_none());
        e.advance_to(due + 100);
        button(&mut e, control, true);
        e.advance_to(due + 150);
        button(&mut e, control, false);
        let t = e.lifecycle().expect("release window");
        assert_eq!(t.phase, lifecycle::LifecyclePhase::ReleaseWindow);
        assert!(t.output_at.is_some());
        e.advance_to(e.now + 20);
        button(&mut e, control, true);
        assert_eq!(
            e.lifecycle().unwrap().phase,
            lifecycle::LifecyclePhase::SecondHold
        );
        e.advance_to(e.lifecycle().unwrap().deadline.unwrap());
        assert_eq!(
            e.lifecycle().unwrap().phase,
            lifecycle::LifecyclePhase::Covered
        );
        button(&mut e, control, false);
        assert!(e.lifecycle().is_none());
    }
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn labels_and_pad_regions_come_from_the_selected_layout() {
    let e = Engine::new(Layout::catalog().unwrap()[0].clone());
    assert_eq!(e.display_label("button_diamond/button_a"), "F");
    let pad: PadView = e.pad_view("right_trackpad", true);
    assert_eq!(pad.center, "Middle click");
    assert_eq!(
        pad.directions,
        ["Scroll up", "Forward", "Scroll down", "Back"]
    );
    assert!(pad.inner > pad.outer);
    let pad = e.pad_view("left_trackpad", false);
    assert_eq!(pad.mode, "2dscroll");
    assert_eq!(pad.directions, ["Tab", "Enter", "Backspace", "Escape"]);
    assert_eq!(pad.center, "Swipe");
    assert!(!pad.circular);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn output_does_not_steal_window_and_combined_gesture_has_both_owners() {
    let mut e = Engine::new(Layout::catalog().unwrap()[0].clone());
    button(&mut e, "button_diamond/button_a", true);
    assert!(e.lifecycle().is_none());
    button(&mut e, "button_diamond/button_a", false);
    button(&mut e, "switch/left_bumper", true);
    e.advance_to(50);
    button(&mut e, "switch/left_bumper", false);
    button(&mut e, "switch/right_bumper", true);
    assert_eq!(e.lifecycle().unwrap().owners, ["switch/left_bumper"]);
    e.advance_to(200);
    assert!(
        e.lifecycle()
            .is_none_or(|t| t.owners != ["switch/left_bumper"])
    );
    let mut e = Engine::new(Layout::catalog().unwrap()[0].clone());
    button(&mut e, "switch/left_bumper", true);
    button(&mut e, "switch/right_bumper", true);
    let t = e.lifecycle().unwrap();
    assert_eq!(t.owners, ["switch/left_bumper", "switch/right_bumper"]);
    e.advance_to(t.deadline.unwrap());
    assert!(e.lifecycle().is_some());
    button(&mut e, "switch/left_bumper", false);
    button(&mut e, "switch/right_bumper", false);
    assert!(e.lifecycle().is_none());
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn pad_scroll_lifecycle_uses_touch_owner_and_clears_on_lift() {
    let mut e = Engine::new(Layout::catalog().unwrap()[0].clone());
    let pad = |touching, position| Input::Surface {
        source: "right_trackpad".into(),
        position,
        touching,
        click: false,
    };
    e.input(&pad(true, [0., 0.]));
    assert_eq!(e.lifecycle().unwrap().owners, ["right_trackpad/touch"]);
    e.advance_to(60);
    e.input(&pad(false, [0., 0.]));
    assert_eq!(
        e.lifecycle().unwrap().phase,
        lifecycle::LifecyclePhase::ReleaseWindow
    );
    e.advance_to(110);
    e.input(&pad(true, [0., -0.9]));
    assert!(e.stack_titles().contains(&"RTP: Circular Scroll"));
    assert!(e.lifecycle().is_some());
    e.input(&pad(false, [0., -0.9]));
    assert!(e.lifecycle().is_none());
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn pause_step_and_reset_use_the_same_lifecycle_clock() {
    let mut s = crate::demo::Session::new(Layout::catalog().unwrap()[0].clone());
    s.scale = 10;
    s.tick(0.);
    s.input(Input::Button {
        control: "switch/left_bumper".into(),
        down: true,
    });
    s.tick(1000.);
    let t = s.engine.lifecycle().unwrap();
    assert_eq!(t.progress(s.engine.now), 0.5);
    s.paused = true;
    s.tick(9000.);
    assert_eq!(t.progress(s.engine.now), 0.5);
    s.step();
    assert_eq!(
        s.engine.lifecycle().unwrap().phase,
        lifecycle::LifecyclePhase::Held
    );
    s.reset();
    assert!(s.engine.lifecycle().is_none());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn steering_lifecycle_follows_the_stick_and_cancels_with_its_driver() {
    let mut e = Engine::new(Layout::catalog().unwrap()[0].clone());
    for (c, down) in [
        ("switch/button_escape", true),
        ("joystick/click", true),
        ("joystick/click", false),
        ("switch/button_escape", false),
    ] {
        button(&mut e, c, down);
    }
    assert_eq!(e.mode(), "Steering");
    button(&mut e, "switch/right_bumper", true);
    e.input(&Input::Surface {
        source: "joystick".into(),
        position: [0., -1.],
        touching: false,
        click: false,
    });
    let t = e.lifecycle().expect("stick gesture has a lifecycle");
    assert!(t.summary.contains(" :: "));
    assert!(t.deadline.is_some());
    e.advance_to(t.deadline.unwrap());
    assert!(e.lifecycle().is_some());
    button(&mut e, "switch/right_bumper", false);
    assert!(e.lifecycle().is_none());
}
