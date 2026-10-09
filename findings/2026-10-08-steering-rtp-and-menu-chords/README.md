# 90.38: menu chords and RTP access in Steering

Built on 2026-10-08 from the author's
[plan](../../plans/2026-10-07-menu-chords-and-steering-fallback.md), for default
and alternative. Automated validation is complete; JSON/VDF exports are
saved under `versions/neptune/90.38/`. No Steam upload or Deck test.

## Changes

Both variants retain 88 layers. The change reports compare them with 90.37:
16 layers, 41 source/input changes each, plus title and description updates.

### Menu entry

`Steering`, `Steering | LS: Fallback Guard` and `Cursor Gyro` now use the
same repeating, uninterruptible self-chords as Base: Select mask 4096 and
Start mask 16384. Their targets remain the two `Stateful | Menu …: Entry Point`
layers. Base already had these chords in 90.37.

The opposite menu button's existing first-button chord also repeats, with
Interruptable Off, in these six layers:

- `Menu Left: Entry Point`, `Menu Right: Entry Point`
- `Menu Left: Fn Layer`, `Menu Right: Fn Layer`
- `Stateful | Menu Left: Entry Point`, `Stateful | Menu Right: Entry Point`

Their original chord selectors and targets are retained. Stateful Fn's
Enter/Backspace outputs are unchanged. The 200 ms delayed holds, 250 ms
resets and interruptible cleanup entries retain their settings.

### RTP access and timed completion

Steering and fallback no longer have their own right-pad groups. Base's
mouse response, click and explicitly silent repeating touch entry inherit.
Tap, double tap and circular scroll now work in Steering. This supersedes
the historical 90.7 entry block and the 90.35 copy into fallback.

The newly reachable `RTP: Double Tap` window blocks the four left-stick
directions: possible lower outputs differ, so R140 cannot choose one safe
replacement. This can suppress movement for the window's 150 ms. Other
window restrictions stay; ordinary Steering layers do not block RTP entry.
The two Steering Double Tap windows' pad release now removes the window
first and then the RTP Entry Point that can be underneath.

Six delayed targets and their twelve existing stick-touch completion
entries add their target before removing non-window RTP helpers:

| Owner | Target |
|---|---|
| `Steering | LS Down: Modifier 0` | `Steering | LS: Tap Cover` |
| `Steering | LS Up: Modifier 1` | `Steering | LS: Tap Cover` |
| `Steering | R1!L1: Modifier 2` | `L1: Tap Cover` |
| `Steering | L1!R1: Modifier 2` | `R1: Tap Cover` |
| `Stateful | Menu Left: Entry Point` | `Stateful | Menu Left: Fn Layer` |
| `Stateful | Menu Right: Entry Point` | `Stateful | Menu Right: Fn Layer` |

Alternative uses L2/R2. These entries then clear RTP Entry Point, Tap Cover,
Circular Scroll, Click Entry Point, Mouse Buttons and Middle Click. Arrays
store removals above the existing commands, because execution is bottom to
top. No ordinary face-button cover entry gains this cleanup. RTP Double Tap
is excluded from that list: its own isolation and self-first exits govern it.

The RTP layers can coexist with these owners whether the thumb arrives first
or second. A held thumb can re-enter RTP after the ordered cleanup through
Base's repeating touch; this is intentional, not a permanent pad block.
Gyro modifiers reached from fallback retain their existing cursor/cover
completion behavior. There is no new unconditional pad-touch-release apply:
RTP's own release still chooses its window/cleanup route, and the existing
stick releases complete the owner's valid delayed target.

### Fallback

Steering up/down are Soft Presses at `activation_threshold: 29031`, matching
the right-stick ramp threshold. They keep repeat rate 50 ms, Interruptable
Off, strong haptic 3 and the existing execution order: add fallback, remove
Steering. Fallback's W/S outputs themselves remain ordinary presses.

Fallback's left-stick edge now has an activator-local inverted, silent,
uninterruptible repeating chord, Any driver (mask 12 in default, 50331648
in alternative). Its sole command adds Steering. It does not remove fallback.

