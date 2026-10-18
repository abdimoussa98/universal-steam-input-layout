# Plan: restore the gamepad viewer and lifecycle timeline

**Status:** implemented and verified locally on macOS and Linux Chrome.

## Implementation record

- Restored the original Ibex silhouette and binding-oriented controls, with
  Neptune and DSE control arrangements, all four back/Fn inputs, integrated pads,
  stick knobs and touch controls. Retained six release-derived layouts.
- Added read-only presentation of executed layer provenance for the complete
  lifecycle rail, including release-window output markers, combined ownership,
  held phases, second holds and cancellation. Execution timing is unchanged.
- Restored the trackpad explorer with labels and regions from the selected
  layout. Added rotation-aware mouse coordinates and prevented gesture drags
  from scrolling the page underneath their captured input.
- Reduced gyro to a 160 × 100 canvas directly beneath the gamepad, with compact
  activation/threshold feedback and optional motion controls in a window.
- Added native/WASM lifecycle tests and packaged browser checks for visual
  ordering/dimensions, stable targets, 1×/10× phases, real outputs in all six
  layouts, explorer overlap priority and narrow-screen usability.
- Local checks passed: Rust size/format, strict core/WASM/macOS Clippy, core and
  macOS tests, headless Chrome WASM tests, 20 Python tests, 25 JavaScript tests,
  and the expanded packaged browser suite on macOS Chrome 155.0.8059.79 and
  Linux Chrome 155.0.8059.84. Screenshots were reviewed at desktop and narrow
  widths. Windows and physical-controller verification remain CI/device checks.

The requested change was to make the existing browser viewer execute the real
layouts and add a small gyro visualization. Replacing the gamepad illustration
and its lifecycle timeline with a control grid and generic timer bars was a
scope mistake. Restore the previous presentation while retaining the new
layout compiler, execution engine and browser timing fixes.

This plan supersedes the presentation decisions in
[the layout-driven demo plan](2026-10-17-layout-driven-browser-demo.md).
The browser remains the product; the desktop HUD stays deprecated.

## Intended screen

```text
Compact layout/version selector, input connection and slowdown controls
─────────────────────────────────────────────────────────────────────
Minimal lifecycle timeline — no text unless a :: gesture is active
─────────────────────────────────────────────────────────────────────

                 Original illustrated gamepad
         Actual bindings, live highlights, interactive controls

                     Small gyro cuboid
                Activation + threshold indicator

                 Existing trackpad explorer
                  Expandable output / details
```

- Keep the previous gamepad silhouette, proportions, binding labels, control
  placement, trackpad visualization and visual styling as the starting point.
  Use the UI before commit `6dd6b05` as the visual reference.
- Keep the timeline above the gamepad, with a fixed 48 px allocation and its
  original thin rail. Idle has no text. Starting or ending a gesture must not
  move the gamepad or change a held pointer target.
- Put the gyro immediately below the gamepad at every viewport width. Target
  an approximately 160 × 100 px cuboid canvas with a compact status/threshold
  row. It must not become a large second column or displace the gamepad.
- Preserve the trackpad explorer below that row, using the selected layout's
  bindings and regions. Put verbose gyro controls, output playground, event
  history and raw stack/coverage information in expandable sections.
- Keep layout selection, actual mode, slowdown and controller connection easy
  to reach. Secondary playback/help controls can be grouped compactly. Modes
  continue to change through the selected layout's real gestures.

## What can be reused

The old presentation is still present in `overlay/src/ui/controller.rs`,
`ui/controller/controls.rs`, `ui/trackpads/`, `ui/timelines.rs`,
`ui/timelines/painting.rs`, `ui/theme.rs` and `ui/panels.rs`.
The browser now starts `DemoApp`, whose separate `demo_ui/controls.rs` draws
the replacement grid and whose `demo_ui/toolbar.rs` renders pending timers.

Simply switching back to `OverlayApp` would discard layout-driven behavior.
Its drawing code reads the old `FrameData`, profile and inferred gesture lanes.
Reuse the drawing and interaction conventions through a presentation model
fed by the current engine; do not run the legacy gesture engine alongside it.

## Implementation sequence

### 1. Establish the visual and behavioral baseline

- Capture the previous viewer in an isolated checkout and the current demo at
  the same viewport sizes. Record idle, active `::` lifecycle and trackpad
  states. Use these for side-by-side review of the restored presentation.
- Inventory the old diagram's control IDs and hit regions against the current
  engine's control/source IDs. Include stick touch, stick click, analog trigger
  travel, back buttons and DSE's whole touchpad/mute control.
- Keep the current six compiled releases, reference traces, motion behavior
  and browser clock fixture as the functional baseline.

**Gate:** a concrete mapping of existing drawing elements to engine inputs,
with no layout action lost because the old diagram had fewer controls.

### 2. Connect the original gamepad presentation to the layout engine

- Extract/adapt the original drawing into focused rendering modules under
  `demo_ui/`, with a typed view of resolved bindings, held states, analog
  values and available controls from `demo/`.
