//! SDL and thread hotkeys stay on the process main thread. Eframe owns a
//! separate Windows event loop; state changes wake it, idle samples do not.
use crate::{BUNDLED_PROFILE, core::*, ui::*};
use eframe::egui;
use std::{
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    thread,
    time::Duration,
};
use windows::Win32::UI::{Input::KeyboardAndMouse::*, WindowsAndMessaging::*};
use winit::platform::windows::EventLoopBuilderExtWindows;

use super::host::Hub;

struct NativeBackend(Arc<Mutex<Hub>>);
impl Backend for NativeBackend {
    fn data(&self) -> FrameData {
        self.0.lock().expect("hub").data.clone()
    }
    fn command(&mut self, command: Command) {
        let mut h = self.0.lock().expect("hub");
        match command {
            Command::Mode(mode) => {
                h.data.state.select_mode(mode);
            }
            Command::Select(id) => {
                h.data.settings.selected = id;
                h.data.state.unavailable(InputStatus::SelectDevice);
            }
            Command::Profile(json) => h.import(json),
            Command::ImportPath(path) => match std::fs::read_to_string(path) {
                Ok(json) => h.import(json),
                Err(e) => h.data.error = Some(e.to_string()),
            },
            Command::Preferences(p) => match p.validate() {
                Ok(()) => {
                    h.data.preferences = p.clone();
                    h.data.settings.hotkeys = p.hotkeys;
                    h.data.error = h
                        .persist(
                            "preferences.json",
                            &serde_json::to_string(&p).expect("preferences"),
                        )
                        .err();
                }
                Err(e) => h.data.error = Some(e),
            },
            Command::Hud(hud) => h.window(hud, false),
            Command::Hide => h.window(false, true),
        }
        h.changed();
    }
}
struct WinHotkeys;
impl HotkeyApi for WinHotkeys {
    fn register(&mut self, id: i32, key: u8) -> Result<(), String> {
        // Thread-scoped registration; this object is used and dropped on main.
        unsafe {
            RegisterHotKey(
                None,
                id,
                MOD_NOREPEAT,
                u32::from(VK_F1.0) + u32::from(key) - 1,
            )
        }
        .map_err(|e| e.to_string())
    }
    fn unregister(&mut self, id: i32) {
        let _ = unsafe { UnregisterHotKey(None, id) };
    }
}
struct RecoveryHotkey(bool);
impl RecoveryHotkey {
    fn new() -> Self {
        Self(
            unsafe {
                RegisterHotKey(
                    None,
                    100,
                    MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
                    u32::from(b'O'),
                )
            }
            .is_ok(),
        )
    }
}
impl Drop for RecoveryHotkey {
    fn drop(&mut self) {
        if self.0 {
            let _ = unsafe { UnregisterHotKey(None, 100) };
        }
    }
}

