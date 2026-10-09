# Plan: menu chords, RTP access in Steering and fallback threshold

Status, updated 2026-10-08: implemented as **90.38** in both working layouts
after the author approved implementation. See the
[build and validation record](../findings/2026-10-08-steering-rtp-and-menu-chords/README.md).
The sections below preserve the approved design and its review requirements.
Read using the repository's layout-prep and binding-order skills; both
variants pass the layer-order, preset-order, sequential-ID and unique-title
preflight checks. Analysis used temporary title-form copies.

## 1. Repeat the menu entry chords everywhere they are needed

90.37 changed only Base. The same two buttons still use repeating
`Full_Press` entries in three other owners:

| Owner | Select target | Start target |
|---|---|---|
| Base, already fixed | `Menu Left: Entry Point` | `Menu Right: Entry Point` |
| `Steering` | `Stateful | Menu Left: Entry Point` | `Stateful | Menu Right: Entry Point` |
| `Steering | LS: Fallback Guard` | Same Stateful target | Same Stateful target |
| `Cursor Gyro` | Same Stateful target | Same Stateful target |

Convert those six remaining entries per variant into self-chords, retaining
their existing targets. Select (`button_menu`) selects mask `4096`; Start
(`button_escape`) selects `16384`. Both repeat (`hold_repeats: "1"`) and
are uninterruptible (`interruptable: "0"`), as in Base. Layers inheriting
these entries get the change without redundant local copies.

Also review the menu Entry Points and Fn layers themselves. Four existing
cross-button entries add `Menu Left!Right: Entry Point` or
`Menu Right!Left: Entry Point`: the opposite button in each ordinary Entry
Point and Fn layer. They are already chords on the first menu button, but
do not repeat. Plan to enable repeating entry where it must work when
exposed under a held button; retain the first-button condition and current
command order. A self-chord would lose that condition. Check the Stateful
equivalents, which enter their Fn layer directly instead of that chain.

Classify every menu binding before changing it: entry, delayed Fn apply,
key output, owner guard, cleanup, release or delay reset. Keep the 200 ms
holds and 250 ms resets; do not turn timed holds into immediate repeats,
repeat key output incidentally, or turn interruptible cleanup into an
uninterruptible self-chord. Driver-layer Tab/Escape outputs, protected
windows and Gamepad's intentional menu behavior have separate purposes.

## 2. Allow RTP layers in Steering; isolate them only in windows

**Author decision, 2026-10-08:** “i dont want the rtp layers blocked in
steering unless its it windows and for delays it should follow our existing
patterns for them by added the delayed layer first then removing rtp layers”.
This supersedes the proposed haptic-only fix and retention of the old block.

Remove the explicit empty `right_trackpad/touch` binding from `Steering`
and `Steering | LS: Fallback Guard`. Let Base's repeating, uninterruptible,
explicitly silent RTP Entry Point add inherit. Remove their redundant pad
groups if no local behavior needs them; preserve effective mouse settings
and the inherited click. Ordinary Steering helpers must permit the RTP
sequence too, including tap/double tap and circular scroll. A pending delay
alone is not a reason to block RTP entry.

