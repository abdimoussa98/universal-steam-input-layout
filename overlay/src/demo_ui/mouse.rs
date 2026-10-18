use super::DemoApp;
use crate::demo::Input;
use eframe::egui::{self, Event, PointerButton, Pos2, Rect};

#[derive(Clone)]
pub(super) enum Target {
    Button(String),
    Surface(String),
    Gyro,
}
#[derive(Clone)]
pub(super) struct Hit {
    pub target: Target,
    pub rect: Rect,
    pub angle: f32,
    pub clip: Rect,
    pub layer: egui::LayerId,
}
impl Hit {
    fn local(&self, pos: Pos2) -> egui::Vec2 {
        let delta = pos - self.rect.center();
        egui::vec2(
            delta.x * self.angle.cos() + delta.y * self.angle.sin(),
            -delta.x * self.angle.sin() + delta.y * self.angle.cos(),
        ) / (self.rect.size() * 0.5)
    }
    fn contains(&self, pos: Pos2, ctx: &egui::Context) -> bool {
        self.local(pos).abs().max_elem() <= 1.
            && self.clip.contains(pos)
            && ctx
                .layer_id_at(pos)
                .is_none_or(|layer| layer == self.layer || layer.order == egui::Order::Tooltip)
    }
}
pub(super) struct Capture {
    pub hit: Hit,
    pub last: Pos2,
    pub at: u64,
}
impl DemoApp {
    pub(super) fn mouse(&mut self, ctx: &egui::Context) {
        if self.session.paused || self.session.replaying {
            self.capture = None;
            return;
        }
        for event in ctx.input(|i| i.events.clone()) {
            match event {
                Event::PointerButton {
                    pos,
                    button: PointerButton::Primary,
                    pressed: true,
                    ..
                } => self.begin(pos, ctx),
                Event::PointerButton {
                    pos,
                    button: PointerButton::Primary,
                    pressed: false,
                    ..
                } => self.finish(pos),
                Event::PointerButton {
                    pos,
                    button: PointerButton::Secondary,
                    pressed: true,
                    ..
                } => self.pin(pos, ctx),
                Event::PointerMoved(pos) => self.movement(pos),
                Event::PointerGone if !ctx.input(|i| i.pointer.primary_down()) => {
                    self.finish(Pos2::ZERO);
                }
                _ => {}
            }
        }
    }
    fn begin(&mut self, pos: Pos2, ctx: &egui::Context) {
        let Some(hit) = self
            .hits
            .iter()
            .rev()
            .find(|h| h.contains(pos, ctx))
            .cloned()
        else {
            return;
        };
        match &hit.target {
            Target::Button(control) => self.virtual_button(control, true),
            Target::Surface(source) => self.send_surface(source.clone(), &hit, pos, true),
            Target::Gyro => {}
        }
        self.capture = Some(Capture {
            hit,
            last: pos,
            at: self.session.engine.now,
        });
    }
    fn finish(&mut self, pos: Pos2) {
        let Some(capture) = self.capture.take() else {
            return;
        };
        match &capture.hit.target {
            Target::Button(control) => {
                if !self.pinned.contains(control) {
                    self.virtual_button(control, false);
                }
            }
            Target::Surface(source) => self.send_surface(source.clone(), &capture.hit, pos, false),
            Target::Gyro => {}
        }
    }
    fn pin(&mut self, pos: Pos2, ctx: &egui::Context) {
        let Some(Target::Button(control)) = self
            .hits
            .iter()
            .rev()
            .find(|h| h.contains(pos, ctx))
            .map(|h| h.target.clone())
        else {
            return;
        };
        let down = if self.pinned.remove(&control) {
            false
        } else {
            self.pinned.insert(control.clone());
            true
        };
        self.virtual_button(&control, down);
    }
    fn virtual_button(&mut self, control: &str, down: bool) {
        if let Some(source) = control
            .strip_suffix("/edge")
            .filter(|s| s.ends_with("_trigger"))
        {
            let value = if down { 1. } else { 0. };
            self.triggers[usize::from(source == "right_trigger")] = value;
            self.session.input(Input::Trigger {
                source: source.into(),
                value,
            });
        } else {
            self.session.input(Input::Button {
                control: control.into(),
                down,
            });
        }
    }
    fn movement(&mut self, pos: Pos2) {
        let Some(mut capture) = self.capture.take() else {
            return;
        };
        match &capture.hit.target {
            Target::Surface(source) => self.send_surface(source.clone(), &capture.hit, pos, true),
            Target::Gyro => {
                let delta = pos - capture.last;
                let scale = if self.fine_motion { 0.02 } else { 0.35 };
                self.session.input(Input::Motion {
                    degrees: [f64::from(-delta.y) * scale, f64::from(delta.x) * scale, 0.],
                    duration_ms: self.session.engine.now.saturating_sub(capture.at).max(1),
                });
            }
            Target::Button(_) => {}
        }
        capture.last = pos;
        capture.at = self.session.engine.now;
        self.capture = Some(capture);
    }
    fn send_surface(&mut self, source: String, hit: &Hit, pos: Pos2, down: bool) {
        let stick = source.contains("joystick");
        let position = if !down && stick {
            [0.; 2]
        } else {
            let p = hit.local(pos);
            [f64::from(p.x.clamp(-1., 1.)), f64::from(p.y.clamp(-1., 1.))]
        };
        let touch = down || (stick && self.pinned.contains(&format!("{source}/touch")));
        let click = if stick {
            self.pinned.contains(&format!("{source}/click"))
        } else {
            down && self.pad_click
        };
        self.session.input(Input::Surface {
            source,
            position,
            touching: touch,
            click,
        });
    }
}
