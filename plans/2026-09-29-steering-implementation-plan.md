# Steering implementation plan — sixteen-layer revision

Updated 2026-09-30. **Both candidates generated; native acceptance pending.**
The latest user decisions supersede the older rearm and Mod 2 gesture policies:
a held opposite takes over movement, Mod 2 scroll is immediate/hold-repeat,
normal directional state lives in Modifier 0/1, and normal repeat uses one cover.

[Exports, implementation and layer inventory](../findings/2026-09-30-steering-lean/README.md)
· [Acceptance](../findings/2026-09-30-steering-lean/ACCEPTANCE.md)
· [Previous 25-layer plan](2026-09-30-steering-implementation-plan.25-layer.md)
· [Original baseline plan](2026-09-29-steering-implementation-plan.baseline.md)

## Architecture and naming

| Default title | Alternative title | Purpose |
|---|---|---|
| Steering | Same | Membership, WASD fallback and timed exit |
| Steering &#124; LS: Entry Point | Same | Disposable untimed initial WASD |
| Steering &#124; R1: W Key | Steering &#124; R2: W Key | Right movement owner |
| Steering &#124; L1: S Key | Steering &#124; L2: S Key | Left movement owner |
| Steering &#124; LS Down: Modifier 0 | Same | Down map and normal Down gesture state |
| Steering &#124; LS Up: Modifier 1 | Same | Up map and normal Up gesture state |
| Steering &#124; R1!L1: Modifier 2 | Steering &#124; R2!L2: Modifier 2 | Right owner, opposite held; simple scrolling |
| Steering &#124; L1!R1: Modifier 2 | Steering &#124; L2!R2: Modifier 2 | Left owner, opposite held; simple scrolling |
| Steering &#124; LS: Tap Cover | Same | Shared normal consumed state |
| Steering &#124; LS Up: Double Tap | Same | Up pending single/double window |
| Steering &#124; LS Down: Double Tap | Same | Down pending single/double window |
| Steering &#124; LS: Double Tap Cover | Same | Both normal repeat directions |
| Steering &#124; Menu Left: Entry Point | Same | Protected left-menu entry |
| Steering &#124; Menu Right: Entry Point | Same | Protected right-menu entry |
| Steering &#124; Menu Left: Tap Cover | Same | Silent left-menu coverage |
| Steering &#124; Menu Right: Tap Cover | Same | Silent right-menu coverage |

**16 added layers, 71 total; no new Always On actions.** Existing Base action
set retained; no new action set. Saves nine against the previous lean export
and twenty against the original baseline. All added children use the Gyro-style
`Steering | control: function` schema.

## Transitions and cleanup

Owner Regular Press supplies W/S and Release Press clears all temporary steering
helpers. Upper helpers omit the dominant input. Fallback acquisition repeats at
50 ms, allowing a held opposite to take over after cleanup; no Rearm remains.
Both-held initial acquisition is guarded, and takeover consumes carried stick
history. W/S handoff and release races still need native measurement.

Fresh Up/Down selects Modifier 1/0. Cardinal release alone does not remove it:
recognized center opens the corresponding double window; sideways removes the
bank silently; direct reversal selects the other bank with Tap Cover above it.
Hold or modified action adds Tap Cover. The cover restores the current map and
reasserts itself last; true center clears both maps and cover. Preserve A/D.

Double windows retain ordinary 150 ms timing and the widened edge clock. A second
same direction enters the shared repeat cover. Both direction wheel binds use
5 ms initial delay and 50 ms repeat; old-direction release, center or sideways
tears down the cover and consumes the carried gesture. The delay must cancel
before any reversed tick; this is not proven by static command order.

Modifier 2 cancels normal gesture history and uses plain Up/Down wheel binds
with 50 ms hold repeat. No Mod 2 tap/hold/double/consumed layers remain. Releasing
the opposite control stops that context and restores normal direction consumed;
releasing the dominant permits the held opposite to become the new owner.

Preserve protected menu entry, deliberate Fn, release commitment and disposable
initial WASD. Fallback W warns at 1 s and exits at 2.5 seconds with beep/vibration;
W release or acquisition cancels timing. Preserve unrelated persistent Gyro,
except Mod 2's quick opposite tap, which clears to Base by design (author, 2026-09-30).

## Decisions and failure branches

- If cover reassertion does not retain priority without restarting selectors,
  fix the restore routing before promotion; no synthetic tap or selector churn.
- If shared-repeat reversal emits a delayed opposite tick, fix cancellation;
  a configured 5 ms delay alone is not a passing runtime result.
- If takeover overlaps W/S or leaves stale Mod 2, fix handoff; do not restore the
  now-rejected both-controls-released Rearm behavior.
- If normal/Mod 2 changed-held outputs synthesize replacement presses, implement
  suppression rather than claiming native handoff passed.
- If window/fallback clocks drift, warning persists, or existing foreign AO
  ordering is violated, block promotion and repair the route.

## Validation and delivery

Generate both readable/numeric JSON and VDF candidates. Check every input's
three-entry budget, unique/sequential IDs, resolved title references, both Mod 2
orders, exact 16-layer inventory, complete cleanup, inherited movement releases
and absence of new Always On inputs. Run binding traces for takeover, normal
center/reversal, Mod 2 simplification, double repeat and consumed restore.

Device checks are listed in the linked acceptance document; Python array traces
and the overview do not emulate Steam. Keep working exports and original
36-layer candidate unchanged; do not upload or promote before native acceptance.

## Reused single-side covers

Reuse L1/L2 Tap Cover for W Key and R1/R2 Tap Cover for S Key; no new Mod 2
cover definitions remain. Total returns to **16/71**. Opposite input uses the
existing 200 ms cover / 250 ms reset pattern; short uncovered opposite release
clears all layers. Dominant input is omitted from both Mod 2 and its opposite
single cover, preserving inherited W/S and normal owner release in every phase.

To keep shared Base/Gyro releases removal-only, install normal consumed state
beneath Mod 2 on entry. Shared cover release/recovery appends only removal of only the corresponding Steering Modifier 2 layer, exposing that state without re-adding anything. Preserve
original side cleanup, touch-release commands and guards. Owner cleanup clears
both reused covers. Test Base/Gyro regressions and pending lower selector work
at Mod 2 boundaries, in addition to existing timing/held-output gates.

## Interrupted delayed applies

Every new Fire Start Delay layer apply has a scoped repeating removal on the
same owning input: W/S Up/Down selectors use 5/50 ms, protected menu covers
300/350 ms, and Mod 2 covers 200/250 ms. Applying the target overrides the whole
input and stops its parent reset. The LS Tap Cover instead uses regular
50 ms repeating routing with no delayed apply: removing its active bank on a
repeat would strip the modifier because the cover stays on top. Routing never
removes the current bank or the cover itself. No additional layers are needed.
