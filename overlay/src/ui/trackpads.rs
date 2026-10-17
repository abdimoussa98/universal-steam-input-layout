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

/// Same schematic zones on the small controller pads and the enlarged explorer.
/// Text stays upright even though the physical pad is canted.
pub(super) fn field(
    p: &egui::Painter,
    center: egui::Pos2,
    half: f32,
    angle: f32,
    pad: &TrackpadBindings,
    touch_view: bool,
    preview: Option<[f32; 2]>,
) {
    let at = |x: f32, y: f32| {
        center
            + egui::vec2(
                x * angle.cos() - y * angle.sin(),
                x * angle.sin() + y * angle.cos(),
            ) * half
    };
    let active = preview.map(|[x, y]| preview_pad_zone(x, y));
    let detailed = half > 85.0;
    let size = if detailed { 14.0 } else { 10.0 };
    if !touch_view {
        if pad.regions.is_some() {
            // Outer wedges first, center last: the shared band belongs to center.
            for n in 0..4 {
                let start = -135.0 + n as f32 * 90.0;
                let mut polygon = vec![center];
                for i in 0..=16 {
                    let a = (start + i as f32 * 90.0 / 16.0).to_radians();
                    polygon.push(at(a.cos() * 0.96, a.sin() * 0.96));
                }
                p.add(egui::Shape::convex_polygon(
                    polygon,
                    if active == Some(PadZone::Outer(n)) {
                        Color32::from_rgb(37, 77, 67)
                    } else {
                        Color32::from_rgb(28, 35, 41)
                    },
                    egui::Stroke::new(1.0_f32, BORDER),
                ));
            }
            p.circle_filled(
                center,
                half * PAD_INNER_RADIUS,
                if matches!(active, Some(PadZone::Inner | PadZone::Overlap)) {
                    Color32::from_rgb(42, 71, 65)
                } else {
                    Color32::from_rgb(29, 44, 43)
                },
            );
            let band = (PAD_INNER_RADIUS - PAD_OUTER_START) * half;
            p.circle_stroke(
                center,
                (PAD_INNER_RADIUS + PAD_OUTER_START) * half / 2.0,
                egui::Stroke::new(
                    band,
                    if active == Some(PadZone::Overlap) {
                        OVERLAP
                    } else {
                        Color32::from_rgb(101, 84, 57)
                    },
                ),
            );
            p.circle_stroke(
                center,
                PAD_INNER_RADIUS * half,
                egui::Stroke::new(1.0_f32, OVERLAP.gamma_multiply(0.65)),
            );
        }
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
    if let Some([x, y]) = preview {
        let dot = at(x, y);
        p.circle_filled(dot, 3.0, Color32::WHITE);
        p.circle_stroke(dot, 6.0, egui::Stroke::new(1.0_f32, Color32::WHITE));
    }
}

pub(super) fn explorer(ui: &mut egui::Ui, data: &FrameData, touch_view: &mut bool) {
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
        ui.horizontal_wrapped(|ui| {
            ui.label(RichText::new("Trackpads").size(19.0).color(Color32::WHITE));
            for (value,title) in [(false,"Click zones"),(true,"Touch gestures")] {
                let response=ui.selectable_label(*touch_view==value,title);
                target(ui,if value {"pads:touch"} else {"pads:click"},&response);
                if response.clicked() {*touch_view=value;}
            }
        });
        ui.add_space(8.0);
        if *touch_view {
            ui.label(RichText::new("Swipes and double-tap touch bindings for the current layer.").color(MUTED));
        } else {
            ui.horizontal_wrapped(|ui| {
                ui.colored_label(ACCENT,"Inner click");
                ui.colored_label(OVERLAP,"Overlap · inner wins");
                ui.label("Outer click");
            });
            ui.label(RichText::new("Hover or drag across a pad to preview its binding.").size(12.0).color(MUTED))
                .on_hover_text("Zone sizes are schematic. Steam's raw Soft Press thresholds are not a calibrated touch radius.");
        }
        ui.add_space(12.0);
        if ui.available_width()>=620.0 {
            ui.columns(2,|cols| {for side in 0..2 {card(&mut cols[side],side,&pads[side],*touch_view);}});
        } else {
            for (side,pad) in pads.iter().enumerate() {card(ui,side,pad,*touch_view);ui.add_space(12.0);}
        }
    });
}

fn card(ui: &mut egui::Ui, side: usize, pad: &TrackpadBindings, touch_view: bool) {
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
            let (area, response) = ui.allocate_exact_size(
                egui::vec2(ui.available_width(), half * 2.0 + 24.0),
                egui::Sense::click_and_drag(),
            );
            let center = area.center();
            let bounds = egui::Rect::from_center_size(center, egui::vec2(half * 2.0, half * 2.0));
            let preview = ui
                .input(|i| i.pointer.hover_pos())
                .filter(|pos| bounds.contains(*pos) && response.contains_pointer())
                .map(|pos| [(pos.x - center.x) / half, (pos.y - center.y) / half]);
            let painter = ui.painter();
            painter.rect_filled(bounds, 18.0, Color32::from_rgb(25, 30, 36));
            painter.rect_stroke(
                bounds,
                18.0,
                egui::Stroke::new(1.0_f32, BORDER),
                egui::StrokeKind::Inside,
            );
            field(painter, center, half, 0.0, pad, touch_view, preview);
            target_point(ui, &format!("pad:{side}:center"), center);
            target_point(
                ui,
                &format!("pad:{side}:overlap"),
                center + egui::vec2(half * (PAD_INNER_RADIUS + PAD_OUTER_START) / 2.0, 0.0),
            );
            target_point(
                ui,
                &format!("pad:{side}:outer"),
                center + egui::vec2(half * 0.84, 0.0),
            );
            if !touch_view {
                let (selected, caption) = if pad.regions.is_none() {
                    (&pad.center, "Click")
                } else {
                    match preview.map(|[x, y]| preview_pad_zone(x, y)) {
                        Some(PadZone::Inner) => (&pad.center, "Inner click"),
                        Some(PadZone::Overlap) => (&pad.center, "Overlap · inner wins"),
                        Some(PadZone::Outer(n)) => (&pad.outer[n], "Outer click"),
                        None => (&pad.center, "Inner click"),
                    }
                };
                let value = format!("{caption} · {}", label(selected));
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
