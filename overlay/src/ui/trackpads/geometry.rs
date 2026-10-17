use super::*;

#[derive(Clone, Copy)]
pub(in crate::ui) struct Geometry {
    pub center: egui::Pos2,
    pub half: f32,
    pub angle: f32,
}
impl Geometry {
    pub fn at(self, x: f32, y: f32) -> egui::Pos2 {
        self.center
            + egui::vec2(
                x * self.angle.cos() - y * self.angle.sin(),
                x * self.angle.sin() + y * self.angle.cos(),
            ) * self.half
    }
    pub fn hover(self, ui: &egui::Ui) -> Option<[f32; 2]> {
        let Self {
            center,
            half,
            angle,
        } = self;
        if !ui.rect_contains_pointer(egui::Rect::from_center_size(
            center,
            egui::vec2(half * 2.3, half * 2.3),
        )) {
            return None;
        }
        ui.input(|i| i.pointer.hover_pos()).and_then(|pos| {
            let delta = (pos - center) / half;
            let xy = [
                delta.x * angle.cos() + delta.y * angle.sin(),
                -delta.x * angle.sin() + delta.y * angle.cos(),
            ];
            let distance = xy[0].hypot(xy[1]);
            (distance <= pad_edge(xy[1].atan2(xy[0]))).then_some(xy)
        })
    }
}
pub(super) fn pad_edge(angle: f32) -> f32 {
    let (x, y) = (angle.cos().abs(), angle.sin().abs());
    let corner = 62.0 / 82.0;
    let radius = 20.0 / 82.0;
    if y <= corner * x {
        1.0 / x
    } else if x <= corner * y {
        1.0 / y
    } else {
        corner * (x + y)
            + (radius * radius - corner * corner * (x - y) * (x - y))
                .max(0.0)
                .sqrt()
    }
}
