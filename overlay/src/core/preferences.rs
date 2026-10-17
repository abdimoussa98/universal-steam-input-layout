//! User preferences and local mode shortcuts.
use super::Mode;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Preferences {
    pub schema_version: u32,
    pub hotkeys: [u8; 3],
    pub opacity: f32,
    pub scale: f32,
}
impl Default for Preferences {
    fn default() -> Self {
        Self {
            schema_version: 1,
            hotkeys: [1, 2, 3],
            opacity: 0.92,
            scale: 1.0,
        }
    }
}
impl Preferences {
    pub fn parse(json: &str) -> Result<Self, String> {
        let p: Self = serde_json::from_str(json).map_err(|e| e.to_string())?;
        p.validate()?;
        Ok(p)
    }
    pub fn validate(&self) -> Result<(), String> {
        if self.schema_version != 1
            || !(0.25..=1.0).contains(&self.opacity)
            || !(0.75..=2.0).contains(&self.scale)
        {
            return Err("Invalid preferences version, opacity or scale".into());
        }
        if self.hotkeys.iter().any(|k| !(1..=12).contains(k))
            || self.hotkeys[0] == self.hotkeys[1]
            || self.hotkeys[0] == self.hotkeys[2]
            || self.hotkeys[1] == self.hotkeys[2]
        {
            return Err("Choose three different keys from F1–F12".into());
        }
        Ok(())
    }
}
pub fn page_shortcut(keys: &[u8; 3], key: u8, repeat: bool, text_entry: bool) -> Option<Mode> {
    if repeat || text_entry {
        None
    } else {
        keys.iter().position(|k| *k == key).map(|i| Mode::ALL[i])
    }
}
pub fn can_enter_hud(recovery_shortcut_registered: bool) -> bool {
    recovery_shortcut_registered
}
