#[cfg(windows)]
fn main() {
    if let Err(error) = keybind_overlay::platform::macos::run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
#[cfg(target_os = "macos")]
fn main() {
    if let Err(error) = keybind_overlay::platform::macos::run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
#[cfg(not(any(windows, target_os = "macos")))]
fn main() {
    eprintln!(
        "The native adapter currently supports Windows. Build the web target for this platform."
    );
    std::process::exit(1);
}
