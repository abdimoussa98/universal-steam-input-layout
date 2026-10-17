use super::{WebState, now_ms, page_hidden};
use crate::core::{Control, Device, InputStatus, steam_hid};
use crate::ui::BrowserConnection;
use std::{cell::RefCell, rc::Rc};
use wasm_bindgen::{JsCast, prelude::*};

mod gamepad;

const HID_DEVICE_ID: &str = "webhid:steam-controller-usb";

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = window, js_name = SteamHid)]
    #[derive(Clone)]
    pub(super) type SteamHid;
    #[wasm_bindgen(constructor, js_namespace = window)]
    fn new(on_input: &js_sys::Function, on_state: &js_sys::Function) -> SteamHid;
    #[wasm_bindgen(method, getter)]
    fn available(this: &SteamHid) -> bool;
    #[wasm_bindgen(method, getter, js_name = supportMessage)]
    fn support_message(this: &SteamHid) -> String;
    #[wasm_bindgen(method)]
    pub(super) fn connect(this: &SteamHid) -> js_sys::Promise;
    #[wasm_bindgen(method)]
    pub(super) fn disconnect(this: &SteamHid) -> js_sys::Promise;
    #[wasm_bindgen(method)]
    pub(super) fn destroy(this: &SteamHid) -> js_sys::Promise;
}

pub(super) type HidReportCallback = Closure<dyn FnMut(u8, js_sys::Uint8Array)>;
pub(super) type HidStatusCallback = Closure<dyn FnMut(String, String)>;

pub(super) fn attach_hid(shared: &Rc<RefCell<WebState>>) -> (HidReportCallback, HidStatusCallback) {
    let weak = Rc::downgrade(shared);
    let report = Closure::wrap(Box::new(move |id: u8, bytes: js_sys::Uint8Array| {
        if let Some(state) = weak.upgrade() {
            state.borrow_mut().hid_report(id, &bytes.to_vec());
        }
    }) as Box<dyn FnMut(u8, js_sys::Uint8Array)>);
    let weak = Rc::downgrade(shared);
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
    (report, status)
}

impl WebState {
    fn hid_connected(&self) -> bool {
        self.data
            .browser_connection
            .as_ref()
            .is_some_and(|c| c.connected)
    }

    fn hid_report(&mut self, id: u8, bytes: &[u8]) {
        if self.paused || page_hidden() || !self.hid_connected() {
            return;
        }
        match steam_hid::decode_report(id, bytes) {
            Ok(Some(frame)) => {
                let now = now_ms();
                let changed = self.hid_input.as_ref() != Some(&frame);
                if changed {
                    if self.samples.len() >= 1024 {
                        self.samples.clear();
                    }
                    self.samples
                        .push_back((HID_DEVICE_ID.into(), now, frame.clone()));
                }
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

    fn hid_device(&self) -> Device {
        let input = self.hid_input.clone().unwrap_or_default();
        Device {
            held: [input.down(Control::L1), input.down(Control::R1)],
            input,
            id: HID_DEVICE_ID.into(),
            name: if self
                .data
                .browser_connection
                .as_ref()
                .is_some_and(|c| c.message.starts_with("Steam Deck connected"))
            {
                "Steam Deck · WebHID"
            } else {
                "Steam Controller · WebHID"
            }
            .into(),
            standard: true,
        }
    }

    pub(super) fn poll(&mut self) {
        let mut result = gamepad::devices();
        let hid_connected = self.hid_connected();
        if hid_connected {
            let device = self.hid_device();
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
            self.hid_unavailable(hid_connected, result);
            return;
        }
        self.sample_devices(result);
    }

    fn hid_unavailable(&mut self, connected: bool, result: Result<Vec<Device>, String>) {
        let old = self.data.state.status.clone();
        self.data.state.unavailable(if connected {
            InputStatus::Unavailable
        } else {
            InputStatus::Disconnected
        });
        if let Ok(devices) = result {
            self.data.settings.devices = devices;
        }
        let error = connected.then(|| {
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
    }

    fn sample_devices(&mut self, result: Result<Vec<Device>, String>) {
        match result {
            Ok(devices) => {
                let recovered = self.data.settings.error.take().is_some();
                let changed = self.tracker.sample_timed(
                    &mut self.data.state,
                    &devices,
                    &[],
                    now_ms() as u64,
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
