pub mod core;
pub mod demo;
#[cfg(feature = "ui")]
pub mod demo_ui;
pub mod platform;
#[cfg(feature = "ui")]
pub mod ui;
pub const BUNDLED_PROFILE: &str = include_str!("../profiles/ibex-1.0-default.json");
