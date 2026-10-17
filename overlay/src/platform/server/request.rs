use super::*;
use crate::core::ModeCommand;
use std::io::{Cursor, Read};
use tiny_http::{Header, Method, Request, Response, StatusCode};

pub(super) struct CompanionServer {
    pub hub: Arc<Mutex<Hub>>,
    pub directory: Option<PathBuf>,
    pub host: String,
    pub session: String,
    pub allowed_origin: Option<String>,
}

impl CompanionServer {
    pub fn respond(&self, mut req: Request) {
        let host = header(&req, "Host").unwrap_or_default();
        let origin = header(&req, "Origin");
        let cors = origin
            .as_ref()
            .filter(|o| self.allowed_origin.as_ref() == Some(o));
        let api = req.url().starts_with("/api/");
        let preflight = req.method() == &Method::Options;
        let origin_allowed = origin
            .as_ref()
            .is_none_or(|o| o == &format!("http://{}", self.host) || (api && cors.is_some()));
        let response = if host != self.host
            || !origin_allowed
            || (preflight && !(cors.is_some() && preflight_allowed(&req)))
            || (api
                && !preflight
                && header(&req, "X-Keybind-Session").unwrap_or_default() != self.session)
        {
            reply(403, b"Forbidden".to_vec(), "text/plain")
        } else if preflight {
            reply(204, vec![], "text/plain")
        } else {
            self.route(&mut req)
        };
        let mut response = security_headers(response);
        if let Some(origin) = cors.filter(|_| host == self.host && api) {
            cors_headers(&mut response, origin, preflight);
        }
        let _ = req.respond(response);
    }

    fn route(&self, req: &mut Request) -> Response<Cursor<Vec<u8>>> {
        let digest = header(req, "X-Keybind-Profile").unwrap_or_default();
        if req.url() == "/api/state" && req.method() == &Method::Get {
            self.snapshot(&digest)
        } else if req.url() == "/api/mode" && req.method() == &Method::Post {
            self.mode(req, &digest)
        } else if req.method() == &Method::Get {
            self.asset(req.url())
        } else {
            reply(405, b"Method not allowed".to_vec(), "text/plain")
        }
    }

    fn snapshot(&self, digest: &str) -> Response<Cursor<Vec<u8>>> {
        reply(
            200,
            serde_json::to_vec(
                &self
                    .hub
                    .lock()
                    .expect("hub")
                    .snapshot(&self.session, digest),
            )
            .expect("snapshot"),
            "application/json",
        )
    }

    fn mode(&self, req: &mut Request, digest: &str) -> Response<Cursor<Vec<u8>>> {
        let mut body = String::new();
        let read = req.as_reader().take(1025).read_to_string(&mut body);
        if read.is_err() || body.len() > 1024 {
            return reply(400, b"Invalid command".to_vec(), "text/plain");
        }
        match serde_json::from_str::<ModeCommand>(&body) {
            Ok(command) => {
                let mut h = self.hub.lock().expect("hub");
                if h.data.state.select_mode(command.mode) {
                    h.changed();
                }
                reply(
                    200,
                    serde_json::to_vec(&h.snapshot(&self.session, digest)).expect("snapshot"),
                    "application/json",
                )
            }
            Err(_) => reply(400, b"Invalid command".to_vec(), "text/plain"),
        }
    }

    fn asset(&self, path: &str) -> Response<Cursor<Vec<u8>>> {
        // Static assets carry a bundle-version query for browser caches.
        let path = path.split_once('?').map_or(path, |(path, _)| path);
        match (asset_path(path), self.directory.as_ref()) {
            (Some((name, mime)), Some(directory)) => match std::fs::read(directory.join(name)) {
                Ok(body) => reply(200, body, mime),
                Err(_) => reply(500, b"Missing asset".to_vec(), "text/plain"),
            },
            _ => reply(404, b"Not found".to_vec(), "text/plain"),
        }
    }
}

fn header(req: &Request, name: &str) -> Option<String> {
    req.headers()
        .iter()
        .find(|h| h.field.as_str().as_str().eq_ignore_ascii_case(name))
        .map(|h| h.value.as_str().to_owned())
}

fn preflight_allowed(req: &Request) -> bool {
    matches!(
        (
            req.url(),
            header(req, "Access-Control-Request-Method").as_deref()
        ),
        ("/api/state", Some("GET")) | ("/api/mode", Some("POST"))
    ) && header(req, "Access-Control-Request-Headers").is_some_and(|headers| {
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
    })
}

fn reply(code: u16, body: Vec<u8>, mime: &str) -> Response<Cursor<Vec<u8>>> {
    Response::from_data(body)
        .with_status_code(StatusCode(code))
        .with_header(Header::from_bytes("Content-Type", mime).expect("header"))
}

fn security_headers(mut response: Response<Cursor<Vec<u8>>>) -> Response<Cursor<Vec<u8>>> {
    for (name, value) in [
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "no-referrer"),
    ] {
        response.add_header(Header::from_bytes(name, value).expect("header"));
    }
    response
}

fn cors_headers(response: &mut Response<Cursor<Vec<u8>>>, origin: &str, preflight: bool) {
    response.add_header(Header::from_bytes("Access-Control-Allow-Origin", origin).expect("header"));
    response.add_header(Header::from_bytes("Vary", "Origin").expect("header"));
    if preflight && response.status_code() == StatusCode(204) {
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

fn asset_path(path: &str) -> Option<(&str, &str)> {
    // Whitelist bundle assets; no filesystem paths are accepted from clients.
    match path {
        "/" | "/index.html" => Some(("index.html", "text/html; charset=utf-8")),
        "/steam-hid.js" => Some(("steam-hid.js", "text/javascript")),
        "/downloads.js" => Some(("downloads.js", "text/javascript")),
        "/layouts/index.json" => Some(("layouts/index.json", "application/json")),
        "/start.js" => Some(("start.js", "text/javascript")),
        "/pkg/keybind_overlay.js" => Some(("pkg/keybind_overlay.js", "text/javascript")),
        "/pkg/keybind_overlay_bg.wasm" => Some(("pkg/keybind_overlay_bg.wasm", "application/wasm")),
        _ if path.strip_prefix("/layouts/").is_some_and(|name| {
            name.ends_with(".vdf")
                && name.starts_with(|c: char| c.is_ascii_alphanumeric())
                && name
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b"_.-".contains(&b))
        }) =>
        {
            Some((&path[1..], "application/octet-stream"))
        }
        _ => None,
    }
}
