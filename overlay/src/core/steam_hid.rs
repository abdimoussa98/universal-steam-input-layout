//! Steam Controller 2 (Triton/Ibex) HID input, shared by native/WASM tests.
//!
//! Wire layout and button assignments follow SDL 3.4.18's
//! src/joystick/hidapi/SDL_hidapi_steam_triton.c and steam/controller_structs.h.
//! This is an independent decoder, not an SDL driver. WebHID has already
//! separated the report ID from the payload before this function is called.
use super::{Control, InputChange, InputFrame, PadContact};

pub fn decode_report(id: u8, bytes: &[u8]) -> Result<Option<InputFrame>, &'static str> {
    let pad_offset = match id {
        0x42 | 0x45 => 17,
        0x47 => 19,
        _ => return Ok(None), // Battery and wireless status aren't input frames.
    };
    if bytes.len() < 45 {
        return Err("Incomplete Steam Controller input report");
    }
    let buttons = u32::from_le_bytes(bytes[1..5].try_into().unwrap());
    let mut frame = InputFrame::default();
    for (control, mask) in [
        (Control::A, 0x1),
        (Control::B, 0x2),
        (Control::X, 0x4),
        (Control::Y, 0x8),
        (Control::Select, 0x4000),
        (Control::Start, 0x40),
        (Control::Up, 0x2000),
        (Control::Right, 0x800),
        (Control::Down, 0x400),
        (Control::Left, 0x1000),
        (Control::L3, 0x8000),
        (Control::R3, 0x20),
        (Control::L1, 0x80000),
        (Control::R1, 0x200),
    ] {
        frame.buttons[control as usize] = buttons & mask != 0;
    }
    let read = |offset| i32::from(i16::from_le_bytes([bytes[offset], bytes[offset + 1]]));
    let axis = |offset, invert: bool| {
        let raw = read(offset) * if invert { -1 } else { 1 };
        (raw * 1000 / 32767).clamp(-1000, 1000) as i16
    };
    for side in 0..2 {
        let trigger = (read(5 + side * 2).max(0) * 1000 / 32767) as u16;
        InputChange::Trigger(side, trigger).apply(&mut frame);
        InputChange::StickAxis(side, 0, axis(9 + side * 4, false)).apply(&mut frame);
        InputChange::StickAxis(side, 1, axis(11 + side * 4, true)).apply(&mut frame);
        frame.touches[side] = Some(buttons & [0x01000000, 0x00100000][side] != 0);
        let touching = buttons & [0x02000000, 0x00200000][side] != 0;
        frame.pads[side] = Some(PadContact {
            touching,
            position: [
                axis(pad_offset + side * 6, false),
                axis(pad_offset + side * 6 + 2, true),
            ],
        });
        frame.pad_active |= touching;
    }
    Ok(Some(frame))
}