- Preserve the original Ibex diagram faithfully. Supply controller-specific
  geometry/capabilities for Neptune and DSE in the same visual style; represent
  the actual pad arrangement and available controls instead of presenting
  unsupported inputs as functioning buttons.
- Produce readable binding labels, including `::` summaries, from the compiled
  layout's binding graph. Keep full explanations in hover help. Do not revive
  the stale hand-maintained display profile or duplicate behavior tables.
- Route every mouse interaction through the current `Session::input` path.
  Retain press/release, right-click latching for chords, touch/click distinction,
  pad drags, stick movement/touch/click and trigger travel. Retain source/focus
  cleanup and pointer capture when a drag leaves its initial control.
- Share the pad model between the diagram and explorer so region priority,
  labels, contact markers, swipes and circular scrolling agree.
- Preserve current diagnostic IDs where possible, and add explicit geometry
  diagnostics for the controller, gyro and timeline. Hit tests must use the
  rendered geometry, clipping and pad rotation.

**Gate:** the restored diagram operates the selected layout with the same
outputs as the current demo, and resembles the previous viewer.

### 3. Restore the full lifecycle timeline

- Reuse the original rail, progress styling, release-window marker, compact
  binding summary and phase/countdown presentation.
- Add a typed lifecycle view derived from executed bindings, layer transitions
  and their provenance. Include the owner, binding summary, phase start,
  deadline when present, output marker and completion/cancellation state.
- The current `Engine::timers()` list is insufficient: it only exposes future
  first-fire deadlines and loses active holds after their timer has fired.
  Model the observable lifecycle from real engine execution rather than
  treating arbitrary pending timers as `::` gestures or guessing from text.
- Cover initial hold, release window, second hold, held/cover outcomes,
  combined gestures and interruption. Keep an active held phase visible until
  its lifecycle ends, even when it has no pending deadline.
- Preserve deterministic owner selection during overlapping gestures: a
  replacement output must not steal a still-active release-window timeline.
  Use the existing timeline tests as behavioral references, then add cases
  for the supported layouts and new input sources.
- Use the session's logical clock for progress, outputs and animation. Display
  the slowed wall-time countdown consistently with the previous viewer.
  Pause freezes it; stepping/replay advances it from engine events. Reset,
  source/layout changes and focus-loss cleanup clear stale lifecycle state.
- Hide all timeline text when no `::` lifecycle is active. General repeat
  timers, ordinary buttons and gyro motion must not populate the idle rail.

**Gate:** the original timeline behavior is restored at 1× and 10×, including
phases with no timer, without shifting the controller.

### 4. Make the gyro a small supporting widget

- Size the existing cuboid projection from its allocated rectangle so it fits
  the compact canvas at every rotation. Keep it centered below the controller.
- Retain drag-to-rotate and a clear inactive/active indication driven by the
  real layout gate. Show the blocking reason on hover or in expanded details.
- In Cursor Gyro, show a small movement-threshold meter and emitted-movement
  pulse; retain the optional threshold beep. Use the same logical clock so
  slowdown makes buildup and emissions understandable.
- Keep fine motion, roll, recenter, sound and calibration accessible through
  compact controls or an expanded gyro section. Resizing must not silently
  change the motion sensitivity or threshold behavior.
- Keep status and threshold space stable so activation never moves the
  gamepad, trackpads or an ongoing mouse target.

**Gate:** gyro activation and threshold feedback remain functional while the
gamepad remains the primary visual element.

### 5. Validate the actual screen and publish the correction

- Add rendering/geometry checks for timeline-above-gamepad, gyro-below-gamepad,
  compact gyro dimensions, blank idle timeline and stable control positions
  across lifecycle/gyro transitions. Inspect screenshots against the baseline.
- Check desktop and narrow viewports. Keep labels readable, preserve deliberate
  scrolling where needed, and verify targets cannot be clicked through clipped
  or off-screen content or open dialogs.
- Extend the packaged browser suite to click the restored diagram, verify
  emitted actions and timeline phases, and exercise all six layout selections
  with representative layout-specific actions rather than only title changes.
- Retain double-touch circular scroll at 1×/10×, the 200 ms slow-frame
  regression, gyro gate/threshold/audio, WebHID edge ordering and disconnect
  cleanup. Test both on-diagram pads and the explorer.
- Run the required Rust size/format, native/core/WASM Clippy and tests,
  Python/JavaScript checks, built WASM tests and packaged Chrome suite locally
  on macOS and Linux. Keep Windows and macOS CI adapter checks intact.
- Update the README and provide before/after screenshots with the correction.
  When implementation is authorized, commit/push the completed correction and
  verify the web CI result before reporting it finished.

## Completion criteria

The browser looks like the previous gamepad viewer, with its minimal lifecycle
timeline at the top and a small gyro visualization immediately underneath the
gamepad. All six layouts continue to drive labels, interactions, timing and
outputs through the shared engine. Restoring the presentation does not remove
the recently added functionality or reintroduce the CI gesture timing failure.
