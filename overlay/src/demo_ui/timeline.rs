use super::{ACCENT, BORDER, DemoApp, target};
use eframe::egui::{self, Align2, Color32, FontId, Rect, Sense, Stroke, vec2};

impl DemoApp {
    pub(super) fn timeline(&self, ctx: &egui::Context) {
        egui::TopBottomPanel::top("demo.timeline").exact_height(48.).show(ctx, |ui| {
            let width = ui.available_width().min(1000.);
            let (row, _) = ui.allocate_exact_size(vec2(ui.available_width(), 44.), Sense::hover());
            let rect = Rect::from_center_size(row.center(), vec2(width, row.height()));
            target(ui, "timeline", rect);
            let rail = Rect::from_min_size(rect.left_bottom() - vec2(0., 10.), vec2(width, 4.));
            ui.painter().rect_filled(rail, 2., BORDER);
            let mut diagnostic = serde_json::json!({"active":false,"text":"","progress":0.,"remaining_ms":null});
            if let Some(lifecycle) = self.session.engine.lifecycle() {
                let now = self.session.engine.now;
                let remaining = lifecycle.remaining(now, self.session.scale);
                let progress = lifecycle.progress(now);
                let window = lifecycle.phase.label() == "Release window";
                let color = if window { Color32::from_rgb(244, 191, 88) } else { ACCENT };
                let status = remaining.map_or_else(|| lifecycle.phase.label().into(),
                    |ms| format!("{} · {ms} ms", lifecycle.phase.label()));
                let painted = ui.painter().text(rect.right_top() + vec2(0., 15.), Align2::RIGHT_CENTER,
                    &status, FontId::proportional(12.), color);
                let label_rect = Rect::from_min_max(rect.min, egui::pos2((painted.left() - 16.).max(rect.left()), rect.bottom()));
                ui.painter().with_clip_rect(label_rect).text(rect.left_top() + vec2(0., 15.), Align2::LEFT_CENTER,
                    &lifecycle.summary, FontId::proportional(15.), Color32::WHITE);
                ui.painter().rect_filled(Rect::from_min_size(rail.min, vec2(width * progress, 4.)), 2., color);
                if let Some((output, due)) = lifecycle.output_at.zip(lifecycle.deadline) {
                    let fraction = output.saturating_sub(lifecycle.started) as f32 / due.saturating_sub(lifecycle.started).max(1) as f32;
                    let x = rail.left() + width * fraction.clamp(0., 1.);
                    ui.painter().line_segment([egui::pos2(x, rail.top()-2.), egui::pos2(x, rail.bottom()+2.)], Stroke::new(1.5_f32, Color32::WHITE));
                }
                diagnostic = serde_json::json!({"active":true,"text":format!("{} · {status}",lifecycle.summary),
                    "progress":progress,"remaining_ms":remaining,"phase":lifecycle.phase,"owners":lifecycle.owners});
            }
            ctx.data_mut(|d| d.insert_temp(egui::Id::new("demo.timeline.state"), diagnostic));
        });
    }
}
