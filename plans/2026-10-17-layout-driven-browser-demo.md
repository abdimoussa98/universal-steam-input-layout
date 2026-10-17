# Plan: a layout-driven browser demo

**Status, 2026-10-17:** implemented as the browser product, with the analog and
hardware fidelity limits below. Source layout JSON/VDF files remain unchanged.
Supersedes the desktop-overlay direction of the
[initial viewer plan](2026-10-15-rust-keybind-overlay.md).

The product is an interactive browser demonstration of the actual layout.
Someone without a controller should be able to perform its gestures, see the
resulting actions, and slow them down to understand them. Connected controllers
can supply the same inputs. Deprecate the Windows desktop HUD and its overlay
controls. A native input companion, if retained, serves only browser input.

## Implementation record

- Added a reproducible compiler and construct inventory for both variants of
  tagged Ibex 1.2, Neptune 90.78 and DSE 1.2. The web build compiles its bundled
  releases; unknown commands, setting names, activators and source modes fail.
- Added the shared Rust execution engine for layers, inheritance, disabled
  overrides, chords, held-input ownership, timers, native Gamepad press
  exceptions and mode shifts. The demo uses the layout's real stateful routes.
- Replaced the manual-reference viewer with mouse-operated controls, pad
  touch/click and circular scrolling, swipes, sticks, triggers, grips, DSE
  controls and a visible output playground. Controller sources are explicit.
- Added the rotating gyro cuboid, resolved activation status, threshold buildup
  and emissions, optional sound, recenter and hardware motion decoding. Sound
  follows individual runtime events; pause/reset/hiding cancels scheduled audio.
- Added one logical clock, slowdown, blank idle timeline, recording/replay,
  pause and next-event stepping. Fixed-size motion integration keeps held-stick
  output independent of render frequency. Source/focus changes clear sessions.
- Added 880 Python-reference traces, native/WASM runtime and analog tests,
  protocol-report tests, and packaged Mac/Linux Chrome scenarios. Browser
  pointer sequences run inside the page; popup clicks wait for stable rendered
  geometry. Normal tests retain zero extra WebDriver latency.
- Deprecated the desktop HUD and its packaging. Windows/macOS launch the
  input-only companion; native adapter CI stays in place. Historical code/docs
  are retained for compatibility. Folder, executable and hosting identifier
  renaming remains a separate migration, as planned.

Implementation entry points: [compiler](../steam_layout/demo_compile.py),
[runtime](../overlay/src/demo/mod.rs), [browser UI](../overlay/src/demo_ui/mod.rs),
[browser acceptance suite](../overlay/scripts/browser_demo.py), and
[usage/build instructions](../overlay/README.md).

### Fidelity boundaries

Digital semantics follow the repository's documented simulator assumptions.
The coverage report explicitly describes simplified analog behavior: linear
stick response, direct pad movement without trackball inertia/acceleration,
continuous directional keys without Steam duty-cycle modulation, and a
documented demo conversion for `scroll_angle`. Gyro accumulation follows Valve's
documented minimum-movement principle, but threshold units, precision response,
projection and feedback cadence remain browser approximations. Optional gyro
ticks explain emitted movement; they do not claim to reproduce physical haptics.
The playground shows key events and simple text, not full operating-system text
composition. Gamepad API inputs cannot supply absent touch/gyro/grip signals.

Local acceptance includes strict core/WASM/macOS Clippy, size/format checks,
native tests, Python/JavaScript packaging tests, headless Chrome WASM tests,
workflow validation and packaged Chrome on macOS and Linux (CI's pinned
155.0.8059.84). The browser suite checks actual output, sound/mute, 1×/10× scroll,
all six selections, queued HID edges, gyro input and disconnect cleanup.
Windows adapter execution and physical-controller/Steam comparisons are not
locally verified. These are stated limits, not evidence of hardware parity.

## Findings before implementation

