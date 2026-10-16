//! Shared physical input adapter. Construct and poll on the process main thread.
use crate::core::*;
use sdl3::{
    event::Event,
    gamepad::{Axis, Button, Gamepad},
};
use std::{
    collections::BTreeMap,
    time::{Duration, Instant},
};

pub struct Sample {
    pub devices: Vec<Device>,
    pub events: Vec<InputEvent>,
    pub now_ms: u64,
    pub identities: Vec<(String, Option<String>)>,
}

pub struct SdlInput {
    pub quit_requested: bool,
    opened: BTreeMap<sdl3::joystick::JoystickId, Gamepad>,
    pump: sdl3::EventPump,
    gamepads: sdl3::GamepadSubsystem,
    last_scan: Instant,
    _sdl: sdl3::Sdl,
}
impl SdlInput {
    pub fn new() -> Result<Self, String> {
        if !sdl3::hint::set("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1") {
            return Err("Could not enable SDL background controller input".into());
        }
        if !sdl3::hint::set("SDL_JOYSTICK_HIDAPI_STEAM", "1") {
            return Err("Could not enable SDL's direct Steam Controller driver".into());
        }
        let sdl = sdl3::init().map_err(|e| e.to_string())?;
        let gamepads = sdl.gamepad().map_err(|e| e.to_string())?;
        let pump = sdl.event_pump().map_err(|e| e.to_string())?;
        Ok(Self {
            quit_requested: false,
            opened: BTreeMap::new(),
            pump,
            gamepads,
            last_scan: Instant::now() - Duration::from_secs(2),
            _sdl: sdl,
        })
    }
    pub fn poll(&mut self) -> Result<Sample, String> {
        let mut events = Vec::new();
        for event in self.pump.poll_iter() {
            let item = match event {
                Event::Quit { .. } => {
                    self.quit_requested = true;
                    None
                }
                Event::GamepadButtonDown {
                    timestamp,
                    which,
                    button,
                } => {
                    button_control(button).map(|c| (which, timestamp, InputChange::Button(c, true)))
                }
                Event::GamepadButtonUp {
                    timestamp,
                    which,
                    button,
                } => button_control(button)
                    .map(|c| (which, timestamp, InputChange::Button(c, false))),
                Event::GamepadAxisMotion {
                    timestamp,
                    which,
                    axis,
                    value,
                } => match axis {
                    Axis::TriggerLeft => {
                        Some((which, timestamp, InputChange::Trigger(0, trigger(value))))
                    }
                    Axis::TriggerRight => {
                        Some((which, timestamp, InputChange::Trigger(1, trigger(value))))
                    }
                    Axis::LeftX => Some((
                        which,
                        timestamp,
                        InputChange::StickAxis(0, 0, stick_axis(value)),
                    )),
                    Axis::LeftY => Some((
                        which,
                        timestamp,
                        InputChange::StickAxis(0, 1, stick_axis(value)),
                    )),
                    Axis::RightX => Some((
                        which,
                        timestamp,
                        InputChange::StickAxis(1, 0, stick_axis(value)),
                    )),
                    Axis::RightY => Some((
                        which,
                        timestamp,
                        InputChange::StickAxis(1, 1, stick_axis(value)),
                    )),
                },
                Event::JoyButtonDown {
                    timestamp,
                    which,
                    button_idx,
                }
                | Event::JoyButtonUp {
                    timestamp,
                    which,
                    button_idx,
                } if matches!(button_idx, 18 | 19)
                    && self.opened.get(&which).is_some_and(is_triton) =>
                {
                    Some((
                        which,
                        timestamp,
                        InputChange::Touch(
                            if button_idx == 19 { 0 } else { 1 },
                            matches!(event, Event::JoyButtonDown { .. }),
                        ),
                    ))
                }
                _ => None,
            };
            if let Some((which, timestamp, change)) = item {
                events.push(InputEvent {
                    device: which.raw().to_string(),
                    at_ms: timestamp / 1_000_000,
                    change,
                });
            }
        }
        if self.last_scan.elapsed() >= Duration::from_secs(1) {
            self.opened.retain(|_, p| p.connected());
            for id in self.gamepads.gamepads().map_err(|e| e.to_string())? {
                if let std::collections::btree_map::Entry::Vacant(entry) = self.opened.entry(id) {
                    entry.insert(
                        self.gamepads
                            .open(id)
                            .map_err(|e| format!("Cannot open SDL device {}: {e}", id.raw()))?,
                    );
                }
            }
            self.last_scan = Instant::now();
        }
        let mut devices = Vec::new();
        let mut identities = Vec::new();
        for (id, pad) in self.opened.iter().filter(|(_, p)| p.connected()) {
            let id = id.raw().to_string();
            identities.push((
                id.clone(),
                physical_device_identity(
                    pad.vendor_id(),
                    pad.product_id(),
                    pad.serial_number().as_deref(),
                    pad.path().as_deref(),
                ),
            ));
            let input = frame(pad);
            devices.push(Device {
                input,
                id,
                name: format!(
                    "{} · {:?} · {}",
                    pad.name().unwrap_or_default(),
                    pad.real_type(),
                    pad.path().unwrap_or_default()
                ),
                standard: true,
                held: [
                    pad.button(Button::LeftShoulder),
                    pad.button(Button::RightShoulder),
                ],
            });
        }
        events.sort_by_key(|e| e.at_ms);
        Ok(Sample {
            events,
            now_ms: sdl3::timer::ticks(),
            devices,
            identities,
        })
    }
}

