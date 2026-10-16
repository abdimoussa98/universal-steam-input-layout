//! Shared native host state; independent of Windows input APIs.
use crate::{core::*, ui::*};
use eframe::egui;
use std::path::PathBuf;

pub struct Hub {
    pub data: FrameData,
    pub sequence: u64,
    pub context: Option<egui::Context>,
    pub hidden: bool,
    pub settings_dir: PathBuf,
    pub digest: String,
}
impl Hub {
    pub fn new(data: FrameData, settings_dir: PathBuf) -> Self {
        let digest = data.profile.digest();
        Self {
            data,
            settings_dir,
            digest,
            sequence: 1,
            context: None,
            hidden: false,
        }
    }
    pub fn changed(&mut self) {
        self.sequence += 1;
        if !self.hidden
            && let Some(ctx) = &self.context
        {
            ctx.request_repaint();
        }
    }
    pub fn window(&mut self, hud: bool, hidden: bool) {
        if (hud || hidden) && !can_enter_hud(self.data.recovery_available) {
            return;
        }
        self.data.hud = hud;
        self.hidden = hidden;
        if let Some(ctx) = &self.context {
            ctx.send_viewport_cmd(egui::ViewportCommand::MousePassthrough(hud));
            ctx.send_viewport_cmd(egui::ViewportCommand::Decorations(!hud));
            ctx.send_viewport_cmd(egui::ViewportCommand::WindowLevel(if hud {
                egui::WindowLevel::AlwaysOnTop
            } else {
                egui::WindowLevel::Normal
            }));
            ctx.send_viewport_cmd(egui::ViewportCommand::Visible(!hidden));
            if !hud && !hidden {
                ctx.send_viewport_cmd(egui::ViewportCommand::Minimized(false));
            }
            ctx.request_repaint();
        }
        self.changed();
    }
    pub fn snapshot(&self, session: &str, known_digest: &str) -> BridgeSnapshot {
        BridgeSnapshot {
            version: 1,
            session: session.into(),
            sequence: self.sequence,
            state: self.data.state.clone(),
            profile_digest: self.digest.clone(),
            profile: if self.digest == known_digest {
                None
            } else {
                Some(self.data.profile.clone())
            },
            settings: self.data.settings.clone(),
        }
    }
    pub fn persist(&self, name: &str, json: &str) -> Result<(), String> {
        std::fs::create_dir_all(&self.settings_dir).map_err(|e| e.to_string())?;
        // Write first; never truncate the previous usable file on an encoding failure.
        let temporary = self.settings_dir.join(format!("{name}.tmp"));
        std::fs::write(&temporary, json).map_err(|e| e.to_string())?;
        std::fs::rename(temporary, self.settings_dir.join(name)).map_err(|e| e.to_string())
    }
    pub fn import(&mut self, json: String) {
        match Profile::parse(&json) {
            Ok(p) => {
                self.digest = p.digest();
                self.data.profile = p;
                self.data.state.gestures = Gestures::default();
                self.data.error = self.persist("profile.json", &json).err();
            }
            Err(e) => self.data.error = Some(format!("Profile not loaded: {e}")),
        }
    }
}
