# Temp Cursor Gyro through modifier holds — original design

Implemented in both Neptune JSON layouts on 2026-09-29, from baseline `c820d22`.
Version remains 90.2. The actual converters were used before editing and after
validation. See the [implementation record](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md)
and [pending Deck checks](../archived/manual-testing.md).
Stateful Cursor Gyro is outside this change.

**Historical design, superseded by the implemented
[cursor self-removal follow-up](2026-09-29-cursor-self-removal.md).** The record
below preserves the original property-restoration approach and its tuning/reset
follow-ups. Current normal Tap Covers inherit gyro; cursor cancellation removes
cursor itself, exposing separate uninterruptible output and repeating cover-add
chords. Cursor touch inputs now inherit the parent, while normal covers retain
cleanup-only touch replacements. Use the implementation record for current
behavior; the restoration and cursor-touch instructions below no longer apply.

## Confirmed behavior

- Apply to Mod 0/1 and their Gyro variants in both layouts: L1/R1 in default,
  L2/R2 in alternative. There are four owning modifier layers per layout.
- The owner's delayed hold applies a new Temp Cursor Gyro overlay instead of
  the existing normal Tap Cover. Both stick-touch releases also apply that
  cursor overlay before clearing their respective LST/RST layers: they complete
  the pending apply early so those removals cannot postpone it.
- Face buttons, D-pad directions, stick clicks, Start/Select, and the opposite
  modifier still apply the normal Tap Cover. That cover replaces both touch
  inputs with guarded recovery and stick-release cleanup, with no cursor add.
- Temp Cursor Gyro uses the response and haptic properties from the July
  reference's **Gated Gyro** layer. Natural sensitivity stays inherited at its
  current value of `300`; neither cursor overlays nor normal covers override it.
  Normal Tap Covers explicitly restore every changed property. Temp Cursor Gyro
  does not toggle persistent Gyro.
- Keep the existing `300 ms` delay. The
  both-stick condition should qualify at roughly **25% deflection on each stick**.
- Once a normal Tap Cover overrides the cursor properties, they stay overridden
  until the modifier is released and held again. Releasing the qualifying face
  button, lifting a thumb, or recentering the sticks must not restore the cursor
  properties. An override before 300 ms must prevent cursor entry altogether
  for that hold, not merely restore normal properties after a late cursor apply.
- Add a normal-cover path to each stick edge, qualified by the opposing stick's
  deflection and the held modifier. Use an interruptible owner guard, an
  uninterruptible override chord, and repeating recovery: three entries total.
- The author accepts moving these single-modifier edge regions to about 25%,
  including earlier recovery when the modifier is no longer held. Other layers'
  edge thresholds and Base's WASD/ramp-up bindings are unchanged. The later
  reference-tuning follow-up changes Base gyro and ramp response settings below.
- Cleanup must include the new overlays wherever the owning interaction ends.

**Activation rule retained:** preserve each owner's existing gyro activation
rules, consistent with the earlier decision to change response rather than force
gyro on. The implementation does not copy Gated Gyro's activation mask.
Regular modifiers inherit Base's
six-input All gate; Gyro variants use the four stick-touch/deflection inputs with
Any. Changing response/haptic properties alone does not force gyro on. See the
property table below for the mask distinction.

## Baseline behavior that matters

Each single modifier had sixteen paths that added its normal Tap Cover:
the 300 ms primary hold, four face buttons, four D-pad directions, two stick
clicks, Start and Select, the opposite modifier, and two stick-touch releases.
Three paths per owner change target: the delayed primary hold and both touch
releases. Across four owners, that is **twelve retargeted entries per layout**
(four delayed, eight release). The other thirteen paths per owner keep applying
the normal cover, including Start/Select and the opposite modifier.

