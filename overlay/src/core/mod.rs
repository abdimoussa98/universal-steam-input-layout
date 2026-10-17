//! Platform-independent display state. This never changes Steam's state.
mod gestures;
pub use gestures::*;
mod trackpads;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
pub use trackpads::*;

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
                for b in &rows[0].bindings {
                    match b {
                        Binding::Inherit if context == Context::None => {
                            return Err("Unmodified bindings cannot inherit".into());
                        }
                        Binding::Label { text } if text.trim().is_empty() => {
                            return Err("Empty label; use explicit unbound".into());
                        }
                        Binding::Unavailable { reason } if reason.trim().is_empty() => {
                            return Err("Unavailable binding needs a reason".into());
                        }
                        _ => {}
                    }
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
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InputStatus {
    #[default]
    SelectDevice,
    Live,
    Disconnected,
    Paused,
    UnsupportedMapping,
    Unavailable,
}
impl InputStatus {
    pub fn label(&self) -> &'static str {
        match self {
            Self::SelectDevice => "Select a controller · press a button if it is missing",
            Self::Live => "Live",
            Self::Disconnected => "Controller disconnected · select it again after reconnecting",
            Self::Paused => "Input paused · waiting for a fresh snapshot",
            Self::UnsupportedMapping => "Unsupported controller mapping",
            Self::Unavailable => "Input unavailable",
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct State {
    pub mode: Mode,
    pub held: [bool; 2],
    pub status: InputStatus,
    pub device: Option<String>,
    #[serde(default)]
    pub input: InputFrame,
    #[serde(default)]
    pub gestures: Gestures,
    /// Viewer-only time stretch; Steam and the exported profile stay unchanged.
    #[serde(default = "normal_timing")]
    pub timing_scale: u8,
}
fn normal_timing() -> u8 {
    1
}
impl Default for State {
    fn default() -> Self {
        Self {
            mode: Mode::default(),
            held: [false; 2],
            status: InputStatus::default(),
            device: None,
            input: InputFrame::default(),
            gestures: Gestures::default(),
            timing_scale: 1,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct View {
    pub mode: Mode,
    pub held: [bool; 2],
    pub labels: [String; 4],
    pub status: InputStatus,
}
impl State {
    pub fn timing_scale(&self) -> u8 {
        self.timing_scale.clamp(1, 10)
    }
    pub fn set_timing_scale(&mut self, scale: u8) {
        let scale = scale.clamp(1, 10);
        if self.timing_scale != scale {
            self.timing_scale = scale;
            // A speed change cannot finish a gesture or turn a held button into
            // a fresh press. The next sample requires release before tracking.
            self.gestures = Gestures::default();
        }
    }
    pub fn select_mode(&mut self, mode: Mode) -> bool {
        let changed = self.mode != mode;
        if changed {
            self.gestures = Gestures::default();
        }
        self.mode = mode;
        changed
    }
    pub fn modifier(&mut self, index: usize, held: bool) -> bool {
        if index >= 2 || self.status != InputStatus::Live {
            return false;
        }
        let changed = self.held[index] != held;
        self.held[index] = held;
        changed
    }
    pub fn snapshot(&mut self, id: &str, held: [bool; 2]) {
        self.device = Some(id.into());
        self.held = held;
        self.status = InputStatus::Live;
    }
    pub fn unavailable(&mut self, status: InputStatus) {
        self.held = [false; 2];
        self.input = InputFrame::default();
        self.gestures = Gestures::default();
        self.device = None;
        self.status = status;
    }
    pub fn view(&self, p: &Profile) -> View {
        View {
            mode: self.mode,
            held: self.held,
            labels: p.labels(self.mode, Context::from_held(self.held)),
            status: self.status.clone(),
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Device {
    #[serde(default)]
    pub input: InputFrame,
    pub id: String,
    pub name: String,
    pub standard: bool,
    pub held: [bool; 2],
}
#[derive(Default)]
pub struct InputTracker {
    pub selected: Option<String>,
}
impl InputTracker {
    pub fn select(&mut self, id: Option<String>) {
        self.selected = id;
    }
    /// Full snapshots avoid stale queued button events and seed already-held buttons.
    pub fn sample(&self, state: &mut State, devices: &[Device], paused: bool) -> bool {
        let old = state.clone();
        if paused {
            state.unavailable(InputStatus::Paused);
        } else if let Some(id) = &self.selected {
            match devices.iter().find(|d| &d.id == id) {
                Some(d) if d.standard => state.snapshot(id, d.held),
                Some(_) => state.unavailable(InputStatus::UnsupportedMapping),
                None => state.unavailable(InputStatus::Disconnected),
            }
        } else {
            state.unavailable(InputStatus::SelectDevice);
        }
        *state != old
    }
}

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

pub mod steam_hid;

mod companion_link;
pub use companion_link::{CompanionEndpoint, HostedViewer};

pub trait HotkeyApi {
    fn register(&mut self, id: i32, key: u8) -> Result<(), String>;
    fn unregister(&mut self, id: i32);
}
pub struct Hotkeys<A: HotkeyApi> {
    api: A,
    registered: Vec<i32>,
}
impl<A: HotkeyApi> Hotkeys<A> {
    pub fn new(api: A) -> Self {
        Self {
            api,
            registered: vec![],
        }
    }
    pub fn rebind(&mut self, keys: [u8; 3]) -> Vec<String> {
        for id in self.registered.drain(..) {
            self.api.unregister(id);
        }
        let mut errors = vec![];
        for (i, key) in keys.into_iter().enumerate() {
            let id = i as i32 + 1;
            match self.api.register(id, key) {
                Ok(()) => self.registered.push(id),
                Err(e) => errors.push(format!("F{key}: {e}")),
            }
        }
        errors
    }
}
impl<A: HotkeyApi> Drop for Hotkeys<A> {
    fn drop(&mut self) {
        for id in self.registered.drain(..) {
            self.api.unregister(id);
        }
    }
}

#[derive(Default)]
pub struct InputFreshness {
    last: Option<f64>,
}
impl InputFreshness {
    pub fn received(&mut self, milliseconds: f64) {
        self.last = Some(milliseconds);
    }
    pub fn expired(&self, milliseconds: f64) -> bool {
        self.last.is_none_or(|last| milliseconds - last > 3000.0)
    }
}

/// Prefer a device's hardware serial: macOS HID paths change on reconnect.
/// Hash the serial so diagnostic identities do not disclose it.
pub fn physical_device_identity(
    vendor: Option<u16>,
    product: Option<u16>,
    serial: Option<&str>,
    path: Option<&str>,
) -> Option<String> {
    if let (Some(vendor), Some(product), Some(serial)) = (
        vendor,
        product,
        serial.map(str::trim).filter(|s| !s.is_empty()),
    ) {
        return Some(format!(
            "serial:{vendor:04x}:{product:04x}:{:x}",
            Sha256::digest(serial.as_bytes())
        ));
    }
    path.filter(|p| !p.is_empty()).map(|p| format!("path:{p}"))
}

/// SDL instance IDs change on reconnect; only a unique physical identity can
/// restore a previous selection automatically. Device names are not identities.
#[derive(Default)]
pub struct DeviceSelection {
    pub current: Option<String>,
    path: Option<String>,
}
impl DeviceSelection {
    /// A headless host can choose the only device initially. Once chosen,
    /// reconnect must still match its physical identity, never a different pad.
    pub fn resolve_single(&mut self, devices: &[(String, Option<String>)]) -> Option<String> {
        if self.current.is_none() && devices.len() == 1 {
            self.choose(devices[0].0.clone(), devices[0].1.clone());
        }
        self.resolve(devices)
    }
    pub fn choose(&mut self, id: String, path: Option<String>) {
        self.current = Some(id);
        self.path = path.filter(|p| !p.is_empty());
    }
    pub fn resolve(&mut self, devices: &[(String, Option<String>)]) -> Option<String> {
        let current = self.current.as_ref()?;
        if let Some((id, path)) = devices.iter().find(|(id, _)| id == current) {
            if let Some(path) = path.as_ref().filter(|p| !p.is_empty()) {
                self.path = Some(path.clone());
            }
            return Some(id.clone());
        }
        let path = self.path.as_ref()?;
        let matches: Vec<_> = devices
            .iter()
            .filter(|(_, p)| p.as_ref() == Some(path))
            .collect();
        if matches.len() != 1 {
            return None;
        }
        let id = matches[0].0.clone();
        self.current = Some(id.clone());
        Some(id)
    }
}
