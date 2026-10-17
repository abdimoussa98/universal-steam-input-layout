//! Physical input snapshots, queued edges, and stable device selection.
use super::{InputStatus, Profile, State};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[repr(usize)]
pub enum Control {
    A,
    B,
    X,
    Y,
    Select,
    Start,
    Up,
    Right,
    Down,
    Left,
    L3,
    R3,
    L1,
    R1,
    L2,
    R2,
}
impl Control {
    pub const ALL: [Self; 16] = [
        Self::A,
        Self::B,
        Self::X,
        Self::Y,
        Self::Select,
        Self::Start,
        Self::Up,
        Self::Right,
        Self::Down,
        Self::Left,
        Self::L3,
        Self::R3,
        Self::L1,
        Self::R1,
        Self::L2,
        Self::R2,
    ];
    pub const OWNERS: [Self; 4] = [Self::L1, Self::R1, Self::Select, Self::Start];
    pub fn label(self) -> &'static str {
        [
            "A", "B", "X", "Y", "Select", "Start", "Up", "Right", "Down", "Left", "L3", "R3", "L1",
            "R1", "L2", "R2",
        ][self as usize]
    }
    pub fn key(self) -> &'static str {
        [
            "a", "b", "x", "y", "select", "start", "up", "right", "down", "left", "l3", "r3", "l1",
            "r1", "l2", "r2",
        ][self as usize]
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct InputFrame {
    pub buttons: [bool; 16],
    /// Trigger travel in thousandths, without assuming a Steam activation threshold.
    pub triggers: [u16; 2],
    pub touches: [Option<bool>; 2],
    pub sticks: [bool; 2],
    pub pad_active: bool,
    /// Signed thousandths; positive Y points down. None means unavailable.
    pub stick_positions: [Option<[i16; 2]>; 2],
    pub pads: [Option<PadContact>; 2],
    /// Physical pad presses, separate from touch. None means unsupported.
    pub pad_clicks: [Option<bool>; 2],
    /// Deck pad force in thousandths. Digital clicks may be disabled by Steam/SDL.
    pub pad_pressures: [Option<u16>; 2],
    /// L4, L5, R4, R5. Unknown is different from released.
    pub back_buttons: [Option<bool>; 4],
    pub motion: Option<MotionSample>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MotionSample {
    /// Pitch, yaw, roll in millidegrees/second, SDL's right-handed axes.
    pub rate: [i32; 3],
    pub timestamp: u32,
    /// Timestamp tick in microseconds (Deck reports use a 4000 us update period).
    pub tick_us: u32,
    pub modulus: u64,
}
impl MotionSample {
    pub fn elapsed_ms(&self, previous: &Self) -> Option<u64> {
        if self.modulus != previous.modulus
            || self.tick_us != previous.tick_us
            || !(1..=1_u64 << 32).contains(&self.modulus)
            || u64::from(self.timestamp) >= self.modulus
            || u64::from(previous.timestamp) >= self.modulus
        {
            return None;
        }
        let elapsed = (u64::from(self.timestamp) + self.modulus - u64::from(previous.timestamp))
            % self.modulus;
        let ms = elapsed.checked_mul(u64::from(self.tick_us))? / 1000;
        (1..=100).contains(&ms).then_some(ms)
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PadContact {
    pub touching: bool,
    pub position: [i16; 2],
}
impl InputFrame {
    pub fn pad_pressed(&self, side: usize, threshold: u16, was_pressed: bool) -> bool {
        if self.pad_clicks[side] == Some(true) {
            return true;
        }
        let touching = self.pads[side].as_ref().is_some_and(|pad| pad.touching);
        // Release slightly below actuation to avoid flickering near the threshold.
        let threshold = if was_pressed {
            threshold * 4 / 5
        } else {
            threshold
        };
        touching && self.pad_pressures[side].is_some_and(|force| force >= threshold.max(1))
    }

    pub fn down(&self, c: Control) -> bool {
        self.buttons[c as usize]
    }
}
#[derive(Clone, Debug)]
pub struct InputEvent {
    pub device: String,
    pub at_ms: u64,
    pub change: InputChange,
}
#[derive(Clone, Debug)]
pub enum InputChange {
    Button(Control, bool),
    Trigger(usize, u16),
    Touch(usize, bool),
    Stick(usize, bool),
    StickAxis(usize, usize, i16),
}
impl InputChange {
    pub fn apply(&self, i: &mut InputFrame) {
        match *self {
            Self::Button(c, b) => i.buttons[c as usize] = b,
            Self::Trigger(n, v) => {
                i.triggers[n] = v;
                i.buttons[Control::L2 as usize + n] = v > 0;
            }
            Self::Touch(n, b) => i.touches[n] = Some(b),
            Self::Stick(n, b) => i.sticks[n] = b,
            Self::StickAxis(n, axis, v) => {
                let xy = i.stick_positions[n].get_or_insert([0, 0]);
                xy[axis] = v.clamp(-1000, 1000);
                i.sticks[n] = xy.iter().any(|v| v.unsigned_abs() > 405);
            }
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Device {
    #[serde(default)]
    pub input: InputFrame,
    pub id: String,
    pub name: String,
    pub standard: bool,
    pub held: [bool; 2],
}
#[derive(Default)]
pub struct InputTracker {
    pub selected: Option<String>,
}
impl InputTracker {
    pub fn select(&mut self, id: Option<String>) {
        self.selected = id;
    }
    /// Full snapshots avoid stale queued button events and seed already-held buttons.
    pub fn sample(&self, state: &mut State, devices: &[Device], paused: bool) -> bool {
        let old = state.clone();
        if paused {
            state.unavailable(InputStatus::Paused);
        } else if let Some(id) = &self.selected {
            match devices.iter().find(|d| &d.id == id) {
                Some(d) if d.standard => state.snapshot(id, d.held),
                Some(_) => state.unavailable(InputStatus::UnsupportedMapping),
                None => state.unavailable(InputStatus::Disconnected),
            }
        } else {
            state.unavailable(InputStatus::SelectDevice);
        }
        *state != old
    }
}

impl InputTracker {
    #[expect(
        clippy::too_many_arguments,
        reason = "Preserve the public timed-sampling API while keeping queued edges separate from snapshots"
    )]
    pub fn sample_timed(
        &self,
        state: &mut State,
        devices: &[Device],
        events: &[InputEvent],
        now: u64,
        p: &Profile,
    ) -> bool {
        let mut old = state.clone();
        if let Some(d) = self
            .selected
            .as_ref()
            .and_then(|id| devices.iter().find(|d| &d.id == id))
            .filter(|d| d.standard)
        {
            if state.device.as_deref() == Some(&d.id) && state.status == InputStatus::Live {
                for e in events.iter().filter(|e| e.device == d.id) {
                    let mut i = state.input.clone();
                    e.change.apply(&mut i);
                    state.sample_input(&d.id, i, p, e.at_ms.min(now));
                }
            }
            let mut frame = d.input.clone();
            frame.buttons[Control::L1 as usize] = d.held[0];
            frame.buttons[Control::R1 as usize] = d.held[1];
            state.sample_input(&d.id, frame, p, now);
        } else {
            self.sample(state, devices, false);
        }
        // Time alone need not redraw an idle window; active countdowns do.
        if !state.gestures.animating() {
            old.gestures.clock_ms = state.gestures.clock_ms;
        }
        old != *state
    }
}
#[derive(Default)]
pub struct InputFreshness {
    last: Option<f64>,
}
impl InputFreshness {
    pub fn received(&mut self, milliseconds: f64) {
        self.last = Some(milliseconds);
    }
    pub fn expired(&self, milliseconds: f64) -> bool {
        self.last.is_none_or(|last| milliseconds - last > 3000.0)
    }
}

/// Prefer a device's hardware serial: macOS HID paths change on reconnect.
/// Hash the serial so diagnostic identities do not disclose it.
pub fn physical_device_identity(
    vendor: Option<u16>,
    product: Option<u16>,
    serial: Option<&str>,
    path: Option<&str>,
) -> Option<String> {
    if let (Some(vendor), Some(product), Some(serial)) = (
        vendor,
        product,
        serial.map(str::trim).filter(|s| !s.is_empty()),
    ) {
        return Some(format!(
            "serial:{vendor:04x}:{product:04x}:{:x}",
            Sha256::digest(serial.as_bytes())
        ));
    }
    path.filter(|p| !p.is_empty()).map(|p| format!("path:{p}"))
}

/// SDL instance IDs change on reconnect; only a unique physical identity can
/// restore a previous selection automatically. Device names are not identities.
#[derive(Default)]
pub struct DeviceSelection {
    pub current: Option<String>,
    path: Option<String>,
}
impl DeviceSelection {
    /// A headless host can choose the only device initially. Once chosen,
    /// reconnect must still match its physical identity, never a different pad.
    pub fn resolve_single(&mut self, devices: &[(String, Option<String>)]) -> Option<String> {
        if self.current.is_none() && devices.len() == 1 {
            self.choose(devices[0].0.clone(), devices[0].1.clone());
        }
        self.resolve(devices)
    }
    pub fn choose(&mut self, id: String, path: Option<String>) {
        self.current = Some(id);
        self.path = path.filter(|p| !p.is_empty());
    }
    pub fn resolve(&mut self, devices: &[(String, Option<String>)]) -> Option<String> {
        let current = self.current.as_ref()?;
        if let Some((id, path)) = devices.iter().find(|(id, _)| id == current) {
            if let Some(path) = path.as_ref().filter(|p| !p.is_empty()) {
                self.path = Some(path.clone());
            }
            return Some(id.clone());
        }
        let path = self.path.as_ref()?;
        let matches: Vec<_> = devices
            .iter()
            .filter(|(_, p)| p.as_ref() == Some(path))
            .collect();
        if matches.len() != 1 {
            return None;
        }
        let id = matches[0].0.clone();
        self.current = Some(id.clone());
        Some(id)
    }
}
