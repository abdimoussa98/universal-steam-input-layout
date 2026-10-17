//! Validated control pages and gesture recipes exported from a layout.
use super::super::{Binding, Context, Control, Mode, TrackpadBindings};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ControlPage {
    pub mode: Mode,
    pub context: Context,
    pub phase: String,
    pub bindings: BTreeMap<Control, Binding>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub trackpads: Option<[TrackpadBindings; 2]>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Recipe {
    pub mode: Mode,
    pub control: Control,
    pub hold_ms: u64,
    pub output_ms: u64,
    pub window_ms: u64,
    pub cover_ms: u64,
    pub repeat_ms: Option<u64>,
    pub tap_label: String,
    pub hold_label: String,
    /// Immediate modifier action; hold_label describes its delayed effect.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub modifier_label: Option<String>,
    pub touch_completes: bool,
    pub touch_cancels_window: bool,
    pub both_sticks_consume: bool,
    pub cancel_controls: Vec<Control>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DashboardProfile {
    pub pages: Vec<ControlPage>,
    pub recipes: Vec<Recipe>,
    pub combined_hold_ms: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub combined_release_label: Option<String>,
    pub trigger_thresholds: [Option<u16>; 2],
    #[serde(default)]
    pub steering: Option<SteeringProfile>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SteeringProfile {
    pub output_ms: u64,
    pub deadzone: i16,
    pub hold_ms: u64,
    pub window_ms: u64,
    pub cover_ms: u64,
}
impl ControlPage {
    fn validate(&self, previous: &[Self]) -> Result<(), String> {
        if let Some(pads) = &self.trackpads {
            for pad in pads {
                pad.validate()?;
            }
        }
        if self.bindings.len() != 16
            || Control::ALL.iter().any(|c| !self.bindings.contains_key(c))
            || previous.iter().any(|page| {
                page.mode == self.mode && page.context == self.context && page.phase == self.phase
            })
        {
            return Err("Missing or duplicate control page/binding".into());
        }
        for binding in self.bindings.values() {
            match binding {
                Binding::Label { text } if text.trim().is_empty() => {
                    return Err("Empty control label".into());
                }
                Binding::Unavailable { reason } if reason.is_empty() => {
                    return Err("Missing unavailable reason".into());
                }
                Binding::Inherit => {
                    return Err("Dashboard pages require resolved bindings".into());
                }
                _ => {}
            }
        }
        Ok(())
    }
}

impl Recipe {
    fn validate(&self, previous: &[Self], pages: &[ControlPage]) -> Result<(), String> {
        if !Control::OWNERS.contains(&self.control)
            || previous
                .iter()
                .any(|r| r.mode == self.mode && r.control == self.control)
            || [self.hold_ms, self.output_ms, self.window_ms, self.cover_ms]
                .iter()
                .any(|ms| !(1..=1000).contains(ms))
            || self.output_ms >= self.window_ms
            || self.repeat_ms.is_some_and(|ms| !(1..=1000).contains(&ms))
            || self
                .modifier_label
                .as_ref()
                .is_some_and(|s| s.trim().is_empty())
        {
            return Err("Invalid gesture recipe".into());
        }
        for phase in ["pressed", "hold", "window", "second", "cover"] {
            let id = format!("{}:{phase}", self.control.key());
            if !pages
                .iter()
                .any(|page| page.mode == self.mode && page.phase == id)
            {
                return Err(format!("Missing gesture page {id}"));
            }
        }
        Ok(())
    }
}

impl SteeringProfile {
    fn validate(&self) -> Result<(), String> {
        if self.output_ms >= self.window_ms
            || !(1..1000).contains(&self.deadzone)
            || [self.hold_ms, self.window_ms, self.cover_ms, self.output_ms]
                .iter()
                .any(|ms| !(1..=1000).contains(ms))
        {
            return Err("Invalid Steering thresholds".into());
        }
        Ok(())
    }
}

impl DashboardProfile {
    pub fn recipe(&self, mode: Mode, c: Control) -> Option<&Recipe> {
        self.recipes
            .iter()
            .find(|r| r.mode == mode && r.control == c)
    }
    pub fn validate(&self) -> Result<(), String> {
        self.validate_limits()?;
        if let Some(steering) = &self.steering {
            steering.validate()?;
        }
        for (index, page) in self.pages.iter().enumerate() {
            page.validate(&self.pages[..index])?;
        }
        self.validate_reference_pages()?;
        for (index, recipe) in self.recipes.iter().enumerate() {
            recipe.validate(&self.recipes[..index], &self.pages)?;
        }
        Ok(())
    }
    fn validate_limits(&self) -> Result<(), String> {
        if self.pages.len() > 256
            || self.recipes.len() > 12
            || !(1..=1000).contains(&self.combined_hold_ms)
            || self
                .combined_release_label
                .as_ref()
                .is_some_and(|s| s.trim().is_empty())
            || self.trigger_thresholds.iter().flatten().any(|v| *v > 1000)
        {
            return Err("Invalid dashboard limits".into());
        }
        Ok(())
    }
    fn validate_reference_pages(&self) -> Result<(), String> {
        for mode in Mode::ALL {
            for context in Context::ALL {
                if !self.pages.iter().any(|page| {
                    page.mode == mode && page.context == context && page.phase == "reference"
                }) {
                    return Err("Missing reference page".into());
                }
            }
        }
        Ok(())
    }
}
