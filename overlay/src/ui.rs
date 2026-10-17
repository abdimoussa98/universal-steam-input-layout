//! One interface used by both native eframe and WebRunner.
mod app;
mod backend;
mod controller;
mod diagnostics;
mod labels;
mod mouse;
mod panels;
mod preview;
mod settings;
mod theme;
mod timelines;
mod trackpads;

use crate::core::*;
pub use app::OverlayApp;
pub use backend::{Backend, BrowserConnection, Command, FrameData};
use diagnostics::{target, target_point};
use eframe::egui::{self, Color32, RichText};
use labels::{compact_binding, gesture_binding, recipe_binding, timed_gesture_outcomes};

const BACKGROUND: Color32 = Color32::from_rgb(17, 19, 23);
const SURFACE: Color32 = Color32::from_rgb(24, 27, 32);
const BORDER: Color32 = Color32::from_rgb(44, 49, 57);
const MUTED: Color32 = Color32::from_rgb(156, 164, 177);
const ACCENT: Color32 = Color32::from_rgb(125, 211, 184);
