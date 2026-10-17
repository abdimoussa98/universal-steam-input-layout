use keybind_overlay::core::{Control, InputFrame, steam_hid::decode_report};
#[cfg(target_arch = "wasm32")]
use wasm_bindgen_test::wasm_bindgen_test;
#[cfg(target_arch = "wasm32")]
wasm_bindgen_test::wasm_bindgen_test_configure!(run_in_browser);

// Triton reports from SDL 3.4.18's packed controller_structs.h. WebHID supplies
// reportId separately; the first payload byte is the sequence counter.
fn report(buttons: u32) -> [u8; 45] {
    let mut bytes = [0; 45];
    bytes[0] = 17;
    bytes[1..5].copy_from_slice(&buttons.to_le_bytes());
    bytes
}
fn axis(bytes: &mut [u8], offset: usize, value: i16) {
    bytes[offset..offset + 2].copy_from_slice(&value.to_le_bytes());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn usb_buttons_match_the_existing_native_controller_mapping() {
    for (mask, expected) in [
        (0x1, Control::A),
        (0x2, Control::B),
        (0x4, Control::X),
        (0x8, Control::Y),
        (0x4000, Control::Select),
        (0x40, Control::Start),
        (0x2000, Control::Up),
        (0x800, Control::Right),
        (0x400, Control::Down),
        (0x1000, Control::Left),
        (0x8000, Control::L3),
        (0x20, Control::R3),
        (0x80000, Control::L1),
        (0x200, Control::R1),
    ] {
        let frame = decode_report(0x47, &report(mask)).unwrap().unwrap();
        assert!(frame.down(expected), "{expected:?}");
        assert_eq!(frame.buttons.iter().filter(|b| **b).count(), 1);
    }
    let released = decode_report(0x47, &report(0)).unwrap().unwrap();
    assert_eq!(released.buttons, [false; 16]);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn triggers_sticks_and_capacitive_touches_feed_the_shared_frame() {
    let mut bytes = report(0x01000000);
    axis(&mut bytes, 5, 16384);
    axis(&mut bytes, 7, 32767);
    axis(&mut bytes, 9, -32768);
    axis(&mut bytes, 11, 32767);
    axis(&mut bytes, 13, 32767);
    axis(&mut bytes, 15, -32768);
    let frame = decode_report(0x47, &bytes).unwrap().unwrap();
    assert_eq!(frame.triggers, [500, 1000]);
    assert!(frame.down(Control::L2) && frame.down(Control::R2));
    assert_eq!(
        frame.stick_positions,
        [Some([-1000, -1000]), Some([1000, 1000])]
    );
    assert_eq!(frame.sticks, [true, true]);
    assert_eq!(frame.touches, [Some(true), Some(false)]);
    axis(&mut bytes, 5, -1);
    assert_eq!(decode_report(0x47, &bytes).unwrap().unwrap().triggers[0], 0);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn trackpad_offsets_follow_the_report_version_and_y_points_down() {
    for (id, offset) in [(0x42, 17), (0x45, 17), (0x47, 19)] {
        let mut bytes = report(0x02200000);
        axis(&mut bytes, offset, -16384);
        axis(&mut bytes, offset + 2, 16384);
        axis(&mut bytes, offset + 6, 16384);
        axis(&mut bytes, offset + 8, -16384);
        let frame = decode_report(id, &bytes).unwrap().unwrap();
        assert!(frame.pad_active);
        let left = frame.pads[0].as_ref().unwrap();
        let right = frame.pads[1].as_ref().unwrap();
        assert!(left.touching && right.touching);
        assert_eq!(left.position, [-500, -500]);
        assert_eq!(right.position, [500, 500]);
        let released = decode_report(id, &report(0)).unwrap().unwrap();
        assert!(!released.pad_active);
        assert!(!released.pads[0].as_ref().unwrap().touching);
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn malformed_or_other_hid_reports_cannot_create_controller_input() {
    for id in [0x42, 0x45, 0x47] {
        for length in 0..45 {
            assert!(decode_report(id, &report(u32::MAX)[..length]).is_err());
        }
    }
    for id in [0, 1, 0x43, 0x46, 0x79, 255] {
        assert_eq!(decode_report(id, &report(u32::MAX)), Ok(None));
    }
    let mut bytes = report(0);
    axis(&mut bytes, 9, 32767);
    let first = decode_report(0x47, &bytes).unwrap().unwrap();
    let released = decode_report(0x47, &report(0)).unwrap().unwrap();
    assert_ne!(first, released);
    assert_eq!(released.stick_positions, [Some([0, 0]), Some([0, 0])]);
    assert_eq!(released.triggers, InputFrame::default().triggers);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn pad_click_flags_are_independent_of_contact_and_other_buttons() {
    for id in [0x42, 0x45, 0x47] {
        for (bits, expected) in [
            (0, [false, false]),
            (0x04000000, [true, false]),
            (0x00400000, [false, true]),
            (0x04400000, [true, true]),
        ] {
            let frame = decode_report(id, &report(bits)).unwrap().unwrap();
            assert_eq!(frame.pad_clicks, expected.map(Some));
            assert!(!frame.pad_active);
            assert_eq!(frame.buttons, [false; 16]);
        }
        let touched = decode_report(id, &report(0x02200000)).unwrap().unwrap();
        assert!(touched.pad_active);
        assert_eq!(touched.pad_clicks, [Some(false), Some(false)]);
    }
    let old: InputFrame = serde_json::from_str("{}").unwrap();
    assert_eq!(old.pad_clicks, [None, None]);
}
