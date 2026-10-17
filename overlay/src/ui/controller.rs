use super::*;
mod controls;

const SHELL: Color32 = Color32::from_rgb(35, 39, 46);
const EDGE: Color32 = Color32::from_rgb(66, 73, 84);
const DARK: Color32 = Color32::from_rgb(21, 24, 29);

struct Diagram<'a> {
    ui: &'a egui::Ui,
    data: &'a FrameData,
    area: egui::Rect,
    scale: f32,
}

// Symmetric Ibex controls in a single, softly rounded shell. Physical control
// names live in hover help; the drawing gives its space to the actual bindings.
pub(super) fn draw(ui: &mut egui::Ui, data: &FrameData) {
    let available = ui.available_width();
    let width = available.min(780.0);
    let scale = width / 1000.0;
    let (row, _) =
        ui.allocate_exact_size(egui::vec2(available, 685.0 * scale), egui::Sense::hover());
    let area = egui::Rect::from_center_size(row.center(), egui::vec2(width, row.height()));

    let diagram = Diagram {
        ui,
        data,
        area,
        scale,
    };
    diagram.shell();
    diagram.pads();
    diagram.bridge();
    diagram.controls();
}
impl Diagram<'_> {
    fn at(&self, x: f32, y: f32) -> egui::Pos2 {
        self.area.min + egui::vec2(x * self.scale, y * self.scale)
    }
    fn box_at(&self, x: f32, y: f32, w: f32, h: f32) -> egui::Rect {
        egui::Rect::from_center_size(self.at(x, y), egui::vec2(w * self.scale, h * self.scale))
    }
    fn outline(&self) -> Vec<egui::Pos2> {
        let at = |x, y| self.at(x, y);
        let mut outline = Vec::new();
        // Proportions and control centers follow the front-view hardware reference:
        // https://steamdb.info/static/img/blog/106/sc_front.webp
        // The shell is about 1.4 times as wide as it is tall (excluding shoulders).
        for [a, b, c, d] in [
            [[223., 145.], [270., 112.], [380., 115.], [500., 115.]],
            [[500., 115.], [620., 115.], [730., 112.], [777., 145.]],
            [[777., 145.], [821., 186.], [856., 355.], [874., 450.]],
            [[874., 450.], [896., 585.], [861., 651.], [798., 658.]],
            [[798., 658.], [751., 665.], [747., 590.], [718., 557.]],
            [[718., 557.], [706., 539.], [685., 538.], [670., 538.]],
            [[670., 538.], [570., 536.], [430., 536.], [330., 538.]],
            [[330., 538.], [315., 538.], [294., 539.], [282., 557.]],
            [[282., 557.], [253., 590.], [249., 665.], [202., 658.]],
            [[202., 658.], [139., 651.], [104., 585.], [126., 450.]],
            [[126., 450.], [144., 355.], [179., 186.], [223., 145.]],
        ] {
            for i in 0..20 {
                let t = i as f32 / 20.0;
                let u = 1.0 - t;
                outline.push(at(
                    u * u * u * a[0]
                        + 3.0 * u * u * t * b[0]
                        + 3.0 * u * t * t * c[0]
                        + t * t * t * d[0],
                    u * u * u * a[1]
                        + 3.0 * u * u * t * b[1]
                        + 3.0 * u * t * t * c[1]
                        + t * t * t * d[1],
                ));
            }
        }
        outline
    }
    fn shell(&self) {
        let p = self.ui.painter();
        let outline = self.outline();
        let at = |x, y| self.at(x, y);
        let shell = SHELL;
        let edge = EDGE;
        // This outline is star-shaped around the bridge. A triangle fan preserves
        // its concave underside, unlike egui's convex-polygon fill.
        let mut mesh = egui::Mesh::default();
        mesh.colored_vertex(at(500.0, 280.0), shell);
        for pos in &outline {
            mesh.colored_vertex(*pos, shell);
        }
        for n in 0..outline.len() {
            mesh.add_triangle(0, (n + 1) as u32, ((n + 1) % outline.len() + 1) as u32);
        }
        p.add(egui::Shape::mesh(mesh));
        p.add(egui::Shape::closed_line(
            outline,
            egui::Stroke::new(1.2_f32, edge),
        ));
    }
    fn pads(&self) {
        let scale = self.scale;
        let p = self.ui.painter();
        p.rect_filled(
            self.box_at(500.0, 420.0, 520.0, 228.0),
            48.0 * scale,
            Color32::from_rgb(29, 33, 39),
        );
        for (n, (x, angle)) in [(352.0, 0.12_f32), (648.0, -0.12_f32)]
            .into_iter()
            .enumerate()
        {
            self.pad(
                n,
                trackpads::Geometry {
                    center: self.at(x, 410.0),
                    half: 82.0 * scale,
                    angle,
                },
            );
        }
    }
    fn pad(&self, n: usize, geometry: trackpads::Geometry) {
        let p = self.ui.painter();
        let ui = self.ui;
        let data = self.data;
        let center = geometry.center;
        p.add(egui::Shape::convex_polygon(
            self.pad_outline(geometry),
            DARK,
            egui::Stroke::new(1.0_f32, EDGE),
        ));
        let input = trackpads::feedback(ui, data, n, geometry.hover(ui));
        if let Some(pads) = data
            .state
            .control_page(&data.profile)
            .and_then(|page| page.trackpads.as_ref())
        {
            trackpads::field(p, geometry, &pads[n], input);
            trackpads::record_feedback(ui, n, &pads[n], input);
        } else if let Some([x, y]) = input.position {
            p.circle_stroke(geometry.at(x, y), 4.0, egui::Stroke::new(1.0_f32, ACCENT));
        }
        target_point(ui, &format!("controller-pad:{n}:center"), center);
        target_point(
            ui,
            &format!("controller-pad:{n}:outer"),
            geometry.at(0.92, 0.0),
        );
    }
    fn pad_outline(&self, geometry: trackpads::Geometry) -> Vec<egui::Pos2> {
        let scale = self.scale;
        let center = geometry.center;
        let angle = geometry.angle;
        let rotate = |delta: egui::Vec2| {
            center
                + egui::vec2(
                    delta.x * angle.cos() - delta.y * angle.sin(),
                    delta.x * angle.sin() + delta.y * angle.cos(),
                )
        };
        let mut pad = Vec::new();
        for (cx, cy, start) in [
            (-62.0, -62.0, 180.0_f32),
            (62.0, -62.0, 270.0),
            (62.0, 62.0, 0.0),
            (-62.0, 62.0, 90.0),
        ] {
            for i in 0..=8 {
                let a = (start + i as f32 * 90.0 / 8.0).to_radians();
                pad.push(rotate(
                    egui::vec2(cx + 20.0 * a.cos(), cy + 20.0 * a.sin()) * scale,
                ));
            }
        }
        pad
    }
    fn bridge(&self) {
        let p = self.ui.painter();
        let data = self.data;
        let scale = self.scale;
        let at = |x, y| self.at(x, y);
        let box_at = |x, y, w, h| self.box_at(x, y, w, h);
        let dark = DARK;
        let edge = EDGE;
        p.circle_filled(at(500.0, 207.0), 25.0 * scale, dark);
        p.circle_stroke(
            at(500.0, 207.0),
            25.0 * scale,
            egui::Stroke::new(1.0_f32, edge),
        );
        p.circle_filled(
            at(500.0, 160.0),
            3.0 * scale,
            if data.state.status == InputStatus::Live {
                ACCENT
            } else {
                edge
            },
        );
        p.rect_filled(box_at(500.0, 410.0, 62.0, 28.0), 12.0 * scale, dark);
        for x in [489.0, 500.0, 511.0] {
            p.circle_filled(at(x, 410.0), 2.0 * scale, edge);
        }
    }
}
