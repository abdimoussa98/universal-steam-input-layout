use super::{Entry, Gyro, Layout, Output, Surface};
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::Arc,
};

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub(crate) enum Phase {
    Down,
    Up,
    Tap,
}
#[derive(Clone)]
pub(crate) struct Binding {
    pub control: String,
    pub layer: usize,
    pub group: usize,
    pub index: usize,
    pub entry: Entry,
    pub inverted: bool,
}
impl Binding {
    pub fn inverted_chord(&self) -> bool {
        self.entry.kind == "chord" && self.entry.flag("edge_binding_invert")
    }
}
#[derive(Clone)]
pub(crate) struct Act {
    pub binding: Binding,
    pub phase: Phase,
    pub due: Option<u64>,
    pub began: u64,
    pub first: bool,
    pub order: u64,
    pub down: BTreeSet<String>,
    pub holds: BTreeSet<usize>,
    pub allow_ops: bool,
}

pub struct Engine {
    pub(crate) presentation: super::presentation::Presentation,
    pub layout: Arc<Layout>,
    pub now: u64,
    pub error: Option<String>,
    pub(crate) stack: Vec<usize>,
    pub(crate) held: BTreeSet<String>,
    pub(crate) between: BTreeSet<String>,
    pub(crate) acts: BTreeMap<u64, Act>,
    pub(crate) bound: BTreeMap<(String, Phase), Option<(usize, usize)>>,
    pub(crate) inverted: BTreeSet<String>,
    pub(crate) pressed_at: BTreeMap<String, u64>,
    pub(crate) order: u64,
    pub(crate) output: Output,
    pub(crate) surfaces: BTreeMap<String, Surface>,
    pub(crate) gyro: Gyro,
    pub(crate) trigger_values: BTreeMap<String, f64>,
    pub(crate) integrated_at: u64,
    next_motion: u64,
}
impl Engine {
    pub fn new(layout: Arc<Layout>) -> Self {
        let mut engine = Self {
            presentation: Default::default(),
            layout,
            now: 0,
            error: None,
            stack: vec![0],
            held: BTreeSet::new(),
            between: BTreeSet::new(),
            acts: BTreeMap::new(),
            bound: BTreeMap::new(),
            inverted: BTreeSet::new(),
            pressed_at: BTreeMap::new(),
            order: 0,
            output: Output::default(),
            surfaces: BTreeMap::new(),
            gyro: Gyro::default(),
            trigger_values: BTreeMap::new(),
            integrated_at: 0,
            next_motion: 8,
        };
        engine.collect_inverted();
        engine.rebind(vec![0]);
        engine.drain();
        engine
    }
    pub fn stack_titles(&self) -> Vec<&str> {
        self.stack
            .iter()
            .map(|i| self.layout.layers[*i].title.as_str())
            .collect()
    }
    pub fn mode(&self) -> &str {
        self.stack_titles()
            .into_iter()
            .rev()
            .find(|t| {
                matches!(
                    *t,
                    "Gyro" | "Steering" | "Cursor Gyro" | "Menu Keys" | "Gamepad"
                )
            })
            .unwrap_or("Base")
    }
    pub fn advance_to(&mut self, end: u64) {
        if self.error.is_some() || end < self.now {
            return;
        }
        // Bound work across deadlines too; a malformed repeat cannot freeze WASM.
        for _ in 0..100_000 {
            let motion = self
                .surfaces
                .iter()
                .any(|(s, v)| s.contains("joystick") && v.position != [0.; 2]);
            let due = self
                .next_deadline()
                .into_iter()
                .chain(motion.then_some(self.next_motion))
                .min();
            let Some(due) = due.filter(|d| *d <= end) else {
                self.now = end;
                return;
            };
            let due = due.max(self.now);
            self.integrate_sticks(due);
            self.now = due;
            self.next_motion = (due / 8 + 1) * 8;
            self.drain();
            if self.error.is_some() {
                return;
            }
        }
        self.error = Some("Layout exceeded the scheduled event limit".into());
    }
    pub fn next_deadline(&self) -> Option<u64> {
        self.acts.values().filter_map(|a| a.due).min()
    }
    pub(crate) fn drain(&mut self) {
        for _ in 0..10_000 {
            let next = self
                .acts
                .iter()
                .filter(|(_, a)| a.due.is_some_and(|d| d <= self.now))
                .min_by_key(|(_, a)| (a.due, a.order))
                .map(|(id, _)| *id);
            let Some(id) = next else {
                self.sync_outputs();
                return;
            };
            self.fire(id);
        }
        self.error = Some(format!("Layout did not settle at {} ms", self.now));
        self.acts.clear();
        self.sync_outputs();
    }
    pub(crate) fn note(&mut self, kind: &str, detail: String) {
        self.output.note(self.now, kind, detail);
    }
    pub(crate) fn sync_outputs(&mut self) {
        let down: BTreeSet<_> = self
            .acts
            .values()
            .flat_map(|a| a.down.iter().cloned())
            .collect();
        for output in self
            .output
            .down
            .difference(&down)
            .cloned()
            .collect::<Vec<_>>()
        {
            self.note("up", output);
        }
        self.output.down = down;
        self.refresh_gyro_gate();
    }
    pub fn snapshot(&self) -> serde_json::Value {
        serde_json::json!({
            "layout": self.layout.label(), "tag": self.layout.tag, "sha256": self.layout.sha256,
            "now": self.now, "mode": self.mode(), "stack": self.stack_titles(), "held": self.held,
            "output": self.output, "gyro": self.gyro_status(), "surfaces": self.surfaces,
            "timers": self.timers(), "error": self.error, "lifecycle": self.lifecycle(),
        })
    }
    pub(crate) fn timers(&self) -> Vec<serde_json::Value> {
        self.acts
            .values()
            .filter(|a| a.first && a.due.is_some_and(|d| d > self.now))
            .map(|a| {
                serde_json::json!({"control":a.binding.control,
                "layer":self.layout.layers[a.binding.layer].title,
                "group":self.layout.groups[a.binding.group].id, "start":a.began,
                "due":a.due, "commands":a.binding.entry.commands})
            })
            .collect()
    }
}
