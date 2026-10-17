//! Derived edges and interruption signals for one monotonic input sample.
use super::{Control, DashboardProfile, InputFrame, Mode};

pub(super) struct GestureSample<'a> {
    pub mode: Mode,
    pub profile: &'a DashboardProfile,
    pub previous: &'a InputFrame,
    pub input: &'a InputFrame,
    pub now: u64,
    pub pressed: Vec<Control>,
    pub touched_release: bool,
}
impl<'a> GestureSample<'a> {
    pub fn new(
        mode: Mode,
        profile: &'a DashboardProfile,
        [previous, input]: [&'a InputFrame; 2],
        now: u64,
    ) -> Self {
        Self {
            mode,
            profile,
            previous,
            input,
            now,
            pressed: Control::ALL
                .into_iter()
                .filter(|c| input.down(*c) && !previous.down(*c))
                .collect(),
            touched_release: (0..2)
                .any(|n| previous.touches[n] == Some(true) && input.touches[n] == Some(false)),
        }
    }

    pub fn uncertain(&self, animating: bool) -> bool {
        let menu_count = [Control::Select, Control::Start]
            .iter()
            .filter(|c| self.input.down(**c))
            .count();
        // Combined menu and menu-stick-click routes can alter persistent Steam state.
        // Never infer a new manual mode from those physical gestures.
        menu_count > 1
            || (menu_count > 0
                && [Control::L3, Control::R3]
                    .iter()
                    .any(|c| self.input.down(*c)))
            || self.input.pad_active && !self.previous.pad_active
            || (menu_count > 0 && self.input.sticks.iter().any(|b| *b) && animating)
    }

    pub fn all_released(&self) -> bool {
        !self.input.buttons.iter().any(|b| *b)
            && !self.input.pad_active
            && !self.input.sticks.iter().any(|b| *b)
    }

    pub fn combined_press(&self) -> bool {
        self.mode == Mode::Base
            && self.input.down(Control::L1)
            && self.input.down(Control::R1)
            && self
                .pressed
                .iter()
                .any(|c| matches!(c, Control::L1 | Control::R1))
    }
}
