use super::js_error;
use crate::BUNDLED_PROFILE;
use crate::core::{HostSettings, Preferences, Profile, State};
use crate::ui::FrameData;

pub(super) const PROFILE_KEY: &str = "keybind.profile.v1";
pub(super) const PREFERENCES_KEY: &str = "keybind.preferences.v1";

fn read(key: &str) -> Result<Option<String>, String> {
    web_sys::window()
        .ok_or("No browser window")?
        .local_storage()
        .map_err(js_error)?
        .ok_or("Browser storage unavailable")?
        .get_item(key)
        .map_err(js_error)
}

pub(super) fn write(key: &str, value: &str) -> Result<(), String> {
    web_sys::window()
        .ok_or("No browser window")?
        .local_storage()
        .map_err(js_error)?
        .ok_or("Browser storage unavailable")?
        .set_item(key, value)
        .map_err(js_error)
}

fn load<T>(
    key: &str,
    parse: impl FnOnce(&str) -> Result<T, String>,
    default: impl FnOnce() -> T,
    error: &mut Option<String>,
) -> T {
    match read(key).and_then(|json| json.map(|json| parse(&json)).transpose()) {
        Ok(Some(value)) => value,
        Ok(None) => default(),
        Err(e) => {
            *error = Some(e);
            default()
        }
    }
}

pub(super) fn load_frame_data(remote: bool) -> FrameData {
    let mut error = None;
    let profile = load(
        PROFILE_KEY,
        Profile::parse,
        || Profile::parse(BUNDLED_PROFILE).expect("bundled profile"),
        &mut error,
    );
    let preferences = load(
        PREFERENCES_KEY,
        Preferences::parse,
        Preferences::default,
        &mut error,
    );
    let settings = HostSettings {
        hotkeys: preferences.hotkeys,
        ..Default::default()
    };
    FrameData {
        state: State::default(),
        profile,
        settings,
        preferences,
        native: false,
        remote,
        recovery_available: false,
        hud: false,
        companion_url: None,
        browser_connection: None,
        error,
    }
}
