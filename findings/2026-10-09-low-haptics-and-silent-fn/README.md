# Low haptics and silent Fn entry

90.41 extends the live 90.40 builder. Every explicit Medium or High haptic
intensity becomes Low in both variants, including mode-level overrides and
individual activators. Explicit Off settings stay Off; omitted settings and
gyro bump-angle parameters are preserved.

The layer-add beep is disabled for `Menu Left: Fn Layer`, `Menu Right: Fn Layer`
and their two `Stateful` equivalents. Four delayed-entry commands per variant
change from `0 1` to `0 0`. Other entry routes into these Fn layers were already
silent. Menu Keys, Gyro and stateful mode-transition beeps are preserved.

The default layout has 82 intensity changes and alternative has 84. Both
retain 88 layers. Bindings, layer targets, selectors, execution order, timing,
repeat settings and the concise layout descriptions otherwise stay the same.
The 90.39 fallback-window experiment remains outside this builder chain.

## Inheritance and feedback

Base pad-click feedback and copied feedback inside Double Tap windows all use
Low. Left-pad arrow and right-pad mouse-button mode overrides also use Low,
while their explicitly silent scroll/cleanup activators remain Off. Cursor
gyro movement stays explicitly silent. Existing omitted settings keep their
inheritance/client-default behavior; this change does not introduce feedback
on previously unspecified bindings. Protected windows retain their blocks,
entry/exit order and timers.

The four repeating Steering/fallback feedback activators per variant keep
their configured 50 ms repeat interval but now specify Low. Their transitions
still replace the relevant bindings. Physical pulse counts and repeat timing
remain subject to the [documented Steam timing limitations](../../resources/Delay%20Timers%20and%20Repeat%20Rates.md).

## Build

```bash
python3 findings/2026-10-09-low-haptics-and-silent-fn/build_candidate.py --install
python3 -m tools.audit_build
node tools/convert_vdf.mjs neptune/single-set-default_hold-gyro_latest.json
node tools/convert_vdf.mjs neptune/single-set-alternative_hold-gyro_latest.json
```

The frozen previous builder runs its fix pipeline. This builder converts to
title form, changes only the two intensity property types and named Fn add
beep flags, then verifies the numeric roundtrip. It checks the expected edit
counts and that applying the feedback edit again makes no further changes.

Historical builder assertions retain their original feedback settings; live
scenario and cursor assertions now expect Low, and the ordinary/Stateful Fn
entry scenarios expect no beep. Saved verification results accompany this
record. Physical haptic strength and Fn silence need a fresh Deck load.

## Verification

- [Exact comparison with 90.40](exact-diff.json): only the 82/84 intensity
  changes, four Fn beep flags per variant and version title differ, including
  stored order. The concise descriptions are unchanged.
- [Preflight](preflight.json): both layouts retain valid ordering, sequential
  preset IDs, unique layer titles and numeric references.
- [Scenario run](scenario-tests.txt): all 255 tests pass. Every changed layer
  is reached: 39 default and 37 alternative, with no
  [coverage gaps](scenario-coverage.json).
- [Focused checks](focused-tests.txt): 12 layout/Steering checks pass. The
  cursor module initially failed to import its sibling helper because the
  command omitted `tests` from `PYTHONPATH`; its corrected
  [rerun](cursor-tests.txt) passes all 12 tests. No layout fix was needed.
- [Rule registry](rule-registry-tests.txt): all 27 tests pass.
- [Build audits](build-audit.txt): Budget, Window, Flow and Cleanup pass on
  both layouts. [Default](default-export.txt) and
  [alternative](alternative-export.txt) VDF exports verify keys, values and
  order. Both JSON/VDF pairs are saved under `versions/neptune/90.41/`,
  byte-identical to the working files; [manifest and hashes](manifest.json).
- [Unverified assumptions](unverified-assumptions.txt) preserve the distinction
  between simulator results and actual Steam timing/feedback.
