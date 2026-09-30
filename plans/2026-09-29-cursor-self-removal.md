# Plan: cursor self-removal and repeating modifier covers

Status: implemented in both Neptune JSON layouts on 2026-09-29, including regular
and Gyro variants. Deck validation remains pending. The implementation preserves
the 300/350 ms reset fix and reference gyro/right-stick tuning.

This replaces the normal covers' gyro-property restoration with cursor
self-removal. The [existing cursor plan](2026-09-29-temp-cursor-gyro.md) is retained
as history; the [implementation record](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md)
and [inheritance review](../findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md)
describe the result. Version and VDF export remain separate work. The sequence
below records the agreed implementation scope, not outstanding coding work.

Subsequent publication preparation updates both JSON titles to 90.3 and reviews
their descriptions, following the author's
[required publication workflow](../README.md#publishing-layout-changes). This
supersedes the original no-version-bump scope for the release. Both sibling VDFs
have been regenerated and verified; Deck checks remain pending.

## Accepted behavior

- Temp Cursor Gyro alone supplies the four Gated response/haptic overrides.
  Normal Tap Covers have no active gyro override; removing cursor exposes the
  lower gyro settings and activation rules.
- Cursor cancellation bindings repeatedly remove only their own cursor layer.
  They contain no key/mouse output, normal-cover addition, or Mod 2 transition.
  The newly exposed modifier input supplies those actions.
- Normal Tap Covers keep cursor off for the rest of the owner hold. Their
  primary-input replacement stops the parent's delayed apply and reset; their
  cleanup-only touch releases prevent thumb lifts from adding cursor again.
- Cursor layers inherit both LS and RS touch inputs from the modifier. Those
  releases apply cursor first, then clear the matching LST/RST family. Preserve
  that deliberate execution order and the inherited guarded recovery.
- Each ordinary modifier input has two owner-held chords: one for the existing
  output and one for adding the normal cover. **Both are uninterruptible.** Only
  the cover-add chord gains Hold to Repeat; output repetition stays unchanged.
- Opposite-modifier transitions and dual-stick cover additions repeat. The
  cursor layers have matching repeating self-removal exits for those gestures.
- The three-command maximum, cleanup ownership, timer protection, and Always On
  isolation remain requirements.

The design uses the author's [held-input rule](../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes):
removing a layer exposes the held input below it; repeats also support inputs
already held when a layer is added. Preserve this design premise. Deck checks
still establish current-client behavior, particularly key/mouse delivery and
release, rather than treating a static configuration check as runtime proof.

## 1. Split the ordinary modifier inputs

There are four owning layers per layout: Mod 0, Mod 1, and their two Gyro
variants. Owner selectors remain L1/R1 (`1`/`2`) in default and L2/R2 soft pull
(`7`/`8`) in alternative.

Change these twelve inputs in each owner: four face buttons, four D-pad
directions, LS/RS click, Start, and Select. Fresh title-form inspection confirms
**48 inputs per layout**, each currently holding two command entries.

| Entry after splitting | Binding | Settings |
|---|---|---|
| Owner-held chord: output | Original key/mouse command(s), with the cover addition removed | Same owner selector and original output settings; set `interruptable: "0"`; preserve existing repeat behavior |
| Owner-held chord: cover | Add only this owner's normal Tap Cover | Same owner selector; `interruptable: "0"`, `hold_repeats: "1"`; no start delay |
| Regular Press: recovery | Existing owner-family cleanup, including normal and cursor overlays | Preserve `hold_repeats: "1"` and default Interruptable; owner-held chords suppress it |

This is exactly three entries, even though both chords are stored in one
`chord` list. No key output is copied into the repeating cover entry. Keep key
strings, mouse buttons, haptics, release semantics, and cleanup scope intact.
Keep feedback on the existing output entry; use no haptic feedback for new
command-only repeats. Use the existing default repeating-add cadence unless
validation demonstrates a need for an explicit interval.

Splitting the original subcommand array removes its guaranteed add-before-key
execution order. Do not claim JSON chord-list order recreates that guarantee.
Check both uninterruptible chords execute together and that applying the cover
does not lose, duplicate, or strand the output.

Do not centralize these additions on the owner button: its release, 300 ms
cursor apply, and independent 350 ms reset already consume three entries.

## 2. Make cursor cancellation local

Keep the two existing owner-specific cursor layers per layout, shared between
regular and Gyro owners. Give each cursor layer explicit cancellation inputs:

- Four face buttons and four D-pad directions.
- Start and Select.
- LS click and RS click.
- The opposite modifier: bumper in default, trigger edge in alternative.

Each of these thirteen inputs contains one Regular Press that removes **only
that cursor layer**, with Hold to Repeat enabled, Interruptable off, and no
key/mouse action or layer addition. No owner chord is needed for this local
exit: an invalid residual cursor should also remove itself. Reuse partial
groups where possible and preserve inherited source settings.

The parent then supplies its output and repeating cover addition. For the
opposite modifier, the actual exposed regular/Gyro parent supplies its existing
transition, so cursor layers do not duplicate or choose between Mod 2 branches.

Retain the cursor's existing primary-release exit and the owner's broader
recovery ownership. "Self-removal" here describes cancellation inputs; it does
not replace the primary release's family cleanup with a short-tap transition.

## 3. Keep dual-stick detection separate

Retain the existing about-25% geometry: LS radius 4915 and RS radius 7209 in
single-modifier parents. Keep each local edge qualified by its owner and the
opposing stick's deflection (All semantics).

| Input | Entry 1 | Entry 2 | Entry 3 |
|---|---|---|---|
| Modifier LS/RS edge | Interruptible empty owner guard | Uninterruptible owner + opposite-stick chord, repeating normal-cover addition | Interruptible repeating family recovery |
| Cursor LS/RS edge | Interruptible empty owner guard | Same uninterruptible condition, repeating removal of only this cursor | Interruptible repeating removal of only this cursor when the owner guard is absent |

Cursor stick groups inherit the parent's geometry and movement settings. One
stick alone while the owner is held must not cancel cursor. After cursor exits,
the exposed modifier edge adds the normal cover. Lost-owner recovery then
exposes the parent's existing family cleanup.

The new requirement that **both output/cover chords are uninterruptible** applies
to section 1's split inputs. Keep the stick-edge empty owner guard interruptible
so the stronger dual-stick chord can take precedence. Each edge stays at three
entries; Mod 2 and unrelated recovery edges retain their existing design.

## 4. Preserve the touch and primary lifecycles

| Layer | LS/RS touch input | Primary owner input |
|---|---|---|
| Mod 0/1 parent | Existing guarded recovery and cursor-add-before-helper-removal release | Release exit + 300 ms apply + 350 ms independent reset |
| Temp Cursor Gyro | Omit `touch` entirely to inherit the parent; do not substitute an empty binding | Existing release-only replacement |
| Normal Tap Cover | Retain explicit guarded recovery and cleanup-only touch release; no cursor additions | Existing release-only replacement |

Remove only the normal covers' active gyro source associations. Do not disable
gyro or replace those associations with a gyro group that resets defaults.
An unused, unshared restoration group can be removed once its references are
checked. Cursor response remains 750/0/1/5 for precision/haptic/bump/threshold;
normal inherited values are 300/0/5/0 with the current reference tuning. Natural
sensitivity stays inherited at 300. Gyro/LST/RST remain activation-only sources;
intentional menu and Gyro Off suppression remains intact.

The 350 ms reset continues to target only cursor. Never add normal-cover removal
to it. Both overlays still replace the primary input to retire the apply/reset
pair; a cursor exit must lead to a normal cover before the exposed delay can
re-establish cursor eligibility.

## 5. Resolve inherited repeats before finalizing

The new cover repeats can remain inherited after a normal Tap Cover applies.
Trace held inputs through both cover types, Mod 2, scroll/menu/Fn/Transition
layers, and all seven Double Tap windows. Record the exposed input, whether it
can mutate layers, and which upper binding stops it. Inactive groups and empty
`inputs` objects are not explicit blocks.

**Concrete timer stack to protect:** Mod 0/1 → optional Cursor → inherited RTP
Entry → quick RTP touch release → RTP Double Tap. RTP Double Tap can sit above
the still-active modifier/cursor. The existing windows' edge/touch protection
does not establish that face, D-pad, and click inputs are protected. A new
repeating cursor self-removal or cover addition must not run beneath Always On.

Implementation must trace that route and add narrow, explicit no-op replacements
for its exposed face/D-pad/stick-click inputs while RTP Double Tap is active.
This deliberately blocks those outputs for the protected window. Audit the
other six windows individually and add the same protection wherever a modifier
or cursor can coexist beneath them; document why each is blocked or already
isolated. Preserve existing safe outputs, explicit blocks, and self-first exits.
Do not silently introduce a new early exit or add Always On to cursor layers.

Also inspect mode-shift targets reachable in those contexts, not only active
source groups. The trackpad mode-shift concern remains an unverified follow-up;
this plan does not claim it is a confirmed runtime bypass or import reference
mode-shift bindings.

**Fixed alternative-layout exception:** `R2: Modifier 1` and
`Gyro | R2: Modifier 1` had opposing-LT chords without `hold_repeats` (groups
258 and 12940). This implementation completes
[held-input follow-up F1](2026-09-29-held-input-rule-followups.md#11-fix-f1-in-the-alternative-layout)
by adding only `hold_repeats: "1"` to those entries. Their targets, conditions,
interruption setting, and subcommand execution order are preserved.
All four opposite-modifier routes per layout now repeat.

## 6. Implementation sequence and static validation

1. Read the prep/binding-order/apply skills and preserve all current work. Run
   preflight and actual `to-titles --output` on both JSONs before editing.
2. Record the 48 split inputs per layout, two cursor layers, normal-cover source
   groups, all affected inherited stacks, and the two alternative F1 entries.
3. Split the ordinary inputs, enable the existing parent dual-edge cover repeats,
   and complete F1 if needed. Preserve the owner primary's three entries.
4. Add cursor cancellation inputs and guarded dual-edge exits; remove cursor
   `touch` overrides, retaining normal-cover touch replacements and both
   overlays' primary exits. Remove normal-cover gyro overrides.
5. Apply the required timed-window protection from section 5, recording any
   temporarily displaced key/click actions. Verify actual source and input
   replacement; do not infer safety solely from lower owner-held guards.
6. Update cursor/gyro tests: split chord settings and exact outputs, repeats,
   three-entry budgets, self-removal-only targets, touch inheritance versus
   normal-cover blocking, no normal-cover gyro source, activation-only layers,
   reference tuning, 300/350 ms retry scope, and protected timer transitions.
7. Update current implementation documentation, vocabulary/examples, both skill
   mirrors, TODO status, and manual tests to describe self-removal. Historical
   property-restoration records must be labeled as superseded, not silently
   presented as current. Retain the separate mode-shift verification task.
8. Run the full tests and command-budget scans, preflight order/unique-title
   checks, actual `to-ids`, and exact title round-trips. Review the semantic diff
   against the working baseline. No version bump, VDF changes, or commit is
   included in this planning request.

## 7. Deck acceptance

Run both layouts, both owners, and regular/Gyro variants after a fresh load:

- Owner first, then each qualifying button; button first, then owner; keep the
  button held across cursor application and removal. Output fires with its
  original repeat behavior and releases cleanly; the normal cover applies.
- Override before, at, and after 300 ms. Before-delay override prevents cursor
  entry; after-entry override removes cursor and restores inherited gyro. Keep
  holding past multiple 350 ms intervals: no re-entry or repeated reset leak.
- Lift each thumb before entry, while cursor is active, and after cancellation.
  Cursor inherits the first two cases' completion/cleanup behavior; normal
  covers perform cleanup only and never reactivate cursor in that hold.
- Test both dual-stick orders and sticks already deflected before entry. One
  stick alone preserves a valid hold; the two-stick gesture exits and covers;
  releasing the owner exposes the existing family recovery.
- Test both opposite-modifier orders, regular/Gyro destinations, and alternative
  partial/full trigger pulls. Parent transition ordering and repeat are preserved.
- Hold each affected input across protected windows, especially a quick RTP tap
  above a modifier/cursor both with an input already held and with a new press.
  No unrelated layer mutation runs until the window expires or exits self-first.
- Check same-selector uninterruptible chords together: no lost/duplicate output,
  repeated key pulses introduced by the new cover repeat, or stuck mouse button.
  Link any output-handoff discrepancy to the held-input audit's F3 checks rather
  than adding keyboard commands to the repeating cursor removal.

Static validation can establish configuration and budgets. Record Deck results
separately, including the client version, before calling runtime behavior proven.
