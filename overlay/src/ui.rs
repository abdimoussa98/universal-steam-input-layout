//! One interface used by both native eframe and WebRunner.
use crate::core::*;
use eframe::egui::{self, Color32, RichText};

const BACKGROUND: Color32 = Color32::from_rgb(17, 19, 23);
const SURFACE: Color32 = Color32::from_rgb(24, 27, 32);
const BORDER: Color32 = Color32::from_rgb(44, 49, 57);
const MUTED: Color32 = Color32::from_rgb(156, 164, 177);
const ACCENT: Color32 = Color32::from_rgb(125, 211, 184);

fn theme(ctx: &egui::Context) {
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

#[derive(Clone)]
pub struct FrameData {
    pub state: State,
    pub profile: Profile,
    pub settings: HostSettings,
    pub preferences: Preferences,
    pub native: bool,
    pub remote: bool,
    pub recovery_available: bool,
    pub hud: bool,
    pub companion_url: Option<String>,
    pub browser_connection: Option<BrowserConnection>,
    pub error: Option<String>,
}
#[derive(Clone, serde::Serialize)]
pub struct BrowserConnection {
    pub available: bool,
    pub busy: bool,
    pub connected: bool,
    pub message: String,
}
impl FrameData {
    fn browser_has_no_devices(&self) -> bool {
        !self.native
            && !self.remote
            && self.state.status == InputStatus::SelectDevice
            && self.settings.devices.is_empty()
    }
    pub fn input_status_label(&self) -> String {
        if self.browser_has_no_devices() {
            if self
                .browser_connection
                .as_ref()
                .is_some_and(|c| c.available)
            {
                "Connect a controller to begin".into()
            } else {
                "No controllers exposed by this browser".into()
            }
        } else if self.state.status == InputStatus::Live
            && let Some(device) = self
                .settings
                .devices
                .iter()
                .find(|d| self.state.device.as_deref() == Some(d.id.as_str()))
        {
            format!(
                "Live · {}{}",
                // Native names append diagnostic type/path fields; keep those
                // in Settings and show the friendly name in the main status.
                device.name.split(" · ").next().unwrap_or(&device.name),
                if self.remote { " · via helper" } else { "" }
            )
        } else {
            self.state.status.label().into()
        }
    }
    pub fn controller_help(&self) -> Option<&'static str> {
        self.browser_has_no_devices().then_some("For a Steam Controller 2, click Connect controller and select the controller or its wireless receiver in the browser picker. Other supported gamepads appear after pressing a controller button. Steam and a local helper are not required.")
    }
    pub fn display_preferences(&self) -> Preferences {
        let mut preferences = self.preferences.clone();
        if self.remote {
            preferences.hotkeys = self.settings.hotkeys;
        }
        preferences
    }
}
pub enum Command {
    ConnectController,
    DisconnectController,
    Mode(Mode),
    Select(Option<String>),
    Profile(String),
    Preferences(Preferences),
    Hud(bool),
    Hide,
    ImportPath(std::path::PathBuf),
}
pub trait Backend {
    fn data(&self) -> FrameData;
    fn command(&mut self, command: Command);
}
pub struct OverlayApp {
    backend: Box<dyn Backend>,
    show_settings: bool,
    profile_json: String,
    draft: Preferences,
    applied_scale: f32,
    host_clock: u64,
    clock_received: f64,
}
impl OverlayApp {
    pub fn new(cc: &eframe::CreationContext<'_>, backend: Box<dyn Backend>) -> Self {
        theme(&cc.egui_ctx);
        let draft = backend.data().display_preferences();
        Self {
            backend,
            show_settings: false,
            profile_json: String::new(),
            draft,
            applied_scale: 0.0,
            host_clock: 0,
            clock_received: 0.0,
        }
    }
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
        });
    }
    fn settings(&mut self, ui: &mut egui::Ui, data: &FrameData) {
        if data.remote {
            self.draft.hotkeys = data.settings.hotkeys;
            ui.label("Controller, profile and shortcuts are managed in the native companion.");
        }
        ui.add_enabled_ui(!data.remote, |ui| {
            let selected = data.settings.selected.as_deref().unwrap_or("");
            let combo = egui::ComboBox::from_label("Controller")
                .selected_text(data.settings.devices.iter().find(|d| d.id == selected).map(|d| d.name.as_str()).unwrap_or("Select a controller"))
                .show_ui(ui,|ui| {
                    if ui.selectable_label(selected.is_empty(),"None").clicked() { self.backend.command(Command::Select(None)); }
                    for d in &data.settings.devices {
                        let response=ui.selectable_label(selected==d.id, format!("{} [{}]{}",d.name,d.id,if d.standard {""} else {" · unsupported mapping"}));
                        target(ui,&format!("device:{}",d.id),&response);
                        if response.clicked() { self.backend.command(Command::Select(Some(d.id.clone()))); }
                    }
                });
            target(ui,"controller",&combo.response);
            ui.label("Choose the physical controller. Steam may also expose a virtual one.");
            ui.horizontal(|ui| {
                for (i,label) in ["Base", "Steering", "Menu"].iter().enumerate() {
                    ui.label(*label);
                    ui.add(egui::DragValue::new(&mut self.draft.hotkeys[i]).range(1..=12).prefix("F"));
                }
            });
            ui.label(if data.native {"Global shortcuts are reserved while this app runs."} else {"Shortcuts work when this page has keyboard focus; browser-reserved keys may need rebinding."});
            ui.collapsing("Import a display profile",|ui| {
                ui.label("Drop a profile JSON file onto the window, or paste its contents below.");
                ui.add(egui::TextEdit::multiline(&mut self.profile_json).desired_rows(4).desired_width(f32::INFINITY).code_editor());
                if ui.button("Load profile").clicked() { self.backend.command(Command::Profile(self.profile_json.clone())); }
                ui.small(format!("{} · {} · source {}",data.profile.controller,data.profile.variant,data.profile.source_version));
            });
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
            ui.add_enabled_ui(data.recovery_available, |ui| {
                if ui.button("Enter click-through HUD").clicked() {
                    self.backend.command(Command::Hud(true));
                }
                if data.companion_url.is_some()
                    && ui.button("Hide window · use browser only").clicked()
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
        if let Some(url) = &data.companion_url {
            ui.hyperlink_to("Open browser companion", url);
        }
        if let Some(help) = data.controller_help() {
            ui.label(help);
        }
    }
}
impl eframe::App for OverlayApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        let data = self.backend.data();
        ctx.data_mut(|d| {
            d.insert_temp(
                egui::Id::new("keybind.targets"),
                std::collections::BTreeMap::<String, [f32; 2]>::new(),
            )
        });
        let time = ctx.input(|i| i.time);
        if self.host_clock != data.state.gestures.clock_ms {
            self.host_clock = data.state.gestures.clock_ms;
            self.clock_received = time;
        }
        let now = self
            .host_clock
            .saturating_add(((time - self.clock_received).max(0.0) * 1000.0) as u64);
        if data.state.status == InputStatus::Live && data.state.gestures.animating() {
            ctx.request_repaint_after(std::time::Duration::from_millis(16));
        }
        if self.applied_scale != data.preferences.scale {
            ctx.set_zoom_factor(data.preferences.scale);
            self.applied_scale = data.preferences.scale;
        }
        if !data.native && !ctx.wants_keyboard_input() {
            let events = ctx.input(|i| i.events.clone());
            let keys = [
                egui::Key::F1,
                egui::Key::F2,
                egui::Key::F3,
                egui::Key::F4,
                egui::Key::F5,
                egui::Key::F6,
                egui::Key::F7,
                egui::Key::F8,
                egui::Key::F9,
                egui::Key::F10,
                egui::Key::F11,
                egui::Key::F12,
            ];
            for e in events {
                if let egui::Event::Key {
                    key,
                    pressed: true,
                    repeat,
                    modifiers,
                    ..
                } = e
                    && modifiers.is_none()
                    && let Some(index) = keys.iter().position(|k| *k == key)
                    && let Some(mode) =
                        page_shortcut(&data.settings.hotkeys, index as u8 + 1, repeat, false)
                {
                    self.backend.command(Command::Mode(mode));
                }
            }
        }
        if !data.remote {
            for file in ctx.input(|i| i.raw.dropped_files.clone()) {
                if let Some(bytes) = file.bytes {
                    self.backend.command(Command::Profile(
                        String::from_utf8_lossy(&bytes).into_owned(),
                    ));
                } else if let Some(path) = file.path {
                    self.backend.command(Command::ImportPath(path));
                }
            }
        }
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
                            ui.horizontal(|ui| {
                                ui.vertical(|ui| {
                                    ui.label(RichText::new("STEAM INPUT").size(10.0).color(MUTED));
                                    ui.label(RichText::new("Binding reference").size(26.0).strong());
                                });
                                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                    if !data.hud {
                                        let response = ui.button(if self.show_settings { "Close settings" } else { "Settings" });
                                        target(ui, "settings", &response);
                                        if response.clicked() {
                                            self.show_settings = !self.show_settings;
                                            self.draft = data.display_preferences();
                                        }
                                    }
                                });
                            });
                            ui.label(RichText::new(&data.profile.name).size(12.0).color(MUTED));
                            ui.add_space(12.0);
                            self.mode_buttons(ui, &data);
                            ui.add_space(8.0);
                            egui::ScrollArea::vertical().id_salt("viewer-content").show(ui, |ui| {
                            egui::Frame::new().fill(SURFACE).corner_radius(14.0)
                                .stroke(egui::Stroke::new(1.0_f32, BORDER)).inner_margin(16.0)
                                .show(ui, |ui| {
                                    ui.horizontal_wrapped(|ui| {
                                        let live = data.state.status == InputStatus::Live;
                                        ui.label(RichText::new(if live { "Live input" } else { "Reference" })
                                            .color(if live { ACCENT } else { MUTED }));
                                        ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                            if let Some(connection) = &data.browser_connection {
                                                let response = ui.add_enabled(connection.available && !connection.busy,
                                                    egui::Button::new(if connection.busy { "Please wait…" } else if connection.connected { "Disconnect controller" } else { "Connect controller" }));
                                                target(ui, if connection.connected { "disconnect" } else { "connect" }, &response);
                                                if response.clicked() {
                                                    self.backend.command(if connection.connected { Command::DisconnectController } else { Command::ConnectController });
                                                }
                                            }
                                        });
                                    });
                                    ui.add_space(8.0);
                                    // Keep diagram labels legible on small windows; only the diagram scrolls sideways.
                                    egui::ScrollArea::horizontal().id_salt("controller-diagram").show(ui, |ui| {
                                        ui.set_min_width(720.0);
                                        draw_controller(ui, &data);
                                    });
                                    ui.add_space(6.0);
                                    ui.label(RichText::new(data.input_status_label()).size(12.0).color(MUTED));
                                    if let Some(connection) = &data.browser_connection {
                                        if !connection.message.starts_with("Connect your Steam Controller") {
                                            ui.label(RichText::new(&connection.message).size(12.0).color(MUTED));
                                        }
                                    }
                                });
                            ui.add_space(4.0);
                            draw_timelines(ui, &data, now);
                            ui.add_space(8.0);
                            ui.collapsing("Reading this view", |ui| {
                                ui.label("Choose the mode to match Steam. Labels describe a fresh press in the current layer.");
                                ui.label("Stick rings show deflection; green means thumb contact. Trackpad dots show thumb position. Trigger bars show travel; Full means a full pull.");
                                ui.label("Before :: is the tap or tap-then-hold output; after :: is the hold action. For example, Escape :: Fn.");
                                ui.label("Gesture timing follows the layout’s configured delays. No game input is sent.");
                                if let Some(help) = data.controller_help() { ui.label(help); }
                            });
                            if let Some(error) = data.error.as_ref().or(data.settings.error.as_ref()) {
                                ui.colored_label(Color32::LIGHT_RED, error);
                            }
                        });
                    });
                });
            });
        if self.show_settings && !data.hud {
            egui::Window::new("Viewer settings")
                .id(egui::Id::new("settings-window"))
                .default_pos([28.0, 76.0])
                .default_width(430.0)
                .collapsible(false)
                .show(ctx, |ui| {
                    egui::ScrollArea::vertical()
                        .max_height(470.0)
                        .show(ui, |ui| self.settings(ui, &data));
                });
        }
    }
    fn clear_color(&self, _visuals: &egui::Visuals) -> [f32; 4] {
        [0.0; 4]
    }
}
fn target(ui: &egui::Ui, name: &str, response: &egui::Response) {
    ui.ctx().data_mut(|d| {
        let map = d.get_temp_mut_or_default::<std::collections::BTreeMap<String, [f32; 2]>>(
            egui::Id::new("keybind.targets"),
        );
        map.insert(
            name.into(),
            [response.rect.center().x, response.rect.center().y],
        );
    });
}
// Display wording stays separate from profile semantics and source bindings.
fn compact_binding(label: &str) -> String {
    label
        .replace(" / Function layer", " :: Fn")
        .replace(" / Cursor gyro", " :: Gyro")
        .replace("Function layer", "Fn")
        .replace("Cursor gyro", "Gyro")
        .replace("Mouse left", "Left click")
        .replace("Mouse right", "Right click")
        .replace("Mouse middle", "Middle click")
        .replace("CAPSLOCK", "Caps Lock")
        .replace("UP_ARROW", "↑")
        .replace("RIGHT_ARROW", "→")
        .replace("DOWN_ARROW", "↓")
        .replace("LEFT_ARROW", "←")
        .replace("_ARROW", "")
        .replace("Unbound", "—")
}

