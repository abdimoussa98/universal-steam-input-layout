use super::{Engine, Input, Layout, Session};
fn engine() -> Engine {
    Engine::new(Layout::catalog().unwrap()[0].clone())
}
fn pad(e: &mut Engine, position: [f64; 2], touching: bool, click: bool) {
    e.input(&Input::Surface {
        source: "right_trackpad".into(),
        position,
        touching,
        click,
    });
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn circular_motion_executes_both_directions_and_resets_on_lift() {
    let mut e = engine();
    pad(&mut e, [0., 0.], true, false);
    e.advance_to(60);
    pad(&mut e, [0., 0.], false, false);
    e.advance_to(110);
    pad(&mut e, [0., -0.9], true, false);
    assert!(
        e.stack_titles().contains(&"RTP: Circular Scroll"),
        "{}",
        e.snapshot()
    );
    for angle in [-60_f64, -30., 0., 30., 60.] {
        pad(
            &mut e,
            [
                angle.to_radians().cos() * 0.9,
                angle.to_radians().sin() * 0.9,
            ],
            true,
            false,
        );
    }
    let forward = e.output.wheel;
    assert!(forward > 0, "{}", e.snapshot());
    for angle in [30_f64, 0., -30., -60., -90.] {
        pad(
            &mut e,
            [
                angle.to_radians().cos() * 0.9,
                angle.to_radians().sin() * 0.9,
            ],
            true,
            false,
        );
    }
    assert!(e.output.wheel < forward);
    pad(&mut e, [0., -0.9], false, false);
    e.advance_to(500);
    assert_eq!(e.stack_titles(), ["Base"]);
    assert!(e.output.down.is_empty());
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn pad_click_arbitrates_center_overlap_and_outer_from_layout() {
    for (radius, expected) in [
        (0., "RTP: Middle Click"),
        (0.735, "RTP: Middle Click"),
        (0.9, "RTP: Mouse Buttons"),
    ] {
        let mut e = engine();
        pad(&mut e, [radius, 0.], true, true);
        e.advance_to(100);
        assert!(
            e.stack_titles().contains(&expected),
            "{radius}: {}",
            e.snapshot()
        );
        pad(&mut e, [radius, 0.], false, false);
        e.advance_to(500);
        assert!(e.output.down.is_empty(), "{}", e.snapshot());
    }
}
fn cursor(e: &mut Engine) {
    for (control, down) in [
        ("switch/button_menu", true),
        ("right_joystick/click", true),
        ("right_joystick/click", false),
        ("switch/button_menu", false),
        ("right_joystick/touch", true),
    ] {
        e.input(&Input::Button {
            control: control.into(),
            down,
        });
    }
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn gyro_accumulates_emits_rearms_and_does_not_replay_gated_motion() {
    let mut e = engine();
    e.motion([0., 30., 0.], 16);
    assert_eq!(e.output.pointer, [0.; 2]);
    cursor(&mut e);
    assert_eq!(e.gyro_status()["active"], true);
    e.motion([0., 0.001, 0.], 16);
    assert_eq!(e.output.pointer, [0.; 2]);
    assert!(e.gyro.pending[0] > 0.);
    e.motion([0., 1., 0.], 16);
    assert!(e.output.pointer[0] > 0.);
    assert_eq!(e.gyro.ticks, 1);
    let before = e.output.pointer;
    e.input(&Input::Recenter);
    assert_eq!(before, e.output.pointer);
    assert_eq!(e.gyro.pending, [0.; 2]);
    e.motion([0.; 3], 16);
    assert_eq!(e.gyro.ticks, 1);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn replay_and_slowdown_keep_identical_logical_events() {
    let layout = Layout::catalog().unwrap()[0].clone();
    let mut a = Session::new(layout.clone());
    let mut b = Session::new(layout);
    b.scale = 10;
    a.tick(0.);
    b.tick(0.);
    for (time, control, down) in [
        (10., "switch/button_menu", true),
        (70., "right_joystick/click", true),
        (130., "right_joystick/click", false),
        (190., "switch/button_menu", false),
    ] {
        a.tick(time);
        b.tick(time * 10.);
        let input = Input::Button {
            control: control.into(),
            down,
        };
        a.input(input.clone());
        b.input(input);
    }
    assert_eq!(a.engine.snapshot(), b.engine.snapshot());
    let expected = a.engine.snapshot();
    a.replay();
    a.tick(0.);
    a.tick(190.);
    assert_eq!(a.engine.snapshot(), expected);
}
