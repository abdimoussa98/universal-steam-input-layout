# 90.39 fallback window testing candidate

Built from 90.32 for default and alternative, with compatible fixes through
90.38, following the [approved plan](../../plans/2026-10-09-fallback-window-backport.md).
Each candidate has 90 action layers. This is a separate testing build; the
live Neptune layouts and their builder remain on 90.38. Deck testing is pending.

## Testing files

- [Default VDF](single-set-default-fallback-window_hold-gyro_90.39.vdf)
- [Alternative VDF](single-set-alternative-fallback-window_hold-gyro_90.39.vdf)
- Matching numeric JSONs and readable JSON copies are in this folder.
- Identical JSON/VDF backups are in [versions/neptune/90.39](../../versions/neptune/90.39/).

The title includes `fallback-window testing` before the final `90.39` version.
Candidate filenames also include `-fallback-window`, giving their snapshots
a separate identity from the live layout. The snapshot checks verify both
variants and their VDFs without advancing the live 90.38 comparison baseline.

## Preserved fallback behavior

Default drivers are L1/R1; alternative drivers are L2/R2.

Enter Steering with Start plus left-stick click/release. The original Entry
Guard protects a stick already out at entry. After moving it and letting go,
LS up/down without a driver adds Fallback Hold and then Fallback Window.

For one second, up/down sends W/S with a strong pulse every 250 ms. Releasing
the direction or edge before expiry removes the two helpers and keeps
Steering. During that second the drivers scroll and Start/Select send
Tab/Escape. Those buttons do not change layers or restart the timer.

At 1000 ms the window removes itself. Releasing the direction then exits
Steering, with its beep and strong pulse. A driver/menu button pressed after
expiry, or still held across expiry, also exits through the Hold's repeating
binding. Stick-touch releases and missed-release recovery retain the old
behavior. The eight-way settings, ordinary directional entry, and blocked
Steering stick edges are retained.

## Backported changes

| Origin | Applied change |
|---|---|
| 90.33 | Gyro Modifier 2 quick clears include the opposite Gyro Modifier 2, Base modifiers, and the retained Steering family. Steering windows are removed first. |
| 90.36 | Cleanup inputs store Regular Press, guard, Release. 121 inputs reorder in each candidate; 531 default and 557 alternative inputs have cleanup functions. |
| 90.37/90.38 | Base, Steering and Cursor Gyro use repeating uninterruptible Start/Select self-chords. Six existing opposite-menu-button chords repeat with their original conditions and targets. |
| 90.38 | Steering inherits Base's silent RTP entry, mouse response and clicks. RTP hold, double tap and circular scroll work outside timed windows. |
| 90.38 | Six delayed applies and twelve existing stick-touch completion entries add the intended target before clearing non-window RTP helpers. |
| 90.38, adapted | RTP Double Tap blocks the four ambiguous LS directions. The two Steering Double Tap windows and restored Fallback Window remove themselves before cleaning up an underlying RTP touch interaction. |

The Entry Guard's guarded menu outputs, Fallback Window's keys/scroll, and
Fallback Hold's menu exits keep their original roles. No fallback menu bind
was converted into a menu-layer entry.

The four-way stick, open-edge turn assist, persistent Fallback Guard, layer
swap, near-rim threshold, and inverted-edge return are later design changes
and are excluded. The 90.35 driver ramp cleanup is unnecessary here:
scenario E1 enters Steering from all three ramp phases, verifies the
transition clears them, and verifies the retained edges prevent re-entry.

## Inheritance review

Base provides the new menu self-chords to ordinary layers that omit those
inputs. Steering and Cursor Gyro retain their own Stateful targets. Modifier
parents retain navigation-key chords and cursor cancellation. Menu Entry/Fn
layers retain their delays, resets, guarded recovery, and owned releases.

Removing Steering's empty right-pad group exposes Base's silent RTP touch
entry through the Entry Guard, Fallback Hold, and ordinary Steering helpers
when no upper layer overrides that input. This follows the approved RTP
access decision. Timed windows remain the isolation boundary. In particular,
RTP Double Tap blocks LS direction changes for its 150 ms lifetime, then the
held direction can enter fallback through Steering's repeating add. Fallback
Window keeps its own touch-release exit and cannot inherit a second window
or another layer entry while its timer runs.

The six delayed-completion owners match 90.38: the two Steering directional
modifiers, the two Steering Modifier 2 layers, and the two Stateful menu
Entry Points. Completion preserves each owner/direction condition and adds
its target before ordinary RTP removals. No unconditional pad-release apply
was added. A thumb still held after cleanup can re-enter RTP normally.

The full-clear extensions are local to the two Gyro Modifier 2 layers. They
do not replace the fallback window's driver/scroll inputs or create the
later fallback-to-Gyro-modifier route. Candidate tests cover both modifier
orders, both release orders, stale Steering helpers, and menu-plus-stick
clears that preserve Gyro.