fn gesture_binding(tap: &str, hold: &str) -> String {
    format!("{} :: {}", compact_binding(tap), compact_binding(hold))
}

// Symmetric Ibex controls in a single, softly rounded shell. Physical control
// names live in hover help; the drawing gives its space to the actual bindings.
fn draw_controller(ui: &mut egui::Ui, data: &FrameData) {
    let available = ui.available_width();
    let width = available.min(840.0);
    let scale = width / 1000.0;
    let (row, _) =
        ui.allocate_exact_size(egui::vec2(available, 505.0 * scale), egui::Sense::hover());
    let area = egui::Rect::from_center_size(row.center(), egui::vec2(width, row.height()));
    let p = ui.painter();
    let at = |x: f32, y: f32| area.min + egui::vec2(x * scale, y * scale);
    let box_at = |x: f32, y: f32, w: f32, h: f32| {
        egui::Rect::from_center_size(at(x, y), egui::vec2(w * scale, h * scale))
    };
    let shell = Color32::from_rgb(35, 39, 46);
    let edge = Color32::from_rgb(66, 73, 84);
    let dark = Color32::from_rgb(21, 24, 29);
    let mut outline = Vec::new();
    for [a, b, c, d] in [
        [[212., 134.], [280., 106.], [387., 116.], [500., 116.]],
        [[500., 116.], [613., 116.], [720., 106.], [788., 134.]],
        [[788., 134.], [838., 158.], [850., 228.], [874., 313.]],
        [[874., 313.], [893., 380.], [916., 455.], [875., 479.]],
        [[875., 479.], [825., 510.], [778., 453.], [747., 418.]],
        [[747., 418.], [708., 445.], [632., 440.], [500., 440.]],
        [[500., 440.], [368., 440.], [292., 445.], [253., 418.]],
        [[253., 418.], [222., 453.], [175., 510.], [125., 479.]],
        [[125., 479.], [84., 455.], [107., 380.], [126., 313.]],
        [[126., 313.], [150., 228.], [162., 158.], [212., 134.]],
    ] {
        for i in 0..20 {
            let t = i as f32 / 20.0;
            let u = 1.0 - t;
            outline.push(at(
                u * u * u * a[0]
                    + 3.0 * u * u * t * b[0]
                    + 3.0 * u * t * t * c[0]
                    + t * t * t * d[0],
                u * u * u * a[1]
                    + 3.0 * u * u * t * b[1]
                    + 3.0 * u * t * t * c[1]
                    + t * t * t * d[1],
            ));
        }
    }
    // This outline is star-shaped around the bridge. A triangle fan preserves
    // its concave underside, unlike egui's convex-polygon fill.
    let mut mesh = egui::Mesh::default();
    mesh.colored_vertex(at(500.0, 235.0), shell);
    for pos in &outline {
        mesh.colored_vertex(*pos, shell);
    }
    for n in 0..outline.len() {
        mesh.add_triangle(0, (n + 1) as u32, ((n + 1) % outline.len() + 1) as u32);
    }
    p.add(egui::Shape::mesh(mesh));
    p.add(egui::Shape::closed_line(
        outline,
        egui::Stroke::new(1.2_f32, edge),
    ));

    // Quiet hardware cues, without placeholder text inside the trackpads.
    for (n, x) in [327.0, 673.0].into_iter().enumerate() {
        let pad = box_at(x, 366.0, 148.0, 124.0);
        p.rect_filled(
            pad.expand(4.0 * scale),
            25.0 * scale,
            Color32::from_rgb(29, 33, 39),
        );
        p.rect_filled(pad, 22.0 * scale, dark);
        p.rect_stroke(
            pad,
            22.0 * scale,
            egui::Stroke::new(1.0_f32, edge),
            egui::StrokeKind::Inside,
        );
        if data.state.status == InputStatus::Live
            && let Some(touch) = data.state.input.pads[n].as_ref().filter(|pad| pad.touching)
        {
            let xy = touch
                .position
                .map(|v| f32::from(v.clamp(-1000, 1000)) / 1000.0);
            let dot = pad.center() + egui::vec2(xy[0] * 55.0, xy[1] * 43.0) * scale;
            p.circle_filled(dot, 5.0 * scale, ACCENT);
            p.circle_stroke(dot, 9.0 * scale, egui::Stroke::new(1.0_f32, ACCENT));
        }
    }
    p.circle_filled(at(500.0, 222.0), 19.0 * scale, dark);
    p.circle_stroke(
        at(500.0, 222.0),
        19.0 * scale,
        egui::Stroke::new(1.0_f32, edge),
    );
    p.circle_filled(
        at(500.0, 222.0),
        3.0 * scale,
        if data.state.status == InputStatus::Live {
            ACCENT
        } else {
            edge
        },
    );
    p.rect_filled(box_at(500.0, 350.0, 42.0, 18.0), 9.0 * scale, dark);
    for x in [491.0, 500.0, 509.0] {
        p.circle_filled(at(x, 350.0), 1.5 * scale, edge);
    }

    let labels = data.state.control_labels(&data.profile);
    let positions = [
        (754.0, 289.0),
        (808.0, 235.0),
        (700.0, 235.0),
        (754.0, 181.0),
        (404.0, 151.0),
        (596.0, 151.0),
        (246.0, 189.0),
        (292.0, 235.0),
        (246.0, 281.0),
        (200.0, 235.0),
        (405.0, 252.0),
        (595.0, 252.0),
        (280.0, 81.0),
        (720.0, 81.0),
        (280.0, 32.0),
        (720.0, 32.0),
    ];
    p.rect_filled(box_at(246.0, 235.0, 50.0, 142.0), 12.0 * scale, dark);
    p.rect_filled(box_at(246.0, 235.0, 142.0, 50.0), 12.0 * scale, dark);
    for (n, control) in Control::ALL.into_iter().enumerate() {
        let (x, y) = positions[n];
        let center = at(x, y);
        let down = data.state.status == InputStatus::Live && data.state.input.down(control);
        let fill = if down {
            Color32::from_rgb(36, 70, 61)
        } else {
            dark
        };
        let stroke = egui::Stroke::new(
            if down { 1.8_f32 } else { 1.0_f32 },
            if down { ACCENT } else { edge },
        );
        let (w, h) = match control {
            Control::L1 | Control::R1 | Control::L2 | Control::R2 => (244.0, 40.0),
            Control::Select | Control::Start => (168.0, 38.0),
            Control::L3 | Control::R3 => (110.0, 110.0),
            Control::A | Control::B | Control::X | Control::Y => (60.0, 60.0),
            _ => (50.0, 50.0),
        };
        let card = box_at(x, y, w, h);
        if matches!(control, Control::L3 | Control::R3) {
            p.circle_filled(center, 57.0 * scale, Color32::from_rgb(17, 20, 25));
            p.circle_stroke(center, 57.0 * scale, egui::Stroke::new(1.0_f32, edge));
            p.circle_filled(center, 49.0 * scale, fill);
            p.circle_stroke(center, 49.0 * scale, stroke);
            if data.state.status == InputStatus::Live {
                let side = n - 10;
                if data.state.input.touches[side] == Some(true) {
                    p.circle_stroke(center, 54.0 * scale, egui::Stroke::new(2.0_f32, ACCENT));
                }
                if let Some(xy) = data.state.input.stick_positions[side] {
                    let delta = egui::vec2(f32::from(xy[0]), f32::from(xy[1])) / 1000.0;
                    if delta.length() > 0.08 {
                        // Keep motion feedback on the rim, clear of binding text.
                        let dot = center + delta.normalized() * 53.0 * scale;
                        p.circle_filled(dot, (2.0 + 3.0 * delta.length().min(1.0)) * scale, ACCENT);
                    }
                }
            }
        } else if n < 4 {
            p.circle_filled(center, 30.0 * scale, fill);
            p.circle_stroke(center, 30.0 * scale, stroke);
        } else {
            let radius = if n >= 12 { 12.0 } else { 9.0 } * scale;
            p.rect_filled(card, radius, fill);
            if down || n < 6 || n >= 12 {
                p.rect_stroke(card, radius, stroke, egui::StrokeKind::Inside);
            }
        }
        let mut label = compact_binding(&labels[n]);
        if n < 4 {
            // Conventional keycap abbreviations avoid splitting a key name
            // across lines on the small face buttons.
            label = match label.as_str() {
                "Escape" => "Esc".into(),
                "Backspace" => "Bksp".into(),
                _ => label,
            };
        }
        if matches!(labels[n].as_str(), "Timed gesture" | "Modifier")
            && let Some(recipe) = data
                .profile
                .dashboard
                .as_ref()
                .and_then(|d| d.recipe(data.state.mode, control))
        {
            label = gesture_binding(&recipe.tap_label, &recipe.hold_label);
        }
        let arrow = match label.as_str() {
            "↑" => Some(egui::vec2(0.0, -1.0)),
            "→" => Some(egui::vec2(1.0, 0.0)),
            "↓" => Some(egui::vec2(0.0, 1.0)),
            "←" => Some(egui::vec2(-1.0, 0.0)),
            _ => None,
        };
        if let Some(direction) = arrow {
            // Default egui fonts do not include these keyboard-arrow glyphs.
            p.arrow(
                center - direction * 10.0 * scale,
                direction * 20.0 * scale,
                egui::Stroke::new(1.8_f32, if down { ACCENT } else { Color32::WHITE }),
            );
        } else {
            let font_size = if label.chars().count() <= 2 {
                23.0
            } else {
                17.0
            };
            let mut job = egui::text::LayoutJob::simple(
                label,
                egui::FontId::proportional((font_size * scale).max(13.0)),
                if down {
                    ACCENT
                } else {
                    Color32::from_rgb(240, 243, 248)
                },
                (w - 12.0) * scale,
            );
            job.halign = egui::Align::Center;
            job.wrap.max_rows = if matches!(control, Control::L3 | Control::R3) || n < 4 {
                2
            } else {
                1
            };
            let galley = p.layout_job(job);
            p.galley(
                center - egui::vec2(0.0, galley.size().y / 2.0),
                galley,
                Color32::WHITE,
            );
        }
        if n >= 14 {
            let track = egui::Rect::from_min_size(
                card.left_bottom() + egui::vec2(12.0, -4.0) * scale,
                egui::vec2((w - 24.0) * scale, 2.0 * scale),
            );
            p.rect_filled(track, 1.0, BORDER);
            let travel = data.state.input.triggers[n - 14].min(1000) as f32 / 1000.0;
            if travel > 0.0 {
                p.rect_filled(
                    egui::Rect::from_min_size(
                        track.min,
                        egui::vec2(track.width() * travel, track.height()),
                    ),
                    1.0,
                    ACCENT,
                );
            }
            if let Some(t) = data
                .profile
                .dashboard
                .as_ref()
                .and_then(|d| d.trigger_thresholds[n - 14])
            {
                let x = track.left() + track.width() * t as f32 / 1000.0;
                p.line_segment(
                    [
                        egui::pos2(x, track.top() - 3.0),
                        egui::pos2(x, track.bottom()),
                    ],
                    egui::Stroke::new(1.0_f32, ACCENT),
                );
            }
        }
        let response = ui.interact(card, egui::Id::new(("control", n)), egui::Sense::hover());
        let mut help = format!("{}: {}", control.label(), labels[n]);
        if n >= 14 {
            help.push_str(&format!(
                "\nTravel: {}%",
                data.state.input.triggers[n - 14] / 10
            ));
        }
        response.on_hover_text(help);
    }
}
fn draw_timelines(ui: &mut egui::Ui, data: &FrameData, now: u64) {
    if data.state.mode == Mode::Steering {
        let direction = if data.state.gestures.steering_direction < 0 {
            "up"
        } else {
            "down"
        };
        let phase = data.state.gestures.steering_lane.phase;
        if phase != Phase::Idle {
            ui.label(format!(
                "Steering · left stick {direction} · {} · L3: {} · R3: {}",
                phase.label(),
                data.state.control_labels(&data.profile)[10],
                data.state.control_labels(&data.profile)[11]
            ));
        } else {
            ui.small("Steering: hold L1 or R1, then move the left stick up or down to see its modifier bindings.");
        }
    }

    let Some(n) = data.state.timer_owner(&data.profile) else {
        ui.label("Load a dashboard profile to see timed gestures.");
        return;
    };
    let profile = data.profile.dashboard.as_ref().unwrap();
    let control = Control::OWNERS[n];
    let mut r = profile.recipe(data.state.mode, control).unwrap().clone();
    let steering = data.state.mode == Mode::Steering
        && data.state.gestures.steering_lane.phase != Phase::Idle
        && !data.state.input.down(Control::Select)
        && !data.state.input.down(Control::Start)
        && profile.steering.is_some();
    let lane = if steering {
        let s = profile.steering.as_ref().unwrap();
        r.hold_ms = s.hold_ms;
        r.window_ms = s.window_ms;
        r.output_ms = s.output_ms;
        r.cover_ms = s.cover_ms;
        r.tap_label = if data.state.gestures.steering_direction < 0 {
            "Scroll up"
        } else {
            "Scroll down"
        }
        .into();
        r.hold_label = "Tap Cover".into();
        &data.state.gestures.steering_lane
    } else {
        &data.state.gestures.lanes[n]
    };
    let live = data.state.status == InputStatus::Live;
    let combined = matches!(lane.phase, Phase::Combined | Phase::CombinedCover);
    let owner = if steering {
        if data.state.gestures.steering_direction < 0 {
            "Left stick up"
        } else {
            "Left stick down"
        }
    } else if combined {
        "L1 + R1"
    } else {
        control.label()
    };
    let hold_ms = if combined {
        profile.combined_hold_ms
    } else {
        r.hold_ms
    };
    let tap = if combined {
        "Release combo"
    } else {
        &r.tap_label
    };
    let hold = if combined { "Tap Cover" } else { &r.hold_label };
    let outcomes = timed_gesture_outcomes(&r);
    let amber = Color32::from_rgb(244, 191, 88);
    let teal = ACCENT;
    let muted = MUTED;
    ui.add_space(8.0);
    egui::Frame::new().fill(SURFACE).stroke(egui::Stroke::new(1.0_f32, BORDER)).corner_radius(14.0)
        .inner_margin(16.0).show(ui, |ui| {
        ui.set_width(ui.available_width());
        ui.horizontal_wrapped(|ui| {
            ui.label(RichText::new(gesture_binding(tap, hold)).size(19.0).color(Color32::WHITE))
                .on_hover_text(owner);
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                ui.label(RichText::new(lane.phase.label()).size(12.0).color(if live { teal } else { muted }));
            });
        });
        ui.add_space(4.0);
        let (stage, duration, start, end, hint) = match lane.phase {
            Phase::Window => (1, r.window_ms, "Released".to_string(), format!("Window closes {} ms", r.window_ms),
                format!("{} at {} ms after release. Press again before this window closes.", r.tap_label, r.output_ms)),
            Phase::Second | Phase::Cover => (2, r.cover_ms, "Second hold".into(), format!("Cover at {} ms", r.cover_ms),
                if lane.phase == Phase::Cover { "Tap, then hold is active. Release ends the gesture.".into() }
                else { "Keep the second press held until its cover applies; releasing early reopens the release window.".into() }),
            _ => (0, hold_ms, "Initial hold".into(), format!("Hold at {hold_ms} ms"),
                match lane.phase {
                    Phase::Hold => format!("{hold} active. Release ends the gesture."),
                    Phase::Consumed | Phase::CombinedCover => "Tap Cover applied. The modifier was used; release will not trigger a tap.".into(),
                    Phase::Unknown => "Release this button once to start tracking its timing.".into(),
                    Phase::Interrupted => "Timing paused; inherited bindings remain visible.".into(),
                    _ => format!("Release before {hold_ms} ms for {tap}. Keep holding for {hold}."),
                }),
        };
        let (bar, _) = ui.allocate_exact_size(egui::vec2(ui.available_width(), 6.0), egui::Sense::hover());
        let painter = ui.painter();
        painter.rect_filled(bar, 6.0, Color32::from_rgb(49, 61, 77));
        let complete = matches!(lane.phase, Phase::Hold | Phase::Cover | Phase::Consumed | Phase::CombinedCover);
        let elapsed = now.saturating_sub(lane.started_ms).min(duration);
        let progress = if !live { 0.0 } else if complete { 1.0 }
            else if lane.deadline_ms.is_some() { elapsed as f32 / duration as f32 } else { 0.0 };
        if progress > 0.0 {
            painter.rect_filled(egui::Rect::from_min_size(bar.min,egui::vec2(bar.width()*progress,bar.height())),6.0,if stage==1 {amber} else {teal});
        }
        if stage == 1 {
            let x=bar.left()+bar.width()*r.output_ms as f32/r.window_ms as f32;
            painter.line_segment([egui::pos2(x,bar.top()-3.0),egui::pos2(x,bar.bottom()+3.0)],egui::Stroke::new(2.0_f32,Color32::WHITE));
        }
        ui.horizontal(|ui| {
            ui.small(start);
            if live && let Some(deadline)=lane.deadline_ms {
                ui.label(RichText::new(format!("{} ms left",deadline.saturating_sub(now))).color(if stage==1 {amber} else {teal}).strong());
            }
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center),|ui| { ui.small(end); });
        });
        ui.collapsing("Gesture details", |ui| {
            ui.label("Tap / tap, then hold :: Hold");
            if combined {
                ui.label(format!("Release: {tap}. Hold: {hold}."));
            } else {
                for outcome in &outcomes { ui.label(outcome); }
            }
            ui.label(hint);
            if !live { ui.small("Connect a controller to animate this timeline."); }
            else if lane.phase == Phase::Idle {
                ui.small("Press a bumper, Select or Start. The bar follows its timed gesture.");
            }
        });
    });
    if let Some(message) = &data.state.gestures.uncertainty {
        ui.colored_label(Color32::YELLOW, message);
    }
}

fn timed_gesture_outcomes(recipe: &Recipe) -> [String; 3] {
    [
        format!("HOLD  {}", recipe.hold_label),
        format!("TAP  {}", recipe.tap_label),
        format!("TAP, THEN HOLD  {} while held", recipe.tap_label),
    ]
}

#[cfg(test)]
mod timed_gesture_wording_tests {
    use super::*;

    #[test]
    fn outcomes_keep_single_tap_distinct_from_second_hold() {
        let profile = Profile::parse(crate::BUNDLED_PROFILE).unwrap();
        let dashboard = profile.dashboard.unwrap();
        let bumper = dashboard.recipe(Mode::Base, Control::L1).unwrap();
        assert_eq!(
            timed_gesture_outcomes(bumper),
            [
                "HOLD  Cursor gyro",
                "TAP  Scroll down",
                "TAP, THEN HOLD  Scroll down while held"
            ]
        );
        let menu = dashboard.recipe(Mode::Base, Control::Select).unwrap();
        assert_eq!(
            timed_gesture_outcomes(menu),
            [
                "HOLD  Function layer",
                "TAP  Escape",
                "TAP, THEN HOLD  Escape while held"
            ]
        );
    }
}
