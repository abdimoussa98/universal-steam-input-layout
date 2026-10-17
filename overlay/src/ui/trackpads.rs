use super::*;

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

fn text(p: &egui::Painter, center: egui::Pos2, value: &str, width: f32, size: f32, color: Color32) {
    let direction = match value {
        "↑" => Some(egui::vec2(0.0, -1.0)),
        "→" => Some(egui::vec2(1.0, 0.0)),
        "↓" => Some(egui::vec2(0.0, 1.0)),
        "←" => Some(egui::vec2(-1.0, 0.0)),
        _ => None,
    };
    if let Some(d) = direction {
        p.arrow(
            center - d * size * 0.45,
            d * size * 0.9,
            egui::Stroke::new(1.5_f32, color),
        );
        return;
    }
    let mut job =
        egui::text::LayoutJob::simple(value.into(), egui::FontId::proportional(size), color, width);
    job.halign = egui::Align::Center;
    job.wrap.max_rows = 2;
    let galley = p.layout_job(job);
    p.galley(
        center - egui::vec2(0.0, galley.size().y / 2.0),
        galley,
        color,
    );
}

#[derive(Clone, Copy, Default)]
pub(super) struct Feedback {
    pub position: Option<[f32; 2]>,
    pub pressed: bool,
    pub live: bool,
}

pub(super) fn feedback(
    ui: &egui::Ui,
    data: &FrameData,
    side: usize,
    hover: Option<[f32; 2]>,
) -> Feedback {
    let key = egui::Id::new(format!("pad:{side}:pressure-pressed"));
    let pressed = ui.ctx().data_mut(|d| {
        let force = d
            .get_temp::<u16>(egui::Id::new("pad:click-force"))
            .unwrap_or(15);
        let was_pressed = d.get_temp::<bool>(key).unwrap_or(false);
        let pressed = data.state.status == InputStatus::Live
            && data.state.input.pad_pressed(side, force * 10, was_pressed);
        d.insert_temp(key, pressed);
        pressed
    });
    if data.state.status == InputStatus::Live {
        if let Some(touch) = data.state.input.pads[side]
            .as_ref()
            .filter(|pad| pad.touching)
        {
            return Feedback {
                position: Some(
                    touch
                        .position
                        .map(|v| f32::from(v.clamp(-1000, 1000)) / 1000.0),
                ),
                pressed,
                live: true,
            };
        }
        if pressed {
            return Feedback {
                position: None,
                pressed: true,
                live: true,
            };
        }
    }
    Feedback {
        position: hover,
        pressed: hover.is_some() && ui.input(|i| i.pointer.primary_down()),
        ..Feedback::default()
    }
}

pub(super) fn hover(ui: &egui::Ui, center: egui::Pos2, half: f32, angle: f32) -> Option<[f32; 2]> {
    if !ui.rect_contains_pointer(egui::Rect::from_center_size(
        center,
        egui::vec2(half * 2.3, half * 2.3),
    )) {
        return None;
    }
    ui.input(|i| i.pointer.hover_pos()).and_then(|pos| {
        let delta = (pos - center) / half;
        let xy = [
            delta.x * angle.cos() + delta.y * angle.sin(),
            -delta.x * angle.sin() + delta.y * angle.cos(),
        ];
        let distance = xy[0].hypot(xy[1]);
        (distance <= pad_edge(xy[1].atan2(xy[0]))).then_some(xy)
    })
}

fn pad_edge(angle: f32) -> f32 {
    let (x, y) = (angle.cos().abs(), angle.sin().abs());
    let corner = 62.0 / 82.0;
    let radius = 20.0 / 82.0;
    if y <= corner * x {
        1.0 / x
    } else if x <= corner * y {
        1.0 / y
    } else {
        corner * (x + y)
            + (radius * radius - corner * corner * (x - y) * (x - y))
                .max(0.0)
                .sqrt()
    }
}

