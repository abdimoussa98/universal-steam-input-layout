use super::super::js_error;
use crate::core::{Device, InputChange, InputFrame};
use wasm_bindgen::JsCast;

pub(super) fn devices() -> Result<Vec<Device>, String> {
    let pads = web_sys::window()
        .ok_or("No browser window")?
        .navigator()
        .get_gamepads()
        .map_err(|e| format!("Gamepad API blocked/unavailable: {}", js_error(e)))?;
    let mut devices = vec![];
    for value in pads.iter() {
        if value.is_null() || value.is_undefined() {
            continue;
        }
        let pad: web_sys::Gamepad = value.dyn_into().map_err(js_error)?;
        if pad.connected() {
            devices.push(device(&pad));
        }
    }
    Ok(devices)
}

fn device(pad: &web_sys::Gamepad) -> Device {
    let buttons = pad.buttons();
    let pressed = |i| {
        buttons
            .get(i)
            .dyn_into::<web_sys::GamepadButton>()
            .is_ok_and(|b| b.pressed())
    };
    let mut input = InputFrame::default();
    for (n, index) in [0, 1, 2, 3, 8, 9, 12, 15, 13, 14, 10, 11, 4, 5, 6, 7]
        .into_iter()
        .enumerate()
    {
        input.buttons[n] = pressed(index);
    }
    for n in 0..2 {
        input.triggers[n] = buttons
            .get(6 + n as u32)
            .dyn_into::<web_sys::GamepadButton>()
            .map(|b| (b.value().clamp(0.0, 1.0) * 1000.0).round() as u16)
            .unwrap_or(0);
    }
    sample_sticks(pad, &mut input);
    Device {
        input,
        id: format!("{}:{}", pad.index(), pad.id()),
        name: pad.id(),
        standard: pad.mapping() == web_sys::GamepadMappingType::Standard,
        held: [pressed(4), pressed(5)],
    }
}

fn sample_sticks(pad: &web_sys::Gamepad, input: &mut InputFrame) {
    let axes = pad.axes();
    for n in 0..2 {
        let xy: Option<Vec<f64>> = (0..2)
            .map(|a| {
                axes.get((n * 2 + a) as u32)
                    .as_f64()
                    .filter(|v| v.is_finite())
            })
            .collect();
        if let Some(xy) = xy {
            for (a, v) in xy.into_iter().enumerate() {
                InputChange::StickAxis(n, a, (v.clamp(-1.0, 1.0) * 1000.0).round() as i16)
                    .apply(input);
            }
        }
    }
}