| Area | Current implementation | Missing behavior |
|---|---|---|
| Layout source | Bundled `Ibex 1.0 · default` display profile; current tagged layouts are Ibex 1.2, Neptune 90.78, DSE 1.2 | Execute the selected released layout; keep demo identity and download identity aligned |
| State | Manual Base/Gyro, Steering and Menu pages; four gesture-owner lanes | Actual layer operations, persistent transitions, distinct Base/Gyro/Cursor Gyro/Gamepad behavior, concurrent gestures |
| Right trackpad | Exports double-touch timings and scroll labels; paints touch/click references | Touch/release window, second-touch position, circular motion, actual wheel output, cleanup |
| Left trackpad | Swipe labels and click-region previews | Swipe recognition and key lifecycles, click entry/overlap arbitration, held outputs |
| Virtual input | Sixteen buttons; triggers are effectively fully pressed or released; pad clicks are UI feedback | Independent pad touch/click, stick dragging/touch, analog trigger travel, grips/back buttons, controller-specific inputs, simulated gyro |
| Gyro visualization | No gyro samples/orientation in the shared input frame and no motion visualization | Rotating rectangular block, actual activation gates, Cursor Gyro movement threshold and motion feedback |
| Outputs | Binding labels and predicted gesture phases | Key down/up, pointer movement, mouse buttons, wheel steps, gamepad outputs and feedback visible in a playground |
| Controller variants | Exporter supports the reviewed default Ibex family; hardware connection does not select a matching layout | Both variants of all three controllers, their distinct geometry and capabilities |
| Tests | Some pad reference/geometry tests; existing Python layer scenarios | Browser gestures asserting emitted actions and cleanup, plus runtime parity against layout scenarios |

Evidence: [profile exporter](../steam_layout/overlay_profile.py),
[pad exporter](../steam_layout/overlay_trackpads.py),
[pad reference types](../overlay/src/core/trackpads.rs),
[pad UI feedback](../overlay/src/ui/trackpads/feedback.rs),
[mouse preview](../overlay/src/ui/preview.rs),
[input types](../overlay/src/core/input.rs), and
[gesture uncertainty rules](../overlay/src/core/gestures/sample.rs).
The current pad `double_tap`, `swipe` and `repeat_ms` data describe bindings;
they do not implement those gestures. Pad activity can instead interrupt the
four-lane gesture inference. Adding another caption cannot fix this.

The repository already has a useful [press simulator](../steam_layout/simulator.py)
and [scenario vocabulary](../tests/scenario.py). Reuse their tested semantics and
expected traces. They are not a complete analog or motion engine: continuous
pad/stick/gyro movement needs additional modeling, and mode-shift support must
be checked per pattern rather than assumed complete.

## Design decisions

1. **The selected layout is authoritative.** Compile its JSON into a versioned,
   executable data model. Preserve inputs, active source groups, mode-shift
   targets, activators, settings, commands, inheritance and timers. Generate
   labels from the same data. Do not maintain separate binding tables in the UI.
2. **Keep layers internal.** Their ordering, blocking, cleanup and timers are
   essential to correct behavior. The normal UI shows the resulting mode,
   available actions and outputs; no manual layer selection is needed. An
   optional inspector can explain the active stack and why an action fired.
3. **One execution engine.** Keep Rust/WASM and reuse the existing browser UI and
   input adapters. Virtual input, WebHID and Gamepad input feed the same engine.
   Python remains the build-time compiler/reference-test infrastructure.
4. **Observable actions inside the page.** Provide a virtual keyboard/text area,
   pointer target, scrollable content and gamepad indicators. Apply structured
   engine outputs directly to that playground. The demo does not need to send
   operating-system input or control another application.
5. **Explicit fidelity.** Distinguish implemented behavior, simulated feedback,
   unavailable hardware input and unresolved Steam behavior. A layout contains
   configuration, but does not fully specify Steam's implementation or every
   default. Use the repository's documented assumptions and name unresolved
   ones; do not silently guess or claim complete Steam equivalence.

## Implementation sequence and acceptance gates

### 1. Inventory and compile the real layouts

- Start with tagged Ibex 1.2 Default as the first complete vertical slice.
  Inventory both variants for Ibex, Neptune and DSE from the outset. Record
  source tag, controller, variant, schema and SHA-256 in each compiled artifact.
- Reuse `steam_layout.model`, binding resolution and the controller registry;
  add focused compiler modules and a CLI under `steam_layout/` and `tools/`.
  Work on analysis copies. Leave generated layouts and tagged snapshots intact.
- Resolve numeric layer references without losing identity, command execution
  order or source provenance. Retain dormant groups referenced by mode shifts.
  Distinguish inheritance, explicit empty bindings and active disabled sources.
- Generate a coverage manifest for every behavior-bearing command, setting,
  activator and source mode: implemented, intentionally visualized, unsupported,
  or unreachable with a recorded reason. Classify presentation metadata
  separately. Unknown behavior must fail compilation or mark a development
  build incomplete; it must never disappear silently.
