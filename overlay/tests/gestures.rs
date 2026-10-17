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

#[path = "gestures/lifecycle.rs"]
mod lifecycle;
#[path = "gestures/modifiers.rs"]
mod modifiers;
#[path = "gestures/steering.rs"]
mod steering;
#[path = "gestures/windows.rs"]
mod windows;
