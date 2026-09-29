# Selected left-stick edge recovery

Date: 2026-09-28. Applied to both Neptune JSON layouts after the separate
repeat-convention commit `ebc55bc`. Layout version remains 90.2; VDF conversion
and runtime validation remain with the author.

## Author decisions

- Add LS-edge recovery to all eight modifier variants: the two single-modifier
  roles and both Mod 2 orders, each in regular and Gyro form.
- Also include both Menu Entry Points, both modifier scroll layers, and both
  Transition Sets. RTP Entry Point is outside this pass.
- For Transition Sets, apply the deeper recovery rule now: once neither menu
  button is held, remove the current Transition Set and both possible Menu
  Entry/Fn families. Apply this same scope to existing LS touch, RS touch, and
  RS edge recovery as well as the new LS edge.

## Fourteen recovery layers per layout

Every new LS-edge binding copies its corresponding RS-edge guards, removal
scope, stored binding order, and interruption/repeat settings. Transition Set
RS recovery is updated to the agreed scope before copying it.

| Parent layers | Count | Guard: recovery suppressed while… | Removal scope |
|---|---:|---|---|
| Left/right single modifier, regular and Gyro | 4 | That modifier is held | Its regular/Gyro pair and single Tap Cover: 3 targets |
| Both Mod 2 orders, regular and Gyro | 4 | Either modifier is held | Current order's regular/Gyro pair, all four singles, and three covers: 9 targets |
| Menu Left/Right Entry Point | 2 | That entry's menu button is held | Its own Entry Point and Fn layer: 2 targets |
| Left Scroll Down / Right Scroll Up | 2 | That scroll button is held | The scroll layer and its Double Tap Cover: 2 targets |
| Transition Set 0/1 | 2 | Either menu button is held | Current Transition Set plus both Menu Entry/Fn pairs: 5 targets |

Default uses L1/R1 modifier roles; alternative uses L2/R2. Single-owner
recoveries have two GUI entries, and Mod 2/Transition recoveries have three.
Every removal uses Hold to Repeat with default Interruptable, so the held-owner
chord(s) suppress it. Persistent Gyro and the opposite-order Mod 2 pair remain
outside their existing recovery scope. No new delayed-apply reset was added.

**Why these layers:** the author chose movement-based recovery across modifier
and scrolling interactions, including cases where touch/click recovery exists.
The menu entries gain direct LS recovery instead of relying on LS release into
Fn. Transition recovery now ends its invalid menu ancestry in the same entry.
This is a selected expansion of recovery gestures, not a finding that each
previously missing LS edge was a demonstrated runtime failure.

## Left-stick geometry and movement tradeoff

Each selected LS group keeps its `dpad` movement mode and its existing inputs.
Only the edge binding and two edge settings are added:

- `edge_binding_radius: "21000"`
- `edge_binding_invert: "0"`

These are the existing Fn LS-edge settings. They select an outer region rather
than inheriting Base's inverted edge region. No Fn direction mappings, movement
deadzone, click requirements, or other stick settings are copied.

**The LS edge can no longer supply an inherited WASD modifier while one of
these layers owns it**, even when a chord is suppressing cleanup. Base's shipped
edge slot is empty, but a user-configured Walk or similar modifier would be
displaced. WASD directional bindings themselves are unchanged. The author
accepted this tradeoff for the selected modifier/scroll families and does not
require gameplay modifier availability during menu interactions.

The Transition Sets previously had no explicit LS-edge binding; in their normal
stack, the underlying Fn layer already owns that edge. Their explicit recovery
now includes the Transition Set itself and both possible menu ancestries.

## Always On isolation

This change is the concrete example for the reusable
[inheritance review](../../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes):
changing a lower binding requires checking upper layers that can inherit it,
even when those layers were not originally part of the edit.

All seven Double Tap windows previously omitted LS edge. A new removal in a
lower layer could therefore be inherited through a timed window, particularly
in a stale or overlapping stack. Each window now explicitly blocks LS edge with
the same empty Regular Press already used on its RS edge:

