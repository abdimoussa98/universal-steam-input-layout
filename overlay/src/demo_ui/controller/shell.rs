use super::*;
impl Diagram<'_> {
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
    pub(super) fn shell(&self) {
        let p = self.ui.painter();
        if self.app.session.engine.layout.controller == "neptune" {
            p.rect(
                self.box_at(500., 370., 900., 500.),
                45. * self.scale,
                SHELL,
                Stroke::new(1.0_f32, EDGE),
                egui::StrokeKind::Inside,
            );
            p.rect(
                self.box_at(500., 355., 270., 360.),
                12. * self.scale,
                DARK,
                Stroke::new(1.0_f32, EDGE),
                egui::StrokeKind::Inside,
            );
            return;
        }
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
}