pub(super) fn record_feedback(ui: &egui::Ui, side: usize, pad: &TrackpadBindings, input: Feedback) {
    let zone = match input
        .position
        .and_then(|xy| pad.regions.as_ref().map(|r| r.zone(xy)))
    {
        Some(PadZone::Inner) => "inner".to_string(),
        Some(PadZone::Overlap) => "overlap".into(),
        Some(PadZone::Outer(n)) => format!("outer{n}"),
        None => "none".into(),
    };
    let value = format!(
        "{}:{zone}:{}",
        if input.live {
            "live"
        } else if input.position.is_some() {
            "hover"
        } else {
            "idle"
        },
        if input.pressed { "pressed" } else { "released" }
    );
    ui.ctx()
        .data_mut(|d| d.insert_temp(egui::Id::new(format!("pad:{side}:feedback")), value));
    ui.ctx().data_mut(|d| {
        d.insert_temp(
            egui::Id::new(format!("pad:{side}:layer")),
            if input.pressed {
                "click".to_string()
            } else {
                "touch".to_string()
            },
        )
    });
}

/// The same configured zones and light feedback on both pad views.
pub(super) fn field(
    p: &egui::Painter,
    center: egui::Pos2,
    half: f32,
    angle: f32,
    pad: &TrackpadBindings,
    input: Feedback,
) {
    let at = |x: f32, y: f32| {
        center
            + egui::vec2(
                x * angle.cos() - y * angle.sin(),
                x * angle.sin() + y * angle.cos(),
            ) * half
    };
    let active = input
        .position
        .and_then(|xy| pad.regions.as_ref().map(|r| r.zone(xy)));
    let detailed = half > 85.0;
    let size = if detailed { 14.0 } else { 10.0 };
    {
        let outline: Vec<_> = (0..=96)
            .map(|i| {
                let angle = i as f32 * std::f32::consts::TAU / 96.0;
                let radius = pad_edge(angle);
                at(angle.cos() * radius, angle.sin() * radius)
            })
            .collect();
        let tint =
            Color32::from_rgba_unmultiplied(119, 211, 182, if input.pressed { 8 } else { 4 });
        let edge =
            Color32::from_rgba_unmultiplied(119, 211, 182, if input.pressed { 70 } else { 18 });
        if let Some(regions) = &pad.regions {
            // Neutral guides stay visible through a light, whole-pad center tint.
            p.circle_stroke(
                center,
                half * regions.inner_radius(),
                egui::Stroke::new(1.0_f32, Color32::from_white_alpha(7)),
            );
            p.circle_stroke(
                center,
                half * regions.outer_start(),
                egui::Stroke::new(1.0_f32, Color32::from_white_alpha(4)),
            );
            if matches!(active, Some(PadZone::Inner | PadZone::Overlap)) {
                p.add(egui::Shape::convex_polygon(
                    outline.clone(),
                    tint,
                    egui::Stroke::new(1.0_f32, edge),
                ));
            }
            if let Some(PadZone::Outer(n)) = active {
                let start = (-135.0 + n as f32 * 90.0).to_radians();
                for i in 0..24 {
                    let a = start + i as f32 * std::f32::consts::FRAC_PI_2 / 24.0;
                    let b = start + (i + 1) as f32 * std::f32::consts::FRAC_PI_2 / 24.0;
                    let point =
                        |angle: f32, radius: f32| at(angle.cos() * radius, angle.sin() * radius);
                    let inner = regions.inner_radius();
                    p.add(egui::Shape::convex_polygon(
                        vec![
                            point(a, inner),
                            point(a, pad_edge(a)),
                            point(b, pad_edge(b)),
                            point(b, inner),
                        ],
                        tint,
                        egui::Stroke::NONE,
                    ));
                    p.line_segment(
                        [point(a, pad_edge(a)), point(b, pad_edge(b))],
                        egui::Stroke::new(if input.pressed { 1.8_f32 } else { 1.0_f32 }, edge),
                    );
                }
            }
        } else if input.position.is_some() && matches!(pad.center, Binding::Label { .. }) {
            p.add(egui::Shape::convex_polygon(
                outline.clone(),
                tint,
                egui::Stroke::new(1.0_f32, edge),
            ));
        }
        if input.pressed && active.is_none() {
            p.add(egui::Shape::closed_line(
                outline,
                egui::Stroke::new(1.8_f32, edge),
            ));
        }
    }
    if input.pressed {
        text(
            p,
            center,
            &label(&pad.center),
            half * 0.75,
            size,
            Color32::WHITE,
        );
        if pad.regions.is_some() {
            for (n, (x, y)) in [(0.0, -0.79), (0.79, 0.0), (0.0, 0.79), (-0.79, 0.0)]
                .into_iter()
                .enumerate()
            {
                let value = label(&pad.outer[n]);
                let value = if !detailed && value == "Forward" {
                    "Fwd".into()
                } else {
                    value
                };
                text(
                    p,
                    at(x, y),
                    &value,
                    if n % 2 == 0 { half * 1.2 } else { half * 0.46 },
                    if detailed && n % 2 == 1 { 12.0 } else { size },
                    if active == Some(PadZone::Outer(n)) {
                        ACCENT
                    } else {
                        Color32::from_gray(222)
                    },
                );
            }
        }
    } else if let Some(swipes) = &pad.swipe {
        for (n, (x, y)) in [(0.0, -0.72), (0.72, 0.0), (0.0, 0.72), (-0.72, 0.0)]
            .into_iter()
            .enumerate()
        {
            let delta = at(x * 0.65, y * 0.65) - center;
            p.arrow(
                center + delta * 0.28,
                delta * 0.55,
                egui::Stroke::new(1.3_f32, ACCENT),
            );
            let value = label(&swipes[n]);
            let value = if !detailed && value == "Escape" {
                "Esc".into()
            } else {
                value
            };
            text(
                p,
                at(x, y),
                &value,
                if n % 2 == 0 { half * 1.4 } else { half * 0.52 },
                size,
                Color32::WHITE,
            );
        }
    } else if pad.double_tap.is_some() {
        for sign in [-1.0, 1.0] {
            let points: Vec<_> = (0..=24)
                .map(|i| {
                    let a = (30.0 + i as f32 * 120.0 / 24.0).to_radians();
                    at(a.cos() * 0.81, a.sin() * sign * 0.81)
                })
                .collect();
            p.add(egui::Shape::line(
                points,
                egui::Stroke::new(5.0_f32, ACCENT.gamma_multiply(0.8)),
            ));
        }
        text(p, center, "Pointer", half * 1.1, size, Color32::WHITE);
        text(p, at(0.0, -0.60), "Scroll", half, size, ACCENT);
        text(p, at(0.0, 0.60), "Scroll", half, size, ACCENT);
    } else {
        text(p, center, &pad.touch, half * 1.4, size, MUTED);
    }
    if let Some([x, y]) = input.position {
        let dot = at(x, y);
        let color = if input.live { ACCENT } else { Color32::WHITE };
        p.circle_stroke(
            dot,
            if input.pressed { 5.0 } else { 4.0 },
            egui::Stroke::new(if input.pressed { 2.0_f32 } else { 1.0_f32 }, color),
        );
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

fn card(ui: &mut egui::Ui, side: usize, pad: &TrackpadBindings, data: &FrameData) {
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
            let half = (ui.available_width() / 2.0 - 8.0).min(116.0);
            let (area, _) = ui.allocate_exact_size(
                egui::vec2(ui.available_width(), half * 2.0 + 24.0),
                egui::Sense::click_and_drag(),
            );
            let center = area.center();
            let bounds = egui::Rect::from_center_size(center, egui::vec2(half * 2.0, half * 2.0));
            let input = feedback(ui, data, side, hover(ui, center, half, 0.0));
            let painter = ui.painter();
            painter.rect_filled(bounds, 18.0, Color32::from_rgb(25, 30, 36));
            painter.rect_stroke(
                bounds,
                18.0,
                egui::Stroke::new(1.0_f32, BORDER),
                egui::StrokeKind::Inside,
            );
            field(painter, center, half, 0.0, pad, input);
            if !input.pressed {
                let value = if pad.swipe.is_some() {
                    "Touch · Swipe bindings".into()
                } else if pad.double_tap.is_some() {
                    "Touch · Pointer / Double tap to scroll".into()
                } else {
                    format!("Touch · {}", pad.touch)
                };
                ui.ctx().data_mut(|d| {
                    d.insert_temp(egui::Id::new(format!("pad:{side}:preview")), value)
                });
            }
            if input.live || input.position.is_some() {
                record_feedback(ui, side, pad, input);
            }
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
            if input.pressed {
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
                ui.ctx().data_mut(|d| {
                    d.insert_temp(egui::Id::new(format!("pad:{side}:preview")), value.clone())
                });
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
            } else if pad.swipe.is_some() {
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
        });
}
