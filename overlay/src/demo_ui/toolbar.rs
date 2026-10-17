use super::{ACCENT, DemoApp, MUTED, target};
use crate::ui::Command;
use eframe::egui;

impl DemoApp {
    pub(super) fn toolbar(&mut self, ctx: &egui::Context) {
        egui::TopBottomPanel::top("demo.header").show(ctx, |ui| {
            ui.horizontal_wrapped(|ui| {
                ui.heading("Layout playground");
                ui.label(egui::RichText::new(self.session.engine.mode()).color(ACCENT));
                let mut index = self.selection;
                let response = egui::ComboBox::from_id_salt("demo.layout")
                    .selected_text(self.catalog[index].label())
                    .show_ui(ui, |ui| {
                        for (i, l) in self.catalog.iter().enumerate() {
                            let r = ui.selectable_value(&mut index, i, l.label());
                            target(ui, &format!("layout:{i}"), r.rect);
                        }
                    });
                target(ui, "layout", response.response.rect);
                if index != self.selection {
                    self.select_layout(index);
                }
                let downloads = ui.button("Download layouts");
                target(ui, "downloads", downloads.rect);
                if downloads.clicked() {
                    self.backend.command(Command::DownloadLayouts);
                }
                ui.checkbox(&mut self.inspector, "Details");
            });
            self.playback_controls(ui);
        });
    }
    fn playback_controls(&mut self, ui: &mut egui::Ui) {
        ui.horizontal_wrapped(|ui| {
            let mut scale = self.session.scale;
            for (value, label) in [
                (1, "1x"),
                (2, "1/2 speed"),
                (5, "1/5 speed"),
                (10, "1/10 speed"),
            ] {
                let r = ui.selectable_value(&mut scale, value, label);
                target(ui, &format!("speed:{value}"), r.rect);
            }
            self.session.scale = scale;
            let pause = ui.button(if self.session.paused {
                "Resume"
            } else {
                "Pause"
            });
            target(ui, "pause", pause.rect);
            if pause.clicked() {
                self.session.paused = !self.session.paused;
                self.capture = None;
                self.cancel_sound();
            }
            let step = ui.button("Next event");
            target(ui, "step", step.rect);
            if step.clicked() {
                self.session.step();
            }
            let replay = ui.add_enabled(
                !self.session.recording.is_empty(),
                egui::Button::new("Replay"),
            );
            target(ui, "replay", replay.rect);
            if replay.clicked() {
                self.cancel_sound();
                self.session.replay();
                self.feedback_seen = 0;
                self.pinned.clear();
                self.capture = None;
            }
            let reset = ui.button("Reset");
            target(ui, "reset", reset.rect);
            if reset.clicked() {
                self.reset();
            }
            let sound = ui.checkbox(&mut self.sound, "Sound");
            target(ui, "sound", sound.rect);
            if sound.changed() {
                self.enable_sound();
            }
            self.source_selector(ui);
        });
    }
    fn source_selector(&mut self, ui: &mut egui::Ui) {
        let data = self.backend.data();
        let before = self.source.clone();
        let name = self
            .source
            .as_ref()
            .and_then(|id| data.settings.devices.iter().find(|d| &d.id == id))
            .map(|d| d.name.as_str())
            .unwrap_or(if self.source.as_deref() == Some("companion") {
                "Companion (sampled input)"
            } else {
                "Mouse"
            });
        let selector = egui::ComboBox::from_id_salt("demo.input")
            .selected_text(name)
            .show_ui(ui, |ui| {
                let response = ui.selectable_value(&mut self.source, None, "Mouse");
                target(ui, "source:mouse", response.rect);
                if data.remote {
                    ui.selectable_value(
                        &mut self.source,
                        Some("companion".into()),
                        "Companion (sampled input)",
                    );
                }
                for device in data.settings.devices.iter().filter(|d| d.standard) {
                    let response = ui.selectable_value(
                        &mut self.source,
                        Some(device.id.clone()),
                        &device.name,
                    );
                    target(ui, &format!("source:{}", device.id), response.rect);
                }
            });
        target(ui, "source", selector.response.rect);
        if self.source != before {
            self.reset();
            self.gyro_bias = [0; 3];
            self.backend.command(Command::Select(self.source.clone()));
        }
        if let Some(connection) = data.browser_connection {
            let r = ui.add_enabled(
                connection.available && !connection.busy,
                egui::Button::new(if connection.connected {
                    "Disconnect"
                } else {
                    "Connect controller"
                }),
            );
            target(ui, "connect", r.rect);
            if r.clicked() {
                self.backend.command(if connection.connected {
                    Command::DisconnectController
                } else {
                    Command::ConnectController
                });
            }
            r.on_hover_text(connection.message);
        }
    }
    pub(super) fn timeline(&self, ctx: &egui::Context) {
        egui::TopBottomPanel::top("demo.timeline")
            .exact_height(44.)
            .show(ctx, |ui| {
                let timers = self.session.engine.timers();
                if timers.is_empty() {
                    return;
                }
                ui.horizontal(|ui| {
                    for timer in timers.iter().take(3) {
                        let start = timer["start"].as_u64().unwrap_or(0);
                        let due = timer["due"].as_u64().unwrap_or(start + 1);
                        let fraction =
                            (self.session.engine.now - start) as f32 / (due - start).max(1) as f32;
                        ui.vertical(|ui| {
                            ui.label(
                                egui::RichText::new(timer["layer"].as_str().unwrap_or(""))
                                    .small()
                                    .color(MUTED),
                            );
                            ui.add(
                                egui::ProgressBar::new(fraction)
                                    .desired_width(210.)
                                    .desired_height(4.)
                                    .fill(ACCENT),
                            );
                        });
                    }
                    if timers.len() > 3 {
                        ui.label(format!("+{} timers", timers.len() - 3));
                    }
                });
            });
    }
}
