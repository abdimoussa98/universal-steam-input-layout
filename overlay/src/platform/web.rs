use crate::core::*;
use crate::ui::FrameData;
use eframe::egui;
use wasm_bindgen::{JsCast, JsValue};

mod backend;
mod companion;
mod diagnostics;
mod input;
mod lifecycle;
mod storage;

pub use lifecycle::WebHandle;

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
    hid: Option<input::SteamHid>,
    hid_input: Option<InputFrame>,
    hid_received: Option<f64>,
    hid_error: Option<String>,
    remote_timing_scale: Option<u8>,
    samples: std::collections::VecDeque<(String, f64, InputFrame)>,
}

impl WebState {
    fn new(endpoint: Option<CompanionEndpoint>) -> Self {
        Self {
            data: storage::load_frame_data(endpoint.is_some()),
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
            remote_timing_scale: None,
            samples: std::collections::VecDeque::new(),
        }
    }

    fn repaint(&self) {
        if let Some(c) = &self.context {
            c.request_repaint();
        }
    }
}

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

fn js_error(e: JsValue) -> String {
    e.as_string()
        .or_else(|| {
            e.dyn_ref::<js_sys::Error>()
                .map(|e| String::from(e.message()))
        })
        .unwrap_or_else(|| format!("{e:?}"))
}
