use super::*;

pub(super) fn card(ui: &mut egui::Ui, side: usize, pad: &TrackpadBindings, data: &FrameData) {
    egui::Frame::new()
        .fill(PAD_FILL)
        .corner_radius(12.0)
        .inner_margin(14.0)
        .show(ui, |ui| {
            ui.set_min_width((ui.available_width() - 2.0).max(0.0));
            ui.label(
                RichText::new(if side == 0 {
                    "Left trackpad"
                } else {
                    "Right trackpad"
                })
                .strong(),
            );
            let input = pad_diagram(ui, side, pad, data);
            if input.pressed {
                click_caption(ui, side, pad, input);
            } else {
                touch_caption(ui, pad);
            }
        });
}
fn pad_diagram(
    ui: &mut egui::Ui,
    side: usize,
    pad: &TrackpadBindings,
    data: &FrameData,
) -> Feedback {
    let half = (ui.available_width() / 2.0 - 8.0).min(116.0);
    let (area, _) = ui.allocate_exact_size(
        egui::vec2(ui.available_width(), half * 2.0 + 24.0),
        egui::Sense::click_and_drag(),
    );
    let center = area.center();
    let bounds = egui::Rect::from_center_size(center, egui::vec2(half * 2.0, half * 2.0));
    let geometry = Geometry {
        center,
        half,
        angle: 0.0,
    };
    let input = feedback(ui, data, side, geometry.hover(ui));
    let painter = ui.painter();
    painter.rect_filled(bounds, 18.0, Color32::from_rgb(25, 30, 36));
    painter.rect_stroke(
        bounds,
        18.0,
        egui::Stroke::new(1.0_f32, BORDER),
        egui::StrokeKind::Inside,
    );
    field(painter, geometry, pad, input);

    record_preview(ui, side, pad, input);
    targets(ui, side, pad, geometry);
    input
}
fn record_preview(ui: &egui::Ui, side: usize, pad: &TrackpadBindings, input: Feedback) {
    if !input.pressed {
        let value = if pad.swipe.is_some() {
            "Touch · Swipe bindings".into()
        } else if pad.double_tap.is_some() {
            "Touch · Pointer / Double tap to scroll".into()
        } else {
            format!("Touch · {}", pad.touch)
        };
        ui.ctx()
            .data_mut(|d| d.insert_temp(egui::Id::new(format!("pad:{side}:preview")), value));
    }
    if input.live || input.position.is_some() {
        record_feedback(ui, side, pad, input);
    }
}
fn targets(ui: &egui::Ui, side: usize, pad: &TrackpadBindings, geometry: Geometry) {
    let Geometry { center, half, .. } = geometry;
    target_point(ui, &format!("pad:{side}:center"), center);
    target_point(
        ui,
        &format!("pad:{side}:overlap"),
        center
            + egui::vec2(
                half * pad
                    .regions
                    .as_ref()
                    .map_or(0.5, |r| (r.inner_radius() + r.outer_start()) / 2.0),
                0.0,
            ),
    );
    target_point(
        ui,
        &format!("pad:{side}:outer"),
        center + egui::vec2(half * 0.84, 0.0),
    );
}
fn click_caption(ui: &mut egui::Ui, side: usize, pad: &TrackpadBindings, input: Feedback) {
    let (selected, caption) = if pad.regions.is_none() {
        (&pad.center, "Click")
    } else {
        match input
            .position
            .and_then(|xy| pad.regions.as_ref().map(|r| r.zone(xy)))
        {
            Some(PadZone::Inner) => (&pad.center, "Inner click"),
            Some(PadZone::Overlap) => (&pad.center, "Overlap · inner wins"),
            Some(PadZone::Outer(n)) => (&pad.outer[n], "Outer click"),
            None => (&pad.center, "Inner click"),
        }
    };
    let value = format!(
        "{caption} · {}{}",
        label(selected),
        if input.pressed { " · Pressed" } else { "" }
    );
    ui.ctx()
        .data_mut(|d| d.insert_temp(egui::Id::new(format!("pad:{side}:preview")), value.clone()));
    ui.label(
        RichText::new(value).color(if caption.starts_with("Overlap") {
            OVERLAP
        } else {
            ACCENT
        }),
    );
    if let Some(delay) = pad.repeat_ms.iter().flatten().next() {
        ui.small(format!("Scroll repeats after {delay} ms while touching."));
    } else if pad.regions.is_some() {
        ui.small("The center binding takes priority in the shared ring.");
    } else {
        ui.small("Click regions are blocked in this layer.");
    }
}
fn touch_caption(ui: &mut egui::Ui, pad: &TrackpadBindings) {
    if pad.swipe.is_some() {
        ui.label("Swipe toward a binding. No click needed.");
        ui.small("No double-tap touch binding on this pad.");
    } else if let Some(tap) = &pad.double_tap {
        ui.label("Double tap :: Circular scroll");
        ui.small(format!(
            "Lift before {} ms; touch the upper or lower edge again within {} ms.",
            tap.hold_ms, tap.window_ms
        ));
        ui.horizontal_wrapped(|ui| {
            ui.label(format!("Clockwise · {}", label(&tap.clockwise)));
            ui.label(format!(
                "Counterclockwise · {}",
                label(&tap.counterclockwise)
            ));
        });
        ui.small("Center or sides return to the pointer. Lift to end scrolling.");
    } else {
        ui.label(&pad.touch);
        ui.small("Double-tap touch is blocked in this layer.");
    }
}