fn button_control(b: Button) -> Option<Control> {
    Some(match b {
        Button::South => Control::A,
        Button::East => Control::B,
        Button::West => Control::X,
        Button::North => Control::Y,
        Button::Back => Control::Select,
        Button::Start => Control::Start,
        Button::DPadUp => Control::Up,
        Button::DPadRight => Control::Right,
        Button::DPadDown => Control::Down,
        Button::DPadLeft => Control::Left,
        Button::LeftStick => Control::L3,
        Button::RightStick => Control::R3,
        Button::LeftShoulder => Control::L1,
        Button::RightShoulder => Control::R1,
        _ => return None,
    })
}
fn trigger(value: i16) -> u16 {
    (u32::from(value.max(0) as u16) * 1000 / 32767) as u16
}
fn is_triton(p: &Gamepad) -> bool {
    p.vendor_id() == Some(0x28de)
        && p.product_id()
            .is_some_and(|id| (0x1302..=0x1305).contains(&id))
}
fn frame(p: &Gamepad) -> InputFrame {
    let mut i = InputFrame::default();
    for b in [
        Button::South,
        Button::East,
        Button::West,
        Button::North,
        Button::Back,
        Button::Start,
        Button::DPadUp,
        Button::DPadRight,
        Button::DPadDown,
        Button::DPadLeft,
        Button::LeftStick,
        Button::RightStick,
        Button::LeftShoulder,
        Button::RightShoulder,
    ] {
        if let Some(c) = button_control(b) {
            i.buttons[c as usize] = p.button(b);
        }
    }
    for (n, a) in [Axis::TriggerLeft, Axis::TriggerRight]
        .into_iter()
        .enumerate()
    {
        InputChange::Trigger(n, trigger(p.axis(a))).apply(&mut i);
    }
    i.stick_positions = [
        Some([
            stick_axis(p.axis(Axis::LeftX)),
            stick_axis(p.axis(Axis::LeftY)),
        ]),
        Some([
            stick_axis(p.axis(Axis::RightX)),
            stick_axis(p.axis(Axis::RightY)),
        ]),
    ];
    i.sticks = [
        p.axis(Axis::LeftX).unsigned_abs() > 13276 || p.axis(Axis::LeftY).unsigned_abs() > 13276,
        p.axis(Axis::RightX).unsigned_abs() > 13276 || p.axis(Axis::RightY).unsigned_abs() > 13276,
    ];
    // SDL's pinned Triton HID driver exposes capacitive stick touches as raw
    // joystick buttons 19/18. Never apply this device-specific mapping elsewhere.
    if is_triton(p) {
        unsafe {
            let j = sdl3::sys::gamepad::SDL_GetGamepadJoystick(p.raw());
            if !j.is_null() && sdl3::sys::joystick::SDL_GetNumJoystickButtons(j) >= 20 {
                i.touches = [
                    Some(sdl3::sys::joystick::SDL_GetJoystickButton(j, 19)),
                    Some(sdl3::sys::joystick::SDL_GetJoystickButton(j, 18)),
                ];
            }
        }
    }
    for pad in 0..p.touchpads_count().min(2) {
        unsafe {
            let mut down = false;
            let (mut x, mut y) = (0.0, 0.0);
            if sdl3::sys::gamepad::SDL_GetGamepadTouchpadFinger(
                p.raw(),
                i32::from(pad),
                0,
                &mut down,
                &mut x,
                &mut y,
                std::ptr::null_mut(),
            ) {
                i.pad_active |= down;
                i.pads[pad as usize] = Some(PadContact {
                    touching: down,
                    position: [
                        ((x.clamp(0.0, 1.0) * 2.0 - 1.0) * 1000.0).round() as i16,
                        ((y.clamp(0.0, 1.0) * 2.0 - 1.0) * 1000.0).round() as i16,
                    ],
                });
            }
        }
    }
    i
}

fn stick_axis(value: i16) -> i16 {
    (i32::from(value) * 1000 / 32767).clamp(-1000, 1000) as i16
}
