//! Browser-first, interactive playground for the executable layout.
mod app;
mod controller;
mod controls;
mod gyro;
mod hardware;
mod mouse;
mod output;
mod pads;
mod panels;
mod timeline;
mod toolbar;

pub use app::DemoApp;
use eframe::egui::{self, Color32};
const ACCENT: Color32 = Color32::from_rgb(125, 211, 184);
const MUTED: Color32 = Color32::from_rgb(156, 164, 177);
const SURFACE: Color32 = Color32::from_rgb(24, 27, 32);
const BORDER: Color32 = Color32::from_rgb(44, 49, 57);

impl DemoApp {
    fn binding_label(&self, ui: &egui::Ui, control: &str) -> String {
        let label = self.session.engine.display_label(control);
        ui.ctx().data_mut(|data| {
            data.get_temp_mut_or_default::<std::collections::BTreeMap<String, String>>(
                egui::Id::new("demo.binding-labels"),
            )
            .insert(control.into(), label.clone());
        });
        label
    }
}

fn target(ui: &egui::Ui, id: &str, rect: egui::Rect) {
    ui.ctx().data_mut(|data| {
        let targets = data.get_temp_mut_or_default::<std::collections::BTreeMap<String, [f32; 4]>>(
            egui::Id::new("demo.targets"),
        );
        targets.insert(
            id.into(),
            [
                rect.center().x,
                rect.center().y,
                rect.width(),
                rect.height(),
            ],
        );
    });
}
