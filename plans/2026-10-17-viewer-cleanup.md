# Viewer cleanup — first pass

Preserve the illustrated gamepad, the fixed-height minimal lifecycle timeline
above it, the small gyro below it, and all six executable layouts.

1. Fit the gamepad to both viewport width and available height. Compact the
   toolbar, keep mouse targets stable through input/lifecycle changes, and
   stack trackpad detail cards on narrow screens with wrapped instructions.
2. Show a compact, always-open output preview beside the main interaction area.
   Read actual emitted keys, pointer, wheel and axes from the existing engine.
   Keep the full output playground available and make enlarged pads expandable.
3. Separate gyro instructions/status from a real threshold meter. Only show the
   meter for active threshold-based gyro, preserve logical-clock feedback and
   slowdown, and make the compact panel fit narrow screens.
4. Verify desktop (1366×768), narrow (700px), and phone (390px/320px) geometry,
   visible output updates/reset, gyro activation/threshold, all layouts, and
   existing gesture/timeline/browser regressions. Run repository quality gates.

This pass does not change layout files, gesture thresholds, or execution rules.
The broader keyboard/accessibility work remains a separate follow-up.

## Acceptance

- Full controller and header controls fit within the viewport horizontally.
- On a 1366×768 viewport, the main gamepad, small gyro and output preview are
  visible together without scrolling.
- Output/lifecycle changes do not move controller or gyro mouse targets.
- Narrow trackpad detail captions wrap and cards stack without clipping.
- Idle gyro has no misleading filled meter; active cursor gyro shows buildup
  and output pulses. Normal and slowed gestures produce unchanged outputs.
- Native, WASM and packaged browser checks pass before completion.

## Implementation and validation

Completed the first pass locally:

- Viewport height and width now determine gamepad size. Its illustrated shape,
  layout-driven controls and fixed-height lifecycle rail remain intact.
- The toolbar uses compact speed controls and a More menu for Next event/Replay.
  The repeated header mode label is removed; input and layout selectors truncate
  within their available width.
- The fixed-size output preview reads emitted text, held/last keys, pointer,
  wheel and axes directly from the engine. It remains visible on laptop/phone
  viewports and does not move the input targets as its contents change.
- Trackpad detail expands on demand, stacks on narrow screens and wraps its
  instructions. Tiny integrated pads show an overview; expanded pads keep all
  directional labels and the same bindings.
- The gyro has separate instructions and a threshold meter. The meter appears
  only when threshold-based gyro is active, and buildup/output pulses retain
  the engine's logical timing. Narrow screens use the smaller cuboid.
- Added an inline controller favicon and updated the viewer documentation.

Passed checks:

- Rust size gate, formatting, strict core/web/macOS Clippy, native core and
  macOS desktop suites, including the existing reference traces.
- Headless WASM suites: 71 tests across runtime, behavior, motion, gestures,
  HID and pads.
- 25 JavaScript checks and 20 Python packaging/helper tests.
- Full packaged-browser suite on macOS Chrome 155.0.8059.79 and Linux Chrome
  155.0.8059.84 (the version pinned in CI).
- Browser regressions cover all six layouts at 1366×768, 700×900, 390×844 and
  320×740; actual visible output/reset; stable mouse targets; stacked captions;
  gyro meter buildup/pulses at 1× and 1/10×; and the relocated playback actions.
- Existing lifecycle, circular scroll, 200 ms slow-frame, WebHID and download
  checks remain enabled and passed. No layout thresholds or test delays changed.

Windows and physical controller acceptance were not run locally. Keyboard and
screen-reader support for the canvas controls remains follow-up work. The
results above are local; publication is tracked by the GitHub Actions run.
