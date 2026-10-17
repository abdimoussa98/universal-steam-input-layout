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
    let Some(options) = Options::parse()? else {
        return Ok(());
    };
    let Options {
        directory,
        viewer_url,
        device,
        diagnostic,
        profile,
    } = options;
    let input = SdlInput::new()?;
    let mut selection = DeviceSelection::default();
    if let Some(id) = device {
        selection.choose(id, None);
    }
    let hub = create_hub(profile);
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
    let mut host = ControllerHost {
        input,
        selection,
        diagnostic,
        previous: None,
    };
    loop {
        let mut h = hub.lock().expect("hub");
        host.poll(&mut h);
        drop(h);
        if host.input.quit_requested {
            return Ok(());
        }
        thread::sleep(Duration::from_millis(8));
    }
}

struct Options {
    directory: Option<PathBuf>,
    viewer_url: Option<String>,
    device: Option<String>,
    diagnostic: bool,
    profile: Profile,
}
impl Options {
    fn parse() -> Result<Option<Self>, String> {
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
                    return Ok(None);
                }
                _ => return Err(format!("Unknown argument: {arg}\n{USAGE}")),
            }
        }
        if directory.is_none() && viewer_url.is_none() && !diagnostic {
            return Err(USAGE.into());
        }
        Ok(Some(Self {
            directory,
            viewer_url,
            device,
            diagnostic,
            profile,
        }))
    }
}

struct ControllerHost {
    input: SdlInput,
    selection: DeviceSelection,
    diagnostic: bool,
    previous: Option<Vec<Device>>,
}
impl ControllerHost {
    fn poll(&mut self, h: &mut Hub) {
        match self.input.poll() {
            Ok(sample) => {
                self.accept_sample(h, sample);
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
    }
    fn accept_sample(&mut self, h: &mut Hub, sample: super::sdl_input::Sample) {
        let recovered = h.data.settings.error.take().is_some();
        self.selection.resolve_single(&sample.identities);
        h.data.settings.selected = self.selection.current.clone();
        let tracker = InputTracker {
            selected: self.selection.current.clone(),
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
        if self.diagnostic && self.previous.as_ref() != Some(&sample.devices) {
            println!(
                "{}",
                serde_json::to_string(&sample.devices).expect("devices")
            );
            self.previous = Some(sample.devices.clone());
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
            self.report_devices(h, &metadata, &sample.identities);
            h.data.settings.devices = metadata;
            h.changed();
        }
    }
    fn report_devices(
        &self,
        h: &Hub,
        metadata: &[Device],
        identities: &[(String, Option<String>)],
    ) {
        if metadata != h.data.settings.devices.as_slice() {
            if self.diagnostic {
                for (id, identity) in identities {
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
            if self.selection.current.is_none() && metadata.len() > 1 {
                println!("Multiple controllers: restart with --device ID from this list.");
            }
        }
    }
}

fn create_hub(profile: Profile) -> Arc<Mutex<Hub>> {
    Arc::new(Mutex::new(Hub::new(
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
            browser_connection: None,
            error: None,
        },
        std::env::temp_dir().join("keybind-overlay-macos"),
    )))
}
