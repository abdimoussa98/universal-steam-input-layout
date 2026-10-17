//! SDL and thread hotkeys stay on the process main thread. Eframe owns a
//! separate Windows event loop; state changes wake it, idle samples do not.
mod backend;
mod hotkeys;
mod runtime;
mod settings;

use super::host::Hub;
use crate::{BUNDLED_PROFILE, core::*, ui::*};
use backend::NativeBackend;
use eframe::egui;
use hotkeys::{RecoveryHotkey, WinHotkeys};
use settings::Options;
use std::{
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    thread,
    time::Duration,
};
use winit::platform::windows::EventLoopBuilderExtWindows;

pub fn run() -> Result<(), String> {
    let mut opts = Options::parse()?;
    let loaded = settings::LoadedSettings::load(opts.profile.take())?;
    let recovery = RecoveryHotkey::new();
    let mut keys = Hotkeys::new(WinHotkeys);
    let hub = settings::create_hub(&mut opts, loaded, recovery.0, &mut keys);
    let registered = hub.lock().expect("hub").data.preferences.hotkeys;
    let running = Arc::new(AtomicBool::new(true));
    if let Some(url) = opts.viewer_url {
        super::server::start_hosted(hub.clone(), running.clone(), opts.companion, &url)?;
    } else if let Some(dir) = opts.companion {
        super::server::start(hub.clone(), running.clone(), dir)?;
    }
    let input = super::sdl_input::SdlInput::new()?;
    let gui = start_gui(&hub, &running, opts.diagnostic);
    let mut runtime = runtime::NativeLoop::new(input, keys, registered, opts.diagnostic);
    runtime.run(&hub, &running);
    if let Some(gui) = gui {
        gui.join().map_err(|_| "GUI thread panicked")??;
    }
    Ok(())
}

fn start_gui(
    hub: &Arc<Mutex<Hub>>,
    running: &Arc<AtomicBool>,
    diagnostic: bool,
) -> Option<thread::JoinHandle<Result<(), String>>> {
    if !diagnostic {
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
    }
}
