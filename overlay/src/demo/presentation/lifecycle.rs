use super::{Engine, Entry, Layout, Operation, layer_label};
use crate::demo::Binding;
use serde::Serialize;
use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub(crate) enum LifecyclePhase {
    InitialHold,
    ReleaseWindow,
    SecondHold,
    Held,
    Covered,
}
impl LifecyclePhase {
    fn next(window: bool, hold: bool, previous: Option<&Lifecycle>) -> Self {
        if window {
            Self::ReleaseWindow
        } else if hold {
            if previous.is_some_and(|p| {
                matches!(
                    p.phase,
                    Self::ReleaseWindow | Self::SecondHold | Self::Covered
                )
            }) {
                Self::SecondHold
            } else {
                Self::InitialHold
            }
        } else if previous.is_some_and(|p| matches!(p.phase, Self::SecondHold | Self::Covered)) {
            Self::Covered
        } else {
            Self::Held
        }
    }

    #[cfg(feature = "ui")]
    pub fn label(self) -> &'static str {
        match self {
            Self::InitialHold => "Initial hold",
            Self::ReleaseWindow => "Release window",
            Self::SecondHold => "Second hold",
            Self::Held => "Held",
            Self::Covered => "Tap cover",
        }
    }
}
#[derive(Clone, Serialize)]
pub(crate) struct Lifecycle {
    pub owners: Vec<String>,
    pub summary: String,
    pub phase: LifecyclePhase,
    pub started: u64,
    pub deadline: Option<u64>,
    pub output_at: Option<u64>,
    pub chain: u64,
    pub order: u64,
}
impl Lifecycle {
    #[cfg(any(feature = "ui", test))]
    pub fn progress(&self, now: u64) -> f32 {
        self.deadline
            .map_or(1., |due| {
                now.saturating_sub(self.started) as f32
                    / due.saturating_sub(self.started).max(1) as f32
            })
            .clamp(0., 1.)
    }
    #[cfg(any(feature = "ui", test))]
    pub fn remaining(&self, now: u64, scale: u8) -> Option<u64> {
        self.deadline
            .map(|d| d.saturating_sub(now) * u64::from(scale))
    }
}
#[derive(Default)]
pub(crate) struct Presentation {
    pub layers: BTreeMap<usize, Lifecycle>,
    serial: u64,
}
impl Layout {
    fn hold_entry(&self, layer: usize) -> Option<(String, &Entry)> {
        self.entries(layer).find(|(control, e)| {
            !control.ends_with("/always_on_action")
                && e.kind != "release"
                && e.value("delay_start") > 0
                && e.repeat().is_none()
                && e.commands
                    .iter()
                    .any(|op| matches!(op, Operation::AddLayer { .. }))
        })
    }
    fn window_duration(&self, layer: usize) -> Option<u64> {
        self.entries(layer)
            .filter(|(control, e)| {
                control.ends_with("/always_on_action")
                    && e.value("delay_start") > 0
                    && e.commands.iter().any(
                        |op| matches!(op, Operation::RemoveLayer {target, ..} if *target == layer),
                    )
            })
            .map(|(_, e)| e.value("delay_start"))
            .max()
    }
    fn releases_itself(&self, layer: usize, owners: &[String]) -> bool {
        self.entries(layer).any(|(c, e)| {
            owners.contains(&c)
                && e.kind == "release"
                && e.commands
                    .iter()
                    .any(|op| matches!(op, Operation::RemoveLayer {target, ..} if *target == layer))
        })
    }
    pub(super) fn gesture_summary(&self, layer: usize) -> Option<String> {
        let (owner, hold) = self.hold_entry(layer)?;
        let branch = self
            .entries(layer)
            .filter(|(c, e)| *c == owner && e.kind == "release")
            .flat_map(|(_, e)| &e.commands)
            .find_map(|op| match op {
                Operation::AddLayer { target, .. } => Some(*target),
                _ => None,
            });
        let tap = branch
            .map(|target| {
                let entries: Vec<_> = self
                    .entries(target)
                    .filter(|(c, _)| c.ends_with("/always_on_action"))
                    .map(|(_, e)| e.clone())
                    .collect();
                let label = self.entry_label(&entries, 2);
                if label.is_empty() {
                    let entries: Vec<_> = self
                        .entries(target)
                        .filter(|(c, _)| *c == owner)
                        .map(|(_, e)| e.clone())
                        .collect();
                    entries
                        .iter()
                        .filter(|e| e.kind != "release")
                        .flat_map(|e| &e.commands)
                        .filter_map(|op| match op {
                            Operation::AddLayer { target, .. } if *target != layer => Some(*target),
                            _ => None,
                        })
                        .next_back()
                        .map(|target| layer_label(&self.layers[target].title))
                        .unwrap_or_default()
                } else {
                    label
                }
            })
            .unwrap_or_else(|| self.entry_label(std::slice::from_ref(hold), 2));
        let name = layer_label(&self.layers[layer].title);
        if name == "Entry Point" {
            let hold = self.entry_label(std::slice::from_ref(hold), 2);
            return Some(format!("{tap} :: {hold}"));
        }
        Some(format!("{name} :: {tap}"))
    }
}
impl Engine {
    pub(crate) fn trace_layer(
        &mut self,
        binding: &Binding,
        target: usize,
        parent: Option<&Lifecycle>,
    ) {
        let hold = self.layout.hold_entry(target);
        let window = self.layout.window_duration(target);
        let mut owners = parent.map_or_else(|| vec![binding.control.clone()], |p| p.owners.clone());
        if let Some((control, entry)) = &hold {
            owners = vec![control.clone()];
            if let Some(condition) = &entry.condition {
                owners.extend(
                    condition
                        .groups
                        .iter()
                        .flatten()
                        .filter(|c| self.held.contains(*c))
                        .cloned(),
                );
            }
            owners.sort();
            owners.dedup();
        }
        let inherited = parent.filter(|_| self.layout.releases_itself(target, &owners));
        if hold.is_none() && window.is_none() && inherited.is_none() {
            return;
        }
        // Timed autonomous setup (for example gyro ramps) is not a user gesture.
        if parent.is_none() && hold.is_none() {
            return;
        }
        let previous = parent.filter(|p| p.owners == owners);
        let phase = LifecyclePhase::next(window.is_some(), hold.is_some(), previous);
        self.presentation.serial += 1;
        let serial = self.presentation.serial;
        let chain = previous.map_or(serial, |p| p.chain);
        let summary = previous
            .map(|p| p.summary.clone())
            .or_else(|| self.layout.gesture_summary(target))
            .unwrap_or_default();
        let trace = Lifecycle {
            owners,
            summary,
            phase,
            started: self.now,
            deadline: None,
            output_at: None,
            chain,
            order: serial,
        };
        if matches!(phase, LifecyclePhase::Held | LifecyclePhase::Covered) {
            for item in self
                .presentation
                .layers
                .values_mut()
                .filter(|t| t.chain == chain)
            {
                item.phase = phase;
            }
        }
        self.presentation.layers.insert(target, trace);
    }
    pub(crate) fn lifecycle(&self) -> Option<Lifecycle> {
        if self.error.is_some() {
            return None;
        }
        let mut chains: BTreeMap<u64, Lifecycle> = BTreeMap::new();
        for (&layer, trace) in &self.presentation.layers {
            if !self.stack.contains(&layer) {
                continue;
            }
            let mut trace = trace.clone();
            self.trace_deadlines(layer, &mut trace);
            if trace.deadline.is_none() && !trace.owners.iter().any(|c| self.held.contains(c)) {
                continue;
            }
            if chains
                .get(&trace.chain)
                .is_none_or(|old| old.order < trace.order)
            {
                chains.insert(trace.chain, trace);
            }
        }
        // A replacement output cannot steal an existing release-window rail.
        chains.into_values().max_by_key(|t| {
            (
                t.phase == LifecyclePhase::ReleaseWindow,
                t.owners.len(),
                t.order,
            )
        })
    }
    fn trace_deadlines(&self, layer: usize, trace: &mut Lifecycle) {
        if matches!(trace.phase, LifecyclePhase::Held | LifecyclePhase::Covered) {
            return;
        }
        let acts: Vec<_> = self
            .acts
            .values()
            .filter(|a| {
                a.binding.layer == layer
                    && a.first
                    && a.binding.entry.repeat().is_none()
                    && a.binding.entry.value("delay_start") > 0
            })
            .collect();
        let timer = acts
            .iter()
            .filter(|a| {
                a.binding.entry.commands.iter().any(|op| match op {
                    Operation::AddLayer { .. } => true,
                    Operation::RemoveLayer { target, .. } => *target == layer,
                    _ => false,
                })
            })
            .max_by_key(|a| a.due);
        if let Some(a) = timer {
            trace.started = a.began;
            trace.deadline = a.due;
        } else if trace.phase != LifecyclePhase::ReleaseWindow {
            trace.phase = LifecyclePhase::Held;
        }
        // Preserve the output marker after its activator fires.
        trace.output_at = self
            .layout
            .entries(layer)
            .filter(|(c, e)| {
                c.ends_with("/always_on_action")
                    && e.commands
                        .iter()
                        .any(|o| o.output().is_some() || matches!(o, Operation::MouseWheel { .. }))
            })
            .map(|(_, e)| trace.started + e.value("delay_start"))
            .min();
    }
}
