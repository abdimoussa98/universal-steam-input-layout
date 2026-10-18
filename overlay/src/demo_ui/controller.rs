//! The original illustrated viewer, fed by the executable layout.
mod controls;
mod shell;
use super::{ACCENT, BORDER, DemoApp, MUTED, SURFACE, target};
use eframe::egui::{self, Color32, Rect, Sense, Stroke, vec2};

const SHELL: Color32 = Color32::from_rgb(35, 39, 46);
const EDGE: Color32 = Color32::from_rgb(66, 73, 84);
const DARK: Color32 = Color32::from_rgb(21, 24, 29);
struct Diagram<'a> {
    app: &'a mut DemoApp,
    ui: &'a egui::Ui,
    area: Rect,
    scale: f32,
}
impl DemoApp {
    pub(super) fn controller(&mut self, ui: &mut egui::Ui) {
        egui::Frame::new()
            .fill(SURFACE)
            .corner_radius(14.)
            .stroke(Stroke::new(1.0_f32, BORDER))
            .inner_margin(16.)
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.colored_label(ACCENT, self.session.engine.mode());
                    ui.label(
                        egui::RichText::new("Hold to press · right-click to latch a chord")
                            .small()
                            .color(MUTED),
                    );
                });
                egui::ScrollArea::horizontal()
                    .drag_to_scroll(false)
                    .id_salt("illustrated-controller")
                    .show(ui, |ui| {
                        ui.set_min_width(620.);
                        let available = ui.available_width();
                        let width = available.min(780.);
                        let scale = width / 1000.;
                        let (row, _) =
                            ui.allocate_exact_size(vec2(available, 685. * scale), Sense::hover());
                        let area = Rect::from_center_size(row.center(), vec2(width, row.height()));
                        target(ui, "controller", area);
                        let mut diagram = Diagram {
                            app: self,
                            ui,
                            area,
                            scale,
                        };
                        diagram.shell();
                        diagram.pads();
                        diagram.controls();
                        diagram.extras();
                    });
            });
    }
}
impl Diagram<'_> {
    fn at(&self, x: f32, y: f32) -> egui::Pos2 {
        self.area.min + vec2(x, y) * self.scale
    }
    fn box_at(&self, x: f32, y: f32, w: f32, h: f32) -> Rect {
        Rect::from_center_size(self.at(x, y), vec2(w, h) * self.scale)
    }
    fn pads(&mut self) {
        let device = self.app.session.engine.layout.controller.as_str();
        let pads: &[(&str, f32, f32, f32, f32)] = match device {
            "dse" => &[("center_trackpad", 500., 175., 135., 0.)],
            "neptune" => &[
                ("left_trackpad", 270., 400., 80., 0.),
                ("right_trackpad", 730., 400., 80., 0.),
            ],
            _ => &[
                ("left_trackpad", 352., 410., 82., 0.12),
                ("right_trackpad", 648., 410., 82., -0.12),
            ],
        };
        if device == "ibex" {
            self.ui.painter().rect_filled(
                self.box_at(500., 420., 520., 228.),
                48. * self.scale,
                Color32::from_rgb(29, 33, 39),
            );
        }
        for &(source, x, y, half, angle) in pads {
            let rect = self.box_at(
                x,
                y,
                half * 2.,
                if source == "center_trackpad" {
                    110.
                } else {
                    half * 2.
                },
            );
            self.app.pad_field(self.ui, source, rect, (angle, true));
        }
    }
}
