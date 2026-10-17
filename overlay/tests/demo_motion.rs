use keybind_overlay::core::steam_hid::decode_report;
#[cfg(target_arch = "wasm32")]
wasm_bindgen_test::wasm_bindgen_test_configure!(run_in_browser);

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn triton_imu_axes_scale_time_and_grips_match_the_pinned_protocol() {
    let mut bytes = [0_u8; 45];
    bytes[1..5].copy_from_slice(&0x60080_u32.to_le_bytes());
    bytes[31..33].copy_from_slice(&65535_u16.to_le_bytes());
    bytes[39..41].copy_from_slice(&32767_i16.to_le_bytes());
    bytes[41..43].copy_from_slice(&16384_i16.to_le_bytes());
    bytes[43..45].copy_from_slice(&(-16384_i16).to_le_bytes());
    let frame = decode_report(0x47, &bytes).unwrap().unwrap();
    let motion = frame.motion.unwrap();
    assert_eq!(motion.rate, [1_999_938, -1_000_000, -1_000_000]);
    assert_eq!(
        (motion.timestamp, motion.tick_us, motion.modulus),
        (65535, 32, 65536)
    );
    assert_eq!(
        frame.back_buttons,
        [Some(true), Some(true), Some(true), Some(false)]
    );
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn deck_imu_and_paddle_fields_are_independent_of_touch_bits() {
    let mut bytes = [0_u8; 64];
    bytes[..4].copy_from_slice(&[1, 0, 9, 64]);
    bytes[4..8].copy_from_slice(&123_u32.to_le_bytes());
    bytes[8..12].copy_from_slice(&0x18000_u32.to_le_bytes());
    bytes[12..16].copy_from_slice(&0x600_u32.to_le_bytes());
    bytes[34..36].copy_from_slice(&16384_i16.to_le_bytes());
    let frame = decode_report(0, &bytes).unwrap().unwrap();
    assert_eq!(frame.back_buttons, [Some(true); 4]);
    assert_eq!(frame.touches, [Some(false); 2]);
    let motion = frame.motion.unwrap();
    assert_eq!(motion.rate, [0, 1_000_000, 0]);
    assert_eq!(motion.tick_us, 4000);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn motion_clock_wraps_and_rejects_stalls_or_changed_clock_domains() {
    use keybind_overlay::core::MotionSample;
    let previous = MotionSample {
        rate: [0; 3],
        timestamp: 65530,
        tick_us: 32,
        modulus: 65536,
    };
    let mut next = previous.clone();
    next.timestamp = 100;
    assert_eq!(next.elapsed_ms(&previous), Some(3));
    next.timestamp = 10000;
    assert_eq!(next.elapsed_ms(&previous), None);
    next.modulus = 0;
    assert_eq!(next.elapsed_ms(&previous), None);
    next.modulus = 1_u64 << 32;
    assert_eq!(next.elapsed_ms(&previous), None);
}
