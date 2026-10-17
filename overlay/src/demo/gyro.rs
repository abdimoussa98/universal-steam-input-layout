use super::data::number;
use super::{Engine, Settings};
use serde::Serialize;

#[derive(Default, Serialize)]
pub(crate) struct Gyro {
    pub pose: [f64; 3],
    pub raw: [f64; 2],
    pub pending: [f64; 2],
    pub emitted: [f64; 2],
    pub last_output: Option<u64>,
    pub ticks: u64,
    #[serde(skip)]
    pub response: String,
}
impl Gyro {
    pub fn recenter(&mut self) {
        self.pose = [0.; 3];
    }
}
impl Engine {
    pub(crate) fn refresh_gyro_gate(&mut self) {
        let (active, settings, _) = self.gyro_gate();
        let response = format!("{active}:{settings:?}");
        if self.gyro.response != response {
            self.gyro.pending = [0.; 2];
            self.gyro.response = response;
        }
    }
    fn gyro_gate(&self) -> (bool, Settings, String) {
        let (mode, settings, condition) = self.effective("gyro");
        let disabled = mode != "gyro_to_mouse";
        let selected = condition.as_ref().is_none_or(|c| c.satisfied(&self.held));
        let reason = if disabled {
            "Disabled by the effective source"
        } else if !selected {
            "Required touch or button selector is not held"
        } else {
            "Activation gate open"
        };
        (!disabled && selected, settings, reason.into())
    }
    pub(crate) fn gyro_status(&self) -> serde_json::Value {
        let (active, settings, reason) = self.gyro_gate();
        let moving = active
            && self
                .gyro
                .last_output
                .is_some_and(|t| self.now.saturating_sub(t) < 120);
        serde_json::json!({"active":active, "status":if !active {"Off"} else if moving {"Moving"} else {"Ready"},
            "reason":reason, "cursor":number(&settings,"mouse_move_threshold",0.) > 0.,
            "threshold":number(&settings,"mouse_move_threshold",0.), "settings":settings,
            "motion":self.gyro, "fidelity":"Simulated motion; threshold scale and feedback cadence are approximations"})
    }
    pub(crate) fn motion(&mut self, degrees: [f64; 3], duration: u64) {
        for (i, d) in degrees.iter().enumerate() {
            self.gyro.pose[i] += d;
        }
        let (active, settings, _) = self.gyro_gate();
        let response = format!("{active}:{settings:?}");
        if response != self.gyro.response {
            self.gyro.pending = [0.; 2];
            self.gyro.response = response;
        }
        self.gyro.emitted = [0.; 2];
        let delta = projected(degrees, self.gyro.pose, &settings);
        self.gyro.raw = delta;
        if !active {
            self.gyro.pending = [0.; 2];
            return;
        }
        let speed =
            degrees.iter().map(|v| v * v).sum::<f64>().sqrt() * 1000. / duration.max(1) as f64;
        let precision = number(&settings, "gyro_precision_speed", 300.) / 100.;
        let gain = (speed / precision.max(0.001)).clamp(0., 1.);
        for (i, v) in delta.iter().enumerate() {
            self.gyro.pending[i] += v * gain;
        }
        let threshold = number(&settings, "mouse_move_threshold", 0.);
        if self.gyro.pending[0].hypot(self.gyro.pending[1]) < threshold {
            return;
        }
        let output = self.gyro.pending;
        if output.iter().all(|v| v.abs() < 1e-9) {
            return;
        }
        self.gyro.pending = [0.; 2];
        self.gyro.emitted = output;
        self.gyro.last_output = Some(self.now);
        self.move_pointer(output, "gyro");
        if threshold > 0. {
            self.gyro.ticks += 1;
            self.note("gyro_tick", "Simulated threshold crossing".into());
        }
    }
}
fn projected(degrees: [f64; 3], pose: [f64; 3], settings: &Settings) -> [f64; 2] {
    let [pitch, yaw, roll] = degrees;
    let horizontal = match number(settings, "gyro_to_2d_conversion_style", 4.) as u8 {
        0 => yaw,
        1 => -roll,
        2 => yaw - roll,
        // Player/world space projection uses the block's pitch as its gravity reference.
        _ => yaw * pose[0].to_radians().cos() - roll * pose[0].to_radians().sin(),
    };
    let sensitivity = number(settings, "gyro_natural_sensitivity", 300.) / 100.;
    let pixels = number(settings, "flickstick_rotation_sensitivity", 3853.) / 360.;
    let vertical = number(settings, "gyro_vertical_horizontal_ratio", 100.) / 100.;
    [
        horizontal * sensitivity * pixels,
        -pitch * sensitivity * pixels * vertical,
    ]
}
