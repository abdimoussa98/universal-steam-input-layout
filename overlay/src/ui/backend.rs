use crate::core::*;

#[derive(Clone)]
pub struct FrameData {
    pub state: State,
    pub profile: Profile,
    pub settings: HostSettings,
    pub preferences: Preferences,
    pub native: bool,
    pub remote: bool,
    pub recovery_available: bool,
    pub hud: bool,
    pub companion_url: Option<String>,
    pub browser_connection: Option<BrowserConnection>,
    pub error: Option<String>,
}
#[derive(Clone, serde::Serialize)]
pub struct BrowserConnection {
    pub available: bool,
    pub busy: bool,
    pub connected: bool,
    pub message: String,
}
impl FrameData {
    fn browser_has_no_devices(&self) -> bool {
        !self.native
            && !self.remote
            && self.state.status == InputStatus::SelectDevice
            && self.settings.devices.is_empty()
    }
    pub fn input_status_label(&self) -> String {
        if self.state.device.as_deref() == Some("viewer-mouse") {
            "Mouse preview · right-click a button to hold or release it".into()
        } else if self.browser_has_no_devices() {
            if self
                .browser_connection
                .as_ref()
                .is_some_and(|c| c.available)
            {
                "Connect a controller to begin".into()
            } else {
                "No controllers exposed by this browser".into()
            }
        } else if self.state.status == InputStatus::Live
            && let Some(device) = self
                .settings
                .devices
                .iter()
                .find(|d| self.state.device.as_deref() == Some(d.id.as_str()))
        {
            format!(
                "Live · {}{}",
                // Native names append diagnostic type/path fields; keep those
                // in Settings and show the friendly name in the main status.
                device.name.split(" · ").next().unwrap_or(&device.name),
                if self.remote { " · via helper" } else { "" }
            )
        } else {
            self.state.status.label().into()
        }
    }
    pub fn controller_help(&self) -> Option<&'static str> {
        self.browser_has_no_devices().then_some("For a Steam Controller 2 or Steam Deck, click Connect controller and choose it in the browser picker. On the Deck, use a WebHID browser in Desktop Mode; the built-in controller may be named Steam Controller. Other supported gamepads appear after pressing a controller button.")
    }
    pub fn display_preferences(&self) -> Preferences {
        let mut preferences = self.preferences.clone();
        if self.remote {
            preferences.hotkeys = self.settings.hotkeys;
        }
        preferences
    }
}
pub enum Command {
    TimingScale(u8),
    DownloadLayouts,
    ConnectController,
    DisconnectController,
    Mode(Mode),
    Select(Option<String>),
    Profile(String),
    Preferences(Preferences),
    Hud(bool),
    Hide,
    ImportPath(std::path::PathBuf),
}
pub trait Backend {
    fn data(&self) -> FrameData;
    fn command(&mut self, command: Command);
    /// Preserve device edges that arrive between rendered frames.
    fn input_samples(&mut self) -> Vec<(String, f64, InputFrame)> {
        vec![]
    }
    fn input_blocked(&self) -> bool {
        false
    }
    fn input_epoch(&self) -> u64 {
        0
    }
}