- Left and right modifier Double Tap.
- LST and RST Double Tap.
- RTP Double Tap.
- Menu Left and Menu Right Double Tap.

These are **seven blocks, not seven cleanup functions**. They execute no layer
commands. Their existing 150/200 ms timers, outputs, self-first exits, and
add-last entries are unchanged. The LS edge's underlying action is unavailable
during each protected window; directional movement remains unchanged.

The target child's same-source LS edge is explicitly replaced in each of these
windows. Static structure establishes the configured block, not the current
client's scheduling of a previously pending activator. Test deflection held
across entry/expiry as well as deflection beginning during the window.

No additional LS recovery is added to overlays, ramp stages, or RTP Entry Point.
The RTP trackpad-touch momentum exception is preserved. The Fn layers already
had both edges and remain unchanged. Overlays inherit their owning stack's
recovery; shared or still-held interactions retain the existing guards.

## Transition Set cleanup depth

Each Transition Set has four guarded recovery inputs after this change:
LS touch, RS touch, LS edge, and RS edge. Their stored removal array is:

1. Menu Left: Fn Layer
2. Menu Left: Entry Point
3. Menu Right: Fn Layer
4. Menu Right: Entry Point
5. The current Transition Set

Subcommands execute bottom to top, so the current Transition Set is removed
**first**, then the two menu families. Both menu-button guards remain, and all
removals share one repeating Regular Press entry. A still-held menu button
prevents the whole recovery rather than being cleared out from underneath it.

This replaces the previous intentional self-only recovery for these two
layers. It is not a global clear-all: it does not remove the other Transition
Set, persistent Gyro, modifier families, or menu overlays. Recovery of invalid
menu helpers remains the separate owning-layer review in `todos.md`.

## Verification and Deck checks

- Actual `to-titles` conversion preceded edits; actual `to-ids` finalized them.
  All **1,527 runtime references per file** resolve and round-trip exactly.
- Both full command-budget scans pass, including inactive/unreferenced groups
  and disabled banks. Maximum remains three commands per input.
- All **199 active guarded recoveries per layout** repeat; six dormant guarded
  entries also repeat. Each file gained 14 recoveries and seven blocks, totaling
  41 GUI entries. Existing Transition Set changes only expand subcommand arrays.
- The 13 Always On incoming entries still add the timed layer last; all 30
  directly owned mutation entries still remove it first.
- A structural comparison against `ebc55bc` verifies that removing the 21 new
  edge definitions and 28 edge settings, and restoring six Transition Set
  removal arrays, reproduces each complete pre-change layout. Other inputs,
  movement, source modes, timers, metadata, IDs/order, and VDFs are preserved.
- [Recovery regression checks](../../tests/test_neptune_recovery.py) verify
  guards, target scope, geometry, Transition Set consistency/order, timed
  blocks, repetition, RTP exclusion, command budget, and reference ordering.
  `python3 -m unittest discover -s tests -v` passes all 12 tests.

On the Deck, verify:

1. Held single modifiers suppress cleanup. For each Mod 2 order/Gyro variant,
   either held modifier still suppresses it; with neither held, LS deflection
   clears the expected branch without toggling persistent Gyro.
2. Menu-entry/scroll guards preserve valid holds and pending cover/Fn delays.
   After missed releases, LS recovery clears the intended pair.
3. Both Transition Sets recover on all four inputs when neither menu button
   is held, and stay active when either is held. Check stacks entered from
   either Menu Fn layer and confirm unrelated state survives.
4. All seven Double Tap windows block inherited LS mutations while their
   timeout and intended second-press behavior still work. Test entering and
   leaving a window while the stick is already deflected.
5. Ordinary WASD movement remains correct, recovery uses the intended outer
   region, and the accepted edge-modifier restriction occurs only while an
   overriding layer owns that input. RTP momentum remains intact.

No fresh-load Deck test was available in this change.
