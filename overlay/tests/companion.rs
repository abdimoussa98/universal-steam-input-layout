#![cfg(all(feature = "desktop", not(target_arch = "wasm32")))]
use keybind_overlay::{
    BUNDLED_PROFILE, core::*, platform::host::Hub, platform::server, ui::FrameData,
};
use std::{
    io::{Read, Write},
    net::TcpStream,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
};

#[test]
fn real_http_companion_authority_origin_and_asset_boundaries() {
    let directory = std::env::temp_dir().join(format!("keybind-http-test-{}", std::process::id()));
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
    let profile = Profile::parse(BUNDLED_PROFILE).unwrap();
    let hub = Arc::new(Mutex::new(Hub::new(
        FrameData {
            state: State::default(),
            profile,
            settings: HostSettings::default(),
            preferences: Preferences::default(),
            native: true,
            remote: false,
            recovery_available: true,
            hud: false,
            companion_url: None,
            browser_connection: None,
            error: None,
        },
        directory.clone(),
    )));
    let running = Arc::new(AtomicBool::new(true));
    server::start(hub.clone(), running.clone(), directory.clone()).unwrap();
    let url = hub.lock().unwrap().data.companion_url.clone().unwrap();
    let (origin, session) = url.split_once("/#companion=").unwrap();
    let address = origin.strip_prefix("http://").unwrap();
    // HTTP/1.0 keeps this small raw-socket test independent of chunked transfer.
    // The browser smoke test exercises the production HTTP/1.1 path.
    let request = |path: &str, token: &str, request_origin: &str, body: Option<&str>| {
        let mut socket = TcpStream::connect(address).unwrap();
        socket
            .set_read_timeout(Some(std::time::Duration::from_secs(3)))
            .unwrap();
        let data = body.unwrap_or("");
        write!(socket,"{} {} HTTP/1.0\r\nHost: {}\r\nOrigin: {}\r\nX-Keybind-Session: {}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",if body.is_some(){"POST"}else{"GET"},path,address,request_origin,token,data.len(),data).unwrap();
        let mut response = String::new();
        socket.read_to_string(&mut response).unwrap();
        response
    };
    assert!(request("/api/state", "wrong", origin, None).starts_with("HTTP/1.0 403"));
    assert!(request("/api/state", session, "http://evil.test", None).starts_with("HTTP/1.0 403"));
    assert!(request("/../profile.json", session, origin, None).starts_with("HTTP/1.0 404"));
    assert!(request("/", session, origin, None).contains("test asset"));
    for path in [
        "/layouts/../profile.vdf",
        "/layouts/%2e%2e/profile.vdf",
        "/layouts/sub/file.vdf",
        "/layouts/profile.json",
    ] {
        assert!(request(path, session, origin, None).starts_with("HTTP/1.0 404"));
    }

    for asset in [
        "start.js",
        "steam-hid.js",
        "downloads.js",
        "layouts/index.json",
        "layouts/deck_1.0.vdf",
        "pkg/keybind_overlay.js",
        "pkg/keybind_overlay_bg.wasm",
    ] {
        let response = request(&format!("/{asset}?v=release-hash"), session, origin, None);
        assert!(response.starts_with("HTTP/1.0 200"), "{asset}: {response}");
        assert!(response.contains("test asset"));
    }
    assert!(
        request("/../profile.json?v=release-hash", session, origin, None)
            .starts_with("HTTP/1.0 404")
    );
    let response = request("/api/state", session, origin, None);
    assert!(response.starts_with("HTTP/1.0 200"));
    let first: BridgeSnapshot =
        serde_json::from_str(response.split_once("\r\n\r\n").unwrap().1).unwrap();
    assert_eq!(first.state.mode, Mode::Base);
    assert!(first.profile.is_some());
    assert!(
        request(
            "/api/mode",
            session,
            origin,
            Some(r#"{"mode":"menu","file":"oops"}"#)
        )
        .starts_with("HTTP/1.0 400")
    );
    let response = request("/api/mode", session, origin, Some(r#"{"mode":"steering"}"#));
    let next: BridgeSnapshot =
        serde_json::from_str(response.split_once("\r\n\r\n").unwrap().1).unwrap();
    assert_eq!(next.state.mode, Mode::Steering);
    assert!(next.sequence > first.sequence);
    assert_eq!(hub.lock().unwrap().data.state.mode, Mode::Steering);
    running.store(false, Ordering::Release);
    std::fs::remove_dir_all(directory).unwrap();
}

#[test]
fn hosted_viewer_pairs_only_with_its_allowed_origin_and_session() {
    let hub = Arc::new(Mutex::new(Hub::new(
        FrameData {
            state: State::default(),
            profile: Profile::parse(BUNDLED_PROFILE).unwrap(),
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
        std::env::temp_dir(),
    )));
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
    let address = endpoint
        .base_url
        .trim_start_matches("http://")
        .trim_end_matches('/');
    let request = |method: &str, path: &str, origin: &str, host: &str, extra: &str, body: &str| {
        let mut socket = TcpStream::connect(address).unwrap();
        socket
            .set_read_timeout(Some(std::time::Duration::from_secs(3)))
            .unwrap();
        write!(socket, "{method} {path} HTTP/1.0\r\nHost: {host}\r\nOrigin: {origin}\r\n{extra}Content-Length: {}\r\nConnection: close\r\n\r\n{body}", body.len()).unwrap();
        let mut response = String::new();
        socket.read_to_string(&mut response).unwrap();
        response
    };
    let preflight = "Access-Control-Request-Method: GET\r\nAccess-Control-Request-Headers: x-keybind-session,x-keybind-profile\r\nAccess-Control-Request-Private-Network: true\r\n";
    let response = request(
        "OPTIONS",
        "/api/state",
        "https://viewer.example",
        address,
        preflight,
        "",
    );
    assert!(response.starts_with("HTTP/1.0 204"), "{response}");
    assert!(
        response
            .to_lowercase()
            .contains("access-control-allow-origin: https://viewer.example")
    );
    assert!(
        response
            .to_lowercase()
            .contains("access-control-allow-private-network: true")
    );
    for origin in [
        "https://evil.example",
        "https://viewer.example.evil.test",
        "null",
        "http://viewer.example",
    ] {
        let response = request("OPTIONS", "/api/state", origin, address, preflight, "");
        assert!(response.starts_with("HTTP/1.0 403"));
        assert!(
            !response
                .to_lowercase()
                .contains("access-control-allow-origin")
        );
    }
    assert!(
        request(
            "OPTIONS",
            "/api/state",
            "https://viewer.example",
            "rebound.example",
            preflight,
            ""
        )
        .starts_with("HTTP/1.0 403")
    );
    assert!(
        request(
            "OPTIONS",
            "/api/state",
            "https://viewer.example",
            address,
            "Access-Control-Request-Method: DELETE\r\n",
            ""
        )
        .starts_with("HTTP/1.0 403")
    );
    assert!(
        request(
            "GET",
            "/api/state",
            "https://viewer.example",
            address,
            "",
            ""
        )
        .starts_with("HTTP/1.0 403")
    );
    let token = format!("X-Keybind-Session: {}\r\n", endpoint.session);
    let response = request(
        "POST",
        "/api/mode",
        "https://viewer.example",
        address,
        &token,
        r#"{"mode":"steering"}"#,
    );
    assert!(response.starts_with("HTTP/1.0 200"), "{response}");
    assert_eq!(hub.lock().unwrap().data.state.mode, Mode::Steering);
    let response = request(
        "GET",
        "/api/state",
        "https://viewer.example",
        address,
        &token,
        "",
    );
    assert!(response.starts_with("HTTP/1.0 200"));
    assert!(
        response
            .to_lowercase()
            .contains("access-control-allow-origin: https://viewer.example")
    );
    assert!(
        request(
            "GET",
            "/api/state",
            "https://evil.example",
            address,
            &token,
            ""
        )
        .starts_with("HTTP/1.0 403")
    );
    running.store(false, Ordering::Release);
}
