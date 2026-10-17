//! Opt-in, same-machine companion. Only mode commands can mutate host state.
mod request;

use super::host::Hub;
use crate::core::HostedViewer;
use request::CompanionServer;
use std::{
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    thread,
    time::Duration,
};
use tiny_http::Server;

pub fn start(
    hub: Arc<Mutex<Hub>>,
    running: Arc<AtomicBool>,
    directory: PathBuf,
) -> Result<(), String> {
    start_server(hub, running, Some(directory), None)
}

pub fn start_hosted(
    hub: Arc<Mutex<Hub>>,
    running: Arc<AtomicBool>,
    directory: Option<PathBuf>,
    viewer_url: &str,
) -> Result<(), String> {
    start_server(
        hub,
        running,
        directory,
        Some(HostedViewer::parse(viewer_url)?),
    )
}

fn start_server(
    hub: Arc<Mutex<Hub>>,
    running: Arc<AtomicBool>,
    directory: Option<PathBuf>,
    viewer: Option<HostedViewer>,
) -> Result<(), String> {
    let directory = validate_directory(directory)?;
    let server = Server::http("127.0.0.1:0").map_err(|e| e.to_string())?;
    let address = server.server_addr().to_ip().ok_or("No loopback address")?;
    let host = address.to_string();
    let mut bytes = [0_u8; 32];
    getrandom::fill(&mut bytes).map_err(|e| e.to_string())?;
    let session: String = bytes.iter().map(|b| format!("{b:02x}")).collect();
    let url = viewer
        .as_ref()
        .map(|v| v.pairing_url(address.port(), &session))
        .unwrap_or_else(|| format!("http://{host}/#companion={session}"));
    let allowed_origin = viewer.map(|v| v.origin());
    println!("Browser companion: {url}");
    hub.lock().expect("hub").data.companion_url = Some(url);
    let companion = CompanionServer {
        hub,
        directory,
        host,
        session,
        allowed_origin,
    };
    thread::spawn(move || {
        while running.load(Ordering::Acquire) {
            if let Ok(Some(req)) = server.recv_timeout(Duration::from_millis(100)) {
                companion.respond(req);
            }
        }
    });
    Ok(())
}

fn validate_directory(directory: Option<PathBuf>) -> Result<Option<PathBuf>, String> {
    let directory = directory
        .map(|d| {
            d.canonicalize()
                .map_err(|e| format!("Web bundle directory: {e}"))
        })
        .transpose()?;
    if let Some(directory) = &directory {
        for file in [
            "index.html",
            "start.js",
            "steam-hid.js",
            "pkg/keybind_overlay.js",
            "pkg/keybind_overlay_bg.wasm",
        ] {
            if !directory.join(file).is_file() {
                return Err(format!("Missing web bundle asset: {file}"));
            }
        }
    }
    Ok(directory)
}
