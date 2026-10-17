use super::*;

fn stick_marker(center: egui::Pos2, xy: [i16; 2], scale: f32) -> egui::Pos2 {
    center
        + egui::vec2(
            f32::from(xy[0].clamp(-1000, 1000)),
            f32::from(xy[1].clamp(-1000, 1000)),
        ) * (10.0 * scale / 1000.0)
}

const POSITIONS: [(f32, f32); 16] = [
    (735.0, 257.0),
    (779.0, 213.0),
    (691.0, 213.0),
    (735.0, 169.0),
    (364.0, 145.0),
    (636.0, 145.0),
    (264.0, 173.0),
    (304.0, 213.0),
    (264.0, 253.0),
    (224.0, 213.0),
    (385.0, 257.0),
    (615.0, 257.0),
    (280.0, 81.0),
    (720.0, 81.0),
    (280.0, 32.0),
    (720.0, 32.0),
];

impl Diagram<'_> {
    pub(super) fn controls(&self) {
        let labels = self.data.state.control_labels(&self.data.profile);
        let p = self.ui.painter();
        p.rect_filled(
            self.box_at(264.0, 213.0, 44.0, 124.0),
            10.0 * self.scale,
            DARK,
        );
        p.rect_filled(
            self.box_at(264.0, 213.0, 124.0, 44.0),
            10.0 * self.scale,
            DARK,
        );
        for (n, control) in Control::ALL.into_iter().enumerate() {
            let drawing = ControlDrawing::new(self, n, control);
            drawing.shape();
            drawing.label(&labels[n]);
            if n >= 14 {
                drawing.trigger();
            }
            drawing.hover(&labels[n]);
        }
    }
}
struct ControlDrawing<'a> {
    diagram: &'a Diagram<'a>,
    n: usize,
    control: Control,
    center: egui::Pos2,
    card: egui::Rect,
    width: f32,
    down: bool,
    fill: Color32,
    stroke: egui::Stroke,
}
impl<'a> ControlDrawing<'a> {
    fn new(diagram: &'a Diagram<'a>, n: usize, control: Control) -> Self {
        let data = diagram.data;
        let dark = DARK;
        let edge = EDGE;
        let at = |x, y| diagram.at(x, y);
        let box_at = |x, y, w, h| diagram.box_at(x, y, w, h);
        let (x, y) = POSITIONS[n];
        let center = at(x, y);
        let down = data.state.status == InputStatus::Live && data.state.input.down(control);
        let fill = if down {
            Color32::from_rgb(36, 70, 61)
        } else {
            dark
        };
        let stroke = egui::Stroke::new(
            if down { 1.8_f32 } else { 1.0_f32 },
            if down { ACCENT } else { edge },
        );
        let (w, h) = match control {
            Control::L1 | Control::R1 | Control::L2 | Control::R2 => (244.0, 40.0),
            Control::Select | Control::Start => (136.0, 38.0),
            Control::L3 | Control::R3 => (92.0, 92.0),
            Control::A | Control::B | Control::X | Control::Y => (48.0, 48.0),
            _ => (44.0, 44.0),
        };
        let card = box_at(x, y, w, h);

        Self {
            diagram,
            n,
            control,
            center,
            card,
            width: w,
            down,
            fill,
            stroke,
        }
    }
    fn shape(&self) {
        let p = self.diagram.ui.painter();
        let scale = self.diagram.scale;
        let Self {
            n,
            center,
            card,
            fill,
            stroke,
            down,
            ..
        } = *self;
        if matches!(self.control, Control::L3 | Control::R3) {
            self.stick();
        } else if n < 4 {
            p.circle_filled(center, 24.0 * scale, fill);
            p.circle_stroke(center, 24.0 * scale, stroke);
        } else {
            let radius = if n >= 12 { 12.0 } else { 9.0 } * scale;
            p.rect_filled(card, radius, fill);
            if down || !(6..12).contains(&n) {
                p.rect_stroke(card, radius, stroke, egui::StrokeKind::Inside);
            }
        }
    }
    fn stick(&self) {
        let ui = self.diagram.ui;
        let data = self.diagram.data;
        let p = ui.painter();
        let scale = self.diagram.scale;
        let edge = EDGE;
        let Self {
            n,
            center,
            fill,
            stroke,
            ..
        } = *self;
        p.circle_filled(center, 46.0 * scale, Color32::from_rgb(17, 20, 25));
        p.circle_stroke(center, 46.0 * scale, egui::Stroke::new(1.0_f32, edge));
        p.circle_filled(center, 39.0 * scale, fill);
        p.circle_stroke(center, 39.0 * scale, stroke);
        let side = n - 10;
        // Separate the click label above from the full XY travel field below.
        let origin = center + egui::vec2(0.0, 21.0 * scale);
        p.circle_stroke(origin, 16.0 * scale, egui::Stroke::new(1.0_f32, edge));
        target_point(ui, &format!("stick:{side}:shell"), center);
        target_point(ui, &format!("stick:{side}:center"), origin);
        target_point(
            ui,
            &format!("stick:{side}:range"),
            origin + egui::vec2(10.0 * scale, 0.0),
        );
        if data.state.status == InputStatus::Live {
            if data.state.input.touches[side] == Some(true) {
                p.circle_stroke(center, 43.0 * scale, egui::Stroke::new(2.0_f32, ACCENT));
            }
            if let Some(xy) = data.state.input.stick_positions[side] {
                let dot = stick_marker(origin, xy, scale);
                let color = if data.state.input.touches[side] == Some(true) {
                    ACCENT
                } else {
                    Color32::from_rgb(244, 191, 88)
                };
                p.line_segment([origin, dot], egui::Stroke::new(1.0_f32, color));
                p.circle_stroke(dot, 3.0 * scale, egui::Stroke::new(1.8_f32, color));
                p.circle_filled(dot, 1.0 * scale, color);
                target_point(ui, &format!("stick:{side}:marker"), dot);
            }
        }
    }
    fn binding(&self, source: &str) -> String {
        let n = self.n;
        let data = self.diagram.data;
        let control = self.control;
        let mut label = compact_binding(source);
        if n < 4 {
            // Conventional keycap abbreviations avoid splitting a key name
            // across lines on the small face buttons.
            label = match label.as_str() {
                "Escape" => "Esc".into(),
                "Backspace" => "Bksp".into(),
                _ => label,
            };
        }
        if matches!(source, "Timed gesture" | "Modifier")
            && let Some(recipe) = data
                .profile
                .dashboard
                .as_ref()
                .and_then(|d| d.recipe(data.state.mode, control))
        {
            label = recipe_binding(recipe);
        }
        label
    }
    fn label(&self, source: &str) {
        let control = self.control;
        let center = self.center;
        let scale = self.diagram.scale;
        let down = self.down;
        let p = self.diagram.ui.painter();
        let label = self.binding(source);
        let label_center = if matches!(control, Control::L3 | Control::R3) {
            center - egui::vec2(0.0, 15.0 * scale)
        } else {
            center
        };
        let arrow = match label.as_str() {
            "↑" => Some(egui::vec2(0.0, -1.0)),
            "→" => Some(egui::vec2(1.0, 0.0)),
            "↓" => Some(egui::vec2(0.0, 1.0)),
            "←" => Some(egui::vec2(-1.0, 0.0)),
            _ => None,
        };
        if let Some(direction) = arrow {
            // Default egui fonts do not include these keyboard-arrow glyphs.
            p.arrow(
                label_center - direction * 10.0 * scale,
                direction * 20.0 * scale,
                egui::Stroke::new(1.8_f32, if down { ACCENT } else { Color32::WHITE }),
            );
        } else {
            self.text_label(label_center, label);
        }
    }
    fn text_label(&self, label_center: egui::Pos2, label: String) {
        let control = self.control;
        let n = self.n;
        let w = self.width;
        let scale = self.diagram.scale;
        let down = self.down;
        let p = self.diagram.ui.painter();
        let font_size = if label.chars().count() <= 2 {
            23.0
        } else {
            17.0
        };
        let mut job = egui::text::LayoutJob::simple(
            label,
            egui::FontId::proportional((font_size * scale).max(13.0)),
            if down {
                ACCENT
            } else {
                Color32::from_rgb(240, 243, 248)
            },
            (if matches!(control, Control::L3 | Control::R3) {
                64.0
            } else if n < 4 {
                w - 4.0
            } else {
                w - 12.0
            }) * scale,
        );
        job.halign = egui::Align::Center;
        job.wrap.max_rows = if matches!(control, Control::L3 | Control::R3) || n < 4 {
            2
        } else {
            1
        };

        let galley = self.fit_label(job, label_center);
        p.galley(
            label_center - egui::vec2(0.0, galley.size().y / 2.0),
            galley,
            Color32::WHITE,
        );
    }
    fn fit_label(
        &self,
        mut job: egui::text::LayoutJob,
        label_center: egui::Pos2,
    ) -> std::sync::Arc<egui::Galley> {
        let control = self.control;
        let scale = self.diagram.scale;
        let n = self.n;
        let ui = self.diagram.ui;
        let p = ui.painter();
        let mut galley = p.layout_job(job.clone());
        if matches!(control, Control::L3 | Control::R3) {
            // Fit two lines inside the upper part of the circle. The travel
            // field stays clear even at maximum upward deflection.
            while galley.size().y > 32.0 * scale || galley.size().x > 64.0 * scale {
                for section in &mut job.sections {
                    section.format.font_id.size *= 0.95;
                }
                galley = p.layout_job(job.clone());
            }
            let half = galley.size() / 2.0;
            target_point(
                ui,
                &format!("stick:{}:label_min", n - 10),
                label_center - half,
            );
            target_point(
                ui,
                &format!("stick:{}:label_max", n - 10),
                label_center + half,
            );
        }
        galley
    }
    fn trigger(&self) {
        let data = self.diagram.data;
        let p = self.diagram.ui.painter();
        let scale = self.diagram.scale;
        let n = self.n;
        let card = self.card;
        let w = self.width;
        let track = egui::Rect::from_min_size(
            card.left_bottom() + egui::vec2(12.0, -4.0) * scale,
            egui::vec2((w - 24.0) * scale, 2.0 * scale),
        );
        p.rect_filled(track, 1.0, BORDER);
        let travel = data.state.input.triggers[n - 14].min(1000) as f32 / 1000.0;
        if travel > 0.0 {
            p.rect_filled(
                egui::Rect::from_min_size(
                    track.min,
                    egui::vec2(track.width() * travel, track.height()),
                ),
                1.0,
                ACCENT,
            );
        }
        if let Some(t) = data
            .profile
            .dashboard
            .as_ref()
            .and_then(|d| d.trigger_thresholds[n - 14])
        {
            let x = track.left() + track.width() * t as f32 / 1000.0;
            p.line_segment(
                [
                    egui::pos2(x, track.top() - 3.0),
                    egui::pos2(x, track.bottom()),
                ],
                egui::Stroke::new(1.0_f32, ACCENT),
            );
        }
    }
    fn hover(&self, label: &str) {
        let ui = self.diagram.ui;
        let data = self.diagram.data;
        let n = self.n;
        let control = self.control;
        let card = self.card;
        let response = ui.interact(
            card,
            egui::Id::new(("control", n)),
            egui::Sense::click_and_drag(),
        );
        target(ui, &format!("control:{}", control.key()), &response);
        mouse::register(ui, control, &response);
        let mut help = format!(
            "{}: {}\nClick and hold to preview. Right-click to hold or release for combinations.",
            control.label(),
            label
        );
        if n >= 14 {
            help.push_str(&format!(
                "\nTravel: {}%",
                data.state.input.triggers[n - 14] / 10
            ));
        }
        response
            .on_hover_cursor(egui::CursorIcon::PointingHand)
            .on_hover_text(help);
    }
}
