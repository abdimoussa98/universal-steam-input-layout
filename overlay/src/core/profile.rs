//! Profile identity, mode bindings, and validated profile loading.
use super::DashboardProfile;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Mode {
    #[default]
    Base,
    Steering,
    Menu,
}
impl Mode {
    pub const ALL: [Self; 3] = [Self::Base, Self::Steering, Self::Menu];
    pub fn label(self) -> &'static str {
        match self {
            Self::Base => "Base / Gyro",
            Self::Steering => "Steering",
            Self::Menu => "Menu",
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Context {
    None,
    Left,
    Right,
    Both,
}
impl Context {
    pub const ALL: [Self; 4] = [Self::None, Self::Left, Self::Right, Self::Both];
    pub fn from_held(held: [bool; 2]) -> Self {
        match held {
            [false, false] => Self::None,
            [true, false] => Self::Left,
            [false, true] => Self::Right,
            [true, true] => Self::Both,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Binding {
    Label { text: String },
    Unbound,
    Unavailable { reason: String },
    Inherit,
}
impl Binding {
    fn validate(&self, context: Context) -> Result<(), String> {
        match self {
            Self::Inherit if context == Context::None => {
                Err("Unmodified bindings cannot inherit".into())
            }
            Self::Label { text } if text.trim().is_empty() => {
                Err("Empty label; use explicit unbound".into())
            }
            Self::Unavailable { reason } if reason.trim().is_empty() => {
                Err("Unavailable binding needs a reason".into())
            }
            _ => Ok(()),
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Bindings {
    pub mode: Mode,
    pub context: Context,
    pub bindings: [Binding; 4],
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Profile {
    pub schema_version: u32,
    pub name: String,
    pub controller: String,
    pub variant: String,
    pub source_version: String,
    pub source_digest: String,
    pub modifiers: [String; 2],
    /// south, east, west, north; positional across controller brands.
    pub glyphs: [String; 4],
    pub contexts: Vec<Bindings>,
    #[serde(default)]
    pub dashboard: Option<DashboardProfile>,
}
impl Profile {
    pub fn parse(json: &str) -> Result<Self, String> {
        if json.len() > 1_048_576 {
            return Err("Profile exceeds 1 MiB".into());
        }
        let p: Self = serde_json::from_str(json).map_err(|e| e.to_string())?;
        p.validate()?;
        Ok(p)
    }
    pub fn validate(&self) -> Result<(), String> {
        if ![1, 2].contains(&self.schema_version) {
            return Err("Unsupported profile schema".into());
        }
        if self.schema_version == 2 && self.dashboard.is_none() {
            return Err("Missing dashboard profile".into());
        }
        if let Some(dashboard) = &self.dashboard {
            dashboard.validate()?;
        }
        if self.name.trim().is_empty()
            || self.controller.trim().is_empty()
            || self.source_version.trim().is_empty()
        {
            return Err("Missing profile identity".into());
        }
        if self.variant != "default" || self.modifiers != ["L1", "R1"] {
            return Err("Only default L1/R1 profiles are supported".into());
        }
        if self.source_digest.len() != 64
            || !self.source_digest.bytes().all(|b| b.is_ascii_hexdigit())
        {
            return Err("Invalid source SHA-256".into());
        }
        if self.glyphs.iter().any(|g| g.trim().is_empty()) {
            return Err("Missing button glyph".into());
        }
        self.validate_contexts()
    }
    fn validate_contexts(&self) -> Result<(), String> {
        if self.contexts.len() != 12 {
            return Err("Exactly twelve mode/context entries are required".into());
        }
        for mode in Mode::ALL {
            for context in Context::ALL {
                let rows: Vec<_> = self
                    .contexts
                    .iter()
                    .filter(|r| r.mode == mode && r.context == context)
                    .collect();
                if rows.len() != 1 {
                    return Err("Missing or duplicate mode/context".into());
                }
                for binding in &rows[0].bindings {
                    binding.validate(context)?;
                }
            }
        }
        Ok(())
    }
    pub fn digest(&self) -> String {
        format!(
            "{:x}",
            Sha256::digest(serde_json::to_vec(self).expect("serializable profile"))
        )
    }
    pub fn labels(&self, mode: Mode, context: Context) -> [String; 4] {
        std::array::from_fn(|index| self.label(mode, context, index))
    }
    fn label(&self, mode: Mode, context: Context, index: usize) -> String {
        let Some(row) = self
            .contexts
            .iter()
            .find(|r| r.mode == mode && r.context == context)
        else {
            return "Unavailable".into();
        };
        match &row.bindings[index] {
            Binding::Label { text } => text.clone(),
            Binding::Unbound => "Unbound".into(),
            Binding::Unavailable { reason } => format!("Unavailable: {reason}"),
            Binding::Inherit if context != Context::None => self.label(mode, Context::None, index),
            Binding::Inherit => "Unavailable: invalid inheritance".into(),
        }
    }
}
pub struct ProfileSlot {
    pub profile: Profile,
}
impl ProfileSlot {
    pub fn new(json: &str) -> Result<Self, String> {
        Ok(Self {
            profile: Profile::parse(json)?,
        })
    }
    pub fn reload(&mut self, json: &str) -> Result<(), String> {
        let next = Profile::parse(json)?;
        self.profile = next;
        Ok(())
    }
}
