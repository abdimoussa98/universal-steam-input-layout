# Todo:

Manual Deck validation is tracked in [the separate testing checklist](manual-testing.md).

## Done

- [x] Make L1&R1: Tap Cover interruptable (in R1!L1, L1!R1, R2!L2, and L2!R2 layers)

## Gamepad layer

- [ ] Move gamepad layer → Menu Right + RS click / Menu Left + LS click
  - Note: requires same-side input (claw style); not frequent, so acceptable tradeoff

## Steering

- [ ] Add steering stateful set
- [ ] Add steering layer → Right Menu + LS click
- [ ] Include W / S modifiers on bumpers or left stick up / down
  - Intent: steering is primarily handled via bumpers
  - Left stick up / down acts as fallback to base layer behavior without exiting the stateful set
- [ ] Duplicate bumper mod 0 / 1 layers
  - Mod 0 when `L1!R1`: "W" + R1 (empty)
  - Mod 1 when `R1!L1`: "S" + L1 (empty)
  - Use opposite bumper to increment layer from mod 0–2
- [ ] Scroll wheel on joystick; hold up / down to exit

## Menu stateful set

- [ ] Add menu stateful set
  - Enter: Menu Left + Right
  - Exit: both sticks deflected, or one stick deflected + any face button
  - Inputs: D-pad → arrow keys; face buttons → Enter / Tab / Escape / Backspace
  - On entry: remove gyro stateful set

## Menu gyro

- [ ] Stateful menu gyro
  - Activate via Left Menu + RS click
  - Only remove when both left and right sticks are deflected
- [ ] Temporary menu gyro
  - Activate via L1 / R1 holds (tap covers)
  - Ensure proper add / remove behavior during hold lifecycle
  - Match Enter / Backspace to current Menu Left / Menu Right behavior

## Ramp up / triggers

- [x] Remove dedicated trigger layers and the old layer-based chorded ramp-up arrangement
  - Confirmed in both layouts: dedicated trigger layers are gone. Base still intentionally uses grouped Any chords to select or suppress ramp-up; this does not mean removing every ramp-up chord
- [x] Move ramp up gyro on / off entry selection to Base
  - Base RS edge adds Gyro Off Ramp Up normally, or Turning Ramp Up 0 directly while a firing control is held. Modifier-held input suppresses entry. Firing controls are L2/R2 in default and L1/R1 in alternative
- [x] Have firing controls remove Gyro Off Ramp Up during ramp-up
  - Gyro Off Ramp Up owns repeating, uninterruptible removal on default trigger pulls / alternative bumpers. Turning Ramp Up 0/1 leave those firing inputs unoverridden, inheriting the removal while Gyro Off Ramp Up remains below them
  - Verified from both JSON layouts on 2026-09-28; this is configuration verification, not a fresh Deck runtime test
