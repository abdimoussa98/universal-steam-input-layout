//! Display state and the profile page selected by physical input.
use super::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InputStatus {
    #[default]
    SelectDevice,
    Live,
    Disconnected,
    Paused,
    UnsupportedMapping,
    Unavailable,
}
impl InputStatus {
    pub fn label(&self) -> &'static str {
        match self {
            Self::SelectDevice => "Select a controller · press a button if it is missing",
            Self::Live => "Live",
            Self::Disconnected => "Controller disconnected · select it again after reconnecting",
            Self::Paused => "Input paused · waiting for a fresh snapshot",
            Self::UnsupportedMapping => "Unsupported controller mapping",
            Self::Unavailable => "Input unavailable",
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct State {
    pub mode: Mode,
    pub held: [bool; 2],
    pub status: InputStatus,
    pub device: Option<String>,
    #[serde(default)]
    pub input: InputFrame,
    #[serde(default)]
    pub gestures: Gestures,
    /// Viewer-only time stretch; Steam and the exported profile stay unchanged.
    #[serde(default = "normal_timing")]
    pub timing_scale: u8,
}
fn normal_timing() -> u8 {
    1
}
impl Default for State {
    fn default() -> Self {
        Self {
            mode: Mode::default(),
            held: [false; 2],
            status: InputStatus::default(),
            device: None,
            input: InputFrame::default(),
            gestures: Gestures::default(),
            timing_scale: 1,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct View {
    pub mode: Mode,
    pub held: [bool; 2],
    pub labels: [String; 4],
    pub status: InputStatus,
}
impl State {
    pub fn timing_scale(&self) -> u8 {
        self.timing_scale.clamp(1, 10)
    }
    pub fn set_timing_scale(&mut self, scale: u8) {
        let scale = scale.clamp(1, 10);
        if self.timing_scale != scale {
            self.timing_scale = scale;
            // A speed change cannot finish a gesture or turn a held button into
            // a fresh press. The next sample requires release before tracking.
            self.gestures = Gestures::default();
        }
    }
    pub fn select_mode(&mut self, mode: Mode) -> bool {
        let changed = self.mode != mode;
        if changed {
            self.gestures = Gestures::default();
        }
        self.mode = mode;
        changed
    }
    pub fn modifier(&mut self, index: usize, held: bool) -> bool {
        if index >= 2 || self.status != InputStatus::Live {
            return false;
        }
        let changed = self.held[index] != held;
        self.held[index] = held;
        changed
    }
    pub fn snapshot(&mut self, id: &str, held: [bool; 2]) {
        self.device = Some(id.into());
        self.held = held;
        self.status = InputStatus::Live;
    }
    pub fn unavailable(&mut self, status: InputStatus) {
        self.held = [false; 2];
        self.input = InputFrame::default();
        self.gestures = Gestures::default();
        self.device = None;
        self.status = status;
    }
    pub fn view(&self, p: &Profile) -> View {
        View {
            mode: self.mode,
            held: self.held,
            labels: p.labels(self.mode, Context::from_held(self.held)),
            status: self.status.clone(),
        }
    }
}
impl State {
    /// One shared display follows the timed gesture, never a replacement output.
    pub fn timer_owner(&self, p: &Profile) -> Option<usize> {
        let dashboard = p.dashboard.as_ref()?;
        let supported = |n: usize| dashboard.recipe(self.mode, Control::OWNERS[n]).is_some();
        (0..4)
            .filter(|n| supported(*n))
            .filter(|n| !matches!(self.gestures.lanes[*n].phase, Phase::Idle | Phase::Output))
            .max_by_key(|n| {
                let l = &self.gestures.lanes[*n];
                (
                    l.phase == Phase::Window,
                    l.deadline_ms.is_some(),
                    l.started_ms,
                )
            })
            .or_else(|| {
                self.gestures
                    .history
                    .iter()
                    .rev()
                    .find(|m| {
                        supported(m.lane) && self.gestures.lanes[m.lane].phase != Phase::Output
                    })
                    .map(|m| m.lane)
            })
            .or_else(|| (0..4).find(|n| supported(*n)))
    }
    pub fn sample_input(&mut self, id: &str, input: InputFrame, p: &Profile, now: u64) {
        let now = now / u64::from(self.timing_scale());
        if self.device.as_deref() != Some(id) || self.status != InputStatus::Live {
            self.gestures = Gestures::default();
        }
        if let Some(d) = &p.dashboard {
            self.gestures
                .update(self.mode, d, [&self.input, &input], now);
        }
        self.input = input;
        self.held = [self.input.down(Control::L1), self.input.down(Control::R1)];
        self.device = Some(id.into());
        self.status = InputStatus::Live;
    }
    pub fn control_page<'a>(&self, p: &'a Profile) -> Option<&'a ControlPage> {
        let d = p.dashboard.as_ref()?;
        let phases = self.effective_phases();
        let phase = Self::owner_phase(phases);
        let steering_phase = self.steering_phase();
        let combined_phase = (self.held == [true, true]
            && phases[..2].contains(&Phase::CombinedCover))
        .then(|| "combined:cover".to_string());
        let phase = phase.or(steering_phase).or(combined_phase);
        phase
            .as_ref()
            .and_then(|phase| {
                d.pages.iter().find(|row| {
                    row.mode == self.mode
                        && row.phase == *phase
                        && (!phase.starts_with("ls:")
                            || row.context == Context::from_held(self.held))
                })
            })
            .or_else(|| {
                d.pages.iter().find(|row| {
                    row.mode == self.mode
                        && row.context
                            == Context::from_held(std::array::from_fn(|n| {
                                self.held[n] && phases[n] != Phase::Output
                            }))
                        && row.phase == "reference"
                })
            })
    }
    fn effective_phases(&self) -> [Phase; 4] {
        std::array::from_fn(|n| {
            let lane = &self.gestures.lanes[n];
            if lane.phase == Phase::Interrupted {
                if self.input.down(Control::OWNERS[n]) {
                    lane.inherited_phase.unwrap_or(Phase::Idle)
                } else {
                    Phase::Idle
                }
            } else {
                lane.phase
            }
        })
    }
    fn owner_phase(phases: [Phase; 4]) -> Option<String> {
        // Windows have highest priority; otherwise menu owners then second-press
        // phases, followed by ordinary single modifiers. Both modifiers use the
        // exported press-order-checked reference page.
        let active = (0..4).find(|n| phases[*n] == Phase::Window).or_else(|| {
            [2, 3, 0, 1]
                .into_iter()
                .find(|n| phases[*n].page().is_some())
        });
        active.and_then(|n| {
            phases[n]
                .page()
                .map(|phase| format!("{}:{phase}", Control::OWNERS[n].key()))
        })
    }
    fn steering_phase(&self) -> Option<String> {
        (self.mode == Mode::Steering)
            .then(|| {
                self.gestures.steering_lane.phase.page().map(|phase| {
                    format!(
                        "ls:{}:{phase}",
                        if self.gestures.steering_direction < 0 {
                            "up"
                        } else {
                            "down"
                        }
                    )
                })
            })
            .flatten()
    }
    pub fn control_labels(&self, p: &Profile) -> [String; 16] {
        let Some(_) = &p.dashboard else {
            return std::array::from_fn(|n| {
                if n < 4 {
                    p.labels(self.mode, Context::from_held(self.held))[n].clone()
                } else {
                    "Unavailable".into()
                }
            });
        };
        let page = self.control_page(p);
        std::array::from_fn(
            |n| match page.and_then(|row| row.bindings.get(&Control::ALL[n])) {
                Some(Binding::Label { text }) => text.clone(),
                Some(Binding::Unbound) => "Unbound".into(),
                Some(Binding::Unavailable { .. }) | None | Some(Binding::Inherit) => {
                    "Unavailable".into()
                }
            },
        )
    }
}
