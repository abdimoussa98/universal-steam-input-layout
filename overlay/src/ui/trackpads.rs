use super::*;
mod cards;
mod drawing;
mod feedback;
mod geometry;

use cards::card;
pub(super) use drawing::field;
pub(super) use feedback::{Feedback, feedback, record_feedback};
pub(super) use geometry::Geometry;
use geometry::pad_edge;

const OVERLAP: Color32 = Color32::from_rgb(211, 164, 91);
const PAD_FILL: Color32 = Color32::from_rgb(21, 24, 29);

fn label(binding: &Binding) -> String {
    match binding {
        Binding::Label { text } => compact_binding(text)
            .replace("Mouse forward", "Forward")
            .replace("Mouse back", "Back"),
        Binding::Unbound => "—".into(),
        _ => "Unavailable".into(),
    }
}

pub(super) fn explorer(ui: &mut egui::Ui, data: &FrameData) {
    if data.state.input.pad_pressures.iter().any(Option::is_some) {
        let key = egui::Id::new("pad:click-force");
        let mut force = ui.ctx().data(|d| d.get_temp::<u16>(key)).unwrap_or(15);
        let response = ui.add(egui::Slider::new(&mut force, 1..=100).suffix("%").text("Deck click force"))
            .on_hover_text("Adjust the viewer's pressure threshold to match your Steam click feel. This only changes the preview.");
        target(ui, "pad:click-force", &response);
        ui.ctx().data_mut(|d| d.insert_temp(key, force));
    }
    let Some(pads) = data
        .state
        .control_page(&data.profile)
        .and_then(|page| page.trackpads.as_ref())
    else {
        return;
    };
    ui.add_space(8.0);
    egui::Frame::new().fill(SURFACE).corner_radius(14.0)
        .stroke(egui::Stroke::new(1.0_f32,BORDER)).inner_margin(16.0).show(ui,|ui| {
        ui.label(RichText::new("Trackpads").size(19.0).color(Color32::WHITE));
        ui.label(RichText::new("Touch bindings first. Press a pad to see its click bindings; release to return.").color(MUTED));
        ui.label(RichText::new("You can also hold the mouse button over a pad to preview a click. The inner binding wins in the overlap.").size(12.0).color(MUTED));
        ui.add_space(12.0);
        if ui.available_width()>=620.0 {
            ui.columns(2,|cols| {for side in 0..2 {card(&mut cols[side],side,&pads[side],data);}});
        } else {
            for (side,pad) in pads.iter().enumerate() {card(ui,side,pad,data);ui.add_space(12.0);}
        }
    });
}
