//! Executable, release-derived browser layout demonstration.
#[cfg(all(test, target_arch = "wasm32"))]
wasm_bindgen_test::wasm_bindgen_test_configure!(run_in_browser);
mod activators;
mod analog;
#[cfg(test)]
mod analog_tests;
mod commands;
#[cfg(test)]
mod coverage_tests;
mod data;
mod engine;
mod gyro;
mod input;
#[cfg(test)]
mod lifecycle_tests;
mod output;
#[cfg(test)]
mod parity_tests;
pub(crate) mod presentation;
mod resolve;
mod session;
#[cfg(test)]
mod tests;

pub(crate) use analog::Surface;
pub use data::{Catalog, Layout};
pub(crate) use data::{Condition, Entry, Operation, Settings};
pub use engine::Engine;
pub(crate) use engine::{Act, Binding, Phase};
pub(crate) use gyro::Gyro;
pub use input::Input;
pub(crate) use output::Output;
pub use session::Session;
