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

## Cursor gyro

- [ ] Cursor gyro (stateful)
  - Activate via Left Menu + RS click
  - Only remove when both left and right sticks are deflected
- [ ] Temp cursor gyro
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
- [x] Add WASD modifier scaffold (user-defined)
  - Both layouts use the July reference's Base left-stick Soft Press setup, with an explicit empty binding in place of `KEYPAD_ASTERISK`; the user chooses the modifier key
  - Copied the reference's thresholds, style, inner-ring settings, and noninterruptible WASD presses. The empty scaffold sends no modifier; WASD-only, modifier-only, and combined behavior after assigning a key are covered in [manual testing](manual-testing.md#wasd-modifier-scaffold)
  - Existing LS-edge recovery and Double Tap blocks still override this slot. See [configuration and inheritance](resources/Steam%20Input%20JSON%20Structure.md#user-defined-wasd-modifier-scaffold)
- [x] Add haptics to Fn stick-direction key selection
  - Both Menu Fn layers in both layouts: `haptic_intensity: "2"` on their eight directional keybinds (four LS + four RS), totaling 16 entries per layout
  - Separate mode-shift bindings, cleanup, empty guards, touch/click actions, and timer ordering are unchanged. Upper layers can inherit the Fn directional feedback; verify feel in [manual testing](manual-testing.md#menu-buttons)

## Global stateful behavior

- [ ] L1 + R1 clears all stateful sets
  - Exception: gamepad stateful set is preserved

## Bugs

- [x] Fix menu-entry start-delay interruption
  - Both Menu Entry → Fn paths apply after 300 ms and have a repeating 350 ms reset with Interruptable Off. Implemented in both layouts; Deck validation remains in the [manual checklist](manual-testing.md#menu-buttons)
- [x] Fix combined tap covers not properly re-adding after interrupt
  - All four Mod 2 variants per layout (both press orders, regular and Gyro) apply the combined Tap Cover after 200 ms and reset it every 250 ms with Interruptable Off. Deck validation remains in [triggers and ramp-up](manual-testing.md#triggers-and-ramp-up)
- [x] Split menu entry layer into separate Menu Left / Menu Right layers
  - Both layouts have distinct Menu Left: Entry Point and Menu Right: Entry Point layers and their own Fn paths
- [ ] Review extending the delayed-apply reset to additional tap-cover paths
  - Rechecked both layouts on 2026-09-29: coverage remains 7 of 19 delayed-add paths—the two menu paths, four combined-cover paths, and Turning Ramp Up 0 → 1. The completed fixes above do not imply every delayed apply needs a reset
  - [Binding inventory](findings/2026-09-28-delayed-apply-reset-audit/INVENTORY.md) and [proposed follow-up work](findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md#proposed-todo-split-and-validation); missing resets are not proof of runtime failures
  - Proposed additions, not yet implemented: four single-modifier paths, then LST/RST Entry → Tap Cover per layout. Keep resets in the parent owning the pending apply; preserve overlays and the three-command limit
  - Preserve the author-confirmed RTP touch exclusion for trackball momentum. Defer the four scroll/menu-key Double Tap Cover paths until a design preserves output timing within three entries; leave the 5 ms Gyro Off → Turning Ramp Up 0 handoff unchanged unless it fails. These deferred choices are audit recommendations, not confirmed historical exclusions
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

- [x] Make Base gyro activation require LS/RS deflect, LS/RS touch, Select, and Start together, replacing the Start/Select gyro mode shifts
  - Verified in both layouts on 2026-09-29: active Base gyro group 576 uses mask `211109453778944` with `gyro_ratchet_button_requireany_or_all: "1"` (All six inputs)
  - The Start/Select gyro mode shifts are removed. Remaining mode shifts serve trackpad-touch navigation and menu Fn stick punctuation; they are unrelated and remain intentional
  - Implementation: [gyro mode-shift removal plan](plans/2026-09-27-neptune-gyro-shifts-navkeys.md). Runtime checks remain in [manual testing](manual-testing.md#modifier-layers); other gyro layers retain their own activation rules
- [ ] Handle cursor gyro layer (may be covered by [Cursor gyro above](#cursor-gyro))
- [ ] Clear all unnecessary layers on action set swap
- [ ] Add temp gyro to both right and left stick touch
