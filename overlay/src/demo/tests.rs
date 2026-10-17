use super::{Engine, Input, Layout};

fn engine() -> Engine {
    Engine::new(Layout::catalog().unwrap()[0].clone())
}
fn button(e: &mut Engine, control: &str, down: bool) {
    e.input(&Input::Button {
        control: control.into(),
        down,
    });
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn real_right_pad_window_and_scroll_bindings() {
    let mut e = engine();
    button(&mut e, "right_trackpad/touch", true);
    e.advance_to(60);
    button(&mut e, "right_trackpad/touch", false);
    assert!(e.stack_titles().contains(&"RTP: Double Tap"));
    e.advance_to(110);
    button(&mut e, "right_trackpad/touch", true);
    button(&mut e, "right_trackpad/dpad_north", true);
    assert!(
        e.stack_titles().contains(&"RTP: Circular Scroll"),
        "{}",
        e.snapshot()
    );
    button(&mut e, "right_trackpad/scroll_clockwise", true);
    button(&mut e, "right_trackpad/scroll_clockwise", false);
    assert_eq!(e.output.wheel, 1);
    button(&mut e, "right_trackpad/scroll_counterclockwise", true);
    button(&mut e, "right_trackpad/scroll_counterclockwise", false);
    assert_eq!(e.output.wheel, 0);
    button(&mut e, "right_trackpad/touch", false);
    e.advance_to(500);
    assert_eq!(e.stack_titles(), ["Base"]);
    assert!(e.error.is_none());
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn stateful_cursor_is_reached_by_menu_and_click_release() {
    let mut e = engine();
    button(&mut e, "switch/button_menu", true);
    e.advance_to(60);
    button(&mut e, "right_joystick/click", true);
    e.advance_to(120);
    button(&mut e, "right_joystick/click", false);
    button(&mut e, "switch/button_menu", false);
    assert_eq!(e.mode(), "Cursor Gyro", "{}", e.snapshot());
    assert_eq!(e.gyro_status()["threshold"], 5.);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn all_catalogs_start_without_outputs_or_errors() {
    for layout in Layout::catalog().unwrap() {
        let mut e = Engine::new(layout);
        e.advance_to(1000);
        assert!(e.error.is_none(), "{}", e.snapshot());
        assert!(e.output.down.is_empty(), "{}", e.snapshot());
    }
}
