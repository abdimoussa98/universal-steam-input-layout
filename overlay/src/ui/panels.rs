use super::*;

impl OverlayApp {
    fn mode_buttons(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        ui.horizontal_wrapped(|ui| {
            for (i, mode) in Mode::ALL.into_iter().enumerate() {
                let label = format!("{}  F{}", mode.label(), data.settings.hotkeys[i]);
                let selected = data.state.mode == mode;
                let response = ui.add(
                    egui::Button::new(RichText::new(label).color(if selected {
                        ACCENT
                    } else {
                        MUTED
                    }))
                    .selected(selected)
                    .corner_radius(8.0)
                    .min_size(egui::vec2(100.0, 36.0)),
                );
                target(ui, &format!("mode:{i}"), &response);
                if response.clicked() {
                    self.backend.command(Command::Mode(mode));
                }
            }
            if !data.native && !data.hud {
                let response =
                    ui.add(egui::Button::new("Download layouts").min_size(egui::vec2(120.0, 36.0)));
                target(ui, "downloads", &response);
                if response.clicked() {
                    self.backend.command(Command::DownloadLayouts);
                }
            }
        });
    }
    pub(super) fn viewer(&mut self, ctx: &egui::Context, data: &FrameData, now: u64) {
        let fill = Color32::from_rgba_unmultiplied(
            BACKGROUND.r(),
            BACKGROUND.g(),
            BACKGROUND.b(),
            if data.native {
                (data.preferences.opacity * 255.0) as u8
            } else {
                255
            },
        );

        egui::CentralPanel::default()
            .frame(egui::Frame::new().fill(fill).inner_margin(20.0))
            .show(ctx, |ui| {
                let width = ui.available_width().min(1000.0);
                ui.with_layout(egui::Layout::left_to_right(egui::Align::Min), |ui| {
                    ui.add_space(((ui.available_width() - width) / 2.0).max(0.0));
                    ui.vertical(|ui| {
                        ui.set_width(width);
                        ui.add_space(8.0);
                        self.heading(ui, data);
                        ui.label(RichText::new(&data.profile.name).size(12.0).color(MUTED));
                        ui.add_space(12.0);
                        self.mode_buttons(ui, data);
                        if !data.hud {
                            self.timing_controls(ui, data);
                        }
                        timelines::draw(ui, data, now);
                        self.content(ui, data);
                    });
                });
            });
    }
    fn heading(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        ui.horizontal(|ui| {
            ui.vertical(|ui| {
                ui.label(RichText::new("STEAM INPUT").size(10.0).color(MUTED));
                ui.label(RichText::new("Binding reference").size(26.0).strong());
            });
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if !data.hud {
                    let response = ui.button(if self.show_settings {
                        "Close settings"
                    } else {
                        "Settings"
                    });
                    target(ui, "settings", &response);
                    if response.clicked() {
                        self.show_settings = !self.show_settings;
                        self.draft = data.display_preferences();
                    }
                }
            });
        });
    }
    fn timing_controls(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        ui.horizontal_wrapped(|ui| {
            ui.label(RichText::new("Gesture slow motion").size(12.0).color(MUTED));
            let mut scale = data.state.timing_scale();
            let response = ui.add(
                egui::Slider::new(&mut scale, 1..=10)
                    .suffix("× longer")
                    .show_value(true),
            );
            target(ui, "timing-scale", &response);
            target_point(
                ui,
                "timing-scale:slow",
                egui::pos2(
                    response.rect.left() + ui.spacing().slider_width - 4.0,
                    response.rect.center().y,
                ),
            );
            if response.changed() {
                self.backend.command(Command::TimingScale(scale));
            }
            if scale > 1 {
                let response = ui.small_button("Normal speed");
                target(ui, "timing-normal", &response);
                if response.clicked() {
                    self.backend.command(Command::TimingScale(1));
                }
                ui.label(
                    RichText::new("Viewer preview only · Steam unchanged")
                        .size(12.0)
                        .color(ACCENT),
                );
            }
        });
        if data.state.timing_scale() > 1 {
            ui.label(RichText::new("Hold or tap, then hold a button with your mouse or controller. Release held buttons after changing speed.").size(12.0).color(MUTED));
        }
    }
    fn content(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        let content_height =
            (ui.ctx().screen_rect().bottom() - ui.cursor().min.y - 20.0).max(100.0);
        egui::ScrollArea::vertical()
            .id_salt("viewer-content")
            .max_height(content_height)
            .auto_shrink([false, false])
            .show(ui, |ui| {
                self.controller_panel(ui, data);
                ui.add_space(4.0);
                trackpads::explorer(ui, data);
                ui.add_space(8.0);
                reading_help(ui, data);
                if let Some(error) = data.error.as_ref().or(data.settings.error.as_ref()) {
                    ui.colored_label(Color32::LIGHT_RED, error);
                }
            });
    }
    fn controller_panel(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        egui::Frame::new()
            .fill(SURFACE)
            .corner_radius(14.0)
            .stroke(egui::Stroke::new(1.0_f32, BORDER))
            .inner_margin(16.0)
            .show(ui, |ui| {
                self.connection_controls(ui, data);
                ui.add_space(8.0);
                // Keep diagram labels legible on small windows; only the diagram scrolls sideways.
                egui::ScrollArea::horizontal()
                    .id_salt("controller-diagram")
                    .show(ui, |ui| {
                        ui.set_min_width(720.0);
                        controller::draw(ui, data);
                    });
                ui.add_space(6.0);
                ui.label(
                    RichText::new(data.input_status_label())
                        .size(12.0)
                        .color(MUTED),
                );
                if let Some(connection) = &data.browser_connection
                    && !connection
                        .message
                        .starts_with("Connect your Steam Controller")
                {
                    ui.label(RichText::new(&connection.message).size(12.0).color(MUTED));
                }
            });
    }
    fn connection_controls(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        ui.horizontal_wrapped(|ui| {
            let preview = data.state.device.as_deref() == Some("viewer-mouse");
            let live = data.state.status == InputStatus::Live;
            ui.label(
                RichText::new(if preview {
                    "Mouse preview"
                } else if live {
                    "Live input"
                } else {
                    "Reference"
                })
                .color(if live { ACCENT } else { MUTED }),
            );
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if let Some(connection) = &data.browser_connection {
                    let response = ui.add_enabled(
                        connection.available && !connection.busy,
                        egui::Button::new(if connection.busy {
                            "Please wait…"
                        } else if connection.connected {
                            "Disconnect controller"
                        } else {
                            "Connect controller"
                        }),
                    );
                    target(
                        ui,
                        if connection.connected {
                            "disconnect"
                        } else {
                            "connect"
                        },
                        &response,
                    );
                    if response.clicked() {
                        self.backend.command(if connection.connected {
                            Command::DisconnectController
                        } else {
                            Command::ConnectController
                        });
                    }
                }
            });
        });
    }
}
fn reading_help(ui: &mut egui::Ui, data: &FrameData) {
    ui.collapsing("Reading this view", |ui| {
        ui.label("Choose the mode to match Steam. Labels describe a fresh press in the current layer.");
        ui.label("Click and hold any controller button to preview it. Right-click to hold or release a button while you try another button or trackpad. Mouse previews stay in the viewer.");
        ui.label("Stick dots show X/Y travel; green rings mean thumb contact. Trackpad dots show thumb position. Trigger bars show travel; Full means a full pull.");
        ui.label("Bumpers: Mod 0 :: Scroll down and Mod 1 :: Scroll up mean hold the modifier, or tap then hold to scroll. Menu buttons: Escape :: Fn and Tab :: Fn show the key and function-layer alternatives.");
        ui.label("At 1×, gestures follow the layout’s configured delays. Slow motion stretches the viewer’s hold, release-window and second-hold timings together. It does not change Steam or send game input.");
        ui.label("Enter :: Menu and Backspace :: Menu show tap-then-hold key output versus holding to enter Menu, depending on which menu button you press first.");
        if let Some(help) = data.controller_help() { ui.label(help); }
    });
}
