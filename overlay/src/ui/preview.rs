//! Local pointer input uses the same gesture clock as controller input.
use super::FrameData;
use crate::core::{Control, InputChange, InputFrame, Profile, State};

#[cfg(test)]
mod tests;

const DEVICE: &str = "viewer-mouse";

#[derive(Default)]
pub(super) struct Preview {
    session: Option<Session>,
}

struct Session {
    state: State,
    profile: Profile,
}

impl Session {
    fn new(data: &FrameData, now_ms: u64) -> Self {
        let mut state = State {
            mode: data.state.mode,
            timing_scale: data.state.timing_scale(),
            ..State::default()
        };
        // A controller first seen while held is intentionally uncertain. Mouse
        // input has a known press edge, so seed the neutral snapshot first.
        state.sample_input(DEVICE, InputFrame::default(), &data.profile, now_ms);
        Self {
            state,
            profile: data.profile.clone(),
        }
    }

    fn matches(&self, data: &FrameData) -> bool {
        self.state.mode == data.state.mode
            && self.state.timing_scale() == data.state.timing_scale()
            && self.profile == data.profile
    }

    fn sample(&mut self, input: InputFrame, now_ms: u64) {
        // Pass wall-clock milliseconds unchanged; State applies slow motion.
        self.state
            .sample_input(DEVICE, input, &self.profile, now_ms);
    }
}

impl Preview {
    pub(super) fn active(&self) -> bool {
        self.session.is_some()
    }

    pub(super) fn cancel(&mut self) {
        self.session = None;
    }

    pub(super) fn set(&mut self, control: Control, down: bool, data: &FrameData, now_ms: u64) {
        self.invalidate(data);
        if !down && !self.active() {
            return;
        }
        let session = self
            .session
            .get_or_insert_with(|| Session::new(data, now_ms));
        let mut input = session.state.input.clone();
        let change = match control {
            Control::L2 => InputChange::Trigger(0, if down { 1000 } else { 0 }),
            Control::R2 => InputChange::Trigger(1, if down { 1000 } else { 0 }),
            _ => InputChange::Button(control, down),
        };
        change.apply(&mut input);
        // Sample every edge immediately, even when press and release arrive in
        // one rendered frame. Coalescing them would lose the timed window.
        session.sample(input, now_ms);
    }

    pub(super) fn update(&mut self, data: &FrameData, now_ms: u64) -> Option<State> {
        self.invalidate(data);
        let session = self.session.as_mut()?;
        session.sample(session.state.input.clone(), now_ms);
        if session.state.input.buttons.iter().any(|down| *down)
            || session.state.gestures.animating()
        {
            Some(session.state.clone())
        } else {
            self.cancel();
            None
        }
    }

    fn invalidate(&mut self, data: &FrameData) {
        if self
            .session
            .as_ref()
            .is_some_and(|session| !session.matches(data))
        {
            self.cancel();
        }
    }
}
