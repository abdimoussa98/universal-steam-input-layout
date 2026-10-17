use super::{
    ACCENT, BORDER, DemoApp, MUTED, SURFACE,
    mouse::{Hit, Target},
    target,
};
use crate::demo::Input;
use eframe::egui::{self, Color32, Rect, Sense, Stroke, vec2};

impl DemoApp {
    pub(super) fn gyro_panel(&mut self, ui: &mut egui::Ui) {
        let status = self.session.engine.gyro_status();
        ui.horizontal(|ui| {
            ui.heading(if status["cursor"] == true {
                "Cursor Gyro"
            } else {
                "Gyro"
            });
            ui.label(
                egui::RichText::new(status["status"].as_str().unwrap_or("Off")).color(
                    if status["active"] == true {
                        ACCENT
                    } else {
                        MUTED
                    },
                ),
            );
        });
        ui.label(
            egui::RichText::new(status["reason"].as_str().unwrap_or(""))
                .small()
                .color(MUTED),
        );
        let (rect, _) = ui.allocate_exact_size(vec2(ui.available_width(), 210.), Sense::hover());
        cuboid(
            ui,
            rect,
            self.session.engine.gyro.pose,
            status["active"] == true,
        );
        target(ui, "gyro", rect);
        self.hits.push(Hit {
            target: Target::Gyro,
            rect,
            clip: ui.clip_rect(),
            layer: ui.layer_id(),
        });
        self.motion_controls(ui);
        self.threshold(ui, &status);
        self.motion_source(ui);
    }
    fn motion_controls(&mut self, ui: &mut egui::Ui) {
        ui.horizontal(|ui| {
            ui.label("Drag to rotate");
            let fine = ui.checkbox(&mut self.fine_motion, "Fine motion");
            target(ui, "fine-motion", fine.rect);
            let r = ui.button("Recenter");
            target(ui, "recenter", r.rect);
            if r.clicked() {
                self.session.input(Input::Recenter);
                self.roll = 0.;
            }
        });
        let before = self.roll;
        let roll = ui.add_enabled(
            self.virtual_input_enabled(),
            egui::Slider::new(&mut self.roll, -180.0..=180.0).text("Roll"),
        );
        target(ui, "roll", roll.rect);
        if roll.changed() {
            self.session.input(Input::Motion {
                degrees: [0., 0., f64::from(self.roll - before)],
                duration_ms: 16,
            });
        }
    }
    fn motion_source(&mut self, ui: &mut egui::Ui) {
        if self.source.is_none() {
            ui.label(
                egui::RichText::new(if self.session.engine.layout.controller == "dse" {
                    "Mouse motion · enable Cursor Gyro with Select + R3."
                } else {
                    "Mouse motion · enable Cursor Gyro with Select + R3, then hold RS touch."
                })
                .small()
                .color(MUTED),
            );
        } else if let Some(sample) = self.physical.as_ref().and_then(|f| f.motion.as_ref()) {
            ui.horizontal(|ui| {
                ui.label("Device motion");
                if ui.button("Calibrate at rest").clicked() {
                    self.gyro_bias = sample.rate;
                }
            });
        } else {
            ui.label("Motion unavailable from this input source. Choose Mouse to simulate it.");
        }
    }
    fn threshold(&self, ui: &mut egui::Ui, status: &serde_json::Value) {
        if status["cursor"] == true {
            let threshold = status["threshold"].as_f64().unwrap_or(5.);
            let gyro = &self.session.engine.gyro;
            let pending = gyro.pending[0].hypot(gyro.pending[1]);
            ui.add(
                egui::ProgressBar::new((pending / threshold.max(0.001)) as f32)
                    .text(format!(
                        "Movement building up · {:.1} / {threshold:.0}",
                        pending
                    ))
                    .fill(ACCENT),
            );
            let pulse = gyro
                .last_output
                .is_some_and(|at| self.session.engine.now.saturating_sub(at) < 120);
            ui.label(
                egui::RichText::new(if pulse {
                    "Movement emitted"
                } else {
                    "Waiting for movement"
                })
                .color(if pulse { ACCENT } else { MUTED }),
            );
            ui.label(
                egui::RichText::new("Threshold feedback is simulated; sound is optional.")
                    .small()
                    .color(MUTED),
            );
        }
    }
}
fn cuboid(ui: &egui::Ui, rect: Rect, pose: [f64; 3], active: bool) {
    let points = [
        [-1., -0.35, -0.65],
        [1., -0.35, -0.65],
        [1., 0.35, -0.65],
        [-1., 0.35, -0.65],
        [-1., -0.35, 0.65],
        [1., -0.35, 0.65],
        [1., 0.35, 0.65],
        [-1., 0.35, 0.65],
    ];
    let vertices: Vec<_> = points
        .into_iter()
        .map(|p| rotate(p, [pose[0] + 24., pose[1] + 25., pose[2]]))
        .collect();
    let mut faces = vec![
        ([0, 1, 2, 3], Color32::from_rgb(49, 91, 94)),
        ([4, 5, 6, 7], ACCENT),
        ([0, 1, 5, 4], Color32::from_rgb(79, 125, 169)),
        ([3, 2, 6, 7], Color32::from_rgb(53, 77, 108)),
        ([0, 3, 7, 4], Color32::from_rgb(183, 153, 92)),
        ([1, 2, 6, 5], Color32::from_rgb(113, 91, 135)),
    ];
    faces.sort_by(|(a, _), (b, _)| {
        let depth = |ids: &[usize; 4]| ids.iter().map(|i| vertices[*i][2]).sum::<f64>();
        depth(a).total_cmp(&depth(b))
    });
    ui.painter().rect_filled(rect, 14., SURFACE);
    for (ids, color) in faces {
        let points = ids
            .iter()
            .map(|i| {
                let p = vertices[*i];
                let perspective = 4. / (4. - p[2]);
                rect.center() + vec2(p[0] as f32, -p[1] as f32) * 65. * perspective as f32
            })
            .collect();
        ui.painter().add(egui::Shape::convex_polygon(
            points,
            if active {
                color
            } else {
                color.gamma_multiply(0.5)
            },
            Stroke::new(1.5_f32, BORDER),
        ));
    }
}
fn rotate([x, y, z]: [f64; 3], pose: [f64; 3]) -> [f64; 3] {
    let [p, yaw, r] = pose.map(f64::to_radians);
    let (y, z) = (y * p.cos() - z * p.sin(), y * p.sin() + z * p.cos());
    let (x, z) = (
        x * yaw.cos() + z * yaw.sin(),
        -x * yaw.sin() + z * yaw.cos(),
    );
    [x * r.cos() - y * r.sin(), x * r.sin() + y * r.cos(), z]
}