### A cleanup gap found by the new scenarios

Holding RTP first can leave `RTP: Tap Cover` under Fallback Window; a prior
double tap can similarly leave `RTP: Circular Scroll`. A right-pad release
inside a Steering window must clear those helpers after removing the window.
The cleanup analyzer's chain approximation marked these removals as
unnecessary. Scenario P4 initially reproduced the leftover Tap Cover; P5
checks both pad modes under all three Steering windows.

The candidate's local R132 entry retains Entry Point, Tap Cover and Circular
Scroll removals on those window exits. The fallback exit executes:
remove Window, remove Hold, then remove those RTP helpers. The directional
Double Tap exits remove their own window, then the RTP helpers. These
commands remain in one activator, preserving execution order.

Two other local R132 entries retain the approved Gyro full-clear scope even
for helpers absent from ordinary chains. [candidate-rules.json](candidate-rules.json)
copies the shared register and adds only these three entries. Historical
and live builders use the shared register, so their generated outputs are
unaffected. The fix pipeline reaches a fixed point with the candidate rules.

## Rebuild and validate

```bash
python3 findings/2026-10-09-fallback-window-backport/build_candidate.py
python3 findings/2026-10-09-fallback-window-backport/validate.py --export
```

The builder first reproduces both frozen 90.32 snapshots apart from metadata,
then edits readable titles. Validation explicitly supplies 90.32 as the
baseline and the candidate rules to all applicable audits. For example:

```bash
python3 -m tools.audit_build findings/2026-10-09-fallback-window-backport/single-set-default-fallback-window_hold-gyro_90.39.json --rules findings/2026-10-09-fallback-window-backport/candidate-rules.json --baseline versions/neptune/90.32/single-set-default_hold-gyro_90.32.json --verbose
```

The optional `audit_build` arguments forward the appropriate CLI flags to
Window, Flow and Cleanup; Budget retains its normal checks. Without these
arguments the live-layout audit works as before.

Validation records include per-variant build-audit logs, preflight/roundtrip
results, fix reports, change reports against 90.32 and 90.38, candidate
scenario output, changed-layer coverage, unverified assumptions, and export
hashes. The candidate scenario loader keeps its reached-layer set separate
from the live layout's scenario coverage.

### Completed validation

- All four audits pass for both candidates, against 90.32 with the local rules:
  [default](default-build-audit.txt), [alternative](alternative-build-audit.txt).
- [30 candidate scenarios pass](candidate-scenarios.txt), exercising both
  variants and both interpretations of A9 where declared. All 34 changed
  layers per variant are reached; [coverage](scenario-coverage.json).
- The full active Python suite ran **996 tests in 88 modules**, with no errors
  or skips, in 1709.494 seconds. Its two initial failures are resolved on
  focused reruns; the original [full log](full-python-tests.txt) and
  [summary](full-python-summary.json) retain the original result.
- One assumption-report assertion depended on scenario import order. It now
  checks that R111 and scenario 90.10 T5 are attributed within A8 without
  requiring that scenario to be first. The [retest](report-attribution-retest.txt)
  reproduces the candidate-first import order and passes.
- The existing five-second Window audit timing test measured 5.004806 seconds
  in the full suite. Its [isolated rerun](window-timing-retest.txt) passed in
  4.732 seconds. Neither the timing bound nor the audit implementation changed.
- All [six Node exporter tests pass](exporter-tests.txt). Both exports verified
  keys, values and stored order. Snapshot bytes/hashes match the candidate files.
- Frozen historical builders and the live 90.38 builder reproduce their
  respective layouts. Both 90.39 candidates also rebuild exactly, including
  stored order. The fix pipeline reaches a fixed point.

No automated failures remain. Physical behavior still needs the Deck checks
below. The verification summary and snapshot hashes are saved alongside the
logs; no live-layout installation or Steam upload was part of this candidate build.

## Deck test order

1. Compare untouched 90.32 and this candidate: up/down held for less than a
   second, just past a second, and released; then driver/menu taps inside
   the second and held across expiry.
2. On a fresh load, rest a thumb on LS and then RS and hold Start/Select.
   Check Fn at 200 ms, quick taps, thumb lifts during a hold, and both menu orders.
3. Hold or double-tap RTP before entering fallback, and touch it during the
   window. Release the pad inside the window and check that no pad helper
   or mouse/wheel output remains stuck. Check centre and outer pad clicks.
4. Exercise modifier taps/holds, both-driver clears, and a menu-plus-stick
   clear with Gyro on. Check recovery after a release missed in the Steam menu.

Simulator results do not establish Steam's stored-entry-order behavior,
held-input scheduling, release delivery, mouse response or haptic feel.
The menu fixes remain remedies to test, not proof of the reported Fn fault's
internal cause. See [unverified-assumptions.txt](unverified-assumptions.txt).
