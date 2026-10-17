use super::{Binding, Engine, Phase, Settings};

impl Engine {
    pub(crate) fn group_at(&self, layer: usize, source: &str) -> Option<usize> {
        for control in &self.held {
            let (owner, entries) = self.binding_unshifted(control);
            if owner.map(|o| o.0) != Some(layer) {
                continue;
            }
            for binding in entries {
                if binding.entry.kind != "Full_Press" {
                    continue;
                }
                for op in binding.entry.commands {
                    if let super::Operation::ModeShift {
                        source: target,
                        target: gid,
                    } = op
                        && target == source
                        && !control.starts_with(&format!("{source}/"))
                    {
                        return Some(gid);
                    }
                }
            }
        }
        self.layout.layers[layer].sources.get(source).copied()
    }
    fn resolve_binding(
        &self,
        control: &str,
        shifted: bool,
    ) -> (Option<(usize, usize)>, Vec<Binding>) {
        let Some((source, name)) = control.split_once('/') else {
            return (None, vec![]);
        };
        let mut mode = None;
        let mut top = None;
        for &layer in self.stack.iter().rev() {
            let gid = if shifted {
                self.group_at(layer, source)
            } else {
                self.layout.layers[layer].sources.get(source).copied()
            };
            let Some(gid) = gid else {
                continue;
            };
            let group = &self.layout.groups[gid];
            if group.mode == "disabled" {
                return (Some((layer, gid)), vec![]);
            }
            if mode.is_none() {
                mode = Some(&group.mode);
                top = Some((layer, gid));
            }
            if mode != Some(&group.mode) {
                return (top, vec![]);
            }
            if group.inputs.contains_key(name) {
                return (Some((layer, gid)), self.entries_of(layer, gid, control));
            }
        }
        (None, vec![])
    }
    pub(crate) fn binding_unshifted(&self, c: &str) -> (Option<(usize, usize)>, Vec<Binding>) {
        self.resolve_binding(c, false)
    }
    pub(crate) fn binding(&self, c: &str) -> (Option<(usize, usize)>, Vec<Binding>) {
        self.resolve_binding(c, true)
    }
    fn entries_of(&self, layer: usize, gid: usize, control: &str) -> Vec<Binding> {
        let group = &self.layout.groups[gid];
        let name = control.split_once('/').unwrap().1;
        let ring = name == "edge"
            && group
                .settings
                .get("edge_binding_invert")
                .is_some_and(|v| v == "1");
        group
            .inputs
            .get(name)
            .into_iter()
            .flatten()
            .enumerate()
            .map(|(index, e)| {
                let own = e.flag("edge_binding_invert");
                let inverted = if e.kind == "Soft_Press" {
                    own
                } else if e.kind == "chord" && own {
                    !ring
                } else {
                    ring || own
                };
                Binding {
                    control: control.into(),
                    layer,
                    group: gid,
                    index,
                    entry: e.clone(),
                    inverted,
                }
            })
            .collect()
    }
    pub(crate) fn collect_inverted(&mut self) {
        for (layer, data) in self.layout.layers.iter().enumerate() {
            for (source, gid) in &data.sources {
                for name in self.layout.groups[*gid].inputs.keys() {
                    let control = format!("{source}/{name}");
                    if self
                        .entries_of(layer, *gid, &control)
                        .iter()
                        .any(|e| e.inverted)
                    {
                        self.inverted.insert(control);
                    }
                }
            }
        }
    }
    pub(crate) fn effective(&self, source: &str) -> (String, Settings, Option<super::Condition>) {
        let mut mode = String::new();
        let mut settings = Settings::new();
        let mut condition = None;
        for &layer in self.stack.iter().rev() {
            let Some(gid) = self.group_at(layer, source) else {
                continue;
            };
            let group = &self.layout.groups[gid];
            if mode.is_empty() {
                mode = group.mode.clone();
            }
            if group.mode != mode {
                break;
            }
            for (key, value) in &group.settings {
                settings.entry(key.clone()).or_insert(value.clone());
            }
            if condition.is_none() {
                condition = group.condition.clone();
            }
        }
        (mode, settings, condition)
    }
    pub(crate) fn rebind(&mut self, before: Vec<usize>) {
        let cancelled: Vec<_> = self
            .acts
            .iter()
            .filter(|(_, a)| {
                a.phase == Phase::Tap
                    && self.binding(&a.binding.control).0.map(|b| b.0) != Some(a.binding.layer)
            })
            .map(|(id, _)| *id)
            .collect();
        for id in cancelled {
            self.acts.remove(&id);
        }
        let mut live: std::collections::BTreeSet<_> =
            self.held.iter().map(|c| (c.clone(), Phase::Down)).collect();
        live.extend(
            self.inverted
                .iter()
                .filter(|c| !self.held.contains(*c) || self.between.contains(*c))
                .map(|c| (c.clone(), Phase::Up)),
        );
        for &layer in &self.stack {
            for (source, gid) in &self.layout.layers[layer].sources {
                if self.layout.groups[*gid]
                    .inputs
                    .contains_key("always_on_action")
                {
                    live.insert((format!("{source}/always_on_action"), Phase::Down));
                }
            }
        }
        for (c, p) in self
            .bound
            .keys()
            .filter(|k| !live.contains(*k))
            .cloned()
            .collect::<Vec<_>>()
        {
            self.end(&c, p, false);
        }
        for (c, p) in live {
            let answer = self.binding(&c).0;
            if self.bound.get(&(c.clone(), p)) == Some(&answer) {
                continue;
            }
            self.end(&c, p, true);
            let how = if c.ends_with("/always_on_action") {
                "pressed"
            } else if answer.is_some_and(|a| before.contains(&a.0)) {
                "exposed"
            } else {
                "landed"
            };
            self.establish(&c, p, how);
        }
    }
    pub fn label(&self, control: &str) -> String {
        let (_, entries) = self.binding(control);
        let labels: std::collections::BTreeSet<_> = entries
            .iter()
            .flat_map(|b| &b.entry.commands)
            .filter_map(|c| {
                c.output().or_else(|| match c {
                    super::Operation::MouseWheel { value } => Some(value.clone()),
                    _ => None,
                })
            })
            .collect();
        if labels.is_empty() {
            let gestures: std::collections::BTreeSet<_> = entries
                .iter()
                .flat_map(|b| &b.entry.commands)
                .filter_map(|c| match c {
                    super::Operation::AddLayer { target, .. }
                    | super::Operation::HoldLayer { target, .. } => {
                        Some(self.layout.layers[*target].title.as_str())
                    }
                    _ => None,
                })
                .collect();
            if gestures.is_empty() {
                "—".into()
            } else {
                gestures.into_iter().collect::<Vec<_>>().join(" / ")
            }
        } else {
            labels.into_iter().collect::<Vec<_>>().join(" / ")
        }
    }
}