- Inventory the twelve source modes present in current Ibex Default:
  `four_buttons`, `dpad`, `trigger`, `joystick_mouse`, `2dscroll`, `single_button`,
  `gyro_to_mouse`, `disabled`, `absolute_mouse`, `switches`, `scrollwheel`, and
  `joystick_move`. Inventory both variants and the other controllers separately.
- Share the selected release identity with the download catalog. When a newer
  release cannot yet be executed by the runtime, show the demo's actual version
  and compatibility status rather than silently labeling an old demo current.

**Gate:** reproducible artifacts and a complete gap manifest for all six layouts;
the compiler rejects an injected unknown command and detects stale artifacts.

### 2. Build the execution core and make right-pad scrolling work first

- Add domain modules for executable layout data, source resolution, activators,
  scheduling, outputs and analog interpretation. Follow the existing Rust size
  and Clippy limits; avoid a monolithic Steam interpreter.
- Implement layer add/remove/hold ordering, source-mode inheritance, held-input
  rebinding, release ownership, chords/Any/All/inversion, interruption, delays,
  repeats and always-on expiry. Preserve bottom-to-top binding arrays and the
  repository's held-input and timer-reset semantics. Bound same-timestamp
  processing so a malformed layout reports an error instead of hanging.
- Preserve output ownership: multiple bindings can hold one key; one binding
  releasing must not release another owner's key. Preserve handovers without
  inventing duplicate presses. Keep wheel pulses distinct from held keys.
- First connect virtual right-pad touch, position and click to this core, then
  to a visible scroll target. Use the actual layout's entry, window and scroll
  bindings; do not add a separate hardcoded double-tap shortcut.
- Current Ibex behavior to prove: lift the first touch before its 150 ms cover;
  touch the upper/lower region inside the 150 ms release window; rotate clockwise
  for Scroll Down and counterclockwise for Scroll Up. Center/side re-entry,
  expired windows and a long first touch take their configured pointer routes.
  Release and click transitions follow the layout's cleanup and click-entry
  rules. Import region thresholds and scroll settings, including `scroll_angle`,
  and verify their units/defaults before translating movement into wheel ticks.
- Handle angle wraparound, direction reversals, stationary contact and center
  jitter. Re-entering scroll must not reuse an earlier touch's accumulated angle.

**Gate:** a mouse-only browser user can double-touch and circle the right pad and
see content scroll in both directions. Tests assert emitted wheel events, no
spurious output on rejected entry paths, cleanup, and operation at 1× and 10×.

### 3. Finish input and behavior coverage

| Family | Required coverage |
|---|---|
| Buttons | Face/D-pad/menu, bumpers, stick clicks, all four grips/back buttons, controller-specific controls; held chords and press order |
| Triggers | Soft/full pull, thresholds and hysteresis, independent travel, default and alternative modifier roles |
| Trackpads | Left swipes, right pointer and circular scroll, center/outer clicks, overlap winner, delayed/repeating clicks, touch/click independence, mode-dependent blocks |
| Sticks | Continuous position, directional/deadzone/edge behavior, touch and touch-release gestures, movement/aiming, steering rocking and ramp transitions |
| Stateful routes | Base, Gyro, Steering, Cursor Gyro, Menu Keys and Gamepad reached through their actual gestures, plus exits and reset |
| Timed/modifier routes | Single tap, hold, tap-then-hold, combined modifiers, both menu press orders, Fn, cancellation, recovery, concurrent inputs and timers |
| Gyro and feedback | Rotating rectangular block, enable/disable/ratchet conditions, response settings and ramps; Cursor Gyro threshold and motion feedback; virtual motion control and optional sound, with hardware capability stated |
| Controller differences | Neptune touch/pressure behavior; DSE whole-pad swipes/clicks, mute, remapped grips, absence of stick touch and different gyro gating |
| Native activator exceptions | Existing Gamepad Long/Double Press behavior; do not rewrite the layout's allowed exceptions into the common timed-layer pattern |

- Expand the input vocabulary beyond the current sixteen-button array and four
  gesture owners. Keep unsupported physical signals unknown rather than false.
- Offer a small Touch/Click choice for virtual pads: touch mode uses press/drag/
  release as finger contact; click mode adds pad pressure/click to contact.
  Hover alone remains an inspection aid. Make both available on the controller
  diagram and enlarged pads. Preserve button hold/pin interactions for chords.
