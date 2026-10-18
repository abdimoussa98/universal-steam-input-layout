# Layout playground

An interactive browser demonstration compiled from the released Steam Input
layouts. Use a mouse without installing Steam or connecting a controller.
Choose Ibex, Neptune or DualSense Edge, Default or Alternative. The title shows
the **actual bundled version**; Details includes its release tag and source hash.
The demo never injects keyboard or mouse events into other applications.

The illustrated gamepad is the main view, with the original binding labels and
interactive pads. Its minimal lifecycle timeline sits above it; a small
gyro cuboid sits directly below (160 × 100, or 100 × 76 on narrow screens).
The gamepad fits the viewport width and available height. A compact output
preview shows emitted keys, pointer motion and scrolling without opening a panel.
Trackpad detail, the full output playground and extra analog controls expand
when needed; trackpad detail cards stack on phones. The
presentation reads the executable layout engine, including the timeline's
hold, release-window and second-hold phases.

## Try it

- Press/hold any controller button. Right-click to latch it for a chord, then
  right-click again to release. Hover for its resolved binding.
  Labels follow the active stack and immediate cursor cancellation: holding
  Mod 0 keeps A's inherited G visible before and after its Tap Cover activates.
  Explicit blocks and disabled sources remain blank.
- Select **Touch** or **Click** for the pads, then drag. Touch is finger contact;
  Click adds a physical press. Left-pad swipes type keys in the output playground.
- For right-pad circular scrolling, briefly touch and lift, touch the top/bottom
  within the release window, then circle. Clockwise scrolls down; reverse to go up.
  Both 150 ms windows stretch with the selected slowdown.
- Click a stick's binding label to press it, drag its lower knob to move it,
  and use **Touch** below the stick for capacitive contact. Expand **Analog
  controls** to adjust trigger travel.
  Back buttons, DSE mute and DSE's whole pad use their own compiled bindings.
- Enter **Cursor Gyro** by holding Select, clicking/releasing R3, then releasing
  Select. Hold RS touch on Ibex/Neptune to open its gyro gate. Drag the rectangular
  block for pitch/yaw or use Roll. Fine motion makes threshold buildup easier to
  see. Recenter changes only the displayed pose. Sound is optional. **Gyro
  controls…** opens roll, calibration and source help.
- Modes change through the layout's real gestures. For example, Start + L3
  enters Steering; Start + R3 enters Gamepad. The same gestures exit stateful modes.
  There is no manual layer picker in the main demo.
- Pause or reset from the toolbar; **More** contains Next event and Replay.
  Drag **Slow motion** from normal speed to 10× slower, including intermediate
  values. It changes the logical clock, keeping input, output and pending timers together.
  The top timeline has no text outside a `::` lifecycle. It stays visible through
  active held/cover phases even when there is no pending timer. Its fixed height
  keeps mouse targets stationary. Pad and gyro drags never scroll the page;
  use the mouse wheel or scrollbars to navigate the viewer.

The gyro shows activation help when off, and a separate threshold meter only
while threshold-based gyro is active. Its output pulse uses the same logical
clock as the timeline and slowdown.

The expandable output playground displays held keys/mouse buttons, typed text, pointer movement,
wheel output and gamepad axes. Details exposes the actual active stack, recent
events and a construct coverage report. Labels and behavior share one engine.

## Controller input

**Connect controller** uses the existing WebHID adapter for wired/wireless
Steam Controller 2 and the Steam Deck's built-in controller. Choose the connected
device in the source selector; Mouse and device input remain separate. HTTPS or
localhost and a browser with WebHID are required. Normalized Gamepad devices are
also selectable, but that API cannot provide pad contacts, capacitive touches,
grips or gyro. Unsupported signals remain unavailable.

Ibex/Deck IMU axes, scales, timestamps and grip bits follow the pinned SDL 3.4.18
protocols and have synthetic-report tests. Calibrate at rest removes a stationary
bias. Physical device/browser acceptance is still required; synthetic tests do
not establish live hardware accuracy. The optional native companion supplies
sampled input to the browser and retains its existing executable/pairing URL.

