use super::{WebState, js_error, now_ms, page_hidden};
use crate::core::{BridgeSnapshot, Gestures, InputStatus, Mode, ModeCommand, Profile, State};
use crate::ui::FrameData;
use std::{cell::RefCell, rc::Rc};
use wasm_bindgen::{JsCast, JsValue};
use wasm_bindgen_futures::{JsFuture, spawn_local};

async fn fetch_snapshot(
    base: &str,
    token: &str,
    digest: &str,
    mode: Option<Mode>,
) -> Result<BridgeSnapshot, String> {
    let init = request_init(token, digest, mode)?;
    let window = web_sys::window().ok_or("No browser window")?;
    let endpoint = format!(
        "{base}api/{}",
        if mode.is_some() { "mode" } else { "state" }
    );
    let response: web_sys::Response = JsFuture::from(window.fetch_with_str_and_init(
        &endpoint,
        &init,
    ))
    .await
    .map_err(|e| format!("{} · keep the helper running, allow local network access in this site's browser permissions, and reopen its pairing link", js_error(e)))?
    .dyn_into()
    .map_err(js_error)?;
    if !response.ok() {
        return Err(format!(
            "Companion returned HTTP {} · reopen its link if it restarted",
            response.status()
        ));
    }
    let text = JsFuture::from(response.text().map_err(js_error)?)
        .await
        .map_err(js_error)?
        .as_string()
        .ok_or("Invalid companion response")?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn request_init(
    token: &str,
    digest: &str,
    mode: Option<Mode>,
) -> Result<web_sys::RequestInit, String> {
    let init = web_sys::RequestInit::new();
    // The initial Local Network Access permission prompt may need user time.
    init.set_signal(Some(&web_sys::AbortSignal::timeout_with_u32(
        if digest.is_empty() { 30000 } else { 3000 },
    )));
    init.set_method(if mode.is_some() { "POST" } else { "GET" });
    let headers = web_sys::Headers::new().map_err(js_error)?;
    headers.set("X-Keybind-Session", token).map_err(js_error)?;
    headers.set("X-Keybind-Profile", digest).map_err(js_error)?;
    if let Some(mode) = mode {
        headers
            .set("Content-Type", "application/json")
            .map_err(js_error)?;
        init.set_body(&JsValue::from_str(
            &serde_json::to_string(&ModeCommand { mode }).expect("mode"),
        ));
    }
    init.set_headers(&headers);
    Ok(init)
}

pub(super) fn poll(shared: &Rc<RefCell<WebState>>) {
    let mut s = shared.borrow_mut();
    // One request at a time; at most 30 Hz. Rendering only wakes on changed state.
    s.check_companion_freshness();
    s.animate_preview();
    if s.busy || js_sys::Date::now() - s.last_poll < 33.0 {
        return;
    }
    s.busy = true;
    s.last_poll = js_sys::Date::now();
    let bridge = s.bridge.as_ref().expect("remote");
    let token = bridge.session.clone();
    let base = s.bridge_base.clone();
    let digest = bridge
        .profile
        .as_ref()
        .map(Profile::digest)
        .unwrap_or_default();
    let mode = s.pending_mode.take();
    let generation = s.generation;
    let shared = shared.clone();
    drop(s);
    spawn_local(async move {
        let result = fetch_snapshot(&base, &token, &digest, mode).await;
        let mut s = shared.borrow_mut();
        s.busy = false;
        if generation != s.generation || s.paused || page_hidden() {
            return;
        }
        s.accept_snapshot(result);
    });
}

impl WebState {
    fn check_companion_freshness(&mut self) {
        if self.freshness.expired(js_sys::Date::now())
            && self.data.state.status == InputStatus::Live
        {
            self.data.state.unavailable(InputStatus::Unavailable);
            if let Some(bridge) = &mut self.bridge {
                bridge.disconnect();
            }
            self.data.error = Some("Companion input timed out".into());
            self.repaint();
        }
    }

    fn animate_preview(&mut self) {
        if self.remote_timing_scale.is_some() && self.data.state.status == InputStatus::Live {
            let FrameData { state, profile, .. } = &mut self.data;
            if let Some(id) = state.device.clone() {
                state.sample_input(&id, state.input.clone(), profile, now_ms() as u64);
            }
            if self.data.state.gestures.animating() {
                self.repaint();
            }
        }
    }

    fn accept_snapshot(&mut self, result: Result<BridgeSnapshot, String>) {
        let profile_changed = result.as_ref().is_ok_and(|snap| snap.profile.is_some());
        let result = result.and_then(|snap| self.bridge.as_mut().expect("remote").accept(snap));
        match result {
            Ok(changed) => {
                self.freshness.received(js_sys::Date::now());
                if changed {
                    self.apply_snapshot(profile_changed);
                    self.data.error = None;
                    self.repaint();
                }
            }
            Err(e) => {
                let old = self.data.error.clone();
                self.bridge.as_mut().expect("remote").disconnect();
                self.data.state.unavailable(InputStatus::Unavailable);
                self.data.error = Some(format!("Companion disconnected: {e}"));
                if old != self.data.error {
                    self.repaint();
                }
            }
        }
    }

    fn apply_snapshot(&mut self, profile_changed: bool) {
        let bridge = self.bridge.as_ref().expect("remote");
        let state = bridge.state.clone();
        self.data.settings = bridge.settings.clone();
        if let Some(profile) = bridge.profile.clone() {
            self.data.profile = profile;
        }
        if let Some(scale) = self.remote_timing_scale {
            self.apply_preview(state, profile_changed, scale);
        } else {
            self.data.state = state;
        }
    }

    fn apply_preview(&mut self, state: State, profile_changed: bool, scale: u8) {
        if profile_changed {
            self.data.state.gestures = Gestures::default();
        }
        self.data.state.set_timing_scale(scale);
        self.data.state.select_mode(state.mode);
        if state.status == InputStatus::Live {
            if let Some(id) = state.device {
                let FrameData {
                    state: preview,
                    profile,
                    ..
                } = &mut self.data;
                preview.sample_input(&id, state.input, profile, now_ms() as u64);
            }
        } else {
            self.data.state.unavailable(state.status);
        }
    }
}