- [x] Match default trigger configuration to the July reference (clarified scope of the hip-fire TODO; alternative excluded)
  - Both Base trigger groups now match the reference's bindings and settings, retaining their own group IDs. Removed only the explicit `adaptive_threshold: "0"` settings; no Soft Press/hip-fire activator was added, since the reference triggers do not use one
  - Reference: [MOST_RECENT_LAYOUT.post-fix.json](findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json). Fresh-load checks remain in [manual testing](manual-testing.md#default-trigger-reference-match)

## Sticks

- [x] Add left-stick edge cleanup only where needed, matching appropriate right-stick recovery
  - Implemented in both layouts: all eight modifier variants, both Menu Entry Points, both scroll layers, and both Transition Sets; see [scope, guards, and validation](findings/2026-09-28-left-stick-recovery/CHANGES.md). RTP Entry Point remains excluded; Fn layers already cover both edges
  - New LS recovery matches each RS guard and family scope, with Hold to Repeat and default Interruptable. Single modifiers remove three targets; Mod 2 removes its nine-target branch; menu entries and scroll layers remove their own pairs. Persistent Gyro remains intact
  - Author-approved Transition Set depth: LS/RS touch and edge all remove the current Transition Set first, then both Menu Entry/Fn families, only when neither menu button is held. Invalid menu-overlay recovery remains the separate ownership review
  - Added explicit LS-edge empty blocks in all seven Double Tap windows to prevent inherited layer mutations while Always On is active; existing timers and self-first/add-last boundaries remain intact
  - Uses Fn's LS outer region (radius 21000, inversion off) without changing WASD directions. The inherited WASD modifier is displaced while these layers own the edge; see [the accepted tradeoff](resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions)
- [ ] Add WASD modifier scaffold (user-defined)
  - Empty bind on left stick (soft press) for WASD modifier
  - Supports: WASD only, modifier only, or both (hipfire aggressive / relax compatible)
  - User defines modifier key
- [ ] Add haptics to FN layers
  - Apply to LS and RS

## Global stateful behavior

- [ ] L1 + R1 clears all stateful sets
  - Exception: gamepad stateful set is preserved

## Bugs

- [ ] Fix tap cover / menu entry bug (start delay interrupt)
  - [Coverage audit for both layouts](findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md): 7 of 19 delayed-add paths per layout already have the reset—both Menu Entry → Fn paths, all four combined-modifier paths, and Turning Ramp Up 0 → 1. Deck validation of interrupted holds/retries is tracked in the [manual checklist](manual-testing.md#menu-buttons)
- [ ] Fix tap covers not properly re-adding after interrupt
  - [Binding inventory](findings/2026-09-28-delayed-apply-reset-audit/INVENTORY.md) and [proposed follow-up work](findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md#proposed-todo-split-and-validation); missing resets are not proof of runtime failures
  - Proposed additions, not yet implemented: four single-modifier paths, then LST/RST Entry → Tap Cover per layout. Keep resets in the parent owning the pending apply; preserve overlays and the three-command limit
  - Preserve the author-confirmed RTP touch exclusion for trackball momentum. Defer the four scroll/menu-key Double Tap Cover paths until a design preserves output timing within three entries; leave the 5 ms Gyro Off → Turning Ramp Up 0 handoff unchanged unless it fails. These deferred choices are audit recommendations, not confirmed historical exclusions
- [ ] Split menu entry layer into separate Menu Left / Menu Right layers
- [x] Confirm menu helper/cover overrides are intentional within the overlay design
  - Keep Backspace / Enter, Escape / Tab, and the two Menu Double Tap Covers local to their button/action; the underlying stack owns recovery. Release-only exits remain valid; review invalid residual helpers in the owner's recovery instead of automatically adding independent edge cleanup to each overlay
  - Author confirmed: Start/Select menu interactions are not used during gameplay. Preserve disabled gyro in all six layers and the Escape / Tab RS-edge blocks; WASD modifiers and ramp-up are not required in menu context
  - Preserve the still-held second menu button; do not add Enter / Backspace removal to the first Fn button's release
  - Background: [button overlays and inherited cleanup](resources/Steam%20Input%20JSON%20Structure.md#button-overlays-and-inherited-cleanup), [vocabulary](resources/Layout%20Vocabulary.md), and both audits

## Layer cleanup

- [x] Complete the static [cleanup audit](findings/2026-09-28-neptune-cleanup-audit/AUDIT.md) and [blocking audit](findings/2026-09-28-neptune-blocking-audit/AUDIT.md) for both layouts, including all layers, entry/exit references, dormant groups, and Always On ordering
- [x] Document per-layer cleanup and blocking, with [concrete scope examples](resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) and guidance in the editing skills
- [x] Enable Hold to Repeat on every guarded recovery removal in both layouts; see the [separate change record](findings/2026-09-28-repeating-recovery/CHANGES.md). Static validation passed; Deck behavior remains part of the [manual recovery checks](manual-testing.md#missed-releases-and-cleanup-scope)
- [ ] Review owning-layer recovery against the [overlay cleanup ownership rule](resources/Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership)
  - Each layer applying an overlay is responsible for removing it during stale-state recovery when that interaction is no longer valid; retain the overlay's local exit and inherited recovery
  - Trace shared owners and still-held buttons before extending target lists. Review the menu Entry/Fn helpers that currently rely on another related-button press after parent recovery; preserve valid held helpers and normal release behavior

## Carried over

- [ ] Make base gyro activation dependent on: left stick deflect, right stick deflect, left stick touch, right stick touch, Select, and Start all being held at the same time. This removes the need for mode shifts everywhere we want to hold Start and Select (L1/R1 layers and Menu button layers)
- [ ] Handle cursor gyro layer (may be covered by Menu gyro above)
- [ ] Clear all unnecessary layers on action set swap
- [ ] Add temp gyro to both right and left stick touch
