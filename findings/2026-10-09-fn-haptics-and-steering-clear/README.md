# Fn feedback and full deflection Steering exit

90.42 extends the live 90.41 layout in both variants. The two-driver
release-order fix and its two new Tap Covers are deferred in
[todos.md](../../todos.md#steering-exit-and-fn-feedback-2026-10-09).
Both layouts retain their existing 88 layers and runtime IDs.

## Binding changes

Every activator that adds one of the four Fn layers now has Low haptic
feedback (`haptic_intensity: "1"`). This is 16 entries per variant: the
delayed menu hold, opposite-menu-button entry, and both stick-touch release
completions in each ordinary/Stateful Menu Entry Point. Fn add commands
retain their silent beep flags. Their conditions, delays, repeats and
bottom-to-top command order remain unchanged.

In the stateful `Steering` layer, left-stick up/down now clears Steering
instead of adding Fallback Guard. Both inputs retain their Soft Press,
`activation_threshold: "29031"`, uninterruptible repeat at 50 ms, and Low
haptic feedback. Only their command arrays change. The exit beeps once on
Steering's own removal, following R161.

The clear removes all 12 `Steering` / `Steering | …` layers plus the two
single-side Tap Covers used by Steering Modifier 2. It removes the two
Steering Always On windows first, then ordinary helpers/covers, and Steering
last. It preserves Gyro, the combined modifier cover, ramp layers, ordinary
trackpad/touch helpers, and shared Stateful menu layers. The lower layout
then answers the held direction as normal W/S movement.

No symmetric Mod2 clear, new cover, both-held entry arbitration, broad Gyro
clear, or change to fallback's inverted-edge binding is included.

## Inheritance and dormant fallback

Driver and directional modifier layers still answer the left stick while
they own it; their existing scroll/modifier behavior remains. Stateful menu
Entry/Fn layers have their own directions. RTP Double Tap and the other
Always On windows continue to block inherited layer mutations until their
ordered exits. The shared single-side Tap Covers are included because
Steering Modifier 2 directly applies them; unrelated families are preserved.

Removing the only two Fallback Guard adds makes that layer dormant. Its
saved bindings remain intact for the deferred work, and the new clear still
removes it from a stale stack. An exact R145 declaration makes the Flow
audit report it as retained but unreachable. Other unreachable layers still
fail; an explicit request to audit an unreachable target still fails.
Budget checks continue to inspect every saved group.

The Cleanup audit infers a live stateful mode from reachable adders. An
unreachable fallback add must not make Steering look like a held overlay.
Historical layouts with a reachable fallback still receive their usual
checks; the dormant declaration does not supply a fabricated entry route.

## Build and validation

```bash
python3 findings/2026-10-09-fn-haptics-and-steering-clear/build_candidate.py --install
python3 -m tools.audit_build --verbose
python3 -m tests.scenario --out findings/2026-10-09-fn-haptics-and-steering-clear/
node tools/convert_vdf.mjs neptune/single-set-default_hold-gyro_latest.json
node tools/convert_vdf.mjs neptune/single-set-alternative_hold-gyro_latest.json
```

Validation completed for both variants:

- [Preflight and roundtrip checks](preflight.json) passed. Compared with
  90.41, each layout changes exactly 18 inputs in five layers, plus its
  release title. Layer order, runtime IDs, descriptions and unrelated
  bindings are preserved. The fix pipeline makes no further changes.
  See the [default](default-changes.txt) and
  [alternative](alternative-changes.txt) change reports.
- Budget, Window, Flow and Cleanup audits passed for
  [default](default-build-audit.txt) and
  [alternative](alternative-build-audit.txt).
- [Scenario checks](scenario-tests.txt): all 262 scenarios and two focused
  static checks passed against the built candidates. These include 206 live
  scenarios, 26 frozen 90.41 fallback scenarios and 30 independent 90.39
  experiment scenarios. Historical and experiment checks do not supply live
  coverage. All five changed layers are reached in both variants;
  [coverage](scenario-coverage.json) was recorded against 90.41 before saving
  the new snapshot. The 206 live and 30 experiment scenarios also passed on
  an installed-layout rerun.
- [Focused binding/scenario checks](focused-tests.txt): 13 passed;
  [layout and rule regressions](layout-regressions.txt): 47 passed;
  [scenario registry checks](scenario-registry-tests.txt): 15 passed;
  [dormant-layer audit checks](dormant-audit-tests.txt): 116 passed, followed
  by 17 exception checks after the final preservation entries.
- [VDF exporter checks](exporter-tests.txt): six passed. Both sibling VDFs
  were regenerated with serializer roundtrip verification
  ([default](default-export.txt), [alternative](alternative-export.txt)).
  The four JSON/VDF files were copied byte-for-byte to
  [`versions/neptune/90.42/`](../../versions/neptune/90.42/);
  [snapshot hashes](snapshot-manifest.json) record the final files.

The [unverified-assumptions report](unverified-assumptions.txt) separates
simulator results from behavior still requiring a Steam/Deck observation.

On a fresh Deck load, verify a shallow up/down push stays in Steering and
a near-rim push exits, with ordinary W/S continuing. Test an already-held
direction at Steering entry and after a protected pad window expires. Check
Fn feedback through a hold, opposite-menu press, and each thumb lift in
ordinary and Stateful menus. The simulator does not establish physical
thresholds, haptic feel, or Steam's actual repeat scheduling.
