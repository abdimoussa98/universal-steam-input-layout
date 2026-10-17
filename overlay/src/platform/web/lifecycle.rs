use super::backend::WebBackend;
use super::input::{HidReportCallback, HidStatusCallback};
use super::{WebState, companion, diagnostics, input, page_hidden};
use crate::core::{CompanionEndpoint, InputStatus};
use crate::ui::OverlayApp;
use std::{cell::RefCell, rc::Rc};
use wasm_bindgen::{JsCast, prelude::*};

fn tick(shared: &Rc<RefCell<WebState>>) {
    let mut s = shared.borrow_mut();
    if page_hidden() {
        if !s.paused {
            s.paused = true;
            s.generation += 1;
            s.data.state.unavailable(InputStatus::Paused);
            s.hid_input = None;
            s.hid_received = None;
            if let Some(bridge) = &mut s.bridge {
                bridge.disconnect();
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
    drop(s);
    companion::poll(shared);
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
            let (report, status) = input::attach_hid(&shared);
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
        self.start_timer(&window, shared)
    }

    /// Read-only diagnostics used by input probes and packaged-browser tests.
    pub fn diagnostic_snapshot(&self) -> String {
        self.state
            .as_ref()
            .map(|state| diagnostics::snapshot(&state.borrow()))
            .unwrap_or_else(|| "null".into())
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

impl WebHandle {
    fn start_timer(
        &mut self,
        window: &web_sys::Window,
        shared: Rc<RefCell<WebState>>,
    ) -> Result<(), JsValue> {
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
