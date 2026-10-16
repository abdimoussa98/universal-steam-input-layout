//! Opt-in, same-machine companion. Only mode commands can mutate host state.
use super::host::Hub;
use crate::core::{ModeCommand, validate_request};
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
    let directory = directory
        .canonicalize()
        .map_err(|e| format!("Web bundle directory: {e}"))?;
    for file in [
        "index.html",
        "start.js",
        "pkg/keybind_overlay.js",
        "pkg/keybind_overlay_bg.wasm",
    ] {
        if !directory.join(file).is_file() {
            return Err(format!("Missing web bundle asset: {file}"));
        }
    }
    let server = Server::http("127.0.0.1:0").map_err(|e| e.to_string())?;
    let address = server.server_addr().to_ip().ok_or("No loopback address")?;
    let host = address.to_string();
    let mut bytes = [0_u8; 32];
    getrandom::fill(&mut bytes).map_err(|e| e.to_string())?;
    let session: String = bytes.iter().map(|b| format!("{b:02x}")).collect();
    let url = format!("http://{host}/#companion={session}");
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
            let mut code = 200;
            let (body, mime) = if request_host != host
                || origin
                    .as_ref()
                    .is_some_and(|o| o != &format!("http://{host}"))
                || (api
                    && !validate_request(&request_host, origin.as_deref(), &token, &host, &session))
            {
                code = 403;
                (b"Forbidden".to_vec(), "text/plain")
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
                let asset = match path.as_str() {
                    "/" | "/index.html" => Some(("index.html", "text/html; charset=utf-8")),
                    "/start.js" => Some(("start.js", "text/javascript")),
                    "/pkg/keybind_overlay.js" => {
                        Some(("pkg/keybind_overlay.js", "text/javascript"))
                    }
                    "/pkg/keybind_overlay_bg.wasm" => {
                        Some(("pkg/keybind_overlay_bg.wasm", "application/wasm"))
                    }
                    _ => None,
                };
                match asset {
                    Some((name, mime)) => match std::fs::read(directory.join(name)) {
                        Ok(b) => (b, mime),
                        Err(_) => {
                            code = 500;
                            (b"Missing asset".to_vec(), "text/plain")
                        }
                    },
                    None => {
                        code = 404;
                        (b"Not found".to_vec(), "text/plain")
                    }
                }
            } else {
                code = 405;
                (b"Method not allowed".to_vec(), "text/plain")
            };
            let response = Response::from_data(body)
                .with_status_code(StatusCode(code))
                .with_header(Header::from_bytes("Content-Type", mime).expect("header"))
                .with_header(Header::from_bytes("Cache-Control", "no-store").expect("header"))
                .with_header(
                    Header::from_bytes("X-Content-Type-Options", "nosniff").expect("header"),
                )
                .with_header(Header::from_bytes("Referrer-Policy", "no-referrer").expect("header"));
            let _ = req.respond(response);
        }
    });
    Ok(())
}
