//! Configured gesture expectations, driven by monotonic physical input samples.
use super::*;
use std::collections::BTreeMap;

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
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PadContact {
    pub touching: bool,
    pub position: [i16; 2],
}
impl InputFrame {
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
impl DashboardProfile {
    pub fn recipe(&self, mode: Mode, c: Control) -> Option<&Recipe> {
        self.recipes
            .iter()
            .find(|r| r.mode == mode && r.control == c)
    }
    pub fn validate(&self) -> Result<(), String> {
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
        if self.steering.as_ref().is_some_and(|s| {
            s.output_ms >= s.window_ms
                || !(1..1000).contains(&s.deadzone)
                || [s.hold_ms, s.window_ms, s.cover_ms, s.output_ms]
                    .iter()
                    .any(|t| !(1..=1000).contains(t))
        }) {
            return Err("Invalid Steering thresholds".into());
        }
        for (n, p) in self.pages.iter().enumerate() {
            if let Some(pads) = &p.trackpads {
                for pad in pads {
                    pad.validate()?;
                }
            }
            if p.bindings.len() != 16
                || Control::ALL.iter().any(|c| !p.bindings.contains_key(c))
                || self.pages[..n]
                    .iter()
                    .any(|q| q.mode == p.mode && q.context == p.context && q.phase == p.phase)
            {
                return Err("Missing or duplicate control page/binding".into());
            }
            for b in p.bindings.values() {
                match b {
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
        }
        for mode in Mode::ALL {
            for context in Context::ALL {
                if !self
                    .pages
                    .iter()
                    .any(|p| p.mode == mode && p.context == context && p.phase == "reference")
                {
                    return Err("Missing reference page".into());
                }
            }
        }
        for (n, r) in self.recipes.iter().enumerate() {
            if !Control::OWNERS.contains(&r.control)
                || self.recipes[..n]
                    .iter()
                    .any(|q| q.mode == r.mode && q.control == r.control)
                || [r.hold_ms, r.output_ms, r.window_ms, r.cover_ms]
                    .iter()
                    .any(|x| !(1..=1000).contains(x))
                || r.output_ms >= r.window_ms
                || r.repeat_ms.is_some_and(|x| !(1..=1000).contains(&x))
                || r.modifier_label
                    .as_ref()
                    .is_some_and(|s| s.trim().is_empty())
            {
                return Err("Invalid gesture recipe".into());
            }
            for phase in ["pressed", "hold", "window", "second", "cover"] {
                let id = format!("{}:{phase}", r.control.key());
                if !self.pages.iter().any(|p| p.mode == r.mode && p.phase == id) {
                    return Err(format!("Missing gesture page {id}"));
                }
            }
        }
        Ok(())
    }
}
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Phase {
    #[default]
    Idle,
    Pressed,
    Window,
    Second,
    Hold,
    Cover,
    Consumed,
    Output,
    Combined,
    CombinedCover,
    Unknown,
    Interrupted,
}
impl Phase {
    pub fn label(self) -> &'static str {
        match self {
            Self::Idle => "Ready",
            Self::Pressed => "Release for tap",
            Self::Window => "Release window open",
            Self::Second => "Second hold in progress",
            Self::Hold => "Hold action active",
            Self::Cover => "Second hold active",
            Self::Consumed => "Tap Cover · gesture used",
            Self::Output => "Output in another gesture",
            Self::Combined => "Combined modifiers",
            Self::CombinedCover => "Combined Tap Cover",
            Self::Unknown => "Held before tracking · release to reset",
            Self::Interrupted => "Timing interrupted",
        }
    }
    pub fn page(self) -> Option<&'static str> {
        match self {
            Self::Pressed => Some("pressed"),
            Self::Window => Some("window"),
            Self::Second => Some("second"),
            Self::Hold => Some("hold"),
            Self::Cover => Some("cover"),
            Self::Consumed => Some("consumed"),
            _ => None,
        }
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Lane {
    pub phase: Phase,
    #[serde(default)]
    pub inherited_phase: Option<Phase>,
    pub started_ms: u64,
    pub deadline_ms: Option<u64>,
    pub output_at_ms: Option<u64>,
    pub output_seen: bool,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct GestureMark {
    pub lane: usize,
    pub at_ms: u64,
    pub label: String,
}
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
    fn update_steering(
        &mut self,
        mode: Mode,
        p: &DashboardProfile,
        old: &InputFrame,
        input: &InputFrame,
        now: u64,
    ) {
        let Some(r) = p.steering.as_ref().filter(|_| mode == Mode::Steering) else {
            return;
        };
        let one_bumper = input.down(Control::L1) != input.down(Control::R1);
        let direction = input.stick_positions[0]
            .map(|[x, y]| {
                if y.unsigned_abs() > r.deadzone as u16 && y.unsigned_abs() >= x.unsigned_abs() {
                    if y < 0 { -1 } else { 1 }
                } else {
                    0
                }
            })
            .unwrap_or(0);
        if !one_bumper {
            self.steering_lane = Lane::default();
            self.steering_direction = 0;
            return;
        }
        let l = &mut self.steering_lane;
        if l.deadline_ms.is_some_and(|t| now >= t) {
            l.phase = match l.phase {
                Phase::Pressed => Phase::Hold,
                Phase::Second => Phase::Cover,
                _ => Phase::Idle,
            };
            l.deadline_ms = None;
        }
        if direction == 0 {
            if matches!(l.phase, Phase::Pressed | Phase::Second) {
                *l = Lane {
                    phase: Phase::Window,
                    started_ms: now,
                    deadline_ms: Some(now + r.window_ms),
                    ..Lane::default()
                };
            } else if l.phase != Phase::Window {
                *l = Lane::default();
            }
        } else if direction != self.steering_direction
            || matches!(l.phase, Phase::Idle | Phase::Window)
        {
            let second = direction == self.steering_direction && l.phase == Phase::Window;
            *l = Lane {
                phase: if second {
                    Phase::Second
                } else {
                    Phase::Pressed
                },
                started_ms: now,
                deadline_ms: Some(now + if second { r.cover_ms } else { r.hold_ms }),
                ..Lane::default()
            };
            self.steering_direction = direction;
        }
        // A consumed direction applies Tap Cover without dropping its inherited modifier.
        if l.phase == Phase::Pressed
            && (Control::ALL
                .into_iter()
                .any(|c| !matches!(c, Control::L1 | Control::R1) && input.down(c) && !old.down(c))
                || (0..2).any(|n| old.touches[n] == Some(true) && input.touches[n] == Some(false)))
        {
            l.phase = Phase::Hold;
            l.deadline_ms = None;
        }
    }
    fn update(
        &mut self,
        mode: Mode,
        p: &DashboardProfile,
        old: &InputFrame,
        input: &InputFrame,
        now: u64,
    ) {
        let now = now.max(self.clock_ms);
        self.clock_ms = now;
        if !self.initialized {
            self.initialized = true;
            for (n, c) in Control::OWNERS.iter().enumerate() {
                if input.down(*c) && p.recipe(mode, *c).is_some() {
                    self.enter(n, Phase::Unknown, now, None);
                }
            }
            return;
        }
        self.update_steering(mode, p, old, input, now);
        self.advance(mode, p, now);
        let touched_release =
            (0..2).any(|n| old.touches[n] == Some(true) && input.touches[n] == Some(false));
        let pressed: Vec<_> = Control::ALL
            .into_iter()
            .filter(|c| input.down(*c) && !old.down(*c))
            .collect();
        let bumper_count = [Control::L1, Control::R1]
            .iter()
            .filter(|c| input.down(**c))
            .count();
        let menu_count = [Control::Select, Control::Start]
            .iter()
            .filter(|c| input.down(**c))
            .count();
        // Combined menu and menu-stick-click routes can alter persistent Steam state.
        // Never infer a new manual mode from those physical gestures.
        if menu_count > 1
            || (menu_count > 0 && [Control::L3, Control::R3].iter().any(|c| input.down(*c)))
            || input.pad_active && !old.pad_active
            || (menu_count > 0 && input.sticks.iter().any(|b| *b) && self.animating())
        {
            self.uncertainty =
                Some("Timing uncertain after a pad/menu gesture. Showing inherited modifier bindings; release controls to reset timing.".into());
            for (n, c) in Control::OWNERS.iter().enumerate() {
                if (input.down(*c) || self.lanes[n].phase == Phase::Window)
                    && self.lanes[n].phase != Phase::Interrupted
                {
                    let inherited = self.lanes[n].phase;
                    self.enter(n, Phase::Interrupted, now, None);
                    self.lanes[n].inherited_phase = Some(inherited);
                }
            }
        }
        if self.uncertainty.is_some() {
            if !input.buttons.iter().any(|b| *b)
                && !input.pad_active
                && !input.sticks.iter().any(|b| *b)
            {
                self.uncertainty = None;
                self.lanes = Default::default();
            }
            return;
        }
        if mode == Mode::Base
            && bumper_count == 2
            && pressed
                .iter()
                .any(|c| matches!(c, Control::L1 | Control::R1))
        {
            let window = self.lanes[..2]
                .iter()
                .any(|l| matches!(l.phase, Phase::Window | Phase::Second | Phase::Cover));
            if !window {
                for n in 0..2 {
                    self.enter(n, Phase::Combined, now, Some(p.combined_hold_ms));
                }
            }
        }
        for (n, c) in Control::OWNERS.into_iter().enumerate() {
            let Some(r) = p.recipe(mode, c) else { continue };
            let down = input.down(c);
            let was = old.down(c);
            let phase = self.lanes[n].phase;
            if phase == Phase::Window && r.touch_cancels_window && touched_release {
                self.enter(n, Phase::Idle, now, None);
            }
            let phase = self.lanes[n].phase;
            if !down && was {
                match phase {
                    Phase::Pressed | Phase::Second => {
                        self.enter(n, Phase::Window, now, Some(r.window_ms));
                        self.lanes[n].output_at_ms = Some(now + r.output_ms);
                    }
                    Phase::Combined | Phase::CombinedCover => {
                        self.enter(n, Phase::Idle, now, None);
                        if n < 2 && input.down(Control::OWNERS[1 - n]) {
                            self.enter(1 - n, Phase::Consumed, now, None);
                        }
                    }
                    _ => self.enter(n, Phase::Idle, now, None),
                }
            } else if down && !was && !matches!(phase, Phase::Combined | Phase::CombinedCover) {
                // An opposite-owner press inside a timed window is a replacement output,
                // not a new modifier entry. Leave that window's own clock intact.
                let other_owner = self
                    .lanes
                    .iter()
                    .enumerate()
                    .any(|(j, l)| j != n && l.phase.page().is_some());
                if phase == Phase::Window {
                    self.enter(n, Phase::Second, now, Some(r.cover_ms));
                } else if other_owner {
                    self.enter(n, Phase::Output, now, None);
                } else {
                    self.enter(n, Phase::Pressed, now, Some(r.hold_ms));
                }
            }
            if down {
                let phase = self.lanes[n].phase;
                if matches!(phase, Phase::Pressed | Phase::Hold)
                    && (pressed.iter().any(|c| r.cancel_controls.contains(c))
                        || (r.both_sticks_consume && input.sticks.iter().all(|b| *b)))
                {
                    self.enter(n, Phase::Consumed, now, None);
                } else if r.touch_completes && touched_release {
                    if phase == Phase::Pressed {
                        self.enter(n, Phase::Hold, now, None);
                    } else if phase == Phase::Second {
                        self.enter(n, Phase::Cover, now, None);
                    }
                }
            }
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
        if self.device.as_deref() != Some(id) || self.status != InputStatus::Live {
            self.gestures = Gestures::default();
        }
        if let Some(d) = &p.dashboard {
            self.gestures.update(self.mode, d, &self.input, &input, now);
        }
        self.input = input;
        self.held = [self.input.down(Control::L1), self.input.down(Control::R1)];
        self.device = Some(id.into());
        self.status = InputStatus::Live;
    }
    pub fn control_page<'a>(&self, p: &'a Profile) -> Option<&'a ControlPage> {
        let d = p.dashboard.as_ref()?;
        let phases: [Phase; 4] = std::array::from_fn(|n| {
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
        });
        let mut active = None;
        // Windows have highest priority; otherwise menu owners then second-press
        // phases, followed by ordinary single modifiers. Both modifiers use the
        // exported press-order-checked reference page.
        for n in [0, 1, 2, 3] {
            if phases[n] == Phase::Window {
                active = Some(n);
                break;
            }
        }
        if active.is_none() {
            for n in [2, 3, 0, 1] {
                if phases[n].page().is_some() {
                    active = Some(n);
                    break;
                }
            }
        }
        let phase = active.and_then(|n| {
            phases[n]
                .page()
                .map(|phase| format!("{}:{phase}", Control::OWNERS[n].key()))
        });
        let steering_phase = (self.mode == Mode::Steering)
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
            .flatten();
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
impl InputTracker {
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
