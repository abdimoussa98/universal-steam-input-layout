use super::*;
use crate::demo_ui::mouse::Target;
use eframe::egui::{Align2, FontId, StrokeKind};

const CONTROLS: [(&str, &str, f32, f32, f32, f32); 16] = [
    ("A", "button_diamond/button_a", 735., 257., 48., 48.),
    ("B", "button_diamond/button_b", 779., 213., 48., 48.),
    ("X", "button_diamond/button_x", 691., 213., 48., 48.),
    ("Y", "button_diamond/button_y", 735., 169., 48., 48.),
    ("Select", "switch/button_menu", 364., 145., 136., 38.),
    ("Start", "switch/button_escape", 636., 145., 136., 38.),
    ("Up", "dpad/dpad_north", 264., 173., 44., 44.),
    ("Right", "dpad/dpad_east", 304., 213., 44., 44.),
    ("Down", "dpad/dpad_south", 264., 253., 44., 44.),
    ("Left", "dpad/dpad_west", 224., 213., 44., 44.),
    ("L3", "joystick/click", 385., 257., 92., 92.),
    ("R3", "right_joystick/click", 615., 257., 92., 92.),
    ("L1", "switch/left_bumper", 280., 81., 244., 40.),
    ("R1", "switch/right_bumper", 720., 81., 244., 40.),
    ("L2", "left_trigger/edge", 280., 32., 244., 40.),
    ("R2", "right_trigger/edge", 720., 32., 244., 40.),
];
impl Diagram<'_> {
    pub(super) fn controls(&mut self) {
        for (label, control, mut x, mut y, w, h) in CONTROLS {
            match self.app.session.engine.layout.controller.as_str() {
                "neptune" if label == "L3" => {
                    x = 340.;
                    y = 200.;
                }
                "neptune" if label == "R3" => {
                    x = 660.;
                    y = 200.;
                }
                "neptune" if matches!(label, "Up" | "Right" | "Down" | "Left") => {
                    x -= 80.;
                    y += 35.;
                }
                "neptune" if matches!(label, "A" | "B" | "X" | "Y") => {
                    x += 80.;
                    y += 35.;
                }
                "dse" if label == "Select" => {
                    x = 325.;
                    y = 150.;
                }
                "dse" if label == "Start" => {
                    x = 675.;
                    y = 150.;
                }
                "dse" if label == "L3" || label == "R3" => {
                    y = 380.;
                }
                _ => {}
            }
            let rect = self.box_at(x, y, w, h);
            if label == "L3" || label == "R3" {
                self.stick(control, rect);
            } else {
                self.button(label, control, rect);
            }
        }
    }
    fn button(&mut self, name: &str, control: &str, rect: Rect) {
        let engine = &self.app.session.engine;
        let down = engine.held.contains(control);
        let color = if down { ACCENT } else { EDGE };
        let p = self.ui.painter();
        let fill = if down {
            Color32::from_rgb(36, 70, 61)
        } else {
            DARK
        };
        let stroke = Stroke::new(if down { 1.8_f32 } else { 1. }, color);
        if matches!(name, "A" | "B" | "X" | "Y") {
            p.circle(rect.center(), rect.width() * 0.5, fill, stroke);
        } else {
            p.rect(rect, 9. * self.scale, fill, stroke, StrokeKind::Inside);
        }
        let binding = if name.ends_with(" touch") {
            "Touch".into()
        } else {
            engine.display_label(control)
        };
        let font = if rect.width() < 50. { 20. } else { 16. } * self.scale;
        let measured = p
            .layout_no_wrap(binding.clone(), FontId::proportional(font), Color32::WHITE)
            .size()
            .x;
        let font = font * ((rect.width() - 6.) / measured.max(1.)).min(1.);
        p.with_clip_rect(rect.intersect(self.ui.clip_rect())).text(
            rect.center(),
            Align2::CENTER_CENTER,
            &binding,
            FontId::proportional(font),
            Color32::WHITE,
        );
        if let Some(source) = control
            .strip_suffix("/edge")
            .filter(|s| s.ends_with("_trigger"))
        {
            let amount = engine.trigger_values.get(source).copied().unwrap_or(0.) as f32;
            let start = rect.left_bottom() + vec2(6., -3.);
            p.line_segment(
                [start, start + vec2(rect.width() - 12., 0.)],
                Stroke::new(1.0_f32, EDGE),
            );
            p.line_segment(
                [start, start + vec2((rect.width() - 12.) * amount, 0.)],
                Stroke::new(2.0_f32, ACCENT),
            );
        }
        self.ui
            .interact(rect, self.ui.id().with(control), Sense::hover())
            .on_hover_text(format!(
                "{name} · {binding}\nHold to press; right-click to latch."
            ));
        self.app
            .hit(self.ui, control, Target::Button(control.into()), (rect, 0.));
    }
    fn stick(&mut self, control: &str, rect: Rect) {
        let source = control.strip_suffix("/click").unwrap();
        let p = self.ui.painter();
        p.circle(
            rect.center(),
            rect.width() / 2.,
            DARK,
            Stroke::new(1.0_f32, EDGE),
        );
        p.circle_stroke(
            rect.center(),
            rect.width() * 0.43,
            Stroke::new(1.0_f32, EDGE),
        );
        let name = if source == "joystick" { "L3" } else { "R3" };
        let label = self.app.session.engine.display_label(control);
        let click = Rect::from_center_size(
            rect.center() - vec2(0., rect.height() * 0.15),
            vec2(rect.width() * 0.64, rect.height() * 0.38),
        );
        p.text(
            click.center(),
            Align2::CENTER_CENTER,
            &label,
            FontId::proportional(
                (rect.width() / (label.len().max(2) as f32 * 0.65)).min(20. * self.scale),
            ),
            Color32::WHITE,
        );
        self.app.hit(
            self.ui,
            control,
            Target::Button(control.into()),
            (click, 0.),
        );
        self.stick_travel(source, rect);
        self.ui
            .interact(rect, self.ui.id().with(name), Sense::hover())
            .on_hover_text(format!(
                "{name} · {label}\nClick the label to press; drag the lower knob to move."
            ));
        self.stick_touch(source, rect);
    }
    fn stick_travel(&mut self, source: &str, rect: Rect) {
        let p = self.ui.painter();
        let travel = Rect::from_center_size(
            rect.center() + vec2(0., rect.height() * 0.22),
            vec2(rect.width() * 0.38, rect.height() * 0.38),
        );
        let position = self
            .app
            .session
            .engine
            .surfaces
            .get(source)
            .map_or([0.; 2], |s| s.position);
        p.circle(
            travel.center(),
            travel.width() / 2.,
            DARK,
            Stroke::new(1.0_f32, EDGE),
        );
        p.circle_filled(
            travel.center() + vec2(position[0] as f32, position[1] as f32) * travel.width() * 0.3,
            2.,
            ACCENT,
        );
        self.app.hit(
            self.ui,
            source,
            Target::Surface(source.into()),
            (travel, 0.),
        );
    }
    fn stick_touch(&mut self, source: &str, rect: Rect) {
        if self.app.session.engine.layout.controller != "dse" {
            let touch = format!("{source}/touch");
            let area = Rect::from_center_size(
                rect.center() + vec2(0., rect.height() * 0.7),
                vec2(rect.width(), 18.),
            );
            self.button(
                if source == "joystick" {
                    "LS touch"
                } else {
                    "RS touch"
                },
                &touch,
                area,
            );
        }
    }
    pub(super) fn extras(&mut self) {
        for (name, control, x) in [
            ("L4", "button_back_left_upper", 218.),
            ("L5", "button_back_left", 218.),
            ("R4", "button_back_right_upper", 782.),
            ("R5", "button_back_right", 782.),
        ] {
            let upper = name.ends_with('4');
            let dse_fn = self.app.session.engine.layout.controller == "dse" && upper;
            let (x, y) = if dse_fn {
                (if name.starts_with('L') { 385. } else { 615. }, 455.)
            } else {
                (x, if upper { 530. } else { 580. })
            };
            let rect = self.box_at(x, y, 100., 34.);
            self.button(name, &format!("switch/{control}"), rect);
        }
        if self.app.session.engine.layout.controller == "dse" {
            self.button(
                "Mute",
                "switch/button_capture",
                self.box_at(500., 300., 100., 30.),
            );
        }
        self.ui.painter().circle(
            self.at(500., 245.),
            24. * self.scale,
            DARK,
            Stroke::new(1.0_f32, EDGE),
        );
    }
}
