use super::*;

fn text(p: &egui::Painter, center: egui::Pos2, value: &str, width: f32, style: (f32, Color32)) {
    let (size, color) = style;
    let direction = match value {
        "↑" => Some(egui::vec2(0.0, -1.0)),
        "→" => Some(egui::vec2(1.0, 0.0)),
        "↓" => Some(egui::vec2(0.0, 1.0)),
        "←" => Some(egui::vec2(-1.0, 0.0)),
        _ => None,
    };
    if let Some(d) = direction {
        p.arrow(
            center - d * size * 0.45,
            d * size * 0.9,
            egui::Stroke::new(1.5_f32, color),
        );
        return;
    }
    let mut job =
        egui::text::LayoutJob::simple(value.into(), egui::FontId::proportional(size), color, width);
    job.halign = egui::Align::Center;
    job.wrap.max_rows = 2;
    let galley = p.layout_job(job);
    p.galley(
        center - egui::vec2(0.0, galley.size().y / 2.0),
        galley,
        color,
    );
}

/// The same configured zones and light feedback on both pad views.
pub(in crate::ui) fn field(
    p: &egui::Painter,
    geometry: Geometry,
    pad: &TrackpadBindings,
    input: Feedback,
) {
    let field = Field {
        p,
        geometry,
        pad,
        input,
        active: input
            .position
            .and_then(|xy| pad.regions.as_ref().map(|r| r.zone(xy))),
    };
    field.background();
    field.bindings();
    field.pointer();
}
struct Field<'a> {
    p: &'a egui::Painter,
    geometry: Geometry,
    pad: &'a TrackpadBindings,
    input: Feedback,
    active: Option<PadZone>,
}
impl Field<'_> {
    fn background(&self) {
        let Self {
            p,
            pad,
            input,
            active,
            ..
        } = *self;
        let Geometry { center, half, .. } = self.geometry;
        let at = |x, y| self.geometry.at(x, y);
        let outline: Vec<_> = (0..=96)
            .map(|i| {
                let angle = i as f32 * std::f32::consts::TAU / 96.0;
                let radius = pad_edge(angle);
                at(angle.cos() * radius, angle.sin() * radius)
            })
            .collect();
        let tint =
            Color32::from_rgba_unmultiplied(119, 211, 182, if input.pressed { 8 } else { 4 });
        let edge =
            Color32::from_rgba_unmultiplied(119, 211, 182, if input.pressed { 70 } else { 18 });
        if let Some(regions) = &pad.regions {
            // Neutral guides stay visible through a light, whole-pad center tint.
            p.circle_stroke(
                center,
                half * regions.inner_radius(),
                egui::Stroke::new(1.0_f32, Color32::from_white_alpha(7)),
            );
            p.circle_stroke(
                center,
                half * regions.outer_start(),
                egui::Stroke::new(1.0_f32, Color32::from_white_alpha(4)),
            );
            if matches!(active, Some(PadZone::Inner | PadZone::Overlap)) {
                p.add(egui::Shape::convex_polygon(
                    outline.clone(),
                    tint,
                    egui::Stroke::new(1.0_f32, edge),
                ));
            }

            if let Some(PadZone::Outer(n)) = active {
                self.outer_highlight(n, regions, tint, edge);
            }
        } else if input.position.is_some() && matches!(pad.center, Binding::Label { .. }) {
            p.add(egui::Shape::convex_polygon(
                outline.clone(),
                tint,
                egui::Stroke::new(1.0_f32, edge),
            ));
        }
        if input.pressed && active.is_none() {
            p.add(egui::Shape::closed_line(
                outline,
                egui::Stroke::new(1.8_f32, edge),
            ));
        }
    }
    fn outer_highlight(&self, n: usize, regions: &PadRegions, tint: Color32, edge: Color32) {
        let p = self.p;
        let input = self.input;
        let at = |x, y| self.geometry.at(x, y);
        let start = (-135.0 + n as f32 * 90.0).to_radians();
        for i in 0..24 {
            let a = start + i as f32 * std::f32::consts::FRAC_PI_2 / 24.0;
            let b = start + (i + 1) as f32 * std::f32::consts::FRAC_PI_2 / 24.0;
            let point = |angle: f32, radius: f32| at(angle.cos() * radius, angle.sin() * radius);
            let inner = regions.inner_radius();
            p.add(egui::Shape::convex_polygon(
                vec![
                    point(a, inner),
                    point(a, pad_edge(a)),
                    point(b, pad_edge(b)),
                    point(b, inner),
                ],
                tint,
                egui::Stroke::NONE,
            ));
            p.line_segment(
                [point(a, pad_edge(a)), point(b, pad_edge(b))],
                egui::Stroke::new(if input.pressed { 1.8_f32 } else { 1.0_f32 }, edge),
            );
        }
    }
    fn bindings(&self) {
        if self.input.pressed {
            self.click_bindings();
        } else if let Some(swipes) = &self.pad.swipe {
            self.swipe_bindings(swipes);
        } else if self.pad.double_tap.is_some() {
            self.scroll_bindings();
        } else {
            text(
                self.p,
                self.geometry.center,
                &self.pad.touch,
                self.geometry.half * 1.4,
                (self.size(), MUTED),
            );
        }
    }
    fn size(&self) -> f32 {
        if self.geometry.half > 85.0 {
            14.0
        } else {
            10.0
        }
    }
    fn click_bindings(&self) {
        let Self { p, pad, active, .. } = *self;
        let Geometry { center, half, .. } = self.geometry;
        let at = |x, y| self.geometry.at(x, y);
        let detailed = half > 85.0;
        let size = self.size();
        text(
            p,
            center,
            &label(&pad.center),
            half * 0.75,
            (size, Color32::WHITE),
        );
        if pad.regions.is_some() {
            for (n, (x, y)) in [(0.0, -0.79), (0.79, 0.0), (0.0, 0.79), (-0.79, 0.0)]
                .into_iter()
                .enumerate()
            {
                let value = label(&pad.outer[n]);
                let value = if !detailed && value == "Forward" {
                    "Fwd".into()
                } else {
                    value
                };
                text(
                    p,
                    at(x, y),
                    &value,
                    if n % 2 == 0 { half * 1.2 } else { half * 0.46 },
                    (
                        if detailed && n % 2 == 1 { 12.0 } else { size },
                        if active == Some(PadZone::Outer(n)) {
                            ACCENT
                        } else {
                            Color32::from_gray(222)
                        },
                    ),
                );
            }
        }
    }
    fn swipe_bindings(&self, swipes: &[Binding; 4]) {
        let p = self.p;
        let Geometry { center, half, .. } = self.geometry;
        let at = |x, y| self.geometry.at(x, y);
        let detailed = half > 85.0;
        let size = self.size();
        for (n, (x, y)) in [(0.0, -0.72), (0.72, 0.0), (0.0, 0.72), (-0.72, 0.0)]
            .into_iter()
            .enumerate()
        {
            let delta = at(x * 0.65, y * 0.65) - center;
            p.arrow(
                center + delta * 0.28,
                delta * 0.55,
                egui::Stroke::new(1.3_f32, ACCENT),
            );
            let value = label(&swipes[n]);
            let value = if !detailed && value == "Escape" {
                "Esc".into()
            } else {
                value
            };
            text(
                p,
                at(x, y),
                &value,
                if n % 2 == 0 { half * 1.4 } else { half * 0.52 },
                (size, Color32::WHITE),
            );
        }
    }
    fn scroll_bindings(&self) {
        let p = self.p;
        let Geometry { center, half, .. } = self.geometry;
        let at = |x, y| self.geometry.at(x, y);
        let size = self.size();
        for sign in [-1.0, 1.0] {
            let points: Vec<_> = (0..=24)
                .map(|i| {
                    let a = (30.0 + i as f32 * 120.0 / 24.0).to_radians();
                    at(a.cos() * 0.81, a.sin() * sign * 0.81)
                })
                .collect();
            p.add(egui::Shape::line(
                points,
                egui::Stroke::new(5.0_f32, ACCENT.gamma_multiply(0.8)),
            ));
        }
        text(p, center, "Pointer", half * 1.1, (size, Color32::WHITE));
        text(p, at(0.0, -0.60), "Scroll", half, (size, ACCENT));
        text(p, at(0.0, 0.60), "Scroll", half, (size, ACCENT));
    }
    fn pointer(&self) {
        let p = self.p;
        let input = self.input;
        let at = |x, y| self.geometry.at(x, y);
        if let Some([x, y]) = input.position {
            let dot = at(x, y);
            let color = if input.live { ACCENT } else { Color32::WHITE };
            p.circle_stroke(
                dot,
                if input.pressed { 5.0 } else { 4.0 },
                egui::Stroke::new(if input.pressed { 2.0_f32 } else { 1.0_f32 }, color),
            );
        }
    }
}