The old block originated as the
[90.7 F1 workaround](../findings/2026-09-30-steering-dod-audit/README.md#f1-rtp-double-tap-inherits-steering-layer-commands):
RTP Double Tap could sit over Steering and inherit stick layer commands
during its Always On timer. 90.35 copied the block into fallback when
Steering stopped remaining underneath. Keep that record as history; the
new design permits that route and protects the window itself instead.

### Delayed applies and RTP cleanup

Use the existing
[complete-apply-before-cleanup pattern](../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release)
for RTP cleanup in a pending Steering transition. When a relevant RTP
release/cleanup completes the pending apply, its execution order is:

1. Add the matching delayed target, retaining its owner/direction condition.
2. Remove the applicable RTP layers that can be present in that stack.

The same ordering applies when the delayed activator itself carries that
cleanup. Put those commands in one entry, not independently scheduled
activators. Stored arrays run bottom to top: RTP removals are above the
add, and the add is at the bottom. Do not remove RTP layers first and reset
the pending delay before completing its target. Do not change hold durations
or enable repeated key/wheel output as part of this change.

Current Steering/Stateful delayed layer entries to trace in both variants:

| Owner | Delayed target |
|---|---|
| `Steering | LS Down: Modifier 0` | `Steering | LS: Tap Cover` |
| `Steering | LS Up: Modifier 1` | `Steering | LS: Tap Cover` |
| `Steering | R1!L1: Modifier 2` | `L1: Tap Cover` |
| `Steering | L1!R1: Modifier 2` | `R1: Tap Cover` |
| `Stateful | Menu Left: Entry Point` | `Stateful | Menu Left: Fn Layer` |
| `Stateful | Menu Right: Entry Point` | `Stateful | Menu Right: Fn Layer` |

L1/R1 become L2/R2 in alternative. Include Gyro modifiers reachable from
fallback and their cursor/cover transitions in the inheritance review.
For each path, record which input owns completion, whether an RTP layer
covers it, which target is valid, and which RTP layers are actually removed.
Trace Entry Point, Tap Cover, Circular Scroll and the click layers; do not
blindly remove every RTP-named layer or reapply a target after its completed
cover has taken ownership. Directional transitions retain their conditions.

### Window behavior

Keep the existing restrictions inside `Steering | LS Up: Double Tap` and
`Steering | LS Down: Double Tap`, and all other Always On windows. Run the
Window audit with the newly reachable RTP-over-Steering stacks. In
`RTP: Double Tap`, replace inherited layer-changing inputs with their known
output when it is unambiguous; otherwise explicitly block them during the
window, following R140. Record any temporarily displaced movement.

An Always On window still leaves **self first**, before other layer changes
(R148), and is added last (R146). The add-delayed-target-before-RTP-cleanup
pattern does not authorize adding a target while `RTP: Double Tap` is still
active: any such early exit first removes that window, then completes the
valid apply and cleans the remaining RTP helpers. Ordinary pending delays
and Always On windows remain distinct.

### Haptic behavior

The old empty touch activator omitted haptic settings, unlike Base's
explicit haptic 0. That remains a plausible explanation for the reported
bump, not a verified cause. With the block removed, normal Steering touch
uses Base's silent entry; preserve strong click feedback. Check touch,
hold, release, double tap and click on a fresh Deck load. If a bump remains,
trace the effective group and activator settings rather than restoring the
block.

## 3. Require near-full up/down deflection to enter fallback

Today `Steering`'s `joystick/dpad_north` and `dpad_south` are repeating
Regular Presses. Each adds Fallback Guard, then removes Steering, with a
strong haptic (`3`), repeat rate 50 ms and Interruptable Off. Steering's
stick is four-way, deadzone `13276`; Fallback Guard's is eight-way.

Change those two activators to `Soft_Press`, with
`activation_threshold: "29031"`. This is the exact value used by
`Gyro Off Ramp Up` and `Turning Ramp Up 0` for their outer Soft Presses.
Keep the strong entry bump, repeating held-input support, and existing
swap order: **add Fallback Guard, then remove Steering**. In the stored
array the removal is above the add, because arrays execute bottom to top.

Expected behavior: a shallow up/down movement in Steering does not enter
fallback; crossing the near-rim threshold adds fallback and gives the
strong bump. Fallback then supplies W/S, with its existing eight-way WASD.
Its W/S outputs themselves do not gain the near-rim threshold. Steering's
A/D and the right-stick ramp retain their current settings.

Verify on the Deck that Soft Press on a D-pad direction reads the intended
axis deflection. The existing simulator does not model numeric stick
distance, so saved-setting checks plus binary transition scenarios are
insufficient to establish this behavior. Record that dependency in the
assumptions register when building; do not call it verified because the
right-stick edge uses the same number.

## 4. Add the repeating return chord on fallback's left-stick edge

The fallback currently leaves its edge unbound and inherits Base's empty
WASD-modifier Soft Press. Add a local `joystick/edge` chord whose command
is `add_layer {{Base::Steering}} 0 0`, with Hold to Repeat.

**Implemented interpretation:** “the chorded bind itself should be inverted” most
naturally describes an inverted stick-edge activator: return inward while
either driver is held. It is different from negating the driver condition
(neither driver held). The author has been asked which meaning they intend.
90.38 uses the inward-edge interpretation, local to fallback:

| Setting | Default | Alternative |
|---|---|---|
| Chord buttons | L1 or R1 | L2 or R2, soft/full pull as the existing driver selectors |
| Modern mask | `12` | `50331648` |
| Any/All | Any (`gyro_ratchet_button_requireany_or_all: "0"`) | Any (`"0"`) |
| Inversion | Activator `edge_binding_invert: "1"` | Same |
| Repeat | `hold_repeats: "1"` | Same |
| Action | Add Steering | Add Steering |

Keep the inversion on this entry, not on the whole joystick group. The
requested `29031` applies to Steering's directional Soft Presses; it does
not by itself specify a new radius for the fallback's inverted edge.
Keep this return silent unless feedback is requested for it too.

Implementation findings (see scenarios 90.38 S2/S3 in the build record):

1. **The edge may be hidden.** A driver pressed with the stick out adds a
   Gyro Modifier 0/1 over fallback. Those modifiers explicitly bind the LS
   edge, as do further covers. A fallback-local chord cannot run through an
   overriding input. Trace driver-before-centering, centering-before-driver,
   and return after a cover ends. If the intended return must happen while
   those layers answer the edge, design a context-specific path that reaches
   it; never make ordinary Gyro modifiers enter Steering outside fallback.
2. **An add alone creates a new stack.** Since 90.35, Steering and fallback
   normally replace each other to avoid the reported four-way/eight-way
   inheritance problem. The requested edge add alone can leave fallback
   underneath Steering. Honor the requested add and review that new stack,
   its cleanup and subsequent driver behavior; do not silently append a
   fallback removal. Ensure another near-rim push cannot cause a repeated
   swap/bump loop or leave the wrong stick mode active.

## 5. Inheritance and verification

Before installation, record effective input providers for Base/Gyro,
Steering, fallback, Cursor Gyro, their menu Entry Points/Fn layers, driver
layers, Gyro modifiers, Temp Cursor Gyro, Tap Covers and Double Tap windows.
Include both possible orders of Steering and fallback if the additive edge
return makes those reachable. Recheck the existing R139 right-pad inheritance
exceptions: they were reviewed against the previous empty touch entry.
Retire or narrow any that become stale when Steering inherits Base's touch,
and document newly reachable RTP-over-Steering stacks. Review R170/R171 obligations for the new bound
edge while preserving intentional survivors and protected timers.

Tests for both variants:

- Each menu entry owner: press inside it, enter/expose it while the button
  is held, thumb resting on either stick, missed release, and re-entry after
  a Double Tap window. Cover the cross-button chain and Stateful Fn route.
- Right-pad touch in Steering/fallback and inherited contexts: silent
  entry, working tap/double-tap/circular-scroll routes, mouse movement and
  strong centre/outer click feedback. Exercise RTP held before Steering
  entry and touched inside each helper, plus missed touch release.
- RTP cleanup during each pending delay: the valid target is added before
  ordinary RTP removals; completed covers do not re-enter it. Test just
  before/at the deadline and after a window exposes the held input.
- RTP Double Tap over Steering: no inherited layer mutation during the
  window, output/block replacements as reviewed, and self-first early exits.
  Steering's own Double Tap windows retain their pad restrictions.
- Up and down: below threshold, crossing threshold, entering Steering with
  stick already out, holding at the rim, moving diagonally in fallback,
  releasing/repressing, and driver presses around the crossing.
- Fallback edge: neither/left/right/both drivers, driver before/after the
  inward edge, Gyro modifier and cover above fallback, missed release,
  already-held input after a removal, and the new additive stack's exits.
- Both-driver clear still ends at Base; menu-plus-stick clear retains the
  established Gyro behavior. Right-stick ramp exits remain correct.

Separate exact saved-binding assertions, simulator scenarios and physical
Deck checks. Extend simulator threshold support only if it can represent
the new behavior honestly; numeric threshold acceptance still needs Steam.

## 6. Build and release after the plan is settled

Extend the frozen 90.37 builder with readable-title edits. Keep historical
builder tests pinned to their historical releases and move the working-layout
contract to the new builder. Update current scenarios only where behavior
intentionally changes, with an explanation of the new contract.

Run the fix pipeline, review the change report, and require all four build
audits (Budget, Window, Flow, Cleanup) to pass for both variants. Run the full
documented active Python suite and Node exporter tests; save the results and
unverified-assumption report. Review the complete descriptions, bump both
variants once (90.38 if still the next release), export both VDFs and save
their JSON/VDF version snapshots. Keep the separate delay experiment deferred.

90.38 includes both JSON/VDF working files and version snapshots. The local
fallback edge remains hidden while a Gyro modifier or cover owns that input;
extending the return through those overrides remains a separate design question.
Physical threshold, inverted-edge reliability and haptic feel remain Deck checks.
