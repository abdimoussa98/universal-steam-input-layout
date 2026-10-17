use super::*;

pub(super) fn draw(ui: &mut egui::Ui, data: &FrameData, now: u64) {
    steering_status(ui, data);
    let Some(n) = data.state.timer_owner(&data.profile) else {
        ui.label("Load a dashboard profile to see timed gestures.");
        return;
    };
    Timeline::new(data, n).show(ui, now);
    if let Some(message) = &data.state.gestures.uncertainty {
        ui.colored_label(Color32::YELLOW, message);
    }
}

fn steering_status(ui: &mut egui::Ui, data: &FrameData) {
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
}
struct Timeline<'a> {
    data: &'a FrameData,
    profile: &'a DashboardProfile,
    control: Control,
    recipe: Recipe,
    lane: &'a Lane,
    steering: bool,
}

struct Stage {
    index: u8,
    duration: u64,
    start: String,
    end: String,
    hint: String,
}

impl<'a> Timeline<'a> {
    fn new(data: &'a FrameData, n: usize) -> Self {
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

        Self {
            data,
            profile,
            control,
            recipe: r,
            lane,
            steering,
        }
    }
    fn combined(&self) -> bool {
        matches!(self.lane.phase, Phase::Combined | Phase::CombinedCover)
    }
    fn live(&self) -> bool {
        self.data.state.status == InputStatus::Live
    }
    fn real_ms(&self, ms: u64) -> u64 {
        ms * u64::from(self.data.state.timing_scale())
    }
    fn owner(&self) -> &'static str {
        if self.steering {
            if self.data.state.gestures.steering_direction < 0 {
                "Left stick up"
            } else {
                "Left stick down"
            }
        } else if self.combined() {
            "L1 + R1"
        } else {
            self.control.label()
        }
    }
    fn hold_ms(&self) -> u64 {
        if self.combined() {
            self.profile.combined_hold_ms
        } else {
            self.recipe.hold_ms
        }
    }
    fn tap(&self) -> &str {
        if self.combined() {
            self.profile
                .combined_release_label
                .as_deref()
                .unwrap_or("Stateful layer switch")
        } else {
            &self.recipe.tap_label
        }
    }
    fn hold(&self) -> &str {
        if self.combined() {
            "Tap Cover"
        } else {
            self.recipe
                .modifier_label
                .as_deref()
                .unwrap_or(&self.recipe.hold_label)
        }
    }
    fn summary(&self) -> String {
        if self.combined() {
            if self.lane.phase == Phase::CombinedCover {
                "Mod 2".into()
            } else {
                gesture_binding("Mod 2", self.tap())
            }
        } else if self.steering {
            gesture_binding(self.tap(), self.hold())
        } else {
            recipe_binding(&self.recipe)
        }
    }
    fn stage(&self) -> Stage {
        let r = &self.recipe;
        let lane = self.lane;
        let hold_ms = self.hold_ms();
        let hold = self.hold();
        let tap = self.tap();
        let real_ms = |ms| self.real_ms(ms);
        let (stage, duration, start, end, hint) = match lane.phase {
            Phase::Window => (
                1,
                r.window_ms,
                "Released".to_string(),
                format!("Window closes {} ms", real_ms(r.window_ms)),
                format!(
                    "{} at {} ms after release. Press again before this window closes.",
                    r.tap_label,
                    real_ms(r.output_ms)
                ),
            ),
            Phase::Second | Phase::Cover => (
                2,
                r.cover_ms,
                "Second hold".into(),
                format!("Cover at {} ms", real_ms(r.cover_ms)),
                if lane.phase == Phase::Cover {
                    "Tap, then hold is active. Release ends the gesture.".into()
                } else {
                    "Keep the second press held until its cover applies; releasing early reopens the release window.".into()
                },
            ),
            _ => (
                0,
                hold_ms,
                "Initial hold".into(),
                format!("Hold at {} ms", real_ms(hold_ms)),
                match lane.phase {
                    Phase::Hold => format!("{hold} active. Release ends the gesture."),
                    Phase::Consumed | Phase::CombinedCover => {
                        "Tap Cover applied. The modifier was used; release will not trigger a tap."
                            .into()
                    }
                    Phase::Unknown => {
                        "Release this button once to start tracking its timing.".into()
                    }
                    Phase::Interrupted => {
                        "Timing paused; inherited bindings remain visible.".into()
                    }
                    _ => format!(
                        "Release before {} ms for {tap}. Keep holding for {hold}.",
                        real_ms(hold_ms)
                    ),
                },
            ),
        };

        Stage {
            index: stage,
            duration,
            start,
            end,
            hint,
        }
    }
    fn show(&self, ui: &mut egui::Ui, now: u64) {
        let stage = self.stage();
        ui.add_space(8.0);
        egui::Frame::new()
            .fill(SURFACE)
            .stroke(egui::Stroke::new(1.0_f32, BORDER))
            .corner_radius(14.0)
            .inner_margin(16.0)
            .show(ui, |ui| {
                ui.set_width(ui.available_width());
                ui.horizontal_wrapped(|ui| {
                    ui.label(
                        RichText::new(self.summary())
                            .size(19.0)
                            .color(Color32::WHITE),
                    )
                    .on_hover_text(self.owner());
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        ui.label(
                            RichText::new(self.lane.phase.label())
                                .size(12.0)
                                .color(if self.live() { ACCENT } else { MUTED }),
                        );
                    });
                });
                ui.add_space(4.0);
                self.progress_bar(ui, &stage, now);
                self.countdown(ui, &stage, now);
                ui.collapsing("Gesture details", |ui| self.details(ui, &stage));
            });
    }
    fn progress_bar(&self, ui: &mut egui::Ui, stage: &Stage, now: u64) {
        let r = &self.recipe;
        let lane = self.lane;
        let live = self.live();
        let duration = stage.duration;
        let stage = stage.index;
        let amber = Color32::from_rgb(244, 191, 88);
        let teal = ACCENT;
        let (bar, _) =
            ui.allocate_exact_size(egui::vec2(ui.available_width(), 6.0), egui::Sense::hover());
        let painter = ui.painter();
        painter.rect_filled(bar, 6.0, Color32::from_rgb(49, 61, 77));
        let complete = matches!(
            lane.phase,
            Phase::Hold | Phase::Cover | Phase::Consumed | Phase::CombinedCover
        );
        let elapsed = now.saturating_sub(lane.started_ms).min(duration);
        let progress = if !live {
            0.0
        } else if complete {
            1.0
        } else if lane.deadline_ms.is_some() {
            elapsed as f32 / duration as f32
        } else {
            0.0
        };
        if progress > 0.0 {
            painter.rect_filled(
                egui::Rect::from_min_size(
                    bar.min,
                    egui::vec2(bar.width() * progress, bar.height()),
                ),
                6.0,
                if stage == 1 { amber } else { teal },
            );
        }
        if stage == 1 {
            let x = bar.left() + bar.width() * r.output_ms as f32 / r.window_ms as f32;
            painter.line_segment(
                [
                    egui::pos2(x, bar.top() - 3.0),
                    egui::pos2(x, bar.bottom() + 3.0),
                ],
                egui::Stroke::new(2.0_f32, Color32::WHITE),
            );
        }
    }
    fn countdown(&self, ui: &mut egui::Ui, stage: &Stage, now: u64) {
        ui.horizontal(|ui| {
            ui.small(&stage.start);
            if self.live()
                && let Some(deadline) = self.lane.deadline_ms
            {
                ui.label(
                    RichText::new(format!(
                        "{} ms left",
                        self.real_ms(deadline.saturating_sub(now))
                    ))
                    .color(if stage.index == 1 {
                        Color32::from_rgb(244, 191, 88)
                    } else {
                        ACCENT
                    })
                    .strong(),
                );
            }
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                ui.small(&stage.end);
            });
        });
    }
    fn details(&self, ui: &mut egui::Ui, stage: &Stage) {
        let combined = self.combined();
        let r = &self.recipe;
        let hold_ms = self.hold_ms();
        let tap = self.tap();
        let real_ms = |ms| self.real_ms(ms);
        let live = self.live();
        let lane = self.lane;
        let outcomes = timed_gesture_outcomes(r);
        if combined {
            ui.label(format!(
                "Hold: Mod 2. Release either bumper before {} ms to switch {tap}.",
                real_ms(hold_ms)
            ));
            ui.label("Once Tap Cover applies, releasing does not switch stateful layers.");
        } else if let Some(modifier) = &r.modifier_label {
            ui.label(format!(
                "Hold: {modifier}. Tap, then hold: {}.",
                r.tap_label
            ));
            ui.label(format!(
                "{} is a delayed effect after {} ms; {modifier} remains active.",
                r.hold_label,
                real_ms(r.hold_ms)
            ));
        } else {
            ui.label("Tap / tap, then hold :: Hold");
        }
        if !combined {
            for outcome in &outcomes {
                ui.label(outcome);
            }
        }
        ui.label(&stage.hint);
        if !live {
            ui.small("Connect a controller to animate this timeline.");
        } else if lane.phase == Phase::Idle {
            ui.small("Press a bumper, Select or Start. The bar follows its timed gesture.");
        }
    }
}
