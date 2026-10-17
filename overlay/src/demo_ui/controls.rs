use super::{
    ACCENT, BORDER, DemoApp, MUTED, SURFACE,
    mouse::{Hit, Target},
    target,
};
use eframe::egui::{self, Align2, FontId, Rect, Sense, Stroke, StrokeKind, vec2};

const BUTTONS: [(&str, &str, f32, f32); 23] = [
    ("L1", "switch/left_bumper", 0.12, 0.10),
    ("R1", "switch/right_bumper", 0.88, 0.10),
    ("Select", "switch/button_menu", 0.39, 0.27),
    ("Start", "switch/button_escape", 0.61, 0.27),
    ("Up", "dpad/dpad_north", 0.16, 0.34),
    ("Left", "dpad/dpad_west", 0.08, 0.50),
    ("Down", "dpad/dpad_south", 0.16, 0.66),
    ("Right", "dpad/dpad_east", 0.24, 0.50),
    ("Y", "button_diamond/button_y", 0.84, 0.34),
    ("X", "button_diamond/button_x", 0.76, 0.50),
    ("A", "button_diamond/button_a", 0.84, 0.66),
    ("B", "button_diamond/button_b", 0.92, 0.50),
    ("L3", "joystick/click", 0.38, 0.53),
    ("R3", "right_joystick/click", 0.62, 0.53),
    ("L4", "switch/button_back_left_upper", 0.10, 0.90),
    ("L5", "switch/button_back_left", 0.27, 0.90),
    ("R5", "switch/button_back_right", 0.73, 0.90),
    ("R4", "switch/button_back_right_upper", 0.90, 0.90),
    ("LS touch", "joystick/touch", 0.38, 0.72),
    ("RS touch", "right_joystick/touch", 0.62, 0.72),
    ("Mute", "switch/button_capture", 0.50, 0.90),
    ("L2", "left_trigger/edge", 0.28, 0.10),
    ("R2", "right_trigger/edge", 0.72, 0.10),
];
impl DemoApp {
    pub(super) fn controller(&mut self, ui: &mut egui::Ui) {
        ui.heading("Try the layout");
        ui.label(
            egui::RichText::new("Press and hold · right-click to latch a button for chords")
                .small()
                .color(MUTED),
        );
        let width = ui.available_width().min(720.);
        let (rect, _) = ui.allocate_exact_size(vec2(width, 270.), Sense::hover());
        ui.painter().rect(
            rect.shrink(3.),
            36.,
            SURFACE,
            Stroke::new(1.0_f32, BORDER),
            StrokeKind::Inside,
        );
        let dse = self.session.engine.layout.controller == "dse";
        for (label, control, x, y) in BUTTONS {
            if (dse && control.ends_with("/touch")) || (!dse && label == "Mute") {
                continue;
            }
            let size = if label.len() > 2 {
                vec2(66., 30.)
            } else {
                vec2(40., 34.)
            };
            let center = rect.min + vec2(width * x, 250. * y + 8.);
            self.control(ui, Rect::from_center_size(center, size), label, control);
        }
        ui.add_enabled_ui(self.virtual_input_enabled(), |ui| self.trigger_controls(ui));
        self.analog_controls(ui, width, dse);
    }
    fn analog_controls(&mut self, ui: &mut egui::Ui, width: f32, dse: bool) {
        ui.horizontal(|ui| {
            ui.label("Trackpads");
            for (value, label) in [(false, "Touch"), (true, "Click")] {
                let response = ui.selectable_label(self.pad_click == value, label);
                target(
                    ui,
                    if value { "pad-click" } else { "pad-touch" },
                    response.rect,
                );
                if response.clicked() {
                    self.pad_click = value;
                }
            }
        });
        if dse {
            self.surface_widget(ui, "center_trackpad", "Whole touchpad", 180.);
        } else {
            ui.horizontal(|ui| {
                let size = ((width - 30.) / 2.).min(190.);
                ui.vertical(|ui| {
                    self.surface_widget(ui, "left_trackpad", "Left trackpad", size);
                });
                ui.vertical(|ui| {
                    self.surface_widget(ui, "right_trackpad", "Right trackpad", size);
                });
            });
        }
        ui.horizontal(|ui| {
            ui.vertical(|ui| {
                self.surface_widget(ui, "joystick", "Left stick", 130.);
            });
            ui.vertical(|ui| {
                self.surface_widget(ui, "right_joystick", "Right stick", 130.);
            });
        });
    }
    fn control(&mut self, ui: &mut egui::Ui, rect: Rect, label: &str, control: &str) {
        let down = self.session.engine.held.contains(control);
        let color = if down { ACCENT } else { BORDER };
        ui.painter().rect(
            rect,
            10.,
            color.gamma_multiply(0.25),
            Stroke::new(1.0_f32, color),
            StrokeKind::Inside,
        );
        ui.painter().text(
            rect.center() - vec2(0., 5.),
            Align2::CENTER_CENTER,
            label,
            FontId::proportional(13.),
            if down { ACCENT } else { egui::Color32::WHITE },
        );
        let binding = self
            .session
            .engine
            .label(control)
            .replace("mouse_button LEFT", "Left click")
            .replace("mouse_button RIGHT", "Right click")
            .replace("mouse_button MIDDLE", "Mid click")
            .replace("LEFT_SHIFT", "Shift")
            .replace("LEFT_CONTROL", "Ctrl")
            .replace("LEFT_ALT", "Alt")
            .replace("LEFT_WINDOWS", "Win")
            .replace("xinput_button ", "Pad ");
        ui.painter().text(
            rect.center() + vec2(0., 9.),
            Align2::CENTER_CENTER,
            binding.chars().take(11).collect::<String>(),
            FontId::proportional(9.),
            MUTED,
        );
        ui.interact(rect, ui.id().with(control), Sense::hover())
            .on_hover_text(format!("{}\n{}", label, self.session.engine.label(control)));
        target(ui, control, rect);
        self.hits.push(Hit {
            target: Target::Button(control.into()),
            rect,
            clip: ui.clip_rect(),
            layer: ui.layer_id(),
        });
    }
    fn trigger_controls(&mut self, ui: &mut egui::Ui) {
        for (side, source) in ["left_trigger", "right_trigger"].iter().enumerate() {
            let response = ui.add(
                egui::Slider::new(&mut self.triggers[side], 0.0..=1.0).text(if side == 0 {
                    "L2 travel"
                } else {
                    "R2 travel"
                }),
            );
            target(ui, source, response.rect);
            if response.changed() {
                self.session.input(crate::demo::Input::Trigger {
                    source: (*source).into(),
                    value: self.triggers[side],
                });
            }
        }
    }
    fn surface_widget(&mut self, ui: &mut egui::Ui, source: &str, label: &str, size: f32) {
        ui.label(label);
        let (rect, _) = ui.allocate_exact_size(vec2(size, size), Sense::hover());
        let center = rect.center();
        let radius = size * 0.5 - 4.;
        let surface = self.session.engine.surfaces.get(source);
        let touching = surface.is_some_and(|s| s.touching);
        let color = if touching { ACCENT } else { BORDER };
        ui.painter()
            .circle(center, radius, SURFACE, Stroke::new(2.0_f32, color));
        ui.painter()
            .circle_stroke(center, radius * 0.72, Stroke::new(1.0_f32, BORDER));
        ui.painter().line_segment(
            [center - vec2(radius, 0.), center + vec2(radius, 0.)],
            Stroke::new(1.0_f32, BORDER),
        );
        ui.painter().line_segment(
            [center - vec2(0., radius), center + vec2(0., radius)],
            Stroke::new(1.0_f32, BORDER),
        );
        if let Some(surface) = surface
            && touching
        {
            let position =
                center + vec2(surface.position[0] as f32, surface.position[1] as f32) * radius;
            ui.painter().circle_filled(position, 7., ACCENT);
        }
        target(ui, source, rect);
        self.hits.push(Hit {
            target: Target::Surface(source.into()),
            rect,
            clip: ui.clip_rect(),
            layer: ui.layer_id(),
        });
        let mode = self.session.engine.effective(source).0;
        ui.label(
            egui::RichText::new(mode.replace('_', " "))
                .small()
                .color(MUTED),
        );
    }
}
