//! One interface used by both native eframe and WebRunner.
use crate::core::*;
use eframe::egui::{self, Color32, RichText};

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
        cc.egui_ctx.set_visuals(egui::Visuals::dark());
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
        ui.horizontal(|ui| {
            for (i, mode) in Mode::ALL.into_iter().enumerate() {
                let label = format!("{}  F{}", mode.label(), data.settings.hotkeys[i]);
                let response = ui.selectable_label(data.state.mode == mode, label);
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
            18,
            23,
            32,
            if data.native {
                (data.preferences.opacity * 255.0) as u8
            } else {
                255
            },
        );
        egui::CentralPanel::default().frame(egui::Frame::new().fill(fill).inner_margin(16.0)).show(ctx,|ui| {
            ui.horizontal(|ui| {
                ui.heading("Binding reference");
                if !data.hud { let response=ui.button(if self.show_settings {"Close settings"} else {"Settings"}); target(ui,"settings",&response); if response.clicked() { self.show_settings = !self.show_settings; self.draft=data.display_preferences(); } }
            });
            ui.small(&data.profile.name);
            if let Some(connection) = &data.browser_connection {
                ui.horizontal_wrapped(|ui| {
                    let response = ui.add_enabled(connection.available && !connection.busy,
                        egui::Button::new(if connection.busy { "Please wait…" } else if connection.connected { "Disconnect controller" } else { "Connect controller" }));
                    target(ui, if connection.connected { "disconnect" } else { "connect" }, &response);
                    if response.clicked() {
                        self.backend.command(if connection.connected { Command::DisconnectController } else { Command::ConnectController });
                    }
                    ui.small(&connection.message);
                });
            }
            self.mode_buttons(ui,&data);
            ui.add_space(8.0);
            egui::ScrollArea::vertical().show(ui,|ui| {
                ui.horizontal(|ui| {
                    for i in 0..2 {
                        let color=if data.state.held[i] {Color32::from_rgb(72,221,173)} else {Color32::GRAY};
                        ui.label(RichText::new(format!("{} {}",data.profile.modifiers[i],if data.state.held[i] {"held"} else {"released"})).color(color).strong());
                    }
                });
                draw_controller(ui,&data);
                draw_timelines(ui,&data,now);
                ui.label(RichText::new(data.input_status_label()).color(if data.state.status==InputStatus::Live {Color32::from_rgb(72,221,173)} else {Color32::YELLOW}));
                ui.small("Mode is selected manually. Timelines show configured expectations; no game input is sent.");
                if let Some(error)=data.error.as_ref().or(data.settings.error.as_ref()) { ui.colored_label(Color32::LIGHT_RED,error); }

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
// Front-view Ibex geometry. The pads and system buttons are orientation cues;
// binding indicators remain the sixteen controls supported by the input model.
fn draw_controller(ui: &mut egui::Ui, data: &FrameData) {
    let available = ui.available_width();
    let width = available.min(900.0);
    let scale = width / 1000.0;
    let (row, _) =
        ui.allocate_exact_size(egui::vec2(available, 510.0 * scale), egui::Sense::hover());
    let area = egui::Rect::from_center_size(row.center(), egui::vec2(width, row.height()));
    let p = ui.painter();
    let at = |x: f32, y: f32| area.min + egui::vec2(x * scale, y * scale);
    let box_at = |x: f32, y: f32, w: f32, h: f32| {
        egui::Rect::from_center_size(at(x, y), egui::vec2(w * scale, h * scale))
    };
    let shell = Color32::from_rgb(43, 48, 55);
    let edge = Color32::from_rgb(78, 85, 94);
    let dark = Color32::from_rgb(17, 21, 27);
    let teal = Color32::from_rgb(72, 221, 173);
    // Sample cubic curves so the body keeps the controller's curved silhouette.
    let curve = |points: [[f32; 2]; 4]| -> Vec<egui::Pos2> {
        (0..=16)
            .map(|i| {
                let t = i as f32 / 16.0;
                let u = 1.0 - t;
                let x = u * u * u * points[0][0]
                    + 3.0 * u * u * t * points[1][0]
                    + 3.0 * u * t * t * points[2][0]
                    + t * t * t * points[3][0];
                let y = u * u * u * points[0][1]
                    + 3.0 * u * u * t * points[1][1]
                    + 3.0 * u * t * t * points[2][1]
                    + t * t * t * points[3][1];
                at(x, y)
            })
            .collect()
    };
    // Rounded descending grips sit behind the broad upper shell.
    for mirror in [false, true] {
        let transform = |v: egui::Pos2| {
            if mirror {
                egui::pos2(at(1000.0, 0.0).x - (v.x - area.left()), v.y)
            } else {
                v
            }
        };
        let mut grip = curve([
            [225.0, 110.0],
            [182.0, 145.0],
            [160.0, 310.0],
            [158.0, 407.0],
        ]);
        grip.extend(curve([
            [158.0, 407.0],
            [155.0, 477.0],
            [185.0, 493.0],
            [224.0, 490.0],
        ]));
        grip.extend(curve([
            [224.0, 490.0],
            [259.0, 487.0],
            [256.0, 423.0],
            [288.0, 402.0],
        ]));
        grip.extend(curve([
            [288.0, 402.0],
            [321.0, 320.0],
            [306.0, 173.0],
            [225.0, 110.0],
        ]));
        p.add(egui::Shape::convex_polygon(
            grip.into_iter().map(transform).collect(),
            shell,
            egui::Stroke::new(1.5_f32, edge),
        ));
    }
    let mut top = curve([[225.0, 110.0], [245.0, 90.0], [755.0, 90.0], [775.0, 110.0]]);
    top.extend(curve([
        [775.0, 110.0],
        [808.0, 135.0],
        [824.0, 265.0],
        [818.0, 355.0],
    ]));
    top.extend(curve([
        [818.0, 355.0],
        [805.0, 402.0],
        [742.0, 412.0],
        [700.0, 410.0],
    ]));
    top.push(at(300.0, 410.0));
    top.extend(curve([
        [300.0, 410.0],
        [258.0, 412.0],
        [195.0, 402.0],
        [182.0, 355.0],
    ]));
    top.extend(curve([
        [182.0, 355.0],
        [176.0, 265.0],
        [192.0, 135.0],
        [225.0, 110.0],
    ]));
    p.add(egui::Shape::convex_polygon(
        top,
        shell,
        egui::Stroke::new(1.5_f32, edge),
    ));
    // Recessed lower panel and the two canted square trackpads.
    p.rect_filled(
        box_at(500.0, 350.0, 460.0, 126.0),
        35.0 * scale,
        Color32::from_rgb(33, 38, 44),
    );
    for (n, (x, angle)) in [(360.0, 0.12_f32), (640.0, -0.12_f32)]
        .into_iter()
        .enumerate()
    {
        let center = at(x, 350.0);
        let rotate = |q: egui::Pos2| {
            let d = q - center;
            center
                + egui::vec2(
                    d.x * angle.cos() - d.y * angle.sin(),
                    d.x * angle.sin() + d.y * angle.cos(),
                )
        };
        let mut outline = Vec::new();
        for (cx, cy, start) in [
            (-48.0, -48.0, 180.0_f32),
            (48.0, -48.0, 270.0),
            (48.0, 48.0, 0.0),
            (-48.0, 48.0, 90.0),
        ] {
            for i in 0..=8 {
                let a = (start + i as f32 * 90.0 / 8.0).to_radians();
                outline.push(rotate(
                    center
                        + egui::vec2((cx + 18.0 * a.cos()) * scale, (cy + 18.0 * a.sin()) * scale),
                ));
            }
        }
        p.add(egui::Shape::convex_polygon(
            outline,
            dark,
            egui::Stroke::new(2.0_f32, edge),
        ));
        p.text(
            center,
            egui::Align2::CENTER_CENTER,
            match data.state.input.pads[n].as_ref() {
                Some(pad) if pad.touching => "TOUCH",
                Some(_) => "TRACKPAD",
                None => "NO TOUCH DATA",
            },
            egui::FontId::proportional(9.0 * scale),
            Color32::from_rgb(85, 95, 107),
        );
        if data.state.status == InputStatus::Live
            && let Some(pad) = data.state.input.pads[n].as_ref().filter(|pad| pad.touching)
        {
            let xy = pad
                .position
                .map(|v| f32::from(v.clamp(-1000, 1000)) / 1000.0);
            let dot = rotate(center + egui::vec2(xy[0] * 52.0 * scale, xy[1] * 52.0 * scale));
            p.circle_filled(dot, 6.0 * scale, teal);
            p.circle_stroke(dot, 9.0 * scale, egui::Stroke::new(1.0_f32, teal));
        }
    }
    p.circle_filled(at(500.0, 190.0), 22.0 * scale, dark);
    p.circle_stroke(
        at(500.0, 190.0),
        22.0 * scale,
        egui::Stroke::new(1.5_f32, edge),
    );
    p.text(
        at(500.0, 190.0),
        egui::Align2::CENTER_CENTER,
        "STEAM",
        egui::FontId::proportional(9.0 * scale),
        Color32::GRAY,
    );
    p.circle_filled(
        at(500.0, 143.0),
        2.0 * scale,
        if data.state.status == InputStatus::Live {
            teal
        } else {
            edge
        },
    );
    p.rect_filled(box_at(500.0, 350.0, 48.0, 25.0), 12.0 * scale, dark);
    for x in [490.0, 500.0, 510.0] {
        p.circle_filled(at(x, 350.0), 2.0 * scale, edge);
    }
    // The D-pad is one connected cross, with four individually lit directions.
    p.rect_filled(box_at(275.0, 200.0, 42.0, 126.0), 8.0 * scale, dark);
    p.rect_filled(box_at(275.0, 200.0, 126.0, 42.0), 8.0 * scale, dark);
    let labels = data.state.control_labels(&data.profile);
    let positions = [
        (725.0, 242.0),
        (767.0, 200.0),
        (683.0, 200.0),
        (725.0, 158.0),
        (375.0, 128.0),
        (625.0, 128.0),
        (275.0, 158.0),
        (317.0, 200.0),
        (275.0, 242.0),
        (233.0, 200.0),
        (402.0, 243.0),
        (598.0, 243.0),
        (300.0, 76.0),
        (700.0, 76.0),
        (300.0, 30.0),
        (700.0, 30.0),
    ];
    for (n, c) in Control::ALL.into_iter().enumerate() {
        let (x, y) = positions[n];
        let center = at(x, y);
        let down = data.state.status == InputStatus::Live && data.state.input.down(c);
        let fill = if down {
            Color32::from_rgb(27, 82, 70)
        } else {
            dark
        };
        let stroke = egui::Stroke::new(
            if down { 2.0_f32 } else { 1.0_f32 },
            if down { teal } else { edge },
        );
        let (w, h) = match c {
            Control::L1 | Control::R1 | Control::L2 | Control::R2 => (160.0, 38.0),
            Control::Select | Control::Start => (104.0, 36.0),
            Control::L3 | Control::R3 => (86.0, 86.0),
            _ => (42.0, 42.0),
        };
        let card = box_at(x, y, w, h);
        if matches!(c, Control::L3 | Control::R3) {
            p.circle_filled(
                center + egui::vec2(0.0, 5.0 * scale),
                48.0 * scale,
                Color32::from_rgb(21, 25, 30),
            );
            p.circle_filled(center, 43.0 * scale, fill);
            p.circle_stroke(center, 43.0 * scale, stroke);
            p.circle_stroke(
                center,
                36.0 * scale,
                egui::Stroke::new(2.0_f32, Color32::from_rgb(65, 72, 81)),
            );
        } else if n < 4 {
            p.circle_filled(center, 23.0 * scale, fill);
            p.circle_stroke(center, 23.0 * scale, stroke);
        } else {
            p.rect_filled(card, if n >= 12 { 10.0 * scale } else { 7.0 * scale }, fill);
            if down || matches!(c, Control::Select | Control::Start) {
                p.rect_stroke(card, 7.0 * scale, stroke, egui::StrokeKind::Inside);
            }
        }
        let caption = if n >= 14 {
            format!(
                "{}   {}%",
                c.label(),
                data.state.input.triggers[n - 14] / 10
            )
        } else {
            c.label().into()
        };
        p.text(
            center - egui::vec2(0.0, 10.0 * scale),
            egui::Align2::CENTER_CENTER,
            caption,
            egui::FontId::proportional(10.0 * scale),
            if down {
                teal
            } else {
                Color32::from_rgb(156, 170, 184)
            },
        );
        let label = labels[n]
            .replace("Function layer", "Fn")
            .replace("Cursor gyro", "Gyro")
            .replace("_ARROW", "");
        let mut job = egui::text::LayoutJob::simple(
            label.clone(),
            egui::FontId::proportional(if label.len() > 7 {
                10.0 * scale
            } else {
                14.0 * scale
            }),
            Color32::WHITE,
            (w - 7.0) * scale,
        );
        job.wrap.max_rows = 1;
        let galley = p.layout_job(job);
        p.galley(
            egui::pos2(center.x - galley.size().x / 2.0, center.y),
            galley,
            Color32::WHITE,
        );
        if n >= 14 {
            let bar = egui::Rect::from_min_size(
                card.left_bottom() - egui::vec2(0.0, 3.0 * scale),
                egui::vec2(
                    w * scale * data.state.input.triggers[n - 14].min(1000) as f32 / 1000.0,
                    3.0 * scale,
                ),
            );
            p.rect_filled(bar, 2.0 * scale, teal);
            if let Some(t) = data
                .profile
                .dashboard
                .as_ref()
                .and_then(|d| d.trigger_thresholds[n - 14])
            {
                let x = card.left() + card.width() * t as f32 / 1000.0;
                p.line_segment(
                    [
                        egui::pos2(x, card.bottom() - 7.0 * scale),
                        egui::pos2(x, card.bottom()),
                    ],
                    egui::Stroke::new(1.0_f32, Color32::WHITE),
                );
            }
        }
        if matches!(c, Control::L3 | Control::R3) && data.state.status == InputStatus::Live {
            let side = n - 10;
            if let Some(xy) = data.state.input.stick_positions[side] {
                let delta = egui::vec2(f32::from(xy[0]), f32::from(xy[1])) / 1000.0;
                let dot = center + delta * 32.0 * scale;
                let color = if data.state.input.touches[side] == Some(true) {
                    teal
                } else {
                    Color32::from_rgb(244, 191, 88)
                };
                p.line_segment([center, dot], egui::Stroke::new(1.5_f32, color));
                p.circle_stroke(dot, 5.0 * scale, egui::Stroke::new(2.0_f32, color));
                if data.state.input.touches[side] == Some(true) {
                    p.circle_filled(dot, 2.5 * scale, color);
                }
            }
        }
        ui.interact(card, egui::Id::new(("control", n)), egui::Sense::hover())
            .on_hover_text(format!("{}: {}", c.label(), labels[n]));
    }
}
fn draw_timelines(ui: &mut egui::Ui, data: &FrameData, now: u64) {
    ui.small("Stick ring: deflection · green: thumb touching · trackpad dot: thumb position");
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
    let teal = Color32::from_rgb(72, 221, 173);
    let muted = Color32::from_rgb(160, 180, 197);
    ui.add_space(8.0);
    egui::Frame::new().fill(Color32::from_rgb(23,31,43)).corner_radius(10.0)
        .inner_margin(14.0).show(ui, |ui| {
        ui.set_min_width((ui.available_width()).min(992.0));
        ui.horizontal(|ui| {
            ui.strong(format!("{owner}  ·  {}", if combined { "Combined modifiers" } else { "Hold / Tap, then hold" }));
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                ui.small(if combined { "Two modifiers" } else { "Timed gestures" });
            });
        });
        ui.add_space(4.0);
        if combined {
            ui.columns(2, |cols| {
                cols[0].label(RichText::new(format!("RELEASE   {tap}")).color(amber).size(15.0));
                cols[1].label(RichText::new(format!("HOLD   {hold}")).color(teal).size(15.0));
            });
        } else {
            ui.columns(3, |cols| {
                cols[0].label(RichText::new(&outcomes[0]).color(teal).size(14.0));
                cols[1].label(RichText::new(&outcomes[1]).color(amber).size(14.0));
                cols[2].label(RichText::new(&outcomes[2]).color(amber).size(14.0));
            });
        }
        ui.add_space(7.0);
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
        ui.horizontal(|ui| {
            for (i, title) in ["1  Initial hold", "2  Release window", "3  Second hold"].iter().enumerate() {
                ui.label(RichText::new(*title).color(if i == stage { Color32::WHITE } else { muted }));
                if i < 2 { ui.label(" / "); }
            }
        });
        let (bar, _) = ui.allocate_exact_size(egui::vec2(ui.available_width(), 18.0), egui::Sense::hover());
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
        ui.label(hint);
        if !live { ui.small("Connect a controller to animate this timeline."); }
        else if lane.phase == Phase::Idle {
            ui.small("Press a bumper, Select or Start. The bar follows its timed gesture.");
        }
    });
    if let Some(message) = &data.state.gestures.uncertainty {
        ui.colored_label(Color32::YELLOW, message);
    }
    ui.small("Timing shows configured expectations, not observed game output.");
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
