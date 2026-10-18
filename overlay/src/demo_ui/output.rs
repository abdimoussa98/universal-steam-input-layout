//! Compact feedback from outputs actually emitted by the layout engine.
use super::{ACCENT, BORDER, DemoApp, MUTED, SURFACE, target};
use crate::demo::presentation::friendly;
use eframe::egui::{self, Align2, FontId, Rect, Sense, Stroke, StrokeKind, vec2};

impl DemoApp {
    pub(super) fn output_preview(&self, ui: &mut egui::Ui) {
        let (rect, _) = ui.allocate_exact_size(vec2(ui.available_width(), 64.), Sense::hover());
        target(ui, "output-preview", rect);
        let p = ui.painter();
        p.rect(
            rect,
            10.,
            SURFACE,
            Stroke::new(1.0_f32, BORDER),
            StrokeKind::Inside,
        );
        let motion = Rect::from_min_size(rect.min + vec2(10., 10.), vec2(60., 44.));
        p.line_segment(
            [motion.left_center(), motion.right_center()],
            Stroke::new(1.0_f32, BORDER),
        );
        p.line_segment(
            [motion.center_top(), motion.center_bottom()],
            Stroke::new(1.0_f32, BORDER),
        );
        let output = &self.session.engine.output;
        let point = motion.min
            + vec2(
                (30. + output.pointer[0] as f32).rem_euclid(motion.width()),
                (22. + output.pointer[1] as f32).rem_euclid(motion.height()),
            );
        p.circle_filled(point, 3., ACCENT);
        p.text(
            motion.left_top(),
            Align2::LEFT_TOP,
            "Output",
            FontId::proportional(10.),
            MUTED,
        );
        let lines = self.output_lines();
        for (i, line) in lines.iter().enumerate() {
            let r = Rect::from_min_size(
                rect.min + vec2(82., 8. + i as f32 * 24.),
                vec2((rect.width() - 92.).max(1.), 20.),
            );
            preview_line(ui, r, i, line);
        }
        ui.ctx()
            .data_mut(|d| d.insert_temp(egui::Id::new("demo.output-preview"), lines));
    }
    fn output_lines(&self) -> [String; 2] {
        let output = &self.session.engine.output;
        let typed: String = output
            .text
            .chars()
            .rev()
            .take(32)
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .map(|c| if c == '\n' { '↵' } else { c })
            .collect();
        let held = output
            .down
            .iter()
            .map(|s| friendly(s))
            .collect::<Vec<_>>()
            .join(" + ");
        let last = output
            .events
            .iter()
            .rev()
            .find(|e| matches!(e.kind.as_str(), "down" | "tap"))
            .map(|e| friendly(&e.detail))
            .unwrap_or_else(|| "—".into());
        let keys = if !held.is_empty() {
            format!("Held: {held}")
        } else if !typed.is_empty() {
            format!("Typed: {typed} · Last: {last}")
        } else {
            format!("Last input: {last}")
        };
        let axes = if output.axes.is_empty() {
            String::new()
        } else {
            format!(" · Sticks: {:?}", output.axes)
        };
        [
            keys,
            format!(
                "Pointer {:+.0}, {:+.0} · Scroll {:+}{axes}",
                output.pointer[0], output.pointer[1], output.wheel
            ),
        ]
    }
}

fn preview_line(ui: &egui::Ui, rect: Rect, index: usize, text: &str) {
    let color = if index == 0 { ACCENT } else { MUTED };
    let mut job =
        egui::text::LayoutJob::simple(text.into(), FontId::proportional(12.), color, rect.width());
    job.wrap.max_rows = 1;
    job.wrap.break_anywhere = true;
    let galley = ui.painter().layout_job(job);
    ui.painter()
        .with_clip_rect(rect)
        .galley(rect.min + vec2(0., 2.), galley, color);
    ui.interact(rect, ui.id().with(("output-line", index)), Sense::hover())
        .on_hover_text(text);
}
