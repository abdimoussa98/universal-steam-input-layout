//! Shared physical input adapter. Construct and poll on the process main thread.
mod decoding;
use crate::core::*;
use decoding::{decode_event, frame};
use sdl3::{
    event::Event,
    gamepad::{Button, Gamepad},
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
            if matches!(event, Event::Quit { .. }) {
                self.quit_requested = true;
            }
            if let Some(event) = decode_event(event, &self.opened) {
                events.push(event);
            }
        }
        self.scan_devices()?;
        let (devices, identities) = self.device_snapshots();
        events.sort_by_key(|e| e.at_ms);
        Ok(Sample {
            events,
            now_ms: sdl3::timer::ticks(),
            devices,
            identities,
        })
    }
    fn scan_devices(&mut self) -> Result<(), String> {
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
        Ok(())
    }
    fn device_snapshots(&self) -> (Vec<Device>, Vec<(String, Option<String>)>) {
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
        (devices, identities)
    }
}
