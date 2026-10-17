use super::*;

fn scene(orders: &[egui::Order], clipped: bool) -> egui::Context {
    let ctx = egui::Context::default();
    let rect = egui::Rect::from_min_size(egui::pos2(100.0, 100.0), egui::vec2(100.0, 100.0));
    for frame in 0..3 {
        let _ = ctx.run(
            egui::RawInput {
                screen_rect: Some(egui::Rect::from_min_size(
                    egui::Pos2::ZERO,
                    egui::vec2(600.0, 400.0),
                )),
                time: Some(f64::from(frame) / 60.0),
                ..Default::default()
            },
            |ctx| {
                egui::CentralPanel::default().show(ctx, |ui| {
                    if clipped {
                        ui.set_clip_rect(egui::Rect::from_min_max(
                            egui::Pos2::ZERO,
                            egui::pos2(80.0, 80.0),
                        ));
                    }
                    let response = ui.interact(
                        rect,
                        egui::Id::new("test-control"),
                        egui::Sense::click_and_drag(),
                    );
                    register(ui, Control::A, &response);
                });
                for (index, order) in orders.iter().enumerate() {
                    egui::Area::new(egui::Id::new(("cover", index)))
                        .order(*order)
                        .fixed_pos(rect.min)
                        .interactable(true)
                        .show(ctx, |ui| {
                            ui.allocate_exact_size(rect.size(), egui::Sense::hover());
                        });
                }
            },
        );
    }
    ctx
}

#[test]
fn tooltip_does_not_eat_a_controller_press_after_hovering() {
    let ctx = scene(&[egui::Order::Tooltip], false);
    let pos = egui::pos2(150.0, 150.0);
    assert_eq!(ctx.layer_id_at(pos).unwrap().order, egui::Order::Tooltip);
    assert_eq!(MousePreview::hit(&ctx, pos), Some(Control::A));
}

#[test]
fn settings_and_popups_still_block_controls_beneath_tooltips() {
    for order in [egui::Order::Middle, egui::Order::Foreground] {
        let ctx = scene(&[order, egui::Order::Tooltip], false);
        let pos = egui::pos2(150.0, 150.0);
        assert_eq!(ctx.layer_id_at(pos).unwrap().order, egui::Order::Tooltip);
        assert_eq!(MousePreview::hit(&ctx, pos), None);
        let ctx = scene(&[order], false);
        assert_eq!(MousePreview::hit(&ctx, pos), None);
    }
}

#[test]
fn clipped_controls_remain_unavailable_even_under_a_tooltip() {
    let ctx = scene(&[egui::Order::Tooltip], true);
    assert_eq!(MousePreview::hit(&ctx, egui::pos2(150.0, 150.0)), None);
}
