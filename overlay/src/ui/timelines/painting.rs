use super::*;

fn bar(rect: egui::Rect) -> egui::Rect {
    egui::Rect::from_min_size(
        egui::pos2(rect.left(), rect.bottom() - 12.0),
        egui::vec2(rect.width(), 4.0),
    )
}

pub(super) fn rail(ui: &egui::Ui, rect: egui::Rect) {
    ui.painter().rect_filled(bar(rect), 2.0, BORDER);
}

impl Timeline<'_> {
    pub(super) fn paint(&self, ui: &egui::Ui, rect: egui::Rect, now: u64) {
        let color = if self.lane.phase == Phase::Window {
            WINDOW_COLOR
        } else {
            ACCENT
        };
        self.text(ui, rect, now, color);
        let bar = bar(rect);
        let progress = self.progress(now);
        if progress > 0.0 {
            ui.painter().rect_filled(
                egui::Rect::from_min_size(
                    bar.min,
                    egui::vec2(bar.width() * progress, bar.height()),
                ),
                2.0,
                color,
            );
        }
        if self.lane.phase == Phase::Window {
            let x = bar.left()
                + bar.width() * self.recipe.output_ms as f32 / self.recipe.window_ms as f32;
            ui.painter().line_segment(
                [
                    egui::pos2(x, bar.top() - 2.0),
                    egui::pos2(x, bar.bottom() + 2.0),
                ],
                egui::Stroke::new(1.5_f32, Color32::WHITE),
            );
        }
    }

    fn text(&self, ui: &egui::Ui, rect: egui::Rect, now: u64, color: Color32) {
        let painter = ui.painter().with_clip_rect(rect.intersect(ui.clip_rect()));
        let status = painter.text(
            egui::pos2(rect.right(), rect.top() + 17.0),
            egui::Align2::RIGHT_CENTER,
            self.status(now),
            egui::FontId::proportional(12.0),
            color,
        );
        let summary_rect = egui::Rect::from_min_max(
            rect.min,
            egui::pos2((status.left() - 16.0).max(rect.left()), rect.bottom()),
        );
        painter.with_clip_rect(summary_rect).text(
            egui::pos2(rect.left(), rect.top() + 17.0),
            egui::Align2::LEFT_CENTER,
            self.summary(),
            egui::FontId::proportional(15.0),
            Color32::WHITE,
        );
    }
}
