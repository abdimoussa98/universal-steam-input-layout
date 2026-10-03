# Todo:

The Deck checklist was retired on 2026-10-03, and this list was re-sorted the
same day. Press-by-press checks are scenario tests (`python3 -m tests.scenario`).
What is left for the Deck is in [the next section](#on-the-deck-the-unverified-assumptions).
A "validate on Deck" item whose checks became tests is closed below, with where
each check went ([migration record](findings/2026-10-03-deck-check-sorting/README.md)).
None of them was run on the Deck: a layer whose tests pass but rest on an
unverified assumption is done, and listed (author, 2026-10-02).

Reviewed 2026-10-01 against release 90.9 (69 layers per layout). Every version
has to pass the build audit, `python3 audit_build.py`
([definition of done §10](resources/Layer%20Definition%20of%20Done.md#10-ship-it)).

Terminology: use **stateful layer** for a persistent action layer and refer to
its supporting layers separately. This replaces the earlier “stateful set”
wording. These features use layers throughout; action-set switching is excluded
because the author reports buggy behavior with Steam action sets.

## On the Deck: the unverified assumptions

The Deck is used to settle an assumption, once, and again after a Steam update
that could change it. Each has one procedure in its row of
[Steam Behaviour Assumptions](resources/Steam%20Behaviour%20Assumptions.md).
What rests on each one, [as of 90.13](findings/2026-10-03-deck-check-sorting/unverified-assumptions.txt);
`python3 -m tests.scenario` prints the current list.

The layout relies on these twelve. If one is false, something is broken:

- [ ] A8: A stick edge's Release fires in a layer that was added while the stick was already out (unverified; rests on it: 9 scenarios; R111, R137)
- [ ] A10: A key or mouse output fires on an input that is already held when its layer is added (reported by the author; rests on it: 10 scenarios; R138)
- [ ] A11: A key or mouse output fires when a removal exposes it under an input that is held (unverified; rests on it: 7 scenarios)
- [ ] A13: Any `remove_layer` can reset a running start delay; an `add_layer` doesn't (reported by the author; rests on it: R123, R126, R141)
- [ ] A14: A delay starts again when a removal exposes it under a button that is held (unverified; rests on it: 2 scenarios)
- [ ] A16: A delay's clock starts when its layer is added, not at the physical press (unverified; rests on it: 8 scenarios)
- [ ] A26: Stick inputs inherit through the middle of the stack like any other input (unverified; rests on it: R140)
- [ ] A27: An active chord suppresses an interruptible Regular Press on the same input. How two chords on one input are ordered is not known (reported; rests on it: 3 scenarios; R133, R135)
- [ ] A33: Steam loads an exported VDF as written: the same layers, groups and bindings as the JSON it was made from (reported; rests on it: R151)
- [ ] A34: A group marked `inactive modeshift` takes effect only while a `mode_shift` binding that targets it is held (unverified)
- [ ] A36: A chord is decided when its binding starts answering a held input: at the press, or when its layer lands or is exposed. Pressing the chord button afterwards doesn't start it (unverified)
- [ ] A38: A stick group that doesn't state `edge_binding_invert` has a normal edge. It doesn't take the inverted setting of the group it replaces in a lower layer (unverified; rests on it: 2 scenarios; R111)

The layout is built to work either way under these seven. Settling one takes a
branch out of the tests:

- [ ] A9: Removing a layer fires the exposed layer command on an input that is held (held-input rule 3) (unverified; rests on it: 7 scenarios; R114)
- [ ] A18: A `remove_layer` call makes Steam re-evaluate held inputs (unverified)
- [ ] A24: Adding or removing another layer while a layer with an Always On action is active caused crashes (reported by the author; rests on it: R140, R146, R147, R148, R149)
- [ ] A31: A repeating activator keeps its schedule when another layer is removed (unverified; rests on it: R114)
- [ ] A32: When two separate activators on one input are due at the same moment, their order is not fixed. Inside one activator the array still runs bottom to top (unverified; rests on it: 1 scenario)
- [ ] A35: Hold to Repeat with no stated rate repeats at one fixed default interval (unverified; rests on it: 1 scenario)
- [ ] A37: When the layer that answers a held input changes and the new binding sends the same key, the key stays down with no release in between (unverified; rests on it: 2 scenarios)

## Rules without a check

- [ ] Ten rules have no check and eighteen have one that covers only part: `python3 -m steam_layout.rules` lists them. Each is a to-do for a test
- [ ] Decide R116 for four layers, so it can be checked. The rule lets only a cover-type layer inherit a stick-touch Release. `Gyro Off Ramp Up` and `Steering | LS: Fallback Hold` bind neither stick's touch Release, and `LST: Double Tap` and `RST: Double Tap` bind only the other stick's. Are they exceptions, or findings?

## Next: allowed activators and cleanup (90.6)

Implemented in 90.6 ([chorded delays](plans/2026-09-30-steering-chorded-delays.md),
[banned activators and dead groups](plans/2026-09-30-banned-activators-and-dead-groups.md)).
The audit now fails on Long/Double Press. The Deck gates below were re-sorted on 2026-10-03; none was run.

- [x] Validate steering chorded delays on Deck (gates C1–C5): fallback warning/exit, entry carry, window clock from layer add, consume + 300 ms reset, reset never strips the cover — **closed 2026-10-03 without a Deck run**
  - Where the gates went: C4 and C5 are one scenario test ([90.6 C4/C5/S7](tests/test_scenarios_90_6_to_90_9.py)) and C2 is 90.11 F7's. C1 and C3 are obsolete, replaced by 90.11 F1 to F9 and by 90.10 D5. They rest on A8 and A16
  - 90.11 replaces the fallback gate (C1) with [F1 to F9](tests/test_scenarios_90_11.py)
  - The [transition build](#stateful-layer-transitions) replaces the window clock (C3) with an Always On action. The consume hold stays on the direction but is chorded on Any driver instead of stick deflection. Those gates then need rewriting; the fallback warning/exit gate stays and gains S
- [x] Validate the prune and RTP chord on Deck (gates D1–D5): fresh load, RTP tap/hold scroll, RTP edges, mode shifts, temporary gyro — **closed 2026-10-03 without a Deck run**
  - Where the gates went: static tests (`test_layout_hygiene.test_no_unreferenced_groups_or_plain_inactive_slots`, `test_layout_hygiene.test_rtp_scroll_repeat_is_a_touch_chorded_delay`, `test_fixes.test_working_layouts_are_a_fixed_point`). That the file loads as written is A33
- [x] Validate the second-press cover resets (gates R1–R3), including that desktop drops only the 4th entry ([record](findings/2026-09-30-second-press-cover-reset/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gates went: R1 is a scenario test ([90.6 R1](tests/test_scenarios_90_6_to_90_9.py), rests on A10). R2 is A12 and R3 is A21, both verified by the author
- [x] Validate Transition Set 0's new stick-touch release on Deck (gate T1) ([record](findings/2026-09-30-touch-release-rule/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gate went: obsolete. The transitions were rebuilt in 90.10 (scenario 90.10 T4), and what the editor shows for the merged chord is A30, verified
  - Goes away with the [transition build](#stateful-layer-transitions), which drops the transition's chord-guarded stick-touch recovery. Only worth running if that build is delayed
- [x] Validate the derived Double Tap window blocks on Deck (gate B1) ([record](findings/2026-09-30-derived-window-blocks/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gate went: a static test (`test_double_tap_windows.test_rtp_double_tap_keeps_its_touch_selection_and_clears_the_fn_back_buttons`). Its trigger part is scenario 90.10 T10, which rests on A37
- [x] Validate the Double Tap window pads on Deck (gate P1) ([record](findings/2026-09-30-double-tap-pad-blocks/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gate went: two static tests (`test_double_tap_windows.test_left_pad_swipes_send_keys_without_the_layer_api`, `test_double_tap_windows.test_right_pad_stays_the_mouse_with_click_and_touch_cleared`). The swipe feel is a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes)
- [ ] Deck check: do stick inputs (edge, click, touch, directions) inherit through the middle of the stack, or only from the top layer and Base? Put three layers up where only the middle one binds LS click. A 2022 community report says sticks skip the middle ([JSON Structure](resources/Steam%20Input%20JSON%20Structure.md#how-binding-overlay-works)). If true, the inheritance tools must model it
  - Assumption A26, listed [above](#on-the-deck-the-unverified-assumptions)
  - This is gate 1 of the [transition build](#stateful-layer-transitions): the stick guards and Fn layers inherit the stick clicks from the Entry Point. The author expects it to hold and the plan assumes it does ([test steps](resources/Stateful%20Layer%20Transitions.md#steerings-left-stick-and-the-deck-gates))
- [x] Build the intended-flow inheritance checker ([implementation plan](plans/2026-10-01-intended-flow-inheritance.md)) instead of resuming exhaustive stack/timer proofs ([record](findings/2026-10-01-intended-flow-checker/README.md))
  - Follow intended explicit layer-addition paths from Base; retain stack order, input/chord conditions and removals within each transition
  - For each relevant button, report the nearest inherited binding and original activators on each path
  - When paths expose multiple distinct non-Base bindings, recommend explicit clear/block; compare actual bindings and activators, not just owner names. Do not assume replacement is safe
    - Corrected 2026-10-01 (author): this misread the rule. Clear-or-override only applies under an Always On layer with an inherited layer command ([§8](resources/Layer%20Definition%20of%20Done.md#how-to-check-it)). The Flow audit now lists these as "varies" and doesn't fail on them
  - Handle above-layer interactions separately for lightweight covers; do not make global above-layer reachability a prerequisite
  - Benchmark the checker on both variants and audit cleanup functions/blocks against the project docs. Scope is intended flows, not every runtime interleaving
- [x] `RTP: Entry Point` over `RTP: Double Tap`: resolved by the author's mode rule; a source-mode change blocks inheritance, so the window's dpad pad never inherits Base's touch ([decisions](findings/2026-10-01-intended-flow-checker/README.md#author-decisions-2026-10-01))
- [x] Opposite-button overlays: removed in 90.9. The menu chords type Backspace / Enter directly (fix `menu_combo_keys`); the stray Escape / Tab when the first button is lifted first is accepted
  - The [transition build](#stateful-layer-transitions) takes the key back out of the Entry Points: their chord only adds Fn, and Fn types Backspace / Enter, as before the split (author, 2026-10-01)
- [x] Inheritance across a source-mode change: author rule, it blocks; documented in [Layer Definition of Done §8](resources/Layer%20Definition%20of%20Done.md#a-source-mode-change-blocks-inheritance)
- [ ] Use the Flow audit's per-layer reports to review cleanup lists and blocks (plan [§6](plans/2026-10-01-intended-flow-inheritance.md#6-follow-up-after-the-first-checker-is-useful))
  - Blocks are covered by the Window audit, which checks the one blocking rule: under an Always On layer, an inherited layer command must be cleared or overridden. Cleanup lists are not checked by any audit; see the Cleanup audit under [Layer cleanup](#layer-cleanup)
  - The per-layer report is now `audit_layer.py` (2026-10-01)
- [x] Name the audits and add one gate for every version: `audit_build.py` runs the Budget, Window and Flow audits on both layouts. In [definition of done §10](resources/Layer%20Definition%20of%20Done.md#10-ship-it) and the layout-apply skill (2026-10-01)
- [x] Deprecate the exhaustive stack/timed-proof audit as the default workflow; preserve code, tests and a compact research checkpoint for reuse, moved to [archived/](archived/README.md) on 2026-10-02 ([archive](findings/2026-09-30-stack-search/ARCHIVE.md))
- [x] Deprecate the depth-limited stack search and the family walk; every audit builds its stacks from backward chains (2026-10-01, [record](findings/2026-10-01-backward-chain-stacks/README.md#deprecated))
  - `flow_config.json` no longer declares families: a new layer needs no entry. Code and tests of both older searches are kept in [archived/](archived/README.md) since 2026-10-02, with comparisons frozen at 90.9
- [ ] Decide RTP Double Tap's LB and RB: their inherited values change with the stack, so §8 says clear ([finding](findings/2026-09-30-stack-search/README.md#what-we-learned))
  - At 90.9 the menu buttons and both trigger stages are cleared in that window. LB and RB are replaced with the scroll wheel, like the other windows. What's left to decide is whether that replacement stays or becomes a clear
- [ ] Periodically recheck whether Steam's desktop configuration still drops entries after the third; consider filing a Valve bug report (assumption A21). If it's fixed, revisit the [command entry budget](resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget)

## Done

- [x] Make L1&R1: Tap Cover interruptable (in R1!L1, L1!R1, R2!L2, and L2!R2 layers)

## Stateful layer transitions

Agreed design, built in 90.10. Its 25 Deck checks became 19 scenario tests, 5 assumption procedures (A8, A14, A15, A26) and 1 obsolete check on 2026-10-03; none was run. The scenarios rest on A8, A9, A10, A11, A14, A16, A27 and A37 ([build record](findings/2026-10-01-stateful-transitions/README.md) · [scenario tests](tests/test_scenarios_90_10.py) · [implementation plan](plans/2026-10-01-stateful-transitions-implementation.md)): [Stateful Layer Transitions](resources/Stateful%20Layer%20Transitions.md) · [brainstorm record](plans/2026-10-01-stateful-layer-transitions.md) · [definition of done §11](resources/Layer%20Definition%20of%20Done.md#11-stateful-layers)

- [x] Build the transition structure in both layouts (90.10; [implementation plan](plans/2026-10-01-stateful-transitions-implementation.md); assumes both Deck gates pass: A26 and A8)
  - Entry Points: both sticks as D-pads, stick-click Release binds, Fn layers inherit the clicks, Fn delay 200 ms / reset 250 ms. The other menu button only adds Fn; Backspace / Enter are typed by Fn alone
  - Two stick guards split by stick and one shared menu Tap Cover, replacing the four protected `Steering | Menu …` layers (one new layer, 70 in total). A guard's menu release still opens the Double Tap window; the hold or a thumb lift applies the Tap Cover
  - Transition 1 (Select release clears for now, Start release enters Steering) and Transition 2 (clear, keeping Gyro); everything layer-adding blocked with empty bindings
  - Steering's own Entry Points; W/S driver layers send Tab / Escape on Start / Select; the plain menu press no longer drops Steering
  - Add the 2.5 s hold exit for S
- [x] Add `tests/test_stateful_transitions.py` (90.10). Extend it with every new stateful layer until all four gestures are taken
- [x] Rework Steering's left-stick centre detection (90.10): the inverted edge on a D-pad stick isn't reliable (seven layer groups; [list](plans/2026-10-01-stateful-layer-transitions.md#9-recentre-detection-decision-19))
  - Built as the author directed (2026-10-01): the stick-guard recipe. A normal, generous outer edge holds Modifier 0 / 1 and its Release cleans up, so rolling to A / D keeps the modifier. The entering direction carries the 250 ms hold that adds the Tap Cover (Any-driver chord, like the L1 / R1 modifiers); left and right add the Tap Cover with A / D; the opposite direction only cleans up; mapped-button cleanups are guarded by two All-chords, left-stick deflection plus each driver. The Tap Cover is never added by a driver press ([details](resources/Stateful%20Layer%20Transitions.md#steerings-left-stick-and-the-deck-gates))
  - Depends on the edge-Release Deck check below (A8)
  - Rebuild the two `Steering | LS …: Double Tap` windows as Always On windows; their 150 ms timeout rides on an inverted edge today (an oversight in the first build). Seven Always On windows become nine, under [definition of done §9](resources/Layer%20Definition%20of%20Done.md#9-always-on-layers). They bind the drivers themselves (W and S, Release removes the window first, then the family) and inherit nothing that changes layers
- [x] Add an audit check for the new rule in [definition of done §3](resources/Layer%20Definition%20of%20Done.md#3-activators): no layer command on an inverted edge of a D-pad-mode stick. Added in 90.10 as `inverted_edges` in the Budget audit
- [ ] Deck check for the stick guards: an edge Release fires in a guard that was added while the stick was already out. The mid-stack stick inheritance check above is a gate for the guards too ([both explained](resources/Stateful%20Layer%20Transitions.md#steerings-left-stick-and-the-deck-gates))
  - Assumptions A8 and A26, listed [above](#on-the-deck-the-unverified-assumptions)
- [ ] Deck check: does a `remove_layer` call re-evaluate held inputs, the way it restarts delays? (author's hypothesis, with the [chord latch](resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30))
  - Assumption A18. The layout works either way

## Gamepad layer

- [ ] Move gamepad layer → Menu Right + RS click / Menu Left + LS click
  - Note: requires same-side input (claw style); not frequent, so acceptable tradeoff
  - Enters through Transition 0, which is created with this layer ([structure](resources/Stateful%20Layer%20Transitions.md#3-transition-layers))

## Steering

[Sixteen-layer candidates](findings/2026-09-30-steering-lean/README.md) are generated for both variants: **16 additions, 71 total at the time, no new Always On actions**. Saves nine against the prior lean build. Installed in both working layouts as release 90.5; the original 36-layer candidate remains unchanged. Completion awaits [native acceptance](findings/2026-09-30-steering-lean/ACCEPTANCE.md). The layouts have 69 layers since 90.9 removed the two menu overlays.

**The [transition build](#stateful-layer-transitions) changes several behaviours listed below** (author decisions, 2026-10-01). Validating them on the Deck before that build tests behaviour that is about to change:
- Protected menu entry is replaced by the stick guards and one menu Tap Cover, and the commit is stick click released first, then the menu button.
- A plain Start or Select press no longer leaves Steering, so Steering can sit under the two menu Double Tap windows. With a driver held they send Tab and Escape.
- A driver press no longer adds `Steering | LS: Tap Cover`; a stick already held enters the modifier at once.
- Sideways keeps Modifier 0 / 1; the stick's edge Release ends it. The opposite direction only cleans up.
- The two Double Tap windows become Always On windows, so "no new Always On actions" no longer holds.
- The hold exit also applies to S. `Steering | LS: Entry Point` is renamed `Steering | LS: Entry Guard`.

Since 2026-10-03 Steering's press sequences are scenario tests (90.7 S, 90.10 D, 90.11 F and 90.13 N). The four "validate" items below predate them and haven't been matched against the scenarios one by one, so they stay open.

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
- [x] Move the fallback exit timer into `Steering | LS: Fallback Hold` (90.11, author 2026-10-02): the timer ran on while the stick was on A or D. `Steering`'s stick up and down only add the layer; the layer types W or S, exits at 1.5 s and leaves on Release; its edge pulses from the start and carries the reset ([record](findings/2026-10-02-steering-fallback-hold/README.md); 71 layers)
  - Nothing is added over the Fallback Hold or the Entry Guard (author): Start and Select type Tab and Escape there; Steering's Entry Points type W and S on stick up and down instead of inheriting the add
- [x] Audit check for a hidden exit (built 2026-10-02 as the Cleanup audit's seventh check, rule R136): a layer that can be added over another binds an input whose Release is that layer's exit, without carrying it (the 90.11 menu-tap case). Prototype and 90.12 results in [findings/2026-10-02-hidden-exit](findings/2026-10-02-hidden-exit/README.md); goes in the cleanup audit as a seventh check
  - Touchpad pairs are an exception for now (author, 2026-10-02; next item). On 90.13, 2 pairs remain, both passing: the menu Tap Cover over a stick guard (its menu Release still removes the guard). The 4 turn-assist pairs over the driver layers were fixed in 90.13 by blocking the right-stick edge in `Steering` (author). (A first run also listed 8 modifier pairs; that was a prototype bug, corrected)
  - Decided (author, 2026-10-02): a cleanup function removing the layer later is not a pass. The prototype uses the keeper rule: 0 findings outside the touchpad exception
- [ ] **Touchpad exception to the hidden-exit rule: address it** (author, 2026-10-02). For now every pair where either layer is a touchpad layer (`Tab`, `Escape`, `Backspace`, `Enter`, `RTP: Entry Point`, `RTP: Circular Scroll`, `RTP: Double Tap`) or the covered exit is a trackpad input is set aside, not a finding. Under the keeper rule (a pair counts only if it covers an exit on what keeps the lower layer alive; a later cleanup doesn't count), that is 68 pairs in 90.13: 40 windows over pad layers and 28 `RTP: Double Tap` over button layers. 26 more (pad layers over the menu hold) are information: no stuck layer, but they block the right-stick click transition gesture ([list](findings/2026-10-02-hidden-exit/README.md#touchpad-exception))
  - Worst first: the 12 pairs where the lower layer has no cleanup function. `RTP: Double Tap` over `Menu Left: Escape`, `Menu Right: Tab`, the four Double Tap Covers, `L1&R1: Tap Cover` and `Menu Buttons: Tap Cover`; the L1, R1, Menu Left and Menu Right windows over `RTP: Tap Cover`. Example: double-tap and hold Select, tap the right pad, let go of Select inside the window: `Menu Left: Escape` stays on
  - Windows can't carry the exit without breaking their isolation, so the choice is a cleanup function on the lower layer or stopping the window from landing
  - Then the 25 mode blocks: the left-pad and RTP layers keep the right stick in mouse mode, which blocks the menu Entry Points' right-stick click Release and the right stick guard's edge Release
  - [ ] Confirm the five choices made while building, first the reset on the edge instead of a 4th entry on up and down ([list](findings/2026-10-02-steering-fallback-hold/README.md#choices-made-while-building))
- [x] Validate the fallback exit, held outputs and recovery ([F1 to F11](tests/test_scenarios_90_11.py)) — **closed 2026-10-03 without a Deck run**
  - Where the checks went: ten are scenario tests, and F4 is A16's procedure. They rest on A8, A9, A10 and A16
  - W or S pulses from the start and exits at 1.5 seconds; rolling to A or D, a release or a driver press cancels; the next hold starts fresh
  - Native timers, feedback, changed-held-output suppression and foreign Always On isolation remain acceptance gates
- [Implementation plan](plans/2026-09-29-steering-implementation-plan.md) · [Behavior matrix](plans/2026-09-29-steering-entry-brainstorm.md) · [Visual overview](plans/steering-overview.html)

## Menu stateful layer

- [ ] Add menu stateful layer
  - Exception (author, 2026-10-01): it will not go through the [stateful transition structure](resources/Stateful%20Layer%20Transitions.md#exceptions). The idea is parked here
  - Enter: Menu Left + Right
  - Exit: both sticks deflected, or one stick deflected + any face button
  - Inputs: D-pad → arrow keys; face buttons → Enter / Tab / Escape / Backspace
  - On entry: remove gyro stateful layer

## Cursor gyro

- [ ] Deck check: does `L1: Temp Cursor Gyro` / `R1: Temp Cursor Gyro` pick up Base's inverted left-stick edge?
  - Their left-stick group doesn't state `edge_binding_invert`, their edge removes the layer, and Base's left-stick edge is inverted. The inverted-edge audit check only counts a layer whose own group says inverted (author, 2026-10-01; [plan](plans/2026-10-01-stateful-transitions-implementation.md#step-6-steerings-left-stick)), so these two pass it either way
  - Assumption A38 since 2026-10-03. The two cursor scenarios that push both sticks (TC8, TC9) rest on it
  - If they do pick it up, they break the rule in [Definition of Done §3](resources/Layer%20Definition%20of%20Done.md#3-activators) and need an explicit setting
- [ ] Cursor gyro (stateful)
  - Activate via Left Menu + RS click, through Transition 1 on the Select release ([structure](resources/Stateful%20Layer%20Transitions.md))
  - Three exits (author, 2026-10-01): any menu button plus any stick click, the Modifier 2 clear, and its own clear, built the same way Temp Cursor Gyro clears (both sticks deflected). The third skips the transition and is a recorded exception
- [x] Temp cursor gyro
  - 90.4: high haptic pulse on the initial 300 ms hold entry only, in all regular/Gyro owners. Touch-release entry stays silent and ongoing gyro vibration remains off
  - Implemented in both JSON layouts: delayed Mod 0/1 holds apply owner-specific cursor overlays in regular/Gyro variants (L1/R1 default, L2/R2 alternative). See the [implementation and inheritance review](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md), [current design](plans/2026-09-29-cursor-self-removal.md), and the [scenario tests](tests/test_scenarios_cursor.py)
  - Apply Gated Gyro's response/haptic properties after 300 ms: precision 750, haptic intensity 0, haptic bump 1, movement threshold 5. Cursor self-removal exposes normal 300/0/5/0; normal covers inherit gyro. Natural sensitivity remains inherited at 300, and existing activation gates are preserved
  - Base gyro follows the July reference (rotation 3853, precision 300, conversion style 4, speed deadzone 0). Gyro/LST/RST sources retain activation-only overrides; only cursor overlays supply the temporary response. See [exact settings and inheritance policy](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#reference-tuning-and-gyro-inheritance-follow-up) and the [tuning notes](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (RG1 to RG3)
  - Either stick-touch release completes that apply early, before LST/RST cleanup can reset its delay; see [the documented pattern](resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release)
  - Regular face/D-pad/click inputs, Start/Select, the opposite modifier, and both sticks deflected about 25% apply the normal cover until the next modifier hold. Whether trackpad-held face/D-pad mode shifts bypass that behavior remains unverified; see the check below. An override before 300 ms prevents cursor entry; normal covers replace touch inputs with guarded recovery and LST/RST removals, never cursor additions
  - Three entries per edge: interruptible owner guard, uninterruptible owner-plus-opposing-stick override, and repeating recovery. LS radius 4915 / RS 7209 account for different hysteresis to target ~25% engagement; earlier cleanup when the owner is absent is accepted. Physical/selector thresholds and chord priority remain Deck checks: the travel is a tuning note (TC2), and the chord priority is A27
  - Extended owner-family cleanup for cursor overlays while preserving outputs, opposite held owners, and Always On isolation. A follow-up adds the missing 350 ms reset to each 300 ms cursor-entry parent; both overlay types replace that input to stop the apply/reset pair
- [x] Replace cursor property restoration with repeating cursor self-removal
  - [Implementation plan](plans/2026-09-29-cursor-self-removal.md): split 48 ordinary modifier inputs per layout into output and repeating cover-add chords, both uninterruptible, plus existing interruptible repeating cleanup; keep three entries per input
  - Cursor cancellation removes only itself; normal Tap Covers inherit gyro and retain cleanup-only touch releases. Cursor layers inherit LS/RS touches. Preserve the owner's 300 ms apply / 350 ms reset, repeating opposite-modifier transitions, and separate repeating dual-stick paths
  - Fixed the two missing alternative Mod 2 repeats from held-input F1. RTP Double Tap now explicitly blocks face/D-pad/stick-click inputs above a modifier/cursor; existing timer boundaries stay intact. See the [per-window inheritance review](findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md)
  - Static tests and reference checks pass. The press sequences are [scenario tests](tests/test_scenarios_cursor.py) since 2026-10-03, resting on A9, A11, A32, A35 and A38. Not run on the Deck: both same-selector chords (A27), held-output handoff (A10, A11), interrupted timers (A13) and RTP's brief output blocking
- [ ] Verify whether trackpad-held face/D-pad mode shifts activate under modifiers and bypass Temp Cursor Gyro overrides (assumption A34)
  - Both layouts mark target groups 1039/1043 as `inactive modeshift`. Enabled Base trackpad-touch commands reference them, but those references alone do not establish whether Steam activates them under the modifier stack. The earlier review overstated this as a confirmed behavior gap
  - First reproduce the behavior on the Deck, before and after the 300 ms cursor apply. Only consider a fix if these groups actually take effect and bypass the normal Tap Cover; otherwise close this concern without changing bindings
  - If confirmed, consider modifier-specific mode-shift bindings that preserve existing key outputs and apply the owning normal cover. Trace inheritance through regular/Gyro owners, overlays, and Double Tap windows, including held inputs across transitions; preserve the three-command limit and Always On isolation
  - See the [corrected review note](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#stick-edges-and-inheritance) and A34's procedure

## Ramp up / triggers

- [x] Copy reference Base and ramp-up right-stick settings into both layouts
  - Base and Gyro Off Ramp Up already match. Turning Ramp Up 0 now uses sensitivity/vertical scale 150/80; Turning Ramp Up 1 uses 200/67. Bindings, modifier sensitivity 75, and local cleanup thresholds are preserved; the feel is a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (RG1, RG3)

- [x] Remove dedicated trigger layers and the old layer-based chorded ramp-up arrangement
  - Confirmed in both layouts: dedicated trigger layers are gone. Base still intentionally uses grouped Any chords to select or suppress ramp-up; this does not mean removing every ramp-up chord
- [x] Move ramp up gyro on / off entry selection to Base
  - Base RS edge adds Gyro Off Ramp Up normally, or Turning Ramp Up 0 directly while a firing control is held. Modifier-held input suppresses entry. Firing controls are L2/R2 in default and L1/R1 in alternative
- [x] Have firing controls remove Gyro Off Ramp Up during ramp-up
  - Gyro Off Ramp Up owns repeating, uninterruptible removal on default trigger pulls / alternative bumpers. Turning Ramp Up 0/1 leave those firing inputs unoverridden, inheriting the removal while Gyro Off Ramp Up remains below them
  - Verified from both JSON layouts on 2026-09-28; this is configuration verification, not a fresh Deck runtime test
- [x] Match default trigger configuration to the July reference (clarified scope of the hip-fire TODO; alternative excluded)
  - Both Base trigger groups now match the reference's bindings and settings, retaining their own group IDs. Removed only the explicit `adaptive_threshold: "0"` settings; no Soft Press/hip-fire activator was added, since the reference triggers do not use one
  - Reference: [MOST_RECENT_LAYOUT.post-fix.json](findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json). The checks are static tests (`test_static_checks.test_the_defaults_base_triggers_match_the_july_reference`) and one scenario (DT2 in [test_scenarios_triggers_and_recovery.py](tests/test_scenarios_triggers_and_recovery.py)); a fresh load is A33

## Sticks

- [x] Add left-stick edge cleanup only where needed, matching appropriate right-stick recovery
  - Implemented in both layouts: all eight modifier variants, both Menu Entry Points, both scroll layers, and both Transition Sets; see [scope, guards, and validation](findings/2026-09-28-left-stick-recovery/CHANGES.md). RTP Entry Point remains excluded; Fn layers already cover both edges
  - LS recovery matches each RS owner/family scope, with Hold to Repeat and default Interruptable. With cursor overlays included, single modifiers remove four targets and Mod 2 removes its eleven-target branch; menu entries and scroll layers remove their own pairs. Persistent Gyro remains intact
  - Author-approved Transition Set depth: LS/RS touch and edge all remove the current Transition Set first, then both Menu Entry/Fn families, only when neither menu button is held. Invalid menu-overlay recovery remains the separate ownership review
  - Added explicit LS-edge empty blocks in all seven Double Tap windows to prevent inherited layer mutations while Always On is active; existing timers and self-first/add-last boundaries remain intact
  - Originally used Fn's LS outer region (radius 21000, inversion off). The cursor change moves the four single-modifier pairs to LS radius 4915 / RS 7209; the other ten selected LS layers retain 21000. WASD directions are unchanged; the inherited WASD modifier remains displaced while these layers own the edge. See [the accepted tradeoff](resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions)
- [x] Add WASD modifier scaffold (user-defined)
  - Both layouts use the July reference's Base left-stick Soft Press setup, with an explicit empty binding in place of `KEYPAD_ASTERISK`; the user chooses the modifier key
  - Copied the reference's thresholds, style, inner-ring settings, and noninterruptible WASD presses. The empty scaffold sends no modifier; WASD-only, modifier-only, and combined behavior after assigning a key are a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (WM2)
  - Existing LS-edge recovery and Double Tap blocks still override this slot. See [configuration and inheritance](resources/Steam%20Input%20JSON%20Structure.md#user-defined-wasd-modifier-scaffold)
- [x] Add haptics to Fn stick-direction key selection
  - Both Menu Fn layers in both layouts: `haptic_intensity: "2"` on their eight directional keybinds (four LS + four RS), totaling 16 entries per layout
  - Separate mode-shift bindings, cleanup, empty guards, touch/click actions, and timer ordering are unchanged. Upper layers can inherit the Fn directional feedback; the feel is a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (MB7)

## Global stateful behavior

- [ ] L1 + R1 clears all stateful layers
  - Author rule, 2026-10-01: the Modifier 2 clear (both bumpers in default, both triggers in alternative) always clears everything to Base, including Gyro. It is the fallback from any state and the one exit that never uses a transition ([structure](resources/Stateful%20Layer%20Transitions.md#exceptions)). Every new stateful layer must be removed by it ([definition of done §11](resources/Layer%20Definition%20of%20Done.md#11-stateful-layers))
  - Built for Gyro and Steering: the uncovered opposite release in both ordered Mod 2 variants clears every layer to Base; native acceptance pending
  - The older Gamepad-preservation exception conflicts with this rule. Kept open by the author (2026-10-01); settle it when Gamepad is built

## Bugs

- [x] Fix menu-entry start-delay interruption
  - Both Menu Entry → Fn paths apply after 300 ms and have a repeating 350 ms reset with Interruptable Off. Implemented in both layouts; The sequences are [scenario tests](tests/test_scenarios_menu_and_modifiers.py); that the reset restarts an interrupted delay is A12 (MB3)
- [x] Fix combined tap covers not properly re-adding after interrupt
  - All four Mod 2 variants per layout (both press orders, regular and Gyro) apply the combined Tap Cover after 200 ms and reset it every 250 ms with Interruptable Off. The sequences are [scenario tests](tests/test_scenarios_triggers_and_recovery.py); that the reset restarts an interrupted stage change is A12 (TR9)
- [x] Add delayed-apply reset to all four Temp Cursor Gyro entry parents per layout
  - Corrects the omission from the initial cursor implementation: the owning primary input removes only its Temp Cursor Gyro overlay every 350 ms with Hold to Repeat On and Interruptable Off, alongside the existing 300 ms apply and release exit
  - Both the cursor overlay and normal Tap Cover replace the complete primary input, stopping the reset after cursor entry or override. The reset never removes the normal cover or clears the owner stack. All seven Double Tap windows explicitly replace the primary controls; see [scope and isolation](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#delayed-apply-reset-follow-up) and the [scenario tests](tests/test_scenarios_cursor.py)
- [x] Split menu entry layer into separate Menu Left / Menu Right layers
  - Both layouts have distinct Menu Left: Entry Point and Menu Right: Entry Point layers and their own Fn paths
- [ ] Review extending the delayed-apply reset to additional tap-cover paths
  - At 90.9, 21 of 24 delayed-add paths per layout have a reset (static count, 2026-10-01). The three without are LST Entry → Tap Cover, RST Entry → Tap Cover, and RTP Entry → Tap Cover, which is the deliberate exclusion below. The completed fixes above do not imply every delayed apply needs a reset
  - [Binding inventory](findings/2026-09-28-delayed-apply-reset-audit/INVENTORY.md) and [proposed follow-up work](findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md#proposed-todo-split-and-validation); missing resets are not proof of runtime failures
  - Remaining proposed additions: LST/RST Entry → Tap Cover per layout. The four single-modifier paths now target Temp Cursor Gyro and have their resets. Keep resets in the parent owning the pending apply; preserve overlays and the three-command limit
  - Preserve the author-confirmed RTP touch exclusion for trackball momentum. The four scroll/menu-key Double Tap Cover paths got their resets in 90.6 as a last 4th entry ([record](findings/2026-09-30-second-press-cover-reset/README.md))
  - Keep the 5 ms Gyro Off → Turning Ramp Up 0 delay. It lets the apply fire on the already-held stick under the [held-input rule](resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes), and `tests/test_neptune_held_inputs.py` protects it
- [ ] Run the held-input real-layout checks and act on the results; see the [follow-up plan](plans/2026-09-29-held-input-rule-followups.md)
  - Done: F1 (the alternative R2 → Mod 2 repeats) and the [held-input regression tests](tests/test_neptune_held_inputs.py), including Base's covering repeats
  - Exported: [rule-test.vdf](findings/2026-09-29-held-input-layer-transitions/rule-test.vdf) and both Neptune VDFs using `convert_vdf.mjs`; static export checks pass
  - Pending on the Deck: A10 and A11, the key and mouse output scope (F3.1/F3.2). The staggered Gyro toggle (F3.3) is a scenario test since 2026-10-03, run both ways under A9 (HI2 in [test_scenarios_triggers_and_recovery.py](tests/test_scenarios_triggers_and_recovery.py))
  - Not scheduled: rule 3 (a removal firing the exposed layer command, A9) stays unverified. The layouts back it with repeats; run the optional T4 in `rule-test.vdf` before ever removing a Base repeat
- [x] Confirm menu helper/cover overrides are intentional within the overlay design
  - Keep Backspace / Enter, Escape / Tab, and the two Menu Double Tap Covers local to their button/action; the underlying stack owns recovery. Release-only exits remain valid; review invalid residual helpers in the owner's recovery instead of automatically adding independent edge cleanup to each overlay
  - Author confirmed: Start/Select menu interactions are not used during gameplay. Preserve disabled gyro in all six layers and the Escape / Tab RS-edge blocks; WASD modifiers and ramp-up are not required in menu context
  - Superseded 2026-10-01: the Enter / Backspace layers were removed in 90.9, so the still-held second menu button now falls through to Base
  - Background: [button overlays and inherited cleanup](resources/Steam%20Input%20JSON%20Structure.md#button-overlays-and-inherited-cleanup), [vocabulary](resources/Layout%20Vocabulary.md), and both audits

## Layer cleanup

- [x] Complete the static [cleanup audit](findings/2026-09-28-neptune-cleanup-audit/AUDIT.md) and [blocking audit](findings/2026-09-28-neptune-blocking-audit/AUDIT.md) for both layouts, including all layers, entry/exit references, dormant groups, and Always On ordering
- [x] Document per-layer cleanup and blocking, with [concrete scope examples](resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) and guidance in the editing skills
- [x] Enable Hold to Repeat on every guarded recovery removal in both layouts; see the [separate change record](findings/2026-09-28-repeating-recovery/CHANGES.md). Static validation passed; a missed release and the recovery after it are scenario tests (MR1 in [test_scenarios_triggers_and_recovery.py](tests/test_scenarios_triggers_and_recovery.py), and the missed-release scenarios of each release)
- [x] Build the **Cleanup audit** and add it to the build audit as the fourth audit (90.12)
  - **Built 2026-10-02, tests first:** `audit_cleanups.py` on `steam_layout/cleanups.py`, six checks, stacks from the backward chains ([plan](plans/2026-10-02-cleanup-audit.md)). Not in the build audit yet
  - **First run:** 190 findings per layout, the same in both variants ([fix list](findings/2026-10-02-cleanup-audit/README.md)). Open for the author: the cursor group (recommended: drop), Fn and the stick guards, the other Modifier 2 order, and four new Steering findings
  - **Done in 90.12:** the `cleanup_lists` fix-pipeline step resolves every finding; both layouts are clean and the audit is the fourth gate of `audit_build.py`. C1 to C8 are scenario tests since 2026-10-03 ([test_scenarios_90_12.py](tests/test_scenarios_90_12.py))
  - The gap (2026-10-01): the build audit validates blocks and inheritance, but nothing checks that a cleanup function or an owner release removes the right layers. A list can miss a layer, remove a survivor, or a new layer can be removed by nothing. Today only the Flow audit's cover check and hand-written tests such as `test_neptune_recovery.py` touch this
  - Read-only checker first (`audit_cleanups.py`, steps 1 to 3 of the [cleanup generator plan](plans/2026-09-30-cleanup-generator.md)); no automatic rewriting of lists
  - **The raw lists exist (2026-10-01):** `python3 audit_layer.py <layout> --layer TITLE` prints, for each binding of a layer that removes layers, what it removes that is present, what is present and left, what it removes that is never present, and which layers above intercept it. It is a report, not a check; it passes and fails nothing ([record](findings/2026-10-01-backward-chain-stacks/README.md#the-per-layer-report))
  - Base the audit on those lists. They use the backward chains (`steam_layout/chains.py`) in the view that sees overlaps between families
  - Was blocked on the author's review of the exits lists; answered on 2026-10-02 by the cleanup rules. The tool can see what an exit leaves behind, but not whether that is wrong. "Present, not removed" holds both kinds:
    - left on purpose: `Gyro`, a ramp layer or a stick-touch helper under `Menu Right: Fn Layer`. They belong to something else
    - left by mistake, probably: the Fn layer's 19 recovery bindings leave `Steering | Menu Right: Entry Point` and its Tap Cover, which its release does remove
    - and "removed, never present" may be clutter or a safety net: `L1: Modifier 0`'s release removes `Gyro | L1: Modifier 0`, which is never on the stack with it
  - The review is the same decision as the four open questions in [Cleanup Functions](resources/Cleanup%20Functions.md#questions-for-the-author) (who belongs to a family, what a cleanup must leave alone, which inputs host cleanup functions, who cleans up a layer two families add). Looking at the lists for a few layers is a concrete way to answer them
  - **A rule set to review (2026-10-02):** a cleanup removes the layers below and above it that the same button keeps alive, and nothing another button, a thumb, a timer or a mode keeps alive. Measured on every snapshot; five decisions are open for the author ([findings](findings/2026-10-02-cleanup-boundaries/README.md#decisions-for-the-author))
  - Without those answers a failing check would flag hundreds of correct things or miss the real ones, as the misread blocking rule did ([correction](findings/2026-10-01-backward-chain-stacks/README.md#the-flow-audit-on-chain-stacks))
  - Best done before or with the [transition build](#stateful-layer-transitions), which rewrites many removal lists
- [x] Add the guarded cleanup to both stick touches of the four Modifier 2 layers (author, 2026-10-02: "should have cleanup on its stick touches as well"). They bind the touch with a Release only, which hides the single modifier's touch cleanup ([finding](findings/2026-10-02-cleanup-boundaries/README.md#where-the-layouts-differ-from-the-rules))
- [x] Make the two-step cleanups one step (author's rule, 2026-10-02: every layer takes care of itself and below): the cursor layers' two edge cleanups take the modifier's list, and `RTP: Mouse Buttons`' two stick-touch cleanups also remove `RTP: Circular Scroll`. The cursor's 15 cancellations stay as they are ([record](findings/2026-10-02-cleanup-boundaries/README.md#answered-author-2026-10-02))
- [x] Guard the two stick-touch cleanups of both Steering Modifier 2 layers with either bumper, like their 12 button cleanups (author, 2026-10-02). Today only the bumper pressed first suppresses them
- [x] Shorten every cleanup list to the layers that can be on the stack with its host (author, 2026-10-02: no Gyro twin in a normal layer's list or the reverse, no whole-family lists; "I want to reduce unnecessary layer removals"). About 1,000 of 1,982 removals per layout. Ordinary releases and the Modifier 2 quick tap follow the same rule (up to 139 of 360 removals); deliberate clears and the stick-touch trio keep their lists. Check each against the chains first; `RTP: Mouse Buttons` under `RTP: Circular Scroll` is a known false "never", and the Fn layers' stick guards are a timing-race case to review ([rule 6](findings/2026-10-02-cleanup-boundaries/README.md#6-list-only-what-can-be-on-the-stack-with-you))
- [x] Take the two Steering Double Tap windows out of the six Steering cleanup lists (author, 2026-10-02: a cleanup doesn't list a window; it always clears itself)
- [ ] Review owning-layer recovery against the [overlay cleanup ownership rule](resources/Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership)
  - The Cleanup audit above would check this mechanically. The menu Enter / Backspace overlays named below were removed in 90.9
  - Each layer applying an overlay is responsible for removing it during stale-state recovery when that interaction is no longer valid; retain the overlay's local exit and inherited recovery
  - Trace shared owners and still-held buttons before extending target lists. Review the menu Entry/Fn helpers that currently rely on another related-button press after parent recovery; preserve valid held helpers and normal release behavior

## Carried over

- [x] Make Base gyro activation require LS/RS deflect, LS/RS touch, Select, and Start together, replacing the Start/Select gyro mode shifts
  - Verified in both layouts on 2026-09-29: active Base gyro group 576 uses mask `211109453778944` with `gyro_ratchet_button_requireany_or_all: "1"` (All six inputs)
  - The Start/Select gyro mode shifts are removed. Remaining mode-shift definitions cover trackpad-touch navigation and menu Fn stick punctuation and were preserved by that refactor. Trackpad mode-shift activation under modifiers remains the separate verification item above
  - Implementation: [gyro mode-shift removal plan](plans/2026-09-27-neptune-gyro-shifts-navkeys.md). The runtime checks are scenario tests (ML1 to ML4 in [test_scenarios_menu_and_modifiers.py](tests/test_scenarios_menu_and_modifiers.py)); other gyro layers retain their own activation rules
- [ ] Handle cursor gyro layer (may be covered by [Cursor gyro above](#cursor-gyro))
- [ ] Clear all unnecessary layers on action set swap
  - Likely obsolete: action sets are never switched ([runtime rules](resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30)), and the transitions' clear covers the layer case. Kept open by the author (2026-10-01)
- [ ] Add temp gyro to both right and left stick touch
  - Looks done: `LST: Temporary Gyro` and `RST: Temporary Gyro` exist in both layouts, reached by the second stick touch. Kept open by the author (2026-10-01)
