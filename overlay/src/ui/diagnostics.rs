use super::*;

pub(super) fn target(ui: &egui::Ui, name: &str, response: &egui::Response) {
    target_point(ui, name, response.rect.center());
}
pub(super) fn target_point(ui: &egui::Ui, name: &str, point: egui::Pos2) {
    ui.ctx().data_mut(|d| {
        let map = d.get_temp_mut_or_default::<std::collections::BTreeMap<String, [f32; 2]>>(
            egui::Id::new("keybind.targets"),
        );
        map.insert(name.into(), [point.x, point.y]);
    });
}
