use keybind_overlay::{
    BUNDLED_PROFILE,
    core::*,
    platform::{host::Hub, server},
    ui::FrameData,
};
use std::{
    io::{Read, Write},
    net::TcpStream,
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
};

pub(super) struct TestServer {
    pub(super) hub: Arc<Mutex<Hub>>,
    pub(super) address: String,
    pub(super) origin: String,
    pub(super) session: String,
    running: Arc<AtomicBool>,
    directory: Option<PathBuf>,
}

pub(super) struct Headers<'a> {
    pub(super) host: &'a str,
    pub(super) origin: &'a str,
    pub(super) extra: &'a str,
}

impl TestServer {
    pub(super) fn local() -> Self {
        let directory =
            std::env::temp_dir().join(format!("keybind-http-test-{}", std::process::id()));
        write_assets(&directory);
        let hub = test_hub(directory.clone(), true);
        let running = Arc::new(AtomicBool::new(true));
        server::start(hub.clone(), running.clone(), directory.clone()).unwrap();
        let url = hub.lock().unwrap().data.companion_url.clone().unwrap();
        let (origin, session) = url.split_once("/#companion=").unwrap();
        Self {
            hub,
            address: origin.strip_prefix("http://").unwrap().into(),
            origin: origin.into(),
            session: session.into(),
            running,
            directory: Some(directory),
        }
    }

    pub(super) fn hosted() -> Self {
        let hub = test_hub(std::env::temp_dir(), false);
        let running = Arc::new(AtomicBool::new(true));
        server::start_hosted(
            hub.clone(),
            running.clone(),
            None,
            "https://viewer.example/app/",
        )
        .unwrap();
        let link = hub.lock().unwrap().data.companion_url.clone().unwrap();
        let endpoint = CompanionEndpoint::parse_fragment(link.split_once('#').unwrap().1)
            .unwrap()
            .unwrap();
        Self {
            hub,
            address: endpoint
                .base_url
                .trim_start_matches("http://")
                .trim_end_matches('/')
                .into(),
            origin: "https://viewer.example".into(),
            session: endpoint.session,
            running,
            directory: None,
        }
    }

    pub(super) fn headers<'a>(&'a self, extra: &'a str) -> Headers<'a> {
        Headers {
            host: &self.address,
            origin: &self.origin,
            extra,
        }
    }

    pub(super) fn request(
        &self,
        method: &str,
        path: &str,
        headers: Headers<'_>,
        body: &str,
    ) -> String {
        let mut socket = TcpStream::connect(&self.address).unwrap();
        socket
            .set_read_timeout(Some(std::time::Duration::from_secs(3)))
            .unwrap();
        // HTTP/1.0 keeps this small raw-socket test independent of chunked transfer.
        // The browser smoke test exercises the production HTTP/1.1 path.
        write!(socket,
            "{method} {path} HTTP/1.0\r\nHost: {}\r\nOrigin: {}\r\n{}Content-Length: {}\r\nConnection: close\r\n\r\n{body}",
            headers.host, headers.origin, headers.extra, body.len()
        ).unwrap();
        let mut response = String::new();
        socket.read_to_string(&mut response).unwrap();
        response
    }

    pub(super) fn local_request(
        &self,
        path: &str,
        token: &str,
        origin: &str,
        body: Option<&str>,
    ) -> String {
        let extra = format!("X-Keybind-Session: {token}\r\n");
        let headers = Headers {
            origin,
            ..self.headers(&extra)
        };
        self.request(
            if body.is_some() { "POST" } else { "GET" },
            path,
            headers,
            body.unwrap_or(""),
        )
    }
}

impl Drop for TestServer {
    fn drop(&mut self) {
        self.running.store(false, Ordering::Release);
        if let Some(directory) = &self.directory {
            std::fs::remove_dir_all(directory).unwrap();
        }
    }
}

fn test_hub(directory: PathBuf, recovery_available: bool) -> Arc<Mutex<Hub>> {
    Arc::new(Mutex::new(Hub::new(
        FrameData {
            state: State::default(),
            profile: Profile::parse(BUNDLED_PROFILE).unwrap(),
            settings: HostSettings::default(),
            preferences: Preferences::default(),
            native: true,
            remote: false,
            recovery_available,
            hud: false,
            companion_url: None,
            browser_connection: None,
            error: None,
        },
        directory,
    )))
}

fn write_assets(directory: &std::path::Path) {
    std::fs::create_dir_all(directory.join("pkg")).unwrap();
    std::fs::create_dir_all(directory.join("layouts")).unwrap();
    for asset in [
        "index.html",
        "start.js",
        "steam-hid.js",
        "downloads.js",
        "layouts/index.json",
        "layouts/deck_1.0.vdf",
        "pkg/keybind_overlay.js",
        "pkg/keybind_overlay_bg.wasm",
    ] {
        std::fs::write(directory.join(asset), "test asset").unwrap();
    }
}