- Add draggable sticks, explicit stick-touch controls, trigger travel controls,
  reachable grips/back buttons and virtual gyro movement. Use pointer capture
  and handle pointer cancellation, focus loss and disconnect without stuck input.
- Keep virtual and physical sessions explicit. Selecting an input source or
  resetting clears its held outputs; do not silently mix a mouse gesture with
  a connected controller's unrelated state. Replay should work without hardware.
- Labels, highlights, current mode and output log all read the same engine
  snapshot. Show source binding and reason in optional details, not a parallel
  prediction model.

**Gate:** every supported layout behavior has an executable acceptance scenario
and observable result. No unsupported behavior is hidden behind a plausible label.
All six controller/variant selections run with their own inputs and mappings.

### 3a. Gyro visualization and Cursor Gyro feedback

The requested gyro representation is a **3D rectangular block (cuboid)** with
distinguishable faces so pitch, yaw and roll are readable. This is part of the
browser demo's required functionality, not a later decorative addition.

- Rotate the block from the selected input source's motion, including when the
  layout gates gyro output off. Separately show **Off**, **Ready** (enabled,
  without emitted movement), and **Moving**, using text/icon as well as color.
  Show Cursor Gyro as the effective response mode when its settings apply.
  Details explain an inactive gate, such as a required touch or disabled source.
- Derive activation from the effective gyro source, inherited settings, Any/All
  selectors, ratchet conditions and active disabled overrides. A layer named
  `Gyro` or `Cursor Gyro` being present is not sufficient evidence that output
  is enabled. Cover persistent and temporary Cursor Gyro and their exits.
- Let a user drag the block to simulate pitch/yaw, with a roll control and a
  recenter action. Generate timestamped motion samples for the same engine as
  physical motion. View recentering must not itself emit pointer movement or
  feedback. Label simulated motion and unavailable device motion clearly.
- Extend input adapters with calibrated angular velocity/orientation where the
  device protocol actually supports them. Validate axes, units, sample intervals
  and integration before claiming live motion support. The current shared input
  frame does not carry those signals; reading buttons over WebHID is insufficient.
- Beside the block, show the resulting playground pointer and a compact movement
  threshold indicator: raw motion, the amount held back by the gate, and emitted
  movement. A reference marker/trail makes small motions visible without making
  the indicator look like a fixed angular deadzone. Determine whether Steam's
  minimum movement threshold accumulates, discards or steps small movements,
  and how it rearms, before implementing that behavior or assigning physical units.
- Compile response and feedback settings from the selected layout and resolved
  stack. Current Ibex 1.2 Cursor Gyro and both temporary cursor sources explicitly
  set `mouse_move_threshold: 5`, `flickstick_haptic_bump_per_angle: 1`,
  `haptic_intensity: 0`, and `gyro_precision_speed: 750`; sensitivity and activation
  properties are inherited. Do not treat the raw `5` as five degrees or pixels,
  or assume the haptic bump interval and movement gate are the same threshold.
- Represent the requested movement feedback with a visible pulse and optional
  audible beep/tick. Verify which motion events and settings produce that
  feedback, including the interaction with `haptic_intensity: 0`; preserve its
  actual cadence rather than sounding once per rendered frame. Distinguish this
  browser representation of motion/haptic feedback from the layout's separate
  layer-change beep commands. Provide a sound toggle, visual feedback while
  muted, and enable audio through an explicit user interaction.
- Drive block pose, gate status, pointer output, pulse, sound and trace from the
  same timestamped simulation events. Slow motion stretches their timing
  together; pause stops them and replay reproduces them. Do not replay queued
  sound in a burst after focus returns or mutate threshold values to slow time.

**Gate:** mouse-only users can enter Cursor Gyro through its real gesture, rotate
the block, observe below-threshold behavior, cross/rearm the movement gate and
see/hear the corresponding feedback. Repeat at 1× and 10× and compare logical
output/feedback traces. Test yaw/pitch/roll, reversal, jitter, stationary input,
gated-off movement, temporary/persistent cursor exits, recenter, mute, pause and
disconnect. Enabling gyro must not replay motion accumulated while it was off.
Before claiming Steam fidelity, document threshold units/reset semantics and
feedback cadence from a reference capture or verified source. Unverified motion
behavior remains marked as an approximation in the coverage report.

