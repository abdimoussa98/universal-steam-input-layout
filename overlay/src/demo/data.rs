use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::Arc,
};

pub(crate) type Settings = BTreeMap<String, String>;
pub type Catalog = Vec<Arc<Layout>>;

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Layout {
    pub schema: u8,
    pub controller: String,
    pub variant: String,
    pub version: String,
    pub tag: String,
    pub sha256: String,
    pub(crate) layers: Vec<Layer>,
    pub(crate) groups: Vec<Group>,
    pub coverage: Vec<serde_json::Value>,
}
impl Layout {
    pub fn catalog() -> Result<Catalog, String> {
        let layouts: Vec<Self> =
            serde_json::from_str(include_str!("../../profiles/demo-layouts.json"))
                .map_err(|error| error.to_string())?;
        if layouts.iter().any(|l| l.schema != 1 || l.layers.is_empty()) {
            return Err("Unsupported executable layout schema".into());
        }
        Ok(layouts.into_iter().map(Arc::new).collect())
    }
    pub fn label(&self) -> String {
        format!("{} {} · {}", self.controller, self.version, self.variant)
    }
    pub fn controls(&self) -> BTreeSet<String> {
        self.layers
            .iter()
            .flat_map(|l| l.sources.iter())
            .flat_map(|(source, gid)| {
                self.groups[*gid]
                    .inputs
                    .keys()
                    .map(move |name| format!("{source}/{name}"))
            })
            .collect()
    }
}
#[derive(Clone, Deserialize, Serialize)]
pub(crate) struct Layer {
    pub title: String,
    pub sources: BTreeMap<String, usize>,
}
#[derive(Clone, Deserialize, Serialize)]
pub(crate) struct Group {
    pub id: String,
    pub mode: String,
    pub settings: Settings,
    pub condition: Option<Condition>,
    pub inputs: BTreeMap<String, Vec<Entry>>,
}
#[derive(Clone, Deserialize, Serialize)]
pub(crate) struct Entry {
    pub kind: String,
    pub settings: Settings,
    pub condition: Option<Condition>,
    pub commands: Vec<Operation>,
}
impl Entry {
    pub fn value(&self, name: &str) -> u64 {
        number(&self.settings, name, 0.) as u64
    }
    pub fn flag(&self, name: &str) -> bool {
        self.value(name) == 1
    }
    pub fn interruptible(&self) -> bool {
        self.settings.get("interruptable").is_none_or(|v| v != "0")
    }
    pub fn repeat(&self) -> Option<u64> {
        self.flag("hold_repeats")
            .then(|| self.value("repeat_rate"))
            .map(|rate| if rate == 0 { 100 } else { rate })
    }
}
#[derive(Clone, Deserialize, Serialize)]
pub(crate) struct Condition {
    pub all: bool,
    pub groups: Vec<Vec<String>>,
}
impl Condition {
    pub fn satisfied(&self, held: &BTreeSet<String>) -> bool {
        let mut hits = self
            .groups
            .iter()
            .map(|g| g.iter().any(|c| held.contains(c)));
        if self.all {
            hits.all(|v| v)
        } else {
            hits.any(|v| v)
        }
    }
    pub fn contains(&self, control: &str) -> bool {
        self.groups.iter().flatten().any(|c| c == control)
    }
    pub fn any_held(&self, held: &BTreeSet<String>) -> bool {
        self.groups.iter().flatten().any(|c| held.contains(c))
    }
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
pub(crate) enum Operation {
    AddLayer { target: usize, beep: bool },
    RemoveLayer { target: usize, beep: bool },
    HoldLayer { target: usize, beep: bool },
    Empty,
    KeyPress { value: String },
    MouseButton { value: String },
    XinputButton { value: String },
    MouseWheel { value: String },
    ModeShift { source: String, target: usize },
}
impl Operation {
    pub fn output(&self) -> Option<String> {
        match self {
            Self::KeyPress { value } => Some(value.clone()),
            Self::MouseButton { value } => Some(format!("mouse_button {value}")),
            Self::XinputButton { value } => Some(format!("xinput_button {value}")),
            _ => None,
        }
    }
}
pub(crate) fn number(settings: &Settings, name: &str, fallback: f64) -> f64 {
    settings
        .get(name)
        .and_then(|s| s.parse().ok())
        .unwrap_or(fallback)
}
