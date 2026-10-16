//! macOS runs only the physical-input host; the existing web bundle is its UI.
use super::{host::Hub, sdl_input::SdlInput, server};
use crate::{BUNDLED_PROFILE, core::*, ui::FrameData};
use std::{
    path::PathBuf,
    sync::{Arc, Mutex, atomic::AtomicBool},
    thread,
    time::Duration,
};

const USAGE: &str = "Usage: keybind-overlay --viewer-url https://YOUR_VIEWER/ [--device SDL_ID] [--profile FILE]\nOr: keybind-overlay --companion WEB_DIR [--device SDL_ID] [--profile FILE] [--diagnostic]\nOr: keybind-overlay --diagnostic\nSteam is not required. The only connected controller is selected automatically; use --device for multiple controllers.\nOpen the printed pairing link and allow local network access if the browser asks. Mode buttons and F1/F2/F3 work in the focused browser page. Ctrl+C stops the helper.";

pub fn run() -> Result<(), String> {
    let mut args = std::env::args().skip(1);
    let mut directory = None;
    let mut viewer_url = None;
    let mut device = None;
    let mut diagnostic = false;
    let mut profile = Profile::parse(BUNDLED_PROFILE)?;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--viewer-url" => {
                viewer_url = Some(args.next().ok_or("--viewer-url needs an HTTPS URL")?)
            }
            "--companion" => {
                directory = Some(PathBuf::from(
                    args.next()
                        .ok_or("--companion needs a web bundle directory")?,
                ))
            }
            "--device" => device = Some(args.next().ok_or("--device needs an SDL ID")?),
            "--profile" => {
                profile = Profile::parse(
                    &std::fs::read_to_string(args.next().ok_or("--profile needs a file")?)
                        .map_err(|e| e.to_string())?,
                )?
            }
            "--diagnostic" => diagnostic = true,
            "--help" | "-h" => {
                println!("{USAGE}");
                return Ok(());
            }
            _ => return Err(format!("Unknown argument: {arg}\n{USAGE}")),
        }
    }
    if directory.is_none() && viewer_url.is_none() && !diagnostic {
        return Err(USAGE.into());
    }
    let mut input = SdlInput::new()?;
    let mut selection = DeviceSelection::default();
    if let Some(id) = device {
        selection.choose(id, None);
    }
    let hub = Arc::new(Mutex::new(Hub::new(
        FrameData {
            state: State::default(),
            profile,
            settings: HostSettings::default(),
            preferences: Preferences::default(),
            native: true,
            remote: false,
            recovery_available: false,
            hud: false,
            companion_url: None,
            error: None,
        },
        std::env::temp_dir().join("keybind-overlay-macos"),
    )));
    if let Some(url) = viewer_url {
        server::start_hosted(
            hub.clone(),
            Arc::new(AtomicBool::new(true)),
            directory,
            &url,
        )?;
    } else if let Some(dir) = directory {
        server::start(hub.clone(), Arc::new(AtomicBool::new(true)), dir)?;
    }
    println!(
        "Reading controllers directly with SDL. Steam is not required. Ctrl+C stops the helper."
    );
    let mut previous = None;
    loop {
        let mut h = hub.lock().expect("hub");
        match input.poll() {
            Ok(sample) => {
                let recovered = h.data.settings.error.take().is_some();
                selection.resolve_single(&sample.identities);
                h.data.settings.selected = selection.current.clone();
                let tracker = InputTracker {
                    selected: selection.current.clone(),
                };
                let changed = {
                    let FrameData { state, profile, .. } = &mut h.data;
                    tracker.sample_timed(
                        state,
                        &sample.devices,
                        &sample.events,
                        sample.now_ms,
                        profile,
                    )
                };
                if diagnostic && previous.as_ref() != Some(&sample.devices) {
                    println!(
                        "{}",
                        serde_json::to_string(&sample.devices).expect("devices")
                    );
                    previous = Some(sample.devices.clone());
                }
                let metadata: Vec<_> = sample
                    .devices
                    .into_iter()
                    .map(|mut d| {
                        d.held = [false; 2];
                        d.input = InputFrame::default();
                        d
                    })
                    .collect();
                if changed || recovered || metadata != h.data.settings.devices {
                    if metadata != h.data.settings.devices {
                        if diagnostic {
                            for (id, identity) in &sample.identities {
                                println!(
                                    "Controller {id} reconnect identity: {}",
                                    identity
                                        .as_deref()
                                        .and_then(|s| s.split(':').next())
                                        .unwrap_or("unavailable")
                                );
                            }
                        }
                        println!(
                            "Controllers: {}",
                            serde_json::to_string(&metadata).expect("devices")
                        );
                        if selection.current.is_none() && metadata.len() > 1 {
                            println!(
                                "Multiple controllers: restart with --device ID from this list."
                            );
                        }
                    }
                    h.data.settings.devices = metadata;
                    h.changed();
                }
            }
            Err(error) => {
                if h.data.settings.error.as_ref() != Some(&error) {
                    eprintln!("{error}");
                    h.data.settings.error = Some(error);
                    h.data.state.unavailable(InputStatus::Unavailable);
                    h.changed();
                }
            }
        }
        drop(h);
        if input.quit_requested {
            return Ok(());
        }
        thread::sleep(Duration::from_millis(8));
    }
}
