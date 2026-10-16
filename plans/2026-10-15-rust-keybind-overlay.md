# Plan for a Rust keybind overlay and web companion

**Status, 2026-10-15: first implementation available; Windows hardware and
release acceptance remain pending.**

Implementation: [app and run instructions](../overlay/README.md).
Evidence: [TDD, browser checks and remaining gates](../findings/2026-10-15-keybind-overlay/README.md).
The shared core/UI, Windows adapter/HUD, standalone browser, optional companion,
Ibex default profile exporter and packaging/CI definitions are implemented.
The static web artifact was built and tested. Windows code was type-checked;
a Windows release was not linked or run on the macOS development host.
Milestone exit conditions requiring Windows/physical controller measurements
remain open. The original acceptance checklist below is retained; this status
does not treat synthetic tests as hardware validation.

Build a small companion that shows the bindings for a manually selected mode
and the controller modifiers currently held. Compile the same Rust behavior,
profiles and egui interface into a Windows application and a WebAssembly
browser application. The Windows build provides a normal window and an
optional transparent overlay; the web build provides the same binding display
in a browser. Keep platform differences in small adapters rather than
maintaining two applications.

Develop behavior through test-driven development: write a failing behavioral
test, implement the smallest change that passes, then refactor while the
tests stay green. Run the same behavioral fixtures against native and
WebAssembly builds.

## Product behavior

The user chooses the display mode independently of Steam Input:

| Mode | Initial shortcut | Display |
|---|---|---|
| Base / Gyro | F1 | Base and gyro binding reference |
| Steering | F2 | Steering binding reference |
| Menu | F3 | Menu binding reference |

Both builds have the same three clickable mode buttons. Shortcuts are
configurable; F4 remains unassigned. Native shortcuts work while a game has
focus. Standalone browser shortcuts work only while the page receives keyboard
input; an optional Windows companion supplies global switching for the web
display. Launch in Base / Gyro and keep the selected mode until the user
changes it. Selecting a mode changes the reference display, not the Steam
configuration or the game's input state.

Within each mode, show bindings for no modifier, the left modifier, the right
modifier, or both. Holding L1 in Steering shows Steering's left-modifier
bindings; releasing it restores Steering's unmodified bindings. Releasing
one of two modifiers preserves the remaining modifier. Switching modes while
a modifier is held uses that modifier in the newly selected mode immediately.

The display describes the configured action for a fresh press in that
context. It does not reconstruct Steam's internal layer stack or track the
output of a face button already held through a layer change. Persistent
states are the user's responsibility, as requested.

The first usable slice shows the four face buttons in fixed positions, the
selected mode, and held modifier indicators. The profile format also supports
other controls so the diagram can grow after this slice is validated. Show
key/button outputs as labels; use game action names only where the profile
actually supplies them.

## Scope and repository integration

- Windows is the first native runtime. Support the ordinary window and
  overlays over windowed or borderless games. Also deliver a standalone web
  build, initially validated in Chrome/Edge and Firefox on Windows.
- Validate one named physical controller and connection type first. The
  [controller registry](../steam_layout/controllers.py) currently includes
  Ibex, Neptune and DualSense Edge; layout support alone does not establish
  that an overlay can observe each controller on Windows.
- The first hardware milestone uses the default variant with L1/R1 modifiers.
  Model modifier roles separately from physical buttons so alternative
  L2/R2 profiles can follow with tested trigger thresholds and hysteresis.
- Native Linux/macOS support, exclusive fullscreen integration, automatic mode
  detection, arbitrary Steam layout import, and a graphical binding editor
  are later work. Browser portability does not establish controller support
  on an operating system until that combination has been tested.

