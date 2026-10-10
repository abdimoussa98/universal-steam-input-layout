# Plan to fix Steering fallback and dual bumper clearing

Status, updated 2026-10-09: **the broader recovery proposal is deferred**.
The author requested a narrower implementation after reviewing this plan:

- In the `Steering` stateful base layer, near-rim left-stick up or down
  directly clears the Steering family. Keep `Soft_Press` and threshold
  `29031`; these inputs no longer add Fallback Guard.
- Add a haptic bump to every Fn-layer apply, including ordinary and Stateful
  menu entry paths.
- Leave the asymmetric two-driver clear for a later change. Do not add the
  two dedicated Steering Tap Covers or change Modifier 2 release behavior
  in this implementation.

The narrower implementation is complete in **90.42**, both variants, with
JSON/VDF exports and version backups saved. The
[release record](../findings/2026-10-09-fn-haptics-and-steering-clear/README.md)
documents validation; its builder extends the
[90.41 builder](../findings/2026-10-09-low-haptics-and-silent-fn/build_candidate.py).
The [TODO](../todos.md#steering-exit-and-fn-feedback-2026-10-09) tracks the
requested changes and the deferred work separately. The separate 90.39
fallback-window experiment keeps its existing behavior.

The approved follow-up is complete in **90.43**: the
[Entry Guard plan](2026-10-09-steering-entry-guard.md) restores held/first-push
protection, corrects Modifier 0/1 driver recovery and applies the beep audit
changes. It retains the 90.42 full-deflection clear and Fn bumps, with no new
layers. The broader two-driver release-order proposal below remains deferred.

The direct up/down clear supersedes the fallback-entry feedback proposal
in section 2. Sections 3–5 remain deferred; their layer additions,
both-held entry arbitration, and broader Gyro Modifier 2 clear are not part
of the current implementation. Review their assumptions against the next
live layout before resuming them. The findings and original proposal below
are retained as the 90.41 investigation record, not a claim that those fixes
have shipped.

## Deferred proposal and 90.41 findings

The original intended result was stable fallback entry without sustained
haptics, a quick two-driver clear that works in either release order, and
complete cleanup after a release was missed. In default, the drivers are
L1/R1; alternative maps the same roles to L2/R2.

The deferred proposal interprets “click both bumpers” as a quick
press-and-release that clears; holding both or using a Modifier 2 command consumes that tap
and retains the driving mode. Immediate clearing when the second button goes
down would remove that existing Modifier 2 interaction and is outside this
proposal.

## Findings and expected behavior

| Problem | Evidence from 90.41 | Required result |
|---|---|---|
| Holding up/down produces repeated feedback on the Deck | Steering's up/down Soft Presses repeat every configured 50 ms with Low haptics. The simulator produces one pulse and stable fallback, so it does not reproduce the reported device fault. | Transition retries are silent. A fresh near-rim push has separate nonrepeating feedback; holding the stick must not buzz or repeatedly swap layers. |
| Clearing depends on release order | R1 down, L1 down, R1 up, L1 up leaves Steering. Releasing L1 first clears. The S-first route has the same asymmetry in both variants. W/S output itself does stop after release in these simulations. | Either release order clears an unused quick chord. |
| Both-held entry can stall | When both drivers are seeded as held before Steering evaluates them, its mutual empty chords suppress both driver entries indefinitely in both variants. This models an exposure case, not Steam's same-frame scheduling. | A deterministic route reaches Modifier 2 when both are already held; check near-simultaneous presses on the Deck. |
| Helpers survive a clear | In fallback, enter RTP Tap Cover, enter Gyro Modifier 2, miss stick/pad releases, then release both drivers. The simulated final stack is Base plus RTP Entry Point and Tap Cover, with no controls held. Circular Scroll can survive the same way. | A full clear removes these helpers even when their own release was missed. |
| Steering may return after clearing | Fallback has an inverted repeating edge chord that adds Steering. The author's recorded inverted-chord observations say removing the owning layer can leave an active bind running. This particular resurrection has not been reproduced on the Deck or in the simulator. | Remove that continuing add source and check stability independently from haptic silence. |

References: [current fallback entry and return](../findings/2026-10-08-steering-rtp-and-menu-chords/README.md),
[repeat and delay limitations](../resources/Delay%20Timers%20and%20Repeat%20Rates.md),
[inverted chord observations](../resources/Steam%20Behaviour%20Assumptions.md#inverted-chorded-press-in-action-layers).

## 1. Establish the baseline and regressions

Create `findings/2026-10-09-steering-fallback-recovery/` with a builder extending
90.41. Compare the untouched builder result with both working layouts before
editing, preserving any intervening changes. Keep older builders frozen and
work on `main` without committing or publishing as part of implementation.

Run layout preflight and convert copies to readable title form using
[steam-layout-prep](../skills/steam-layout-prep/SKILL.md). Add regression
scenarios for the release-order and missed-release failures before changing
bindings. Record the haptic fault as a device observation; a passing binary
stick simulation is not a reproduction of it.

## 2. Separate feedback from transition retries

In Steering's `joystick/dpad_north` and `dpad_south`:

- Retain the repeating layer transition, threshold `29031`, and current
  add-Fallback-then-remove-Steering execution order. Set its haptics explicitly
  to Off.
- Add a nonrepeating feedback-only Soft Press at the same threshold, using
  Low intensity and an empty binding. Keep layer changes in the silent entry.
- Keep the total at two command entries per direction. No new delay or repeat
  interval determines whether fallback succeeds.

Apply the same separation to Fallback Guard's two driver return inputs.
Their existing LS-deflection chord must suppress both the ordinary return
and its feedback. Keep the silent repeating `Full_Press` and add a separate
nonrepeating, interruptible `Full_Press` pulse. Together with the chord this
uses three entries. With the stick out, the driver still enters its Gyro
modifier without a false return pulse.

Feedback must not affect state correctness. A newly exposed/already-held
input, or Steam executing the swap before the feedback entry, may omit the
one-shot pulse. Check that on the Deck; do not restore haptics to the retry
to compensate. The release record must distinguish a verified fresh-push
pulse from best-effort feedback on held-input entry.

## 3. Remove the inverted additive return

Remove Fallback Guard's local inverted `joystick/edge` chord that repeatedly
adds Steering. Keep the existing driver-at-centre and stick-touch recovery
routes. Inspect the lower edge binding exposed by the removal and verify
that its inherited output/settings are appropriate.

This deliberately retires the experimental inward-edge return when that
edge is exposed. Gyro modifiers already cover that edge in common
held-driver stacks. Do not introduce an inverted replacement or change
ordinary Gyro modifiers to enter Steering. Keep the four-way Steering and
eight-way fallback swap, and test return to driving through the remaining
routes.

Document the retired route in the current release and stateful transition
reference. Retain any exact R111 exception needed by frozen historical
builders; assert that the new build contains no such active add. An old
exception must not authorize a new inverted binding.

## 4. Make Steering quick clears symmetric without breaking holds

Both Steering Modifier 2 layers currently bind the full clear only on the
second driver. Add the same quick-clear release to the original driver,
preserving its nonrepeating W or S `Full_Press`. Both releases must remove
the same complete layer set.

That alone would make a held/used Modifier 2 clear unexpectedly, because the
ordinary single-driver Tap Covers inherit the original driver's input.
Give Steering two dedicated covers:

| Modifier 2 owner | Existing target | New target in default |
|---|---|---|
| `Steering | R1!L1: Modifier 2` | `L1: Tap Cover` | `Steering | L1: Tap Cover` |
| `Steering | L1!R1: Modifier 2` | `R1: Tap Cover` | `Steering | R1: Tap Cover` |

Map names to L2/R2 for alternative. Use
[steam-layer-duplicate](../skills/steam-layer-duplicate/SKILL.md) and
`tools.duplicate_layer` to append the copies with fresh groups and stable
existing runtime IDs. With exactly these additions, each variant has 90
layers. Retarget self-references and any copied mode-shift group IDs.

Rebuild each copy's lifecycle rather than accepting its inherited cleanup:

- Explicitly bind the original driver's W/S output and its old scoped family
  release. This masks the new quick-clear release while the cover is active.
- The second driver's release ends that Modifier 2 branch and its cover,
  preserving the still-held original driver. Both release orders retain
  Steering after an intentional hold or used command.
- On both stick touches, guard recovery with **either driver held**, matching
  the Modifier 2 parent. The interruptible repeating cleanup removes the
  current driver, matching Modifier 2, and new cover. Touch releases retain
  only their side-local LST/RST cleanup and cannot re-add a cover.
- Review inherited edge/button recovery and required cleanup rules R169 to
  R171. Preserve valid held owners and remove dependents after missed releases.

Retarget every Steering Modifier 2 cover add, delayed apply, repeating
reset, command-use route, and touch-release completion. Update driver exits,
current-branch recovery, relevant window exits, and all full clears to name
the new covers. Global clear lists add the new covers while retaining the
ordinary ones; do not use a global title replacement. Let the cleanup audit
review now-unused Steering removals in the ordinary covers. Ordinary
modifier covers retain their existing behavior.
Preserve add-before-RTP-cleanup completion where required by R123.

Resolve the reproduced both-held entry stall in Steering itself: replace
only the right/W driver's opposite-held empty chord with a silent repeating
entry that adds the W owner, then `Steering | R1!L1: Modifier 2`, in one
ordered command array. Preserve driver-entry ramp cleanup before those adds.
Keep the other driver's empty guard. This chooses W-first only when the
inputs are ambiguous at Steering entry/exposure; normal sequential entry
keeps its existing first-driver choice. Do not route the two chords to
competing branches or add removals that continually rebuild the same stack.
Test both-held exposure separately from sequential presses, and check
near-simultaneous scheduling on the Deck.

## 5. Give fallback a complete clear

Build the full-clear target list from all current non-Base layers, including
the new Steering covers. Use it for both releases in both Steering Modifier
2 layers and both Gyro Modifier 2 layers. This extends the fallback/Gyro
clear beyond its current 15 targets and prevents missed-release RTP helpers
from surviving. Retain one intentional clear notification rather than
adding feedback to every removal.

Preserve the distinct contracts: ordinary Base Modifier 2 still toggles
Gyro; menu-plus-stick clear still preserves Gyro; held/used Modifier 2 uses
scoped release cleanup. Gamepad and Menu Keys retain their existing exits.
Full clearing may expose Base entries while a control remains physically
held. A newly added, valid Base helper is not an orphan: tests must inspect
remove/add history and the final state after all controls are up.

Run the cleanup/window fix pipeline and inspect its changes. Protect the
deliberately broad full-clear scope with narrowly scoped rule-register
entries if its chain analysis would trim stale-state removals. Scope new
entries to the new layout, for example by the presence of the dedicated
Steering covers, so historical builders keep their original outputs.

Always On windows remain isolation boundaries. Verify which input answers
before adding any clear beneath a window; on a reachable early exit, remove
the active window before unrelated layer operations. Keep bottom-to-top
array execution explicit and require the fix pipeline to reach a fixed point.

## 6. Validate and export

Add release scenarios and focused binding checks for both variants:

| Area | Required coverage |
|---|---|
| Quick clear | Both driver orders and both release orders; original driver held well before second press; near-simultaneous presses; one driver remains held briefly after clearing. |
| Used and held Modifier 2 | Hold past the configured 200 ms cover delay; use face, D-pad, menu and stick-click commands; cover entry via thumb lift; release either driver first; release and repress one side. W/S remains continuously down through Mod2 and cover entry, without repeated key-down events; confirm this handover on the Deck too. Preserve scoped exits. |
| Fallback | Up and down, shallow versus near-rim movement on hardware, direction already held at entry, return via driver/touch, repeated entry cycles, and separate assertions for silent retries and stable layers. |
| Missed releases | Reach RTP Entry Point/Tap Cover and Circular Scroll naturally, lose stick/pad releases, then clear. Lose first, second, or both driver releases and exercise touch/edge recovery. Require no stale helpers once all controls are up. |
| Stale state | Inject old Steering helpers and either Steering/fallback stacking order; prove full clear removes them. Label injected stacks separately from naturally reached ones. |
| Inheritance | RTP held before/during entry, menu/Fn layers, temporary cursor, ordinary and new Tap Covers, directional windows, all ramp stages, alternative soft/full trigger pulls. Preserve protected windows and valid ordinary modifier behavior. |

Run relevant cases under both modeled held-input re-exposure outcomes (A9)
and both independent-entry orders where relevant (A32). State correctness
must not depend on their tie order. Keep physical threshold, inversion,
repeat, release and timer uncertainties in the assumption report.

Before export, require Budget, Window, Flow and Cleanup audits to pass,
the full active scenario suite plus focused modifier/Steering/cleanup
regressions, coverage of every changed layer, reproducible builder output,
preflight, numeric/title roundtrip, and exporter tests. Read the change
report against 90.41 before saving a new snapshot. Update the current
builder pointer in `docs/building.md` and the relevant stateful behavior
documentation when implementation is complete.

Follow [steam-layout-apply](../skills/steam-layout-apply/SKILL.md): review the
concise descriptions, bump both titles once, export both sibling VDFs, and
save byte-identical JSON/VDF snapshots in `versions/neptune/<version>/`.
Keep source hashes, audit/test logs, changed-layer coverage and unverified
assumptions in the release findings folder.

On a fresh Deck load, hold each near-rim direction for several seconds,
repeat both clear orders, test intentional Mod 2 holds, and reproduce the
Steam-menu missed-release case. Check that Steering does not return after
the clear and that no output remains held after all controls are released.
Fresh loading matters because removing an old layer may not stop an already
active inverted chord. Compare the same sequences with 90.41 if the fault
persists. Automated success establishes configured behavior; the reported
buzz and any runtime resurrection are resolved only after these device checks.
