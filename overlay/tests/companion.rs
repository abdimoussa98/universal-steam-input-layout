#![cfg(all(feature = "desktop", not(target_arch = "wasm32")))]
use keybind_overlay::core::{BridgeSnapshot, Mode};
#[path = "companion/support.rs"]
mod support;
use support::{Headers, TestServer};

#[test]
fn real_http_companion_authority_origin_and_asset_boundaries() {
    let server = TestServer::local();
    let request = |path, token, origin| server.local_request(path, token, origin, None);
    assert!(request("/api/state", "wrong", &server.origin).starts_with("HTTP/1.0 403"));
    assert!(request("/api/state", &server.session, "http://evil.test").starts_with("HTTP/1.0 403"));
    assert!(
        request("/../profile.json", &server.session, &server.origin).starts_with("HTTP/1.0 404")
    );
    assert!(request("/", &server.session, &server.origin).contains("test asset"));
    check_asset_boundaries(&server);
    check_mode_commands(&server);
}

fn check_asset_boundaries(server: &TestServer) {
    let request = |path: &str| server.local_request(path, &server.session, &server.origin, None);
    for path in [
        "/layouts/../profile.vdf",
        "/layouts/%2e%2e/profile.vdf",
        "/layouts/sub/file.vdf",
        "/layouts/profile.json",
    ] {
        assert!(request(path).starts_with("HTTP/1.0 404"));
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
        let response = request(&format!("/{asset}?v=release-hash"));
        assert!(response.starts_with("HTTP/1.0 200"), "{asset}: {response}");
        assert!(response.contains("test asset"));
    }
    assert!(request("/../profile.json?v=release-hash").starts_with("HTTP/1.0 404"));
}

fn check_mode_commands(server: &TestServer) {
    let request = |path, body| server.local_request(path, &server.session, &server.origin, body);
    let response = request("/api/state", None);
    assert!(response.starts_with("HTTP/1.0 200"));
    let first: BridgeSnapshot =
        serde_json::from_str(response.split_once("\r\n\r\n").unwrap().1).unwrap();
    assert_eq!(first.state.mode, Mode::Base);
    assert!(first.profile.is_some());
    assert!(
        request("/api/mode", Some(r#"{"mode":"menu","file":"oops"}"#)).starts_with("HTTP/1.0 400")
    );
    let response = request("/api/mode", Some(r#"{"mode":"steering"}"#));
    let next: BridgeSnapshot =
        serde_json::from_str(response.split_once("\r\n\r\n").unwrap().1).unwrap();
    assert_eq!(next.state.mode, Mode::Steering);
    assert!(next.sequence > first.sequence);
    assert_eq!(server.hub.lock().unwrap().data.state.mode, Mode::Steering);
}

const PREFLIGHT: &str = "Access-Control-Request-Method: GET\r\nAccess-Control-Request-Headers: x-keybind-session,x-keybind-profile\r\nAccess-Control-Request-Private-Network: true\r\n";

#[test]
fn hosted_viewer_pairs_only_with_its_allowed_origin_and_session() {
    let server = TestServer::hosted();
    check_hosted_preflight(&server);
    check_hosted_authority(&server);
    check_hosted_mode_commands(&server);
}

fn check_hosted_preflight(server: &TestServer) {
    let response = server.request("OPTIONS", "/api/state", server.headers(PREFLIGHT), "");
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
        let headers = Headers {
            origin,
            ..server.headers(PREFLIGHT)
        };
        let response = server.request("OPTIONS", "/api/state", headers, "");
        assert!(response.starts_with("HTTP/1.0 403"));
        assert!(
            !response
                .to_lowercase()
                .contains("access-control-allow-origin")
        );
    }
}

fn check_hosted_authority(server: &TestServer) {
    let rebound = Headers {
        host: "rebound.example",
        ..server.headers(PREFLIGHT)
    };
    assert!(
        server
            .request("OPTIONS", "/api/state", rebound, "")
            .starts_with("HTTP/1.0 403")
    );
    let method = server.headers("Access-Control-Request-Method: DELETE\r\n");
    assert!(
        server
            .request("OPTIONS", "/api/state", method, "")
            .starts_with("HTTP/1.0 403")
    );
    assert!(
        server
            .request("GET", "/api/state", server.headers(""), "")
            .starts_with("HTTP/1.0 403")
    );
}

fn check_hosted_mode_commands(server: &TestServer) {
    let token = format!("X-Keybind-Session: {}\r\n", server.session);
    let response = server.request(
        "POST",
        "/api/mode",
        server.headers(&token),
        r#"{"mode":"steering"}"#,
    );
    assert!(response.starts_with("HTTP/1.0 200"), "{response}");
    assert_eq!(server.hub.lock().unwrap().data.state.mode, Mode::Steering);
    let response = server.request("GET", "/api/state", server.headers(&token), "");
    assert!(response.starts_with("HTTP/1.0 200"));
    assert!(
        response
            .to_lowercase()
            .contains("access-control-allow-origin: https://viewer.example")
    );
    let untrusted = Headers {
        origin: "https://evil.example",
        ..server.headers(&token)
    };
    assert!(
        server
            .request("GET", "/api/state", untrusted, "")
            .starts_with("HTTP/1.0 403")
    );
}
