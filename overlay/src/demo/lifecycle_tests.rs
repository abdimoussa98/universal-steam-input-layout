use super::{Engine, Input, Layout, Session};

fn button(engine: &mut Engine, control: &str, down: bool) {
    engine.input(&Input::Button {
        control: control.into(),
        down,
    });
}
fn gamepad() -> Engine {
    let mut e = Engine::new(Layout::catalog().unwrap()[0].clone());
    for (control, down) in [
        ("switch/button_escape", true),
        ("right_joystick/click", true),
        ("right_joystick/click", false),
        ("switch/button_escape", false),
    ] {
        button(&mut e, control, down);
    }
    assert_eq!(e.mode(), "Gamepad");
    e.advance_to(500);
    e.output.events.clear();
    e
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn native_gamepad_single_double_and_long_press_do_not_leak_outputs() {
    let control = "switch/button_escape";
    let mut single = gamepad();
    button(&mut single, control, true);
    single.advance_to(550);
    button(&mut single, control, false);
    single.advance_to(699);
    assert!(
        !single
            .output
            .events
            .iter()
            .any(|e| e.detail == "xinput_button START")
    );
    single.advance_to(700);
    assert!(
        single
            .output
            .events
            .iter()
            .any(|e| e.kind == "tap" && e.detail == "xinput_button START")
    );
    let mut double = gamepad();
    button(&mut double, control, true);
    double.advance_to(550);
    button(&mut double, control, false);
    double.advance_to(600);
    button(&mut double, control, true);
    assert!(double.output.down.contains("xinput_button START"));
    button(&mut double, control, false);
    double.advance_to(900);
    assert!(double.output.down.is_empty());
    let mut long = gamepad();
    button(&mut long, control, true);
    long.advance_to(701);
    button(&mut long, control, false);
    long.advance_to(1000);
    assert!(
        !long
            .output
            .events
            .iter()
            .any(|e| e.detail == "xinput_button START")
    );
    assert!(long.output.down.is_empty());
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn stepping_a_paused_replay_reproduces_motion_and_finishes() {
    let mut s = Session::new(Layout::catalog().unwrap()[0].clone());
    s.tick(0.);
    for (control, down) in [
        ("switch/button_menu", true),
        ("right_joystick/click", true),
        ("right_joystick/click", false),
        ("switch/button_menu", false),
        ("right_joystick/touch", true),
    ] {
        s.input(Input::Button {
            control: control.into(),
            down,
        });
    }
    for time in 1..=10 {
        s.tick(f64::from(time * 20));
        s.input(Input::Motion {
            degrees: [0.01, 0.08, 0.02],
            duration_ms: 20,
        });
    }
    s.input(Input::Button {
        control: "right_joystick/touch".into(),
        down: false,
    });
    s.tick(250.);
    let expected = s.engine.snapshot();
    assert!(expected["gyro"]["motion"]["ticks"].as_u64().unwrap() > 0);
    s.replay();
    s.scale = 10;
    for _ in 0..50 {
        if !s.replaying {
            break;
        }
        s.step();
    }
    assert!(!s.replaying);
    assert_eq!(s.engine.snapshot(), expected);
}
