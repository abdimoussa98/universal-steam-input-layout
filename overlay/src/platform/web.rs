use crate::{BUNDLED_PROFILE, core::*, ui::*};
use eframe::egui;
use std::{cell::RefCell, rc::Rc};
use wasm_bindgen::{JsCast, prelude::*};
use wasm_bindgen_futures::{JsFuture, spawn_local};

const HID_DEVICE_ID: &str = "webhid:steam-controller-usb";
#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = window, js_name = SteamHid)]
    #[derive(Clone)]
    type SteamHid;
    #[wasm_bindgen(constructor, js_namespace = window)]
    fn new(on_input: &js_sys::Function, on_state: &js_sys::Function) -> SteamHid;
    #[wasm_bindgen(method, getter)]
    fn available(this: &SteamHid) -> bool;
    #[wasm_bindgen(method, getter, js_name = supportMessage)]
    fn support_message(this: &SteamHid) -> String;
    #[wasm_bindgen(method)]
    fn connect(this: &SteamHid) -> js_sys::Promise;
    #[wasm_bindgen(method)]
    fn disconnect(this: &SteamHid) -> js_sys::Promise;
    #[wasm_bindgen(method)]
    fn destroy(this: &SteamHid) -> js_sys::Promise;
}
type HidReportCallback = Closure<dyn FnMut(u8, js_sys::Uint8Array)>;
type HidStatusCallback = Closure<dyn FnMut(String, String)>;
fn now_ms() -> f64 {
    web_sys::window()
        .and_then(|w| w.performance())
        .map(|p| p.now())
        .unwrap_or(0.0)
}
fn page_hidden() -> bool {
    web_sys::window()
        .and_then(|w| w.document())
        .is_none_or(|d| d.hidden())
}
struct WebState {
    data: FrameData,
    tracker: InputTracker,
    bridge: Option<BridgeClient>,
    bridge_base: String,
    context: Option<egui::Context>,
    busy: bool,
    pending_mode: Option<Mode>,
    last_poll: f64,
    paused: bool,
    generation: u64,
    freshness: InputFreshness,
    hid: Option<SteamHid>,
    hid_input: Option<InputFrame>,
    hid_received: Option<f64>,
    hid_error: Option<String>,
}
fn storage_read(key: &str) -> Result<Option<String>, String> {
    web_sys::window()
        .ok_or("No browser window")?
        .local_storage()
        .map_err(js_error)?
        .ok_or("Browser storage unavailable")?
        .get_item(key)
        .map_err(js_error)
}
fn storage_write(key: &str, value: &str) -> Result<(), String> {
    web_sys::window()
        .ok_or("No browser window")?
        .local_storage()
        .map_err(js_error)?
        .ok_or("Browser storage unavailable")?
        .set_item(key, value)
        .map_err(js_error)
}
fn js_error(e: JsValue) -> String {
    e.as_string()
        .or_else(|| {
            e.dyn_ref::<js_sys::Error>()
                .map(|e| String::from(e.message()))
        })
        .unwrap_or_else(|| format!("{e:?}"))
}
impl WebState {
    fn new(endpoint: Option<CompanionEndpoint>) -> Self {
        let mut error = None;
        let profile = match storage_read("keybind.profile.v1") {
            Ok(Some(json)) => Profile::parse(&json).unwrap_or_else(|e| {
                error = Some(e);
                Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
            }),
            Ok(None) => Profile::parse(BUNDLED_PROFILE).expect("bundled profile"),
            Err(e) => {
                error = Some(e);
                Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
            }
        };
        let preferences = match storage_read("keybind.preferences.v1") {
            Ok(Some(json)) => Preferences::parse(&json).unwrap_or_else(|e| {
                error = Some(e);
                Preferences::default()
            }),
            Ok(None) => Preferences::default(),
            Err(e) => {
                error = Some(e);
                Preferences::default()
            }
        };
        let remote = endpoint.is_some();
        let settings = HostSettings {
            hotkeys: preferences.hotkeys,
            ..Default::default()
        };
        Self {
            data: FrameData {
                state: State::default(),
                profile,
                settings,
                preferences,
                native: false,
                remote,
                recovery_available: false,
                hud: false,
                companion_url: None,
                browser_connection: None,
                error,
            },
            tracker: InputTracker::default(),
            bridge_base: endpoint
                .as_ref()
                .map(|e| e.base_url.clone())
                .unwrap_or_default(),
            bridge: endpoint.map(|e| BridgeClient::new(e.session)),
            context: None,
            busy: false,
            pending_mode: None,
            last_poll: 0.0,
            paused: false,
            generation: 0,
            freshness: InputFreshness::default(),
            hid: None,
            hid_input: None,
            hid_received: None,
            hid_error: None,
        }
    }
    fn repaint(&self) {
        if let Some(c) = &self.context {
            c.request_repaint();
        }
    }
    fn hid_report(&mut self, id: u8, bytes: &[u8]) {
        if self.paused
            || page_hidden()
            || !self
                .data
                .browser_connection
                .as_ref()
                .is_some_and(|c| c.connected)
        {
            return;
        }
        match steam_hid::decode_report(id, bytes) {
            Ok(Some(frame)) => {
                let now = now_ms();
                let changed = self.hid_input.as_ref() != Some(&frame);
                self.hid_received = Some(now);
                self.hid_error = None;
                // Process every changed report immediately, including a press
                // and release occurring between two render/poll frames.
                if self.tracker.selected.as_deref() == Some(HID_DEVICE_ID)
                    && (changed || self.data.state.status != InputStatus::Live)
                {
                    self.data.state.sample_input(
                        HID_DEVICE_ID,
                        frame.clone(),
                        &self.data.profile,
                        now as u64,
                    );
                    self.repaint();
                }
                self.hid_input = Some(frame);
            }
            Ok(None) => {}
            Err(error) => {
                self.hid_input = None;
                self.hid_received = None;
                self.hid_error = Some(error.into());
                self.poll();
            }
        }
    }
    fn hid_status(&mut self, status: &str, message: String) {
        let Some(connection) = &mut self.data.browser_connection else {
            return;
        };
        connection.busy = matches!(status, "requesting" | "disconnecting");
        // Waiting for radio input still owns an open receiver connection and
        // must keep Disconnect available. Live requires a fresh input report.
        connection.connected = matches!(status, "connected" | "waiting");
        connection.message = message;
        self.hid_input = None;
        self.hid_received = None;
        self.hid_error = None;
        if connection.connected {
            self.tracker.select(Some(HID_DEVICE_ID.into()));
            self.data.settings.selected = Some(HID_DEVICE_ID.into());
        }
        if self.tracker.selected.as_deref() == Some(HID_DEVICE_ID) {
            self.data.state.unavailable(if status == "disconnected" {
                InputStatus::Disconnected
            } else {
                InputStatus::Unavailable
            });
        }
        self.poll();
        self.repaint();
    }
    fn poll(&mut self) {
        let mut result = (|| -> Result<Vec<Device>, String> {
            let pads = web_sys::window()
                .ok_or("No browser window")?
                .navigator()
                .get_gamepads()
                .map_err(|e| format!("Gamepad API blocked/unavailable: {}", js_error(e)))?;
            let mut devices = vec![];
            for value in pads.iter() {
                if value.is_null() || value.is_undefined() {
                    continue;
                }
                let pad: web_sys::Gamepad = value.dyn_into().map_err(js_error)?;
                if !pad.connected() {
                    continue;
                }
                let buttons = pad.buttons();
                let pressed = |i| {
                    buttons
                        .get(i)
                        .dyn_into::<web_sys::GamepadButton>()
                        .is_ok_and(|b| b.pressed())
                };
                let mut input = InputFrame::default();
                for (n, index) in [0, 1, 2, 3, 8, 9, 12, 15, 13, 14, 10, 11, 4, 5, 6, 7]
                    .into_iter()
                    .enumerate()
                {
                    input.buttons[n] = pressed(index);
                }
                for n in 0..2 {
                    input.triggers[n] = buttons
                        .get(6 + n as u32)
                        .dyn_into::<web_sys::GamepadButton>()
                        .map(|b| (b.value().clamp(0.0, 1.0) * 1000.0).round() as u16)
                        .unwrap_or(0);
                }
                let axes = pad.axes();
                for n in 0..2 {
                    let xy: Option<Vec<f64>> = (0..2)
                        .map(|a| {
                            axes.get((n * 2 + a) as u32)
                                .as_f64()
                                .filter(|v| v.is_finite())
                        })
                        .collect();
                    if let Some(xy) = xy {
                        for (a, v) in xy.into_iter().enumerate() {
                            InputChange::StickAxis(
                                n,
                                a,
                                (v.clamp(-1.0, 1.0) * 1000.0).round() as i16,
                            )
                            .apply(&mut input);
                        }
                    }
                }
                devices.push(Device {
                    input,
                    id: format!("{}:{}", pad.index(), pad.id()),
                    name: pad.id(),
                    standard: pad.mapping() == web_sys::GamepadMappingType::Standard,
                    held: [pressed(4), pressed(5)],
                });
            }
            Ok(devices)
        })();
        let hid_connected = self
            .data
            .browser_connection
            .as_ref()
            .is_some_and(|c| c.connected);
        if hid_connected {
            let input = self.hid_input.clone().unwrap_or_default();
            let device = Device {
                held: [input.down(Control::L1), input.down(Control::R1)],
                input,
                id: HID_DEVICE_ID.into(),
                name: "Steam Controller · WebHID".into(),
                standard: true,
            };
            match &mut result {
                Ok(devices) => devices.push(device),
                Err(_) => result = Ok(vec![device]),
            }
        }
        if self.tracker.selected.as_deref() == Some(HID_DEVICE_ID)
            && (!hid_connected
                || self
                    .hid_received
                    .is_none_or(|received| now_ms() - received > 1500.0))
        {
            let old = self.data.state.status.clone();
            self.data.state.unavailable(if hid_connected {
                InputStatus::Unavailable
            } else {
                InputStatus::Disconnected
            });
            if let Ok(devices) = result {
                self.data.settings.devices = devices;
            }
            let error = hid_connected.then(|| {
                self.hid_error.clone().unwrap_or_else(|| {
                    if self.hid_received.is_some() {
                        "Controller input stopped. Check the controller or receiver connection."
                    } else {
                        "Waiting for controller input…"
                    }
                    .into()
                })
            });
            if old != self.data.state.status || self.data.settings.error != error {
                self.data.settings.error = error;
                self.repaint();
            }
            return;
        }
        match result {
            Ok(devices) => {
                let recovered = self.data.settings.error.take().is_some();
                let now = web_sys::window()
                    .and_then(|w| w.performance())
                    .map(|p| p.now() as u64)
                    .unwrap_or(0);
                let changed = self.tracker.sample_timed(
                    &mut self.data.state,
                    &devices,
                    &[],
                    now,
                    &self.data.profile,
                );
                if changed || recovered || self.data.settings.devices != devices {
                    self.data.settings.devices = devices;
                    self.repaint();
                }
            }
            Err(e) => {
                if self.data.state.status != InputStatus::Unavailable
                    || self.data.settings.error.as_ref() != Some(&e)
                {
                    self.data.state.unavailable(InputStatus::Unavailable);
                    self.data.settings.error = Some(e);
                    self.repaint();
                }
            }
        }
    }
}
struct WebBackend(Rc<RefCell<WebState>>);
impl Backend for WebBackend {
    fn data(&self) -> FrameData {
        self.0.borrow().data.clone()
    }
    fn command(&mut self, command: Command) {
        // The JS permission request can synchronously notify Rust. Release the
        // state borrow before calling it, and preserve the button's activation.
        if matches!(
            command,
            Command::ConnectController | Command::DisconnectController
        ) {
            let hid = self.0.borrow().hid.clone();
            if let Some(hid) = hid {
                if matches!(command, Command::ConnectController) {
                    let _ = hid.connect();
                } else {
                    let _ = hid.disconnect();
                }
            }
            return;
        }
        let mut s = self.0.borrow_mut();
        match command {
            Command::Mode(mode) => {
                if s.bridge.is_some() {
                    s.pending_mode = Some(mode);
                } else {
                    s.data.state.select_mode(mode);
                }
            }
            Command::Select(id) if !s.data.remote => {
                s.tracker.select(id.clone());
                s.data.settings.selected = id;
                s.poll();
            }
            Command::Profile(json) if !s.data.remote => match Profile::parse(&json) {
                Ok(p) => {
                    s.data.profile = p;
                    s.data.state.gestures = Gestures::default();
                    s.data.error = storage_write("keybind.profile.v1", &json).err();
                }
                Err(e) => s.data.error = Some(e),
            },
            Command::Preferences(mut p) => {
                if s.data.remote {
                    p.hotkeys = s.data.settings.hotkeys;
                }
                match p.validate() {
                    Ok(()) => {
                        if !s.data.remote {
                            s.data.settings.hotkeys = p.hotkeys;
                        }
                        s.data.preferences = p.clone();
                        s.data.error = storage_write(
                            "keybind.preferences.v1",
                            &serde_json::to_string(&p).expect("preferences"),
                        )
                        .err();
                    }
                    Err(e) => s.data.error = Some(e),
                }
            }
            _ => {}
        }
        s.repaint();
    }
}
async fn fetch_snapshot(
    base: &str,
    token: &str,
    digest: &str,
    mode: Option<Mode>,
) -> Result<BridgeSnapshot, String> {
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
fn tick(shared: &Rc<RefCell<WebState>>) {
    let mut s = shared.borrow_mut();
    let hidden = web_sys::window()
        .and_then(|w| w.document())
        .is_none_or(|d| d.hidden());
    if hidden {
        if !s.paused {
            s.paused = true;
            s.generation += 1;
            s.data.state.unavailable(InputStatus::Paused);
            s.hid_input = None;
            s.hid_received = None;
            if let Some(b) = &mut s.bridge {
                b.disconnect();
            }
            s.repaint();
        }
        return;
    }
    if s.paused {
        s.paused = false;
        s.generation += 1;
    }
    if s.bridge.is_none() {
        s.poll();
        return;
    }
    // One request at a time; at most 30 Hz. Rendering only wakes on changed state.
    if s.freshness.expired(js_sys::Date::now()) && s.data.state.status == InputStatus::Live {
        s.data.state.unavailable(InputStatus::Unavailable);
        if let Some(b) = &mut s.bridge {
            b.disconnect();
        }
        s.data.error = Some("Companion input timed out".into());
        s.repaint();
    }
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
        if generation != s.generation
            || s.paused
            || web_sys::window()
                .and_then(|w| w.document())
                .is_none_or(|d| d.hidden())
        {
            return;
        }
        let result = result.and_then(|snap| s.bridge.as_mut().expect("remote").accept(snap));
        match result {
            Ok(changed) => {
                s.freshness.received(js_sys::Date::now());
                if changed {
                    let b = s.bridge.as_ref().expect("remote");
                    let state = b.state.clone();
                    let settings = b.settings.clone();
                    let profile = b.profile.clone();
                    s.data.state = state;
                    s.data.settings = settings;
                    if let Some(p) = profile {
                        s.data.profile = p;
                    }
                    s.data.error = None;
                    s.repaint();
                }
            }
            Err(e) => {
                let old = s.data.error.clone();
                s.bridge.as_mut().expect("remote").disconnect();
                s.data.state.unavailable(InputStatus::Unavailable);
                s.data.error = Some(format!("Companion disconnected: {e}"));
                if old != s.data.error {
                    s.repaint();
                }
            }
        }
    });
}
#[wasm_bindgen]
pub struct WebHandle {
    runner: eframe::WebRunner,
    timer: Option<i32>,
    callback: Option<Closure<dyn FnMut()>>,
    visibility: Option<Closure<dyn FnMut()>>,
    state: Option<Rc<RefCell<WebState>>>,
    hid_report: Option<HidReportCallback>,
    hid_status: Option<HidStatusCallback>,
}
#[wasm_bindgen]
impl WebHandle {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        Self {
            runner: eframe::WebRunner::new(),
            timer: None,
            callback: None,
            visibility: None,
            state: None,
            hid_report: None,
            hid_status: None,
        }
    }
    pub async fn start(&mut self, canvas: web_sys::HtmlCanvasElement) -> Result<(), JsValue> {
        let window = web_sys::window().ok_or("No browser window")?;
        let hash = window.location().hash()?;
        let endpoint =
            CompanionEndpoint::parse_fragment(&hash).map_err(|e| JsValue::from_str(&e))?;
        let shared = Rc::new(RefCell::new(WebState::new(endpoint)));
        self.state = Some(shared.clone());
        if !shared.borrow().data.remote {
            let weak = Rc::downgrade(&shared);
            let report = Closure::wrap(Box::new(move |id: u8, bytes: js_sys::Uint8Array| {
                if let Some(state) = weak.upgrade() {
                    state.borrow_mut().hid_report(id, &bytes.to_vec());
                }
            }) as Box<dyn FnMut(u8, js_sys::Uint8Array)>);
            let weak = Rc::downgrade(&shared);
            let status = Closure::wrap(Box::new(move |status: String, message: String| {
                if let Some(state) = weak.upgrade() {
                    state.borrow_mut().hid_status(&status, message);
                }
            }) as Box<dyn FnMut(String, String)>);
            let hid = SteamHid::new(
                report.as_ref().unchecked_ref(),
                status.as_ref().unchecked_ref(),
            );
            shared.borrow_mut().data.browser_connection = Some(BrowserConnection {
                available: hid.available(),
                busy: false,
                connected: false,
                message: hid.support_message(),
            });
            shared.borrow_mut().hid = Some(hid);
            self.hid_report = Some(report);
            self.hid_status = Some(status);
        }
        let for_app = shared.clone();
        self.runner
            .start(
                canvas,
                eframe::WebOptions::default(),
                Box::new(move |cc| {
                    for_app.borrow_mut().context = Some(cc.egui_ctx.clone());
                    Ok(Box::new(OverlayApp::new(cc, Box::new(WebBackend(for_app)))))
                }),
            )
            .await?;
        let for_visibility = shared.clone();
        let visibility = Closure::wrap(Box::new(move || tick(&for_visibility)) as Box<dyn FnMut()>);
        window
            .document()
            .ok_or("No document")?
            .add_event_listener_with_callback(
                "visibilitychange",
                visibility.as_ref().unchecked_ref(),
            )?;
        self.visibility = Some(visibility);
        let callback = Closure::wrap(Box::new(move || tick(&shared)) as Box<dyn FnMut()>);
        self.timer = Some(
            window.set_interval_with_callback_and_timeout_and_arguments_0(
                callback.as_ref().unchecked_ref(),
                16,
            )?,
        );
        self.callback = Some(callback);
        Ok(())
    }
    /// Read-only diagnostics used by input probes and packaged-browser tests.
    pub fn diagnostic_snapshot(&self) -> String {
        let Some(state) = &self.state else {
            return "null".into();
        };
        let s = state.borrow();
        let pad_previews: [Option<String>; 2] = std::array::from_fn(|side| {
            s.context
                .as_ref()
                .and_then(|c| c.data(|d| d.get_temp(egui::Id::new(format!("pad:{side}:preview")))))
        });
        let pad_feedback: [Option<String>; 2] = std::array::from_fn(|side| {
            s.context
                .as_ref()
                .and_then(|c| c.data(|d| d.get_temp(egui::Id::new(format!("pad:{side}:feedback")))))
        });
        serde_json::json!({"pad_feedback":pad_feedback,"pad_previews":pad_previews,"trackpads":s.data.state.control_page(&s.data.profile).and_then(|page|page.trackpads.as_ref()),"ui_targets":s.context.as_ref().and_then(|c|c.data(|d|d.get_temp::<std::collections::BTreeMap<String,[f32;2]>>(egui::Id::new("keybind.targets")))),"control_labels":s.data.state.control_labels(&s.data.profile),"input_status":s.data.input_status_label(),"controller_help":s.data.controller_help(),"browser_connection":s.data.browser_connection,"state":s.data.state,"labels":s.data.state.view(&s.data.profile).labels,"devices":s.data.settings.devices,"error":s.data.error.as_ref().or(s.data.settings.error.as_ref()),"remote":s.data.remote,"settings":s.data.settings,"preferences":s.data.display_preferences()}).to_string()
    }
    pub fn destroy(&mut self) {
        if let Some(state) = &self.state {
            let hid = state.borrow_mut().hid.take();
            if let Some(hid) = hid {
                let _ = hid.destroy();
            }
        }
        self.hid_report = None;
        self.hid_status = None;
        if let Some(timer) = self.timer.take()
            && let Some(w) = web_sys::window()
        {
            w.clear_interval_with_handle(timer);
        }
        self.callback = None;
        if let Some(callback) = self.visibility.take()
            && let Some(document) = web_sys::window().and_then(|w| w.document())
        {
            let _ = document.remove_event_listener_with_callback(
                "visibilitychange",
                callback.as_ref().unchecked_ref(),
            );
        }
        if let Some(state) = &self.state {
            let mut s = state.borrow_mut();
            s.paused = true;
            s.generation += 1;
            s.context = None;
        }
        self.runner.destroy();
    }
}
impl Default for WebHandle {
    fn default() -> Self {
        Self::new()
    }
}
impl Drop for WebHandle {
    fn drop(&mut self) {
        self.destroy();
    }
}
