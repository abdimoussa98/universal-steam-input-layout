# Keybind viewer

A Windows binding overlay and a browser viewer built from the same Rust state
machine, profiles and egui interface. The browser is a normal page, suitable
for a second monitor; it is not a desktop overlay.

This is an initial implementation. Automated behavior tests and browser tests
are recorded in `../findings/2026-10-15-keybind-overlay/README.md`. Windows
controller visibility under Steam Input, HUD behavior and resource usage still
need the hardware acceptance checks below. macOS supports a headless controller
companion for the browser viewer, without Steam. Native Linux is not supported.

## Use

Select **Settings → Controller**, choosing the physical controller rather than
Steam's remapped virtual controller. In a browser, press a controller button
first if the device list is empty. Only standard browser Gamepad mappings are
accepted. Native reconnect uses a unique hardware serial identity when available,
falling back to the device path. macOS device paths can change on reconnect.
Otherwise reselect the controller if its instance ID changed.

Select **Base / Gyro**, **Steering** or **Menu**, using the buttons or F1/F2/F3.
The mode is a manual reference selection; it does not change Steam's mode.
The diagram shows face buttons, Start/Select, all four D-pad directions, both
stick clicks, bumpers and triggers. Pressed controls light up; trigger bars show
physical travel. The Ibex-shaped diagram uses symmetric sticks and tilted
trackpads. Stick rings show deflection, turning green with capacitive thumb
contact; trackpad dots show actual contact coordinates. Standard browser Gamepad
input has stick axes but no pad/touch data; use the companion for those markers.
System buttons remain visual orientation cues.
Labels describe a fresh press in the inferred context, including
its timed-gesture phase. They do not describe keys already held in the game. F4 is unassigned.

