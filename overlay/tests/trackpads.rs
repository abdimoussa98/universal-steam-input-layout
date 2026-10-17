use keybind_overlay::{BUNDLED_PROFILE, core::*};
#[cfg(target_arch = "wasm32")]
use wasm_bindgen_test::wasm_bindgen_test;
#[cfg(target_arch = "wasm32")]
wasm_bindgen_test::wasm_bindgen_test_configure!(run_in_browser);

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn middle_wins_overlap_in_every_direction() {
    for [x, y] in [
        [0.5, 0.0],
        [-0.5, 0.0],
        [0.0, -0.5],
        [0.0, 0.5],
        [0.35, 0.35],
    ] {
        assert_eq!(preview_pad_zone(x, y), PadZone::Overlap);
    }
    assert_eq!(preview_pad_zone(0.0, 0.0), PadZone::Inner);
    assert_eq!(preview_pad_zone(0.0, -0.9), PadZone::Outer(0));
    assert_eq!(preview_pad_zone(0.9, 0.0), PadZone::Outer(1));
    assert_eq!(preview_pad_zone(0.0, 0.9), PadZone::Outer(2));
    assert_eq!(preview_pad_zone(-0.9, 0.0), PadZone::Outer(3));
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn pad_reference_follows_menu_hold_and_release_window_blocks() {
    let p = Profile::parse(BUNDLED_PROFILE).unwrap();
    let mut s = State::default();
    let mut input = InputFrame::default();
    s.sample_input("pad", input.clone(), &p, 0);
    assert!(
        s.control_page(&p).unwrap().trackpads.as_ref().unwrap()[1]
            .double_tap
            .is_some()
    );
    input.buttons[Control::Select as usize] = true;
    s.sample_input("pad", input.clone(), &p, 10);
    s.sample_input("pad", input.clone(), &p, 250);
    for pad in s.control_page(&p).unwrap().trackpads.as_ref().unwrap() {
        assert_eq!(pad.center, Binding::Unbound);
        assert!(pad.regions.is_none());
        assert!(pad.double_tap.is_none());
    }
    input.buttons[Control::Select as usize] = false;
    s.sample_input("pad", input.clone(), &p, 260);
    input.buttons[Control::L1 as usize] = true;
    s.sample_input("pad", input.clone(), &p, 270);
    input.buttons[Control::L1 as usize] = false;
    s.sample_input("pad", input.clone(), &p, 300);
    assert!(
        s.control_page(&p).unwrap().trackpads.as_ref().unwrap()[0]
            .regions
            .is_none()
    );
    s.sample_input("pad", input, &p, 460);
    assert!(
        s.control_page(&p).unwrap().trackpads.as_ref().unwrap()[0]
            .regions
            .is_some()
    );
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn optional_pad_data_is_backward_compatible_but_invalid_geometry_is_rejected() {
    let mut json: serde_json::Value = serde_json::from_str(BUNDLED_PROFILE).unwrap();
    json["dashboard"]["pages"][0]["trackpads"][0]["regions"]["outer_threshold"] = 30000.into();
    assert!(Profile::parse(&json.to_string()).is_err());
    for page in json["dashboard"]["pages"].as_array_mut().unwrap() {
        page.as_object_mut().unwrap().remove("trackpads");
    }
    assert!(Profile::parse(&json.to_string()).is_ok());
}