**Scope of the return:** this is a local fallback binding. A Gyro modifier
or cover that binds the LS edge takes precedence, so holding a driver while
moving inward under that modifier does not invoke the fallback edge in the
simulator. Returning through those overrides would require a separate,
context-specific design; no ordinary Gyro modifier was changed to add
Steering. Scenario S2 records this limit, rather than claiming that path works.
The question about extending the return through those layers was left open.

If the additive return stack is reached, fallback remains below Steering.
Scenario S3 checks driving, returning to fallback and clearing that stack.
Re-adding already-active Steering does not move it (A3); the inherited return
chord is silent. The physical inverted edge remains A54, unverified.

## Inheritance and rules

- Base/Steering/fallback/Cursor Gyro menu entries keep their intended targets;
  modifiers still own their menu outputs. Window exposure and missed-release
  recovery are exercised for each changed owner.
- Right-pad touch now has the same Base provider in ordinary and Steering
  contexts. The three obsolete R139 pad exceptions are retired from the live register
  and preserved in `retired-rtp-exceptions.json`. Frozen builders do not need
  these Flow-review allowances to reproduce their layouts.
- R139 accepts Steering's LS edge inheriting either Base's empty WASD slot or
  fallback's silent idempotent add in the additive return stack. This is the
  only new inheritance allowance.
- R111 has one author-requested exception for fallback's exact inverted chord.
  The Budget audit verifies its owner, source, activation type, target and
  all variant-specific settings. Changed selectors, repeat setting, target
  or a shared extra owner fail the regression test. The ban remains elsewhere.
- The Cleanup audit now recognizes a persistent mode restored by another
  proven persistent mode. It still requires no own Release or Always On
  lifetime, and a bare cycle cannot establish persistence. This preserves
  Steering's stateful classification after the additive return; it does not
  exempt arbitrary held overlays from cleanup.
- R140/R146/R148/R149 still protect windows. R123 completion is add first,
  then ordinary helper cleanup. Existing gyro settings are unchanged.

## Verification

- `python3 -m tools.audit_build --verbose`: all four audits pass for both
  variants; see `build-audit.txt`.
- Full active Python suite: **957 tests in 85 modules**, 1595.921 seconds.
  The initial run had three failures; all subsequently pass on focused reruns.
  The original output is preserved in `full-python-tests.txt`.
  Two failures were register maintenance: obsolete RTP inheritance allowances
  and missing R139 scenario attribution. Their fixes pass 16 and 28 tests
  respectively (`flow-register-retest.txt`, `rule-registry-retest.txt`).
  The five-second Window audit timing bound failed during the full run with
  another audit running, then passed alone in 4.667 seconds
  (`window-timing-retest.txt`). Its bound and implementation were not relaxed.
  No other failures remained; frozen historical builders and the exact
  generated-layout comparison passed in the full run.
- `node --test tests/test_convert_vdf.mjs`: **6 passed**, `exporter-tests.txt`.
- Change reports reviewed: 16 changed layers per variant, all covered by
  scenarios before snapshot creation (`scenario-report.txt`). Fix pipeline
  reaches a fixed point; layer/preset ordering and title/ID roundtrip pass
  (`preflight.json`). Exporter verifies VDF keys, values and stored order.
- Both JSON/VDF version snapshots match the working files byte for byte;
  hashes and paths are recorded in `neptune-installation.json`. The final
  eight layout/snapshot checks pass (`final-snapshot-tests.txt`).

New scenarios: M1/M2 menu entry and recovery; P1 RTP hold and scroll; P2 RTP
window isolation; D1/D2 delayed-target-before-cleanup ordering; S1 fallback
entry/pulse; S2 overridden edge; S3 additive return stack. Historical tests
for the old Steering RTP block now assert the author's replacement behavior.

Static checks verify the numeric threshold and configured feedback. The
simulator uses binary stick deflection and cannot establish the physical
29031 threshold (A53), inverted D-pad edge reliability (A54), haptic feel or
Steam's actual scheduling. These need a fresh Deck load.

## Build

`python3 findings/2026-10-08-steering-rtp-and-menu-chords/build_candidate.py --install`

Then audit, export both VDFs and snapshot 90.38 using `steam-layout-apply`.
The builder extends 90.37 in readable-title form and runs the existing fix
pipeline before converting to numeric runtime IDs.