One central timer follows the active L1, R1, Select or Start gesture. It names
**Hold / Tap, then hold**, and also shows the separate single Tap output where
one is configured. The same bar switches between the Initial hold deadline,
Release window and Second hold cover countdown. The last gesture
stays visible as a reference when idle. Combined bumpers share one timer. For the bundled
profile, the initial release deadline is 200 ms. Releasing early opens a 150 ms
second-press window, with the expected scroll (or Escape/Tab) at 50 ms. Pressing
again cancels the pending window and starts a separate 150 ms countdown for the
Second hold cover. Releasing before that cover reopens the window; releasing after cover
ends the gesture. Event notes remain visible after the window closes. Steering
bumpers are direct S/W bindings and have no bumper tap countdown.
See the [timed-gesture vocabulary](../resources/Layout%20Vocabulary.md#timed-gestures)
for the gesture sequence and the difference between a single Tap and Tap, then hold.

Durations and phase-specific labels are exported from the layout. These are
configured expectations, not observed Steam outputs. Modifier use cancels its
tap; native Steam Controller stick-touch release can complete a hold early or
cancel a pending window. Tracking that starts while a button is held waits for
release before recognizing a gesture. Reconnect, mode/profile changes and input
suspension reset pending timers.

Steering now follows left-stick up/down while exactly one bumper is held,
including the inherited face/D-pad and L3/R3 bindings. Up exposes Mouse back /
Mouse forward clicks; down exposes Caps Lock / Mouse middle. Tap Cover preserves
that modifier's inherited clicks. Centering, reversing direction, both bumpers,
and the release/second-press windows update the reference and shared timer.
Thresholds and timings come from the exported layout. Manual mode selection
still applies when a physical gesture changes Steam's stateful mode.

The bumper model also recognizes both sticks deflected as a Tap Cover gesture.
Trackpad interactions and combined menu/state-changing gestures can make timing
uncertain until controls are released. Known inherited modifier bindings remain
visible during that uncertainty; releasing the owner restores the base reference.
A temporary gyro cover that removes itself on a fresh button press shows the
binding that press exposes underneath, rather than an empty label. Select the mode manually if a gesture changed it. Standard
browser Gamepad input cannot report capacitive stick touch, so its timing can
differ from the native helper. Trigger pressure has no activation marker when
the layout does not explicitly specify a threshold.

Windows shortcuts are global and reserved while the app runs. Change them to
three distinct F1–F12 keys in Settings if they conflict with a game or another
app. Conflicts are shown; the mode buttons keep working. Standalone browser
shortcuts need page focus, and the browser may reserve some keys.

For a Windows overlay, position the interactive window, then choose **Enter
click-through HUD**. **Ctrl+Alt+O** restores the interactive window. HUD and
hide controls are disabled if that recovery shortcut cannot register. Use
windowed or borderless games; exclusive fullscreen is not supported. Size and
background opacity are adjustable. Each launch uses a fresh window position
rather than restoring a potentially offscreen position from another monitor.

The bundled profile is the **Ibex 1.0 default** layout: L1/R1 modifiers. It is
compiled into both targets, with its source SHA-256. This does not establish
physical controller compatibility. Alternative L2/R2 profiles are explicitly
rejected until trigger threshold/hysteresis behavior is implemented. Import a
validated profile by dropping its JSON file on the window or pasting it in
Settings. An invalid replacement retains the current profile.

Windows stores preferences and the imported profile in `%APPDATA%\KeybindOverlay`.
The browser uses local storage; unavailable storage reports an error while
in-memory changes remain usable. Modes and held buttons are not persisted.

## Build Windows

Install Rust with the MSVC toolchain, Visual Studio C++ build tools and CMake.
The tested development toolchain is Rust 1.99.0; `Cargo.lock` pins dependencies.
SDL3 is compiled from source and linked statically. Run from the repository root:

```powershell
cargo test --locked --manifest-path overlay/Cargo.toml --features desktop
cargo run --locked --manifest-path overlay/Cargo.toml --features desktop
# Release with a static MSVC CRT:
$env:RUSTFLAGS = '-C target-feature=+crt-static'
cargo build --locked --manifest-path overlay/Cargo.toml --release --features desktop
python overlay/scripts/package_windows.py
```

The executable is `overlay/target/release/keybind-overlay.exe`. The packaging
script produces `overlay/windows-bundle/`, including the source profile and
dependency license notices. CI builds this separately from the Steam layout ZIP.
A clean Windows machine smoke test is still required before calling it portable.

Input probe (run on the Windows PC with Steam and a game active):

```powershell
.\keybind-overlay.exe --diagnostic
.\keybind-overlay.exe --diagnostic --device 1
.\keybind-overlay.exe --profile profiles\ibex-1.0-default.json
```

The diagnostic prints SDL device names, instance IDs, device paths/types and
changed L1/R1 samples. It does not prove that a device is physical just because
SDL calls it a gamepad. Compare its output to real presses while the game has
focus. If Steam exposes only remapped outputs, the hardware gate fails; the
browser companion cannot fix missing native input.

## Build the browser viewer

```sh
rustup target add wasm32-unknown-unknown
cargo install wasm-pack --version 0.13.1 --locked
python3 overlay/scripts/build_web.py
python3 -m http.server 8080 --bind 127.0.0.1 --directory overlay/dist
```

Open `http://127.0.0.1:8080`. `overlay/dist/` is a static bundle for HTTPS hosting
or localhost; opening `index.html` directly with a `file:` URL is unsupported.
Assets use relative URLs, so a subdirectory deployment works. No hosting or
publication has been performed. Rust optimizes the WASM; wasm-pack's older
optional wasm-opt step is disabled because it rejects current bulk-memory output.

To host with Dockge, see the [container guide](deploy/README.md) and
[Compose example](deploy/compose.yaml). Relevant pushes to `main` build
and publish the web image to GHCR. Dockge pulls the `:latest` image when you
deploy or update the stack. Your HTTPS tunnel forwards to port 18091.

Standalone browser input works only for controllers the browser exposes. A
visible second-monitor page and a hidden tab are different cases. Hidden pages
pause input; resume samples current buttons before displaying live state.

## Optional Windows companion

Build the web bundle above, copy its contents into `web/` beside the executable,
then run:

```powershell
.\keybind-overlay.exe --companion web
```

Open the link printed in the console or shown in Settings. It uses a random
loopback port and a session token in the URL fragment. The same web bundle now
reads the Windows controller and mode state, including global shortcuts. Browser
mode buttons send acknowledged commands to the companion. It never mixes native
input with local browser Gamepad input. Controller/profile/shortcut settings
are read-only in the browser while connected; configure them in the native app.
Size remains a browser-local setting.

Choose **Hide window · use browser only** to stop native rendering while native
input continues. Ctrl+Alt+O restores the settings window. Closing the Windows
app stops the companion. Restarting it creates a new link; reopen that link.
Interrupted input clears held indicators and displays an unavailable state.

The server binds to `127.0.0.1`, checks Host/Origin/session, permits only known
web assets and state/mode endpoints, and exposes no generic file or input APIs.
It polls snapshots at most 30 times per second when visible, sends profiles only
when needed, and redraws on changes. Suspended browser tabs cannot be forced to
render by a native companion.

## macOS companion (Steam not required)

For a hosted HTTPS viewer, start the helper with
`keybind-overlay --viewer-url https://YOUR_VIEWER_HOSTNAME/` and open its
printed pairing link in the browser on the same computer. The helper reads
your Steam Controller locally while the page loads from your server. Allow local
network access if prompted. No local web bundle is needed in this mode.
See [hosted pairing and troubleshooting](deploy/README.md#steam-controller-in-the-hosted-browser).

Some controllers, including the wired Steam Controller tested here, expose
keyboard/mouse and vendor-specific USB interfaces rather than a standard browser
gamepad. A binding profile cannot add browser hardware support. The macOS helper
reads physical input through SDL's Steam Controller HID driver and serves the
same web viewer using the existing companion protocol. Steam is not required.

Install Rust and CMake, build the web bundle above, then run from the repo root:

```sh
cargo build --locked --manifest-path overlay/Cargo.toml --release --features desktop
./overlay/target/release/keybind-overlay --companion overlay/dist
```

Open the **new URL printed by the helper**, including its `#companion=` fragment.
The ordinary static-server URL still uses browser-only input. Keep the helper
running while using the viewer; Ctrl+C stops it. This is a browser viewer, with
no native macOS overlay or global keyboard hooks. Mode buttons and F1/F2/F3 work
when the browser page has focus (browser-reserved keys may need its buttons).

The helper selects the sole connected controller and restores it on reconnect
only if its unique hardware serial identity (or fallback device path) matches.
Serials are hashed internally and are not sent to the browser. It never switches to a different pad
after a disconnect. With multiple controllers, restart with `--device SDL_ID`
using an ID printed in the console. Use `--diagnostic` to print L1/R1 changes,
and `--profile FILE` to load a different validated display profile. The helper
does not persist preferences; appearance remains local to the browser.

## Profile generation

The exporter is deliberately limited to the reviewed default Ibex family.
It resolves all sixteen controls through the existing layout model, compares
Base/Gyro and both combined-modifier press orders, and exports single-owner
gesture pages and timing recipes. Unsupported constructs are reported.
Its report records ignored layer operations and the reference assumptions.
It does not change layout JSON, VDF or version snapshots.

```sh
python3 -m unittest tests.test_overlay_profile
python3 -m tools.export_overlay_profile \
  versions/ibex/1.0/ibex_single-set-default_hold-gyro_1.0.json \
  --controller ibex --version 1.0 --output overlay/profiles/ibex-1.0-default.json
```

Schema 2 adds complete sixteen-control pages, gesture recipes, trigger threshold
metadata and validation. Older schema 1 profiles remain loadable, with the added
controls and timing explicitly unavailable. Schema 1 requires twelve explicit
mode/context entries, four bindings each in
south/east/west/north order. Binding kinds are `label`, `unbound`, `unavailable`
(with a reason), and `inherit` (only from that mode's unmodified context).
Missing contexts, duplicates, unknown fields and unsupported modifiers fail
validation. See `tests/fixtures/profile.json` for a small independent fixture.
Do not use the exporter for an arbitrary layout without reviewing its stacks.

## Tests and architecture

```sh
cargo test --locked --manifest-path overlay/Cargo.toml --no-default-features
cargo fmt --manifest-path overlay/Cargo.toml -- --check
cargo clippy --locked --manifest-path overlay/Cargo.toml --all-targets --features desktop -- -D warnings
cargo test --locked --manifest-path overlay/Cargo.toml --features desktop
cargo check --locked --manifest-path overlay/Cargo.toml --target wasm32-unknown-unknown --features web
wasm-pack test --headless --chrome overlay --no-default-features
wasm-pack test --headless --firefox overlay --no-default-features
python3 overlay/scripts/browser_smoke.py --bundle overlay/dist
```

Browser tests need Chrome/ChromeDriver or Firefox/GeckoDriver. The smoke script
accepts `--driver PATH`, `--browser-binary PATH` and `--screenshot PATH`; it uses
a temporary browser profile. `WASM_BINDGEN_TEST_WEBDRIVER_JSON` can supply custom
browser paths for wasm-pack. Build before the packaged-browser smoke test.
The same `tests/behavior.rs` and `tests/gestures.rs` bodies run natively and in WASM. Companion HTTP
integration tests run on native hosts without Windows input hardware. On Linux,
compiling the optional native UI also requires the platform GUI dependencies;
The viewer pipeline builds Windows/macOS helpers and the web image; tests,
formatting checks and Clippy run locally using the commands above.

- `src/core/`: state, profiles, monotonic gesture timing, hotkey lifecycle and protocol validation.
- `src/ui.rs`: the one diagram/settings interface used by both entry points.
- `src/platform/native.rs`: Windows hotkeys and overlay lifecycle.
- `src/platform/sdl_input.rs`: shared Windows/macOS main-thread SDL input.
- `src/platform/macos.rs`: headless direct-input companion, without Steam.
- `src/platform/web.rs`: Gamepad polling, browser storage and companion client.
- `src/platform/host.rs`, `server.rs`: host state and opt-in loopback transport.
- `web/`: minimal canvas/startup shell; no duplicated binding logic.

SDL preserves timestamped button edges and samples every 8 ms on the main thread; Windows eframe runs on a separate
supported Windows event loop. Unchanged input does not wake the UI. Repaint and
polling are separate, but no measured CPU/memory/latency guarantees are made yet.
The browser polls Gamepad snapshots every 16 ms while visible; it also repaints
for changes, active countdowns or UI interaction. In companion mode, the host
owns the gesture clock; browser animation never advances host gesture state. `window.keybindApp.diagnostic_snapshot()`
returns a read-only semantic snapshot for diagnostics and smoke tests.

## Hardware acceptance still required

Record Windows version, PC, GPU, controller model/connection, SDL device identity,
Steam/game, browser version and focus/visibility for each run. Verify both
press/release orders, held-at-start, reconnect-held, device switching,
suspend/resume, shortcut conflicts, HUD recovery, DPI and multiple monitors.
Verify browser focus loss separately from hidden-tab resume, and companion
mode while the game has focus. Measure CPU, working set, GPU, input-to-label
latency, startup/download size and hidden-window rendering. Set numeric budgets
from that diagnostic baseline before calling this release lightweight or ready.
