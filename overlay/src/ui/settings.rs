use super::*;

impl OverlayApp {
    pub(super) fn settings_window(&mut self, ctx: &egui::Context, data: &FrameData) {
        if self.show_settings && !data.hud {
            egui::Window::new("Viewer settings")
                .id(egui::Id::new("settings-window"))
                .default_pos([28.0, 76.0])
                .default_width(430.0)
                .collapsible(false)
                .show(ctx, |ui| {
                    egui::ScrollArea::vertical()
                        .max_height(470.0)
                        .show(ui, |ui| self.settings(ui, data));
                });
        }
    }

    fn settings(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        if data.remote {
            self.draft.hotkeys = data.settings.hotkeys;
            ui.label("Controller, profile and shortcuts are managed in the native companion.");
        }
        ui.add_enabled_ui(!data.remote, |ui| {
            self.controller_picker(ui, data);
            self.shortcuts_settings(ui, data);
            self.profile_import(ui, data);
        });
        ui.add(egui::Slider::new(&mut self.draft.scale, 0.75..=2.0).text("Size"));
        if data.native {
            ui.add(
                egui::Slider::new(&mut self.draft.opacity, 0.25..=1.0).text("Background opacity"),
            );
        }
        let apply = ui.button("Apply settings");
        target(ui, "apply", &apply);
        if apply.clicked() {
            if data.remote {
                self.draft.hotkeys = data.settings.hotkeys;
            }
            self.backend
                .command(Command::Preferences(self.draft.clone()));
        }
        if data.native {
            self.native_settings(ui, data);
        }
        if let Some(url) = &data.companion_url {
            ui.hyperlink_to("Open browser companion", url);
        }
        if let Some(help) = data.controller_help() {
            ui.label(help);
        }
    }

    fn controller_picker(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        let selected = data.settings.selected.as_deref().unwrap_or("");
        let combo = egui::ComboBox::from_label("Controller")
            .selected_text(
                data.settings
                    .devices
                    .iter()
                    .find(|d| d.id == selected)
                    .map(|d| d.name.as_str())
                    .unwrap_or("Select a controller"),
            )
            .show_ui(ui, |ui| {
                if ui.selectable_label(selected.is_empty(), "None").clicked() {
                    self.backend.command(Command::Select(None));
                }
                for d in &data.settings.devices {
                    let response = ui.selectable_label(
                        selected == d.id,
                        format!(
                            "{} [{}]{}",
                            d.name,
                            d.id,
                            if d.standard {
                                ""
                            } else {
                                " · unsupported mapping"
                            }
                        ),
                    );
                    target(ui, &format!("device:{}", d.id), &response);
                    if response.clicked() {
                        self.backend.command(Command::Select(Some(d.id.clone())));
                    }
                }
            });
        target(ui, "controller", &combo.response);
        ui.label("Choose the physical controller. Steam may also expose a virtual one.");
    }

    fn shortcuts_settings(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        ui.horizontal(|ui| {
            for (i, label) in ["Base", "Steering", "Menu"].iter().enumerate() {
                ui.label(*label);
                ui.add(
                    egui::DragValue::new(&mut self.draft.hotkeys[i])
                        .range(1..=12)
                        .prefix("F"),
                );
            }
        });
        ui.label(if data.native { "Global shortcuts are reserved while this app runs." }
            else { "Shortcuts work when this page has keyboard focus; browser-reserved keys may need rebinding." });
    }

    fn profile_import(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        ui.collapsing("Import a display profile", |ui| {
            ui.label("Drop a profile JSON file onto the window, or paste its contents below.");
            ui.add(
                egui::TextEdit::multiline(&mut self.profile_json)
                    .desired_rows(4)
                    .desired_width(f32::INFINITY)
                    .code_editor(),
            );
            if ui.button("Load profile").clicked() {
                self.backend
                    .command(Command::Profile(self.profile_json.clone()));
            }
            ui.small(format!(
                "{} · {} · source {}",
                data.profile.controller, data.profile.variant, data.profile.source_version
            ));
        });
    }

    fn native_settings(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        ui.add_enabled_ui(data.recovery_available, |ui| {
            if ui.button("Enter click-through HUD").clicked() {
                self.backend.command(Command::Hud(true));
            }
            if data.companion_url.is_some() && ui.button("Hide window · use browser only").clicked()
            {
                self.backend.command(Command::Hide);
            }
        });
        ui.small("Ctrl+Alt+O returns to this window. Position it before entering HUD mode.");
        if !data.recovery_available {
            ui.colored_label(
                Color32::YELLOW,
                "HUD disabled: the recovery shortcut could not be registered.",
            );
        }
    }
}