The touch-release arrays deliberately execute their add before their LST/RST
removals. The author confirmed this completes the delayed transition before
the removal API can reset its timer. It is a lifecycle transition, distinct from
guarded repeating recovery or a periodic delayed-apply reset. See
[completing delayed applies on stick-touch release](../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release).

The normal cover owns the primary button's release and suppresses the parent's
release into Double Tap. Before this change it had no gyro override. Simply adding a
normal cover above a cursor-property layer would therefore inherit its settings.
Restoration needs explicit normal values for every property changed beneath it.

Both layouts currently define normal gyro sensitivity as `300` in Base. Other
active gyro groups inherit it. The initial implementation left the four primary
delayed applies at two entries and deferred their reset/retry logic. The author's
follow-up identified that omission: each now has a third entry, a 350 ms repeating
removal of only its pending Temp Cursor Gyro overlay, with Interruptable Off.
See the [reset follow-up](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#delayed-apply-reset-follow-up).

## Cursor gyro property profile

Source: [July reference](../findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json),
`Gated Gyro` / `Preset_1000058`, active gyro group **370**. Its mode is
`gyro_to_mouse`, with empty inputs and these explicit settings:

```json
{
  "layer": "1",
  "gyro_precision_speed": "750",
  "haptic_intensity": "3",
  "flickstick_haptic_bump_per_angle": "1",
  "gyro_ratchet_button_mask": "211109453778944",
  "mouse_move_threshold": "10"
}
```

Use this active gyro group's response/haptic overrides for both cursor overlays.
Do not clone the reference layer's trigger/switch bindings or its entry/exit logic.
Gated Gyro does not explicitly set natural sensitivity. Leave it inherited in
both cursor overlays and normal covers, preserving the current value of `300`.

| Property | Temp Cursor Gyro | Normal Tap Cover restoration |
|---|---|---|
| `gyro_natural_sensitivity` | Inherited unchanged (`300` from current Base) | Inherited unchanged; no override needed |
| `gyro_precision_speed` | `750` | `300` (current Base) |
| `haptic_intensity` | `3` | `0` (verified native gyro default) |
| `flickstick_haptic_bump_per_angle` | `1` | `5` (verified native gyro default) |
| `mouse_move_threshold` | `10` | `0` (verified native gyro default) |
| `gyro_ratchet_button_mask` | Inherit current owner gate; reference mask is not copied | Inherit current owner gate |
| `gyro_ratchet_button_requireany_or_all` | Inherit current owner's Any/All rule | Inherit current owner's Any/All rule |

Both current layouts have identical active Base gyro response settings in group
576. Their normal haptic intensity, haptic bump, and movement threshold are
omitted, so the layout JSON alone does not establish their effective normal
values. The installed Steam client's native gyro constructors establish values
`0`, `5`, and `0`, which are now explicit in both normal covers; see the
[evidence](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#normal-value-verification).
**Deleting a setting
from the upper cover would inherit the cursor value, not restore normal behavior.**
Do not invent zero values for all three or borrow a value from a different source
mode or a key activator.

The initial cursor implementation retained rotation calibration `4653` and normal
precision `0`. The author's reference-tuning follow-up replaces Base gyro settings
with the reference's rotation `3853`, precision `300`, conversion style `4`, and
speed deadzone `0`; natural sensitivity `300`, vertical ratio `200`, and activation
selection remain unchanged. The normal covers now restore precision `300`.
Cursor overlays inherit all other Base response settings and keep only their
four explicit Gated Gyro overrides.

Base RS settings already match the reference. Ramp 0 now uses sensitivity `150`
and vertical scale `80`; Ramp 1 uses `200` and `67`. Existing bindings, modifier RS
sensitivity `75`, and local cleanup thresholds remain unchanged. See the
[exact settings and inheritance policy](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#reference-tuning-and-gyro-inheritance-follow-up).
Regular modifier owners inherit gyro response; Gyro owners and LST/RST Temporary
Gyro override only activation. All intentional active `disabled` gyro modes remain
in place. The existing normal Tap Covers own response restoration; normal
response settings are not copied into the modifier parents.

**Activation-mask distinction:** the reference mask includes Start/Select as well
as both stick touches/deflections. It matches current Base's six-input selection
but differs from the Gyro variants' `211109453758464` four-input selection.
Group 370 does not specify Any/All; the effective rule depends on the underlying
stack. Copying its mask would therefore change gating in the Gyro variants and
would require a different restoration design. The two shared normal covers
inherit the appropriate gate because cursor overlays leave it untouched.
Never hard-code the Base gate into a cover shared by both variants.

## Layers and state transitions

Use two new overlays per layout, each shared by regular/Gyro owners:

| Role | Default title | Alternative title |
|---|---|---|
| Left modifier hold | L1: Temp Cursor Gyro | L2: Temp Cursor Gyro |
| Right modifier hold | R1: Temp Cursor Gyro | R2: Temp Cursor Gyro |

Separate owners avoid one modifier release clearing a still-valid opposite
hold. A single shared global layer would need additional ownership rules.

Clone the corresponding normal cover's primary-input release structure and
add the cursor properties from the table above. Keep unrelated inputs inherited.
Give the new layer no Always On action and no independent delayed timer.

| Event | Intended result |
|---|---|
| Initial primary press | Enter the existing modifier; begin the hold delay |
| Hold reaches 300 ms without a normal cover | Apply that owner's Temp Cursor Gyro; suppress the primary tap-release action |
| Delayed apply is interrupted before either overlay takes over | The parent's 350 ms repeating removal resets only the pending cursor target so its delayed apply can retry |
| Stick-touch release before the delay, with the modifier held and no normal cover | Apply Temp Cursor Gyro immediately, then clear that stick's LST/RST family |
| Stick-touch release after a normal cover | Clear that stick's family; keep the normal cover and all normal gyro properties; never add cursor gyro |
| A normal-cover input occurs before the delay | Apply the normal cover; prevent later cursor entry for this hold |
| A normal-cover input occurs after cursor entry | Apply the normal cover above it; restore all normal gyro properties for the rest of this hold |
| One stick is deflected alone | Preserve the current hold and cursor state |
| Both-stick condition qualifies | Apply the same normal cover; latch out cursor properties |
| Primary release | Remove the owner family and its normal/cursor overlays; preserve unrelated state |
| Short primary release before either overlay | Retain the existing Double Tap behavior |
| Later fresh primary hold | Start a new delay; cursor properties are eligible again |

Use the confirmed `300 ms` hold delay and leave natural sensitivity inherited.
Touch release is an intentional early-completion path, so 300 ms is not a minimum wait for every
cursor entry. The 25% edge region also intentionally advances stale recovery.

## Making the normal cover win

The requested design is to give the two existing normal Tap Covers explicit
normal-property overrides for every field changed by Temp Cursor Gyro: precision
speed `300`, haptic intensity `0`, haptic bump `5`, and movement threshold `0`.
Natural sensitivity stays inherited in both overlay types. Both forms replace
the complete primary input, including its pending delayed chord and 350 ms reset,
with their own release lifecycle. Verify that Steam retires both parent activators
when either overlay takes over; do not assume a release entry alone proves timer
cancellation. The reset targets only the cursor overlay and must never remove
the normal cover or reopen cursor eligibility during that hold.

The normal cover also needs explicit LS/RS **touch-input replacements**. Each
uses the existing three-entry structure, without inheriting a cursor add:

| Entry | Action |
|---|---|
| Owner-held chord | Empty guard, protecting a valid modifier hold |
| Regular Press | Interruptible, repeating recovery of this owner's regular/Gyro pair and both normal/cursor overlays |
| Touch release | Remove only the corresponding LST or RST Entry Point, Tap Cover, and Temporary Gyro; add no layer |

Preserve the existing touch guard's interruption settings; the interruptible
guard change below is specific to the new edge design. Keep the other stick's
family intact. Replace the whole touch input so a lower release cannot leak
through, and preserve directional, click, edge, and source-mode inheritance.

The cursor overlay should use the same cleanup-only touch replacement once
applied. This avoids re-adding an already completed target on every thumb lift;
the owning modifier retains the early-completion path while its delay is pending.
Both overlays still inherit the owner's edge logic and normal-cover inputs.

The parent's current touch-release activator has no chord condition of its own.
Its sibling owner chord protects the Regular Press recovery; do not assume that
it also qualifies Release Press. Trace losing the owner while a thumb is already
touching: recovery and input replacement must prevent a later release from
leaving an orphan cursor overlay. Check simultaneous normal-cover input and
touch release too, since separate activators have no array-order guarantee.

Keep vertical scaling, calibration, and unrelated settings inherited. Preserve
activation masks and Any/All rules.
Review the actual source-mode behavior before claiming a property override
preserves every disabled-gyro context. An active gyro
source must not accidentally enable gyro in a menu/timed context that disables it.

This has two maintenance costs:

- Normal gyro values would be explicit in both covers, with some also set in
  Base. Future tuning must keep all restoration values synchronized; omission
  in the cover is not a reset. Check precision speed, haptics, and thresholds.
- Layer application order determines which settings are exposed. Test a normal
  cover arriving just before, at, and just after the cursor delay. A late cursor
  apply must not land above the normal cover and defeat the latch.

Use the requested property overrides without adding a cursor removal to every
normal-cover input. Limit removals to their lifecycle/recovery purpose so they
do not repeatedly disturb unrelated delays. Add no Always On action to a cover.

## Stick edges and the command budget

Each of the four owner layers previously had two entries on each stick edge:
an owner-held empty chord and an interruptible repeating recovery removal.
The implementation adds one chord per edge, for eight new entries per layout:

| Entry | Condition | Action | Interruption |
|---|---|---|---|
| Owner guard | Primary modifier held | Empty; protect the valid hold | Interruptible, changed from the baseline's explicit Off |
| Override chord | Primary modifier AND opposing stick deflected | Add this owner's normal Tap Cover | Uninterruptible |
| Recovery | No protecting chord | Repeat removal of this owner's regular/Gyro pair, normal cover, and cursor overlay | Default interruptible; Hold to Repeat |

The edge itself supplies the local stick condition. Use **All** for the new
selector: an opposing-stick-only chord could add a cover to a stale modifier
with no owner held and suppress its cleanup. Including the owner refines
the author's chord sketch to preserve the requested no-owner
recovery and still uses three entries. Preserve the existing bumper predicate
in default and **soft trigger pull** in alternative; do not require both soft
and full pull under All. Resolve mask bits from the verified picker/schema
instead of treating legacy chord IDs as masks.

With the local edge active, the intended behavior is:

| Modifier held | Opposing stick deflected | Result |
|---|---|---|
| No | No or yes | Repeating recovery; never add a cover |
| Yes | No | Empty guard; keep the hold and current gyro properties |
| Yes | Yes | Add normal cover; suppress recovery |

The two chords overlap when the full condition is satisfied. Their execution
is not ordered by the stored list. The chosen interruption settings express the
intended priority, but overlapping-chord arbitration still needs a Deck check.
Verify the stronger chord applies the cover and that releasing the owner while
both sticks remain deflected exposes recovery. If that fails, revisit the
conditions without adding a fourth entry or leaving a valid hold unprotected.

Baseline LS recovery used outer radius `21000`; RS inherited Base's edge radius
`32767`. Those regions are farther out than the selected 25% override threshold.
The installed client's native edge checks add hysteresis when engaging:
10% of full scale for LS `dpad`, and 3% for RS `joystick_mouse`. The saved
outer radii are therefore **LS `4915`, RS `7209`**, targeting roughly 25%
engagement after source calibration. Both checks use radial input independently
of their movement deadzones. A nominal radius `8192` would engage closer to
35% on LS and 28% on RS in this build. No movement deadzone or Base setting
was changed; see the [native evidence](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#edge-threshold-verification).

**Accepted threshold change:** lower these eight owner edge regions per layout
to approximately 25%, with the outer-region sense preserved. Cleanup at that
earlier threshold when the owner is absent is intentional. Preserve LS movement
and RS mouse settings. There is no longer a requirement for separate override
and recovery thresholds on this input.

The opposing-stick deflection selector may use a different threshold from the
local edge region. Check both; changing `edge_binding_radius` alone does not
prove the full condition qualifies at 25% on both sides. That selector's threshold
and physical stick travel remain Deck checks; only its bit identity is verified.

Do not introduce repeating normal-cover additions just for symmetry. Test
both stick activation orders, both already deflected before the modifier hold,
and a held edge when the opposing stick changes state. Any repeat required for
reliable detection must be reviewed for timer interference.

## Cleanup, timer protection, and inherited behavior

- Extend each single modifier's guarded recovery from its existing three
  targets to four by including its own cursor overlay. Keep held-owner guards,
  default Interruptable, and Hold to Repeat. Do not clear the opposite owner.
- Both the new cursor cover and normal cover must clean up the owner's cursor
  overlay on primary release, along with the existing family. Order removals
  so no unintended parent release is assumed to replay after an overlay exits.
- Trace the opposite-modifier transition into Mod 2: it already applies both
  normal covers. They must override any prior cursor state and prevent a new
  cursor delay on either held modifier.
- Extend Mod 2's family recovery to include both cursor overlays. Extend
  combined-cover releases only for the side they invalidate, preserving the
  still-held side and persistent Gyro. Do not broaden the current-order scope
  or copy the separate Gyro-toggle release into recovery.
- Review every release/transition that removes these owner families, including
  uncovered releases into Double Tap. Remove invalid cursor state before adding
  an Always On window; preserve add-last entry and self-first exit ordering.
- All seven Double Tap windows already explicitly block both stick edges.
  Preserve those blocks so they cannot inherit the new cover-add chords.
  Trace their other inherited inputs too; no new layer changes may leak into
  a protected window through face buttons, stick releases, or modifiers.
- Ordinary overlays should inherit appropriate recovery. Do not copy edge
  cleanup into every new cover: it would hide the owner bindings and consume
  movement/ramp inputs unnecessarily.
- Keep the touch-release completion array ordered **add cursor first, then
  remove the matching stick family**. Normal covers replace this entire input
  with cleanup-only release behavior, preventing a later touch release from
  defeating the hold's override. Do not normalize this deliberate ordering into
  the usual removal-before-add transition.
- Keep the 350 ms cursor reset on each single-modifier parent's primary input,
  with Hold to Repeat On and Interruptable Off, removing only its pending cursor
  overlay. Touch-release completion is a separate mechanism. Both overlay types
  and all seven Always On windows replace the primary input; verify the reset
  stops across those transitions. Other delayed-apply reset extensions remain
  in their separate review TODO.

## Implementation sequence followed

1. Use title-form copies; confirm preset ordering and unique titles. Inventory
   all affected owner, cover, recovery, and protected-window paths in both layouts.
2. Add the two owner-specific cursor overlays and their lifecycle exits. Apply
   Gated Gyro's response/haptic properties with natural sensitivity inherited.
   Verify omitted normal values and preserve the activation gates, then explicitly restore
   every changed property in normal covers. Replace the primary input so either
   overlay stops the parent's pending cursor apply.
3. Retarget four primary delayed applies and eight touch releases per layout,
   preserving add-before-stick-removal order. Preserve the other thirteen
   normal-cover paths per owner. Give both overlay types explicit cleanup-only
   touch inputs; verify a normal cover blocks cursor entry for the entire hold.
4. Implement the three-entry edge design and accepted earlier cleanup region.
   Verify the owner-plus-opposing-stick All selector and ~25% behavior on both
   sticks, with movement and other layers' edge regions preserved.
5. Update family cleanup and Mod 2 transitions; verify inherited behavior through
   normal covers, menu layers, mode shifts, and Always On windows.
6. Scan all command budgets; verify preset order, title/ID round-trip, guards,
   target scopes, timing, and execution order. Adapt the existing recovery tests
   to the intentional additional targets rather than weakening their checks.
7. Update documentation and manual tests. Leave VDF conversion, version changes,
   and actual Deck validation as separate work unless requested.

## Runtime acceptance cases

Test both sides, both layouts, and regular/Gyro owners:

- Short tap still enters the expected Double Tap flow; a long hold enters cursor
  response/haptics without producing an unwanted tap on release. Check activation
  against the selected gate behavior for both regular and Gyro variants.
- Verify precision speed, haptic intensity, haptic bump, and movement threshold
  while cursor gyro is active, then check that the normal cover restores every
  one. Natural sensitivity must stay at the inherited value throughout cursor
  entry, override, and cleanup. No residual cursor property may survive override
  or family cleanup.
- Either stick-touch release completes cursor entry early if no override has
  latched, then clears only that stick's family. After either overlay is applied,
  repeated touch/release does not re-add cursor gyro or restart the hold delay.
- Every normal-cover input wins before and after the delay, including Start/Select
  and the opposite modifier. Its original key/mouse output survives. Subsequent
  thumb lifts only clean up LST/RST and cannot restore cursor properties.
- A normal-cover input at the delay boundary never leaves cursor properties
  active later in the same hold; a fresh modifier hold enables it again.
- A normal-cover input and touch release in the same update, before or at
  300 ms, leave normal gyro properties latched. The touch-release cursor add must
  not land above the normal cover and undo the override.
- One stick alone does not override cursor properties. Both orders, simultaneous
  deflection, threshold crossings, and already-held sticks follow the chosen rule.
- With no owner held, either edge recovers the stale family around 25%, even if
  both sticks are deflected. Release the owner while both edges remain active
  to check that the override chord cannot keep adding a cover or block recovery.
- Both Mod 2 orders and partial/full alternative trigger pulls preserve the
  correct held owner, all normal gyro properties, and persistent Gyro state.
- Missed primary releases and Steam-menu interruptions recover cursor overlays
  through the intended owner cleanup. No invalid cursor overlay remains.
- Lose the modifier owner while a stick is already touched, then lift that thumb.
  The unqualified parent release must not leave an orphan cursor overlay; check
  actual recovery/dispatch rather than assuming the sibling guard covers release.
- Always On windows keep their timers and isolation. An input held across window
  entry/exit does not cause inherited cover additions/removals inside the window.

## Runtime checks still open

- Verify the exact selector masks, approximate 25% calibration on both sticks,
  and overlapping-chord priority. The earlier cleanup threshold is accepted.
- Verify primary-input replacement cancels the pending cursor apply, including
  a normal-cover arrival at the 300 ms boundary, and touch replacement prevents
  re-entry. Any runtime failure requires a concrete revision before completion.
- Verify the property overrides preserve intended gate/source behavior through
  regular, Gyro, menu, and timed stacks, and confirm the native normal defaults
  in the target Deck client. Sensitivity and activation masks remain inherited.
- Verify whether trackpad-held face/D-pad mode shifts actually activate under
  modifiers. Targets 1039/1043 are marked `inactive modeshift`; enabled Base
  references alone do not establish runtime activation. Their key-only bindings
  omit normal-cover additions, but the earlier claim of a confirmed cursor bypass
  was too strong. Test before and after cursor entry and with trackpad touches
  held across transitions. Consider binding changes only if the bypass is reproduced.
