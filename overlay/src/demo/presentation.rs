//! Read-only presentation of the executed layout graph. Never schedules input.
#[cfg(any(feature = "ui", test))]
mod bindings;
#[cfg(test)]
mod inheritance_tests;
mod lifecycle;
#[cfg(any(feature = "ui", test))]
mod pads;
#[cfg(test)]
mod tests;

use super::{Engine, Entry, Layout, Operation};
pub(crate) use lifecycle::Presentation;
#[cfg(any(feature = "ui", test))]
pub(crate) use pads::PadView;

pub(crate) fn friendly(value: &str) -> String {
    match value {
        "mouse_button LEFT" => "Left click",
        "mouse_button RIGHT" => "Right click",
        "mouse_button MIDDLE" => "Middle click",
        "mouse_button BACK" => "Back",
        "mouse_button FORWARD" => "Forward",
        "mouse_wheel SCROLL_UP" | "SCROLL_UP" => "Scroll up",
        "mouse_wheel SCROLL_DOWN" | "SCROLL_DOWN" => "Scroll down",
        "LEFT_SHIFT" => "Shift",
        "LEFT_CONTROL" => "Ctrl",
        "LEFT_ALT" => "Alt",
        "LEFT_WINDOWS" => "Win",
        "ESCAPE" => "Escape",
        "RETURN" => "Enter",
        "BACKSPACE" => "Backspace",
        "CAPSLOCK" => "Caps Lock",
        "TAB" => "Tab",
        "SPACE" => "Space",
        "EQUALS" => "=",
        "DASH" => "−",
        "DELETE" => "Delete",
        "INSERT" => "Insert",
        "Fn Layer" => "Fn",
        "Temp Cursor Gyro" => "Cursor gyro",
        "UP_ARROW" => "↑",
        "DOWN_ARROW" => "↓",
        "LEFT_ARROW" => "←",
        "RIGHT_ARROW" => "→",
        other => other,
    }
    .replace("xinput_button ", "Pad ")
    .replace("Modifier ", "Mod ")
}
pub(crate) fn layer_label(title: &str) -> String {
    friendly(title.rsplit_once(": ").map_or(title, |(_, name)| name))
}
fn outputs(entries: &[Entry]) -> String {
    let values: std::collections::BTreeSet<_> = entries
        .iter()
        .filter(|e| e.kind != "release")
        .flat_map(|e| &e.commands)
        .filter_map(|op| match op {
            Operation::MouseWheel { value } => Some(friendly(value)),
            _ => op.output().map(|s| friendly(&s)),
        })
        .collect();
    values.into_iter().collect::<Vec<_>>().join(" / ")
}
impl Layout {
    fn entries(&self, layer: usize) -> impl Iterator<Item = (String, &Entry)> {
        self.layers[layer].sources.iter().flat_map(|(source, gid)| {
            self.groups[*gid]
                .inputs
                .iter()
                .flat_map(move |(name, entries)| {
                    entries.iter().map(move |e| (format!("{source}/{name}"), e))
                })
        })
    }
    fn entry_label(&self, entries: &[Entry], depth: usize) -> String {
        let direct = outputs(entries);
        if !direct.is_empty() || depth == 0 {
            return direct;
        }
        entries
            .iter()
            .filter(|e| e.kind != "release")
            .flat_map(|e| &e.commands)
            .find_map(|op| match op {
                Operation::AddLayer { target, .. } | Operation::HoldLayer { target, .. } => {
                    let entries: Vec<_> = self
                        .entries(*target)
                        .filter(|(c, _)| c.ends_with("/always_on_action"))
                        .map(|(_, e)| e.clone())
                        .collect();
                    let label = self.entry_label(&entries, depth - 1);
                    Some(if label.is_empty() {
                        layer_label(&self.layers[*target].title)
                    } else {
                        label
                    })
                }
                _ => None,
            })
            .unwrap_or_default()
    }
}
impl Engine {
    #[cfg(any(feature = "ui", test))]
    pub(crate) fn display_label(&self, control: &str) -> String {
        if let Some(trace) = self
            .lifecycle()
            .filter(|t| t.owners.iter().any(|c| c == control))
        {
            return trace.summary;
        }
        let entries = self.display_entries(control);
        for entry in &entries {
            for op in &entry.commands {
                if let Operation::AddLayer { target, .. } = op
                    && let Some(summary) = self.layout.gesture_summary(*target)
                {
                    return summary;
                }
            }
        }
        let value = self.layout.entry_label(&entries, 3);
        if value.is_empty() {
            "—".into()
        } else {
            value
        }
    }
}
