# Rust keybind viewer implementation — 2026-10-15

## Direct browser USB input (2026-10-16)

The viewer now has a **Connect controller** action using WebHID, with no native
helper in this path. The picker is restricted to the wired Steam Controller 2
(`28de:1302`); Rust decodes Triton report IDs `0x42`, `0x45`, and `0x47` into the
existing input frame. Button mappings and packed layouts follow the pinned SDL
3.4.18 Triton driver. JavaScript handles browser permissions, raw report delivery,
USB lifecycle and the transient lizard-mode setting; bindings/timing remain Rust.

Validation: 44 native Rust tests passed, including four new report-decoder tests;
seven browser-transport lifecycle tests passed in Node. The packaged WASM app
passed the Brave smoke test with a synthetic USB boundary: picker user activation,
cancel/deny, controls, fast tap edges between frames, stick/trackpad positions,
hidden/resume, unplug/reconnect, stalled input and disconnect. Native and WASM
Clippy passed. Container validation included the new JS asset and release hashes.
The pipeline continues to skip tests as requested; these checks ran locally.

Physical connection was confirmed by the user on 2026-10-16: the wired Steam
Controller 2 connects through **Connect controller** in their normal Brave
window on macOS, and buttons respond in the local browser-only preview. No native
helper is used. This confirms picker access and live button input; it does not
claim a complete physical check of every analog control or timing sequence.
Earlier isolated automated picker probes cancelled in Brave or waited for a
selection in Chrome; those results did not reproduce the user's normal browser.
The hosted HTTPS origin still needs its own permission grant after updating the
Dockge image. Earlier companion hardware checks below apply only to that path.

## Steering and live positions

Added signed stick axes and independent left/right pad contacts to the shared
snapshot. SDL supplies pad coordinates and Triton stick-touch state; browser
Gamepad supplies axes only and explicitly leaves touch coordinates unavailable.
The shared diagram shows deflection rings, contact highlights and trackpad dots.
SDL's pinned Triton driver confirms pad 0 is left, pad 1 is right, with Y down.

Steering exports twenty additional inherited pages for LS up/down with either
bumper, including Tap Cover and double-tap stages. The exporter reads the 405/1000
threshold, 200 ms hold, 50 ms output, 150 ms window and 150 ms cover from the source.
Up click outputs are Mouse back/forward; down outputs are Caps Lock/Mouse middle.
Tap Cover retains these inherited click outputs while the modifier is present.
The source layout is unchanged; the viewer remains a fresh-press reference,
not an observer of Steam's actual layer stack or automatic mode transitions.

TDD: the export test failed on missing Steering metadata and the Rust test failed
on missing stick coordinates before implementation. Eight exporter tests and
nineteen gesture tests now pass. Native and web clippy pass. Packaged browser
checks cover axis normalization and Steering up/down labels; companion checks
verify independent pad/stick coordinates survive transport. The restarted
physical helper reports Live, both stick axes and both pad capabilities.
[Position marker preview](position-markers.png) was visually inspected using
synthetic contacts; actual thumb motion still needs user acceptance.

## Ibex controller diagram

