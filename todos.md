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
- [x] Temp cursor gyro
  - Implemented in both JSON layouts: delayed Mod 0/1 holds apply owner-specific cursor overlays in regular/Gyro variants (L1/R1 default, L2/R2 alternative). See the [implementation and inheritance review](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md), [current design](plans/2026-09-29-cursor-self-removal.md), and [pending Deck tests](manual-testing.md#temp-cursor-gyro)
  - Apply Gated Gyro's response/haptic properties after 300 ms: precision 750, haptic intensity 0, haptic bump 1, movement threshold 5. Cursor self-removal exposes normal 300/0/5/0; normal covers inherit gyro. Natural sensitivity remains inherited at 300, and existing activation gates are preserved
  - Base gyro follows the July reference (rotation 3853, precision 300, conversion style 4, speed deadzone 0). Gyro/LST/RST sources retain activation-only overrides; only cursor overlays supply the temporary response. See [exact settings and inheritance policy](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#reference-tuning-and-gyro-inheritance-follow-up) and [pending Deck checks](manual-testing.md#reference-gyro-and-right-stick-tuning)
  - Either stick-touch release completes that apply early, before LST/RST cleanup can reset its delay; see [the documented pattern](resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release)
  - Regular face/D-pad/click inputs, Start/Select, the opposite modifier, and both sticks deflected about 25% apply the normal cover until the next modifier hold. Whether trackpad-held face/D-pad mode shifts bypass that behavior remains unverified; see the check below. An override before 300 ms prevents cursor entry; normal covers replace touch inputs with guarded recovery and LST/RST removals, never cursor additions
  - Three entries per edge: interruptible owner guard, uninterruptible owner-plus-opposing-stick override, and repeating recovery. LS radius 4915 / RS 7209 account for different hysteresis to target ~25% engagement; earlier cleanup when the owner is absent is accepted. Physical/selector thresholds and chord priority remain Deck checks
  - Extended owner-family cleanup for cursor overlays while preserving outputs, opposite held owners, and Always On isolation. A follow-up adds the missing 350 ms reset to each 300 ms cursor-entry parent; both overlay types replace that input to stop the apply/reset pair
- [x] Replace cursor property restoration with repeating cursor self-removal
  - [Implementation plan](plans/2026-09-29-cursor-self-removal.md): split 48 ordinary modifier inputs per layout into output and repeating cover-add chords, both uninterruptible, plus existing interruptible repeating cleanup; keep three entries per input
  - Cursor cancellation removes only itself; normal Tap Covers inherit gyro and retain cleanup-only touch releases. Cursor layers inherit LS/RS touches. Preserve the owner's 300 ms apply / 350 ms reset, repeating opposite-modifier transitions, and separate repeating dual-stick paths
  - Fixed the two missing alternative Mod 2 repeats from held-input F1. RTP Double Tap now explicitly blocks face/D-pad/stick-click inputs above a modifier/cursor; existing timer boundaries stay intact. See the [per-window inheritance review](findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md)
  - Static tests and reference checks pass; [Deck validation](manual-testing.md#temp-cursor-gyro) remains pending for both same-selector chords, held-output handoff, interrupted timers, and RTP's brief output blocking
- [ ] Verify whether trackpad-held face/D-pad mode shifts activate under modifiers and bypass Temp Cursor Gyro overrides
  - Both layouts mark target groups 1039/1043 as `inactive modeshift`. Enabled Base trackpad-touch commands reference them, but those references alone do not establish whether Steam activates them under the modifier stack. The earlier review overstated this as a confirmed behavior gap
  - First reproduce the behavior on the Deck, before and after the 300 ms cursor apply. Only consider a fix if these groups actually take effect and bypass the normal Tap Cover; otherwise close this concern without changing bindings
  - If confirmed, consider modifier-specific mode-shift bindings that preserve existing key outputs and apply the owning normal cover. Trace inheritance through regular/Gyro owners, overlays, and Double Tap windows, including held inputs across transitions; preserve the three-command limit and Always On isolation
  - See the [corrected review note](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#stick-edges-and-inheritance) and [Deck checks](manual-testing.md#temp-cursor-gyro)

## Ramp up / triggers

- [x] Copy reference Base and ramp-up right-stick settings into both layouts
  - Base and Gyro Off Ramp Up already match. Turning Ramp Up 0 now uses sensitivity/vertical scale 150/80; Turning Ramp Up 1 uses 200/67. Bindings, modifier sensitivity 75, and local cleanup thresholds are preserved; verify feel in [manual testing](manual-testing.md#reference-gyro-and-right-stick-tuning)

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
  - LS recovery matches each RS owner/family scope, with Hold to Repeat and default Interruptable. With cursor overlays included, single modifiers remove four targets and Mod 2 removes its eleven-target branch; menu entries and scroll layers remove their own pairs. Persistent Gyro remains intact
  - Author-approved Transition Set depth: LS/RS touch and edge all remove the current Transition Set first, then both Menu Entry/Fn families, only when neither menu button is held. Invalid menu-overlay recovery remains the separate ownership review
  - Added explicit LS-edge empty blocks in all seven Double Tap windows to prevent inherited layer mutations while Always On is active; existing timers and self-first/add-last boundaries remain intact
  - Originally used Fn's LS outer region (radius 21000, inversion off). The cursor change moves the four single-modifier pairs to LS radius 4915 / RS 7209; the other ten selected LS layers retain 21000. WASD directions are unchanged; the inherited WASD modifier remains displaced while these layers own the edge. See [the accepted tradeoff](resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions)
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
- [x] Add delayed-apply reset to all four Temp Cursor Gyro entry parents per layout
  - Corrects the omission from the initial cursor implementation: the owning primary input removes only its Temp Cursor Gyro overlay every 350 ms with Hold to Repeat On and Interruptable Off, alongside the existing 300 ms apply and release exit
  - Both the cursor overlay and normal Tap Cover replace the complete primary input, stopping the reset after cursor entry or override. The reset never removes the normal cover or clears the owner stack. All seven Double Tap windows explicitly replace the primary controls; see [scope and isolation](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#delayed-apply-reset-follow-up) and [pending Deck checks](manual-testing.md#temp-cursor-gyro)
- [x] Split menu entry layer into separate Menu Left / Menu Right layers
  - Both layouts have distinct Menu Left: Entry Point and Menu Right: Entry Point layers and their own Fn paths
- [ ] Review extending the delayed-apply reset to additional tap-cover paths
  - After the cursor reset follow-up, coverage is 11 of 19 delayed-add paths per layout: four single-modifier cursor paths, two menu paths, four combined-cover paths, and Turning Ramp Up 0 → 1. The completed fixes above do not imply every delayed apply needs a reset
  - [Binding inventory](findings/2026-09-28-delayed-apply-reset-audit/INVENTORY.md) and [proposed follow-up work](findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md#proposed-todo-split-and-validation); missing resets are not proof of runtime failures
  - Remaining proposed additions: LST/RST Entry → Tap Cover per layout. The four single-modifier paths now target Temp Cursor Gyro and have their resets. Keep resets in the parent owning the pending apply; preserve overlays and the three-command limit
  - Preserve the author-confirmed RTP touch exclusion for trackball momentum. Defer the four scroll/menu-key Double Tap Cover paths until a design preserves output timing within three entries; these deferrals are audit recommendations, not confirmed historical exclusions
  - Keep the 5 ms Gyro Off → Turning Ramp Up 0 delay. It lets the apply fire on the already-held stick under the [held-input rule](resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes), and `tests/test_neptune_held_inputs.py` protects it
- [ ] Run the held-input real-layout checks and act on the results; see the [follow-up plan](plans/2026-09-29-held-input-rule-followups.md)
  - Done: F1 (the alternative R2 → Mod 2 repeats) and the [held-input regression tests](tests/test_neptune_held_inputs.py), including Base's covering repeats
  - Exported: [rule-test.vdf](findings/2026-09-29-held-input-layer-transitions/rule-test.vdf) and both Neptune VDFs using `convert_vdf.mjs`; static export checks pass
  - Pending: the real-layout checks in [manual testing](manual-testing.md#held-inputs-across-layer-changes). The key/mouse output scope (F3.1/F3.2) and the staggered Gyro toggle (F3.3) wait on those results
  - Not scheduled: rule 3 (a removal firing the exposed layer command) stays unverified. The layouts back it with repeats; run the optional T4 in `rule-test.vdf` before ever removing a Base repeat
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
  - The Start/Select gyro mode shifts are removed. Remaining mode-shift definitions cover trackpad-touch navigation and menu Fn stick punctuation and were preserved by that refactor. Trackpad mode-shift activation under modifiers remains the separate verification item above
  - Implementation: [gyro mode-shift removal plan](plans/2026-09-27-neptune-gyro-shifts-navkeys.md). Runtime checks remain in [manual testing](manual-testing.md#modifier-layers); other gyro layers retain their own activation rules
- [ ] Handle cursor gyro layer (may be covered by [Cursor gyro above](#cursor-gyro))
- [ ] Clear all unnecessary layers on action set swap
- [ ] Add temp gyro to both right and left stick touch
