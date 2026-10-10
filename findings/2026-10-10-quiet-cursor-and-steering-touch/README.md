# 90.47 — Quiet cursor entry and Steering stick-touch gestures

Status: **validated and exported**, both variants, on 2026-10-10. Matching
JSON/VDF backups are saved under `versions/neptune/90.47/`.

Steering inherits Base's left/right stick-touch gestures after Entry Guard
disarms. Both stick-touch Double Tap windows supply plain W/S for left-stick
up/down, preventing Steering's clear from running during their 200 ms window.
The normal and Gyro Modifier 0/1 delayed Temp Cursor adds now have haptics Off.

| Owner | Change |
|---|---|
| Normal and Gyro Modifier 0/1 | Four delayed cursor-add activators per variant change Low to Off; the 200 ms delay, commands and selectors remain identical. |
| Steering | Remove its two touch Release overrides so Base's repeating LST/RST entries and helper lifecycles are inherited. |
| LST: Double Tap and RST: Double Tap | Add silent, uninterruptible Regular Press W/S on left-stick north/south, without layer commands, delays or repeats. |

There are ten binding changes across seven owners per variant. All 88 action
layers, group IDs and runtime IDs remain in place. Both complete descriptions
were reviewed and retained. Right-stick sensitivity/vertical scale remains
150/100%, 200/75%, 250/60%.

## Inheritance and feedback

Entry Guard is unchanged. It still protects the movement carried into
Steering, or the first push after centered entry, until the existing release
or deliberate handoff. Its touch overrides prevent helpers from covering
that protected movement. Once it disarms, held touches can start their
normal helpers through Base's repeating entry.

W/S owners, Steering Mod 0/1/2, covers, menus and ramps retain their own
touch recovery/replacements. The two shared touch windows continue replacing
driver adds with scroll output, blocking short menu presses and blocking
right-stick ramp entry. The author accepted those window restrictions.

Up/down now stays plain W/S during an active touch window. The window expires
normally; it does not clear Steering early. After expiry or a second-touch
exit, a full direction still held over armed Steering may run the original
clear on exposure or its next 50 ms retry. That clear retains its threshold,
beep and Low haptic. This is separate from Entry Guard protection.

The eight stick-touch cursor-completion adds per variant were already silent.
Fn bumps, touch second-press feedback, cursor gyro response, Steering driver
feedback and Mod 2 behavior remain unchanged. The earlier held-full-direction
Mod 2 release gap and broader release-order redesign are outside this release.

## Window audit coverage

The automatic backward chains omitted the newly reachable Steering context
under the shared touch windows. The audit now supports a declared stack
conditioned on an input actually being inherited from a specified lower
owner. The LST/RST windows each declare Base/Steering and Base/Gyro/Steering
when their touch is exposed from Base. Existing local touch overrides and
source-mode blocks disable the declaration, preserving frozen builders.

No R140/R141 exception permits the Steering clear through a window. Regression
tests remove each W/S replacement independently and require the audit to fail.
Other tests cover the inheritance condition, source-mode barriers, historical
overrides and the complete unchanged guard/Steering-clear contracts.

## Build and validation

The builder extends frozen 90.46. Initial installation required working JSON
to equal the previously validated 90.46 candidates, and preflight passed.
The transformation preserves the fixes-pipeline fixed point and round-trips
all title references to runtime IDs. The change reports list only the ten
intended binding edits per variant.

```bash
python3 findings/2026-10-10-quiet-cursor-and-steering-touch/build_candidate.py
python3 findings/2026-10-10-quiet-cursor-and-steering-touch/build_candidate.py --install
python3 findings/2026-10-10-quiet-cursor-and-steering-touch/validate.py
```

The [build audit](build-audit.txt) passes Budget, Window, Flow and Cleanup
for both variants. [Final validation](final-validation.json) records **311
passing scenario methods and 304 passing regression methods** across the
recorded runs. Every layer is reached: Base plus all 88 action layers in
each variant; no changed layer lacks coverage.

The initial scenario run found 17 assumptions in older tests that a thumb
resting after Steering entry could not own touch helpers. The common settled
fixture now explicitly lifts that thumb; cases that need it resting say so
and verify helper cleanup after release. The full scenario rerun passes.
The regression run passed 292 methods and encountered one cursor-module
import error. The runner's sibling-import path was corrected and all twelve
cursor contracts pass. Original logs remain in `validation.log`, with the
final scenario run in `final-scenarios.log` and cursor check in
`cursor-contracts.log`. No further layout edits were needed after installation.

[Rebuild verification](rebuild-manifest.json) confirms both full frozen builds
exactly match the live JSON and transformation reports. The VDF exporter
verified keys, values and order for both variants; its Node experimental
warning is informational. [Snapshot hashes](snapshot-manifest.json) record
all four exported/backed-up files. `final-scenario-coverage.txt` and
`final-unverified-assumptions.txt` preserve the final scenario reports.

On a fresh Steam load, check silent delayed cursor entry on each modifier,
LST/RST taps and double taps after disarming Entry Guard, W/S during each
window, the normal clear after its expiry, and protected first movement with
thumbs already resting. Automated checks verify configured behavior and
simulator assumptions; they do not establish native timing or felt feedback.
