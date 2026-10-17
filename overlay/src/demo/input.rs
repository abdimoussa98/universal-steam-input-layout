use super::{Engine, Phase};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Input {
    Button {
        control: String,
        down: bool,
    },
    Surface {
        source: String,
        position: [f64; 2],
        touching: bool,
        click: bool,
    },
    Trigger {
        source: String,
        value: f64,
    },
    /// Angular displacement in degrees, not a pose delta inferred on repaint.
    Motion {
        degrees: [f64; 3],
        duration_ms: u64,
    },
    Recenter,
}
impl Engine {
    pub fn input(&mut self, input: &Input) {
        if self.error.is_some() {
            return;
        }
        self.integrate_sticks(self.now);
        match input {
            Input::Button { control, down } => self.button(control, *down, false),
            Input::Surface {
                source,
                position,
                touching,
                click,
            } if position.iter().all(|v| v.is_finite()) => self.surface(
                source,
                position.map(|v| v.clamp(-1., 1.)),
                *touching,
                *click,
            ),
            Input::Trigger { source, value } if value.is_finite() => {
                self.trigger(source, value.clamp(0., 1.))
            }
            Input::Motion {
                degrees,
                duration_ms,
            } if degrees.iter().all(|v| v.is_finite()) => {
                self.motion(degrees.map(|v| v.clamp(-360., 360.)), *duration_ms)
            }
            Input::Recenter => self.gyro.recenter(),
            _ => {}
        }
        // Mode changes must update axis indicators immediately, even at rest.
        self.integrate_sticks(self.now);
    }
    pub(crate) fn button(&mut self, control: &str, down: bool, between: bool) {
        if self.held.contains(control) == down && self.between.contains(control) == between {
            return;
        }
        if self.held.contains(control) {
            self.release(control);
        }
        if down {
            self.press(control, between);
        }
    }
    fn press(&mut self, control: &str, between: bool) {
        self.note("press", control.into());
        if !between {
            self.end(control, Phase::Up, false);
            self.sync_outputs();
        }
        self.held.insert(control.into());
        if between {
            self.between.insert(control.into());
        }
        self.acts.retain(|_, a| {
            !(a.binding.inverted_chord()
                && a.binding
                    .entry
                    .condition
                    .as_ref()
                    .is_some_and(|c| c.contains(control)))
        });
        if between && !self.bound.contains_key(&(control.into(), Phase::Up)) {
            self.establish(control, Phase::Up, "pressed");
        }
        self.establish(control, Phase::Down, "pressed");
        self.rebind(self.stack.clone());
        self.drain();
    }
    fn release(&mut self, control: &str) {
        self.note("release", control.into());
        let (_, found) = self.binding(control);
        let native = found.iter().any(|b| b.entry.kind == "Double_Press");
        let waiting: Vec<_> = self
            .acts
            .values()
            .filter(|a| {
                a.binding.control == control
                    && a.phase == Phase::Down
                    && a.first
                    && a.binding.entry.kind == "Full_Press"
                    && native
            })
            .cloned()
            .collect();
        self.end(control, Phase::Down, false);
        for mut act in waiting {
            act.phase = Phase::Tap;
            self.acts.insert(act.order, act);
        }
        self.held.remove(control);
        let was_between = self.between.remove(control);
        self.sync_outputs();
        if self.inverted.contains(control)
            && !(was_between && self.bound.contains_key(&(control.into(), Phase::Up)))
        {
            self.establish(control, Phase::Up, "pressed");
        }
        for b in found
            .iter()
            .filter(|b| b.entry.kind == "release" && !b.inverted)
        {
            self.execute(b, None, true, true);
        }
        self.rebind(self.stack.clone());
        self.drain();
    }
}
