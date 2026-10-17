use super::*;

pub(super) fn apply(ctx: &egui::Context) {
    let mut style = (*ctx.style()).clone();
    style.visuals = egui::Visuals::dark();
    style.visuals.panel_fill = BACKGROUND;
    style.visuals.window_fill = SURFACE;
    style.visuals.extreme_bg_color = BACKGROUND;
    style.visuals.faint_bg_color = SURFACE;
    style.visuals.override_text_color = Some(Color32::from_rgb(230, 233, 239));
    style.visuals.selection.bg_fill = Color32::from_rgb(38, 67, 60);
    style.visuals.selection.stroke = egui::Stroke::new(1.0_f32, ACCENT);
    for widget in [
        &mut style.visuals.widgets.inactive,
        &mut style.visuals.widgets.noninteractive,
    ] {
        widget.bg_fill = SURFACE;
        widget.weak_bg_fill = SURFACE;
        widget.bg_stroke = egui::Stroke::new(1.0_f32, BORDER);
        widget.corner_radius = egui::CornerRadius::same(8);
    }
    style.visuals.widgets.hovered.bg_fill = Color32::from_rgb(40, 46, 53);
    style.visuals.widgets.hovered.weak_bg_fill = Color32::from_rgb(40, 46, 53);
    style.visuals.widgets.hovered.bg_stroke = egui::Stroke::new(1.0_f32, MUTED);
    style.spacing.item_spacing = egui::vec2(10.0, 8.0);
    style.spacing.button_padding = egui::vec2(12.0, 8.0);
    style.spacing.interact_size.y = 32.0;
    ctx.set_style(style);
}
