//! Display references for pad clicks and touch gestures, resolved per layer page.
use super::Binding;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TrackpadBindings {
    pub center: Binding,
    /// Clockwise from north: up, right, down, left.
    pub outer: [Binding; 4],
    pub repeat_ms: [Option<u64>; 4],
    pub regions: Option<PadRegions>,
    pub touch: String,
    pub swipe: Option<[Binding; 4]>,
    pub double_tap: Option<PadDoubleTap>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PadRegions {
    pub inner_threshold: u16,
    pub outer_threshold: u16,
    pub outer_delay_ms: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PadDoubleTap {
    pub hold_ms: u64,
    pub window_ms: u64,
    pub clockwise: Binding,
    pub counterclockwise: Binding,
}

impl TrackpadBindings {
    pub fn validate(&self) -> Result<(), String> {
        let mut bindings = vec![&self.center];
        bindings.extend(&self.outer);
        if let Some(swipe) = &self.swipe {
            bindings.extend(swipe);
        }
        if let Some(tap) = &self.double_tap {
            bindings.extend([&tap.clockwise, &tap.counterclockwise]);
            if !(1..=1000).contains(&tap.hold_ms) || !(1..=1000).contains(&tap.window_ms) {
                return Err("Invalid pad touch timing".into());
            }
        }
        if bindings.into_iter().any(|b| match b {
            Binding::Label { text } => text.trim().is_empty(),
            Binding::Unavailable { reason } => reason.trim().is_empty(),
            Binding::Inherit => true,
            Binding::Unbound => false,
        }) || self.touch.trim().is_empty()
            || self
                .repeat_ms
                .iter()
                .flatten()
                .any(|ms| !(1..=1000).contains(ms))
        {
            return Err("Invalid pad binding".into());
        }
        if self.regions.as_ref().is_some_and(|r| {
            r.outer_threshold == 0
                || r.outer_threshold >= r.inner_threshold
                || r.inner_threshold > 32767
                || !(1..=1000).contains(&r.outer_delay_ms)
        }) {
            return Err("Invalid overlapping pad regions".into());
        }
        Ok(())
    }
}

/// Configured radial preview, normalized against the controller axis range.
/// This predicts a fresh click; it does not observe Steam's resulting output.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PadZone {
    Inner,
    Overlap,
    Outer(usize),
}
impl PadRegions {
    pub fn inner_radius(&self) -> f32 {
        f32::from(self.inner_threshold) / 32767.0
    }
    pub fn outer_start(&self) -> f32 {
        f32::from(self.outer_threshold) / 32767.0
    }
    pub fn zone(&self, [x, y]: [f32; 2]) -> PadZone {
        let radius = x.hypot(y);
        if radius <= self.outer_start() {
            PadZone::Inner
        } else if radius <= self.inner_radius() {
            PadZone::Overlap
        } else if x.abs() > y.abs() {
            PadZone::Outer(if x > 0.0 { 1 } else { 3 })
        } else {
            PadZone::Outer(if y > 0.0 { 2 } else { 0 })
        }
    }
}
