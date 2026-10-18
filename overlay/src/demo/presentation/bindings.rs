use super::{Engine, Entry, Operation};
use crate::demo::activators::select_chords;

impl Engine {
    pub(super) fn display_entries(&self, control: &str) -> Vec<Entry> {
        let mut stack = self.stack.clone();
        let mut held = self.held.clone();
        held.insert(control.into());
        let mut exposed = false;
        loop {
            let (_, mut bindings) = self.binding_on(&stack, control, true);
            bindings.retain(|b| b.entry.kind != "release");
            let bindings = select_chords(bindings, &held, exposed);
            // Cancellation is an immediate exit, not an empty binding. Resolve
            // the newly exposed input without executing commands or timers.
            let exits = !bindings.is_empty() && bindings.iter().all(|b| {
                !b.inverted && b.entry.value("delay_start") == 0
                    && matches!(b.entry.kind.as_str(), "Full_Press" | "Start_Press" | "chord")
                    && b.entry.commands.iter().all(|op| matches!(op, Operation::RemoveLayer { .. }))
                    && b.entry.commands.iter().any(|op| {
                        matches!(op, Operation::RemoveLayer {target, ..} if *target == b.layer && *target != 0)
                    })
            });
            if !exits {
                return bindings.into_iter().map(|b| b.entry).collect();
            }
            for op in bindings.iter().flat_map(|b| &b.entry.commands) {
                if let Operation::RemoveLayer { target, .. } = op
                    && *target != 0
                {
                    stack.retain(|layer| layer != target);
                }
            }
            // Each pass removes its defining layer, so the walk is bounded by
            // the active stack and never traverses unrelated gesture branches.
            exposed = true;
        }
    }
}
