# 90.48 — Quiet Gyro gestures and Steering entry cleanup

Status: 90.48 exported and backed up for both variants. The remove-only Guard proposal remains deferred.

`Steering` now only adds W/S on its driving inputs. Its redundant Entry
Guard removal is gone. Default uses bumpers; alternative uses trigger soft
pulls. Quiet, uninterruptible 50 ms repeating self-chords are preserved.

Quick Base/Gyro toggles already requested no haptic. The remaining two-driver
hold bump came from the 200 ms combined-cover adds. Those four adds per
variant are now Off in the two ordinary and two Gyro Modifier 2 owners.
Release commands and beep flags are unchanged; Steering Modifier 2 retains
its existing cover bump.

Exactly six input bindings change across five owners per variant. There
are still 88 layers, with no runtime-ID or tuning changes. The release title
advances to 90.48. Both full descriptions were reviewed and retained.

## Why Guard's handoff remains atomic

The requested direct split was tested against validated 90.47 candidates:
Guard removes itself, then Steering's newly exposed repeating chord adds
W/S. With LS already fully up/down, Steering can clear first: 112 of 128
cases per variant failed under the simulator's held-input exposure and tie
order settings. These failures are simulation evidence, not native tests.

An experimental 100 ms clear delay made all 256 cases pass. It was briefly
installed locally for validation, then backed out before export because
[Delay Timers and Repeat Rates](../../resources/Delay%20Timers%20and%20Repeat%20Rates.md)
records the author's observation that layer changes can make delays fire
early. Its instruction is: **“Do not make mission-critical behavior depend
on a delay, a repeat interval, or their ordering across layer changes.”**
A simulated deadline cannot establish safe runtime ordering here.

The final layout therefore retains Guard's atomic remove-self-and-add-W/S
handoff and the existing immediate full-deflection clear. No new delay is
installed. The preference question offers retaining that handoff or planning
a broader clear redesign before separating it. A remove-only Guard remains
pending; it is not claimed as implemented.

The experimental builder and candidates are explicitly named
`experimental-delayed-split*` / `*-experimental-delayed-split.json` and are
not exports. `targeted-initial.log`, `timing-regressions.log`, and the initial
`validation.log` concern that rejected timing experiment. Final evidence is
recorded separately. Baseline probes read 90.47 candidates, not snapshots.

## Inheritance review

- Steering's driver bindings cannot remove Guard after this change. Guard
  locally overrides those same inputs, so its atomic handoff still controls
  protected entry. W/S are added only by whichever owner answers the input.
- Entry Guard's direction/edge releases, inward Any-driver chord, touch
  restrictions, first-movement protection and menu handoffs are unchanged.
- Steering's up/down clear bindings and LST/RST plain-W/S window overrides
  are unchanged. Driver/window blocking and Always On isolation remain.
- Normal/Gyro Modifier 2 cover timers, repeat resets and release cleanup
  change only their four delayed-add haptic settings.
- No audit exceptions, simulator behavior, or new timer assumptions change.

## Reproduce

```bash
python3 findings/2026-10-10-quiet-gyro-and-guard-handoff/build_candidate.py
python3 findings/2026-10-10-quiet-gyro-and-guard-handoff/validate.py
python3 -m tools.audit_build
```

The builder extends frozen 90.47, edits title tokens, requires the fix
pipeline to be an exact no-op and verifies the runtime-ID round trip.
`--from-working` is only for initial installation from validated 90.47.

Native fresh-load checks: Base/Gyro gestures in both press/release orders at
short and long durations should be haptic-free. With LS held up/down, press
either driver through Entry Guard and confirm Steering remains active.

## Final validation and exports

- **315 scenario methods pass**, with every changed layer covered in both variants.
- **83 distinct regression methods pass.** The full run imported the old
  90.44 haptic expectation before its update, so it recorded 82 passes and
  that one stale assertion. `recheck_contracts.py` replays the corrected
  six-method module against validated 90.43 candidates; all six pass.
  `final-validation.json` aggregates these results transparently, and
  `full-run-before-contract-reload.json` preserves the original counts.
- All four build audits pass for both variants (`final-build-audit.txt`).
- `final-scope.json` confirms six changed bindings per variant, unchanged
  Guard and Steering clear groups, and unchanged beep-bearing commands.
- Both VDF exports verify keys, values and order; both JSON/VDF pairs are
  copied and byte-checked under `versions/neptune/90.48/`.
  `snapshot-manifest.json` records their SHA-256 values.
- `git diff --check` passes. Native Deck behavior has not been tested here.
