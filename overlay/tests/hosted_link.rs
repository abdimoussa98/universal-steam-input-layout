use keybind_overlay::core::{CompanionEndpoint, HostedViewer};

const TOKEN: &str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

#[test]
fn hosted_pairing_keeps_input_on_loopback_and_preserves_the_site_path() {
    let viewer = HostedViewer::parse("https://viewer.example/app/").unwrap();
    assert_eq!(viewer.origin(), "https://viewer.example");
    let link = viewer.pairing_url(12345, TOKEN);
    assert_eq!(
        link,
        format!("https://viewer.example/app/#companion={TOKEN}&port=12345")
    );
    let endpoint = CompanionEndpoint::parse_fragment(link.split_once('#').unwrap().1)
        .unwrap()
        .unwrap();
    assert_eq!(endpoint.session, TOKEN);
    assert_eq!(endpoint.base_url, "http://127.0.0.1:12345/");
    let local = CompanionEndpoint::parse_fragment(&format!("companion={TOKEN}"))
        .unwrap()
        .unwrap();
    assert_eq!(local.base_url, "./");
    assert!(
        CompanionEndpoint::parse_fragment("unrelated")
            .unwrap()
            .is_none()
    );
}

#[test]
fn pairing_cannot_redirect_a_token_to_an_arbitrary_host() {
    for fragment in [
        format!("companion={TOKEN}&port=0"),
        format!("companion={TOKEN}&port=65536"),
        format!("companion={TOKEN}&port=123/evil"),
        format!("companion={TOKEN}&url=https://evil.example"),
        format!("companion={TOKEN}&port=1&port=2"),
        "companion=bad-token".into(),
    ] {
        assert!(
            CompanionEndpoint::parse_fragment(&fragment).is_err(),
            "{fragment}"
        );
    }
    for url in [
        "http://viewer.example/",
        "https://user:pass@viewer.example/",
        "https://viewer.example/#secret",
        "https://viewer.example/?secret=x",
        "file:///tmp/index.html",
        "https://viewer.example/\n",
    ] {
        assert!(HostedViewer::parse(url).is_err(), "{url}");
    }
    assert!(HostedViewer::parse("http://127.0.0.1:8080/app/").is_ok());
}