#[derive(Default)]
struct Options {
    diagnostic: bool,
    companion: Option<PathBuf>,
    profile: Option<PathBuf>,
    device: Option<String>,
}
impl Options {
    fn parse() -> Result<Self, String> {
        let mut opts = Self::default();
        let mut args = std::env::args().skip(1);
        while let Some(arg) = args.next() {
            match arg.as_str() {
            "--diagnostic"=>opts.diagnostic=true,
            "--companion"=>opts.companion=Some(args.next().ok_or("--companion needs the web bundle directory")?.into()),
            "--profile"=>opts.profile=Some(args.next().ok_or("--profile needs a JSON path")?.into()),
            "--device"=>opts.device=Some(args.next().ok_or("--device needs an SDL instance ID")?),
            "--help"|"-h"=>return Err("Usage: keybind-overlay [--profile FILE] [--companion WEB_DIR] [--diagnostic] [--device SDL_ID]\nF1/F2/F3 select display modes. Ctrl+Alt+O recovers the interactive window.".into()),
            _=>return Err(format!("Unknown argument: {arg}")),
        }
        }
        Ok(opts)
    }
}
pub fn run() -> Result<(), String> {
    let opts = Options::parse()?;
    let settings_dir = std::env::var_os("APPDATA")
        .map(PathBuf::from)
        .ok_or("APPDATA is unavailable")?
        .join("KeybindOverlay");
    let mut error = None;
    let preferences = match std::fs::read_to_string(settings_dir.join("preferences.json")) {
        Ok(json) => Preferences::parse(&json).unwrap_or_else(|e| {
            error = Some(e);
            Preferences::default()
        }),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Preferences::default(),
        Err(e) => {
            error = Some(e.to_string());
            Preferences::default()
        }
    };
    let profile_path = opts
        .profile
        .unwrap_or_else(|| settings_dir.join("profile.json"));
    let profile = match std::fs::read_to_string(&profile_path) {
        Ok(json) => Profile::parse(&json).unwrap_or_else(|e| {
            error = Some(format!(
                "{}: {e}; using bundled profile",
                profile_path.display()
            ));
            Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
        }),
        Err(e)
            if e.kind() == std::io::ErrorKind::NotFound
                && profile_path == settings_dir.join("profile.json") =>
        {
            Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
        }
        Err(e) => {
            error = Some(format!(
                "{}: {e}; using bundled profile",
                profile_path.display()
            ));
            Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
        }
    };
    let recovery = RecoveryHotkey::new();
    let mut keys = Hotkeys::new(WinHotkeys);
    let mut registered = preferences.hotkeys;
    let conflicts = keys.rebind(registered);
    let digest = profile.digest();
    let hub = Arc::new(Mutex::new(Hub {
        data: FrameData {
            state: State::default(),
            profile,
            settings: HostSettings {
                selected: opts.device,
                hotkeys: registered,
                devices: vec![],
                error: if conflicts.is_empty() {
                    None
                } else {
                    Some(conflicts.join("; "))
                },
            },
            preferences,
            native: true,
            remote: false,
            recovery_available: recovery.0,
            hud: false,
            companion_url: None,
            error,
        },
        sequence: 1,
        context: None,
        hidden: false,
        settings_dir,
        digest,
    }));
    let running = Arc::new(AtomicBool::new(true));
    if let Some(dir) = opts.companion {
        super::server::start(hub.clone(), running.clone(), dir)?;
    }
    let mut input = super::sdl_input::SdlInput::new()?;
    let gui = if !opts.diagnostic {
        let h = hub.clone();
        let running = running.clone();
        Some(thread::spawn(move || {
            let result = eframe::run_native(
                "Binding reference",
                eframe::NativeOptions {
                    viewport: egui::ViewportBuilder::default()
                        .with_inner_size([1000.0, 850.0])
                        .with_min_inner_size([680.0, 640.0])
                        .with_transparent(true),
                    event_loop_builder: Some(Box::new(|b| {
                        b.with_any_thread(true);
                    })),
                    ..Default::default()
                },
                Box::new(move |cc| {
                    h.lock().expect("hub").context = Some(cc.egui_ctx.clone());
                    Ok(Box::new(OverlayApp::new(cc, Box::new(NativeBackend(h)))))
                }),
            );
            running.store(false, Ordering::Release);
            result.map_err(|e| e.to_string())
        }))
    } else {
        println!(
            "SDL3 diagnostic. Select --device ID from the list. Ctrl+C exits. Verify physical L1/R1 with Steam and game focused."
        );
        None
    };
    let mut last_diagnostic = Vec::new();
    let mut last_input_error = None;
    let mut selection = DeviceSelection::default();
    while running.load(Ordering::Acquire) {
        let (sample, input_error) = match input.poll() {
            Ok(sample) => (sample, None),
            Err(error) => (
                super::sdl_input::Sample {
                    devices: vec![],
                    events: vec![],
                    now_ms: sdl3::timer::ticks(),
                    identities: vec![],
                },
                Some(error),
            ),
        };
        if input.quit_requested {
            running.store(false, Ordering::Release);
            if let Some(ctx) = &hub.lock().expect("hub").context {
                ctx.send_viewport_cmd(egui::ViewportCommand::Close);
            }
            break;
        }
        let devices = sample.devices;
        if opts.diagnostic && devices != last_diagnostic {
            println!("{}", serde_json::to_string(&devices).expect("devices"));
            last_diagnostic = devices.clone();
        }
        let mut h = hub.lock().expect("hub");
        if input_error != last_input_error {
            if input_error.is_some() || h.data.error == last_input_error {
                h.data.error = input_error.clone();
            }
            last_input_error = input_error.clone();
            h.changed();
        }
        if h.data.settings.hotkeys != registered {
            registered = h.data.settings.hotkeys;
            let conflicts = keys.rebind(registered);
            h.data.settings.error = if conflicts.is_empty() {
                None
            } else {
                Some(conflicts.join("; "))
            };
            h.changed();
        }
        let mut message = MSG::default();
        while unsafe { PeekMessageW(&mut message, None, WM_HOTKEY, WM_HOTKEY, PM_REMOVE) }.as_bool()
        {
            match message.wParam.0 {
                1..=3 => {
                    if h.data.state.select_mode(Mode::ALL[message.wParam.0 - 1]) {
                        h.changed();
                    }
                }
                100 => h.window(false, false),
                _ => {}
            }
        }
        if h.data.settings.selected != selection.current {
            selection = DeviceSelection::default();
            if let Some(id) = &h.data.settings.selected {
                selection.choose(id.clone(), None);
            }
        }
        let identities = sample.identities;
        if let Some(id) = selection.resolve(&identities)
            && h.data.settings.selected.as_ref() != Some(&id)
        {
            h.data.settings.selected = Some(id);
            h.changed();
        }
        let tracker = InputTracker {
            selected: h.data.settings.selected.clone(),
        };
        let changed = if input_error.is_some() {
            let changed = h.data.state.status != InputStatus::Unavailable;
            h.data.state.unavailable(InputStatus::Unavailable);
            changed
        } else {
            {
                let FrameData { state, profile, .. } = &mut h.data;
                tracker.sample_timed(state, &devices, &sample.events, sample.now_ms, profile)
            }
        };
        let metadata: Vec<_> = devices
            .into_iter()
            .map(|mut d| {
                d.held = [false, false];
                d.input = InputFrame::default();
                d
            })
            .collect();
        if changed || metadata != h.data.settings.devices {
            h.data.settings.devices = metadata;
            h.changed();
        }
        drop(h);
        thread::sleep(Duration::from_millis(8));
    }
    if let Some(gui) = gui {
        gui.join().map_err(|_| "GUI thread panicked")??;
    }
    Ok(())
}
