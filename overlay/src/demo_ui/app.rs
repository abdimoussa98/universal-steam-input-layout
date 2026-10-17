use super::{
    ACCENT, SURFACE,
    mouse::{Capture, Hit},
};
use crate::{
    demo::{Catalog, Layout, Session},
    ui::Backend,
};
use eframe::egui;
use std::collections::BTreeSet;

pub struct DemoApp {
    pub(super) backend: Box<dyn Backend>,
    pub(super) catalog: Catalog,
    pub(super) selection: usize,
    pub(super) session: Session,
    pub(super) source: Option<String>,
    pub(super) physical: Option<crate::core::InputFrame>,
    pub(super) hits: Vec<Hit>,
    pub(super) capture: Option<Capture>,
    pub(super) pinned: BTreeSet<String>,
    pub(super) pad_click: bool,
    pub(super) fine_motion: bool,
    pub(super) sound: bool,
    pub(super) feedback_seen: u64,
    pub(super) roll: f32,
    pub(super) inspector: bool,
    pub(super) triggers: [f64; 2],
    was_focused: bool,
    epoch: u64,
    pub(super) gyro_bias: [i32; 3],
}
impl DemoApp {
    pub fn new(cc: &eframe::CreationContext<'_>, backend: Box<dyn Backend>) -> Self {
        let catalog = Layout::catalog().expect("validated executable catalog");
        let source = backend.data().remote.then(|| "companion".into());
        cc.egui_ctx.set_visuals(egui::Visuals::dark());
        cc.egui_ctx.style_mut(|style| {
            style.visuals.panel_fill = egui::Color32::from_rgb(17, 21, 27);
            style.visuals.widgets.inactive.bg_fill = SURFACE;
            style.visuals.selection.bg_fill = ACCENT.gamma_multiply(0.25);
            style.spacing.item_spacing = egui::vec2(10., 8.);
        });
        Self {
            session: Session::new(catalog[0].clone()),
            catalog,
            backend,
            selection: 0,
            source,
            physical: None,
            hits: vec![],
            capture: None,
            pinned: BTreeSet::new(),
            pad_click: false,
            fine_motion: false,
            sound: false,
            feedback_seen: 0,
            roll: 0.,
            inspector: false,
            triggers: [0.; 2],
            was_focused: true,
            epoch: 0,
            gyro_bias: [0; 3],
        }
    }
    pub(super) fn reset(&mut self) {
        self.cancel_sound();
        self.session.reset();
        self.capture = None;
        self.pinned.clear();
        self.triggers = [0.; 2];
        self.physical = None;
        self.roll = 0.;
        self.feedback_seen = 0;
    }
    pub(super) fn virtual_input_enabled(&self) -> bool {
        self.source.is_none() && !self.session.paused && !self.session.replaying
    }
    pub(super) fn select_layout(&mut self, index: usize) {
        self.selection = index;
        self.session = Session::new(self.catalog[index].clone());
        self.reset();
    }
    fn body(&mut self, ctx: &egui::Context) {
        egui::CentralPanel::default().show(ctx, |ui| {
            egui::ScrollArea::vertical().show(ui, |ui| {
                if ui.available_width() >= 900. {
                    ui.columns(2, |columns| {
                        self.controller(&mut columns[0]);
                        self.gyro_panel(&mut columns[1]);
                        self.playground(&mut columns[1]);
                    });
                } else {
                    self.controller(ui);
                    self.gyro_panel(ui);
                    self.playground(ui);
                }
                self.details(ui);
            });
        });
    }
    fn diagnostics(&self, ctx: &egui::Context) {
        let targets = ctx.data(|d| {
            d.get_temp::<std::collections::BTreeMap<String, [f32; 4]>>(egui::Id::new(
                "demo.targets",
            ))
        });
        let snapshot = serde_json::json!({"demo":self.session.engine.snapshot(), "targets":targets,
            "scale":self.session.scale,"paused":self.session.paused,"replaying":self.session.replaying,
            "source":self.source,"sound":self.sound,"recorded":self.session.recording.len()});
        ctx.data_mut(|d| d.insert_temp(egui::Id::new("keybind.demo"), snapshot));
    }
}
impl eframe::App for DemoApp {
    fn update(&mut self, ctx: &egui::Context, _: &mut eframe::Frame) {
        let focused = ctx.input(|i| i.focused) && !self.backend.input_blocked();
        let epoch = self.backend.input_epoch();
        if (self.was_focused && !focused) || self.epoch != epoch {
            self.reset();
        }
        self.epoch = epoch;
        self.was_focused = focused;
        if focused {
            self.sample_hardware();
        } else {
            self.backend.input_samples();
        }
        self.session.tick(ctx.input(|i| i.time) * 1000.);
        self.hits.clear();
        ctx.data_mut(|d| {
            d.insert_temp(
                egui::Id::new("demo.targets"),
                std::collections::BTreeMap::<String, [f32; 4]>::new(),
            )
        });
        self.toolbar(ctx);
        self.timeline(ctx);
        self.body(ctx);
        if focused && self.source.is_none() {
            self.mouse(ctx);
        }
        self.play_feedback();
        self.diagnostics(ctx);
        ctx.request_repaint_after(std::time::Duration::from_millis(16));
    }
}