## Fidelity

Digital execution follows the repository's documented simulator assumptions:
ordered layer operations, inheritance/blocking, held-input rebinding, delayed
and repeating activators, chord interruption, release ownership, mode shifts and
the existing native Gamepad Long/Double Press exceptions. Generated reference
traces run against both native Rust and WASM.

Analog response remains a **browser approximation**, explicitly listed in
Details. The JSON does not specify Steam's complete transfer functions/defaults.
The gyro movement gate accumulates motion, as described in
[Valve's input-source documentation](https://partner.steamgames.com/doc/features/steam_controller/input_source_modes).
The exported threshold's exact physical scale, precision response and haptic
cadence still need device comparison. The threshold number is shown in demo
output units; the optional threshold tick is explanatory feedback, separate
from layer-change beeps and physical haptics. Circular scrolling uses the
exported `scroll_angle` with a documented tenths-of-a-degree demo convention.
Pointer acceleration/inertia, response curves and OS key composition are not
claims of pixel-for-pixel Steam or operating-system equivalence.

## Build and validate

```sh
python3 -m tools.compile_demo             # latest immutable tags, all six layouts
python3 -m tools.compile_demo --check     # reject stale generated data
python3 -m tools.demo_traces              # regenerate Python reference traces
python3 overlay/scripts/build_web.py     # compile releases, Rust/WASM and downloads
python3 -m http.server 8080 --bind 127.0.0.1 --directory overlay/dist
```

Full Git history/tags and the existing Rust/WASM toolchain are required. Unknown
commands, modes, activators and setting names fail compilation. Source JSON/VDF
files are never edited by the compiler. The web build compiles the same releases
it bundles for downloads. The download dialog can offer a newer release, and
explicitly distinguishes it from the demo's version.

Run the checks in [AGENTS.md](AGENTS.md), including the packaged browser suite:

```sh
python3 overlay/scripts/browser_smoke.py --bundle overlay/dist --webhid
docker run --rm --platform linux/amd64 --shm-size=1g \
  -v "$PWD/overlay:/work/overlay:ro" keybind-browser-check:155
```

Normal browser tests use **zero extra WebDriver delay**. The 650 ms latency stress
run remains optional. Gesture scenarios control the browser's monotonic clock
and wait for each real frame, so slow rendering cannot turn a 60 ms tap into a
hold. They assert input timestamps at 1×/10× and include a 200 ms slow-frame
regression. Playback checks also control this clock so driver latency cannot
expire the pending event before Pause or finish replay before it is observed.
The suite also checks all six layouts' gesture outputs, timeline
phases and geometry, the trackpad explorer, and 320/390/700px mouse controls.
Laptop checks also keep the gamepad, gyro and output preview on screen together;
visible output and threshold-meter checks run against the real rendered app.
The fixture does not change the packaged app or its layout timings.
An additional Rust/WASM regression checks inheritance against the Python source
layout audit for every declared layer: 2,650 family-chain stacks and 134,550
binding lookups across the six bundled layouts. This covers binding ownership,
explicit blocks, and mode barriers, not every timed or stale-stack combination.
Regenerate its source-derived fixture with `python3 overlay/scripts/demo_inheritance.py`
after refreshing the catalog; the web build also refreshes it for release builds.
Use `--driver` and `--browser-binary`
to select matching local executables. Deployment remains at the existing URL;
see [deploy/README.md](deploy/README.md).

## Desktop overlay deprecation

The desktop HUD, click-through window and global mode hotkeys are deprecated.
Windows and macOS executables now start the input-only companion. CI retains
both native adapter checks and publishes helper binaries, without desktop HUD
packaging. Historical UI/gesture code remains for compatibility and regression
tests; [README.legacy.md](README.legacy.md) and `scripts/browser_legacy.py` record
the retired manual-reference product. The browser restores its illustrated
presentation using the executable layout engine, without legacy gesture inference.

The `overlay/`, executable, WASM and container identifiers remain compatible with
existing deployments. Renaming them is a separate migration, not a prerequisite
for using the browser product.
