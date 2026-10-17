//! Protocol axes/scales from the pinned SDL 3.4.18 Steam HID drivers.
use crate::core::{InputFrame, MotionSample};

fn rates(bytes: &[u8], offset: usize) -> [i32; 3] {
    let raw = |i| i32::from(i16::from_le_bytes([bytes[i], bytes[i + 1]]));
    [raw(offset), raw(offset + 4), -raw(offset + 2)]
        .map(|v| (i64::from(v) * 2_000_000 / 32768) as i32)
}
pub(super) fn triton(frame: &mut InputFrame, id: u8, bytes: &[u8], buttons: u32) {
    frame.back_buttons = [0x20000, 0x40000, 0x80, 0x100].map(|mask| Some(buttons & mask != 0));
    let (timestamp, tick_us, modulus) = if id == 0x47 {
        (
            u32::from(u16::from_le_bytes([bytes[31], bytes[32]])),
            32,
            65536,
        )
    } else {
        (
            u32::from_le_bytes(bytes[29..33].try_into().unwrap()),
            1,
            1_u64 << 32,
        )
    };
    frame.motion = Some(MotionSample {
        rate: rates(bytes, 39),
        timestamp,
        tick_us,
        modulus,
    });
}
pub(super) fn deck(frame: &mut InputFrame, bytes: &[u8], buttons: u32, extra: u32) {
    frame.back_buttons = [
        Some(extra & 0x200 != 0),
        Some(buttons & 0x8000 != 0),
        Some(extra & 0x400 != 0),
        Some(buttons & 0x10000 != 0),
    ];
    frame.motion = Some(MotionSample {
        rate: rates(bytes, 30),
        timestamp: u32::from_le_bytes(bytes[4..8].try_into().unwrap()),
        // SDL's Deck driver uses a fixed 4000 us input update period.
        tick_us: 4000,
        modulus: 1_u64 << 32,
    });
}
