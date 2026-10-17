use super::{Binding, Engine, Operation};

impl Engine {
    pub(crate) fn execute(
        &mut self,
        binding: &Binding,
        act: Option<u64>,
        tap: bool,
        commands: bool,
    ) {
        let before = self.stack.clone();
        let mut removed = vec![];
        let mut changed = false;
        for op in &binding.entry.commands {
            if let Operation::MouseWheel { value } = op {
                self.note("tap", format!("mouse_wheel {value}"));
            }
            if !commands {
                continue;
            }
            if tap && let Some(output) = op.output() {
                self.note("tap", output);
            }
            match op {
                Operation::AddLayer { target, beep } | Operation::HoldLayer { target, beep } => {
                    if !self.stack.contains(target) {
                        self.stack.push(*target);
                        self.note("add", self.layout.layers[*target].title.clone());
                    }
                    if matches!(op, Operation::HoldLayer { .. })
                        && let Some(a) = act.and_then(|id| self.acts.get_mut(&id))
                    {
                        a.holds.insert(*target);
                    }
                    if *beep {
                        self.note("beep", self.layout.layers[*target].title.clone());
                    }
                    changed = true;
                }
                Operation::RemoveLayer { target, beep } => {
                    removed.push(*target);
                    if *target != 0 && self.stack.contains(target) {
                        self.stack.retain(|v| v != target);
                        self.note("remove", self.layout.layers[*target].title.clone());
                    }
                    if *beep {
                        self.note("beep", self.layout.layers[*target].title.clone());
                    }
                    changed = true;
                }
                _ => {}
            }
        }
        if commands && binding.entry.value("haptic_intensity") > 0 {
            self.note("haptic", binding.control.clone());
        }
        if !removed.is_empty() {
            self.reset_delays(&removed, act);
        }
        if changed {
            self.rebind(before);
        }
    }
}
