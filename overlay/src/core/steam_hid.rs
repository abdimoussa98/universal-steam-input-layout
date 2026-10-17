//! Steam Controller 2 (Triton/Ibex) and Steam Deck HID input.
//!
//! Wire layout and button assignments follow SDL 3.4.18's
//! src/joystick/hidapi/SDL_hidapi_steam_triton.c, SDL_hidapi_steamdeck.c,
//! and steam/controller_structs.h.
//! This is an independent decoder, not an SDL driver. WebHID has already
//! separated the report ID from the payload before this function is called.
use super::{Control, InputChange, InputFrame, PadContact};
mod motion;

pub fn decode_report(id: u8, bytes: &[u8]) -> Result<Option<InputFrame>, &'static str> {
    if id == 0 {
        return decode_deck(bytes);
    }
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
    motion::triton(&mut frame, id, bytes, buttons);
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
        frame.pad_clicks[side] = Some(buttons & [0x04000000, 0x00400000][side] != 0);
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

fn decode_deck(bytes: &[u8]) -> Result<Option<InputFrame>, &'static str> {
    // Deck uses an unnumbered 64-byte report. The version/type/length header
    // remains in the payload, unlike Triton's separate WebHID report ID.
    if !bytes.starts_with(&[1, 0, 9]) {
        return Ok(None);
    }
    if bytes.len() != 64 || bytes[3] != 64 {
        return Err("Incomplete or invalid Steam Deck input report");
    }
    let buttons = u32::from_le_bytes(bytes[8..12].try_into().unwrap());
    let touches = u32::from_le_bytes(bytes[12..16].try_into().unwrap());
    let mut frame = InputFrame::default();
    motion::deck(&mut frame, bytes, buttons, touches);
    for (control, mask) in [
        (Control::A, 0x80),
        (Control::B, 0x20),
        (Control::X, 0x40),
        (Control::Y, 0x10),
        (Control::Select, 0x1000),
        (Control::Start, 0x4000),
        (Control::Up, 0x100),
        (Control::Right, 0x200),
        (Control::Down, 0x800),
        (Control::Left, 0x400),
        (Control::L3, 0x400000),
        (Control::R3, 0x04000000),
        (Control::L1, 0x8),
        (Control::R1, 0x4),
    ] {
        frame.buttons[control as usize] = buttons & mask != 0;
    }
    let axis = |offset, invert: bool| {
        let raw = i32::from(i16::from_le_bytes([bytes[offset], bytes[offset + 1]]));
        (raw * if invert { -1000 } else { 1000 } / 32767).clamp(-1000, 1000) as i16
    };
    for side in 0..2 {
        let offset = 44 + side * 2;
        let trigger = u32::from(u16::from_le_bytes([bytes[offset], bytes[offset + 1]]));
        InputChange::Trigger(side, (trigger * 1000 / 32767).min(1000) as u16).apply(&mut frame);
        InputChange::StickAxis(side, 0, axis(48 + side * 4, false)).apply(&mut frame);
        InputChange::StickAxis(side, 1, axis(50 + side * 4, true)).apply(&mut frame);
        frame.touches[side] = Some(touches & [0x4000, 0x8000][side] != 0);
        let touching = buttons & [0x80000, 0x100000][side] != 0;
        frame.pad_clicks[side] = Some(buttons & [0x20000, 0x40000][side] != 0);
        // Steam/SDL can set the firmware click threshold to 0xffff, suppressing
        // the digital bits. Preserve force for the viewer's local click preview.
        let offset = 56 + side * 2;
        let force = u32::from(u16::from_le_bytes([bytes[offset], bytes[offset + 1]]));
        frame.pad_pressures[side] = Some((force * 1000 / 32767).min(1000) as u16);
        frame.pads[side] = Some(PadContact {
            touching,
            position: [axis(16 + side * 4, false), axis(18 + side * 4, true)],
        });
        frame.pad_active |= touching;
    }
    Ok(Some(frame))
}
