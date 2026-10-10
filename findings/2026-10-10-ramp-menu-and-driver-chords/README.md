# 90.46 — Ramp menu exits and repeating Steering driver chords

Start or Select now clears all three ramp layers before opening the menu.
Steering and Entry Guard acquire W/S through silent repeating self-chords,
with their old ramp-removal subcommands moved out of driver entry.

| Owner | Change |
|---|---|
| Base and Steering | Both existing menu chords remove Gyro Off Ramp Up, Ramp 0 and Ramp 1 before their normal or Stateful menu Entry Point add. |
| Entry Guard | Both menu Start Presses clear the ramps before their existing guard-removal/menu handoff. |
| Steering and Entry Guard | Each driver uses one self-button chord: quiet 50 ms repeats, remove Guard, then add W or S. The opposite-button empty chord and three ramp removals leave these entries. |
| W and S | Their existing opposite-driver Mod 2 chords gain 50 ms repeats, permitting entry when both controls were already held as W/S landed. Keyboard W/S outputs stay nonrepeating. |
| Gyro Off Ramp Up | Both driver inputs quietly clear all three ramps. Default uses bumpers; alternative uses soft trigger pulls. |
| Ramp 0 and Ramp 1 | Continue inheriting menu entry from Base/Steering. Their existing driver exits and alternative full-pull requirement are unchanged. |

No layers, groups or runtime IDs are added. There are still 88 action layers.
Both descriptions were reviewed and retained. Right-stick settings stay at
150/100%, 200/75%, 250/60% (sensitivity/vertical scale).

## Why menu cleanup stays with menu entry

A ramp-local removal alone exposed Base's held right-stick edge before the
menu could arrive. In simulation that immediately added the ramp again and
could loop. Adding menu buttons to Base's empty blocking chord was insufficient
when a firing-button chord was also eligible. The final command list removes
all ramps and adds the correct menu Entry Point before inputs are rebound.
This preserves normal versus Stateful menu selection, and the existing
stick-guard and Fn behavior. The three ramp layers inherit these menu bindings.

Menu entry alone cannot cover direct driving while already in Steering.
The initial gyro-off stage can persist below the next ramp threshold, or a
driver can arrive during its 5 ms full-deflection delay. Its new driver exits
own that cleanup, preventing a hidden gyro-off layer under W/S. In alternative,
a soft pull now exits this initial stage; Ramp 0/1 still require a full pull.

## Inheritance and release scope

The menu edits are in existing active switch groups in Base, Steering and
Guard. The driver edits are in their existing bumper/trigger groups, the
W/S opposite-driver inputs and Gyro Off Ramp Up's existing groups. Each driver
entry's two commands execute Guard removal before driver add. Repeats change
layers only; they do not repeat W or S key outputs and carry no beep/haptic.

Both-carried entry previously stalled behind mutually blocking empty chords.
One driver now lands, then its repeating opposite-driver chord establishes
Mod 2. Normal sequential presses retain their existing first-driver branch.
With neither driver held, Guard still protects the first movement; a driver
handoff deliberately removes it, including a both-carried handoff.

Always On windows keep their local driver/menu replacements, so the lower
repeats do not mutate layers through those windows. Driver acquisition after
window expiry can now reach Mod 2 and its existing delayed Tap Cover; that
cover's Low haptic is separate from the silent driver/Guard entries.

Mod 2 release arrays are unchanged. Centered releases reacquire the held
driver, but a full up/down held through cleanup can still expose Steering's
independent clear. This release does not claim to solve that earlier handoff
gap or the deferred symmetric quick-clear redesign.

## Build and verification

The builder extends frozen 90.45. Installation first required byte-identical
working inputs and the previously validated 90.45 candidates. The fix pipeline
preserves the exact transformation; title/ID round trips and preflight pass.

```bash
python3 findings/2026-10-10-ramp-menu-and-driver-chords/build_candidate.py
python3 findings/2026-10-10-ramp-menu-and-driver-chords/build_candidate.py --install
python3 findings/2026-10-10-ramp-menu-and-driver-chords/validate.py
```

The [build audit](build-audit.txt) passes Budget, Window, Flow and Cleanup for
both variants. [Final validation](final-validation.json) records 302 passing
scenario methods and 228 distinct regression methods verified across runs.
The initial regression run found one registry-documentation mismatch: R110
did not yet list its new scenario coverage. The declaration was corrected,
and all 28 registry follow-up tests pass in `registry-fix.log`. The original
result remains in `validation.json` and `validation.log`. All 12 frozen
comparison/feedback contracts pass in `contracts.log`.
`scenario-coverage.txt` records no uncovered changed layers.
`rebuild-manifest.json` checks full frozen rebuilds against the live bytes.
`snapshot-manifest.json` records exported VDFs and version snapshots.

Simulation checks configured ordering and held-input cases, not native repeat
timing. On the Deck, check either menu while holding the right stick at each
ramp stage, driver entry at partial deflection, both drivers carried into
Steering, alternative soft/full pulls, and quiet W/S entry. Existing menu
stick guards can defer Fn or consume a menu gesture when a stick remains out.
