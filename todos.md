# Todo:

Manual Deck validation is tracked in [the separate testing checklist](manual-testing.md).

Terminology: use **stateful layer** for a persistent action layer and refer to
its supporting layers separately. This replaces the earlier “stateful set”
wording. These features use layers throughout; action-set switching is excluded
because the author reports buggy behavior with Steam action sets.

## Next: allowed activators and cleanup (90.6)

Implemented in 90.6 ([chorded delays](plans/2026-09-30-steering-chorded-delays.md),
[banned activators and dead groups](plans/2026-09-30-banned-activators-and-dead-groups.md)).
The audit now fails on Long/Double Press. Completion awaits the Deck checks.

- [ ] Validate steering chorded delays on Deck (gates C1–C5): fallback warning/exit, entry carry, window clock from layer add, consume + 300 ms reset, reset never strips the cover
- [ ] Validate the prune and RTP chord on Deck (gates D1–D5): fresh load, RTP tap/hold scroll, RTP edges, mode shifts, temporary gyro
- [ ] Validate the second-press cover resets (gates R1–R3), including that desktop drops only the 4th entry ([record](findings/2026-09-30-second-press-cover-reset/README.md))
- [ ] Validate Transition Set 0's new stick-touch release on Deck (gate T1) ([record](findings/2026-09-30-touch-release-rule/README.md))
- [ ] Validate the derived Double Tap window blocks on Deck (gate B1) ([record](findings/2026-09-30-derived-window-blocks/README.md))
- [ ] Validate the Double Tap window pads on Deck (gate P1) ([record](findings/2026-09-30-double-tap-pad-blocks/README.md))
- [ ] Deck check: do stick inputs (edge, click, touch, directions) inherit through the middle of the stack, or only from the top layer and Base? Put three layers up where only the middle one binds LS click. A 2022 community report says sticks skip the middle ([JSON Structure](resources/Steam%20Input%20JSON%20Structure.md#how-binding-overlay-works)). If true, the inheritance tools must model it
- [ ] Build the intended-flow inheritance checker ([plan](plans/2026-09-30-cleanup-generator.md#intended-flow-inheritance-audit-author-approved)) instead of resuming exhaustive stack/timer proofs
  - Follow intended explicit layer-addition paths from Base; retain stack order, input/chord conditions and removals within each transition
  - For each relevant button, report the nearest inherited binding and original activators on each path
  - When paths expose multiple distinct non-Base bindings, recommend explicit clear/block; compare actual bindings and activators, not just owner names. Do not assume replacement is safe
  - Handle above-layer interactions separately for lightweight covers; do not make global above-layer reachability a prerequisite
  - Benchmark the checker on both variants and audit cleanup functions/blocks against the project docs. Scope is intended flows, not every runtime interleaving
- [x] Deprecate the exhaustive stack/timed-proof audit as the default workflow; preserve code, tests and a compact research checkpoint for reuse ([archive](findings/2026-09-30-stack-search/ARCHIVE.md))
- [ ] Decide RTP Double Tap's LB, RB, menu buttons and trigger edges: their inherited values change with the stack, so §8 says clear ([finding](findings/2026-09-30-stack-search/README.md#what-we-learned))
- [ ] Periodically recheck whether Steam's desktop configuration still drops entries after the third; consider filing a Valve bug report. If it's fixed, revisit the [command entry budget](resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget)

## Done

- [x] Make L1&R1: Tap Cover interruptable (in R1!L1, L1!R1, R2!L2, and L2!R2 layers)

## Gamepad layer

- [ ] Move gamepad layer → Menu Right + RS click / Menu Left + LS click
  - Note: requires same-side input (claw style); not frequent, so acceptable tradeoff

## Steering

[Sixteen-layer candidates](findings/2026-09-30-steering-lean/README.md) are generated for both variants: **16 additions, 71 total, no new Always On actions**. Saves nine against the prior lean build. Installed in both working layouts as release 90.5; the original 36-layer candidate remains unchanged. Completion awaits [native acceptance](findings/2026-09-30-steering-lean/ACCEPTANCE.md).

- [ ] Validate protected menu entry and disposable WASD entry on Deck
  - Right Menu + LS click, release menu to commit; either-stick deflection blocks automatic Fn during entry; deliberate clicks remain
  - Guard ends at LS center or driving press; initial carried W has no timeout
- [ ] Validate W/S ownership and held-opposite takeover
  - Right R1/R2 owns W, left L1/L2 owns S; no built-in bank
  - Dominant release clears old modifiers/gestures; a held opposite takes over. No Rearm layer
- [ ] Validate consolidated normal modifiers and scrolling
  - Mod 0/1 own Down/Up gesture state; actual center qualifies tap; sideways removes silently; reversal before 250 ms selects the other bank consumed
  - Shared normal Tap Cover, two Double Tap windows, one shared Double Tap Cover
  - Tap Cover (90.6): up/down do nothing, center removes Mod 0, Mod 1, then the cover; verify repeat reversal cancels the delayed opposite tick
- [ ] Validate simple Modifier 2 scrolling
  - Two ordered Modifier 2 variants; Up/Down wheel immediately and repeat while held; no Mod 2 gesture helpers
  - Uncovered opposite release clears all layers to Base; 200 ms hold/action coverage uses existing opposite-side single Tap Covers with the existing 250 ms reset
  - Covers preserve W/S and normal covered release behavior; opposite release restores consumed normal mapping without dropping the owner
  - Existing combined Tap Cover remains unchanged to preserve W/S inputs; face outputs remain independent
- [ ] Validate fallback warning/exit, held outputs and recovery
  - W warns from 1 second, exits at 2.5 seconds; W release/driver acquisition cancels; next hold starts fresh
  - Native timers, feedback, changed-held-output suppression and foreign Always On isolation remain acceptance gates
- [Implementation plan](plans/2026-09-29-steering-implementation-plan.md) · [Behavior matrix](plans/2026-09-29-steering-entry-brainstorm.md) · [Visual overview](plans/steering-overview.html)

## Menu stateful layer

- [ ] Add menu stateful layer
  - Enter: Menu Left + Right
  - Exit: both sticks deflected, or one stick deflected + any face button
  - Inputs: D-pad → arrow keys; face buttons → Enter / Tab / Escape / Backspace
  - On entry: remove gyro stateful layer

## Cursor gyro

- [ ] Cursor gyro (stateful)
  - Activate via Left Menu + RS click
  - Only remove when both left and right sticks are deflected
- [x] Temp cursor gyro
  - 90.4: high haptic pulse on the initial 300 ms hold entry only, in all regular/Gyro owners. Touch-release entry stays silent and ongoing gyro vibration remains off
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

- [ ] L1 + R1 clears all stateful layers
  - Steering candidate: uncovered opposite release in both ordered Mod 2 variants clears every layer to Base (Default bumpers / Alternative triggers), including Gyro; native acceptance pending
  - The latest steering request explicitly clears all layers. The older Gamepad-preservation exception remains a separate policy for other global-exit routes

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
