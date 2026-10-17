use super::{ACCENT, BORDER, DemoApp, MUTED, SURFACE};
use eframe::egui::{self, Align2, FontId, Sense, Stroke, vec2};

impl DemoApp {
    pub(super) fn playground(&self, ui: &mut egui::Ui) {
        ui.separator();
        ui.heading("Output playground");
        let output = &self.session.engine.output;
        ui.horizontal_wrapped(|ui| {
            ui.label("Held:");
            if output.down.is_empty() {
                ui.label(egui::RichText::new("—").color(MUTED));
            }
            for key in &output.down {
                ui.label(egui::RichText::new(key).monospace().color(ACCENT));
            }
        });
        let (rect, _) = ui.allocate_exact_size(vec2(ui.available_width(), 145.), Sense::hover());
        ui.painter().rect_filled(rect, 12., SURFACE);
        let center = rect.center();
        let point = center + vec2(output.pointer[0] as f32, output.pointer[1] as f32);
        let point = egui::pos2(
            rect.left() + (point.x - rect.left()).rem_euclid(rect.width()),
            rect.top() + (point.y - rect.top()).rem_euclid(rect.height()),
        );
        for radius in [18., 40., 65.] {
            ui.painter()
                .circle_stroke(center, radius, Stroke::new(1.0_f32, BORDER));
        }
        ui.painter().circle_filled(point, 5., ACCENT);
        ui.painter().text(
            rect.left_top() + vec2(10., 10.),
            Align2::LEFT_TOP,
            "Pointer",
            FontId::proportional(11.),
            MUTED,
        );
        ui.label(
            egui::RichText::new(if output.text.is_empty() {
                "Keys typed by the layout appear here…"
            } else {
                &output.text
            })
            .monospace()
            .color(ACCENT),
        );
        self.scroll_target(ui);
    }
    fn scroll_target(&self, ui: &mut egui::Ui) {
        let output = &self.session.engine.output;
        let (rect, _) = ui.allocate_exact_size(vec2(ui.available_width(), 105.), Sense::hover());
        let painter = ui.painter().with_clip_rect(rect);
        painter.rect_filled(rect, 10., SURFACE);
        // This is a visible wheel target. Its offset is driven only by emitted
        // wheel events, never by mouse movement or a UI caption.
        for row in -1..6 {
            let index = output.wheel + row;
            let y = rect.top() + row as f32 * 24. + 12.;
            painter.text(
                egui::pos2(rect.left() + 12., y),
                Align2::LEFT_TOP,
                format!("{:03}   Scroll the layout's content", index),
                FontId::proportional(13.),
                if row == 0 { ACCENT } else { MUTED },
            );
        }
        ui.label(format!("Wheel: {}", output.wheel));
        if !output.axes.is_empty() {
            ui.label(format!("Gamepad axes: {:?}", output.axes));
        }
        if let Some(error) = &self.session.engine.error {
            ui.colored_label(egui::Color32::LIGHT_RED, error);
        }
    }
    pub(super) fn details(&self, ui: &mut egui::Ui) {
        if !self.inspector {
            return;
        }
        ui.separator();
        ui.heading("Layout details");
        ui.label(format!(
            "{} · {}",
            self.session.engine.layout.tag, self.session.engine.layout.sha256
        ));
        ui.label("Analog motion is a browser model. Exact Steam transfer functions and physical haptics need hardware comparison.");
        ui.label("Cursor Gyro: hold Select, click and release R3, then release Select. On Ibex/Neptune, hold RS touch to enable motion.");
        ui.label("Right scroll: Touch mode; briefly touch and lift, touch the top/bottom within the window, then circle. Use slow motion while learning.");
        ui.label(self.session.engine.stack_titles().join(" → "));
        egui::CollapsingHeader::new("Construct coverage").show(ui, |ui| {
            for entry in &self.session.engine.layout.coverage {
                ui.label(format!(
                    "{} · {} · {}",
                    entry["category"].as_str().unwrap_or(""),
                    entry["name"].as_str().unwrap_or(""),
                    entry["status"].as_str().unwrap_or("")
                ))
                .on_hover_text(entry["reason"].as_str().unwrap_or(""));
            }
        });
        egui::CollapsingHeader::new("Recent actions").show(ui, |ui| {
            for event in self.session.engine.output.events.iter().rev().take(40) {
                ui.monospace(format!(
                    "{:>6} ms  {}  {}",
                    event.at, event.kind, event.detail
                ));
            }
        });
    }
}
