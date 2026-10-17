use super::{WebState, page_hidden};
use crate::core::State;
use eframe::egui;

fn pad_values(state: &WebState, kind: &str) -> [Option<String>; 2] {
    std::array::from_fn(|side| {
        state.context.as_ref().and_then(|context| {
            context.data(|data| data.get_temp(egui::Id::new(format!("pad:{side}:{kind}"))))
        })
    })
}

pub(super) fn snapshot(s: &WebState) -> String {
    let mut data = s.data.clone();
    let preview =
        !page_hidden() && context_value::<bool>(s, "keybind.mouse-preview").unwrap_or(false);
    if preview && let Some(state) = context_value::<State>(s, "keybind.rendered-state") {
        data.state = state;
    }
    let pad_previews = pad_values(s, "preview");
    let pad_feedback = pad_values(s, "feedback");
    let pad_layers = pad_values(s, "layer");
    serde_json::json!({
        "pad_layers": pad_layers,
        "pad_feedback": pad_feedback,
        "pad_previews": pad_previews,
        "mouse_preview": preview,
        "source_state": s.data.state,
        "timeline": context_value::<serde_json::Value>(s, "keybind.timeline"),
        "trackpads": data.state.control_page(&data.profile).and_then(|page| page.trackpads.as_ref()),
        "ui_targets": s.context.as_ref().and_then(|c| c.data(|d| d.get_temp::<std::collections::BTreeMap<String, [f32; 2]>>(egui::Id::new("keybind.targets")))),
        "control_labels": data.state.control_labels(&data.profile),
        "input_status": data.input_status_label(),
        "controller_help": data.controller_help(),
        "browser_connection": s.data.browser_connection,
        "state": data.state,
        "labels": data.state.view(&data.profile).labels,
        "devices": s.data.settings.devices,
        "error": s.data.error.as_ref().or(s.data.settings.error.as_ref()),
        "remote": s.data.remote,
        "settings": s.data.settings,
        "preferences": s.data.display_preferences(),
    })
    .to_string()
}

fn context_value<T: Clone + Send + Sync + 'static>(state: &WebState, key: &str) -> Option<T> {
    state
        .context
        .as_ref()
        .and_then(|context| context.data(|data| data.get_temp(egui::Id::new(key))))
}
