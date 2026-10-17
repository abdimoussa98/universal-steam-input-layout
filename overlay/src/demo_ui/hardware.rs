use super::DemoApp;
use crate::{
    core::{Control, InputFrame},
    demo::Input,
};

impl DemoApp {
    pub(super) fn sample_hardware(&mut self) {
        let samples = self.backend.input_samples();
        let Some(id) = self.source.clone() else {
            return;
        };
        if self.session.paused || self.session.replaying {
            return;
        }
        let data = self.backend.data();
        let frame = if data.remote {
            (data.state.status == crate::core::InputStatus::Live).then_some(data.state.input)
        } else {
            data.settings
                .devices
                .iter()
                .find(|d| d.id == id)
                .map(|d| d.input.clone())
        };
        let Some(frame) = frame else {
            self.reset();
            self.source = None;
            return;
        };
        if id.starts_with("webhid:") && data.state.status != crate::core::InputStatus::Live {
            self.reset();
            return;
        }
        for (_, at, frame) in samples.into_iter().filter(|(device, _, _)| device == &id) {
            self.session.tick(at);
            self.hardware_frame(frame);
        }
        self.hardware_frame(frame);
    }
    fn hardware_frame(&mut self, frame: InputFrame) {
        let old = self.physical.clone().unwrap_or_default();
        self.hardware_buttons(&old, &frame);
        for side in 0..2 {
            let source = ["joystick", "right_joystick"][side];
            if old.stick_positions[side] != frame.stick_positions[side]
                || old.touches[side] != frame.touches[side]
            {
                let position = frame.stick_positions[side]
                    .unwrap_or_default()
                    .map(|v| f64::from(v) / 1000.);
                self.session.input(Input::Surface {
                    source: source.into(),
                    position,
                    touching: frame.touches[side].unwrap_or(false),
                    click: frame.down([Control::L3, Control::R3][side]),
                });
            }
            self.hardware_pad(&old, &frame, side);
            if old.triggers[side] != frame.triggers[side] {
                self.session.input(Input::Trigger {
                    source: ["left_trigger", "right_trigger"][side].into(),
                    value: f64::from(frame.triggers[side]) / 1000.,
                });
            }
        }
        for (side, control) in [
            "button_back_left_upper",
            "button_back_left",
            "button_back_right_upper",
            "button_back_right",
        ]
        .iter()
        .enumerate()
        {
            if frame.back_buttons[side] != old.back_buttons[side] {
                self.session.input(Input::Button {
                    control: format!("switch/{control}"),
                    down: frame.back_buttons[side].unwrap_or(false),
                });
            }
        }
        self.hardware_motion(&old, &frame);
        self.physical = Some(frame);
    }
    fn hardware_motion(&mut self, old: &InputFrame, frame: &InputFrame) {
        let Some(sample) = &frame.motion else {
            return;
        };
        let Some(previous) = &old.motion else {
            return;
        };
        let Some(ms) = sample.elapsed_ms(previous) else {
            return;
        };
        self.session.input(Input::Motion {
            degrees: std::array::from_fn(|i| {
                (f64::from(sample.rate[i]) - f64::from(self.gyro_bias[i])) * ms as f64 / 1_000_000.
            }),
            duration_ms: ms,
        });
    }
    fn hardware_buttons(&mut self, old: &InputFrame, frame: &InputFrame) {
        for (control, source) in Control::ALL.into_iter().zip([
            "button_diamond/button_a",
            "button_diamond/button_b",
            "button_diamond/button_x",
            "button_diamond/button_y",
            "switch/button_menu",
            "switch/button_escape",
            "dpad/dpad_north",
            "dpad/dpad_east",
            "dpad/dpad_south",
            "dpad/dpad_west",
            "joystick/click",
            "right_joystick/click",
            "switch/left_bumper",
            "switch/right_bumper",
            "left_trigger/edge",
            "right_trigger/edge",
        ]) {
            if matches!(control, Control::L2 | Control::R2) {
                continue;
            }
            if old.down(control) != frame.down(control) {
                self.session.input(Input::Button {
                    control: source.into(),
                    down: frame.down(control),
                });
            }
        }
    }
    fn hardware_pad(&mut self, old: &InputFrame, frame: &InputFrame, side: usize) {
        if old.pads[side] == frame.pads[side]
            && old.pad_clicks[side] == frame.pad_clicks[side]
            && old.pad_pressures[side] == frame.pad_pressures[side]
        {
            return;
        }
        if let Some(pad) = &frame.pads[side] {
            let source = ["left_trackpad", "right_trackpad"][side];
            let pressed = self
                .session
                .engine
                .surfaces
                .get(source)
                .is_some_and(|s| s.click);
            self.session.input(Input::Surface {
                source: source.into(),
                position: pad.position.map(|v| f64::from(v) / 1000.),
                touching: pad.touching,
                click: frame.pad_pressed(side, 500, pressed),
            });
        }
    }
    pub(super) fn enable_sound(&mut self) {
        #[cfg(all(target_arch = "wasm32", feature = "web"))]
        sound_enable(self.sound);
    }
    pub(super) fn play_feedback(&mut self) {
        #[cfg(all(target_arch = "wasm32", feature = "web"))]
        if self.sound && !self.session.paused {
            for event in self.session.engine.output.events.iter().filter(|e| {
                e.sequence > self.feedback_seen
                    && matches!(e.kind.as_str(), "beep" | "gyro_tick" | "haptic")
            }) {
                sound_tick(event.at as f64, self.session.scale, &event.kind);
            }
        }
        self.feedback_seen = self.session.engine.output.sequence;
    }
    pub(super) fn cancel_sound(&self) {
        #[cfg(all(target_arch = "wasm32", feature = "web"))]
        sound_cancel();
    }
}
#[cfg(all(target_arch = "wasm32", feature = "web"))]
#[wasm_bindgen::prelude::wasm_bindgen]
extern "C" {
    #[wasm_bindgen::prelude::wasm_bindgen(js_namespace=window,js_name=demoSoundEnable)]
    fn sound_enable(enabled: bool);
    #[wasm_bindgen::prelude::wasm_bindgen(js_namespace=window,js_name=demoSoundTick)]
    fn sound_tick(at: f64, scale: u8, kind: &str);
    #[wasm_bindgen::prelude::wasm_bindgen(js_namespace=window,js_name=demoSoundCancel)]
    fn sound_cancel();
}
