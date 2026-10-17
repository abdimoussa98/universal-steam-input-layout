use super::*;

mod painting;
#[cfg(test)]
mod tests;

const HEIGHT: f32 = 48.0;
const WINDOW_COLOR: Color32 = Color32::from_rgb(244, 191, 88);

pub(super) fn draw(ui: &mut egui::Ui, data: &FrameData, now: u64) {
    // Reserving the same space prevents a held mouse target moving when its
    // gesture opens or closes. An inactive timeline contains no text.
    let (rect, response) = ui.allocate_exact_size(
        egui::vec2(ui.available_width(), HEIGHT),
        egui::Sense::hover(),
    );
    target_point(ui, "timeline", rect.center());
    let timeline = Timeline::active(data);
    let mut diagnostic = timeline.as_ref().map_or_else(
        || {
            serde_json::json!({ "active": false, "text": "", "progress": 0.0,
            "remaining_ms": null, "phase": null })
        },
        |timeline| timeline.diagnostic(now),
    );
    // The renderer may interpolate beyond the latest input sample. Keep the
    // displayed countdown's clock available alongside the rendered state.
    diagnostic["clock_ms"] = now.into();
    ui.ctx().data_mut(|data| {
        data.insert_temp(egui::Id::new("keybind.timeline"), diagnostic);
    });
    painting::rail(ui, rect);
    if let Some(timeline) = timeline {
        timeline.paint(ui, rect, now);
        response.on_hover_ui(|ui| timeline.details(ui));
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

fn lifecycle(phase: Phase) -> bool {
    matches!(
        phase,
        Phase::Pressed
            | Phase::Window
            | Phase::Second
            | Phase::Hold
            | Phase::Cover
            | Phase::Consumed
            | Phase::Combined
            | Phase::CombinedCover
    )
}

impl<'a> Timeline<'a> {
    fn active(data: &'a FrameData) -> Option<Self> {
        if data.state.status != InputStatus::Live || data.state.gestures.uncertainty.is_some() {
            return None;
        }
        let n = data.state.timer_owner(&data.profile)?;
        let timeline = Self::new(data, n);
        lifecycle(timeline.lane.phase).then_some(timeline)
    }

    fn new(data: &'a FrameData, n: usize) -> Self {
        let profile = data.profile.dashboard.as_ref().unwrap();
        let control = Control::OWNERS[n];
        let mut recipe = profile.recipe(data.state.mode, control).unwrap().clone();
        let steering = data.state.mode == Mode::Steering
            && lifecycle(data.state.gestures.steering_lane.phase)
            && !data.state.input.down(Control::Select)
            && !data.state.input.down(Control::Start)
            && profile.steering.is_some();
        let lane = if steering {
            let s = profile.steering.as_ref().unwrap();
            recipe.hold_ms = s.hold_ms;
            recipe.window_ms = s.window_ms;
            recipe.output_ms = s.output_ms;
            recipe.cover_ms = s.cover_ms;
            recipe.tap_label = if data.state.gestures.steering_direction < 0 {
                "Scroll up"
            } else {
                "Scroll down"
            }
            .into();
            recipe.hold_label = "Tap Cover".into();
            &data.state.gestures.steering_lane
        } else {
            &data.state.gestures.lanes[n]
        };
        Self {
            data,
            profile,
            control,
            recipe,
            lane,
            steering,
        }
    }

    fn combined(&self) -> bool {
        matches!(self.lane.phase, Phase::Combined | Phase::CombinedCover)
    }

    fn real_ms(&self, ms: u64) -> u64 {
        ms.saturating_mul(u64::from(self.data.state.timing_scale()))
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

    fn summary(&self) -> String {
        if self.combined() {
            gesture_binding(
                "Mod 2",
                self.profile
                    .combined_release_label
                    .as_deref()
                    .unwrap_or("Stateful layer switch"),
            )
        } else if self.steering {
            gesture_binding(&self.recipe.tap_label, &self.recipe.hold_label)
        } else {
            recipe_binding(&self.recipe)
        }
    }

    fn duration(&self) -> u64 {
        match self.lane.phase {
            Phase::Window => self.recipe.window_ms,
            Phase::Second | Phase::Cover => self.recipe.cover_ms,
            Phase::Combined | Phase::CombinedCover => self.profile.combined_hold_ms,
            _ => self.recipe.hold_ms,
        }
    }

    fn progress(&self, now: u64) -> f32 {
        if matches!(
            self.lane.phase,
            Phase::Hold | Phase::Cover | Phase::Consumed | Phase::CombinedCover
        ) {
            return 1.0;
        }
        let duration = self.duration().max(1);
        now.saturating_sub(self.lane.started_ms).min(duration) as f32 / duration as f32
    }

    fn remaining_ms(&self, now: u64) -> Option<u64> {
        self.lane
            .deadline_ms
            .map(|deadline| self.real_ms(deadline.saturating_sub(now)))
    }

    fn status(&self, now: u64) -> String {
        let phase = match self.lane.phase {
            Phase::Pressed | Phase::Combined => "Initial hold",
            Phase::Window => "Release window",
            Phase::Second => "Second hold",
            _ => self.lane.phase.label(),
        };
        match self.remaining_ms(now) {
            Some(remaining) => format!("{phase} · {remaining} ms"),
            None => phase.into(),
        }
    }

    fn diagnostic(&self, now: u64) -> serde_json::Value {
        serde_json::json!({
            "active": true,
            "text": format!("{} · {}", self.summary(), self.status(now)),
            "progress": self.progress(now),
            "remaining_ms": self.remaining_ms(now),
            "phase": self.lane.phase,
        })
    }

    fn details(&self, ui: &mut egui::Ui) {
        ui.strong(format!("{} · {}", self.owner(), self.summary()));
        if self.combined() {
            ui.label("Releasing either bumper switches layers until Tap Cover applies.");
        } else if self.steering {
            ui.label("Release for scrolling; hold until Tap Cover applies.");
        } else {
            for outcome in timed_gesture_outcomes(&self.recipe) {
                ui.label(outcome);
            }
        }
        if self.lane.phase == Phase::Window {
            ui.label(format!(
                "{} after {} ms. Press again before the window closes to begin a second hold.",
                compact_binding(&self.recipe.tap_label),
                self.real_ms(self.recipe.output_ms),
            ));
        }
    }
}
