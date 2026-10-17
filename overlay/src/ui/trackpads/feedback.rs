use super::*;

#[derive(Clone, Copy, Default)]
pub(in crate::ui) struct Feedback {
    pub position: Option<[f32; 2]>,
    pub pressed: bool,
    pub live: bool,
}

pub(in crate::ui) fn feedback(
    ui: &egui::Ui,
    data: &FrameData,
    side: usize,
    hover: Option<[f32; 2]>,
) -> Feedback {
    let key = egui::Id::new(format!("pad:{side}:pressure-pressed"));
    let pressed = ui.ctx().data_mut(|d| {
        let force = d
            .get_temp::<u16>(egui::Id::new("pad:click-force"))
            .unwrap_or(15);
        let was_pressed = d.get_temp::<bool>(key).unwrap_or(false);
        let pressed = data.state.status == InputStatus::Live
            && data.state.input.pad_pressed(side, force * 10, was_pressed);
        d.insert_temp(key, pressed);
        pressed
    });
    if data.state.status == InputStatus::Live {
        if let Some(touch) = data.state.input.pads[side]
            .as_ref()
            .filter(|pad| pad.touching)
        {
            return Feedback {
                position: Some(
                    touch
                        .position
                        .map(|v| f32::from(v.clamp(-1000, 1000)) / 1000.0),
                ),
                pressed,
                live: true,
            };
        }
        if pressed {
            return Feedback {
                position: None,
                pressed: true,
                live: true,
            };
        }
    }
    Feedback {
        position: hover,
        pressed: hover.is_some() && ui.input(|i| i.pointer.primary_down()),
        ..Feedback::default()
    }
}

pub(in crate::ui) fn record_feedback(
    ui: &egui::Ui,
    side: usize,
    pad: &TrackpadBindings,
    input: Feedback,
) {
    let zone = match input
        .position
        .and_then(|xy| pad.regions.as_ref().map(|r| r.zone(xy)))
    {
        Some(PadZone::Inner) => "inner".to_string(),
        Some(PadZone::Overlap) => "overlap".into(),
        Some(PadZone::Outer(n)) => format!("outer{n}"),
        None => "none".into(),
    };
    let value = format!(
        "{}:{zone}:{}",
        if input.live {
            "live"
        } else if input.position.is_some() {
            "hover"
        } else {
            "idle"
        },
        if input.pressed { "pressed" } else { "released" }
    );
    ui.ctx()
        .data_mut(|d| d.insert_temp(egui::Id::new(format!("pad:{side}:feedback")), value));
    ui.ctx().data_mut(|d| {
        d.insert_temp(
            egui::Id::new(format!("pad:{side}:layer")),
            if input.pressed {
                "click".to_string()
            } else {
                "touch".to_string()
            },
        )
    });
}
