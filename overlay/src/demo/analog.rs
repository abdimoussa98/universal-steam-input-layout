use super::data::number;
use super::{Engine, Settings};
use serde::Serialize;

const DIRECTIONS: [&str; 4] = ["dpad_north", "dpad_east", "dpad_south", "dpad_west"];
#[derive(Clone, Default, Serialize)]
pub(crate) struct Surface {
    pub position: [f64; 2],
    pub touching: bool,
    pub click: bool,
    pub mode: String,
    pub angle: Option<f64>,
    pub accumulated: f64,
    pub origin: [f64; 2],
    pub swiped: bool,
}
impl Engine {
    pub(crate) fn surface(
        &mut self,
        source: &str,
        position: [f64; 2],
        touching: bool,
        click: bool,
    ) {
        let old = self.surfaces.get(source).cloned().unwrap_or_default();
        let mut next = old.clone();
        next.position = position;
        next.touching = touching;
        next.click = click;
        if touching != old.touching {
            next.angle = None;
            next.accumulated = 0.;
            next.origin = position;
            next.swiped = false;
        }
        self.surfaces.insert(source.into(), next);
        let pad = source.ends_with("trackpad");
        // Position is available before touch/click changes expose new bindings.
        if touching || !pad {
            self.surface_edge(source);
        }
        if pad && touching && !old.touching {
            self.center_contact(source);
        }
        self.button(&format!("{source}/touch"), touching, false);
        self.button(&format!("{source}/click"), click, false);
        let (mode, settings, _) = self.effective(source);
        self.surface_directions(source, &mode, &settings);
        if touching && old.touching && mode == old.mode {
            match mode.as_str() {
                "scrollwheel" => self.circular(source, &settings, &old),
                "absolute_mouse" => self.pad_pointer(position, &old, &settings),
                "2dscroll" => self.swipe(source, &settings),
                _ => {}
            }
        }
        if let Some(surface) = self.surfaces.get_mut(source) {
            surface.mode = mode;
        }
        if !touching && pad {
            self.clear_surface_edges(source);
        }
    }
    fn surface_edge(&mut self, source: &str) {
        let surface = &self.surfaces[source];
        let radius = surface.position[0].hypot(surface.position[1]).min(1.) * 32767.;
        let (_, settings, _) = self.effective(source);
        let control = format!("{source}/edge");
        let (outer, inner) = self.soft_ranges(source);
        let edge = number(&settings, "edge_binding_radius", outer.unwrap_or(32767.));
        let between = source.ends_with("trackpad")
            && outer
                .zip(inner)
                .is_some_and(|(a, b)| radius >= a && radius < b);
        self.button(
            &control,
            (radius >= edge && radius > 0.) || between,
            between,
        );
    }
    pub(crate) fn soft_ranges(&self, source: &str) -> (Option<f64>, Option<f64>) {
        let entries = self
            .layout
            .layers
            .iter()
            .filter_map(|l| l.sources.get(source))
            .filter_map(|g| self.layout.groups[*g].inputs.get("edge"))
            .flatten()
            .filter(|e| e.kind == "Soft_Press");
        let mut outer: Option<f64> = None;
        let mut inner: Option<f64> = None;
        for entry in entries {
            let value = entry.value("activation_threshold") as f64;
            if entry.flag("edge_binding_invert") {
                inner = Some(inner.unwrap_or(value).max(value));
            } else {
                outer = Some(outer.unwrap_or(value).min(value));
            }
        }
        (outer, inner)
    }
    fn center_contact(&mut self, source: &str) {
        let (mode, settings, _) = self.effective(source);
        let position = self.surfaces[source].position;
        if mode != "dpad"
            || position[0].hypot(position[1]) * 32767. > number(&settings, "deadzone", 0.)
        {
            return;
        }
        let control = format!("{source}/edge");
        self.end(&control, super::Phase::Up, false);
        self.establish(&control, super::Phase::Up, "pressed");
        self.drain();
    }
    fn clear_surface_edges(&mut self, source: &str) {
        for name in DIRECTIONS.into_iter().chain(["edge"]) {
            let control = format!("{source}/{name}");
            if self.held.contains(&control) {
                self.button(&control, false, false);
            }
        }
    }
    fn surface_directions(&mut self, source: &str, mode: &str, settings: &Settings) {
        let surface = self.surfaces[source].clone();
        let pad = source.ends_with("trackpad");
        let [x, y] = surface.position;
        let radius = x.hypot(y) * 32767.;
        let active = (mode == "dpad"
            || (!pad && matches!(mode, "joystick_mouse" | "joystick_move")))
            && (!pad || surface.touching)
            && radius
                > number(
                    settings,
                    "deadzone",
                    number(settings, "deadzone_inner_radius", 13276.),
                )
            && (number(settings, "requires_click", 0.) == 0. || surface.click);
        let hits = if pad {
            [y < -x.abs(), x > y.abs(), y > x.abs(), x < -y.abs()]
        } else {
            [y < -0.25, x > 0.25, y > 0.25, x < -0.25]
        };
        // Releases precede newly entered directions; diagonal sticks may hold two.
        for down in [false, true] {
            for (index, name) in DIRECTIONS.iter().enumerate() {
                if (active && hits[index]) == down {
                    self.button(&format!("{source}/{name}"), down, false);
                }
            }
        }
    }
    fn pulse(&mut self, control: &str) {
        self.button(control, true, false);
        self.button(control, false, false);
    }
    fn circular(&mut self, source: &str, settings: &Settings, old: &Surface) {
        let surface = self.surfaces.get_mut(source).unwrap();
        let [x, y] = surface.position;
        if x.hypot(y) < 0.2 {
            surface.angle = None;
            surface.accumulated = 0.;
            return;
        }
        let angle = y.atan2(x).to_degrees();
        let previous = old
            .angle
            .unwrap_or_else(|| old.position[1].atan2(old.position[0]).to_degrees());
        let delta = (angle - previous + 180.).rem_euclid(360.) - 180.;
        surface.angle = Some(angle);
        if delta.signum() != surface.accumulated.signum() {
            surface.accumulated = 0.;
        }
        surface.accumulated += delta;
        // Export scale is not documented by Valve; demo convention: tenths of a degree.
        let threshold = (number(settings, "scroll_angle", 150.) / 10.).max(1.);
        let ticks = (surface.accumulated / threshold).trunc() as i32;
        surface.accumulated -= f64::from(ticks) * threshold;
        let control = format!(
            "{source}/{}",
            if ticks >= 0 {
                "scroll_clockwise"
            } else {
                "scroll_counterclockwise"
            }
        );
        for _ in 0..ticks.unsigned_abs().min(360) {
            self.pulse(&control);
        }
    }
    fn pad_pointer(&mut self, position: [f64; 2], old: &Surface, settings: &Settings) {
        let scale = number(settings, "sensitivity", 100.) * 2.;
        let delta = [
            (position[0] - old.position[0]) * scale,
            (position[1] - old.position[1]) * scale,
        ];
        self.move_pointer(delta, "pad");
    }
    fn swipe(&mut self, source: &str, settings: &Settings) {
        let surface = &self.surfaces[source];
        if surface.swiped {
            return;
        }
        let dx = surface.position[0] - surface.origin[0];
        let dy = surface.position[1] - surface.origin[1];
        let threshold = 0.3 * 50. / number(settings, "sensitivity", 50.).max(1.);
        if dx.hypot(dy) < threshold {
            return;
        }
        let index = if dx.abs() > dy.abs() {
            if dx > 0. { 1 } else { 3 }
        } else if dy > 0. {
            2
        } else {
            0
        };
        self.surfaces.get_mut(source).unwrap().swiped = true;
        self.pulse(&format!("{source}/{}", DIRECTIONS[index]));
    }
    pub(crate) fn trigger(&mut self, source: &str, value: f64) {
        self.trigger_values.insert(source.into(), value);
        let (_, settings, _) = self.effective(source);
        let held = self.held.contains(&format!("{source}/edge"));
        let radius = number(&settings, "edge_binding_radius", 0.) / 32767.;
        let threshold = if held { radius * 0.95 } else { radius };
        self.button(&format!("{source}/edge"), value > threshold, false);
        self.button(
            &format!("{source}/click"),
            value >= if held { 0.94 } else { 0.98 },
            false,
        );
        if let Some(output) = settings.get("output_trigger") {
            self.output
                .axes
                .insert(format!("trigger:{output}"), [value, 0.]);
        }
    }
    pub(crate) fn integrate_sticks(&mut self, end: u64) {
        let dt = end.saturating_sub(self.integrated_at) as f64 / 1000.;
        self.integrated_at = end;
        let before = self.now;
        self.now = end;
        self.output.axes.clear();
        for (source, value) in &self.trigger_values {
            let (mode, settings, _) = self.effective(source);
            if mode == "trigger"
                && let Some(output) = settings.get("output_trigger")
            {
                self.output
                    .axes
                    .insert(format!("trigger:{output}"), [*value, 0.]);
            }
        }
        for source in ["joystick", "right_joystick"] {
            let Some(surface) = self.surfaces.get(source) else {
                continue;
            };
            let position = surface.position;
            let (mode, settings, _) = self.effective(source);
            let deadzone = number(&settings, "deadzone_inner_radius", 3280.) / 32767.;
            let outer = number(&settings, "deadzone_outer_radius", 32767.) / 32767.;
            let radius = position[0].hypot(position[1]);
            let amount = ((radius - deadzone) / (outer - deadzone).max(0.001)).clamp(0., 1.);
            let xy = position.map(|v| v / radius.max(0.001) * amount);
            if mode == "joystick_mouse" {
                let sensitivity = number(&settings, "sensitivity", 150.);
                let vertical = number(&settings, "sensitivity_vert_scale", 100.) / 100.;
                self.move_pointer(
                    [
                        xy[0] * sensitivity * dt,
                        xy[1] * sensitivity * dt * vertical,
                    ],
                    source,
                );
            } else if mode == "joystick_move" {
                let output = settings
                    .get("output_joystick")
                    .map(String::as_str)
                    .unwrap_or("0");
                self.output.axes.insert(format!("stick:{output}"), xy);
            }
        }
        self.now = before;
    }
    pub(crate) fn move_pointer(&mut self, delta: [f64; 2], source: &str) {
        if delta.iter().all(|v| v.abs() < 1e-9) {
            return;
        }
        for (i, v) in delta.iter().enumerate() {
            self.output.pointer[i] += v;
        }
        self.note(
            "pointer",
            format!("{source} {:.4} {:.4}", delta[0], delta[1]),
        );
    }
    pub(crate) fn analog_soft_active(&self, binding: &super::Binding) -> bool {
        let Some((source, name)) = binding.control.split_once('/') else {
            return true;
        };
        let Some(surface) = self.surfaces.get(source) else {
            return true;
        };
        if name != "edge" || binding.entry.kind != "Soft_Press" {
            return true;
        }
        let radius = surface.position[0].hypot(surface.position[1]) * 32767.;
        let threshold = binding.entry.value("activation_threshold") as f64;
        (!source.ends_with("trackpad") || surface.touching)
            && if binding.inverted {
                radius < threshold
            } else {
                radius >= threshold
            }
    }
}
