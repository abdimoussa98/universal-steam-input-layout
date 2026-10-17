//! Timed gesture phases and the state recorded for each owner.
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Phase {
    #[default]
    Idle,
    Pressed,
    Window,
    Second,
    Hold,
    Cover,
    Consumed,
    Output,
    Combined,
    CombinedCover,
    Unknown,
    Interrupted,
}
impl Phase {
    pub fn label(self) -> &'static str {
        match self {
            Self::Idle => "Ready",
            Self::Pressed => "Release for tap",
            Self::Window => "Release window open",
            Self::Second => "Second hold in progress",
            Self::Hold => "Hold action active",
            Self::Cover => "Second hold active",
            Self::Consumed => "Tap Cover · gesture used",
            Self::Output => "Output in another gesture",
            Self::Combined => "Combined modifiers",
            Self::CombinedCover => "Combined Tap Cover",
            Self::Unknown => "Held before tracking · release to reset",
            Self::Interrupted => "Timing interrupted",
        }
    }
    pub fn page(self) -> Option<&'static str> {
        match self {
            Self::Pressed => Some("pressed"),
            Self::Window => Some("window"),
            Self::Second => Some("second"),
            Self::Hold => Some("hold"),
            Self::Cover => Some("cover"),
            Self::Consumed => Some("consumed"),
            _ => None,
        }
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Lane {
    pub phase: Phase,
    #[serde(default)]
    pub inherited_phase: Option<Phase>,
    pub started_ms: u64,
    pub deadline_ms: Option<u64>,
    pub output_at_ms: Option<u64>,
    pub output_seen: bool,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct GestureMark {
    pub lane: usize,
    pub at_ms: u64,
    pub label: String,
}
