//! Headless fake-input host for end-to-end browser tests. Never reads hardware.
use keybind_overlay::{
    BUNDLED_PROFILE,
    core::*,
    platform::{host::Hub, server},
    ui::FrameData,
};
use std::{
    io::BufRead,
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
};

fn main() {
    let directory = PathBuf::from(std::env::args().nth(1).expect("web bundle directory"));
    let mut state = State::default();
    let profile = Profile::parse(BUNDLED_PROFILE).unwrap();
    let mut input = InputFrame::default();
    input.buttons[Control::L1 as usize] = true;
    state.sample_input("fixture", input, &profile, 0);
    let hub = Arc::new(Mutex::new(Hub::new(
        FrameData {
            state,
            profile,
            settings: HostSettings {
                selected: Some("fixture".into()),
                hotkeys: [5, 6, 7],
                devices: vec![Device {
                    input: InputFrame::default(),
                    id: "fixture".into(),
                    name: "Fake native controller".into(),
                    standard: true,
                    held: [false, false],
                }],
                error: None,
            },
            preferences: Preferences::default(),
            native: true,
            remote: false,
            recovery_available: true,
            hud: false,
            companion_url: None,
            error: None,
        },
        std::env::temp_dir().join("keybind-fixture-settings"),
    )));
    let running = Arc::new(AtomicBool::new(true));
    if let Some(url) = std::env::args().nth(2) {
        server::start_hosted(hub.clone(), running.clone(), None, &url).unwrap();
    } else {
        server::start(hub.clone(), running.clone(), directory).unwrap();
    }
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        if line == "quit" {
            break;
        }
        let command: serde_json::Value = serde_json::from_str(&line).expect("fixture command JSON");
        let mut h = hub.lock().unwrap();
        if let Some(mode) = command.get("mode") {
            h.data
                .state
                .select_mode(serde_json::from_value(mode.clone()).unwrap());
        }
        if let Some(held) = command.get("held") {
            let held: [bool; 2] = serde_json::from_value(held.clone()).unwrap();
            let mut input = h.data.state.input.clone();
            input.buttons[Control::L1 as usize] = held[0];
            input.buttons[Control::R1 as usize] = held[1];
            let FrameData { state, profile, .. } = &mut h.data;
            state.sample_input("fixture", input, profile, state.gestures.clock_ms + 1);
        }
        if let Some(input) = command.get("input") {
            let FrameData { state, profile, .. } = &mut h.data;
            state.sample_input(
                "fixture",
                serde_json::from_value(input.clone()).unwrap(),
                profile,
                command
                    .get("at_ms")
                    .and_then(|v| v.as_u64())
                    .expect("input requires monotonic fixture time"),
            );
        }
        if let Some(keys) = command.get("hotkeys") {
            h.data.settings.hotkeys = serde_json::from_value(keys.clone()).unwrap();
        }
        h.changed();
    }
    running.store(false, Ordering::Release);
}