The shared Rust UI now draws an Ibex front view with curved grips, symmetric
sticks, outer D-pad/face buttons and tilted square trackpads, using this
[front-view reference](https://steamdb.info/static/img/blog/106/sc_front.webp).
The trackpads and system buttons are orientation cues; the sixteen supported
controls retain live highlights, binding tooltips and trigger pressure bars.
The diagram scales and centers above the single shared timer without adding
an image asset. Native compilation/lint and packaged browser/companion checks
passed, including all sixteen controls and timing. The browser rendering was
visually inspected: [Ibex preview](ibex-controller.png).

## Single central timer experiment

Replaced the four simultaneous timing lanes with one central bar. It follows
the active gesture, shows Hold, single Tap and Tap, then hold outcomes together, and reuses the bar for
the release window (including the delayed-output marker) and second-hold cover
countdown. Combined bumpers appear as one owner. Idle retains the last gesture
as a reference; an opposite bumper used as an output cannot steal the timer.

TDD: the shared-owner test first failed because `timer_owner` did not exist,
then passed with the selector. All 17 gesture tests pass natively and in Chrome
WASM; the packaged browser/companion smoke also passes. The repeat-key smoke
sequence was corrected to model a key held across frames: egui derives repeat
from held state rather than the synthetic DOM repeat flag.

[Single central timer preview](shared-timer.png).

## Expanded controller and timing dashboard

Implemented the requested sixteen controls and always-visible L1, R1, Select
and Start timelines in the shared Rust/egui UI. Trigger bars display physical
travel; no activation threshold is invented when the layout omits it. Schema 2
exports 54 complete control pages and eight source-derived gesture recipes;
schema 1 remains supported with unavailable additions explicitly shown.

The engine uses a monotonic clock, preserves queued native button edges, and
handles the 200 ms initial hold, 50 ms expected scroll/Escape/Tab marker, 150 ms
second-press window and separate 150 ms Double Tap Cover countdown. It includes
chained taps, consumed modifiers, combined bumpers, stick-touch completion and
window cancellation. Native helper snapshots own the timing in companion mode;
the browser only interpolates the displayed countdown. No Steam input is sent.

TDD evidence for this expansion:

| Behavior | Observed red | Green |
|---|---|---|
| All controls and source timings | Export returned schema 1 instead of 2; new Rust gesture types were absent | Seven exporter tests and the shared gesture corpus pass |
| Cover inheritance | Double Tap Cover incorrectly inherited modifier G instead of base F and lacked opposite-bumper Scroll up | Correct window/second/cover stacks resolve inherited controls |
| Layer-only controls | Steering L1 was shown unbound instead of S | Reviewed entry/transition labels are exported |
| Touch release cancellation | A scroll was still predicted after touch released during its window | Pending output is cancelled |
| Modifier menu output | L1 + Select interrupted timing instead of consuming L1 and displaying Delete | Select acts as the modifier output |
| Opposite bumper in a window | A held replacement scroll became a new modifier after expiry | It remains an output; base reference returns after expiry |
| Schema validation | Invalid dashboard accepted under schema number 1 | Any present dashboard is validated |
| User-reported inherited bindings | Timing interruption replaced every label with Uncertain; stick movement interrupted a valid bumper gesture | Known inherited bindings remain; both-stick consumption applies Tap Cover and owner release restores base labels |
| Temporary gyro dismissal | Hold-phase face binding was Unbound | Fresh-press self-removal exposes the underlying modifier binding and consumes the tap |

The user identified the inheritance problem specifically under “Timing
interrupted” during the live trial. Added the reproducing assertions before the
fix. The final host was rebuilt and restarted, and it reports the real wired
Steam Controller Live with capacitive stick-touch data available. Confirmation
of every newly added physical control is separate from the synthetic tests.

Current artifacts: WASM is 2,989,496 bytes (1,318,350 gzip), JS glue is
82,856 bytes (12,360 gzip), and the macOS helper is 3,206,960 bytes. These
are file sizes, not CPU/RAM or network-transfer measurements.

Current validation: **30 shared Rust tests pass both natively and in Chrome
WebAssembly** (14 state/protocol + 16 gesture/inheritance), plus two native UI
contract tests, one real HTTP integration test, and seven Python exporter tests.
macOS, WASM and Windows cross-target Clippy pass with warnings denied. The Windows
check still uses DOCS_RS=1 and does not establish Windows linkage or runtime
behavior. The packaged browser smoke covers all sixteen input mappings, trigger
pressure, hold timing, host-owned timing, inherited labels during interruption,
reconnect, settings and error recovery. The raw-socket HTTP test now uses HTTP/1.0
to avoid parsing chunk framing; the actual browser tests exercise HTTP/1.1.

[Expanded diagram](expanded-controller.png) and
[timing dashboard](expanded-timelines.png) record the shared UI. Timing remains
an estimate of the configured layout. Pad and combined menu/state-changing
routes can pause timing; the UI then labels the displayed inherited modifier
reference explicitly. Standard browser input lacks capacitive touch. Stateful
mode selection remains manual. Windows hardware, HUD and resource gates below
remain open. Source layout JSON and its SHA-256 are unchanged.

## macOS direct-input follow-up

Reconnect regression: the live host later reported selected ID `1`, status
`disconnected`, but a connected Steam Controller at ID `2` with a different
`DevSrvsID` path. macOS paths were therefore not stable physical identities.
Added a failing regression before introducing serial-based identity, scoped by
vendor/product and hashed so the serial stays out of diagnostics and snapshots.
The test covers a changed instance/path, another physical controller and
ambiguous duplicate identities. All 14 core, 2 UI and 1 HTTP tests pass; macOS
and Windows cross-target Clippy pass. The rebuilt release helper confirms the
real controller supplies a serial identity. The user then confirmed that
unplug/reconnect returns to Live and the buttons update the bindings. Native
diagnostics also recorded L1, R1, both held, and releases back to neither held.
This verifies the wired Steam Controller on the user's macOS/Brave setup without
Steam; Windows and other controllers/transports retain their separate gates.

The user reported a wired Steam Controller missing in Brave and explicitly
required operation without Steam. A filtered local IORegistry inspection found
Valve USB `28de:1302`, exposing mouse, keyboard and vendor-specific HID usages,
with no gamepad usage. No `steam_osx` process was running. The standalone viewer
only reads browser Gamepads; it cannot add device support through a profile.

Added a headless macOS companion using the same SDL adapter as Windows, the
existing Rust state/profile code, HTTP protocol and WASM UI. Enabling
`SDL_JOYSTICK_HIDAPI_STEAM=1` was necessary: the initial SDL probe returned no
devices, while the enabled driver detected the connected Steam Controller.
The real companion endpoint returned `status: live`, selected device `1`, and
no input error without Steam. Subsequent physical shoulder press/release and
reconnect verification is recorded above; enumeration alone was not treated as
proof of those inputs.

The helper selects a sole controller, refuses ambiguous initial selection and
retains its identity after disconnect instead of adopting another device. The
browser's mode keys also send acknowledged companion commands when focused.
Missing standalone-browser devices now have a distinct status and help text.

TDD: new selection and UI contract tests failed before their methods existed;
the packaged browser test failed against the old bundle for missing detection
feedback. After implementation, 13 core tests, 2 UI tests, the real HTTP test
and packaged Chrome smoke tests passed (including focused companion shortcuts).
macOS and WASM Clippy passed, and the Windows cross-target Clippy check passed
with `DOCS_RS=1` (no Windows SDL link or runtime verification). Added a macOS CI
job; CI itself has not run. The local arm64 release helper is 2.88 MiB and links
system frameworks, with SDL static. This is executable size, not a RAM/CPU claim.

See [macOS usage](../../overlay/README.md#macos-companion-steam-not-required).

The first implementation is in [overlay/](../../overlay/README.md): one Rust
state/profile engine and one egui UI, compiled to a Windows executable or a
browser WASM module. The browser is a normal reference page. Windows adds SDL
input, reserved global shortcuts, a transparent click-through HUD and an
optional loopback companion serving the same web bundle.

This record is **automated implementation evidence, not Windows hardware
acceptance**. The Windows-specific source type-checks and passes Clippy, but no
Windows executable was linked or run on this macOS machine. SDL physical input
under Steam, native HUD/shortcut behavior and resource budgets remain open.

## What is implemented

- Manual Base/Gyro, Steering and Menu modes, initially F1/F2/F3; clickable mode
  controls; configurable distinct F1–F12 assignments, with F4 initially unused.
- Physical L1/R1 snapshot normalization, both release orders, held-at-start,
  explicit controller selection, disconnect clearing and unique-path native
  reconnect. A missing or ambiguous native path requires manual reselection.
- One fixed-position face-button diagram, held indicators, input/error states,
  profile import, size settings, native opacity and recovery-gated HUD/hide.
- Browser Gamepad mapping checks, sparse arrays, page-focused shortcuts,
  hidden-page pause and fresh resume, and storage failure recovery.
- Companion session/version/profile/sequence validation, native state authority,
  acknowledged browser mode commands, read-only host settings, profile sync,
  bounded fetch timeouts and disconnected/expired input clearing. The browser
  never reads local Gamepads in companion mode.
- Shared schema validation and a read-only Python exporter. The bundled Ibex 1.0
  default profile matches an independent hand-authored expected label table.
- Lockfile, static web build, Windows packaging/third-party notices and a CI
  workflow for Windows plus Chrome/Firefox web checks. CI has not been run here.

SDL stays on the process main thread. Eframe uses Windows' supported secondary
thread event loop. Native input is sampled every 8 ms and device enumeration
runs once a second; only changed state wakes the GUI. Standalone web samples
at 16 ms while visible. Companion HTTP snapshots are requested at most 30 Hz;
the profile is omitted when its digest matches. This is a simple polling
transport rather than a push stream; it avoids another async server runtime.
None of those intervals establishes measured CPU or latency performance.

## TDD record

| Behavior | Observed red step | Green evidence |
|---|---|---|
| All twelve contexts, mode changes, release orders, selected input and profiles | Six integration tests failed to compile against the empty core module | Shared behavior suite passed after implementation |
| Preferences, shortcut filtering and companion validation | Added tests failed on absent APIs | Same suite passed natively and in Chrome WASM |
| Native hotkey lifecycle | Fake-boundary test failed on missing `HotkeyApi` / `Hotkeys` | Registration/conflict/rebind/drop assertions passed |
| Reconnection identity | New test failed on missing `DeviceSelection` | Unique-path reconnect passed; duplicate/missing paths stayed unselected |
| Expired remote input | New test failed on missing `InputFreshness` | Timeout/fresh-snapshot assertions passed |
| Exporter | Four tests failed importing the not-yet-created module | Reviewed real labels, unsupported constructs, explicit unbound and source preservation passed |
| Exporter inversion and competing activators | Two later regression assertions failed: inverted chord produced unbound, mixed activators produced a label | Both passed after using `edge_binding_invert` and rejecting competing output policies |
| Real companion HTTP | Integration test failed on unavailable portable host/server modules | Actual loopback requests verified mode authority and 403/404/400 boundaries |
| Companion-owned display settings | UI contract failed on missing display-preference projection | Host hotkeys update while local appearance is retained |
| Browser recovery | Packaged-app test failed because the old blocked-Gamepad error survived restored live input | Input error now clears without discarding profile/storage errors |

The same `tests/behavior.rs` test bodies and fixture run on native and WASM.
Browser smoke tests exercise the built artifact, not a separately implemented
UI. The fake native companion fixture uses the production host/server modules.

## Validation completed

Development host: Apple Silicon macOS. Rust 1.99.0, eframe 0.31.1, SDL Rust
bindings 0.20.0; exact transitive dependencies are in `overlay/Cargo.lock`.
Browser: official Chrome for Testing 155.0.8059.79, matching ChromeDriver,
headless with software WebGL. Rust and Chrome were placed under `/tmp` without
changing shell startup files; wasm-pack uses its normal tool cache.

| Check | Result |
|---|---|
| Native Rust core behavior tests | 12 passed |
| Native companion HTTP integration test | 1 passed |
| Native shared UI settings contract | 1 passed |
| Same Rust behavior suite in Chrome WASM | 12 passed |
| Python exporter tests | 6 passed |
| rustfmt | Passed |
| Clippy for Windows target, all targets, desktop feature | Passed with warnings denied |
| Clippy for WASM target, all targets, web feature | Passed with warnings denied |
| Shared native UI compilation on macOS | Passed; no macOS controller app claimed |
| Web release packaging | Passed; `overlay/dist/` generated |
| Packaged standalone browser smoke | Passed |
| Packaged browser + real companion server, fake native input | Passed |

The Windows check used `DOCS_RS=1 cargo clippy --target
x86_64-pc-windows-gnu --features desktop --all-targets -- -D warnings` to skip
SDL's native C build/link on macOS. This checks Windows Rust code and APIs,
**not SDL linkage, an MSVC release build, or Windows runtime behavior**. Windows
CI performs the real SDL source build and release packaging.

The smoke test verified startup, subdirectory-relative assets, the visible
canvas, clickable mode switching, focused keys/repeat suppression/F4,
rebound and persisted shortcuts, invalid profile recovery, sparse Gamepad
arrays, held-at-selection state, both/released modifiers, unknown mappings,
disconnect/reconnect, hidden/resumed input, blocked API recovery and denied
storage. Companion checks verified initial state, browser command acknowledgment,
host settings changes, local Gamepad exclusion and clearing on server exit.

[Browser screenshot](browser-viewer.png) and
[companion screenshot](browser-companion.png) were visually inspected. Synthetic
Gamepad objects and the fake host do not prove physical controller compatibility.
An attempted run in the installed Zen Firefox derivative could not start under
WebDriver. Firefox/Edge runtime acceptance is not claimed; Firefox is in CI.

Reproduction commands are in [the app README](../../overlay/README.md). For the
full companion smoke check, also build and supply the deterministic host:

```sh
cargo build --manifest-path overlay/Cargo.toml --features desktop --example companion_fixture
python3 overlay/scripts/browser_smoke.py --bundle overlay/dist \
  --companion-fixture overlay/target/debug/examples/companion_fixture
```

## Profile evidence

Source: `versions/ibex/1.0/ibex_single-set-default_hold-gyro_1.0.json`.
SHA-256: `bfd0072664145ed293a164c641eae13eb5e02a9c43b4d48d04977915e92229e0`.
The source was copied to `/tmp`, passed the layout-prep ordering/duplicate
checks, and was converted to readable titles for inspection. Source SHA-256
was checked again after implementation and remained unchanged.

The [export report](../../overlay/profiles/ibex-1.0-default.report.json) accounts
for ignored layer changes and the fresh-press assumptions. Base and Gyro face
outputs matched; the combined context matched for both press orders. Steering's
single-bumper contexts inherit the unmodified face labels; Menu Keys blocks
bumper modifiers. Unsupported output types, timing/settings and competing
activation policies produce unavailable labels rather than guessed bindings.

## Initial-build artifact measurements and open gates

At the initial build, WASM was **2,771,719 bytes**, or **1,271,306 bytes** compressed with
Python gzip. JS glue is **82,566 bytes**, or **12,316 bytes** gzip. The compressed
numbers describe artifact compression, not a measured HTTP download: the local
Python server does not automatically gzip responses. Dependency notices are
packaged separately and are not loaded at startup.

The following require Windows hardware and remain unfinished acceptance work:

- Link and smoke-test the Windows release/portable bundle on a clean account.
- Prove physical L1/R1 access with a named controller/connection, Steam Input
  active and a focused game. If SDL only sees remapped buttons, investigate
  device-specific HID before claiming native or companion gameplay support.
- Verify hotkey conflicts, HUD recovery/click-through/no-focus-steal, sleep,
  reconnection, DPI, multiple monitors and borderless games on Windows.
- Test real controller input in visible unfocused Chrome/Edge/Firefox pages,
  hidden-tab resume, and browser companion use beside a focused game.
- Measure native/browser idle and active CPU, memory, GPU, input-to-label latency
  and startup; establish numerical budgets from that hardware baseline.

Alternative L2/R2 profiles, native Linux/macOS, arbitrary layout import,
exclusive fullscreen and automatic Steam mode tracking remain outside this
first implementation. No site was published and no PR/commit was created.
