use super::*;

pub struct OverlayApp {
    pub(super) backend: Box<dyn Backend>,
    pub(super) show_settings: bool,
    pub(super) profile_json: String,
    pub(super) draft: Preferences,
    applied_scale: f32,
    host_clock: u64,
    clock_received: f64,
    mouse: mouse::MousePreview,
}
impl OverlayApp {
    pub fn new(cc: &eframe::CreationContext<'_>, backend: Box<dyn Backend>) -> Self {
        theme::apply(&cc.egui_ctx);
        let draft = backend.data().display_preferences();
        Self {
            backend,
            show_settings: false,
            profile_json: String::new(),
            draft,
            applied_scale: 0.0,
            host_clock: 0,
            clock_received: 0.0,
            mouse: mouse::MousePreview::default(),
        }
    }
    fn frame_clock(&mut self, ctx: &egui::Context, data: &FrameData) -> u64 {
        let time = ctx.input(|i| i.time);
        if self.host_clock != data.state.gestures.clock_ms {
            self.host_clock = data.state.gestures.clock_ms;
            self.clock_received = time;
        }
        let now = self.host_clock.saturating_add(
            ((time - self.clock_received).max(0.0) * 1000.0 / f64::from(data.state.timing_scale()))
                as u64,
        );
        if data.state.status == InputStatus::Live && data.state.gestures.animating() {
            ctx.request_repaint_after(std::time::Duration::from_millis(16));
        }
        if self.applied_scale != data.preferences.scale {
            ctx.set_zoom_factor(data.preferences.scale);
            self.applied_scale = data.preferences.scale;
        }
        now
    }
    fn page_shortcuts(&mut self, ctx: &egui::Context, data: &FrameData) {
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
    }
    fn dropped_profiles(&mut self, ctx: &egui::Context, data: &FrameData) {
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
    }
}
impl eframe::App for OverlayApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        let source = self.backend.data();
        let data = self.mouse.frame(ctx, &source);
        ctx.data_mut(|d| {
            d.insert_temp(
                egui::Id::new("keybind.targets"),
                std::collections::BTreeMap::<String, [f32; 2]>::new(),
            )
        });
        let now = self.frame_clock(ctx, &data);
        self.page_shortcuts(ctx, &data);
        self.dropped_profiles(ctx, &data);
        self.viewer(ctx, &data, now);
        self.settings_window(ctx, &source);
    }
    fn clear_color(&self, _visuals: &egui::Visuals) -> [f32; 4] {
        [0.0; 4]
    }
}
