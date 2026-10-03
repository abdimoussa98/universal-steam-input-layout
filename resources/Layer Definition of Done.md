# Layer definition of done

**Status:** draft for author review, 2026-09-30.

A layer is done when every section below holds for both variants (default and
alternative). This page is the one list of the layout's rules. Each section
starts with its rules, one row each, and then gives the notes and links that
explain them. Other documents explain a rule and point at its ID here; they
don't restate it.

## Contents

| # | Section | What it covers |
|---|---|---|
| 1 | [Layer type](#1-layer-type) | What kind of layer this is, which decides how much its cleanup removes |
| 2 | [Placement](#2-placement) | Where it goes in the file so other layers' IDs don't shift |
| 3 | [Activators](#3-activators) | Which Steam activators are allowed, and the three-entry limit |
| 4 | [Entry](#4-entry) | Whether it still works when a button is already held |
| 5 | [Stick-touch release](#5-stick-touch-release) | Lifting a thumb must clear that side's LST or RST layers |
| 6 | [Hold, tap and double tap](#6-hold-tap-and-double-tap) | **The recipe** for chorded delay + repeating reset + release → Double Tap → Double Tap Cover, the stuck-delay bug it works around, and how touch release fits in. Required whenever a layer adds a delay or a double tap |
| 7 | [Cleanup](#7-cleanup) | Normal exit, recovery from stuck layers, and which other layers must remove this one |
| 8 | [Inheritance and blocking](#8-inheritance-and-blocking) | What a layer picks up from the layers below it, when to block that, and what a block looks like |
| 9 | [Always On layers](#9-always-on-layers) | Ordering rules for the Double Tap windows. What they block comes from §8 |
| 10 | [Ship it](#10-ship-it) | Audits, tests, Deck checks and publishing |
| 11 | [Stateful layers](#11-stateful-layers) | A stateful layer is entered and left through the transition structure. Only for stateful layers |
| – | [Rule tables](#rule-tables) | How to read a rule row, and what each column means |
| – | [Open questions](#open-questions) | Decisions for the author |

Main references: [Steam Input JSON Structure](Steam%20Input%20JSON%20Structure.md)
(**JSON Structure** below) and [Layout Vocabulary](Layout%20Vocabulary.md).

---

## Rule tables

Every rule has one row, always in these columns. A test reads them
([test_rule_registry.py](../tests/test_rule_registry.py), through
[rules.py](../steam_layout/rules.py)), so the shape is fixed.

| Column | What it holds |
|---|---|
| ID | `R` plus a number from 101. It is never reused or renumbered, and it says nothing about the section. R1 to R5 are buttons, so no rule has those |
| Rule | One plain statement of what the layout must do. A case the rule itself leaves out is part of this statement |
| Example | One case from the layout |
| Decided | Who decided it, and when |
| Checked by | What fails when the rule is broken: an audit check (`Budget audit: banned activators`), a step of the fix pipeline (`` `cleanup_lists` fix ``) or a test (`` `test_file.test_name` ``), separated by `;`. "(part)" after one means it covers only some layers. **Not checked yet** means nothing fails |
| Rests on | The Steam assumptions the rule depends on, by ID. A dash until the assumptions have IDs |
| Exceptions | Places where the layout breaks the rule and that is accepted or still to fix, with the reason. **None** otherwise |

A rule that stops applying keeps its row and its ID, with "Retired", the date
and the reason under Checked by.

### Exceptions register

Every exception is one entry under `exceptions` in
[flow_config.json](../steam_layout/flow_config.json): the rule's ID, what the
exception covers, `allow` (accepted) or `todo` (a known gap), the reason, who
decided it and when, and the to-do that ends it. The audits read their
exceptions from there ([exceptions.py](../steam_layout/exceptions.py)). A rule's
Exceptions column says "None" exactly when the register has no entry for it; a
test checks that ([test_exceptions.py](../tests/test_exceptions.py)).

### Checks and rules

The link runs both ways. Each audit and each fix declares the rule IDs it
enforces and prints them next to its findings, and a test fails when that
declaration and a row's "Checked by" disagree. To see which rules still need a
check:

```bash
python3 -m steam_layout.rules      # not checked yet, and checked only in part
```

## 1. Layer type

Choose the layer's type first. The author accepted these types on
2026-09-30, and more may be added later.

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R107 | A layer has one type: stateful, owner, overlay, stick-touch helper, Always On window, or ramp. The type decides what removes the layer; what its own cleanup removes follows the cleanup rules in [§7](#7-cleanup) | `Steering` is stateful, `L1: Modifier 0` an owner, `L1: Tap Cover` an overlay, `L1: Double Tap` an Always On window | Author, 2026-09-30 | Not checked yet | — | None |

| Type | Examples | What its cleanup removes |
|---|---|---|
| Stateful | `Gyro`, `Steering` | Removed only by its own deliberate exit. Other layers' cleanup never removes it. See [§11](#11-stateful-layers) |
| Owner | Modifiers, Menu Entry and Fn layers, the two menu stick guards, Scroll, Transition Sets, trackpad modes | Its family or current branch, plus every overlay it applied |
| Overlay | Tap Covers, Double Tap Covers, Temp Cursor Gyro | Itself, or a local pair. The owner handles recovery when it gets stuck |
| Stick-touch helper | `LST` or `RST` `Entry Point`, `Tap Cover` and `Temporary Gyro` | Every layer removes it when the thumb lifts off that stick ([§5](#5-stick-touch-release)) |
| Always On window | The nine Double Tap layers, including `Steering \| LS Up/Down: Double Tap` since 90.10 | Only itself ([§9](#9-always-on-layers)) |
| Ramp or threshold | `Turning Ramp Up 0/1`, `Gyro Off Ramp Up` | Itself and the ramp family, through repeating threshold exits |

**Exception (author, 2026-09-30):** the quick opposite-modifier tap in every
Modifier 2 layer (`Gyro | …` and `Steering | …`) is a deliberate "clear to
Base" gesture. It removes every layer, including the stateful `Gyro` and
`Steering`.

See: [Vocabulary](Layout%20Vocabulary.md#terms) ·
[Cleanup scopes](Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) ·
[Steering per-layer exits](../findings/2026-09-30-steering-lean/CLEANUP-AUDIT.md#per-layer-exit-review)

## 2. Placement

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R101 | Every layer lifetime uses `add_layer` and `remove_layer`. Never `hold_layer` | Base's LB chord adds `L1: Modifier 0`, and the modifier's own LB Release removes it | Author, 2026-09-30 | Not checked yet | — | Still to migrate, not accepted: five `hold_layer` commands in each layout add `LTP: Arrow Keys` and `RTP: Mouse Buttons` |
| R102 | Never switch action sets (`CHANGE_PRESET`). A mode is a layer on Base | `Gyro` and `Steering` are layers; each layout has one action set, Base | Author, 2026-09-30 | Not checked yet | — | None |
| R103 | A new layer is appended to the end of `action_layers` as `Preset_<max+1>`, so no existing runtime ID shifts | `Steering \| LS: Fallback Hold` was appended as the last layer in 90.11 | Since the July layouts | `test_stateful_transitions.test_layers_keep_their_positions` (part); `test_steering_fallback_hold.test_the_hold_is_appended` (part) | — | None |
| R104 | The `action_layers` order equals the `Preset_` numeric order, the preset blocks follow it, and the preset ids run from 0 | In the July layout the two orders disagreed, and Split Stick and `Gyro Off Ramp Up` swapped on a fresh load | Found 2026-07-11 | `test_neptune_recovery.test_command_budget_and_runtime_reference_order` | — | None |
| R105 | Layer titles are unique, and a layout is edited in `{{Base::Title}}` form | Two layers titled `DEPRECATED` both resolved to the last one's ID | Since the converter | Not checked yet | — | None |
| R106 | A layer exists in both layouts. In the alternative, L1 and R1 become L2 and R2 | `L1: Modifier 0` is `L2: Modifier 0` in the alternative, on the trigger's soft pull | Since the two variants | Not checked yet | — | None |

Notes:

- **R101, R102:** see [runtime rules and existing conflicts](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).
- **R104:** otherwise a fresh load can swap layers.

See: [layout-prep skill](../.claude/skills/steam-layout-prep/SKILL.md) ·
[layer-duplicate skill](../.claude/skills/steam-layer-duplicate/SKILL.md) ·
[layer-order swap](../findings/2026-07-11-layer-order-swap/FINDINGS.md)

## 3. Activators

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R108 | Use only Regular, Chorded, Start, Release and Soft Press. Never Long Press or Double Press, in any group, active or not | A hold is a chord with a delay: `Menu Left: Entry Point` adds its Fn layer after 200 ms. A double tap is a window layer: `L1: Double Tap` | Author, 2026-09-30 | Budget audit: banned activators; `rtp_scroll` fix (part); `test_layout_hygiene.test_only_allowed_activation_types_in_any_bank` | — | None |
| R109 | An input has at most three command entries, counted across all activator types. Subcommands inside an entry don't count. A delayed-apply reset may be a 4th entry when it is the last one | Select in `Menu Left: Entry Point` has three: the hold chord, the reset and the Release. Select in `Menu Left: Escape` has four, with the cover's reset last | Author, 2026-09-27; the 4th entry on 2026-09-30 | Budget audit: entry budget; `test_layout_hygiene.test_only_second_press_cover_resets_use_a_last_fourth_entry` | — | None |
| R110 | In a new array the removals sit below the add, so they run first. An existing array keeps its order unless the order changes the result | `L1: Modifier 0`'s Release removes the modifier first and adds `L1: Double Tap` last, so the add is stored on top | Author, 2026-09-27 and 2026-09-30 | Not checked yet | — | None |
| R111 | On a D-pad-mode stick, an inverted edge never adds or removes a layer. One that only sends output is allowed, and mouse-mode sticks are not covered | Steering's stick modifiers end on the outer edge's Release. The WASD modifier is an inverted edge that only sends a key | Author, 2026-10-01 | Budget audit: inverted edges; `test_stateful_transitions.test_no_steering_layer_uses_an_inverted_edge` | — | None |
| R112 | Nothing depends on a chord handing over to another activator when the chord button is released | A chord beside a repeating Regular Press on one input doesn't hand over when the chord button goes up, so Steering's modifiers end on a Release instead | Author, 2026-10-01 | Not checked yet | — | None |

Notes:

- **R108:** build a hold as a chorded delay and a multi-tap as a layer window.
- **R109:** the limit exists because Steam's desktop configuration drops every
  entry after the third. The 4th-entry reset must be **last** so it's the one
  that gets dropped.
- **R110:** subcommand arrays run **bottom to top**. A stick-touch Release is
  the one shape that stores its add last so it runs first (R123).
- **R111:** an inverted edge isn't caught reliably on a D-pad-mode stick. Use
  a normal outer edge and its Release. The ramp-up's Soft Press exits, on a
  mouse-mode stick, work.
  - The Budget audit fails on it since 90.10 (`inverted_edges`). Steering's
    left-stick layers were the only violators and now end on the edge's
    Release.
- **R112:** chords latch (author's test, 2026-10-01). A bind stays in the
  chord until its own button is released.

See: [Allowed activators](Steam%20Input%20JSON%20Structure.md#allowed-activation-types) ·
[Entry budget](Steam%20Input%20JSON%20Structure.md#command-entry-budget) ·
[Execution order](Steam%20Input%20JSON%20Structure.md#binding-execution-order) ·
[binding-order skill](../.claude/skills/steam-binding-order/SKILL.md)

## 4. Entry

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R113 | A layer command that must fire on an input already held when its layer is added has Hold to Repeat, or the next layer is added in the same array | The Menu Entry Points' stick-edge chord repeats every 50 ms, so a stick guard lands when the stick is already out. Modifier 0's chord adds both covers and Modifier 2 in one array | Author, 2026-09-29 | `test_neptune_held_inputs.test_layers_added_over_a_held_input_repeat_their_next_add`; `test_neptune_held_inputs.test_no_held_input_violations_remain` | — | None |
| R114 | A layer command that must fire after a removal has Hold to Repeat | Base is never added, so its menu, modifier, stick-touch and right-stick-edge entries all repeat | Author, 2026-09-29 | `test_neptune_held_inputs.test_base_entries_repeat_so_exposure_after_a_removal_is_guaranteed`; `test_neptune_held_inputs.test_threshold_exits_that_change_layers_repeat` | — | None |
| R115 | A delay that exists so a command fires over a held input is kept, and a delayed add gets no repeat for that purpose | The 5 ms delay from `Gyro Off Ramp Up` to `Turning Ramp Up 0`: the stick is already past its threshold when the layer appears | Author, 2026-09-29 | `test_neptune_held_inputs.test_ramp_handoffs_keep_their_start_delays` | — | None |

Notes:

- **R113:** when a layer is added, its immediate layer command **doesn't fire
  on an input that's already held**.
- **R113 covers the layer API only** (author, 2026-10-01): `add_layer`,
  `remove_layer` and `hold_layer`. It doesn't cover key or mouse outputs. The
  author's experience is that an output does fire on an already-held input
  when its layer is added; this hasn't been tested on the Deck in isolation.
- **R115:** delayed applies do fire on a held input.
- **R114:** how removals affect held inputs is unverified.

See: [Held inputs](Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes) ·
[Held-input audit](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md)

## 5. Stick-touch release

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R116 | Every layer binds both stick-touch Releases itself. Only a cover-type layer may inherit them. `Gyro` inherits Base's, and the `LST` and `RST` helpers bind only their own stick | `L1: Modifier 0` binds both. `L1: Temp Cursor Gyro`, a cover-type layer, inherits them | Author, 2026-09-30 | Not checked yet | — | None |
| R117 | A stick-touch Release clears only its own side's three helpers: the `LST` or `RST` `Entry Point`, `Tap Cover` and `Temporary Gyro`. It never removes `Gyro`, the other stick's helpers or an owner that is still valid | In `L1: Modifier 0` the left-stick touch Release removes the three `LST` layers and leaves `Gyro`, the `RST` layers and R1's layers | Author, 2026-09-30 | `test_neptune_recovery.test_transitions_block_the_stick_edges_and_touch_only_clears_the_trio` (part) | — | None |
| R118 | An Always On window's stick-touch Release removes the window first, then that side's helpers. The `LST` and `RST` windows bind no Release on their own stick | `L1: Double Tap`'s left-stick touch Release stores the window's removal last, so it runs first | Author, 2026-09-30 | `test_double_tap_windows.test_stick_touch_release_removes_the_window_first_then_the_side_trio` | — | None |

**R116.** A cover-type layer is a lightweight layer that is only
ever added on top of another layer. There's no strict definition yet; it's a
judgment call. Current cover-type layers:
- the Tap Covers and the Double Tap Covers, including the steering
  `LS: Tap Cover` and `LS: Double Tap Cover` (since 90.7) and
  `Menu Buttons: Tap Cover` (since 90.10). The two menu stick guards are not
  covers: they bind both stick touches with their own recovery
- Temp Cursor Gyro
- `Gyro Off Ramp Up`. Its only delay is a 5 ms right-stick handoff to
  `Turning Ramp Up 0`, which is a threshold handoff rather than a hold, so a
  thumb release has nothing to complete.

**R118.** Each Double Tap window's touch release removes the window, then
that side's trio (the self-removal is stored last, so it runs first). The
LST/RST windows' own stick has no release: touching it again is the
second-touch transition, which also removes the window first
([§9](#9-always-on-layers)).

- **R117:** the LS touch release removes `LST: Entry Point`, `LST: Tap Cover`
  and `LST: Temporary Gyro`. The RS touch release removes the same three RST
  layers.
- Defining any activator on a stick's touch input **replaces the whole
  inherited input**, so include that input's guarded recovery as well.
- **R116:** every other layer defines both touch inputs itself, even if a
  trace suggests inheritance would work. That includes stateful layers,
  owners, helpers and ramp layers.
- **The two cases R116 leaves out** (author, 2026-09-30):
  - `Gyro` is the base stateful layer and always sits directly on Base, so it
    inherits Base's touch inputs.
  - `LST/RST: Entry Point`, `Tap Cover` and `Temporary Gyro` are the layers
    that the release removes. They need a release only on their own stick,
    not the opposite one.
- A static check on 2026-09-30 found every other layer compliant after
  [`Transition Set 0` was patched](../findings/2026-09-30-touch-release-rule/README.md).

See: [Touch-release rule](Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release) ·
[Steering cleanup audit](../findings/2026-09-30-steering-lean/CLEANUP-AUDIT.md#findings-and-changes)

## 6. Hold, tap and double tap

This section is one concept. The chorded delay, the repeating reset, the
release into a Double Tap window, the Double Tap Cover, and the stick-touch
release all belong to the same recipe. **Any layer that adds a delay or a
double tap must implement the whole recipe, or record which part it leaves
out and why.** Recorded so far: the steering double tap
([deviations](../findings/2026-09-30-steering-lean/README.md#recipe-deviations-dod-6)).

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R119 | A layer that adds a delay or a double tap implements the whole recipe below, or records which part it leaves out and why | The Menu Left chain: `Menu Left: Entry Point`, `Menu Left: Double Tap`, `Menu Left: Escape`, `Menu Left: Double Tap Cover` | Author, 2026-09-30 | Not checked yet | — | The Steering double tap leaves parts out; recorded in its [deviations](../findings/2026-09-30-steering-lean/README.md#recipe-deviations-dod-6) |
| R120 | Every delayed `add_layer` has a reset on the same input: a Regular Press that removes only that target, with Hold to Repeat and `interruptable: 0` | Select in `Menu Left: Entry Point` adds the Fn layer after 200 ms and removes it every 250 ms | Author's workaround, since the July layout | `cover_resets` fix (part); `test_neptune_cursor.test_delayed_cursor_reset_is_scoped_and_replaced_by_upper_inputs` (part) | — | RTP touch has no reset, because a repeated removal breaks trackball momentum (author) |
| R121 | The reset's interval is longer than its delay, so a healthy add lands before the first reset | The pairs in use are 150/200, 200/250, 250/300 and 300/350 ms | Convention | Not checked yet | — | None |
| R122 | The hold target binds the parent's primary input, so the reset can't remove the target once it has landed | `L1: Temp Cursor Gyro` and `L1: Tap Cover` both bind LB, which ends `L1: Modifier 0`'s 300 ms add and its 350 ms reset | Author, 2026-09-29 | `test_neptune_cursor.test_overlays_retire_primary_timers_but_only_normal_covers_replace_touches` (part) | — | None |
| R123 | A stick-touch Release completes the pending add first, then clears that side's helpers. Once the add has landed, a cover's touch Release only cleans up | In `L1: Modifier 0` the right-stick touch Release adds `L1: Temp Cursor Gyro` (stored last, so it runs first), then removes the three `RST` layers | Author, 2026-09-29 | `test_neptune_cursor.test_only_primary_delay_and_touch_completion_enter_cursor` (part) | — | None |
| R124 | A cover's Release doesn't reopen the window | Hold L1, press A, let go of L1: `L1: Tap Cover`'s Release clears the modifier and opens no `L1: Double Tap` | Author | `test_modifier_rocking.test_a_used_bumper_exits_cleanly_without_a_window` (part) | — | None |
| R125 | A delay that sends an output, a haptic or an exit, or that routes by direction, is not completed on thumb release | Steering's 1.5 s hold exit doesn't fire when a thumb lifts off the stick | Author, 2026-09-30 | Not checked yet | — | None |
| R126 | While a delay is pending, unrelated layer changes that could reach it are blocked, because a removal restarts the delay | `L1!R1: Modifier 2`'s cleanup wasn't widened to the other Modifier 2 order: extra removals could restart the 200 ms combined-cover delay | Author | Not checked yet | — | None |

### The bug it works around: the stuck delay

If a delayed `add_layer` is interrupted before its delay finishes, it can fail
to fire on the **next** entry. The hold then silently stops working. The
author observed that a **repeated `remove_layer` of the same target restarts
the delay**, so the add fires again. This is the author's runtime observation,
not a confirmed Steam internal. On 2026-09-30 the author clarified the
reset outcome: restart and wait 300 ms in the discussed case, not cancellation.
Other configured delay values remain distinct.
([Interrupted applies](Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies) ·
[R1 tap-cover findings](../findings/2026-09-27-r1-tap-cover/FINDINGS.md))

### The recipe, using Menu Left as the example

These are the actual default-layout bindings. The modifiers follow the same
shape: L1 → `L1: Double Tap` → `L1: Scroll Down` → `L1: Double Tap Cover`.

```
Base: Select press
  └─ Menu Left: Entry Point ............ (1) parent: tap or hold?
       ├─ hold 200 ms ──► Menu Left: Fn Layer          (hold result)
       └─ release ──────► Menu Left: Double Tap ....... (2) Always On window, 150 ms
            ├─ timeout ──► window removes itself        (single tap)
            └─ 2nd press ► Menu Left: Escape .......... (3) second-press layer
                 ├─ hold 150 ms ► Menu Left: Double Tap Cover  (4) cover
                 │                 └─ release ► remove Escape + cover (done)
                 └─ release ──► Menu Left: Double Tap again (tap chain)
```

**(1) Parent layer.** The primary button uses three entries:

| Entry | Settings | Does |
|---|---|---|
| Chord (hold) | `delay_start: 200` | Adds the hold target, `Menu Left: Fn Layer` |
| Regular Press (**reset**) | `hold_repeats: 1`, `repeat_rate: 250`, `interruptable: 0` | Removes **only** that same target, which restarts a stuck delay |
| Release (tap) | — | Removes the parent, then adds `Menu Left: Double Tap` **last** |

Both stick-touch releases in the parent **complete the pending hold first**
(add `Fn Layer`, last in storage), then clear the LST or RST trio. So a thumb
lift finishes the hold early instead of resetting its timer. See [§5](#5-stick-touch-release).

**(2) Double Tap window.** It's an Always On layer, so all of [§9](#9-always-on-layers)
applies:

- It times out by removing only itself after 150 ms (200 ms for LST and RST).
- It can send a delayed single-tap output. Menu Left sends Escape at 50 ms.
- A second press removes the window **first**, then adds the second-press
  layer.
- Every other layer change is blocked while it's active.

**(3) Second-press layer.** The button holds or repeats its output (the
Escape key, or the scroll wheel for modifiers). A 150 ms chord adds the Double
Tap Cover, and a 200 ms repeating reset protects it. The reset is a **4th
entry, placed last**; see the
[change record](../findings/2026-09-30-second-press-cover-reset/README.md).
Release goes back into a Double Tap window, which is what lets rapid taps
chain. Its touch releases add the cover first, then clear the trio.

**(4) Double Tap Cover.** It keeps the output, and its release cleans up
without opening another window. It has no Always On action.

### Checks for this recipe

- [ ] **Reset present (R120).** Every delayed `add_layer` has a Regular Press on the
      same input in the parent that removes only that target, with
      `hold_repeats: 1` and `interruptable: 0`. If there's no reset, record the
      exception. The known deliberate exception is RTP touch, because the
      reset breaks trackball momentum. If the input is already full, add the
      reset as a **last** 4th entry ([§3](#3-activators)).

      See the [reset coverage table](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md#coverage-at-a-glance).
- [ ] **Reset interval is longer than the delay (R121)**, so a healthy apply lands
      before the first reset. The current pairs are 150/200, 200/250, 250/300
      and 300/350. The +50 ms spacing is a convention, not a proven formula.
- [ ] **The hold target overrides the parent's primary input (R122).** That is what
      stops the reset from removing the target once it has been applied. The
      reset must never strip a cover that has already been applied.
      ([cursor follow-up](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#delayed-apply-reset-follow-up))
- [ ] **The release adds the window last**, and the window's second press
      removes the window first ([§9](#9-always-on-layers)).
- [ ] **Touch releases complete the pending add (R123)**, then clear the trio. Once the
      add completes, covers get cleanup-only touch releases so a thumb lift
      can't re-add the parent's target.
- [ ] **The cover's release doesn't reopen the window (R124).**
- [ ] **A delayed apply needs no repeat (R115)** to fire over a held input. Keep short
      delays such as 5 ms ([Held inputs](Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes)).

### Other delays

- **Output, haptic, exit timer or direction-dependent routing (R125):** don't
  complete these on thumb release. Direction routing keeps its direction
  condition.
- **Any pending timer (R126):** block unrelated layer changes while it's
  pending, because removals reset timers.

See: [Complete delayed applies](Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release) ·
[Blocking for timers](Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) ·
[Reset audit](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md) ·
[Steering delay handling](../findings/2026-09-30-steering-lean/CLEANUP-AUDIT.md#delay-classification-and-ordering)

## 7. Cleanup

Four words these rules use ([Vocabulary](Layout%20Vocabulary.md#terms)):

- A **cleanup function** is the backup exit for a stuck layer: a repeating
  removal that fires when the layer's button is no longer held.
- Its **guard** is the buttons whose chords suppress it.
- A layer's **keeper** is what keeps it alive: usually the button whose
  Release removes it, otherwise a thumb on a stick, a timer or a mode.
- A layer's **exit** is a Release that removes it.

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R127 | The guard is the boundary: a cleanup function removes only layers its guard's buttons keep alive, and all of a layer's cleanup functions have the same guard | `L1: Modifier 0`'s cleanup functions are guarded by LB and remove LB's layers. `L1!R1: Modifier 2`'s are guarded by LB and RB and remove both sides' | Author, 2026-10-02 | Cleanup audit: outside the guard; Cleanup audit: guard mismatch; `cleanup_lists` fix | — | None |
| R128 | Below: a cleanup function removes, in one step, every layer under its host that the guard's buttons keep alive. It stops at Base, a stateful layer, a window, or a layer another button keeps alive | `Menu Left: Fn Layer`'s cleanup function also removes `Menu Left: Entry Point` under it | Author, 2026-10-02 | Cleanup audit: left below; `cleanup_lists` fix | — | None |
| R129 | Above: a cleanup function removes a layer on top of its host that the same buttons keep alive and that leaves the cleanup's input alone | `L1: Tap Cover` binds three inputs. On the others `L1: Modifier 0`'s cleanup function still fires, so it removes the cover | Author, 2026-10-02 | Cleanup audit: left above; `cleanup_lists` fix | — | None |
| R130 | A layer that binds an input with a cleanup function below carries that cleanup on the input, with the same guard | `L1: Tap Cover` binds both stick touches, so it carries the modifier's cleanup function there | Author, 2026-10-02 | Cleanup audit: hidden cleanup; `cleanup_lists` fix | — | None |
| R131 | A cleanup function never removes a stateful layer, a stick-touch helper, a window, or a layer another button keeps alive | `L1: Modifier 0`'s cleanup function leaves `Gyro`, the `RST` helpers, `L1: Double Tap` and R1's layers | Author, 2026-10-02 | Cleanup audit: outside the guard; `cleanup_lists` fix | — | None |
| R132 | A cleanup function, a Release and the Modifier 2 quick tap list only layers that can be on the stack with their host. A deliberate clear keeps its whole list, and a stick-touch Release keeps its three helpers | `L1: Modifier 0`'s cleanup function doesn't list `Gyro \| L1: Modifier 0`: the two are never on the stack together | Author, 2026-10-02 | Cleanup audit: never there; `cleanup_lists` fix | — | None |
| R133 | A cleanup function has the guarded recovery shape: on one input, a chord for each valid owner beside an interruptible Regular Press with Hold to Repeat that removes the layers | Right-stick touch in `L1: Modifier 0`: an empty chord with LB, and a repeating Regular Press that removes LB's layers when LB isn't held | Standardised 2026-09-28 | `test_neptune_recovery.test_all_guarded_removals_repeat_and_rtp_stays_out_of_ls_scope` | — | None |
| R134 | A stick edge gets a cleanup function only where the layer needs one: the left edge costs the WASD modifier and the right edge costs ramp-up | `L1: Modifier 0` has one on both stick edges; `RTP: Entry Point` was left without a left-edge one | Author, 2026-09-28 | Not checked yet | — | None |
| R135 | A cancellation removes only itself, repeats, is uninterruptible and has no guard | Each of `L1: Temp Cursor Gyro`'s 15 cancel inputs removes only the cursor, which exposes the modifier's own binding | Author, 2026-10-02 | `test_neptune_cursor.test_cursor_cancellations_remove_only_themselves_and_leave_outputs_to_parent` | — | None |
| R136 | Hidden exit: a layer that can land on top of another may not cover an exit on what keeps the lower layer alive, unless it removes the lower layer there | In the first 90.11 build a Start tap put a menu Double Tap window over `Steering \| LS: Fallback Hold`. Recentring inside the window missed the layer's Release and left it on | Author, 2026-10-02 | Cleanup audit: hidden exit | — | Touchpad layers are set aside for now, 68 cases on 90.13 (author, 2026-10-02; [to-do](../todos.md#steering)) |
| R138 | The held button's layer owns its combos. No layer exists only to protect a second button that is still held | Hold Start, hold LB for F10, lift Start: LB falls through to Base and becomes the L1 modifier. `Menu Left: Backspace` and `Menu Right: Enter` were removed in 90.9 | Author, 2026-10-01 | `menu_combo_keys` fix (part); `test_fixes.test_overlays_are_gone_and_nothing_references_them` (part) | — | None |

Notes:

- **Normal exit:** it fits the layer's type ([§1](#1-layer-type)) and removes
  only the state it owns.
- **R133, stuck-layer recovery (owners only):** put an owner-held chord and an
  interruptible, repeating Regular Press removal on the inputs likely to be
  used next. Guard against every valid owner.
- **R134, stick edges:** add edge cleanup only where it's needed.
- **R127 to R132** are the six cleanup rules (author, 2026-10-02): every
  layer takes care of itself and what is below it, and of what is above it if
  it has that responsibility.
  [Full text and measurements](../findings/2026-10-02-cleanup-boundaries/README.md#the-rules) ·
  the Cleanup audit checks them ([§10](#10-ship-it)) and the `cleanup_lists`
  fix applies them.
- **R132, other layers' lists:** add a new layer's removal only to a list
  whose host can be on the stack with it. Never add it to the other side's
  lists or to a persistent mode's lists.
- **R136** is the Cleanup audit's seventh check since 2026-10-02
  ([record](../findings/2026-10-02-hidden-exit/README.md)). The stack is
  taken after the whole binding that added the upper layer has run. A layer
  that covers an exit which isn't on the keeper is listed as information: the
  keeper's exit still works. No fix resolves a finding; either the upper
  layer is kept from landing, or it removes the lower layer on that input.
- **Inheritance and blocking** have their own section, [§8](#8-inheritance-and-blocking).

See: [Cleanup Functions](Cleanup%20Functions.md) (draft definitions of every kind) ·
[Stuck layers](Steam%20Input%20JSON%20Structure.md#stuck-layers-and-why-there-is-so-much-cleanup) ·
[Guarded recovery](Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape) ·
[Overlay ownership](Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership) ·
[Stick edges](Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions) ·
[Cleanup audit](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md)

## 8. Inheritance and blocking

Steam overrides **whole inputs**. Any input a layer doesn't define comes from
whatever is below it. That can be any layer, including a stale one left behind
by a missed release, not only the usual parent. So a layer inherits more than
its JSON shows, and a change to a lower layer reaches upper layers whose JSON
never changed.

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R139 | Inheritance is the default. An ordinary layer isn't required to block an input because the layers below would give it different bindings; the Flow audit lists such an input for review | The left-pad key layers inherit the L1 and R1 modifier entries from Base | Author, 2026-10-01 | Not checked yet | — | Accepted: the two Steering stick modifiers inherit the drivers from the W and S layers, by design |
| R140 | Window rule. Under a layer with an Always On action, an input the layer leaves open is handled when any stack can put a layer command under it: replaced with the keybind when only one is possible, cleared otherwise. A stack whose binding is only a layer command adds no keybind | Every default window replaces the trigger edge with Base's mouse button: `Gyro Off Ramp Up` can sit under the window, and its edge only removes it | Author, 2026-09-30, restated 2026-10-01 | Window audit: open routes; Window audit: unchecked window; `window_routes` fix | — | None |
| R141 | A block clears the input by default and replaces it only where the use is obvious. It targets only routes that change layers, and it is never a removal | The modifier Double Tap windows replace the bumper, which normally adds a layer, with the scroll wheel | Author, 2026-09-30 | `window_routes` fix (part) | — | None |
| R137 | Temporary guards: no layer is added over a temporary guard; only removals happen there | In `Steering \| LS: Entry Guard` and `Steering \| LS: Fallback Hold`, Start and Select type Tab and Escape, so no menu layer can land and hide their Releases | Author, 2026-10-02 | `test_steering_fallback_hold.test_no_menu_layer_lands_on_the_hold_or_the_entry_guard` (part) | — | None |
| R142 | Menu layers keep gyro disabled and the right-stick edge blocked | `Menu Left: Escape` has a disabled gyro group and an empty right-stick edge | Author, 2026-09-28 | `test_neptune_gyro.test_gyro_sources_only_override_owned_properties_or_explicitly_disable` (part) | — | None |
| R143 | Base owns the gyro response. An activation layer sets only its selector fields, and the cursor only its four response settings | `Gyro` sets `layer: 1` and its activation selector. `L1: Temp Cursor Gyro` sets precision speed 750 and three haptic and threshold values | From the July reference | `test_neptune_gyro.test_gyro_sources_only_override_owned_properties_or_explicitly_disable`; `test_neptune_cursor.test_cursor_profile_preserves_sensitivity_and_owner_activation` | — | None |
| R144 | A cover never outlives its owners, never sits below its owner, and inherits nothing through a layer between it and its owner | `L1: Tap Cover` sits directly on `L1: Modifier 0` and is removed with it | Author-approved plan, 2026-09-30 | Flow audit: cover check | — | None |
| R145 | A chain of adding bindings reaches every layer. A layer that only `hold_layer` adds is out of scope: the chains don't follow `hold_layer` (R101) | `L1: Double Tap` is reached from Base through `L1: Modifier 0`'s Release. `LTP: Arrow Keys` and `RTP: Mouse Buttons` are the two out of scope | 2026-10-01; `hold_layer` left out by the author | Flow audit: coverage | — | None |

### When to block

Inheritance is the default, and usually it's what we want. Overlays inherit
their owner's recovery and gameplay output. Block only while something must
not be disturbed:

| While… | Block | Because |
|---|---|---|
| An Always On layer is active | Every inherited layer command | Historical crash ([§9](#9-always-on-layers)) |
| A delayed add is pending | Inherited removals that could reset its timer | Removals restart delays ([§6](#6-hold-tap-and-double-tap)) |
| A valid owner is held | The owner's own stale-state recovery, using a guard chord | Recovery would tear down a live interaction ([§7](#7-cleanup)) |
| A menu interaction is active | Gameplay routes such as gyro and RS edge | The author's deliberate menu suppression (R142) |
| A temporary guard is on | Every bind that adds a layer | A layer added over it could hide its exit (R137) |

### What a block looks like

**R141 (author, 2026-09-30): clear first, and replace only where the context
makes it obvious.**

- **Block only the routes that change layers.** Target an inherited input only
  if its binding contains `add_layer`, `remove_layer` or `hold_layer`, directly
  or through a mode shift. Key, mouse and movement output pass through.
- **Default: clear the input.** That means the GUI's cleared binding, which is
  assumed to be saved as `controller_action empty_binding`. When in doubt,
  clear.
- **Replace when there's an obvious contextual use.** Give the input a static
  output with no layer command. For example, the modifier Double Tap windows
  replace the bumper, which normally adds a layer, with the scroll wheel, so
  the button stays useful during the short window.
- **Never block with a removal.** A `remove_layer` is itself a layer change. It
  resets timers, and inside an Always On layer it's exactly what's forbidden.
- **Other block shapes:**
  - a conditional empty chord blocks only while its selector is held
  - a disabled source quiets the whole trackpad or gyro, including its output
  - a group in a different source mode blocks the whole source
    ([below](#a-source-mode-change-blocks-inheritance))
- **Watch the whole-input override.** Clearing or replacing an input drops
  *all* of its inherited activators. Record what's lost; for example, blocking
  LS edge loses the WASD modifier.
- **These are not blocks:**
  - an omitted input
  - an empty `inputs` object
  - an `inactive` group
  - an `empty_binding` inside an array that also has real actions
- **Existing empty bindings may be protecting a timer.** Find out what one
  protects before you replace it.

### A source-mode change blocks inheritance

**Author rule, 2026-10-01: inputs don't inherit between modes.** When a layer
binds a source in a different mode from the layers below it (for example a
`dpad` trackpad over Base's `absolute_mouse` pad), none of that source's
lower inputs carry over, including inputs the upper group leaves unbound. The
mode change is itself the block; no extra clear is needed.

Example: the RTP Double Tap window's right pad is in `dpad` mode and binds no
`touch`. Base's mouse-mode `touch` (which adds `RTP: Entry Point`) does not
fire inside the window, so a second touch only fires the window's own regions.

Both [audit_inheritance.py](../audit_inheritance.py) (blocked kind
`mode replaced`) and [audit_flow_inheritance.py](../audit_flow_inheritance.py)
apply this rule.

### How to check it

**R140 (author, 2026-09-30, restated by the author on 2026-10-01). It applies
to a layer with an Always On action, and to no other layer:**

1. Trace every stack the layer can be applied on.
2. For each input the layer leaves open, look at the bindings it could
   inherit from those stacks.
3. If one of them is a layer command, the layer must handle that input for
   its whole lifetime.
4. How:
   - **Clear** it if more than one keybind is possible underneath. A
     hard-coded replacement would be wrong in some stack.
   - **Replace** it with the keybind if there is only one, for example always
     E or always middle mouse.
   - **A stack whose binding is only a layer command adds no keybind**
     (author, 2026-10-01). Under `Gyro Off Ramp Up` a trigger soft pull only
     removes that layer, so the one keybind is Base's mouse button and the
     window keeps it. Until 90.9 the audit counted that stack as a second,
     empty keybind and cleared the input.
   - If no stack gives a keybind, clear it.

If none of the bindings it could inherit is a layer command, the input is
left alone, even when the keybinds differ between stacks. An ordinary layer
inherits by default (R139); it is never required to block an input because
the layers below would give it different bindings.

The **Window audit** ([audit_inheritance.py](../audit_inheritance.py)) checks
this rule. The **Flow audit**
([audit_flow_inheritance.py](../audit_flow_inheritance.py)) runs the cover
check ([§5](#5-stick-touch-release)), checks that a chain reaches every
layer, and lists inherited bindings that differ between stacks as
information. Until 2026-10-01 it failed on those for every layer, which
misread step 4 as a rule of its own. Both audits build their stacks from the
same backward chains and run in the build audit ([§10](#10-ship-it)):

```bash
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_inheritance.py <layout> --entries "Menu Left: Double Tap"   # who adds it, what they remove first
python3 audit_layer.py <layout> --layer "Menu Left: Fn Layer"             # below, above, inherited, exits
```

For one layer, [audit_layer.py](../audit_layer.py) prints what can be below
and above it, each inherited input with the layer it comes from, and what
each of its exits removes against what can be present. The exits lists are
for review against [§7](#7-cleanup); they aren't a check.

1. **It builds the stacks backwards** (since 2026-10-01,
   [chains.py](../steam_layout/chains.py)). It starts at the layer and asks
   which bindings add it, then which add those layers, back to Base. Each
   chain gives one stack, and applies the whole binding, so a parent that
   removes itself isn't underneath.
   - A step only counts if its layer answers that input on the stack so far.
   - Between two steps a cover may lift (a removal-only binding), and one
     other layer may arrive.
   - **Bystanders:** any other layer stays underneath if it leaves the
     chain's inputs alone and the chain doesn't remove it. This is how
     `Gyro Off Ramp Up` ends up under a bumper window.
   - There is no depth cap and no config, so the Steering layers are reached
     like any other. Every Always On layer is audited automatically.
   - Chords are ignored (author, 2026-10-01): every adding binding is
     followed. That can add a stack that can't happen, never drop one that
     can. Missed releases, `hold_layer` and three families overlapping are
     not covered.
2. **A window no stack reaches fails** as "not checked". Each open route is
   printed with the bindings that built its stack.
3. **It finds the routes.** For each input the layer doesn't define, the
   topmost lower binding in each stack is the effective one. If it changes
   layers, directly or through a mode shift, that's a route. Inputs the layer
   clears, replaces or disables count as blocked.
4. **It recommends the block.** `blocks_needed` says replace (with the exact
   activators) or clear, following the rule above.
   [window_routes.py](../steam_layout/fixes/window_routes.py)
   applies the recommendations to the Always On windows during the install.
5. **Exceptions go in the [exceptions register](#exceptions-register):**
   `allow` with a reason, or `todo` while it awaits the author.
   [traced_stacks.json](../traced_stacks.json) can still add stacks the
   chains can't reach. An undecided `open` route fails the check.
   A different source mode above the definer is a block, not a route
   ([below](#a-source-mode-change-blocks-inheritance)).
6. **The test enforces it.** [test_audit_inheritance.py](../tests/test_audit_inheritance.py)
   fails when a change opens an undecided route or breaks saturation in the
   working layouts.

See: [Inheritance review](Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes) ·
[Blocking for timers](Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) ·
[Blocking audit: types](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md#types-of-blocking-in-use) ·
[Blocking audit: inherited routes](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md#inherited-route-review-and-remaining-uncertainty) ·
[Cursor self-removal inheritance](../findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md)

## 9. Always On layers

This section applies to any layer with an `always_on_action`, which currently
means the nine Double Tap windows.

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R146 | Entry: every other layer change runs first, and the Always On layer is added last | `L1: Modifier 0`'s Release removes the modifier, then adds `L1: Double Tap` | Author, documented 2026-09-28 | `test_neptune_recovery.test_timed_windows_block_both_edges_and_preserve_ordered_boundaries` | — | None |
| R147 | Timeout: an Always On layer's timed action removes only itself | `Menu Left: Double Tap` removes itself after 150 ms | Author, documented 2026-09-28 | `test_neptune_recovery.test_timed_windows_block_both_edges_and_preserve_ordered_boundaries` (part) | — | None |
| R148 | Early exit: the Always On layer is removed first, then the other changes run | `L1: Double Tap`'s second press removes the window, then adds `L1: Scroll Down` | Author, documented 2026-09-28 | `test_neptune_recovery.test_timed_windows_block_both_edges_and_preserve_ordered_boundaries`; `test_double_tap_windows.test_stick_touch_release_removes_the_window_first_then_the_side_trio` | — | None |
| R149 | Both trackpads stay off the layer API during every window. `RTP: Double Tap` keeps its own D-pad pad for the second tap | In `L1: Double Tap` a left-pad swipe types Escape, Enter, Tab or Backspace directly, and the right pad stays the mouse with click and touch cleared | Author, 2026-09-30 | `window_pads` fix; `test_double_tap_windows.test_left_pad_swipes_send_keys_without_the_layer_api`; `test_double_tap_windows.test_right_pad_stays_the_mouse_with_click_and_touch_cleared` | — | None |

While a window is active, every inherited layer command is blocked (R140,
[§8](#8-inheritance-and-blocking)).

**R149, trackpads (author, 2026-09-30):**
- **Left pad:** the swipes send their keys directly: back is Escape, forward is
  Enter, up is Tab, down is Backspace. They don't add the key layers. Click
  and touch are cleared.
- **Right pad:** stays the mouse, so the cursor keeps moving. Click and touch
  are cleared, and the mouse feel inherits from Base. RTP Double Tap keeps its
  own D-pad selection pad, with `click` cleared and no touch bind (see below).

See the [change record](../findings/2026-09-30-double-tap-pad-blocks/README.md).

**Current coverage of rule 2** (derived stacks, depth 5, 2026-09-30): there
are no open routes in any of the seven windows in either layout. The derived
stacks found routes that the earlier hand-traced stacks missed. Most are now
cleared, and one is a deliberate exception
([change record](../findings/2026-09-30-derived-window-blocks/README.md)):
- **Trigger edges, all nine default windows:** `Gyro Off Ramp Up` can sit
  under any window, and its edge removes it. The only keybind underneath is
  Base's left or right mouse button, so since 90.10 the edge is replaced
  with it. It was cleared from 90.6 to 90.9.
- **Right-pad `touch`, RTP Double Tap: blocked by the mode change** (author,
  2026-10-01). The window's D-pad-mode pad is its own second-tap selection: a
  second tap north or south goes to Circular Scroll, and anywhere else leaves
  the window and stays in mouse mode. Base's mouse-mode touch doesn't inherit
  into the dpad-mode pad ([mode rule](#a-source-mode-change-blocks-inheritance)),
  so no touch bind is needed. The former `allow` decision was retired.
- **The four back buttons, RTP Double Tap:** the Fn layers can be underneath
  if you hold a menu button and quick-tap the right pad.
- **Since 90.10** ([record](../findings/2026-10-01-stateful-transitions/README.md)):
  - **Left-stick up and down, the two menu windows:** Steering can sit under
    them, and its hold-exit clock would show through. Both are replaced with
    plain W and S.
  - **The two Steering windows** bind the stick and both drivers themselves.
    Derived on top, because a ramp layer can be added while in Steering: in
    the default layout the trigger edges keep the mouse buttons; in the
    alternative the bumpers keep the mouse buttons and the trigger clicks,
    which have no keybind underneath, are cleared.

**Stick clicks, face buttons and D-pad:** the derived stacks never put a layer
command under them in a window, so they stay inherited. `--untraced` still
lists which layers use them for layer commands, for review.

See: [Always On isolation](Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround) ·
[LS-edge blocks](../findings/2026-09-28-left-stick-recovery/CHANGES.md#always-on-isolation) ·
[Cursor blocks](../findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md#all-seven-always-on-windows)

## 10. Ship it

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R150 | The build audit is clean on every version | `python3 audit_build.py` runs the four audits on both layouts and exits 0 | Author | Build audit; `test_stateful_transitions.test_audits_are_clean` | — | None |
| R151 | A published layout has a reviewed description, one version bump per release, a regenerated VDF and a snapshot under `versions/neptune/<version>/`. Another version's snapshot never changes | 90.13: the title ends in `90.13`, and `versions/neptune/90.13/` holds both variants' JSON and VDF | Author, standing instruction | Not checked yet | — | None |
| R152 | The working layouts are a fixed point of the fix pipeline: running it again changes nothing | `python3 -m steam_layout.fixes neptune/*_latest.json --dry-run` reports nothing to change | Since the pipeline, 2026-09-30 | `test_fixes.test_working_layouts_are_a_fixed_point` | — | None |
| R153 | A layout has no dead groups: no plain-inactive slot and no unreferenced group | 90.6 pruned the four inactive stick-touch Double Press groups | 2026-09-30 | `dead_groups` fix; `test_layout_hygiene.test_no_unreferenced_groups_or_plain_inactive_slots` | — | None |
| R154 | The tests pass, a new invariant gets a new test, and the change is recorded in `findings/<date>-<slug>/` | 90.11 came with `tests/test_steering_fallback_hold.py` and `findings/2026-10-02-steering-fallback-hold/` | Author | Not checked yet | — | None |
| R155 | A Deck section is added to `manual-testing.md` for the change | 90.13 added "90.13: no turn assist in Steering", checks N1 to N4 | Author | Not checked yet | — | None |
| R164 | Before a release ships, its change report is written to the release's findings folder and read: every change in it is one somebody decided | The report for 90.13 shows `Steering` gaining an empty right-stick edge, which was decided, and the two Steering stick windows losing their trigger-edge mouse buttons, which the `window_routes` fix did on its own | Author, 2026-10-02 | Not checked yet | — | None |
| R156 | The working layouts are generated: they equal the current builder's output run through the fix pipeline. A hand edit there is lost on the next install | `neptune/*_latest.json` equals the output of `findings/2026-10-02-steering-fallback-hold/build_candidate.py`, apart from title and description | Since the 09-30 builder | `test_steering_fallback_hold.test_working_layouts_are_this_build` | — | None |

- [ ] **R150: the build audit is clean, on every version.** `python3 audit_build.py`
      runs the four audits below on both variants and exits 0 only when all
      pass. No version ships with a failing line.

      | Audit | Script | Clean means |
      |---|---|---|
      | Budget audit | `audit_command_budget.py` | Three entries per input, no banned activators, and no layer command on an inverted D-pad stick edge ([§3](#3-activators)) |
      | Window audit | `audit_inheritance.py` | No undecided layer command under an Always On window ([§8](#8-inheritance-and-blocking), [§9](#9-always-on-layers)) |
      | Flow audit | `audit_flow_inheritance.py` | A chain of adding bindings reaches every layer, and no cover finding is open ([§5](#5-stick-touch-release), [§8](#8-inheritance-and-blocking)) |
      | Cleanup audit | `audit_cleanups.py` | Every cleanup function and release follows the six cleanup rules, and no layer hides another's exit ([§7](#7-cleanup)) |

      What a clean build audit doesn't prove: it follows the intended flows,
      not every runtime interleaving, missed release or timer race. Those are
      what the Deck checks are for.
- [ ] **A new layer needs no declaration.** The audits pick it up from the
      layout. If no binding adds it, the Flow audit reports it as a coverage
      gap. Only two things go in
      [flow_config.json](../steam_layout/flow_config.json): a cover whose
      title doesn't end in a cover suffix, and an entry in the
      [exceptions register](#exceptions-register). An exception that no
      longer matches anything is reported as stale.
- [ ] **R164:** the change report is read. `python3 change_report.py --out findings/<date>-<slug>/`
      compares each working layout with its newest snapshot, layer by layer
      and input by input, and writes the result into the release's findings
      folder. A change nobody decided is looked at before the release ships.
- [ ] **R154:** the tests pass, and a new invariant gets a new test.
- [ ] **R154:** the change is recorded in `findings/<date>-<slug>/`.
- [ ] **R155:** a Deck section is added to [manual-testing.md](../manual-testing.md). It
      covers an input held across the change, a press inside the layer, and a
      release missed while the Steam menu is open.
- [ ] **R151:** the [layout-apply skill](../.claude/skills/steam-layout-apply/SKILL.md)
      has run: description, version bump, `to-ids`, VDF export and snapshot.

## 11. Stateful layers

This section applies only when a stateful layer is added or changed. The
structure is in [Stateful Layer Transitions](Stateful%20Layer%20Transitions.md).
It was agreed on 2026-10-01 and is built since 90.10; Deck validation is
pending.

The check is whether the transitions behave as that document says.
[test_stateful_transitions.py](../tests/test_stateful_transitions.py) asserts
it on the generated layouts, and is extended with every new stateful layer
until all four gestures are taken.

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R157 | A stateful layer is entered and left through a transition, by one of the four menu-plus-stick-click gestures. Stateful layers never add each other directly. `Gyro` is the one stateful layer outside this: the Modifier 2 Release toggles it | Start plus left-stick click enters `Steering`: the click's Release adds `Transition Set 1`, and that layer's Start Release adds `Steering` | Author, 2026-10-01 | `test_stateful_transitions.test_entry_point_clicks_release_into_their_transition`; `test_stateful_transitions.test_transition_menu_releases` | — | Steering's 1.5 s hold exit and the Modifier 2 clear leave without a transition (author, 2026-10-01) |
| R158 | Inside a stateful layer, any menu button plus any stick click clears it and everything above Base except `Gyro`. The layer has its own Entry Points for that | In `Steering`, both stick clicks in both of its Entry Points lead to `Transition Set 0`, the clear | Author, 2026-10-01 | `test_stateful_transitions.test_entry_point_clicks_release_into_their_transition` | — | None |
| R159 | The Modifier 2 clear removes every stateful layer and its helpers | In `Steering`, a quick tap of both bumpers clears to Base | Author, 2026-09-30 and 2026-10-01 | `test_steering_fallback_hold.test_only_steering_the_clears_and_the_hold_name_the_hold` (part) | — | Open since 2026-10-01: an older to-do keeps Gamepad through this clear ([to-do](../todos.md#global-stateful-behavior)) |
| R160 | No layer is entered from a transition: every input that would add a layer underneath is cleared | `Transition Set 1` clears both bumpers, so no modifier can be entered while it is on | Author, 2026-10-01 | `test_stateful_transitions.test_nothing_is_entered_from_a_transition` | — | None |
| R161 | Every menu Release in a transition beeps and gives a strong pulse | `Transition Set 1`'s Start Release has `haptic_intensity` 3, and its `add_layer` of `Steering` carries the beep flag | Author, 2026-10-02 | `test_stateful_transitions.test_every_transition_beeps_and_pulses_on_its_menu_release` | — | None |
| R162 | At entry a stateful layer has no Release and no delayed binding on Start or Select. A repeating press that adds its Entry Point is allowed | `Steering` adds its Entry Points with a repeating press, as Base does | Author, 2026-10-01 | `test_stateful_transitions.test_base_and_steering_add_their_entry_points_with_a_repeating_press` (part) | — | None |
| R163 | Entering a transition clears the whole stack first, keeping `Gyro`, and adds the transition last | The left-stick click Release in `Menu Right: Entry Point` removes every layer except `Gyro`, then adds `Transition Set 1` | Author, 2026-10-02 | `test_stateful_transitions.test_entry_point_clicks_release_into_their_transition` | — | None |

- [ ] **Gesture (R157).** The layer is entered by one of the four menu-plus-stick-click
      gestures, and the gesture map is updated.
- [ ] **Entry (R157, R163).** The Base Entry Point sends that click's Release to the right
      transition, and the transition's menu Release adds the layer.
- [ ] **Transition feedback (R161).** Every menu Release in a transition beeps and
      gives a high haptic pulse (author, 2026-10-02), entering or clearing:
      `haptic_intensity` 3 on the Release, and the beep flag on the stateful
      layer's `add_layer`, or on the transition's own removal when nothing
      is added. No on-screen notification.
- [ ] **Exit (R158).** Inside the layer, every one of the four gestures leads to the
      clear transition. The layer has Entry Points for that, added by its own
      menu press.
- [ ] **Fallback (R159).** The Modifier 2 clear removes the layer and its helpers.
- [ ] **Clean entry (R162).** At entry the layer has no Release or delayed binding on
      Start or Select. A repeating press that adds its Entry Point, like
      Base's, is allowed (author, 2026-10-01).
- [ ] **No layer is entered from a transition (R160).** Every layer-adding input
      underneath is blocked with an empty binding.
- [ ] **Recipes (R111, R112).** Nothing depends on a chord handing over when the chord
      button is released, or on an inverted edge of a D-pad stick adding or
      removing a layer ([§3](#3-activators)).
- [ ] **Test and Deck checklist (R154, R155)** are updated for the new layer.

**Exceptions (author, 2026-10-01):**
- `Gyro` is toggled by the Modifier 2 release and is left on by the clear.
- The Modifier 2 clear and Steering's W/S hold exit skip the transition.
- Stateful Cursor Gyro will also clear the way Temp Cursor Gyro does. An extra
  exit like these is allowed; the menu-plus-click clear and the Modifier 2
  clear are never dropped.
- The planned Menu stateful layer won't use this structure.

See: [Stateful Layer Transitions](Stateful%20Layer%20Transitions.md) ·
[brainstorm record](../plans/2026-10-01-stateful-layer-transitions.md) ·
[runtime rules](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30)

## Open questions

None. Deck validation is tracked in [manual testing](../manual-testing.md).
