#![cfg(feature = "ui")]
use keybind_overlay::{BUNDLED_PROFILE, core::*, ui::FrameData};

#[test]
fn browser_distinguishes_missing_devices_from_selection_and_input_errors() {
    let mut data = FrameData {
        state: State::default(),
        profile: Profile::parse(BUNDLED_PROFILE).unwrap(),
        settings: HostSettings::default(),
        preferences: Preferences::default(),
        native: false,
        remote: false,
        recovery_available: false,
        hud: false,
        companion_url: None,
        browser_connection: None,
        error: None,
    };
    assert_eq!(
        data.input_status_label(),
        "No controllers exposed by this browser"
    );
    assert!(data.controller_help().is_some());
    data.settings.devices.push(Device {
        input: InputFrame::default(),
        id: "1".into(),
        name: "Controller".into(),
        standard: true,
        held: [false; 2],
    });
    assert_eq!(data.input_status_label(), InputStatus::SelectDevice.label());
    assert!(data.controller_help().is_none());
    data.state.snapshot("1", [false; 2]);
    data.remote = true;
    assert_eq!(data.input_status_label(), "Live · Controller · via helper");
    data.remote = false;
    assert_eq!(data.input_status_label(), "Live · Controller");
    data.settings.devices[0].name = "Controller · Unknown · usb:path".into();
    assert_eq!(data.input_status_label(), "Live · Controller");
    data.settings.devices.clear();
    for status in [
        InputStatus::Unavailable,
        InputStatus::Paused,
        InputStatus::Disconnected,
    ] {
        data.state.status = status;
        assert_eq!(data.input_status_label(), data.state.status.label());
        assert!(data.controller_help().is_none());
    }
    data.state.status = InputStatus::SelectDevice;
    data.remote = true;
    assert_eq!(data.input_status_label(), InputStatus::SelectDevice.label());
    assert!(data.controller_help().is_none());
    data.remote = false;
    data.native = true;
    assert_eq!(data.input_status_label(), InputStatus::SelectDevice.label());
    assert!(data.controller_help().is_none());
}

#[test]
fn companion_settings_display_host_shortcuts_and_keep_local_appearance() {
    let mut data = FrameData {
        state: State::default(),
        profile: Profile::parse(BUNDLED_PROFILE).unwrap(),
        settings: HostSettings {
            hotkeys: [5, 6, 7],
            ..Default::default()
        },
        preferences: Preferences {
            scale: 1.5,
            ..Default::default()
        },
        native: false,
        remote: true,
        recovery_available: false,
        hud: false,
        companion_url: None,
        browser_connection: None,
        error: None,
    };
    assert_eq!(data.display_preferences().hotkeys, [5, 6, 7]);
    assert_eq!(data.display_preferences().scale, 1.5);
    data.settings.hotkeys = [8, 9, 10];
    assert_eq!(data.display_preferences().hotkeys, [8, 9, 10]);
    data.remote = false;
    assert_eq!(data.display_preferences().hotkeys, [1, 2, 3]);
}
