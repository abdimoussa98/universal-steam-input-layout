//! Pairing carries only a session token and a loopback port in the URL fragment.
//! The hosted server never receives either value.
use url::Url;

pub struct HostedViewer(Url);
impl HostedViewer {
    pub fn parse(value: &str) -> Result<Self, String> {
        let url = Url::parse(value).map_err(|e| format!("Viewer URL: {e}"))?;
        let local = matches!(url.host_str(), Some("127.0.0.1" | "localhost" | "[::1]"));
        if value.chars().any(char::is_whitespace)
            || !(url.scheme() == "https" || (url.scheme() == "http" && local))
            || url.host_str().is_none()
            || !url.username().is_empty()
            || url.password().is_some()
            || url.query().is_some()
            || url.fragment().is_some()
        {
            return Err("Use an HTTPS viewer URL without credentials, query or fragment (HTTP is allowed only on localhost).".into());
        }
        Ok(Self(url))
    }
    pub fn origin(&self) -> String {
        self.0.origin().ascii_serialization()
    }
    pub fn pairing_url(&self, port: u16, session: &str) -> String {
        let mut url = self.0.clone();
        url.set_fragment(Some(&format!("companion={session}&port={port}")));
        url.to_string()
    }
}

pub struct CompanionEndpoint {
    pub session: String,
    pub base_url: String,
}
impl CompanionEndpoint {
    pub fn parse_fragment(fragment: &str) -> Result<Option<Self>, String> {
        let fragment = fragment.trim_start_matches('#');
        if !fragment.starts_with("companion=") {
            return Ok(None);
        }
        let mut parts = fragment.split('&');
        let session = parts.next().unwrap().trim_start_matches("companion=");
        if session.len() != 64 || !session.bytes().all(|b| b.is_ascii_hexdigit()) {
            return Err("Invalid pairing link. Open the full link printed by the helper.".into());
        }
        let base_url = if let Some(port) = parts.next() {
            let port = port
                .strip_prefix("port=")
                .filter(|s| !s.is_empty() && s.bytes().all(|b| b.is_ascii_digit()))
                .and_then(|s| s.parse::<u16>().ok())
                .filter(|p| *p != 0)
                .ok_or("Invalid helper port in pairing link")?;
            format!("http://127.0.0.1:{port}/")
        } else {
            "./".into()
        };
        if parts.next().is_some() {
            return Err("Unexpected pairing link parameters".into());
        }
        Ok(Some(Self {
            session: session.into(),
            base_url,
        }))
    }
}
