//! Mouse capture and local button previews shared by the browser and desktop UI.
use super::*;
use std::collections::BTreeMap;

#[cfg(test)]
mod tests;

#[derive(Clone)]
struct HitTarget {
    rect: egui::Rect,
    layer: egui::LayerId,
}

pub(super) fn register(ui: &egui::Ui, control: Control, response: &egui::Response) {
    if response.enabled() {
        ui.ctx().data_mut(|d| {
            d.get_temp_mut_or_default::<BTreeMap<Control, HitTarget>>(egui::Id::new(
                "keybind.controls",
            ))
            .insert(
                control,
                HitTarget {
                    rect: response.rect.intersect(ui.clip_rect()),
                    layer: ui.layer_id(),
                },
            );
        });
    }
}

#[derive(Default)]
pub(super) struct MousePreview {
    preview: preview::Preview,
    captured: Option<Control>,
    pinned: [bool; 16],
}

impl MousePreview {
    pub(super) fn frame(&mut self, ctx: &egui::Context, source: &FrameData) -> FrameData {
        let now = ctx.input(|i| (i.time.max(0.0) * 1000.0) as u64);
        let was_active = self.preview.active();
        let _ = self.preview.update(source, now);
        if was_active && !self.preview.active() {
            self.reset_capture();
        }
        let events = ctx.input(|i| i.events.clone());
        if !ctx.input(|i| i.focused) || source.state.status == InputStatus::Paused {
            self.cancel();
        } else {
            for event in events {
                self.event(ctx, source, now, event);
            }
        }
        let mut data = source.clone();
        if let Some(state) = self.preview.update(source, now) {
            data.state = state;
            ctx.request_repaint_after(std::time::Duration::from_millis(16));
        }
        ctx.data_mut(|d| {
            d.insert_temp(
                egui::Id::new("keybind.mouse-preview"),
                self.preview.active(),
            );
            d.insert_temp(egui::Id::new("keybind.rendered-state"), data.state.clone());
            d.insert_temp(
                egui::Id::new("keybind.controls"),
                BTreeMap::<Control, HitTarget>::new(),
            );
        });
        data
    }

    fn event(&mut self, ctx: &egui::Context, data: &FrameData, now: u64, event: egui::Event) {
        match event {
            egui::Event::WindowFocused(false) | egui::Event::PointerGone => self.cancel(),
            egui::Event::PointerButton {
                pos,
                button,
                pressed,
                ..
            } => {
                let hit = Self::hit(ctx, pos);
                match (button, pressed) {
                    (egui::PointerButton::Primary, true) => {
                        self.captured = hit;
                        if let Some(control) = hit {
                            self.preview.set(control, true, data, now);
                        }
                    }
                    (egui::PointerButton::Primary, false) => {
                        if let Some(control) = self.captured.take() {
                            self.preview
                                .set(control, self.pinned[control as usize], data, now);
                        }
                    }
                    (egui::PointerButton::Secondary, true) => {
                        if let Some(control) = hit {
                            let pinned = &mut self.pinned[control as usize];
                            *pinned = !*pinned;
                            self.preview
                                .set(control, *pinned || self.captured == hit, data, now);
                        }
                    }
                    _ => {}
                }
            }
            _ => {}
        }
    }

    fn hit(ctx: &egui::Context, pos: egui::Pos2) -> Option<Control> {
        let targets = ctx.data(|d| {
            d.get_temp::<BTreeMap<Control, HitTarget>>(egui::Id::new("keybind.controls"))
        })?;
        targets
            .into_iter()
            .find(|(_, target)| target.rect.contains(pos) && uncovered(ctx, target.layer, pos))
            .map(|(control, _)| control)
    }

    fn reset_capture(&mut self) {
        self.captured = None;
        self.pinned = [false; 16];
    }

    fn cancel(&mut self) {
        self.preview.cancel();
        self.reset_capture();
    }
}

fn uncovered(ctx: &egui::Context, layer: egui::LayerId, pos: egui::Pos2) -> bool {
    let top = ctx.layer_id_at(pos);
    if top == Some(layer) {
        return true;
    }
    if !top.is_some_and(|top| top.order == egui::Order::Tooltip)
        || !ctx.memory(|memory| memory.is_above_modal_layer(layer))
    {
        return false;
    }
    // Tooltip areas can be interactable for text selection. They must not eat
    // a controller press, but a window or popup beneath them still blocks it.
    let visible = ctx.memory(|memory| memory.areas().visible_layer_ids());
    !visible.into_iter().any(|other| {
        other != layer
            && other.order >= layer.order
            && other.order != egui::Order::Tooltip
            && egui::AreaState::load(ctx, other.id).is_some_and(|area| {
                let rect = ctx
                    .layer_transform_to_global(other)
                    .map_or(area.rect(), |transform| transform * area.rect());
                area.interactable && rect.contains(pos)
            })
    })
}
