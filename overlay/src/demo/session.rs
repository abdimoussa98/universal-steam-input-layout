use super::{Engine, Input, Layout};
use std::sync::Arc;

#[derive(Clone, serde::Serialize, serde::Deserialize)]
pub struct RecordedInput {
    pub at: u64,
    pub input: Input,
}
pub struct Session {
    pub engine: Engine,
    pub scale: u8,
    pub paused: bool,
    pub recording: Vec<RecordedInput>,
    pub replaying: bool,
    wall: Option<f64>,
    logical: f64,
    replay: Vec<RecordedInput>,
    replay_index: usize,
    replay_end: u64,
}
impl Session {
    pub fn new(layout: Arc<Layout>) -> Self {
        Self {
            engine: Engine::new(layout),
            scale: 1,
            paused: false,
            recording: vec![],
            replaying: false,
            wall: None,
            logical: 0.,
            replay: vec![],
            replay_index: 0,
            replay_end: 0,
        }
    }
    pub fn tick(&mut self, wall: f64) {
        let wall = wall.max(self.wall.unwrap_or(wall));
        let delta = self
            .wall
            .replace(wall)
            .map(|last| (wall - last).max(0.))
            .unwrap_or(0.);
        if !self.paused {
            self.logical += delta / f64::from(self.scale.max(1));
        }
        let end = self.logical as u64;
        if self.replaying {
            while self.replay_index < self.replay.len() && self.replay[self.replay_index].at <= end
            {
                let event = &self.replay[self.replay_index];
                self.engine.advance_to(event.at);
                self.engine.input(&event.input);
                self.replay_index += 1;
            }
            if end >= self.replay_end {
                self.replaying = false;
            }
        }
        self.engine.advance_to(end);
    }
    pub fn input(&mut self, input: Input) {
        if self.paused || self.replaying {
            return;
        }
        self.recording.push(RecordedInput {
            at: self.engine.now,
            input: input.clone(),
        });
        self.engine.input(&input);
    }
    pub fn reset(&mut self) {
        let scale = self.scale;
        *self = Self::new(self.engine.layout.clone());
        self.scale = scale;
    }
    pub fn replay(&mut self) {
        let recording = self.recording.clone();
        let end = self.engine.now;
        self.reset();
        self.replay = recording.clone();
        self.recording = recording;
        self.replaying = true;
        self.replay_end = end;
    }
    pub fn step(&mut self) {
        self.paused = true;
        let input = self
            .replaying
            .then(|| self.replay.get(self.replay_index).map(|e| e.at))
            .flatten();
        if let Some(next) = self
            .engine
            .next_deadline()
            .into_iter()
            .chain(input)
            .chain(self.replaying.then_some(self.replay_end))
            .min()
        {
            self.engine.advance_to(next);
            self.logical = next as f64;
            while self.replaying
                && self
                    .replay
                    .get(self.replay_index)
                    .is_some_and(|e| e.at <= next)
            {
                self.engine.input(&self.replay[self.replay_index].input);
                self.replay_index += 1;
            }
            if self.replaying && next >= self.replay_end {
                self.replaying = false;
            }
        }
    }
    pub fn cancel_input(&mut self) {
        // Source changes/focus loss are a reset, not a burst of synthetic releases
        // that could accidentally complete a multi-tap gesture.
        self.reset();
    }
}