### 4. Unify simulation time, slowdown and explanation

- Use one monotonic logical clock for inputs, delayed activations, repeats,
  expiry, motion samples, output events and timeline rendering. Advance by
  elapsed wall time divided by speed; changing speed must not jump timestamps.
- Preserve ordering when several input edges occur within one rendered frame.
  Drain due work at its deadline, not at the next WebDriver response or repaint.
- Keep the fixed, minimal timeline above the viewer. It has no text when idle;
  timed binding lifecycles reveal their pending actions and progress. Derive
  it from actual pending runtime work, including pads, instead of four fixed
  button recipes. Concurrent timers remain inspectable.
- Add pause, reset, replay and next-event stepping. Pause must define what
  happens to incoming live input; resumption must not replay a burst of stale
  presses or leave outputs held. Recorded input retains logical timestamps.
- Run an identical replay at 1× and 10×: it must produce the same logical event
  sequence and outputs, with only wall duration changed. Include every timer
  family, repeats and continuous-motion interpretation in this contract.

**Gate:** timing boundaries are deterministic at deadline minus 1 ms, exact
deadline and plus 1 ms; speed changes and pause/resume preserve a coherent state;
the rendered timeline agrees with output events.

### 5. Validate completeness and retire the desktop overlay

- Turn reviewed Python scenarios into reusable timestamped inputs and expected
  stack/output traces. Run those against Rust and WASM for the semantics the
  Python simulator models. Treat documented alternative Steam assumptions as
  explicit test cases, not a reason to claim hardware verification.
- Add independently specified continuous-motion tests for geometry, threshold
  crossings, circular scrolling, pointer movement and gyro. These fill the gaps
  that digital press scenarios cannot verify.
- Add browser scenarios through actual mouse/pointer interaction and supported
  input adapters. Assert visible playground effects as well as runtime state;
  checking that a caption contains “scroll” is insufficient.
- Keep normal CI at zero extra WebDriver delay. Use logical-clock tests and
  in-page timed input sequences for boundaries. Keep the 650 ms driver-latency
  run optional. Run the packaged browser suite locally on Linux Chrome matching
  CI before publishing input/runtime changes; retain macOS browser checks too.
- Gate completeness on supported constructs plus meaningful scenario coverage
  for each input family, transition/exit and interruption path. Merely visiting
  every layer, or counting tests, does not prove all behavior works. A changed
  binding must regenerate the artifact and identify affected scenarios.
- Update product copy and entry flow to the browser demo. Remove desktop HUD,
  click-through, window-opacity and global-hotkey affordances from the product.
  Retire desktop-overlay packaging/jobs once shared runtime dependencies are
  separated and browser gates pass. Keep useful WebHID/Gamepad adapters and an
  optional input-only companion; do not make a native helper a demo requirement.
- Archive desktop-only code with a repository record. Rename `overlay/` and
  crate/package/workflow identifiers in a separate final migration, updating
  hosting, scripts, tests and documentation together. Keep the deployed browser
  URL usable throughout the transition.

**Gate:** the browser is the primary supported product, its selected layout
version is explicit, the full coverage report passes, and every remaining
fidelity/hardware limitation is identified. Only then describe it as a complete
representation of that layout under the documented runtime assumptions.

## Original checks performed while planning

- All six working layouts have ordered layers and presets, sequential preset
  IDs and unique layer titles. Current release tags exist locally for Ibex 1.2,
  Neptune 90.78 and DSE 1.2.
- Converted an Ibex Default analysis copy to readable targets under `/private/tmp`.
  Its command-budget audit passed, including the registered Gamepad activator
  exceptions and six permitted fourth-entry resets.
- Ran `MenuComboKeys.test_the_right_pad_double_tap` from
  `tests.scenarios.neptune.test_scenarios_90_6_to_90_9` with
  `SCENARIO_CONTROLLER=ibex` and `SCENARIO_CONTROLLER=neptune`; both passed
  (the scenario covers both variants). This verifies reference layer-entry
  behavior, not continuous circular motion or browser behavior.
- No application code changed, so no browser build or full Rust suite was run
  for this planning document. Implementation starts with stages 1 and 2.
- Gyro follow-up: inspected the current Ibex gyro groups and their explicit
  cursor response settings, and the repository's documented inheritance policy.
  This establishes configuration values, not Steam's physical threshold units
  or motion-feedback cadence. Those require verification during stage 3a.
