# Layout vocabulary

Use **button overlay** for a layer whose job is to change one button's action
or release behavior while running on top of an existing interaction. **Overlay**
is the short form when that scope is clear. This replaces the earlier term
“lightweight cover layer” in maintained documentation; saved layer titles such
as `L1: Tap Cover` do not need to change.

Use **stateful layer** for the persistent action layer of a mode. This replaces
the earlier term **stateful set**. These modes use action layers without
switching Steam action sets.

## Terms

| Term | Definition | Example |
|---|---|---|
| **Stateful layer** | Keeps a mode active after its entry gesture ends, until an explicit exit. Its transient helper and modifier layers are separate layers with narrower lifetimes. | Steering remains active when the dominant W/S control is released; the W/S and Mod 0–2 helpers clear, exposing steering fallback. |
| **Button overlay** | Changes one button's action or lifecycle, relies on the underlying interaction for broader behavior/recovery, and is not intended as a standalone mode. | `Menu Right: Enter` changes Start to Enter while the Menu Left interaction is underneath. |
| **Overlay** | Short form for a button overlay, or the broader category for an equally limited interaction involving linked buttons. | `L1&R1: Tap Cover` covers the two linked modifier releases; it is an overlay, but not strictly a one-button overlay. |
| **Owning layer** | A layer that applies an overlay and is responsible for recovering it when that interaction becomes invalid. A shared overlay can have multiple owners. | `L1: Modifier 0` and its Gyro variant both apply `L1: Tap Cover`. |
| **Interaction stack** | The active layers belonging to one interaction, regardless of their position relative to unrelated active layers. | Menu Left Entry + Fn + the Enter overlay applied for Start. |
| **Guarded recovery** | An owner-held chord suppresses an interruptible, repeating Regular Press removal on the same input. It clears invalid state when no protecting owner is held. | L1's RS-edge fallback removes its regular/Gyro modifier pair, Tap Cover, and Temp Cursor Gyro. |
| **Lifecycle exit** | A normal release, timer expiry, or deliberate transition with its own removal scope and conditions. | A Double Tap window removes itself on timeout. This is not a guarded recovery binding. |

These are repository design terms, not new Steam Input object types. In
particular, an action layer is not automatically a button overlay just because
it sits above another layer. Full modifier and Fn layers provide a broader
interaction and own their recovery.

## Concrete button overlays

**`Menu Right: Enter`:** Menu Left Entry/Fn applies it when Start is pressed.
The overlay provides Enter on Start and removes itself on Start release. The
Menu Left interaction remains responsible for its own recovery and for any
invalid overlay it applied. Start still being held is a valid interaction and
must be preserved when Select is released.

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

Menu Left: Backspace, the single-button Tap Covers, and the individual Double
Tap Covers are other examples. A combined modifier Tap Cover spans both
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
