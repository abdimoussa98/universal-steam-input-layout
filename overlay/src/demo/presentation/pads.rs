use super::{Engine, Layout, Operation, outputs};
use crate::demo::data::Group;

pub(crate) struct PadView {
    pub mode: String,
    pub center: String,
    pub directions: [String; 4],
    pub inner: f32,
    pub outer: f32,
    pub circular: bool,
}
impl Layout {
    fn pad_groups<'a>(&'a self, source: &str, group: &'a Group, depth: usize) -> Vec<&'a Group> {
        let mut groups = vec![group];
        if depth == 0 {
            return groups;
        }
        for op in group.inputs.values().flatten().flat_map(|e| &e.commands) {
            if let Operation::AddLayer { target, .. } | Operation::HoldLayer { target, .. } = op
                && let Some(gid) = self.layers[*target].sources.get(source)
            {
                groups.extend(self.pad_groups(source, &self.groups[*gid], depth - 1));
            }
        }
        groups
    }
}
impl Engine {
    pub(crate) fn pad_view(&self, source: &str, click: bool) -> PadView {
        let (mode, _, _) = self.effective(source);
        let binding = self.binding(&format!("{source}/click")).0;
        let group = binding.map(|(_, gid)| &self.layout.groups[gid]);
        let groups = group
            .map(|g| self.layout.pad_groups(source, g, 3))
            .unwrap_or_default();
        let circular = groups.iter().any(|g| g.mode == "scrollwheel");
        let directions = ["dpad_north", "dpad_east", "dpad_south", "dpad_west"].map(|name| {
            if click {
                groups
                    .iter()
                    .filter(|g| g.mode == "dpad")
                    .filter_map(|g| g.inputs.get(name))
                    .map(|es| self.layout.entry_label(es, 2))
                    .find(|s| !s.is_empty())
                    .unwrap_or_else(|| "—".into())
            } else {
                self.display_label(&format!("{source}/{name}"))
            }
        });
        let center = if click {
            groups
                .iter()
                .filter_map(|g| g.inputs.get("click"))
                .map(|es| outputs(es))
                .find(|s| !s.is_empty())
                .unwrap_or_else(|| self.display_label(&format!("{source}/click")))
        } else {
            match mode.as_str() {
                "absolute_mouse" => "Pointer",
                "scrollwheel" => "Scroll",
                "2dscroll" => "Swipe",
                "disabled" => "Off",
                _ => "Touch",
            }
            .into()
        };
        let (outer, inner) = self.soft_ranges(source);
        PadView {
            mode,
            center,
            directions,
            inner: (inner.unwrap_or(23000.) / 32767.) as f32,
            outer: (outer.unwrap_or(23000.) / 32767.) as f32,
            circular,
        }
    }
}
