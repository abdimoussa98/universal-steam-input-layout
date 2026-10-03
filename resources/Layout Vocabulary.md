# Layout vocabulary

Use **button overlay** for a layer whose job is to change one button's action
or release behavior while running on top of an existing interaction. **Overlay**
is the short form when that scope is clear. This replaces the earlier term
“lightweight cover layer” in maintained documentation; saved layer titles such
as `L1: Tap Cover` do not need to change.

Use **stateful layer** for the persistent action layer of a mode. This replaces
the earlier term **stateful set**. These modes use action layers without
switching Steam action sets.

## Runtime rules (author-confirmed, 2026-09-30)

The rules themselves are in the
[Layer Definition of Done](Layer%20Definition%20of%20Done.md#rule-tables),
by ID. This list says what the author observed behind them; each observation
is an entry in [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md)
(A12, A17 and A19 for the last three).

- **R101:** never use Steam's `hold_layer` API: the author considers it too buggy.
  Implement every layer lifetime with explicit `add_layer` and `remove_layer`
  commands, including layers active while a button is held.
- **R102:** never switch Steam action sets (`CHANGE_PRESET`). Keep the structural Base
  action set and implement modes with action layers. Historical “Transition
  Set” names refer to layers, not action-set switching.
- For the removal/reset behavior discussed in the stack investigation, the
  timer **restarts**, then waits **300 ms**; it is not cancelled. This is the
  author's runtime observation, not a claim that every configured delay is
  300 ms. The untimed search model does not yet represent this behavior.
- **Chords latch** (author's manual test, 2026-10-01; rule R112). Once a chorded
  activator is active, releasing the chord button doesn't re-evaluate it. The
  input stays in the chord until the button the chord is bound to is released.
  A bind therefore can't hand over from a chord to a Regular Press when the
  chord button goes up. Hypothesis, not yet tested: a `remove_layer` call
  re-evaluates held inputs, the same way it restarts delays.
- **An inverted edge on a D-pad-mode stick isn't caught reliably** (author's
  Deck testing, 2026-10-01; rule R111). Never use one to add or remove a layer. A normal
  outer edge and its Release are reliable there. An inverted edge that only
  sends output (a walk bind, the WASD modifier) is fine, and mouse-mode sticks
  aren't affected.

**Known implementation conflicts:** none since 90.14. Until 90.13 both Neptune
layouts contained five `hold_layer` commands, on the trackpad `click` inputs:
three added `RTP: Mouse Buttons` and two added `LTP: Arrow Keys`. 90.14
replaced them with `add_layer` and explicit removals (R101;
[record](../findings/2026-10-03-pad-middle-click/README.md)). Neither
current variant contains `CHANGE_PRESET`. Archived snapshots and generic
format/parser documentation may retain historical APIs.

## Terms

| Term | Definition | Example |
|---|---|---|
| **Stateful layer** | Keeps a mode active after its entry gesture ends, until an explicit exit. Its transient helper and modifier layers are separate layers with narrower lifetimes. | Steering remains active when the dominant W/S control is released; the W/S and Mod 0–2 helpers clear, exposing steering fallback. |
| **Button overlay** | Changes one button's action or lifecycle, relies on the underlying interaction for broader behavior/recovery, and is not intended as a standalone mode. | `Menu Left: Double Tap Cover` changes Select's release while `Menu Left: Escape` is underneath. |
| **Overlay** | Short form for a button overlay, or the broader category for an equally limited interaction involving linked buttons. | `L1&R1: Tap Cover` covers the two linked modifier releases; it is an overlay, but not strictly a one-button overlay. |
| **Owning layer** | A layer that applies an overlay and is responsible for recovering it when that interaction becomes invalid. A shared overlay can have multiple owners. | `L1: Modifier 0` and its Gyro variant both apply `L1: Tap Cover`. |
| **Interaction stack** | The active layers belonging to one interaction, regardless of their position relative to unrelated active layers. | `Menu Left: Escape` + its Double Tap Cover; or L1's modifier + Tap Cover + Temp Cursor Gyro. |
| **Guarded recovery** | An owner-held chord suppresses an interruptible, repeating Regular Press removal on the same input. It clears invalid state when no protecting owner is held. | L1's RS-edge fallback removes `L1: Modifier 0`, its Tap Cover and its Temp Cursor Gyro. |
| **Lifecycle exit** | A normal release, timer expiry, or deliberate transition with its own removal scope and conditions. | A Double Tap window removes itself on timeout. This is not a guarded recovery binding. |
| **Cleanup function** | The backup exit for a stuck layer: a guarded recovery. It fires when a likely next input is pressed and no owner is held (R133). | `L1: Modifier 0`'s right-stick touch removes LB's layers when LB isn't held. |
| **Guard** | The buttons whose chords suppress a cleanup function. Holding any of them stops it (R127). | LB for `L1: Modifier 0`; LB and RB for `L1!R1: Modifier 2`. |
| **Exit** | A Release that removes the layer it is bound in. | LB's Release in `L1: Modifier 0`. |
| **Keeper** | What keeps a layer alive: usually the button whose Release removes it, otherwise a thumb on a stick, a timer, or a mode. The Cleanup audit computes it. | LB keeps `L1: Modifier 0`; a thumb on the left stick keeps `LST: Entry Point`; its 150 ms timer keeps `L1: Double Tap`; `Steering` is a mode. |
| **Cover (an input)** | An upper layer covers an input when it binds it, so a lower layer's binding on that input can't fire. Cover-type layers (Tap Covers, Double Tap Covers, Temp Cursor Gyro) are built to do this on one button. | `L1: Tap Cover` covers LB over `L1: Modifier 0`: its Release fires, not the modifier's. |
| **Pair** | For the hidden-exit rule (R136): one lower layer plus one layer that can sit on top of it and covers one of its exits. | `Tab` under `L1: Double Tap`: lifting the thumb off the left pad inside the window misses `Tab`'s Release. |
| **Temporary guard** | A short-lived layer that waits for one input to return to rest. Nothing is added over it (R137). | `Steering \| LS: Entry Guard`, `Steering \| LS: Fallback Hold`. |

These are repository design terms, not new Steam Input object types. In
particular, an action layer is not automatically a button overlay just because
it sits above another layer. Full modifier and Fn layers provide a broader
interaction and own their recovery.

## Concrete button overlays

**`Menu Right: Enter` and `Menu Left: Backspace` (removed in 90.9):** these
overlays held the second menu button until its release. On 2026-10-01 the
author decided they aren't needed: the menu whose button is held owns the
combo, the menu chords type Enter / Backspace directly, and a still-held
second button falls through to Base when the first is released
([record](../findings/2026-10-01-intended-flow-checker/README.md#author-decisions-2026-10-01)).

**`L1: Tap Cover`:** the L1 modifier applies it to change L1's release behavior.
The overlay suppresses the parent's normal release into a Double Tap window
and instead removes the L1 modifier family and itself. Its local exit can have
several removal subcommands; “one button” describes the affected control, not
the number of commands. Alternative uses L2 for the same modifier role.

**`L1: Temp Cursor Gyro`:** is a response overlay, not strictly a one-button
overlay: it supplies cursor response/haptic properties and owns cancellation
across several inputs. Those inputs repeatedly remove only cursor, exposing the
modifier's output and repeating normal-cover addition. The normal Tap Cover
inherits gyro and prevents re-entry for the rest of the hold. Cursor inherits
stick-touch completion/cleanup; the normal cover explicitly replaces those
releases with cleanup only. Both keep the primary family-release exit, and
the modifier owner remains responsible for recovering both overlays.

The single-button Tap Covers and the individual Double Tap Covers are other
examples. A combined modifier Tap Cover spans both
buttons, so use the broader word **overlay** for that case.

## Ownership and limits

The owning layer's stale-state recovery must include invalid overlays it
applies. Overlays keep their local exits and inherit broader recovery instead
of duplicating every cleanup binding. Preserve still-held buttons, valid shared
overlays, persistent modes, and unrelated interactions.

“One button” describes the overlay's primary responsibility, not a claim that
every other source setting passes through. Existing menu overlays also disable
gyro, and some block RS edge; those restrictions are intentional in menu use.

Normal releases and Always On expiry retain their own scope. For exact guards,
repeat behavior, ownership, and execution-order constraints, see
[guarded recovery](Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape),
[overlay ownership](Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership),
and [Always On isolation](Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround).
