# Viewer inheritance and slow-motion slider

Restore a draggable 1–10× slow-motion control and show the bindings available
through the current layer stack, including immediate cursor cancellation.

1. Restore the slider without changing the shared logical clock, pause, replay,
   timeline, or gyro timing. Preserve browser target IDs and compact sizing.
2. Reuse runtime stack resolution and chord arbitration for presentation. Follow
   immediate removal-only exits to the newly exposed binding. Preserve explicit
   empty bindings, disabled sources, mode boundaries, and delayed exits.
3. Check inherited pad labels through the same modifier/cursor transitions.
   Keep the gamepad, top timeline, and small gyro.
4. Add targeted regressions across all six released layouts; validate formatting,
   size gates, core/desktop/WASM checks, and the packaged browser including narrow
   screens and slider interaction. Leave source layout files unchanged.

Reproduction: hold the primary modifier through its cursor delay. Its temporary
cursor layer replaces face inputs with self-removal. A displays “—” although
pressing it exposes the parent's G/H binding. Ordinary omitted inputs already
inherit in the execution engine; the missing part is the presentation of exits.

Implemented:

- Restored the draggable integer 1–10× slider, preserving speed target IDs and
  using the existing session clock. Browser coverage drags to 7× and verifies
  halfway progress through the hold window.
- Shared chord arbitration and stack lookup with presentation. Labels walk only
  immediate removal-only exits; rendering never mutates the live engine.
- Added regression coverage for both cursor overlays and all twelve ordinary
  cancellation controls across six layouts, inherited pad labels, explicit
  blocks, chord guards, disabled/mismatched modes, and delayed exits.
- Browser checks assert actual painted labels and output: holding Mod 0 shows G,
  pressing A emits G and keeps the cover's inherited label, release restores F.

Validation: size gate, formatting, core/web/macOS strict Clippy, core/macOS
tests, 75 headless WASM tests, 25 JavaScript tests, 20 Python tests, and the full
packaged browser suites on macOS and Linux Chrome 155.0.8059.84 (the CI version)
passed, including viewport, gyro, and playback checks. Windows and physical
devices were not tested locally. Publication is tracked by the GitHub Actions run.

Follow-up all-layer audit:

The original scenario traces did not cover every layer. A new source-derived
fixture uses the existing Python family-chain inheritance audit as an independent
oracle for the Rust/WASM resolver. It covers all 91 layer/set records in each
Ibex/Neptune variant and all 75 in each DSE variant: 2,650 stacks and 134,550
binding lookups. All passed locally. The check also fails if a declared layer
is missing from coverage or the fixture no longer matches its released source.
This is a binding-resolution check; timing, held-input mode shifts, arbitrary
stale stacks, analog response and physical Steam behavior have separate coverage
and are not exhaustively proved by this matrix.
