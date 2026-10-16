pub mod core;
pub mod platform;
#[cfg(feature = "ui")]
pub mod ui;
pub const BUNDLED_PROFILE: &str = include_str!("../profiles/ibex-1.0-default.json");
