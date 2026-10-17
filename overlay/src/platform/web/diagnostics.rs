use super::WebState;
use eframe::egui;

fn pad_values(state: &WebState, kind: &str) -> [Option<String>; 2] {
    std::array::from_fn(|side| {
        state.context.as_ref().and_then(|context| {
            context.data(|data| data.get_temp(egui::Id::new(format!("pad:{side}:{kind}"))))
        })
    })
}

pub(super) fn snapshot(s: &WebState) -> String {
    let pad_previews = pad_values(s, "preview");
    let pad_feedback = pad_values(s, "feedback");
    let pad_layers = pad_values(s, "layer");
    serde_json::json!({
        "pad_layers": pad_layers,
        "pad_feedback": pad_feedback,
        "pad_previews": pad_previews,
        "trackpads": s.data.state.control_page(&s.data.profile).and_then(|page| page.trackpads.as_ref()),
        "ui_targets": s.context.as_ref().and_then(|c| c.data(|d| d.get_temp::<std::collections::BTreeMap<String, [f32; 2]>>(egui::Id::new("keybind.targets")))),
        "control_labels": s.data.state.control_labels(&s.data.profile),
        "input_status": s.data.input_status_label(),
        "controller_help": s.data.controller_help(),
        "browser_connection": s.data.browser_connection,
        "state": s.data.state,
        "labels": s.data.state.view(&s.data.profile).labels,
        "devices": s.data.settings.devices,
        "error": s.data.error.as_ref().or(s.data.settings.error.as_ref()),
        "remote": s.data.remote,
        "settings": s.data.settings,
        "preferences": s.data.display_preferences(),
    })
    .to_string()
}