Put the app in `overlay/` as one Cargo package with a library for testable
logic and UI, a desktop executable, and a WebAssembly library entry point.
Keep the existing layout tools in Python.
Use `steam_layout/overlay_profile.py` for future export logic and
`tools/export_overlay_profile.py` for its command-line entry point. This
follows the [repository conventions](../README.md#directory-map).

Export display profiles from a specified controller, variant and layout
version. Use the [layout model](../steam_layout/model.py) and inspect the
[binding resolver](../steam_layout/flow_model.py) for reusable offline lookup.
Both application targets consume the identical generated JSON and assets;
neither runs Python or the Steam layer simulator at runtime.

When implementation reaches actual layout inspection, follow
[steam-layout-prep](../skills/steam-layout-prep/SKILL.md) on an analysis copy.
Review activator interpretation with
[steam-binding-order](../skills/steam-binding-order/SKILL.md). Profile export
must leave working layouts and version snapshots unchanged.

## Technology and boundaries

| Responsibility | Choice |
|---|---|
| Mode, modifier and binding logic | Shared Rust with no UI or operating-system dependency |
| Diagram, mode buttons and settings | One egui application; eframe native runner and web runner |
| Native controller adapter | SDL3 through Rust bindings, with background input enabled |
| Browser controller adapter | Gamepad API through `web-sys` and `wasm-bindgen` |
| Shortcuts and window integration | `windows` crate on Windows; page keyboard events on web |
| Profiles and preferences | Shared Serde validation; native files or browser storage adapters |
| Build and checks | Cargo, rustfmt, Clippy, `wasm-pack` and `wasm-bindgen-test` |

[Eframe supports both native and web entry points](https://docs.rs/eframe/latest/eframe/#usage-web)
for the same app. Keep mode transitions, modifier handling, binding lookup,
profile validation, diagram layout and settings logic in shared Rust modules.
The web build compiles these modules to `wasm32-unknown-unknown`; it does not
reimplement them in JavaScript or maintain another set of binding tables.

Use target-specific dependencies and small `desktop`/`web` feature entry
points so SDL and Win32 APIs cannot enter the WebAssembly build. Keep the
core testable with neither feature enabled. Limit HTML/JavaScript to the page
shell, canvas, startup/error handling and generated WebAssembly glue. Package
the browser assets with `wasm-pack build --target web` and a small asset-copy step;
the standalone build can run from static HTTPS hosting or localhost.

```text
overlay/
  Cargo.toml
  src/core/          shared state, profiles and binding resolution
  src/ui/            shared egui diagram, controls and settings
  src/platform/      native and browser input, storage and lifecycle adapters
  src/main.rs        Windows entry point
  src/lib.rs         shared library and WebAssembly entry point
  web/               canvas page and minimal startup code
  profiles/          generated profiles and shared assets
  tests/fixtures/    one corpus of profiles and input traces for both targets
```

The UI receives platform capabilities, such as global shortcuts and desktop
click-through, and offers the applicable controls. Bindings and diagram code
remain shared when the capabilities differ.

Egui exposes [transparency, topmost windows and mouse pass-through](https://docs.rs/egui/latest/egui/viewport/struct.ViewportBuilder.html#method.with_mouse_passthrough).
It can [wake the UI for a repaint](https://docs.rs/egui/latest/egui/struct.Context.html#method.request_repaint).
Use those capabilities for a compact HUD and an interactive window sharing
the same diagram. Keep an accessible tray/menu or shortcut route back to
interactive mode when the HUD passes clicks through.

SDL's [background-input setting](https://wiki.libsdl.org/SDL3/SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS)
allows input while the app is unfocused; it does not prove access to the
original physical buttons while Steam Input is active. Select one device
explicitly and distinguish it from Steam's virtual controller. Do not merge
events from every enumerated device.

Keep SDL event pumping on the main thread as required by
[SDL_PollEvent](https://wiki.libsdl.org/SDL3/SDL_PollEvent). The initial probe
must establish how bounded input polling works with eframe's event loop.
Input polling and drawing have different jobs: unchanged samples should not
require drawing the diagram again. If eframe cannot provide that integration
cleanly, replace only the native shell with a directly owned winit loop or
assess a narrower Windows input adapter. Preserve the shared egui UI and web
runner. Pin the working crate versions and commit `Cargo.lock` during
implementation.

The core receives normalized events such as mode selection, button changes,
current-device snapshots and disconnects. It produces a view model containing
the selected mode, modifier indicators, labels and connection status. Windows
hotkeys, browser keyboard events and GUI clicks dispatch the same
mode-selection command. Storage and file import/export adapters exchange JSON
bytes with shared validation rather than putting filesystem calls in the core.

## Browser capabilities and input

| Capability | Standalone web | Web with Windows companion | Native Windows |
|---|---|---|---|
| Same profiles, diagram and mode buttons | Yes | Yes | Yes |
| Automatic modifier display | Browser-exposed controller input | Native controller input | Native controller input |
| F1–F3 while a game has keyboard focus | No | Yes, through companion | Yes |
| Transparent desktop overlay with click-through | No | Use native HUD alongside browser | Yes |

The standalone browser adapter reads current snapshots through
[`navigator.getGamepads()`](https://docs.rs/web-sys/latest/web_sys/struct.Navigator.html#method.get_gamepads).
Start with a visible page and an instruction to interact with the controller
so the browser exposes it. Select one device, inspect its reported mapping,
and normalize it to the same logical controls used by the native adapter.
Use standard indices only when the mapping is `standard`; a nonstandard device
requires an explicit tested mapping. Handle sparse device arrays and index
reuse after reconnection. The [Gamepad specification](https://www.w3.org/TR/gamepad/)
defines the browser-facing contract, not a guarantee that Steam's original
physical modifiers are available.

Poll snapshots while the page is visible and request an egui repaint when
the displayed state changes. Test a visible second-monitor browser while
the game has focus separately from a hidden tab. Loss of keyboard focus is
not itself proof that gamepad input has stopped. Hidden pages can have
[animation callbacks suspended and timers throttled](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API#policies_in_place_to_aid_background_page_performance).
Mark input as paused/unverified across suspension and replace held state
from a fresh snapshot before restoring live status on resume.

[Browser keyboard events target the focused context](https://www.w3.org/TR/uievents/#events-keyboardevents).
Handle page shortcuts where the browser permits, avoiding text-entry controls
and repeated keydown commands; browser-reserved keys may need rebinding.
Mode buttons remain available. A standalone site cannot register global
Windows shortcuts or become a click-through desktop overlay.

### Optional companion input for the browser

For users who need global mode shortcuts or native controller access while
using the browser display, add an opt-in mode to the same Windows executable.
Reuse its input adapter, shortcut registration and shared state reducer.
Serve the identical web bundle and a versioned snapshot stream from one
loopback origin, avoiding a separately maintained backend or a second UI.
Keep the static hosted version usable without this companion.
When the browser is the only display, keep the native HUD hidden and stop
its rendering while continuing input collection.

In this mode the companion owns mode and input state. Browser clicks send
mode commands to it; the browser renders acknowledged snapshots through the
shared resolver and UI. Snapshots identify the session, sequence, selected
mode, held modifiers, controller status and active profile digest. Supply the
matching profile through the same connection and validate it with the shared
loader. Do not simultaneously consume local Gamepad API input.

Controller selection, active profile and global shortcuts are configured in
the companion's existing native settings. While connected, the shared browser
UI shows those settings as read-only through its capability model; it must
not change browser-local copies. Browser display preferences remain local
and editable. Mode buttons are the acknowledged remote command described above.

Bind this optional service to loopback, validate the requesting origin/session,
and expose only the app's profile/state and mode-selection operations. A
disconnect shows unavailable input; reconnect replaces the complete snapshot.
This is a same-machine feature, not remote controller forwarding. A companion
can keep collecting state while a tab sleeps, but cannot force that tab to
render; resume must synchronize before displaying live state again.

## Profile contract

A profile contains a schema version, controller identity, variant, source
layout version and digest, physical-to-logical control mapping, modifier
definitions, and bindings for the three modes. Use controller-independent
face positions internally and controller-appropriate glyphs in the view.

Define the four modifier contexts explicitly. A missing override may inherit
only through a declared rule; an explicitly unbound control stays unbound.
A missing or unsupported context must display an unavailable state rather
than silently substitute base bindings. Unsupported activators, ambiguous
order-dependent bindings and differing Base/Gyro bindings must surface in the
export report for a deliberate display policy. Do not invent an authoritative
mapping from an ambiguous source.

Keep expected labels in a small independently reviewed fixture for all three
modes and four modifier contexts. Exporter tests must compare against that
fixture, not derive both expected and actual values with the same resolver.
Synthetic fixtures exercise inheritance and invalid inputs cheaply; one
pinned real-layout fixture checks the mapping used by the first release.
The native package, hosted web package and companion-served package all use
these same versioned profiles. Native preference files and browser storage
share one schema, with storage-unavailable errors handled by the adapter.

## Test-driven implementation milestones

### 1 Prove input access and compilation for both targets

- [ ] Write failing adapter-contract tests using a fake device: select one
  device, seed held buttons from a snapshot, process press/release, and ignore
  events from other devices or a disconnected session.
- [ ] Implement a minimal diagnostic executable and the normalized adapter.
  Record device identity, backend, connection type and modifier transitions.
- [ ] On Windows with Steam Input enabled and a game focused, verify L1, R1,
  both, both release orders, launch with a button already held, and reconnect
  while held. Compare physical behavior against the diagnostic output.
- [ ] Verify event pumping continues while unfocused and demonstrate idle
  polling without a continuously rendered animation loop.
- [ ] Compile a minimal shared egui view for native and WebAssembly at the
  start. Verify native-only dependencies are excluded from the web target.
- [ ] First test browser snapshot normalization with fake data, then add a
  small browser probe. Record device mapping and modifier visibility with
  Steam Input active, initially focused and then visible while the game has
  focus. Record actual browser/version and connection type.

**Exit:** both targets compile, native input passes on the named controller,
and browser input capabilities are recorded. If SDL sees only remapped outputs,
investigate direct HID for that device before the full HUD. If the browser
cannot observe the required modifiers, its gameplay use needs companion input.
Automated adapter tests do not prove these hardware gates. Shared core work
can progress while access to Windows test hardware is pending.

### 2 Implement mode and modifier behavior

- [ ] First write table-driven tests for all 12 mode/context combinations
  using distinct, hand-authored labels for the four face buttons.
- [ ] Cover mode changes with held modifiers; left/right press and release in
  either order; repeated press and duplicate release events; and equivalent
  mode commands from shortcuts and clicks.
- [ ] Implement the pure state reducer and binding lookup, then refactor.
  The initial display policy selects an explicit combined-modifier context,
  independent of press order; profiles requiring another policy are flagged.
- [ ] Run the same fixture/trace corpus natively and with `wasm-bindgen-test`.
  Assert identical semantic view models and errors, using shared test bodies
  and reviewed expected data rather than separately written platform suites.

**Exit:** deterministic core tests pass on native and WebAssembly without
Steam or a physical controller.

### 3 Validate profiles and generate real labels

- [ ] First test valid fixtures, malformed JSON, unsupported schema versions,
  missing modes/contexts, duplicate identifiers, invalid modifier definitions,
  explicit unbound entries, and declared inheritance.
- [ ] Test that a failed profile reload retains the last valid profile and
  reports the failure. A failed first load shows a configuration error.
- [ ] Use the same validation tests for native file loading, bundled browser
  profiles and browser file import. Add adapter tests for denied/unavailable
  browser storage, quota errors and invalid imported files; retain usable
  in-memory settings when persistence fails.
- [ ] Implement Serde loading and validation, then the Python exporter using
  its own failing tests before production code.
- [ ] Check deterministic exports and source identity against the reviewed
  fixture. Account for every required face-button/context entry and report
  every unsupported source construct. Do not silently drop extra commands.
- [ ] Add alternative-variant profiles only with tests for L2/R2 threshold
  crossing, release hysteresis and noisy trigger readings.

**Exit:** the first supported controller/variant has reviewed, traceable labels
for all three modes. An exporter round trip alone is insufficient evidence.

### 4 Handle native lifecycle and global shortcuts

- [ ] First test that disconnect clears held state but preserves the selected
  mode; reconnect replaces state from a fresh snapshot; startup detects
  already-held modifiers; and switching devices rejects stale events.
- [ ] Test resynchronization after suspend/resume and input interruption.
  Ordinary loss of window focus must not disable background monitoring.
- [ ] First test hotkey registration success, conflict, rebinding, shutdown
  cleanup and suppression of repeated mode-change commands using a fake
  Windows boundary; then implement the real adapter.
- [ ] Register configurable shortcuts with `MOD_NOREPEAT`. Show registration
  failures and keep click selection usable. Unregister old shortcuts when
  rebinding or exiting.

[RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey)
reserves application shortcuts; F1–F3 are dedicated mode controls while
registered. Document that choice and let users change them. If the user later
requires those same keys to reach the game, implement and test passive key
observation as a separate behavior.

**Exit:** lifecycle trace tests pass and Windows checks confirm background
switching, shortcut conflicts and recovery on the supported controller.

### 5 Build one interface for native and web

- [ ] First test view-model outputs for mode labels, modifier highlights,
  connection/configuration errors and resolved button labels. Check that
  unchanged inputs do not request redundant application redraws.
- [ ] Implement the fixed-position face-button diagram, mode buttons,
  controller/profile selection and settings for shortcuts, size and opacity.
- [ ] Mount the same egui app in the native runner and browser canvas. Test
  capability-driven controls so Windows-only settings are not offered by a
  standalone browser, while all binding labels remain identical.
- [ ] Add interactive-window and HUD modes, including a reliable way to
  return from click-through mode. Preserve placement when toggling modes.
- [ ] Test preference validation, invalid/offscreen placement recovery and
  repeated HUD/window transitions through the application boundary.

**Exit:** automated behavior checks pass; manual Windows checks confirm
click-through, no focus theft, readable labels, DPI scaling, multiple monitors
and windowed/borderless gameplay. Browser checks confirm canvas sizing,
keyboard focus, mode buttons, zoom and readable labels. Visual inspection
proves rendering details; view-model tests do not substitute for it.

### 6 Complete browser input and lifecycle behavior

- [ ] Before adapter implementation, test API unavailable/blocked, waiting
  for controller interaction, no devices, sparse arrays, disconnect, index
  reuse, held-at-connect state and unknown mappings using injected snapshots.
- [ ] Test focused-page shortcuts, ignored repeat events, text-entry behavior,
  rebinding and click equivalence. Check reserved-key behavior in real browsers.
- [ ] Test hiding/suspending the page while L1 is held, releasing it while
  paused, and resuming with a fresh snapshot. Preserve the manual mode and
  replace old held state. Distinguish focus loss from visibility suspension.
- [ ] Implement the thin `web-sys` adapter and browser persistence, then
  run the shared corpus through both native and browser normalization paths.
- [ ] Test a visible browser beside a focused game on the named controller.
  Record any combination requiring companion input instead of claiming
  standalone support from synthetic tests.

**Exit:** the standalone web app has the same binding behavior for supported
input, explicit capability/error states and tested resume recovery.

### 7 Add optional native input for the web display

- [ ] First write protocol tests for session/profile/version mismatch, stale
  or out-of-order snapshots, mode-command acknowledgment, source switching,
  disconnect and full synchronization on reconnect/resume.
- [ ] Test that companion mode consumes only native input and has one mode
  authority. A browser click and a native F-key must converge to the same
  selected mode and labels without applying an event twice.
- [ ] Test that companion-owned controller/profile/shortcut settings appear
  read-only in the browser and update from host snapshots, while local display
  preferences remain editable. Include those settings in initial/reconnect
  synchronization so the shared interface never presents conflicting values.
- [ ] Implement loopback serving of the existing web assets and snapshot
  transport using the native adapters and shared core. Test rejection of
  unrelated origins/sessions and unsupported commands.
- [ ] With the browser visible on a second monitor and the game focused,
  verify physical modifiers and F1–F3 update the browser display. Confirm
  that closing the companion leaves a clear disconnected state.

**Exit:** browser users can opt into native input and global shortcuts without
introducing another binding engine, profile format or UI implementation.

### 8 Measure and package both builds

- [ ] Add Windows CI for format, lint, unit and integration tests, and the
  release build. Add WebAssembly compilation and browser tests in Chrome and
  Firefox through `wasm-bindgen-test`. Keep core checks runnable on the current
  macOS development machine; it cannot supply Windows hardware evidence.
- [ ] Produce a portable Windows bundle with required SDL/runtime dependencies,
  profiles, notices and instructions. Smoke-test on a clean Windows account
  without developer tools installed.
- [ ] Build a static web bundle from the same commit and profiles. Serve the
  actual output in browser smoke tests for WebAssembly startup, profile load,
  canvas rendering, mode controls and error recovery. Verify deployed-base-path
  asset URLs and a usable startup error if graphics/WASM initialization fails.
- [ ] Measure idle and active CPU, working set, GPU activity, input-to-label
  latency and bundle size on a named Windows PC, recording build/backend and
  controller details. Include hidden, interactive and overlay states; measure
  browser startup/download size, memory and latency separately, with and
  without the companion. Code sharing does not guarantee equal resource use.
- [ ] Establish numeric performance budgets from the diagnostic baseline
  before UI polish; compare the packaged build against those budgets.
- [ ] Document exactly which controller/connection and game window modes
  passed, including browser versions and focus/visibility conditions. Keep
  native and static web artifacts separate from the existing layout ZIP.

**Exit:** reproducible Windows and static web bundles built from one source,
with automated results, hardware acceptance evidence and measured resource
usage. Packaging is part of this plan; choosing public hosting and publishing
the site can follow separately.

## TDD execution and acceptance

For each behavior, record the failing test and its expected failure reason,
the minimal implementation, the passing command and any refactor. A test that
passes before the feature is implemented does not establish the red step.
Use fake input traces and controlled clocks for deterministic cases; tests
must assert externally meaningful labels, state or recovery behavior rather
than private call sequences. Add a failing regression test before each bug fix.

Planned checks, once `overlay/Cargo.toml` defines the target features. Run the
desktop commands on Windows; the core and browser checks also run on the
development machine:

```bash
cargo test --manifest-path overlay/Cargo.toml --lib --no-default-features
cargo test --manifest-path overlay/Cargo.toml --features desktop
cargo fmt --manifest-path overlay/Cargo.toml -- --check
cargo clippy --manifest-path overlay/Cargo.toml --all-targets --features desktop -- -D warnings
cargo build --manifest-path overlay/Cargo.toml --release --features desktop
cargo check --manifest-path overlay/Cargo.toml --lib --target wasm32-unknown-unknown --no-default-features --features web
```

Use [wasm-bindgen-test in headless browsers](https://wasm-bindgen.github.io/wasm-bindgen/wasm-bindgen-test/browsers.html)
with `wasm-pack test` for the shared corpus and browser adapter tests, and
`wasm-pack build --target web` for browser packaging. Pin the tools and record
the exact feature flags and artifact-copy commands in the implementation's
README. A successful WebAssembly compile is not a browser test pass, and a
synthetic browser test is not proof of physical input access.

Run focused Python exporter tests when adding profile generation, then the
relevant existing model/resolver checks if those shared modules change. Keep
hardware tests explicitly separate from unattended CI. Capture implementation
and measurement results under a dated `findings/` folder and add durable
build/usage instructions in `overlay/README.md`.

The macOS follow-up adds a headless native input companion, without requiring
Steam, because the user's wired Steam Controller was not exposed to Brave's
Gamepad API. It shares SDL input with Windows and reuses the same core, HTTP
protocol and browser UI. It does not add a macOS overlay or global shortcuts.
The direct SDL driver detects the attached controller. The user confirmed wired
macOS/Brave reconnect and shoulder input work without Steam; reconnect now uses
a serial-based identity because macOS device paths change. Tests cover single-controller
selection without silent switching, missing-browser-device feedback and focused
companion mode shortcuts. See the findings for observed red/green evidence.

## Expanded controls and detailed timing — implemented

The shared controller diagram now includes Start/Select, four D-pad directions,
L3/R3, L1/R1 and analog L2/R2 alongside the face buttons. Following the single-timer experiment, one central timing bar follows L1, R1,
Select or Start, with Hold, single Tap and Tap, then hold outcomes visible. It changes stage after
release and second press instead of showing four concurrent lanes. Settings open
in a separate panel so the diagram and timelines remain the main view.

The schema 2 exporter supplies all control labels and the layout's hold,
release-window, delayed-output and second-hold-cover durations. A monotonic Rust
gesture engine handles boundaries, chained taps, consumed modifiers, combined
bumpers, touch completion/cancellation and lifecycle resets. Native and WASM use
the same engine; companion browsers render the host's authoritative gesture state.
Native input retains queued button edges, so a short press and release between
snapshots is not lost. Legacy profiles still load with missing features explicit.

TDD added deterministic traces before the implementation, then regressions for
touch cancellation, menu-as-modifier outputs, opposite-bumper window behavior,
phase inheritance and invalid dashboard profiles. The browser smoke test now
covers all sixteen controls, trigger pressure and host-owned timing. Results and
remaining hardware gates are in the implementation findings.

Timing is an estimate from the configuration, not an observation of Steam's
internal state. Bumper stick deflection consumes the tap using the exported rule. Trackpad and
combined menu/state-changing routes can leave timing uncertain until release,
while known inherited control bindings remain visible. Generic browser input lacks stick
touch; the macOS/Windows Triton adapter reads that capability when available.

The next Windows acceptance task is milestone 1's hardware probe using
`keybind-overlay.exe --diagnostic`, followed by native HUD/recovery checks and
packaged release measurements. Automated implementation results and exact gaps
are recorded in the linked findings; hardware-dependent exits remain open.
