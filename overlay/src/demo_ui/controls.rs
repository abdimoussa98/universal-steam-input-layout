use super::{
    ACCENT, BORDER, DemoApp, MUTED, SURFACE,
    mouse::{Hit, Target},
    target,
};
use eframe::egui::{self, Rect, Sense, Stroke, vec2};

impl DemoApp {
    pub(super) fn hit(&mut self, ui: &egui::Ui, id: &str, kind: Target, geometry: (Rect, f32)) {
        let (rect, angle) = geometry;
        target(ui, id, rect);
        self.hits.push(Hit {
            target: kind,
            rect,
            angle,
            clip: ui.clip_rect(),
            layer: ui.layer_id(),
        });
    }
    pub(super) fn pad_controls(&mut self, ui: &mut egui::Ui) {
        ui.label(egui::RichText::new("Trackpad input").small().color(MUTED));
        for (value, label) in [(false, "Touch"), (true, "Click")] {
            let r = ui.selectable_label(self.pad_click == value, label);
            target(ui, if value { "pad-click" } else { "pad-touch" }, r.rect);
            if r.clicked() {
                self.pad_click = value;
            }
        }
    }
    pub(super) fn explorer(&mut self, ui: &mut egui::Ui) {
        let sources: &[&str] = if self.session.engine.layout.controller == "dse" {
            &["center_trackpad"]
        } else {
            &["left_trackpad", "right_trackpad"]
        };
        ui.columns(sources.len(), |columns| {
            for (ui, source) in columns.iter_mut().zip(sources) {
                egui::Frame::new()
                    .fill(SURFACE)
                    .corner_radius(12.)
                    .stroke(Stroke::new(1.0_f32, BORDER))
                    .inner_margin(14.)
                    .show(ui, |ui| {
                        ui.strong(match *source {
                            "left_trackpad" => "Left trackpad",
                            "right_trackpad" => "Right trackpad",
                            _ => "Touchpad",
                        });
                        let size = (ui.available_width() - 8.).min(232.);
                        let (area, _) = ui.allocate_exact_size(
                            vec2(ui.available_width(), size + 16.),
                            Sense::hover(),
                        );
                        self.pad_field(
                            ui,
                            source,
                            Rect::from_center_size(area.center(), vec2(size, size)),
                            (0., false),
                        );
                        let mode = self.session.engine.effective(source).0;
                        let caption = match mode.as_str() {
                            "absolute_mouse" => "Pointer · double touch for circular scroll",
                            "scrollwheel" => "Circular scroll · lift to finish",
                            "2dscroll" => "Swipe toward a binding",
                            _ => "Touch or click a region to try its binding",
                        };
                        // Fixed caption space, including during center/outer transitions.
                        let (r, _) =
                            ui.allocate_exact_size(vec2(ui.available_width(), 48.), Sense::hover());
                        ui.painter().text(
                            r.left_top(),
                            egui::Align2::LEFT_TOP,
                            caption,
                            egui::FontId::proportional(12.),
                            MUTED,
                        );
                    });
            }
        });
    }
    pub(super) fn analog_details(&mut self, ui: &mut egui::Ui) {
        egui::CollapsingHeader::new("Analog controls").show(ui, |ui| {
            ui.add_enabled_ui(self.virtual_input_enabled(), |ui| {
                for (side, source) in ["left_trigger", "right_trigger"].iter().enumerate() {
                    let response =
                        ui.add(
                            egui::Slider::new(&mut self.triggers[side], 0.0..=1.0)
                                .text(if side == 0 { "L2 travel" } else { "R2 travel" }),
                        );
                    target(ui, source, response.rect);
                    if response.changed() {
                        self.session.input(crate::demo::Input::Trigger {
                            source: (*source).into(),
                            value: self.triggers[side],
                        });
                    }
                }
            });
            ui.colored_label(
                ACCENT,
                "Drag the lower stick knobs on the gamepad to move them.",
            );
        });
    }
}
