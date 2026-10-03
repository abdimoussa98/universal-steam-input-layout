# Rule inventory

**Status, 2026-10-02:** read-only inventory, phase 1 of the
[rule registry plan](../../plans/2026-10-02-rule-registry.md). Nothing was
changed to make it. The rule IDs are given in phase 2; the row numbers here
are only for this page.

## What this page is

Every rule and every Steam assumption the repo states today, with each place
it is written, who decided it, and what checks it.

- A **rule** is what our layout must do. Example: an Always On layer is added
  last in its array.
- An **assumption** is what we believe Steam does. Example: a binding array
  runs bottom to top.
- A **place** is one document, skill, code file or memory note that states it.
  A rule stated in the Definition of Done and in two skills has three places.
- **Checked by** names what fails today when the rule is broken: an audit
  check, a fix, or a test. "Nothing" means no script fails.

## Sources read

| Source | Short name below |
|---|---|
| `resources/Layer Definition of Done.md` | DoD §n |
| `resources/Steam Input JSON Structure.md` | JS "section" |
| `resources/Layout Vocabulary.md`, `Cleanup Functions.md`, `Stateful Layer Transitions.md` | Vocab, CF, SLT |
| `resources/Layer Reverse Lookup.md` | An old ID table (version 31.0). No rules |
| `.claude/skills/` (four skills) | skill:name |
| `.cursor/skills/` (six skills) | A second copy, last changed 2026-09-30. See [stale text](#stale-text) |
| Findings READMEs and plans | F:folder, P:file |
| `todos.md`, `README.md`, `manual-testing.md` | todos, README, Deck |
| `steam_layout/flow_config.json`, `traced_stacks.json` | The two files that record exceptions |
| The audits, the fixes and the tests | By file name |
| The four builders in `findings/` | builder 09-29, 09-30, 10-01, 10-02 |
| My memory notes (21, outside the repo) | mem:name |

## Summary

| | Count |
|---|---|
| General rules | 56 |
| Checked by an audit or a fix | 17 |
| Checked only by tests | 20 |
| Checked by nothing | 19 |
| Decisions about one layer or feature | 14 |
| Steam assumptions | 30 |
| Verified by the author or by Valve's documentation | 19 |
| Reported by the author but never isolated (M, X, AA) | 3 |
| Unverified | 8 |
| Recorded exceptions (accepted findings) | 1 in a file, 1 in prototype code (68 pairs) |
| Stale text | 17 places |
| Conflicts between places | 6 |

## Rules

Grouped by the Definition of Done's sections.

### Layer type and placement (DoD §1, §2)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 1 | Every layer lifetime uses `add_layer` and `remove_layer`. Never `hold_layer` | DoD §2; Vocab runtime rules; JS "Current project policy"; todos | Author, 2026-09-30 | Nothing. Five `hold_layer` commands remain in each layout (migration work); the audits leave those two layers out |
| 2 | Never switch action sets (`CHANGE_PRESET`) | DoD §2; Vocab; JS; skill:binding-order; todos | Author, 2026-09-30 | Nothing (neither layout has one) |
| 3 | A new layer is appended to the end of `action_layers` as `Preset_<max+1>`, so no runtime ID shifts | DoD §2; skill:duplicate; JS "ID Shift on Deletion" | Since the July layouts | Per build only: `test_stateful_transitions.test_layers_keep_their_positions`, `test_steering_fallback_hold.test_the_hold_is_appended` |
| 4 | The `action_layers` order equals the `Preset_` numeric order; preset blocks follow it; preset ids run 0..N | DoD §2; skill:prep; skill:apply; JS "CAVEAT"; README; mem:steam-layer-list-vs-key-order | Found 2026-07-11 | `test_neptune_recovery.test_command_budget_and_runtime_reference_order`; the pre-flight script in two skills, run by hand |
| 5 | Layer titles are unique, and editing happens in `{{Base::Title}}` form | DoD §2; skill:prep; skill:apply; skill:duplicate | Since the converter | The pre-flight script, by hand |
| 6 | A layer is mirrored into the alternative layout (L1/R1 become L2/R2) | DoD §2; SLT checklist | Since the two variants | Nothing general; the tests run on both variants |
| 7 | The layer's type decides how much its cleanup removes (stateful, owner, overlay, stick-touch helper, Always On window, ramp) | DoD §1; CF; Vocab | Author, 2026-09-30 | Superseded in practice by rules 27 to 32 (see [conflicts](#conflicts)) |

### Activators (DoD §3)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 8 | Only Regular, Chorded, Start, Release and Soft Press. Never Long Press or Double Press, in any group | DoD §3; JS "Allowed Activation Types"; skill:binding-order; skill:apply; mem:no-long-press-timing; `audit_command_budget.py`; builders 09-30, 10-01 | Author, 2026-09-30 | Budget audit (banned activators); `test_layout_hygiene.test_only_allowed_activation_types_in_any_bank` |
| 9 | At most three command entries per input. Subcommands don't count. One exception in the rule: a delayed-apply reset may be a 4th entry when it is last | DoD §3, §6; JS "Command Entry Budget"; skill:binding-order, prep, apply, duplicate; README; `audit_command_budget.py`; `fixes/cover_resets.py` | Author, 2026-09-27; the 4th entry on 2026-09-30 | Budget audit (`violations`, `allowed_fourth`); `test_layout_hygiene.test_only_second_press_cover_resets_use_a_last_fourth_entry`; every builder |
| 10 | In a new array, removals go below the add so they run first. An existing array's order is never changed to fit that | JS "Binding Execution Order"; skill:binding-order; mem:keep-existing-binding-order | Author, 2026-09-27 and 2026-09-30 | Nothing general. `test_modifier_rocking` pins the sensitive arrays |
| 11 | On a D-pad-mode stick, an inverted edge never adds or removes a layer | DoD §3, §11; Vocab; SLT rule 6; mem:chords-latch; `audit_command_budget.py` | Author, 2026-10-01 | Budget audit (`inverted_edges`). It only counts a group that states the inversion itself |
| 12 | Nothing depends on a chord handing over to another activator when the chord button is released | DoD §3, §11; SLT rule 6; Vocab | Author, 2026-10-01 | Nothing |

### Entry over held inputs (DoD §4)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 13 | A layer command that must fire on an input already held when its layer is added has Hold to Repeat, or the next layer is added in the same array | DoD §4; JS "Held Inputs"; skill:prep; mem:held-input-add-vs-remove | Author's experience, 2026-09-29 | `test_neptune_held_inputs` (five tests) |
| 14 | Anything that must fire after a removal has Hold to Repeat. Base's entries repeat | DoD §4; JS "Held Inputs"; todos | Author, 2026-09-29 | `test_neptune_held_inputs.test_base_entries_repeat_so_exposure_after_a_removal_is_guaranteed`, `test_threshold_exits_that_change_layers_repeat` |
| 15 | Short delays that exist for held inputs are kept (the 5 ms in `Gyro Off Ramp Up`) | DoD §4, §6; JS "Held Inputs"; todos; skill:prep | Author, 2026-09-29 | `test_neptune_held_inputs.test_ramp_handoffs_keep_their_start_delays` |

### Stick-touch release (DoD §5)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 16 | Every layer binds both stick-touch releases itself. Only cover-type layers may inherit them. In the rule: `Gyro` inherits Base's, and the LST and RST helpers bind only their own stick | DoD §5; JS "Complete Delayed Applies"; CF | Author, 2026-09-30 | Nothing general (a one-off static check on 2026-09-30) |
| 17 | A stick-touch release removes only its own side's three helpers. Never `Gyro`, the other stick's layers or a valid owner | DoD §5; JS; F:cleanup-boundaries rule 5 | Author, 2026-09-30 | Cleanup audit ("outside the guard") |
| 18 | An Always On window's stick-touch release removes the window first, then that side's helpers | DoD §5, §9; JS | Author, 2026-09-30 | `test_double_tap_windows.test_stick_touch_release_removes_the_window_first_then_the_side_trio` |

### Hold, tap and double tap (DoD §6)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 19 | A layer that adds a delay or a double tap implements the whole recipe, or records what it leaves out | DoD §6 | Author, 2026-09-30 | Nothing as a whole |
| 20 | Every delayed `add_layer` has a reset: a Regular Press on the same input that removes only that target, repeating, uninterruptible. In the rule: RTP touch has none (trackball momentum) | DoD §6; JS "Interrupted Delayed Layer Applies"; skill:binding-order; `fixes/cover_resets.py` | Author; RTP exception confirmed | Nothing general (a one-off audit on 2026-09-28). `test_neptune_cursor` pins the cursor's |
| 21 | The reset's interval is longer than the delay (50 ms more by convention) | DoD §6 | Convention | Nothing |
| 22 | The hold target overrides the parent's primary input, so the reset never strips an applied cover | DoD §6; JS; todos | Author, 2026-09-29 | `test_neptune_cursor.test_overlays_retire_primary_timers_but_only_normal_covers_replace_touches` |
| 23 | A stick-touch release completes the pending add first, then clears that side's helpers. An applied cover's touch release only cleans up | DoD §6; JS "Complete Delayed Applies"; skill:binding-order; skill:prep | Author, 2026-09-29 | `test_neptune_cursor.test_only_primary_delay_and_touch_completion_enter_cursor` (cursor only) |
| 24 | A cover's release doesn't reopen the window | DoD §6 | Author | `test_modifier_rocking.test_a_used_bumper_exits_cleanly_without_a_window` |
| 25 | Output, haptic, exit-timer and direction-routing delays are not completed on thumb release | DoD §6; JS | Author, 2026-09-30 | Nothing |
| 26 | While a timer is pending, unrelated layer changes are blocked | DoD §6, §8; JS "Blocking to Protect Layer Timers"; skill:binding-order | Author | Nothing general |

### Cleanup (DoD §7)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 27 | The guard is the boundary: a cleanup removes only layers its guard's buttons keep alive | DoD §7; F:cleanup-boundaries; `audit_cleanups.py`; `steam_layout/cleanups.py`; README; mem:cleanup-boundary-rules | Author, 2026-10-02 | Cleanup audit ("outside the guard", "guard mismatch"); `cleanup_lists` fix; `test_cleanups` |
| 28 | Below: a cleanup removes, in one step, every layer under it that the same buttons keep alive | Same | Author, 2026-10-02 | Cleanup audit ("left below"); `cleanup_lists` fix |
| 29 | Above: a cleanup removes a layer on top that the same buttons keep alive and that leaves the cleanup's input alone | Same; JS "Overlay Cleanup Ownership"; Vocab "Ownership and limits"; skill:binding-order | Author, 2026-10-02 (ownership since 2026-09-28) | Cleanup audit ("left above"); `cleanup_lists` fix |
| 30 | A layer that binds an input with a cleanup below carries that cleanup | Same; DoD §5 | Author, 2026-10-02 | Cleanup audit ("hidden cleanup"); `cleanup_lists` fix |
| 31 | A cleanup never removes a stateful layer, a stick-touch helper, a window, or a layer another button keeps alive | Same; DoD §1 | Author, 2026-10-02 | Cleanup audit ("outside the guard") |
| 32 | A list names only layers that can be on the stack with its host. In the rule: deliberate clears keep whole lists, and the stick-touch helpers stay fixed | Same; todos | Author, 2026-10-02 | Cleanup audit ("never there"); `cleanup_lists` fix |
| 33 | A cleanup function has the guarded recovery shape: a chord for each valid owner beside an interruptible Regular Press with Hold to Repeat | DoD §7; JS "Guarded Recovery Binding Shape"; Vocab; CF; skill:binding-order; skill:prep | Standardised 2026-09-28 | `test_neptune_recovery.test_all_guarded_removals_repeat_and_rtp_stays_out_of_ls_scope`; `steam_layout/flow_model.py` recognises the shape |
| 34 | Stick-edge cleanup only where it is needed: the left edge costs the WASD modifier, the right edge costs ramp-up | DoD §7; JS "Stick-Edge Cleanup"; skill:binding-order; skill:prep | Author | Nothing general. `test_neptune_recovery` pins the selected edges |
| 35 | A cancellation removes only itself, repeating and uninterruptible, and has no guard | CF; JS "Cursor Cancellation"; F:cleanup-boundaries rule 2 | Author, 2026-10-02 | `test_neptune_cursor.test_cursor_cancellations_remove_only_themselves_and_leave_outputs_to_parent` |
| 36 | **Hidden exit.** A layer that can land on top of another may not cover an exit on what keeps the lower layer alive, unless it removes the lower layer there | F:hidden-exit; todos; P:rule-registry | Author, 2026-10-02 (the check isn't approved to build) | The prototype only. Not in the build audit. Not in the DoD |
| 37 | **Temporary guards.** No layer is added over a temporary guard (`Steering \| LS: Entry Guard`, `Steering \| LS: Fallback Hold`); only removals happen there | F:steering-fallback-hold; todos; mem:review-varies-for-new-layers | Author, 2026-10-02 | `test_steering_fallback_hold.test_no_menu_layer_lands_on_the_hold_or_the_entry_guard`. Not in the DoD |
| 38 | The held button's layer owns its combos. No overlay layer exists only to protect a second button that is still held | JS "Button Overlays"; Vocab; F:intended-flow-checker; `fixes/menu_combo_keys.py`; mem:owner-leaves-held-buttons-fall-through | Author, 2026-10-01 | `test_fixes.test_overlays_are_gone_and_nothing_references_them` (those two layers) |

### Inheritance and blocking (DoD §8)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 39 | Inheritance is the default. An ordinary layer is never required to block an input because the layers below give it different bindings | DoD §8; `steam_layout/flow_inheritance.py`; mem:block-or-override-is-the-window-rule | Author, 2026-10-01 | Nothing fails (the Flow audit lists "varies" as information). See [conflicts](#conflicts) |
| 40 | **Window rule.** Under a layer with an Always On action, an input left open whose inherited binding is a layer command in any stack must be handled: replaced with the keybind when only one is possible, cleared otherwise. A stack whose binding is only a layer command adds no keybind | DoD §8, §9; JS "Always-On Layer Isolation"; skill:apply; `audit_inheritance.py`; `fixes/window_routes.py`; mem:block-or-override-is-the-window-rule | Author, 2026-09-30, restated 2026-10-01 | Window audit; `window_routes` fix; `test_audit_inheritance`; `test_double_tap_windows` |
| 41 | A block clears the input by default and replaces it only where the use is obvious. It only targets routes that change layers. It is never a removal | DoD §8 | Author, 2026-09-30 | The Window audit accepts cleared, replaced, disabled and mode-replaced. "Never a removal" is not checked |
| 42 | In menu layers gyro stays disabled and the right-stick edge stays blocked | DoD §8; JS "Button Overlays", "Stick-Edge Cleanup"; skill:prep; todos | Author | `test_neptune_gyro.test_gyro_sources_only_override_owned_properties_or_explicitly_disable` (gyro) |
| 43 | Base owns the gyro response. Activation layers set only their selector fields, the cursor only its four response settings | JS "Gyro Settings Inheritance"; skill:prep | From the July reference | `test_neptune_gyro` (two tests); `test_neptune_cursor.test_cursor_profile_preserves_sensitivity_and_owner_activation` |
| 44 | A cover never outlives its owners, never sits below its owner, and inherits nothing through a layer between it and its owner | `steam_layout/covers.py`; DoD §10 table | Author-approved plan, 2026-09-30 | Flow audit (cover check); `test_covers` |
| 45 | A chain of adding bindings reaches every layer | DoD §10; `audit_flow_inheritance.py` | 2026-10-01 | Flow audit (coverage); `test_flow_inheritance` |

### Always On layers (DoD §9)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 46 | Entry: every other layer change first, the Always On layer added last | DoD §6, §9; JS "Always-On Layer Isolation"; CF; skill:binding-order; skill:prep | Author, documented 2026-09-28 | `test_neptune_recovery.test_timed_windows_block_both_edges_and_preserve_ordered_boundaries` |
| 47 | Timeout: the layer removes only itself | Same | Same | Same test; builders 09-30 and 10-01 refuse an unexpected Always On layer |
| 48 | Early exit: the layer is removed first, then the other changes | Same | Same | Same test; `test_double_tap_windows` |
| 49 | Both trackpads stay off the layer API during every window | DoD §9; `fixes/window_pads.py`; F:double-tap-pad-blocks | Author, 2026-09-30 | `window_pads` fix; `test_double_tap_windows` (three tests) |

### Ship it (DoD §10)

| # | Rule | Places | Decided | Checked by |
|---|---|---|---|---|
| 50 | The build audit is clean on every version | DoD §10; skill:apply; todos; README | Author | `audit_build.py`; `test_stateful_transitions.test_audits_are_clean` |
| 51 | A published layout has a reviewed description, one version bump per release, a regenerated VDF and a snapshot under `versions/neptune/<version>/`. Other versions' snapshots never change | README "Publishing layout changes"; skill:apply; skill:prep; DoD §10 | Author, standing instruction | By hand, through the skill. `test_steering_fallback_hold.test_working_layouts_are_this_build` |
| 52 | The working layouts are a fixed point of the fix pipeline | `steam_layout/fixes/__init__.py` | Since the pipeline | `test_fixes.test_working_layouts_are_a_fixed_point` |
| 53 | No dead groups: no plain-inactive slots and no unreferenced groups | `fixes/dead_groups.py`; P:banned-activators-and-dead-groups | 2026-09-30 | `dead_groups` fix; `test_layout_hygiene.test_no_unreferenced_groups_or_plain_inactive_slots` |
| 54 | The tests pass, a new invariant gets a new test, and the change is recorded in `findings/<date>-<slug>/` | DoD §10; mem:save-plans-as-repo-docs | Author | By hand |
| 55 | A Deck section is added to `manual-testing.md` | DoD §10, §11; README; skill:apply | Author | Nothing. The plan removes this rule in phase 15 |
| 56 | The working layouts are generated: they equal the current builder's output run through the fix pipeline. A hand edit there is lost on the next install | Only `tests/test_steering_fallback_hold.py` and the install script's docstring | Since the 09-30 builder | `test_steering_fallback_hold.test_working_layouts_are_this_build` |

## Decisions about one layer or feature

These are decided and mostly tested, but they describe one layer, not every
layer. They stay in their design documents. I left them out of the registry;
say so if they should get IDs too.

| # | Decision | Places | Decided | Checked by |
|---|---|---|---|---|
| L1 | The Modifier 2 entry adds, in this order: the first side's Tap Cover, the second modifier, its Tap Cover, Modifier 2. The combined cover's release removes only the released side and both Modifier 2 orders | JS "Rocking"; CF "Order matters"; mem:modifier-rocking-is-sensitive | Author, 2026-09-30 and 2026-10-02 | `test_modifier_rocking` (nine tests) |
| L2 | The Modifier 2 quick tap clears everything to Base, including `Gyro`. Every stateful layer is removed by it | DoD §1, §11; SLT; todos | Author, 2026-09-30 and 2026-10-01 | `test_stateful_transitions`; exempt from "never there" in the Cleanup audit |
| L3 | Every stateful layer is entered and left through a transition. Stateful layers never add each other directly | SLT rule 1; DoD §11 | Author, 2026-10-01 | `test_stateful_transitions.test_transition_menu_releases` |
| L4 | No layer can be entered from a transition | SLT rule 3; DoD §11 | Author, 2026-10-01 | `test_stateful_transitions.test_nothing_is_entered_from_a_transition` |
| L5 | Inside a stateful layer, any menu button plus any stick click clears, keeping `Gyro` | SLT rule 4; DoD §11 | Author, 2026-10-01 | `test_stateful_transitions.test_entry_point_clicks_release_into_their_transition` |
| L6 | Entering a transition clears the whole stack first, keeping `Gyro` | mem:cleanup-boundary-rules; F:cleanup-boundaries | Author, 2026-10-02 | Exempt from "never there" as a deliberate clear |
| L7 | Every menu Release in a transition beeps and gives a strong pulse | SLT; DoD §11 | Author, 2026-10-02 | `test_stateful_transitions.test_every_transition_beeps_and_pulses_on_its_menu_release` |
| L8 | At entry a stateful layer has no Release or delayed binding on Start or Select | SLT; DoD §11 | Author, 2026-10-01 | `test_stateful_transitions.test_base_and_steering_add_their_entry_points_with_a_repeating_press` |
| L9 | Menu buttons inside Steering: Entry Points with no driver held, Tab and Escape with a driver held | SLT rule 5 | Author, 2026-10-01 | `test_stateful_transitions.test_steering_drivers_keep_tab_and_escape` |
| L10 | Steering's stick modifiers end on a normal outer edge's Release; the opposite direction only cleans up; their cleanups are guarded by two All-chords | SLT "Steering's left stick"; todos | Author, 2026-10-01 | `test_stateful_transitions` (five tests) |
| L11 | The two Steering windows bind the stick and both drivers themselves | SLT; DoD §9 | Author, 2026-10-01 | `test_stateful_transitions.test_steering_windows_are_always_on_and_bind_everything_themselves` |
| L12 | No turn assist in Steering: `Steering` blocks the right-stick edge | F:steering-fallback-hold; builder 10-02 | Author, 2026-10-02 | `test_steering_fallback_hold.test_no_turn_assist_in_steering` |
| L13 | The stick guards behave like the Entry Point for the held menu button and bring in the menu Tap Cover where the Entry Point brings in Fn | SLT "(2) Stick guards" | Author, 2026-10-01 | `test_stateful_transitions` (three tests) |
| L14 | The cursor's twelve cancel inputs split into three entries: an output chord, a cover chord and the recovery | JS "Cursor Cancellation"; skill:binding-order | 2026-09-29 | `test_neptune_cursor` (twelve tests) |

## Tool scope decisions

Not layout rules: what the audits leave out, by the author's choice. In phase
2 each becomes a clause of the rule its audit checks.

| Decision | Places | Decided |
|---|---|---|
| The chains ignore chords: every adding binding is followed | DoD §8; `steam_layout/chains.py`; mem:backward-chain-stacks | Author, 2026-10-01 |
| `hold_layer` is not followed, and layers only it adds are left out of the Cleanup audit | `steam_layout/chains.py`; `steam_layout/cleanups.py`; mem:cleanup-boundary-rules | Author, 2026-10-01 and 2026-10-02 |
| Missed releases and timing are not modelled | DoD §8, §10; `audit_cleanups.py` | 2026-10-01 |
| No race rule: a cleanup doesn't list a layer that only a timing race could put there | mem:cleanup-boundary-rules; F:cleanup-audit | Author, 2026-10-02 |
| The inverted-edge check counts only a group that states the inversion itself | `audit_command_budget.py`; todos | Author, 2026-10-01 |

## Assumptions

What the rules and tools assume Steam does.

| # | Assumption | Status | Places | What rests on it |
|---|---|---|---|---|
| A | The topmost layer that defines an input answers it; an input a layer leaves unbound comes from the stack below; binding an input replaces all of it | Verified: Valve's documentation and the author's use | DoD §8; JS "How Binding Overlay Works"; `steam_layout/stacks.py` | Every audit; rules 16, 30, 39, 40 |
| B | A disabled source stops the lookup, and a group in a different source mode blocks the whole source | Verified by the author, 2026-10-01 | DoD §8; JS; `audit_inheritance.py`; `steam_layout/flow_inheritance.py`; todos | Window audit, Flow audit; rule 40 |
| C | Re-adding an active layer doesn't move it | Verified: Valve's documentation, and the author on the Deck, 2026-09-30 | JS; CF; `steam_layout/stacks.py`; mem:modifier-rocking-is-sensitive | L1, every stack the chains build |
| D | A binding array runs bottom to top | Verified by the author (long-standing) | JS "Binding Execution Order"; DoD §3; skill:binding-order (two copies); `steam_layout/chains.py` | Rules 10, 18, 23, 46 to 48; L1 |
| E | A layer added over a held input doesn't fire its immediate layer command on that input (held-input rule 1) | Verified by the author's experience, 2026-09-29. Layer commands only | DoD §4; JS "Held Inputs"; skill:prep; mem:held-input-add-vs-remove | Rules 13, 15 |
| F | In that layer, a delayed activator and a repeating activator still fire (held-input rule 2) | Verified by the author's experience, 2026-09-29 | Same | Rules 13, 15; the 5 ms delays |
| G | A Release in a layer added over a held button fires when the button is released | Verified by the author's experience | JS "Held Inputs" table; SLT "The flow" | The transitions; every cover's Release |
| H | A stick edge's Release fires in a layer added while the stick was already out | **Unverified** (Deck gate G3) | SLT "Deck gates"; Deck 90.10 | The stick guards, L10, the Fallback Hold |
| I | Removing a layer fires the exposed layer command on a held input (held-input rule 3) | **Unverified**, by the author's choice. The layout doesn't rely on it: those commands repeat | DoD §4; JS "Held Inputs"; todos; mem:held-input-add-vs-remove | Rule 14 backs it |
| J | A key or mouse output fires on an input that is already held when its layer is added | **Unverified** on its own; the author's experience is that it does | DoD §4; JS "Held Inputs"; SLT | Fn's Backspace and Enter; W and S in a Steering window |
| K | A key or mouse output fires when a removal exposes it under a held input | **Unverified** | JS "Held Inputs"; SLT | The first click after `Gyro Off Ramp Up`; W and S after a Steering window |
| L | An interrupted delayed `add_layer` can fail to fire on the next press, and a repeated `remove_layer` of its target restarts the delay (restart and wait, not cancel) | Verified by the author's observation, clarified 2026-09-30 | DoD §6; JS "Interrupted Delayed Layer Applies"; Vocab | Rules 20 to 22 |
| M | Any removal can reset a running delay; an add doesn't | The author's report; not isolated | JS "Blocking to Protect Layer Timers"; DoD §6, §8 | Rules 23, 26, 41 |
| N | A delay starts again when a removal exposes it under a held button | **Unverified** | SLT "untested in isolation" 4; mem:override-eats-pending-delay | Fn following a guard that came off |
| O | A layer that binds a button while a delay is running on it cancels the delayed action | Verified by the author, 2026-10-01 | JS "Held Inputs"; SLT; mem:override-eats-pending-delay | The stick guards; every Tap Cover over a delayed add |
| P | A delay's clock starts when its layer is added, not at the physical press | **Unverified** (Deck 90.6 C3, 90.11 F4) | todos; Deck | Steering's windows; the Fallback Hold's 1.5 s |
| Q | Chords latch: once a chord is active, releasing the chord button doesn't end it | Verified by the author's test, 2026-10-01 | DoD §3; Vocab; SLT; mem:chords-latch | Rule 12 |
| R | A `remove_layer` call re-evaluates held inputs | **Unverified** (the author's hypothesis) | Vocab; JS; todos | Nothing yet |
| S | On a D-pad-mode stick an inverted edge isn't caught reliably; a normal outer edge and its Release are. Mouse-mode sticks aren't affected | Verified by the author on the Deck, 2026-10-01 | DoD §3; Vocab; `audit_command_budget.py` | Rule 11 |
| T | Long Press and Double Press misbehave with layers | Verified by the author's report, 2026-09-30 | JS "Allowed Activation Types"; skill:binding-order; mem:no-long-press-timing | Rule 8 |
| U | The desktop configuration drops every command entry after the third | Verified by the author, 2026-09-30. That only the 4th is lost is unchecked (Deck 90.6 R3) | JS "Command Entry Budget"; DoD §3; skill:binding-order | Rule 9 |
| V | On a fresh VDF load, Steam can resolve runtime IDs by `Preset_` key order instead of list order | Observed 2026-07-11 on `controller_triton`; older Neptune exports loaded out of order | JS "CAVEAT"; README; skill:prep; mem:steam-layer-list-vs-key-order | Rule 4 |
| W | Deleting a layer shifts every later runtime ID | Verified (documented format) | JS "ID Shift on Deletion"; skill:duplicate | Rule 3 |
| X | Adding or removing another layer while an Always On layer is active caused crashes | The author's report of a historical bug; whether it still happens is unknown | JS "Always-On Layer Isolation"; DoD §8; skill:binding-order | Rules 40, 46 to 49 |
| Y | A release made while the Steam menu is open is missed, and the layers stay on | Verified by the author's observation | JS "Stuck Layers"; DoD §7 | Rules 27 to 34 |
| Z | Stick inputs inherit through the middle of the stack like any other input | **Unverified** (Deck gate G1). A 2022 report says sticks inherit only from the top layer and the action set | JS "How Binding Overlay Works"; SLT "Deck gates"; todos | The stick guards and Fn inheriting the stick clicks; every audit's stick lookups |
| AA | An active chord suppresses an interruptible Regular Press on the same input | Relied on since the July layout; chord arbitration between two chords is **unverified** | JS "Guarded Recovery Binding Shape", "Cursor Cancellation" | Rule 33; L14 |
| AB | Repeated layer removal breaks trackball momentum | Verified by the author's observation | JS "Interrupted Delayed Layer Applies"; DoD §6 | The RTP clause of rule 20 |
| AC | An explicit empty binding overrides the lower binding. An omitted input, an empty `inputs` object and an `inactive` group don't | Verified (documented, and used by every block). That the GUI saves a cleared binding as `empty_binding` is assumed | DoD §8; JS "Empty Bindings" | Rule 41; the Window audit |
| AD | The chord selector's Any is `0` and All is `1`; legacy `chord_button` IDs are not bitmasks | Verified in the installed Steam chord UI schema, 2026-09-27 | JS "Command Entry Budget"; skill:prep; `steam_layout/flow_model.py` | Guards read by the Cleanup audit |

Also unverified, about one feature: whether the trackpad's inactive
mode-shift targets take effect under a modifier (Deck, "Temp cursor gyro").

## Where exceptions live today

An exception is one accepted finding. Phase 4 moves them into one register.

| Where | Shape | Entries today |
|---|---|---|
| `steam_layout/flow_config.json` `decisions` | Layers, inputs, `allow` or `todo`, a reason | 1: the two Steering stick modifiers inherit the drivers |
| `steam_layout/flow_config.json` `covers.allow` | Cover, checks, a reason | 0 |
| `steam_layout/flow_config.json` `cleanups.keep` | Layer, removed layer, a reason | 0 (the key isn't in the file) |
| `traced_stacks.json` `targets` | Extra stacks, and `allow` or `todo` per route | 0 (the last `allow` was retired on 2026-10-01) |
| `findings/2026-10-02-hidden-exit/prototype.py` | Code: every pair with a touchpad layer is set aside | 68 pairs on 90.13 |

`flow_config.json` also holds declarations that aren't exceptions:
`covers.titles` (`Gyro Off Ramp Up` is a cover) and `covers.not_covers` (the
LST and RST Tap Covers aren't).

The plan's phase 4 named three shapes in one file. There are four shapes in
two files, plus the prototype.

## Flags

### Duplicates

Rules restated in many places, each a copy that can drift:

| Rule | Places |
|---|---|
| 9, three entries per input | 7 documents, 2 code files |
| 8, allowed activators | 5 documents and notes, 3 code files |
| 40, the window rule | 4 documents and notes, 3 code files |
| 46 to 48, Always On ordering | 5 documents |
| 27 to 32, the cleanup rules | 4 documents and notes, 3 code files |
| 13 to 15, held inputs | 5 documents and notes |
| 4, list order equals `Preset_` order | 6 documents and notes |
| Assumption D, bottom to top | 3 documents, 1 code file |

The `.cursor/skills/` copies are not counted.

The pre-flight script (rules 4 and 5) is pasted into two skills, in two copies
each.

### Conflicts

1. **What an owner's cleanup removes.** DoD §1's table and CF say "its
   family, plus every overlay it applied". The cleanup rules (27 to 32) say
   what its guard's buttons keep alive and what can be on the stack with it.
   The second is what the audit enforces.
2. **A Release in a layer added over a held input.** SLT calls it
   established; SLT's own Deck gate 2 calls the stick-edge case untested. Both
   are right once split by input: buttons are established (G), a stick edge
   isn't (H). The plan's seed list had them as one unverified entry.
3. **"Varies" entries.** DoD §8 and the Flow audit say they are information.
   The plan's decision 4 (author, 2026-10-02) makes them fail on a changed
   layer until accepted. Not built.
4. **What goes in `flow_config.json`.** DoD §10 says only two things. The
   file takes three kinds of decision, and DoD §8 sends Window audit
   exceptions to a different file.
5. **The Modifier 2 clear and Gamepad.** L2 says it removes every stateful
   layer. An older to-do keeps Gamepad through it; the author left that open
   on 2026-10-01.
6. **Cover-type layers.** DoD §5 says "there's no strict definition yet; it's
   a judgment call", while `flow_config.json` defines them by title suffix
   for the cover check.

### Stale text

Checked against the 90.13 layouts on 2026-10-02.

| Where | Says | Now |
|---|---|---|
| Builder 09-30, line 423 | Steering and the W and S layers keep turn assist | Off since 90.13 (L12). The builder is frozen; note only |
| JS "Complete Delayed Applies" | Enter and Backspace are cover-type layers | Removed in 90.9 |
| JS "Always-On Layer Isolation" | RTP Double Tap's right-pad touch is a deliberate `allow` | Retired 2026-10-01; the mode change blocks it |
| JS "Mod 2 Current-Branch Cleanup" | Eleven targets | 6 since 90.12 |
| JS "Combined Tap Cover" | Nine removals; the uncovered release clears thirteen | 8 and 6 |
| JS "Guarded Recovery Binding Shape", Vocab "Guarded recovery" | `L1: Modifier 0` removes four layers, with its Gyro twin | 3, no twin |
| JS "Always-On Layer Isolation" | "All 13 entry bindings", "30 owned bindings", seven windows | Counts from 90.2; nine windows |
| JS "Stuck Layers", "Guarded Recovery", "Interrupted Delayed Layer Applies" | 390 removing activators; 207 guarded removals; fifteen of nineteen delayed adds have a reset | Counts from 90.2 to 90.6, not recounted |
| DoD §9 "Current coverage of rule 2" | Derived stacks at depth 5, seven windows | The depth search is archived; nine windows |
| DoD §8 "How to check it", steps 5 and 6 | Exceptions go in `traced_stacks.json`; the test fails when saturation breaks | Saturation went with the depth search |
| DoD status line | "draft for author review, 2026-09-30" | In use since |
| skill:apply | The Window audit fails on an unsaturated search | No such failure any more |
| CF status and "Still open" | Everything is a proposal; four questions open | Answered by the cleanup rules, 2026-10-02 |
| Vocab "Known implementation conflicts" | Five `hold_layer` commands at group positions 12, 17, 19, 52, 82 | Still five; the positions are from before the dead-group prune |
| `manual-testing.md` header | Covers the trigger port, the 90.1 reorder, 90.2 | Seven releases behind |
| `.cursor/skills/` | A second copy of four skills, plus two more | Last changed 2026-09-30; all four differ from `.claude/skills/` |
| mem:cleanup-boundary-rules, mem:stack-search-goal | "Awaiting the author's confirmation"; "extend the families in flow_config.json" | Shipped in 90.12; families are gone |

## What I'd take into phase 2

- The 56 general rules get IDs. Rules 27 to 32 stay six rules, as the audit
  has six checks.
- Rules 36 and 37 enter the Definition of Done for the first time.
- Rule 7 is rewritten to point at rules 27 to 32.
- Rule 55 is kept until phase 15 removes it.
- The 19 rules that nothing checks go on the "not checked yet" list.
- The 30 assumptions get IDs in phase 10, with H and G kept apart.

## Corrections made in phase 2

The IDs were given on 2026-10-02 in the
[Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md#rule-tables).

- **Row n here is rule R(100 + n).** Row 8 is R108. The IDs start at 101
  because R1 to R5 are buttons.
- **Seven "one layer" decisions are rules for every stateful layer** and got
  IDs: L3 is R157, L5 is R158, L2 is R159, L4 is R160, L7 is R161, L8 is R162
  and L6 is R163. L1 and L9 to L14 stay in their design documents.
- **Row 17 was wrong about its check.** The Cleanup audit's "outside the
  guard" stops a cleanup function from removing a stick-touch helper (row
  31). Nothing general checks what a stick-touch Release itself removes; one
  test covers the transitions.
- **The registry has 63 rules.** 18 are "Not checked yet". 13 more are
  checked only in part: a test pins some layers, not every layer.

## The tests' length checks, sorted (phase 5)

A **length check** is an `assertEqual(len(...), ...)` line. The tests had 59
at the baseline. Each was sorted by what its number is:

| Kind | Count | What happened | Example |
|---|---|---|---|
| The rule's own number, or a structural "exactly one" | 27 | Kept | "Exactly three entries" on a cursor input; the 12 mapped buttons of a Steering modifier; the 15 inputs that apply the Tap Cover |
| On a made-up layout | 6 | Kept | "One violation" in a four-chord test layout |
| On a frozen builder or a pinned snapshot | 16 | Kept: the number can't move | "16 new layers" from the 09-30 builder; six Steering layers in the 90.10 snapshot |
| A release-specific number on the working layouts or the current build | 10 | Replaced or removed | "71 layers", "69 targets", "9 windows" |

Two more pinned totals weren't length checks: "21 entries" and "44 exits" in
the Always On ordering test. They were replaced too, so 12 numbers went.

| Test file | Number | Now checks |
|---|---|---|
| `test_audit_inheritance.py` | 9 targets | The audited layers are exactly the layers with an Always On action (R140) |
| `test_double_tap_windows.py` | 9 windows | The Always On layers are exactly the layers titled "…: Double Tap" |
| `test_fixes.py` | 71 layers | Removed: the line above already checks the two overlay layers are gone (R138) |
| `test_flow_inheritance.py` | 69 targets, 14 covers | Every layer is reached except the ones only `hold_layer` adds (R145); the cover-checked layers are exactly the cover-type ones (R144) |
| `test_neptune_recovery.py` | 9 windows, 21 entries, 44 exits | The same window check, and every window has an entry and an exit that the loop checked (R146 to R148) |
| `test_neptune_cursor.py` | 9 windows | The same window check |
| `test_stateful_transitions.py` | 12 stick groups, 9 windows | The layers R111 is about are among the ones checked; the same window check |
| `test_steering_fallback_hold.py` | 72 presets | Removed: `test_the_hold_is_appended` already checks the whole layer list (R103) |

Each replacement was run against the working layouts, and the first one was
also tried with a window dropped from the audit, which it catches.

## Stale text, fixed (phase 9)

Every row of the [stale text](#stale-text) table was dealt with on 2026-10-02:

- **Corrected to 90.13:** the structure reference's cleanup lists and counts
  (Modifier 2, the combined Tap Cover, the guarded recovery example, the
  cleanup scopes table, the cover-type list, the RTP `allow` note), the
  Vocabulary's guarded recovery example and `hold_layer` note, the Definition
  of Done's status line, its coverage note in §9 and step 6 in §8, the apply
  skill's "unsaturated search", Cleanup Functions' status, and the Deck
  checklist's header.
- **Dated instead of recounted:** the counts of removing activators, guarded
  removals and delayed-add resets in the structure reference now say which
  release they are from.
- **Left in place, with a note:** the frozen 09-30 builder's comment (noted
  in the [90.13 record](../2026-10-02-steering-fallback-hold/README.md)), and
  `.cursor/skills/`, whose four shared skills now point at the maintained
  copies under `.claude/skills/`.
- **Found while fixing, not in the table:** the cleanup scopes table still
  described a guarded fallback on the Transition Sets, which 90.10 removed.

Of the six [conflicts](#conflicts): 1, 3, 4 and 6 are resolved in the documents, 2
is kept apart as two assumptions for phase 10, and 5 (Gamepad through the
Modifier 2 clear) is the author's open decision, in the exceptions register.
