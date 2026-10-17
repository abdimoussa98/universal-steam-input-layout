//! Platform-independent display state. This never changes Steam's state.
mod bridge;
mod companion_link;
mod gestures;
mod hotkey_api;
mod hotkeys;
mod input;
mod preferences;
mod profile;
mod state;
mod trackpads;

pub mod steam_hid;

pub use bridge::{BridgeClient, BridgeSnapshot, HostSettings, ModeCommand, validate_request};
pub use companion_link::{CompanionEndpoint, HostedViewer};
pub use gestures::{
    ControlPage, DashboardProfile, GestureMark, Gestures, Lane, Phase, Recipe, SteeringProfile,
};
pub use hotkey_api::HotkeyApi;
pub use hotkeys::Hotkeys;
pub use input::{
    Control, Device, DeviceSelection, InputChange, InputEvent, InputFrame, InputFreshness,
    InputTracker, PadContact, physical_device_identity,
};
pub use preferences::{Preferences, can_enter_hud, page_shortcut};
pub use profile::{Binding, Bindings, Context, Mode, Profile, ProfileSlot};
pub use state::{InputStatus, State, View};
pub use trackpads::{PadDoubleTap, PadRegions, PadZone, TrackpadBindings};
