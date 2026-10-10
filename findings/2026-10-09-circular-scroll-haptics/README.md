# Circular scroll haptics on the 90.38 layout

90.40 continues directly from 90.38. The only layout behavior change is Low
haptic feedback for the right trackpad's circular scroll wheel, in both
default and alternative variants. The 90.39 fallback-window experiment is
outside this builder chain.

## Layout change

In `RTP: Circular Scroll`, the active `right_trackpad` group uses
`mode: "scrollwheel"`. Its group setting `haptic_intensity` changes from
`"0"` (Off) to `"1"` (Low). Each group belongs only to that layer: default
group 13187 and alternative group 13194. Local Low-value precedent is recorded
in the [pad haptics plan](../../plans/2026-10-04-pad-bumps-and-menu-layer.md).

The scroll directions, angle, click and release activators, layer transitions,
delays and repeat settings remain those of 90.38. Both layouts still have 88
layers. The complete descriptions were reviewed and retained; the release
title advances to 90.40 to keep the two exported revisions distinguishable.

The Base mouse group has silent haptics. The explicit scrollwheel setting
overrides it while Circular Scroll is active, including over Steering and its
fallback guard, which inherit right-pad gestures. A middle click temporarily
switches to the mouse mode in `RTP: Middle Click`; exiting it exposes the scroll
mode again. Click and touch-release activators remain explicitly silent. No
group is shared with another owner or referenced by a mode shift.

## Delay and repeat observations

The author's 2026-10-09 Deck observations are documented in
[Delay Timers and Repeat Rates](../../resources/Delay%20Timers%20and%20Repeat%20Rates.md).
Layer removal can accelerate held repeats; delay resets are inconsistent; and
an immediate add/remove transition can make a follow-up delay fire immediately,
including the reported cursor-driver example. Critical state changes must not
depend on precise delays or repeat intervals. This release records those
limitations without changing the timing bindings.

## Build and verification

```bash
python3 findings/2026-10-09-circular-scroll-haptics/build_candidate.py --install
python3 -m tools.audit_build
node tools/convert_vdf.mjs neptune/single-set-default_hold-gyro_latest.json
node tools/convert_vdf.mjs neptune/single-set-alternative_hold-gyro_latest.json
```

The builder imports frozen 90.38 directly, runs that builder's fix pipeline,
converts to title form for the setting change, then verifies the conversion
back to numeric IDs.

- [Exact comparison and preflight](preflight.json): the title version and one
  haptic value are the entire difference from 90.38, including stored order.
- [Build audits](build-audit.txt): Budget, Window, Flow and Cleanup pass on
  both variants.
- [Focused regressions](regression-tests.txt): 23 tests pass, including scroll
  entry in Steering/fallback, clicking over scroll and returning to it, and
  touch-release cleanup. [Coverage](scenario-coverage.json) reaches the changed
  layer in both variants. The full Python suite was not rerun for this setting.
- Documentation checks: 27 rule registry tests and 11 scenario registry tests
  pass after updating the timing observations. The
  [assumption report](unverified-assumptions.txt) records remaining uncertainties.
- [Exporter tests](exporter-tests.txt): six pass. Both exports pass key, value
  and stored-order verification; [default](default-export.txt) and
  [alternative](alternative-export.txt) logs are saved.
- [Manifest](manifest.json): both JSON/VDF pairs under
  [versions/neptune/90.40](../../versions/neptune/90.40/) are byte-identical to
  the working files. See the [verification summary](verification-summary.json).

Physical haptic strength is not modeled by the scenario simulator. On a fresh
Deck load, enter circular scroll and rotate both ways, then hold and release a
middle click and scroll again. Check the Low feedback in Base and Steering.
