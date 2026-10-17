use super::*;

pub(super) struct NativeBackend(pub(super) Arc<Mutex<Hub>>);
impl Backend for NativeBackend {
    fn data(&self) -> FrameData {
        self.0.lock().expect("hub").data.clone()
    }
    fn command(&mut self, command: Command) {
        let mut h = self.0.lock().expect("hub");
        match command {
            Command::TimingScale(scale) => h.data.state.set_timing_scale(scale),
            Command::Mode(mode) => {
                h.data.state.select_mode(mode);
            }
            Command::Select(id) => {
                h.data.settings.selected = id;
                h.data.state.unavailable(InputStatus::SelectDevice);
            }
            Command::Profile(json) => h.import(json),
            Command::ImportPath(path) => match std::fs::read_to_string(path) {
                Ok(json) => h.import(json),
                Err(e) => h.data.error = Some(e.to_string()),
            },
            Command::Preferences(p) => match p.validate() {
                Ok(()) => {
                    h.data.preferences = p.clone();
                    h.data.settings.hotkeys = p.hotkeys;
                    h.data.error = h
                        .persist(
                            "preferences.json",
                            &serde_json::to_string(&p).expect("preferences"),
                        )
                        .err();
                }
                Err(e) => h.data.error = Some(e),
            },
            Command::Hud(hud) => h.window(hud, false),
            Command::Hide => h.window(false, true),
            Command::ConnectController
            | Command::DisconnectController
            | Command::DownloadLayouts => {}
        }
        h.changed();
    }
}
