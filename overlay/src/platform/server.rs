//! Opt-in, same-machine companion. Only mode commands can mutate host state.
use super::host::Hub;
use crate::core::{HostedViewer, ModeCommand};
use std::{
    io::Read,
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    thread,
    time::Duration,
};
use tiny_http::{Header, Method, Response, Server, StatusCode};

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
    thread::spawn(move || {
        while running.load(Ordering::Acquire) {
            let Ok(Some(mut req)) = server.recv_timeout(Duration::from_millis(100)) else {
                continue;
            };
            let header = |name: &str| {
                req.headers()
                    .iter()
                    .find(|h| h.field.as_str().as_str().eq_ignore_ascii_case(name))
                    .map(|h| h.value.as_str().to_owned())
            };
            let request_host = header("Host").unwrap_or_default();
            let origin = header("Origin");
            let token = header("X-Keybind-Session").unwrap_or_default();
            let digest = header("X-Keybind-Profile").unwrap_or_default();
            let path = req.url().to_owned();
            let api = path.starts_with("/api/");
            let cors = origin
                .as_ref()
                .filter(|o| allowed_origin.as_ref() == Some(o));
            let origin_allowed = origin
                .as_ref()
                .is_none_or(|o| o == &format!("http://{host}") || (api && cors.is_some()));
            let preflight = req.method() == &Method::Options;
            let preflight_allowed = cors.is_some()
                && matches!(
                    (
                        path.as_str(),
                        header("Access-Control-Request-Method").as_deref()
                    ),
                    ("/api/state", Some("GET")) | ("/api/mode", Some("POST"))
                )
                && header("Access-Control-Request-Headers").is_some_and(|headers| {
                    let headers: Vec<_> = headers
                        .split(',')
                        .map(|h| h.trim().to_ascii_lowercase())
                        .collect();
                    headers.iter().any(|h| h == "x-keybind-session")
                        && headers.iter().all(|h| {
                            matches!(
                                h.as_str(),
                                "x-keybind-session" | "x-keybind-profile" | "content-type"
                            )
                        })
                });
            let mut code = 200;
            let (body, mime) = if request_host != host
                || !origin_allowed
                || (preflight && !preflight_allowed)
                || (api && !preflight && token != session)
            {
                code = 403;
                (b"Forbidden".to_vec(), "text/plain")
            } else if preflight {
                code = 204;
                (vec![], "text/plain")
            } else if path == "/api/state" && req.method() == &Method::Get {
                (
                    serde_json::to_vec(&hub.lock().expect("hub").snapshot(&session, &digest))
                        .expect("snapshot"),
                    "application/json",
                )
            } else if path == "/api/mode" && req.method() == &Method::Post {
                let mut body = String::new();
                let read = req.as_reader().take(1025).read_to_string(&mut body);
                if read.is_err() || body.len() > 1024 {
                    code = 400;
                    (b"Invalid command".to_vec(), "text/plain")
                } else {
                    match serde_json::from_str::<ModeCommand>(&body) {
                        Ok(command) => {
                            let mut h = hub.lock().expect("hub");
                            if h.data.state.select_mode(command.mode) {
                                h.changed();
                            }
                            (
                                serde_json::to_vec(&h.snapshot(&session, &digest))
                                    .expect("snapshot"),
                                "application/json",
                            )
                        }
                        Err(_) => {
                            code = 400;
                            (b"Invalid command".to_vec(), "text/plain")
                        }
                    }
                }
            } else if req.method() == &Method::Get {
                // Whitelist bundle assets; no filesystem paths are accepted from clients.
                // Static assets carry a bundle-version query for browser caches.
                let asset_path = path.split_once('?').map_or(path.as_str(), |(path, _)| path);
                let asset = match asset_path {
                    "/" | "/index.html" => Some(("index.html", "text/html; charset=utf-8")),
                    "/steam-hid.js" => Some(("steam-hid.js", "text/javascript")),
                    "/start.js" => Some(("start.js", "text/javascript")),
                    "/pkg/keybind_overlay.js" => {
                        Some(("pkg/keybind_overlay.js", "text/javascript"))
                    }
                    "/pkg/keybind_overlay_bg.wasm" => {
                        Some(("pkg/keybind_overlay_bg.wasm", "application/wasm"))
                    }
                    _ => None,
                };
                match (asset, directory.as_ref()) {
                    (Some((name, mime)), Some(directory)) => {
                        match std::fs::read(directory.join(name)) {
                            Ok(b) => (b, mime),
                            Err(_) => {
                                code = 500;
                                (b"Missing asset".to_vec(), "text/plain")
                            }
                        }
                    }
                    _ => {
                        code = 404;
                        (b"Not found".to_vec(), "text/plain")
                    }
                }
            } else {
                code = 405;
                (b"Method not allowed".to_vec(), "text/plain")
            };
            let mut response = Response::from_data(body)
                .with_status_code(StatusCode(code))
                .with_header(Header::from_bytes("Content-Type", mime).expect("header"))
                .with_header(Header::from_bytes("Cache-Control", "no-store").expect("header"))
                .with_header(
                    Header::from_bytes("X-Content-Type-Options", "nosniff").expect("header"),
                )
                .with_header(Header::from_bytes("Referrer-Policy", "no-referrer").expect("header"));
            if let Some(origin) = cors.filter(|_| request_host == host && api) {
                response.add_header(
                    Header::from_bytes("Access-Control-Allow-Origin", origin.as_str())
                        .expect("header"),
                );
                response.add_header(Header::from_bytes("Vary", "Origin").expect("header"));
                if preflight && code == 204 {
                    for (name, value) in [
                        ("Access-Control-Allow-Methods", "GET, POST"),
                        (
                            "Access-Control-Allow-Headers",
                            "X-Keybind-Session, X-Keybind-Profile, Content-Type",
                        ),
                        ("Access-Control-Max-Age", "600"),
                        ("Access-Control-Allow-Private-Network", "true"),
                    ] {
                        response.add_header(Header::from_bytes(name, value).expect("header"));
                    }
                }
            }
            let _ = req.respond(response);
        }
    });
    Ok(())
}
