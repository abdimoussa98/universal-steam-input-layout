use super::{WebState, storage};
use crate::core::{Gestures, Preferences, Profile};
use crate::ui::{Backend, Command, FrameData};
use std::{cell::RefCell, rc::Rc};
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = window, js_name = openLayoutDownloads)]
    fn open_layout_downloads();
}

pub(super) struct WebBackend(pub(super) Rc<RefCell<WebState>>);

impl Backend for WebBackend {
    fn input_epoch(&self) -> u64 {
        self.0.borrow().generation
    }
    fn input_blocked(&self) -> bool {
        web_sys::window()
            .and_then(|w| w.document())
            .and_then(|d| d.get_element_by_id("downloads"))
            .is_some_and(|e| {
                js_sys::Reflect::get(&e, &JsValue::from_str("open"))
                    .ok()
                    .and_then(|v| v.as_bool())
                    == Some(true)
            })
    }
    fn input_samples(&mut self) -> Vec<(String, f64, crate::core::InputFrame)> {
        self.0.borrow_mut().samples.drain(..).collect()
    }
    fn data(&self) -> FrameData {
        self.0.borrow().data.clone()
    }

    fn command(&mut self, command: Command) {
        if matches!(command, Command::DownloadLayouts) {
            open_layout_downloads();
            return;
        }
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
        s.apply_command(command);
        s.repaint();
    }
}

impl WebState {
    fn apply_command(&mut self, command: Command) {
        match command {
            Command::TimingScale(scale) => {
                self.data.state.set_timing_scale(scale);
                if self.data.remote {
                    self.remote_timing_scale = Some(scale.clamp(1, 10));
                }
            }
            Command::Mode(mode) => {
                if self.bridge.is_some() {
                    self.pending_mode = Some(mode);
                } else {
                    self.data.state.select_mode(mode);
                }
            }
            Command::Select(id) if !self.data.remote => {
                self.tracker.select(id.clone());
                self.data.settings.selected = id;
                self.poll();
            }
            Command::Profile(json) if !self.data.remote => self.set_profile(json),
            Command::Preferences(preferences) => self.set_preferences(preferences),
            _ => {}
        }
    }

    fn set_profile(&mut self, json: String) {
        match Profile::parse(&json) {
            Ok(profile) => {
                self.data.profile = profile;
                self.data.state.gestures = Gestures::default();
                self.data.error = storage::write(storage::PROFILE_KEY, &json).err();
            }
            Err(error) => self.data.error = Some(error),
        }
    }

    fn set_preferences(&mut self, mut preferences: Preferences) {
        if self.data.remote {
            preferences.hotkeys = self.data.settings.hotkeys;
        }
        match preferences.validate() {
            Ok(()) => {
                if !self.data.remote {
                    self.data.settings.hotkeys = preferences.hotkeys;
                }
                self.data.preferences = preferences.clone();
                self.data.error = storage::write(
                    storage::PREFERENCES_KEY,
                    &serde_json::to_string(&preferences).expect("preferences"),
                )
                .err();
            }
            Err(error) => self.data.error = Some(error),
        }
    }
}
