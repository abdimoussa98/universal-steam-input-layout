//! Companion protocol snapshots and validated client state.
use super::{Device, InputStatus, Mode, Preferences, Profile, State};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct HostSettings {
    pub selected: Option<String>,
    pub hotkeys: [u8; 3],
    pub devices: Vec<Device>,
    pub error: Option<String>,
}
impl Default for HostSettings {
    fn default() -> Self {
        Self {
            selected: None,
            hotkeys: [1, 2, 3],
            devices: vec![],
            error: None,
        }
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BridgeSnapshot {
    pub version: u32,
    pub session: String,
    pub sequence: u64,
    pub state: State,
    pub profile_digest: String,
    pub profile: Option<Profile>,
    pub settings: HostSettings,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModeCommand {
    pub mode: Mode,
}
pub struct BridgeClient {
    pub session: String,
    pub sequence: Option<u64>,
    pub state: State,
    pub profile: Option<Profile>,
    pub settings: HostSettings,
}
impl BridgeClient {
    pub fn new(session: String) -> Self {
        Self {
            session,
            sequence: None,
            state: State::default(),
            profile: None,
            settings: HostSettings::default(),
        }
    }
    pub fn accept(&mut self, next: BridgeSnapshot) -> Result<bool, String> {
        if next.version != 1 || next.session != self.session {
            return Err("Companion protocol/session mismatch; reopen its link".into());
        }
        if self.sequence.is_some_and(|s| next.sequence <= s) {
            return Ok(false);
        }
        let p = next
            .profile
            .as_ref()
            .or(self.profile.as_ref())
            .ok_or("Companion did not supply a profile")?;
        p.validate()?;
        if p.digest() != next.profile_digest {
            return Err("Companion profile mismatch".into());
        }
        Preferences {
            hotkeys: next.settings.hotkeys,
            ..Preferences::default()
        }
        .validate()?;
        self.profile = Some(p.clone());
        self.state = next.state;
        self.settings = next.settings;
        self.sequence = Some(next.sequence);
        Ok(true)
    }
    pub fn disconnect(&mut self) {
        self.state.unavailable(InputStatus::Unavailable);
        self.sequence = None;
    }
}
pub fn validate_request(
    host: &str,
    origin: Option<&str>,
    token: &str,
    expected_host: &str,
    session: &str,
) -> bool {
    host == expected_host
        && token == session
        && !session.is_empty()
        && origin.is_none_or(|o| o == format!("http://{expected_host}"))
}
