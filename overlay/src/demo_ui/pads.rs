use super::{ACCENT, BORDER, DemoApp, MUTED, mouse::Target};
use crate::demo::presentation::PadView;
use eframe::egui::{self, Align2, Color32, FontId, Pos2, Rect, Stroke, vec2};

#[derive(Clone, Copy)]
struct Geometry {
    rect: Rect,
    angle: f32,
}
impl Geometry {
    fn at(self, x: f32, y: f32) -> Pos2 {
        let d = vec2(x * self.rect.width(), y * self.rect.height()) * 0.5;
        self.rect.center()
            + vec2(
                d.x * self.angle.cos() - d.y * self.angle.sin(),
                d.x * self.angle.sin() + d.y * self.angle.cos(),
            )
    }
    fn outline(self) -> Vec<Pos2> {
        let mut points = vec![];
        for (cx, cy, start) in [
            (-0.76, -0.76, 180_f32),
            (0.76, -0.76, 270.),
            (0.76, 0.76, 0.),
            (-0.76, 0.76, 90.),
        ] {
            for i in 0..=8 {
                let a = (start + i as f32 * 90. / 8.).to_radians();
                points.push(self.at(cx + 0.24 * a.cos(), cy + 0.24 * a.sin()));
            }
        }
        points
    }
}
impl DemoApp {
    pub(super) fn pad_field(
        &mut self,
        ui: &egui::Ui,
        source: &str,
        rect: Rect,
        options: (f32, bool),
    ) {
        let (angle, diagram) = options;
        let geometry = Geometry { rect, angle };
        let view = self.session.engine.pad_view(source, self.pad_click);
        let state = self.session.engine.surfaces.get(source);
        let active = state.is_some_and(|s| s.touching);
        let painter = ui.painter();
        painter.add(egui::Shape::convex_polygon(
            geometry.outline(),
            Color32::from_rgb(21, 24, 29),
            Stroke::new(1.0_f32, if active { ACCENT } else { BORDER }),
        ));
        let radius = rect.width().min(rect.height()) * 0.5;
        let color = if self.pad_click {
            Color32::from_rgb(244, 191, 88)
        } else {
            BORDER
        };
        for fraction in [view.inner, view.outer] {
            painter.circle_stroke(
                rect.center(),
                radius * fraction,
                Stroke::new(1.5_f32, color),
            );
        }
        pad_labels(ui, geometry, &view);
        if !self.pad_click && (view.circular || view.mode == "scrollwheel") {
            for offset in [0., std::f32::consts::PI] {
                let points = (0..25)
                    .map(|i| {
                        let a = offset + 0.55 + i as f32 * 2. / 24.;
                        geometry.at(a.cos() * 0.86, -a.sin() * 0.86)
                    })
                    .collect();
                painter.add(egui::Shape::line(points, Stroke::new(3.0_f32, ACCENT)));
            }
        }
        if let Some(s) = state.filter(|s| s.touching) {
            painter.circle_stroke(
                geometry.at(s.position[0] as f32, s.position[1] as f32),
                if s.click { 5. } else { 4. },
                Stroke::new(2.0_f32, ACCENT),
            );
        }
        let id = if diagram {
            source.into()
        } else {
            format!("explorer:{source}")
        };
        self.hit(ui, &id, Target::Surface(source.into()), (rect, angle));
        ui.interact(rect, ui.id().with(&id), egui::Sense::hover())
            .on_hover_text(format!(
                "{} · {}\nUse Touch or Click above the gamepad.",
                source.replace('_', " "),
                view.mode.replace('_', " ")
            ));
    }
}
fn pad_labels(ui: &egui::Ui, g: Geometry, view: &PadView) {
    let p = ui
        .painter()
        .with_clip_rect(g.rect.expand(7.).intersect(ui.clip_rect()));
    let size = (g.rect.width().min(g.rect.height()) * 0.078).clamp(9., 14.);
    p.text(
        g.rect.center(),
        Align2::CENTER_CENTER,
        &view.center,
        FontId::proportional(size),
        Color32::WHITE,
    );
    // Tiny integrated pads remain an overview; expanded detail retains every label.
    if g.rect.width().min(g.rect.height()) < 80. {
        return;
    }
    for (index, (x, y)) in [(0., -0.8), (0.76, 0.), (0., 0.8), (-0.76, 0.)]
        .into_iter()
        .enumerate()
    {
        let text = &view.directions[index];
        if text != "—" {
            p.text(
                g.at(x, y),
                Align2::CENTER_CENTER,
                text,
                FontId::proportional(size * 0.85),
                MUTED,
            );
        }
    }
}
