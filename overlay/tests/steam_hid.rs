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

// Unnumbered Deck reports retain the packed Valve header in the payload.
fn deck_report(buttons: u32, touches: u32) -> [u8; 64] {
    let mut bytes = [0; 64];
    bytes[..4].copy_from_slice(&[1, 0, 9, 64]);
    bytes[8..12].copy_from_slice(&buttons.to_le_bytes());
    bytes[12..16].copy_from_slice(&touches.to_le_bytes());
    bytes
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn deck_buttons_use_neptune_masks_not_triton_masks() {
    for (mask, expected) in [
        (0x80, Control::A),
        (0x20, Control::B),
        (0x40, Control::X),
        (0x10, Control::Y),
        (0x1000, Control::Select),
        (0x4000, Control::Start),
        (0x100, Control::Up),
        (0x200, Control::Right),
        (0x800, Control::Down),
        (0x400, Control::Left),
        (0x400000, Control::L3),
        (0x04000000, Control::R3),
        (0x8, Control::L1),
        (0x4, Control::R1),
    ] {
        let frame = decode_report(0, &deck_report(mask, 0)).unwrap().unwrap();
        assert!(frame.down(expected), "{expected:?}");
        assert_eq!(frame.buttons.iter().filter(|b| **b).count(), 1);
    }
    // Grips, Steam and Quick Access must not light unrelated controls/touches.
    let other = decode_report(0, &deck_report(0x1a000, 0x40600))
        .unwrap()
        .unwrap();
    assert_eq!(other.buttons, [false; 16]);
    assert_eq!(other.touches, [Some(false); 2]);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn deck_analog_input_preserves_small_motion_and_full_travel() {
    let mut bytes = deck_report(0, 0xc000);
    for (offset, value) in [
        (44, 16384),
        (46, 32767),
        (48, -32768),
        (50, 32767),
        (52, 32767),
        (54, -32768),
    ] {
        axis(&mut bytes, offset, value);
    }
    let frame = decode_report(0, &bytes).unwrap().unwrap();
    assert_eq!(frame.triggers, [500, 1000]);
    assert!(frame.down(Control::L2) && frame.down(Control::R2));
    assert_eq!(
        frame.stick_positions,
        [Some([-1000, -1000]), Some([1000, 1000])]
    );
    assert_eq!(frame.touches, [Some(true); 2]);
    axis(&mut bytes, 48, 3277);
    axis(&mut bytes, 50, -6554);
    // Trigger fields are unsigned; clamp unexpected over-range values.
    axis(&mut bytes, 44, -1);
    let frame = decode_report(0, &bytes).unwrap().unwrap();
    assert_eq!(frame.stick_positions[0], Some([100, 200]));
    assert_eq!(frame.triggers[0], 1000);
    let released = decode_report(0, &deck_report(0, 0)).unwrap().unwrap();
    assert_eq!(released.stick_positions, [Some([0, 0]); 2]);
    assert_eq!(released.triggers, [0; 2]);
    assert_eq!(released.touches, [Some(false); 2]);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn deck_pad_contact_clicks_and_stick_touches_are_independent() {
    for side in 0..2 {
        let mut bytes = deck_report([0x80000, 0x100000][side], [0x4000, 0x8000][side]);
        axis(&mut bytes, 16 + side * 4, -16384);
        axis(&mut bytes, 18 + side * 4, 16384);
        let frame = decode_report(0, &bytes).unwrap().unwrap();
        assert!(frame.pad_active);
        let pad = frame.pads[side].as_ref().unwrap();
        assert!(pad.touching);
        assert_eq!(pad.position, [-500, -500]);
        assert!(!frame.pads[1 - side].as_ref().unwrap().touching);
        assert_eq!(frame.pad_clicks, [Some(false); 2]);
        assert_eq!(frame.touches[side], Some(true));
        assert_eq!(frame.touches[1 - side], Some(false));
        let frame = decode_report(0, &deck_report([0x20000, 0x40000][side], 0))
            .unwrap()
            .unwrap();
        assert_eq!(frame.pad_clicks[side], Some(true));
        assert_eq!(frame.pad_clicks[1 - side], Some(false));
        assert!(!frame.pad_active);
        assert_eq!(frame.buttons, [false; 16]);
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn deck_header_validation_rejects_truncated_input_and_ignores_other_messages() {
    let bytes = deck_report(u32::MAX, u32::MAX);
    for length in 3..64 {
        assert!(decode_report(0, &bytes[..length]).is_err());
    }
    for length in 0..3 {
        assert_eq!(decode_report(0, &bytes[..length]), Ok(None));
    }
    for (offset, value) in [(0, 2), (1, 1), (2, 4)] {
        let mut other = bytes;
        other[offset] = value;
        assert_eq!(decode_report(0, &other), Ok(None));
    }
    let mut invalid = bytes;
    invalid[3] = 63;
    assert!(decode_report(0, &invalid).is_err());
    assert!(decode_report(0, &[bytes.as_slice(), &[0]].concat()).is_err());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn deck_force_previews_clicks_when_firmware_click_bits_are_disabled() {
    for side in 0..2 {
        let mut bytes = deck_report([0x80000, 0x100000][side], 0);
        axis(&mut bytes, 56 + side * 2, 6000);
        let mut frame = decode_report(0, &bytes).unwrap().unwrap();
        assert_eq!(frame.pad_clicks, [Some(false); 2]);
        assert_eq!(frame.pad_pressures[side], Some(183));
        assert!(frame.pad_pressed(side, 150, false));
        assert!(!frame.pad_pressed(1 - side, 150, false));
        assert!(
            !frame.pad_pressed(side, 250, false),
            "preview sensitivity is adjustable"
        );
        frame.pad_pressures[side] = Some(140);
        assert!(
            frame.pad_pressed(side, 150, true),
            "pressure jitter must not flicker"
        );
        assert!(
            !frame.pad_pressed(side, 150, false),
            "light contact isn't a click"
        );
        frame.pad_pressures[side] = Some(119);
        assert!(!frame.pad_pressed(side, 150, true));
        frame.pad_pressures[side] = Some(1000);
        frame.pads[side].as_mut().unwrap().touching = false;
        assert!(
            !frame.pad_pressed(side, 150, true),
            "lifting releases even with residual force"
        );
        axis(&mut bytes, 56 + side * 2, -1);
        assert_eq!(
            decode_report(0, &bytes).unwrap().unwrap().pad_pressures[side],
            Some(1000)
        );
    }
    // Old companion snapshots still deserialize with no pressure support.
    let old: InputFrame = serde_json::from_str("{}").unwrap();
    assert_eq!(old.pad_pressures, [None; 2]);
    assert!(!old.pad_pressed(0, 150, true));
}
