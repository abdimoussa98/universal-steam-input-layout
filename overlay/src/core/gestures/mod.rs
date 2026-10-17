//! Configured gesture expectations, driven by monotonic physical input samples.
use super::{Control, InputFrame, Mode};
use serde::{Deserialize, Serialize};

mod dashboard;
mod lane;
mod sample;
mod steering;
mod transitions;
pub use dashboard::{ControlPage, DashboardProfile, Recipe, SteeringProfile};
pub use lane::{GestureMark, Lane, Phase};
use sample::GestureSample;

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Gestures {
    pub lanes: [Lane; 4],
    pub history: Vec<GestureMark>,
    pub clock_ms: u64,
    pub initialized: bool,
    pub uncertainty: Option<String>,
    #[serde(default)]
    pub steering_lane: Lane,
    #[serde(default)]
    pub steering_direction: i8,
}
impl Gestures {
    fn mark(&mut self, n: usize, t: u64, label: impl Into<String>) {
        self.history.push(GestureMark {
            lane: n,
            at_ms: t,
            label: label.into(),
        });
        if self.history.len() > 16 {
            self.history.remove(0);
        }
    }
    fn enter(&mut self, n: usize, phase: Phase, t: u64, duration: Option<u64>) {
        self.lanes[n] = Lane {
            phase,
            started_ms: t,
            deadline_ms: duration.map(|d| t.saturating_add(d)),
            ..Lane::default()
        };
        self.mark(n, t, phase.label());
    }
    pub fn animating(&self) -> bool {
        self.steering_lane.deadline_ms.is_some()
            || self.lanes.iter().any(|l| l.deadline_ms.is_some())
    }
    fn advance(&mut self, mode: Mode, p: &DashboardProfile, now: u64) {
        for n in 0..4 {
            let Some(r) = p.recipe(mode, Control::OWNERS[n]) else {
                continue;
            };
            let l = &self.lanes[n];
            if l.phase == Phase::Window
                && !l.output_seen
                && l.output_at_ms.is_some_and(|t| t <= now)
            {
                let t = l.output_at_ms.unwrap();
                self.lanes[n].output_seen = true;
                self.mark(n, t, format!("Expected {}", r.tap_label));
            }
            if let Some(t) = self.lanes[n].deadline_ms.filter(|t| *t <= now) {
                let phase = match self.lanes[n].phase {
                    Phase::Pressed => Phase::Hold,
                    Phase::Window => Phase::Idle,
                    Phase::Second => Phase::Cover,
                    Phase::Combined => Phase::CombinedCover,
                    _ => continue,
                };
                self.enter(n, phase, t, None);
            }
        }
    }
    pub(super) fn update(
        &mut self,
        mode: Mode,
        profile: &DashboardProfile,
        inputs: [&InputFrame; 2],
        now: u64,
    ) {
        let now = now.max(self.clock_ms);
        self.clock_ms = now;
        let sample = GestureSample::new(mode, profile, inputs, now);
        if !self.initialized {
            self.initialize(&sample);
            return;
        }
        steering::update(self, &sample);
        self.advance(mode, profile, now);
        if sample.uncertain(self.animating()) {
            self.interrupt(&sample);
        }
        if self.uncertainty.is_some() {
            if sample.all_released() {
                self.uncertainty = None;
                self.lanes = Default::default();
            }
            return;
        }
        self.combine(&sample);
        for (n, control) in Control::OWNERS.into_iter().enumerate() {
            if let Some(recipe) = profile.recipe(mode, control) {
                transitions::update(self, n, recipe, &sample);
            }
        }
    }
    fn initialize(&mut self, sample: &GestureSample<'_>) {
        self.initialized = true;
        for (n, control) in Control::OWNERS.iter().enumerate() {
            if sample.input.down(*control) && sample.profile.recipe(sample.mode, *control).is_some()
            {
                self.enter(n, Phase::Unknown, sample.now, None);
            }
        }
    }
    fn interrupt(&mut self, sample: &GestureSample<'_>) {
        self.uncertainty = Some("Timing uncertain after a pad/menu gesture. Showing inherited modifier bindings; release controls to reset timing.".into());
        for (n, control) in Control::OWNERS.iter().enumerate() {
            if (sample.input.down(*control) || self.lanes[n].phase == Phase::Window)
                && self.lanes[n].phase != Phase::Interrupted
            {
                let inherited = self.lanes[n].phase;
                self.enter(n, Phase::Interrupted, sample.now, None);
                self.lanes[n].inherited_phase = Some(inherited);
            }
        }
    }
    fn combine(&mut self, sample: &GestureSample<'_>) {
        if sample.combined_press() {
            let window = self.lanes[..2]
                .iter()
                .any(|lane| matches!(lane.phase, Phase::Window | Phase::Second | Phase::Cover));
            if !window {
                for n in 0..2 {
                    self.enter(
                        n,
                        Phase::Combined,
                        sample.now,
                        Some(sample.profile.combined_hold_ms),
                    );
                }
            }
        }
    }
}
