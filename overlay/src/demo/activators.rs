use super::{Act, Binding, Engine, Operation, Phase};
use std::collections::BTreeSet;

impl Engine {
    pub(crate) fn end(&mut self, control: &str, phase: Phase, handover: bool) {
        let ids: Vec<_> = self
            .acts
            .iter()
            .filter(|(_, a)| a.binding.control == control && a.phase == phase)
            .map(|(id, _)| *id)
            .collect();
        let mut removed = vec![];
        for id in ids {
            let act = self.acts.remove(&id).unwrap();
            if !handover {
                for target in act.holds {
                    if target != 0 && self.stack.contains(&target) {
                        self.stack.retain(|v| *v != target);
                        removed.push(target);
                        self.note("remove", self.layout.layers[target].title.clone());
                    }
                }
            }
        }
        self.bound.remove(&(control.into(), phase));
        if !removed.is_empty() {
            self.reset_delays(&removed, None);
        }
        if !handover {
            self.sync_outputs();
        }
    }
    pub(crate) fn establish(&mut self, control: &str, phase: Phase, how: &str) {
        let (answer, mut found) = self.binding(control);
        self.bound.insert((control.into(), phase), answer);
        self.filter_soft(control, phase, &mut found);
        found.retain(|b| self.analog_soft_active(b));
        found.retain(|e| e.entry.kind != "release" && e.inverted == (phase == Phase::Up));
        if phase == Phase::Down {
            found = self.native(control, how, found);
        }
        let mut chords: Vec<_> = found
            .iter()
            .filter(|b| b.entry.kind == "chord")
            .filter(|b| {
                b.entry.condition.as_ref().is_some_and(|c| {
                    if b.inverted_chord() {
                        how != "exposed" && !c.any_held(&self.held)
                    } else {
                        c.satisfied(&self.held)
                    }
                })
            })
            .cloned()
            .collect();
        if chords.iter().any(|b| !b.entry.interruptible()) {
            chords.retain(|b| !b.entry.interruptible());
        }
        let has_chords = !chords.is_empty();
        chords.extend(
            found
                .into_iter()
                .filter(|b| b.entry.kind != "chord" && !(has_chords && b.entry.interruptible())),
        );
        chords.sort_by_key(|b| b.index);
        for binding in chords {
            self.arm(binding, phase, how, None);
        }
    }
    fn filter_soft(&self, control: &str, phase: Phase, found: &mut Vec<Binding>) {
        let between = self.between.contains(control);
        if between {
            let inner = found
                .iter()
                .filter(|b| b.entry.kind == "Soft_Press" && b.inverted)
                .map(|b| b.entry.value("activation_threshold"))
                .max();
            found.retain(|b| {
                !(b.entry.kind == "Soft_Press"
                    && !b.inverted
                    && inner.is_some_and(|v| b.entry.value("activation_threshold") >= v))
            });
        }
        if found.iter().any(|b| {
            b.entry.kind == "Soft_Press"
                && !b.entry.interruptible()
                && (between || b.inverted == (phase == Phase::Up))
        }) {
            found.retain(|b| b.entry.kind != "Soft_Press" || !b.entry.interruptible());
        }
    }
    fn native(&mut self, control: &str, how: &str, found: Vec<Binding>) -> Vec<Binding> {
        let doubles: Vec<_> = found
            .iter()
            .filter(|b| b.entry.kind == "Double_Press")
            .cloned()
            .collect();
        let longs: Vec<_> = found
            .iter()
            .filter(|b| b.entry.kind == "Long_Press")
            .cloned()
            .collect();
        if doubles.is_empty() && longs.is_empty() {
            return found;
        }
        let window = doubles
            .iter()
            .map(|b| b.entry.value("double_tap_time"))
            .max()
            .unwrap_or(200);
        self.acts
            .retain(|_, a| !(a.binding.control == control && a.phase == Phase::Tap));
        if how == "pressed"
            && !doubles.is_empty()
            && self
                .pressed_at
                .get(control)
                .is_some_and(|t| self.now - t <= window)
        {
            self.pressed_at.remove(control);
            for b in doubles {
                self.arm(b, Phase::Down, how, None);
            }
            return vec![];
        }
        if how == "pressed" {
            self.pressed_at.insert(control.into(), self.now);
        }
        for b in longs {
            let delay = b.entry.value("long_press_time");
            self.arm(b, Phase::Down, how, Some(delay));
        }
        found
            .into_iter()
            .filter(|b| !matches!(b.entry.kind.as_str(), "Long_Press" | "Double_Press"))
            .filter_map(|b| {
                if b.entry.kind == "Full_Press" && b.entry.interruptible() && !doubles.is_empty() {
                    self.arm(b, Phase::Down, how, Some(window));
                    None
                } else {
                    Some(b)
                }
            })
            .collect()
    }
    fn arm(&mut self, binding: Binding, phase: Phase, how: &str, delay: Option<u64>) {
        let delay = delay.unwrap_or_else(|| binding.entry.value("delay_start"));
        let edge = how == "pressed" || how == "exposed";
        let allow_ops = edge || delay > 0 || (binding.entry.repeat().is_some() && how == "landed");
        self.order += 1;
        self.acts.insert(
            self.order,
            Act {
                binding,
                phase,
                due: Some(self.now + delay),
                began: self.now,
                first: true,
                order: self.order,
                down: BTreeSet::new(),
                holds: BTreeSet::new(),
                allow_ops,
            },
        );
    }
    pub(crate) fn fire(&mut self, id: u64) {
        let mut act = self.acts[&id].clone();
        if act.phase == Phase::Tap {
            self.acts.remove(&id);
            self.execute(&act.binding, None, true, true);
            return;
        }
        if act.binding.entry.kind == "Long_Press" && act.first {
            self.acts.retain(|_, a| {
                !(a.binding.control == act.binding.control
                    && a.phase == act.phase
                    && a.binding.entry.kind == "Full_Press"
                    && a.binding.entry.interruptible())
            });
        }
        act.due = act.binding.entry.repeat().map(|r| self.now + r);
        for output in act
            .binding
            .entry
            .commands
            .iter()
            .filter_map(Operation::output)
        {
            if act.first {
                act.down.insert(output.clone());
                if self.output.down.insert(output.clone()) {
                    self.note("down", output);
                }
            } else {
                self.note("tap", output);
            }
        }
        act.first = false;
        let allow = act.allow_ops;
        act.allow_ops = true;
        self.acts.insert(id, act.clone());
        self.execute(&act.binding, Some(id), false, allow);
    }
    pub(crate) fn reset_delays(&mut self, removed: &[usize], skip: Option<u64>) {
        for (id, act) in &mut self.acts {
            let delay = act.binding.entry.value("delay_start");
            if delay == 0 || skip == Some(*id) {
                continue;
            }
            let target = act.binding.entry.commands.iter().any(
                |op| matches!(op, Operation::AddLayer {target, ..} if removed.contains(target)),
            );
            if act.first || (act.due.is_none() && target) {
                act.began = self.now;
                act.due = Some(self.now + delay);
                if !act.first {
                    act.first = true;
                    act.down.clear();
                }
            }
        }
    }
}
