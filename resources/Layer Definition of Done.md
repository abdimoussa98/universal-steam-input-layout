# Layer definition of done

**Status:** in use since 2026-09-30. The rule tables, the checks behind them
and the exceptions register were added on 2026-10-02, and since 2026-10-03
everything on this page is checked by a script or listed as not checked yet
([plan](../plans/2026-10-02-rule-registry.md)).

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
| 10 | [Ship it](#10-ship-it) | Audits, tests, scenarios, assumptions and publishing |
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
| Checked by | What fails when the rule is broken: an audit check (`Budget audit: banned activators`), a step of the fix pipeline (`` `cleanup_lists` fix ``) or a test (`` `test_file.test_name` ``), separated by `;`. "(part)" after one means it covers only some layers. `Scenario tests (part)` means the press-by-press scenarios that name the rule ([below](#checks-and-rules)); they are always "(part)", because they cover the sequences that are written down. **Not checked yet** means nothing fails |
| Rests on | The Steam assumptions the rule depends on, by ID, from [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md). A dash when it depends on none |
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

A **scenario test** is one press sequence run on both layouts by a press
simulator: hold this, tap that, wait, then say which layers are on the stack
and which keys went down ([scenario.py](../tests/scenario.py),
`tests/test_scenarios_*.py`). Each one names the rules it checks and the
assumptions its outcome rests on. A test fails when a rule's row and the
scenarios disagree about whether a scenario checks it
([test_scenario_registry.py](../tests/test_scenario_registry.py)).

```bash
python3 -m tests.scenario R133     # the scenarios that check one rule
python3 -m tests.scenario          # the assumptions that aren't verified, and what rests on each
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
| Owner | Modifiers, Menu Entry and Fn layers, the two menu stick guards, Scroll, Transition Sets, trackpad modes | What its guard's buttons keep alive, under it and on top of it (R127 to R129), and nothing that can't be on the stack with it (R132) |
| Overlay | Tap Covers, Double Tap Covers, Temp Cursor Gyro | Itself, or a local pair. The owner handles recovery when it gets stuck. Where it binds an input its owner has a cleanup on, it carries that cleanup (R130) |
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
| R101 | Every layer lifetime uses `add_layer` and `remove_layer`. Never `hold_layer` | Base's LB chord adds `L1: Modifier 0`, and the modifier's own LB Release removes it. The five `hold_layer` commands of 90.13, on the pad clicks, went in 90.14; 90.19 has four, by the exception | Author, 2026-09-30 | `test_layout_rules.test_hold_layer_is_used_only_where_the_register_says`; `test_pad_middle_click.test_no_hold_layer_is_left`; `test_pad_click_exits.test_no_hold_layer_came_back`; `test_pad_click_holds.test_only_the_four_final_pad_layers_hold_and_only_themselves` | — | Accepted since 90.19 (author, 2026-10-03): the four final pad click layers hold themselves on the click's Soft Press, with the inverted repeating removal as the backup |
| R102 | Never switch action sets (`CHANGE_PRESET`). A mode is a layer on Base | `Gyro` and `Steering` are layers; each layout has one action set, Base | Author, 2026-09-30 | `test_layout_rules.test_no_binding_switches_action_sets_and_there_is_one_set` | — | None |
| R103 | A new layer is appended to the end of `action_layers` as `Preset_<max+1>`, so no existing runtime ID shifts | `Steering \| LS: Fallback Hold` was appended as the last layer in 90.11. Deleting a layer is the other way an ID shifts: 90.33 deleted that layer from the middle of the list, the 18 layers after it moved up by one, and the presets were renumbered in a row; every command is written by title and converted. 90.64 put the whole list in a new order the same way (author, 2026-10-12): the two ramp layers, the five stateful layers, then the other layers grouped by parent (Base, Gyro, Steering, the menu layers Steering and Cursor Gyro share); 88 layers moved and every layer is bind for bind what it was | Since the July layouts | `test_stateful_transitions.test_layers_keep_their_positions` (part); `test_steering_fallback_hold.test_the_hold_is_appended` (part); `test_pad_middle_click.test_the_four_layers_are_appended` (part) | A23 | None |
| R104 | The `action_layers` order equals the `Preset_` numeric order, the preset blocks follow it, and the preset ids run from 0 | In the July layout the two orders disagreed, and Split Stick and `Gyro Off Ramp Up` swapped on a fresh load | Found 2026-07-11 | `test_neptune_recovery.test_command_budget_and_runtime_reference_order` | A22 | None |
| R105 | Layer titles are unique, and a layout is edited in `{{Base::Title}}` form | Two layers titled `DEPRECATED` both resolved to the last one's ID | Since the converter | `test_layout_rules.test_layer_titles_are_unique` (part) | — | None |
| R106 | A layer exists in both layouts. In the alternative, L1 and R1 become L2 and R2 | `L1: Modifier 0` is `L2: Modifier 0` in the alternative, on the trigger's soft pull | Since the two variants | `test_layout_rules.test_the_alternative_has_the_defaults_layers_with_l2_and_r2` | — | None |

Notes:

- **R101, R102:** see [runtime rules and existing conflicts](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).
- **R104:** otherwise a fresh load can swap layers.

See: [layout-prep skill](../skills/steam-layout-prep/SKILL.md) ·
[layer-duplicate skill](../skills/steam-layer-duplicate/SKILL.md) ·
[layer-order swap](../findings/2026-07-11-layer-order-swap/FINDINGS.md)

## 3. Activators

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R108 | Use only Regular, Chorded, Start, Release and Soft Press. Never Long Press or Double Press, in any group, active or not | A hold is a chord with a delay: `Menu Left: Entry Point` adds its Fn layer after 200 ms. A double tap is a window layer: `L1: Double Tap` | Author, 2026-09-30 | Budget audit: banned activators; `test_gamepad.test_only_gamepads_menu_buttons_use_a_long_or_double_press`; `rtp_scroll` fix (part); `test_layout_hygiene.test_only_allowed_activation_types_in_any_bank` | A20, A43, A44 | Start and Select in `Gamepad` have a Double Press and a Long Press each. Nothing can be added over that layer (R168) (author, 2026-10-03) |
| R109 | An input has at most three command entries, counted across all activator types. Subcommands inside an entry don't count. A delayed-apply reset may be a 4th entry when it is the last one | Select in `Menu Left: Entry Point` has three: the hold chord, the reset and the Release. Select in `Menu Left: Escape` has four, with the cover's reset last | Author, 2026-09-27; the 4th entry on 2026-09-30 | Budget audit: entry budget; `test_layout_hygiene.test_only_second_press_cover_resets_use_a_last_fourth_entry`; Scenario tests (part) | A21 | None |
| R110 | In a new array the removals sit below the add, so they run first. An existing array keeps its order unless the order changes the result | `L1: Modifier 0`'s Release removes the modifier first and adds `L1: Double Tap` last, so the add is stored on top | Author, 2026-09-27 and 2026-09-30 | Scenario tests (part) | A3, A4 | None |
| R111 | On a D-pad-mode stick, an inverted edge never adds or removes a layer. One that only sends output is allowed, and mouse-mode sticks are not covered | Steering's stick modifiers end on the outer edge's Release. The WASD modifier is an inverted edge that only sends a key | Author, 2026-10-01 | Budget audit: inverted edges; `test_stateful_transitions.test_no_steering_layer_uses_an_inverted_edge`; Scenario tests (part) | A8, A19, A38 | Fallback Guard's exact repeating inverted LS-edge chord adding Steering (author, 2026-10-07; 90.38), and Entry Guard's exact quiet Any-driver chord removing only itself (author, 2026-10-10; 90.44). The Budget audit matches registered commands/settings and the Entry Guard command's quiet flags; device behavior remains A54, unverified. In 90.53 and in 90.55 the left stick's edge of ten Steering layers carried one registered inverted chord each as the layer's cleanup function there (author, 2026-10-10); 90.56 put the press and its guard chord back (author, 2026-10-11) and those register entries went: the W and S layers, the two stick modifiers, `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover`, the two stick scroll layers and the two Steering Modifier 2 layers. 90.61 registers the same ten edges again, each chord with the list its press had on 90.58 (author, 2026-10-12). Since 90.63 the ring of those ten groups is inverted as well, so the chord runs at the rim with no driver held (author, 2026-10-12: "invert the left stick edge for the chorded inverted clean functions ... every where in steering except in entry steering guard"); the timers' Soft Presses on four of them do not follow the ring (A67) and the Budget audit reads them by their own setting. 90.65 took the ten chords and the ring's inversion out again (author, 2026-10-13); their register entries stay for the 90.61 to 90.64 builds, and only the Entry Guard's matches the working layout |
| R112 | Nothing depends on a chord handing over to another activator when the chord button is released | A chord beside a repeating Regular Press on one input doesn't hand over when the chord button goes up, so Steering's modifiers end on a Release instead | Author, 2026-10-01 | Not checked yet | A17 | None |

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
[binding-order skill](../skills/steam-binding-order/SKILL.md)

## 4. Entry

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R113 | A layer command that must fire on an input already held when its layer is added has Hold to Repeat, or the next layer is added in the same array | The Menu Entry Points' stick-edge chord repeats every 50 ms, so a stick guard lands when the stick is already out. Modifier 0's chord adds both covers and Modifier 2 in one array | Author, 2026-09-29 | `test_neptune_held_inputs.test_layers_added_over_a_held_input_repeat_their_next_add`; `test_neptune_held_inputs.test_no_held_input_violations_remain`; Scenario tests (part) | A5, A6 | None |
| R114 | A layer command that must fire after a removal has Hold to Repeat | Base is never added, so its menu, modifier, stick-touch and right-stick-edge entries all repeat | Author, 2026-09-29 | `test_neptune_held_inputs.test_base_entries_repeat_so_exposure_after_a_removal_is_guaranteed`; `test_neptune_held_inputs.test_threshold_exits_that_change_layers_repeat`; Scenario tests (part) | A9, A31 | None |
| R115 | A delay that exists so a command fires over a held input is kept, and a delayed add gets no repeat for that purpose | The 5 ms delay from `Gyro Off Ramp Up` to `Turning Ramp Up 0`: the stick is already past its threshold when the layer appears | Author, 2026-09-29 | `test_neptune_held_inputs.test_ramp_handoffs_keep_their_start_delays` | A5, A6 | None |

Notes:

- **R113:** when a layer is added, its immediate layer command **doesn't fire
  on an input that's already held**.
- **R113 covers the layer API only** (author, 2026-10-01): `add_layer`,
  `remove_layer` and `hold_layer`. It doesn't cover key or mouse outputs. The
  author's experience is that an output does fire on an already-held input
  when its layer is added. That is assumption A10: reported, and not yet
  verified in isolation.
- **R115:** delayed applies do fire on a held input.
- **R114:** how removals affect held inputs is unverified.

See: [Held inputs](Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes) ·
[Held-input audit](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md)

## 5. Stick-touch release

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R116 | Every layer binds both stick-touch Releases itself, covers included since 90.24 (R169). `Gyro`, `Cursor Gyro` and `Gyro Off Ramp Up` inherit them, and the `LST` and `RST` helpers bind only their own stick | `L1: Modifier 0` binds both. `L1: Temp Cursor Gyro`, a cover-type layer, inherited them until 90.23 and binds both since 90.24 | Author, 2026-09-30 | `test_tap_cover_stick_touches.test_the_cover_binds_both_stick_touches_itself` (part); Scenario tests (part) | A1 | None |
| R117 | A stick-touch Release clears only its own side's three helpers: the `LST` or `RST` `Entry Point`, `Tap Cover` and `Temporary Gyro`. It never removes `Gyro`, the other stick's helpers or an owner that is still valid | In `L1: Modifier 0` the left-stick touch Release removes the three `LST` layers and leaves `Gyro`, the `RST` layers and R1's layers | Author, 2026-09-30 | `test_neptune_recovery.test_transitions_have_a_cleanup_on_the_stick_edges_and_touches_and_the_release_only_clears_the_trio` (part); Scenario tests (part) | — | None |
| R118 | An Always On window's stick-touch Release removes the window first, then that side's helpers. The `LST` and `RST` windows bind no Release on their own stick | `L1: Double Tap`'s left-stick touch Release stores the window's removal last, so it runs first | Author, 2026-09-30 | `test_double_tap_windows.test_stick_touch_release_removes_the_window_first_then_the_side_trio` | A4 | None |

**R116.** A cover-type layer is a lightweight layer that is only
ever added on top of another layer. The audits recognise one by its title:
it ends in `: Tap Cover`, `: Double Tap Cover` or `: Temp Cursor Gyro`, or it
is `Gyro Off Ramp Up`; the `LST` and `RST` Tap Covers are helpers, not covers
([flow_config.json](../steam_layout/flow_config.json), `covers`). Whether a
new kind of layer counts is still a judgment call. Current cover-type layers:
- the Tap Covers and the Double Tap Covers, including the steering
  `LS: Tap Cover` and `LS: Double Tap Cover` (since 90.7). The two menu
  stick guards are not covers: they bind both stick touches with their own
  recovery. `Menu Buttons: Tap Cover` (since 90.10) is a cover by its title
  but binds both stick touches itself since 90.23, with the guards' recovery:
  a pad layer under it can change the right stick's mode, and then nothing
  was inherited
  ([record](../findings/2026-10-04-tap-cover-stick-touches/README.md))
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
  - `Gyro` inherits touch inputs from the stack below it. Ordinarily that is
    Base; since 90.44 it may be toggled back on above retained `Cursor Gyro`,
    which also inherits these touch inputs.
  - `LST/RST: Entry Point`, `Tap Cover` and `Temporary Gyro` are the layers
    that the release removes. They need a release only on their own stick,
    not the opposite one.
- **R169 ended the cover case** (author, 2026-10-04): a cover needs a cleanup
  function on both stick touches, so it binds them and restates the Release.
  90.24 did that for the ten covers that inherited
  ([record](../findings/2026-10-04-required-cleanups/README.md)). On a cover
  the Release only clears that side's three helpers: the owner's Release is
  what adds the cover. `Gyro Off Ramp Up` is a ramp layer and still inherits.
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
| R120 | Every delayed `add_layer` has a reset on the same input: a Regular Press that removes only that target, with Hold to Repeat and `interruptable: 0`. From 90.25 to 90.29 this included the Tap Cover of the stick and right-pad Entry Points; since 90.30 it doesn't (see the exception). Since 90.26 the 5 ms outer ring bind of the two Click Entry Points has one too, on the pad's touch and not on the ring (author, 2026-10-04). A reset on a pad's touch states `haptic_intensity` 0. A start delay owned by a stick direction misfires (author, 2026-10-10; A63). In 90.53 the hold timer of the two Steering stick modifiers and the cover timer of the two stick scroll layers sat on the drivers, chorded on the left stick's deflect. 90.54, built from 90.52, put the stick modifiers' hold timer on the left stick's edge, where it waits its full time (A64). Since 90.55 all four are a Soft Press on that edge, with its own threshold at the stick's deadzone (A65), as turn assist's ramp layers have on the right stick. In each the reset stays on the stick's direction; the author left its place open | Select in `Menu Left: Entry Point` adds the Fn layer after 200 ms and removes it every 250 ms. `RTP: Click Entry Point`'s touch removes `RTP: Mouse Buttons` every 55 ms. In 90.33 `Steering`'s up and down added the fallback guard after 100 ms with a reset at 150 ms; since 90.34 that add has no delay | Author's workaround, since the July layout | `cover_resets` fix (part); `test_neptune_cursor.test_delayed_cursor_reset_is_scoped_and_replaced_by_upper_inputs` (part); `test_standard_delays.test_the_click_entry_points_outer_bind_has_its_reset_on_the_touch` (part); `test_window_releases_and_tap_cover_resets.test_the_three_entry_points_touch_is_that_of_90_24` (part); Scenario tests (part) | A12, A63, A64, A65 | The Tap Cover's 150 ms delayed add in `LST: Entry Point`, `RST: Entry Point` and `RTP: Entry Point` has no reset, for now (author, 2026-10-04, 90.30): the author thinks the repeated removal stopped the menu buttons while a thumb was on a stick. Until 90.24 the pad's was the exception, for trackball momentum (A28) |
| R121 | The reset's configured interval is its delay plus 50 ms. This is intended to let the add land before the first repeat; it is not a runtime timing guarantee across layer changes (author, 2026-10-09). Since 90.26 no hold delay is over 200 ms (author, 2026-10-04); the ramp-up layers are left as they were. The reset also fires once as its layer lands on the held button (A6); nothing is there to remove yet | The pairs in use are 150/200 and 200/250 ms, 5/55 for the pad clicks' outer bind, and `Turning Ramp Up 0`'s 250/300. A first build of 90.26 had the delay plus 5 ms; the author took it back the same day | Convention; the 200 ms ceiling: author, 2026-10-04 | `test_layout_rules.test_a_reset_repeats_more_slowly_than_its_delay`; `test_standard_delays.test_every_reset_repeats_50_ms_after_its_delay`; Scenario tests (part) | A12 | None |
| R122 | The hold target binds the parent's primary input, so the reset can't remove the target once it has landed | `L1: Temp Cursor Gyro` and `L1: Tap Cover` both bind LB, which ends `L1: Modifier 0`'s 200 ms add and its 250 ms reset | Author, 2026-09-29 | `test_neptune_cursor.test_overlays_retire_primary_timers_but_only_normal_covers_replace_touches` (part); Scenario tests (part) | A12, A15 | None |
| R123 | A stick-touch Release completes the pending add first, then clears that side's helpers. Once the add has landed, a cover's touch Release only cleans up | In `L1: Modifier 0` the right-stick touch Release adds `L1: Temp Cursor Gyro` (stored last, so it runs first), then removes the three `RST` layers | Author, 2026-09-29 | `test_neptune_cursor.test_only_primary_delay_and_touch_completion_enter_cursor` (part); Scenario tests (part) | A4, A13 | None |
| R124 | A cover's Release doesn't reopen the window | Hold L1, press A, let go of L1: `L1: Tap Cover`'s Release clears the modifier and opens no `L1: Double Tap` | Author | `test_modifier_rocking.test_a_used_bumper_exits_cleanly_without_a_window` (part); Scenario tests (part) | A7 | None |
| R125 | A delay that sends an output, a haptic or an exit, or that routes by direction, is not completed on thumb release | Completing a pending layer add on thumb release does not copy delayed feedback or output. The ordinary modifier's 200 ms Temp Cursor Gyro add and touch-release completion are both silent since 90.47. Since 90.52 a thumb lifted inside a Steering stick window only closes it: the window's own 50 ms scroll is not completed on the lift | Author, 2026-09-30 | Scenario tests (part) | — | None |
| R126 | While a delay is pending, unrelated layer changes that could reach it are blocked, because removals can disturb the delay; a restart is not guaranteed | `L1!R1: Modifier 2`'s cleanup wasn't widened to the other Modifier 2 order: extra removals could restart the 200 ms combined-cover delay | Author | Not checked yet | A13 | None |
| R173 | A value in a layout is one the Steam editor can set: a start delay, an end delay or a repeat rate of at most 1000 ms, a D-pad outer ring radius from 10,000 to 32,000, and a D-pad layout from 0 to 3. A value from a calculation is checked against the slider before it is written | No delay or repeat rate is over 1000 ms; until 90.30 the fallback's exit was written as 1500 ms with a reset at 1550. The Steering layers state no radius; until 90.30 they stated 4915. `Steering`'s left stick states layout 0, four-way, since 90.34: the number was read from the Steam client | Author, 2026-10-04 | `test_layout_rules.test_every_value_is_one_the_editor_can_set` | — | None |

**Timing limit (author, 2026-10-09):** delays and repeat intervals must not
carry mission-critical behavior. Removal can accelerate held repeats; timer
resets are inconsistent; a following delay can appear immediate during rapid
add/remove transitions. The recipe and configured intervals below remain the
existing workaround, without a guarantee of their timing. See
[Delay Timers and Repeat Rates](Delay%20Timers%20and%20Repeat%20Rates.md).

### The bug it works around: the stuck delay

If a delayed `add_layer` is interrupted before its delay finishes, it can fail
to fire on the **next** entry. The hold then silently stops working. The
author observed that a **repeated `remove_layer` of the same target can restart
the delay**, allowing the add to fire again in those cases. This is the author's runtime observation,
not a confirmed Steam internal. On 2026-09-30 the author clarified the
reset outcome: restart and wait 300 ms in the discussed case, not cancellation.
Other configured delay values remain distinct. The 2026-10-09 observations
above limit this to an observed case, not a dependable reset rule.
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
      exception. Until 90.24 the known deliberate exception was RTP touch,
      because the reset broke trackball momentum (A28). From 90.25 to 90.29
      the stick and pad Entry Points had it; since 90.30 the three Tap Covers
      are the exception again, for now (author, 2026-10-04). On a pad's touch a
      reset states `haptic_intensity` 0. If the input is already full, add
      the reset as a **last** 4th entry ([§3](#3-activators)).

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
| R127 | The guard is the boundary: a cleanup function removes only layers its guard's buttons keep alive, and all of a layer's cleanup functions have the same guard | `L1: Modifier 0`'s cleanup functions are guarded by LB and remove LB's layers. `L1!R1: Modifier 2`'s are guarded by LB and RB and remove both sides' | Author, 2026-10-02 | Cleanup audit: outside the guard; Cleanup audit: guard mismatch; `cleanup_lists` fix; Scenario tests (part) | A30 | None |
| R128 | Below: a cleanup function removes, in one step, every layer under its host that the guard's buttons keep alive. It stops at Base, a stateful layer, a window, or a layer another button keeps alive | `Menu Left: Fn Layer`'s cleanup function also removes `Menu Left: Entry Point` under it | Author, 2026-10-02 | Cleanup audit: left below; `cleanup_lists` fix; Scenario tests (part) | — | None |
| R129 | Above: a cleanup function removes a layer on top of its host that the same buttons keep alive and that leaves the cleanup's input alone | `L1: Tap Cover` binds three inputs. On the others `L1: Modifier 0`'s cleanup function still fires, so it removes the cover | Author, 2026-10-02 | Cleanup audit: left above; `cleanup_lists` fix; Scenario tests (part) | — | None |
| R130 | A layer that binds an input with a cleanup function below carries that cleanup on the input, with the same guard. Left out: the layer's own input, the one whose press, hold and Release run the layer's sequence (as R171 leaves out a layer's own button). For a stick modifier that is its direction, in the modifier, its hold marker, its scroll layer and its cover, and in 90.53 and since 90.55 up and down in the W and S layers, where the sequence starts | `L1: Tap Cover` binds both stick touches, so it carries the modifier's cleanup function there | Author, 2026-10-02 | Cleanup audit: hidden cleanup; `cleanup_lists` fix; Scenario tests (part) | A1 | The own direction of the Steering stick layers, by the left-out clause, named in the register because the audit can't tell a stick layer's own direction: up in `Steering \| LS Up: Modifier 1` and `Steering \| LS Up: Scroll Up`, down in `Steering \| LS Down: Modifier 0` and `Steering \| LS Down: Scroll Down`, both in `Steering \| LS: Tap Cover` and `Steering \| LS: Double Tap Cover` (author, 2026-10-10; 90.51 had the two modifiers as a to-do, 90.52 follows the bumper lifecycle) |
| R131 | A cleanup function never removes a stateful layer, a stick-touch helper, a window, or a layer another button keeps alive | `L1: Modifier 0`'s cleanup function leaves `Gyro`, the `RST` helpers, `L1: Double Tap` and R1's layers | Author, 2026-10-02 | Cleanup audit: outside the guard; `cleanup_lists` fix; Scenario tests (part) | — | None |
| R132 | A cleanup function, a Release and the Modifier 2 quick tap list only layers that can be on the stack when their bind fires. That leaves out a layer that is never on the stack with the host, and, since 90.57, a layer that sits above the host and answers the bind's own input: while it is on, the host's bind does not run. A stick-touch Release keeps its three helpers (R123), a timer's reset names its target (R120), and a Release names its own layer's hold target. Until 90.57 a deliberate clear kept its whole list; since 90.58 it follows this rule too (R163) | `L1: Modifier 0`'s cleanup function doesn't list `Gyro \| L1: Modifier 0`: the two are never on the stack together. The W layer's two driver Releases don't list the Steering stick windows or the Modifier 2 layer over it: each binds the drivers itself, so with one of them on the W layer's Release never runs | Author, 2026-10-02; tightened 2026-10-12 | Cleanup audit: never there; `cleanup_lists` fix; `test_steering_fallback_guard.test_the_gyro_modifier_2_quick_tap_clears_to_base` (part); `test_scenarios_90_57.test_the_w_and_s_layers_name_no_layer_that_answers_the_same_driver` (part); `test_scenarios_90_57.test_the_gyro_modifier_2_releases_name_only_what_can_be_on_the_stack` (part); `test_scenarios_90_58.test_no_cleanup_function_names_a_layer_its_rules_do_not_ask_for`; `test_scenarios_90_58.test_every_bind_has_its_90_57_commands_less_some_removes_and_nothing_else_differs` (part); Scenario tests (part) | A1 | 90.58 applied both halves to every remove of the layout: 1,162 went in the default layout and 1,174 in the alternative, none added ([audit](../findings/2026-10-12-remove-list-audit/README.md), [record](../findings/2026-10-12-removes-that-never-take-a-layer-off/README.md)). One register entry keeps sixteen removes at the two Stateful Entry Points (a stick's Tap Cover and Temporary Gyro): the audit's chains follow no delayed add and call them never there, and on the simulator they were on the stack when the clear fired. Eight removes that a cleanup function's rules do not ask for stay: the right pad's two click layers come on by `hold_layer`, which neither the chains nor the simulator follow. The audit checks the first half only: whether the layer can be on the stack with the host. For cleanup functions a test states the second half since 90.58; inside the Cleanup audit the check would also run in the fix pipeline and change what earlier builders rebuild. A layer above the host that answers the same input is found bind by bind, with random walks; the test "the target binds the same input" alone marks about 2,250 removes a layout, more than 600 of them needed, because the target can also sit below its host ([record](../findings/2026-10-11-owner-release-audit/README.md#10-with-fewer-removes-is-anything-left-on)). Until 90.56 the Gyro Modifier 2 quick tap also removed the four Base modifiers, the other Gyro Modifier 2 layer, `Steering` and its guard, which are never on with it: it was the way to Base from the Steering fallback as well as from `Gyro`, and the July layout lists them too (author, 2026-10-04, 90.33). 90.57 took them out (author, 2026-10-12), and their two register entries end at 90.56 (`until`): the frozen builders of 90.43 to 90.56 still rebuild with them. In 90.31 and 90.32 `Steering \| LS: Fallback Hold`'s cleanup binds removed `Steering`, a stateful layer, which R131 forbids. The Cleanup audit keeps a removal the register names, also when it is outside the guard. A register entry can name a layer it holds with (`where`): the frozen builders read the same register, so the Fallback Hold's entry stays for them and the quick tap's applies only from 90.33 |
| R133 | A cleanup function has the guarded recovery shape: on one input, a chord for each valid owner beside an interruptible Regular Press with Hold to Repeat that removes the layers. The input's entries are stored in this order: the Regular Press, the chords, then a Release if it has one (author, 2026-10-06). A timer's Soft Press on the same input is stored after them (90.55). In 90.53 and 90.55 the left stick's edge of ten Steering layers held one chord with Invert Activation instead of the press and its guard; 90.56 took that back (author, 2026-10-11: "switch back to normal clean ups for all besides the steering entry guard"). 90.61 has the chord there again, built from 90.58 with the press's lists (author, 2026-10-12: "just use a single inverted chord that is repeating") | Right-stick touch in `L1: Modifier 0`: a repeating Regular Press that removes LB's layers when LB isn't held, an empty chord with LB, and the stick-touch Release. Until 90.35 the four menu Entry Points had the Release before the chord there, 109 inputs had the chord first, and the author suspects the first of those kept the Fn layer from coming while a thumb was on a stick | Standardised 2026-09-28; the order 2026-10-06 | `test_neptune_recovery.test_all_guarded_removals_repeat_and_rtp_stays_out_of_ls_scope`; `test_layout_rules.test_a_cleanup_input_stores_the_regular_press_then_the_guard_then_the_release`; Scenario tests (part) | A25, A27, A30, A52 | Since 90.61 the left stick's edge of ten Steering layers holds one repeating chord with Invert Activation on the layer's drivers in place of the Regular Press and its guard chord: the W and S layers, the two stick modifiers, `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover`, the two stick scroll layers and the two Steering Modifier 2 layers. For the open fault [`Steering` ends on a right stick touch with a bumper held](../findings/2026-10-12-steering-ends-on-a-stick-touch/README.md), where the press ran although its bumper was held (author, 2026-10-12). The exact chords are registered under R111. Since 90.63 the ring of those ten groups is inverted, so the chord runs where the press did: at the rim, with no driver held. That exception ends with 90.64: 90.65 has the Regular Press and its guard chord there again, on a normal ring, and the press starts 5 ms late (author, 2026-10-13: "back to the non inverted chord with interruptible regular press removals pattern ... a start delay of 5ms"; A68). The Cleanup audit reads a repeating, interruptible Regular Press of removes as a cleanup function with or without a start delay |
| R134 | A stick edge gets a cleanup function only where the layer needs one: the left edge costs the WASD modifier and the right edge costs ramp-up | `L1: Modifier 0` has one on both stick edges; `RTP: Entry Point` was left without a left-edge one | Author, 2026-09-28 | Retired, 2026-10-04: R170 replaces it. It says which layers need a cleanup function on a stick edge, where this rule left it to judgment | — | None |
| R135 | A cancellation removes only itself, repeats, is uninterruptible and has no guard | Each of `L1: Temp Cursor Gyro`'s 15 cancel inputs removes only the cursor, which exposes the modifier's own binding | Author, 2026-10-02 | `test_neptune_cursor.test_cursor_cancellations_remove_only_themselves_and_leave_outputs_to_parent`; `test_cursor_gyro.test_both_sticks_out_remove_only_the_layer`; Scenario tests (part) | A27 | None |
| R136 | Hidden exit: a layer that can land on top of another may not cover an exit on what keeps the lower layer alive, unless it removes the lower layer there | In the first 90.11 build a Start tap put a menu Double Tap window over `Steering \| LS: Fallback Hold`. Recentring inside the window missed the layer's Release and left it on | Author, 2026-10-02 | Cleanup audit: hidden exit; Cleanup audit: exit to review; Scenario tests (part) | — | Touchpad layers are set aside for now, 68 cases on 90.13, 71 on 90.15, 99 on 90.16, 125 on 90.29 and 87 on 90.30 (author, 2026-10-02; [to-do](../todos.md#steering)). Since 90.30 `RTP: Double Tap` carries the Release of Start, Select and the two modifier buttons: it removes the window, then the layers that button's pair can be holding. It names no Steering layer: a driver let go inside that window in `Steering` leaves its W or S layer, or a Steering Modifier 2 layer, on until a thumb touches a stick (found 2026-10-12; the author: "leave it") |
| R169 | Stick touches: every layer has a cleanup function on both stick touches, covers included. Left out: an Always On window, a stateful layer, a ramp layer and the six stick-touch helpers | `L1: Modifier 0` has one on both touches, guarded by LB. Until 90.23 `Menu Left: Double Tap Cover` bound neither touch and `Menu Left: Escape` only the Release; 90.24 gave both one | Author, 2026-10-04 | Cleanup audit: touch without cleanup; Scenario tests (part) | — | Since 90.43 Entry Guard keeps valid centered protection across either stick touch; its touch Releases clear only ordinary touch helpers. Exact R169 entries preserve the author’s first-push-until-release choice |
| R170 | Stick edges: a layer that binds or blocks a stick's edge has a cleanup function on that edge. A layer that binds or blocks a face button, a D-pad direction, Start, Select or a back button has one on both edges. Left out: an Always On window, a stateful layer and a ramp layer | `L1: Modifier 0` retypes the face buttons and has one on both edges. `RTP: Entry Point` binds only the right-stick edge, has one there, and leaves the left edge open. Until 90.23 the three transitions blocked both edges with an empty binding; since 90.24 each edge is a cleanup guarded by either menu button | Author, 2026-10-04 | Cleanup audit: edge without cleanup; Scenario tests (part) | — | Each menu stick guard handles only its own stick: the other stick's edge stays open, so the Entry Point's add of the other guard comes through. `Steering \| LS: Entry Guard` and `Steering \| LS: Fallback Hold` had none on the left-stick edge: that stick kept them on (author, 2026-10-04). Those historical bindings ended in 90.33; their entries stay for frozen builds. The restored 90.43 Entry Guard has precise exemptions on both edges: normal LS-edge Release disarms it, while RS movement must preserve first-push protection even at center. Since 90.44 a local inverted LS-edge chord additionally removes only the guard; it was written as running while either driver is held, and runs while none is (corrected 2026-10-10, A61). Through 90.37 the fallback guard bound no edge. In 90.38 its additive inverted return is covered by the stateful-layer exclusion |
| R171 | Buttons: every button a layer retypes or blocks carries a cleanup function on that button. The buttons are the face buttons, the D-pad, Start, Select, the back buttons, the bumpers, and each trigger's pull and full pull. A block with an empty binding counts as a retype. Left out: the layer's own button (its Release removes the layer), a button that removes the layer by cancellation (R135), an Always On window, a stateful layer and a ramp layer | `L1: Modifier 0` carries one on A; LB is its own button. Each button of `L1: Temp Cursor Gyro` removes the cursor, so it passes. Until 90.23 `L1: Scroll Down` retyped Start and Select without one; since 90.24 the key is in the guard chord and the cleanup is the Regular Press | Author, 2026-10-04 | Cleanup audit: button without cleanup; Scenario tests (part) | — | None |
| R174 | Inside `Steering`, letting go of one driver never leaves `Steering` itself as the top layer under the other. A Release that takes a driver's layer off while the other driver can be held adds that driver's layer in the same array, stored last so that it runs first, or leaves the held driver's layer on. Bare `Steering` answers a stick at the rim with its exit, and adds the held driver's layer back only at its next repeat | Since 90.62 the held driver's layer is left on: pressing L1 in the W layer adds the S layer and then `Steering \| R1!L1: Modifier 2` over it, as the bumper modifiers outside `Steering` do, and inside Modifier 2 R1's Release removes Modifier 2 and the W layer, L1's removes Modifier 2 and the S layer. From 90.57 to 90.61 R1's Release added the S layer there (the hand-over); W to S worked and S back to W did not (author, 2026-10-12). On 90.56 R1 let go there with the stick at the rim ended `Steering` although L1 was held | Author, 2026-10-12 | `test_scenarios_90_62.test_no_release_in_modifier_2_adds_a_layer`; `test_scenarios_90_62.test_the_second_drivers_press_adds_its_layer_and_then_modifier_2`; Scenario tests (part) | A4, A10, A37 | The two Steering stick windows, a to-do in the register: a driver let go inside one removes both driver layers, and `Steering` adds the held one back at its next repeat (author, 2026-10-12: "just dont touch the window for now and have it remove itself as today"). After a release of the second driver that never reached the Modifier 2 layer, the second driver's layer is left on with nobody holding it when the first is let go; it types nothing and goes at the next touch of a stick |
| R138 | The held button's layer owns its combos. No layer exists only to protect a second button that is still held | Hold Start, hold LB for F10, lift Start: LB falls through to Base and becomes the L1 modifier. `Menu Left: Backspace` and `Menu Right: Enter` were removed in 90.9 | Author, 2026-10-01 | `menu_combo_keys` fix (part); `test_fixes.test_overlays_are_gone_and_nothing_references_them` (part); Scenario tests (part) | A10 | None |

Notes:

- **Normal exit:** it fits the layer's type ([§1](#1-layer-type)) and removes
  only the state it owns.
- **R133, stuck-layer recovery (owners only):** put an owner-held chord and an
  interruptible, repeating Regular Press removal on the inputs likely to be
  used next. Guard against every valid owner.
  A chord requiring both a held driver and LS deflection does not protect
  that driver after the stick centers. Since 90.43 the LS Modifier 0/1
  fallback clears its modifier/cover only in that case; each W/S owner
  retains responsibility for its own missed-release cleanup.
- **R169 to R171** are the required cleanups (author, 2026-10-04): a layer
  has a cleanup function on both stick touches, on the stick edges, and on
  every button it retypes or blocks. They replace R134, which left the
  stick edges to judgment. The guard is the layer's own: the button that
  keeps it on, either menu button for the stick guards and the transitions,
  a driver for the Steering stick modifiers, and the left stick being out
  for Steering's fallback guard (until 90.32, the Entry Guard and the Fallback
  Hold).
  - The Cleanup audit reads each layer on its own
    ([required_cleanups.py](../steam_layout/required_cleanups.py)). A
    cleanup function counts when it is on that input and removes the layer
    itself. An input the author accepts without one is an exception to
    R169, R170 or R171 in the register.
  - A ramp layer is one that no button, thumb or stick keeps on: a
    cancellation or a return to centre ends it.
  - Not read: a group in another mode than the layer below also blocks an
    input (A2). That depends on the stack, so R136 covers it.
  - **90.24 applies them** to 174 inputs in the default layout and 196 in the
    alternative, with the author's five decisions
    ([record](../findings/2026-10-04-required-cleanups/README.md)).
- **R132, other layers' lists:** add a new layer's removal only to a list
  whose host can be on the stack with it. Never add it to the other side's
  lists or to a persistent mode's lists.
- **R136** is the Cleanup audit's seventh check since 2026-10-02
  ([record](../findings/2026-10-02-hidden-exit/README.md)). The stack is
  taken after the whole binding that added the upper layer has run. Since
  2026-10-03 "can land on top" also counts a **landing**: any adding binding
  that answers on a stack the chains visited, whichever layer of the stack it
  belongs to. Before that, a layer was only on top of another through its own
  chain or as one bystander, and the Fallback Hold over the menu second-press
  layers went unseen from 90.11 to 90.14
  ([record](../findings/2026-10-03-menu-second-press-keys/README.md#why-the-hidden-exit-check-missed-it)).
  Since 2026-10-04 the check reads the chain walk with **five extra presses**
  (author; six until 90.24): one layer's chain with up to five arrivals along it, every layer of
  every stack tested, and every stack one landing past them. A compiled engine
  does the walk, so the audit needs a C++ compiler. Before that the check
  tested one example stack for each pair of layers, and `Menu Buttons: Tap
  Cover` over a pad layer went unseen from 90.10 to 90.22
  ([record](../findings/2026-10-03-simultaneous-cap/README.md)); 90.23 fixed it.
  When a source mode change is what covers the exit, the pair names the first
  layer above that changed the mode, not the layer on top. A layer
  that covers an exit which isn't on the keeper is listed as information: the
  keeper's exit still works. When either layer of such a pair changed since
  the last snapshot it fails as "exit to review", until it is fixed or
  accepted in the register. No fix resolves a finding; either the upper
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
| R139 | Inheritance is the default: an ordinary layer isn't required to block an input because the layers below would give it different bindings. But such an input is read when it is new: on a layer that changed since the last snapshot, or that a changed layer feeds, it fails until it is fixed or accepted with a reason | The left-pad key layers inherit the L1 and R1 modifier entries from Base. In the first 90.11 build, two such inputs on the new `Steering \| LS: Fallback Hold` were the menu taps that could strand it. The 90.14 review found two more, on the menu second-press layers, fixed in 90.15 | Author, 2026-10-01; the review on changed layers 2026-10-02 | Flow audit: needs review; Scenario tests (part) | A1 | Accepted: the two Steering stick modifiers inherit the drivers from the W and S layers, by design. Cover layers aren't reviewed this way: the cover check judges them (R144). Read for 90.14 and accepted, not yet confirmed by the author: the pad layers, the left-pad key layers and the stick-touch helpers inherit L1 and R1 from Base or Gyro; the ramp layers their firing inputs; the menu layers the right-pad touch (historical through 90.37); Fn and the stick guards the stick clicks and the other stick's edge. In 90.38 Steering may inherit fallback's silent idempotent LS-edge return in the requested additive stack |
| R140 | Window rule. Under a layer with an Always On action, an input the layer leaves open is handled when any stack can put a layer command under it: replaced with the keybind when only one is possible, cleared otherwise. A stack whose binding is only a layer command adds no keybind | Every default window replaces the trigger edge with Base's mouse button: `Gyro Off Ramp Up` can sit under the window, and its edge only removes it | Author, 2026-09-30, restated 2026-10-01 | Window audit: open routes; Window audit: unchecked window; `window_routes` fix; Scenario tests (part) | A1, A2, A24, A26, A29 | None |
| R141 | A block clears the input by default and replaces it only where the use is obvious. It targets only routes that change layers, and it is never a removal | The modifier Double Tap windows replace the bumper, which normally adds a layer, with the scroll wheel | Author, 2026-09-30 | `window_routes` fix (part) | A13, A29 | None |
| R137 | Temporary guards: no layer is added over a temporary guard. A handoff removes the guard before adding its target so its Releases cannot be hidden | Since 90.43 `Steering \| LS: Entry Guard` protects the first movement. Drivers remove it before adding W/S; fresh menu Start Press removes it before adding an Entry Point. Pad-helper and ramp entries are blocked while it remains | Author, 2026-10-02, 2026-10-04, 2026-10-05 and 2026-10-09 | `test_steering_fallback_guard.test_the_guard_types_w_and_s_and_nothing_on_the_stick_ends_it` (part); `test_steering_fallback_guard.test_nothing_the_modifier_pair_brings_in_binds_the_left_sticks_up_or_down` (part); Scenario tests (part) | — | None |
| R142 | Menu layers keep gyro disabled and the right-stick edge blocked | `Menu Left: Escape` has a disabled gyro group and an empty right-stick edge | Author, 2026-09-28 | `test_neptune_gyro.test_gyro_sources_only_override_owned_properties_or_explicitly_disable` (part) | — | None |
| R143 | Base owns the gyro response. An activation layer sets only its selector fields, and the cursor only its four response settings | `Gyro` sets `layer: 1` and its activation selector. `L1: Temp Cursor Gyro` sets precision speed 750 and three haptic and threshold values | From the July reference | `test_neptune_gyro.test_gyro_sources_only_override_owned_properties_or_explicitly_disable`; `test_neptune_cursor.test_cursor_profile_preserves_sensitivity_and_owner_activation` | — | None |
| R144 | A cover never outlives its owners, never sits below its owner, and inherits nothing through a layer between it and its owner | `L1: Tap Cover` sits directly on `L1: Modifier 0` and is removed with it | Author-approved plan, 2026-09-30 | Flow audit: cover check | — | None |
| R145 | A chain of adding bindings reaches every layer, apart from explicitly registered dormant layers retained without an entry route. Report those separately; their raw bindings still receive Budget checks. A layer that only `hold_layer` adds is out of scope: the chains don't follow `hold_layer` (R101) | `L1: Double Tap` is reached from Base through `L1: Modifier 0`'s Release. In 90.42 the retained Fallback Guard was deliberately dormant; 90.43 reuses its slot as reachable Entry Guard | 2026-10-01; `hold_layer` left out by the author; dormant fallback retained for the narrower Steering exit change, 2026-10-09 | Flow audit: coverage | A2 | R145 dormant-layer entry in the exceptions register |

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

Both [audit_inheritance.py](../tools/audit_inheritance.py) (blocked kind
`mode replaced`) and [audit_flow_inheritance.py](../tools/audit_flow_inheritance.py)
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

The **Window audit** ([audit_inheritance.py](../tools/audit_inheritance.py)) checks
this rule. The **Flow audit**
([audit_flow_inheritance.py](../tools/audit_flow_inheritance.py)) runs the cover
check ([§5](#5-stick-touch-release)), checks that a chain reaches every
layer, and lists inherited bindings that differ between stacks ("varies" and
"review"). Until 2026-10-01 it failed on those for every layer, which
misread step 4 as a rule of its own. Since 2026-10-02 it fails on them only
where they are new (R139): on a layer that changed since the last snapshot,
or that a changed layer feeds. There each one is fixed, or accepted in the
[exceptions register](#exceptions-register) with a reason. Accepting isn't
blocking; the entry was read, and inheriting is what is wanted. Both audits build their stacks from the
same backward chains and run in the build audit ([§10](#10-ship-it)):

```bash
python3 -m tools.audit_inheritance neptune/single-set-default_hold-gyro_latest.json
python3 -m tools.audit_inheritance <layout> --entries "Menu Left: Double Tap"   # who adds it, what they remove first
python3 -m tools.audit_layer <layout> --layer "Menu Left: Fn Layer"             # below, above, inherited, exits
```

For one layer, [audit_layer.py](../tools/audit_layer.py) prints what can be below
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
   [traced_stacks.json](../steam_layout/traced_stacks.json) can still add stacks the
   chains can't reach. An undecided `open` route fails the check.
   A different source mode above the definer is a block, not a route
   ([below](#a-source-mode-change-blocks-inheritance)).
6. **The test enforces it.** [test_audit_inheritance.py](../tests/test_audit_inheritance.py)
   fails when a change opens an undecided route in the working layouts, or
   leaves a window that no stack reaches.

See: [Inheritance review](Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes) ·
[Blocking for timers](Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) ·
[Blocking audit: types](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md#types-of-blocking-in-use) ·
[Blocking audit: inherited routes](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md#inherited-route-review-and-remaining-uncertainty) ·
[Cursor self-removal inheritance](../findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md)

## 9. Always On layers

This section applies to any layer with an `always_on_action`, which currently
means the eleven Double Tap windows.

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R146 | Entry: every other layer change runs first, and the Always On layer is added last | `L1: Modifier 0`'s Release removes the modifier, then adds `L1: Double Tap` | Author, documented 2026-09-28 | `test_neptune_recovery.test_timed_windows_block_both_edges_and_preserve_ordered_boundaries`; Scenario tests (part) | A4, A24 | None |
| R147 | Timeout: an Always On layer's timed action removes only itself | `Menu Left: Double Tap` removes itself after 150 ms | Author, documented 2026-09-28 | `test_neptune_recovery.test_timed_windows_block_both_edges_and_preserve_ordered_boundaries` (part); Scenario tests (part) | A4, A24 | None |
| R148 | Early exit: the Always On layer is removed first, then the other changes run | `L1: Double Tap`'s second press removes the window, then adds `L1: Scroll Down` | Author, documented 2026-09-28 | `test_neptune_recovery.test_timed_windows_block_both_edges_and_preserve_ordered_boundaries`; `test_double_tap_windows.test_stick_touch_release_removes_the_window_first_then_the_side_trio`; Scenario tests (part) | A4, A24 | None |
| R149 | Neither trackpad adds a layer during a window: each pad input takes its known replacement (R172). `RTP: Double Tap` keeps its own D-pad pad for the second tap | In `L1: Double Tap` a left-pad swipe types Escape, Enter, Tab or Backspace directly, and the right pad stays the mouse with its click cleared and a touch Release | Author, 2026-09-30; the touch Release 2026-10-04 | `window_pads` fix; `test_double_tap_windows.test_left_pad_swipes_send_keys_without_the_layer_api`; `test_double_tap_windows.test_right_pad_stays_the_mouse_with_its_click_cleared_and_a_touch_release`; Scenario tests (part) | A24 | None |
| R172 | Known replacements. When a layer has to take a pad input off its layer command, it uses that input's one replacement, the same everywhere: the left pad's swipes type their four keys directly; both pad clicks are blocked; the right pad's touch, which has an Entry Point, follows the stick touches: no press bind, and a Release that removes the layer itself first and then the pad's own layers that can be under it | In `L1: Double Tap` the right pad's touch Release removes the window, `RTP: Entry Point`, `RTP: Tap Cover` and `RTP: Circular Scroll`. In `LST: Double Tap` it removes only the window: a thumb resting on the pad covers the stick touches, so no stick window opens over the pad's layers | Author, 2026-10-04 | `test_menu_chain_and_window_pads.test_a_windows_right_pad_touch_is_a_release_that_ends_the_window_first`; `test_menu_chain_and_window_pads.test_the_left_pad_and_the_clicks_keep_their_known_replacements`; Scenario tests (part) | A7 | None |

While a window is active, every inherited layer command is blocked (R140,
[§8](#8-inheritance-and-blocking)).

**R149 and R172, trackpads (author, 2026-09-30 and 2026-10-04).** The known
replacements, one per pad input, used wherever a layer takes that input off its
layer command:

| Pad input | In Base | Known replacement |
|---|---|---|
| Left pad, the four swipes | Add `Escape`, `Enter`, `Tab`, `Backspace` | Type the key directly: back is Escape, forward is Enter, up is Tab, down is Backspace |
| Left pad, click | Adds `LTP: Click Entry Point` | Blocked |
| Left pad, touch | Nothing | Cleared |
| Right pad, click | Adds `RTP: Click Entry Point` | Blocked |
| Right pad, touch | Adds `RTP: Entry Point` | The stick touches' pattern: no press bind, and a Release that removes the layer itself, then `RTP: Entry Point`, `RTP: Tap Cover` and `RTP: Circular Scroll` where they can be under it |

The right pad stays the mouse, so the cursor keeps moving, and the mouse feel
inherits from Base. RTP Double Tap keeps its own D-pad selection pad, with
`click` cleared and no touch bind (see below). Until 90.27 the right pad's
touch was cleared like the click; a thumb that lifted inside a window then left
the pad's Entry Point and Tap Cover on.

See the [change record](../findings/2026-09-30-double-tap-pad-blocks/README.md).

**Current coverage of R140:** the Window audit builds every stack from the
backward chains and finds no open route in any of the nine windows in either
layout, on every build. The derived stacks found routes that the earlier
hand-traced stacks missed
([change record](../findings/2026-09-30-derived-window-blocks/README.md)).
What the windows block today:
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
| R150 | The build audit is clean on every version | `python3 -m tools.audit_build` runs the four audits on both layouts and exits 0 | Author | Build audit; `test_stateful_transitions.test_audits_are_clean` | — | None |
| R151 | A published layout has a reviewed description, one version bump per release, a regenerated VDF and a snapshot under `versions/neptune/<version>/`. Another version's snapshot never changes | 90.13: the title ends in `90.13`, and `versions/neptune/90.13/` holds both variants' JSON and VDF | Author, standing instruction | `test_layout_rules.test_every_snapshot_holds_both_layouts_under_its_own_version` (part) | A33 | None |
| R152 | The working layouts are a fixed point of the fix pipeline: running it again changes nothing | `python3 -m steam_layout.fixes neptune/*_latest.json --dry-run` reports nothing to change | Since the pipeline, 2026-09-30 | `test_fixes.test_working_layouts_are_a_fixed_point` | — | None |
| R153 | A layout has no dead groups: no plain-inactive slot and no unreferenced group | 90.6 pruned the four inactive stick-touch Double Press groups | 2026-09-30 | `dead_groups` fix; `test_layout_hygiene.test_no_unreferenced_groups_or_plain_inactive_slots` | — | None |
| R154 | The tests pass, a new invariant gets a new test, and the change is recorded in `findings/<date>-<slug>/` | 90.11 came with `tests/test_steering_fallback_hold.py` and `findings/2026-10-02-steering-fallback-hold/` | Author | Not checked yet | — | None |
| R155 | A Deck section is added to `manual-testing.md` for the change | 90.13 added "90.13: no turn assist in Steering", checks N1 to N4 | Author | Retired, 2026-10-03: the Deck checklist is retired. Its press sequences are scenario tests (R165), and what Steam does is in the assumptions document (R166) | — | None |
| R165 | A layer that is new or changed has scenario tests for its press sequences: an input held across the change, a press inside the layer, and a release missed while the Steam menu is open | The 90.10 transitions have 18, in `tests/test_scenarios_90_10.py`: D6 holds a driver across a Steering window, T8 presses the other menu button before the Fn layer is up, and T4 leaves a transition by a missed release | Author, 2026-10-02: part C of the [plan](../plans/2026-10-02-rule-registry.md). The three kinds of sequence come from R155 | `test_scenario_registry.test_every_changed_layer_is_on_the_stack_in_a_scenario` (part) | — | None |
| R166 | A Steam behaviour that a rule, a design or a test depends on has a row in [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md): its status, whether the layout relies on it, one way to verify it, and what rests on it | A37 was written down when the press simulator had to choose one: a key stays down when the layer answering a held input changes and the new binding sends the same key | Author, 2026-10-02: part C of the [plan](../plans/2026-10-02-rule-registry.md) | `test_rule_registry.test_every_assumption_a_rule_rests_on_exists` (part); `test_rule_registry.test_rests_on_and_what_rests_on_it_agree` (part); `test_scenario_registry.test_the_rules_and_assumptions_a_scenario_names_exist` (part) | — | None |
| R167 | The release's record lists every assumption that isn't verified, with the rules and scenario tests that rest on it. A layer whose tests pass but rest on one is done, and listed | For 90.13 the list has 19 assumptions, and 40 of the 87 scenarios rest on one of them; A8, the stick edge's Release in a layer added with the stick out, carries nine | Author, 2026-10-02: "done, and listed" | Not checked yet | — | None |
| R164 | Before a release ships, its change report is written to the release's findings folder and read: every change in it is one somebody decided | The report for 90.13 shows `Steering` gaining an empty right-stick edge, which was decided, and the two Steering stick windows losing their trigger-edge mouse buttons, which the `window_routes` fix did on its own | Author, 2026-10-02 | Not checked yet | — | None |
| R156 | The working layouts are generated: they equal the current builder's output run through the fix pipeline. A hand edit there is lost on the next install | `neptune/*_latest.json` equals the output of the `build_candidate.py` in the findings folder of its own version (for 90.57, `findings/2026-10-12-driver-handover-and-fewer-removes/`), apart from title and description | Since the 09-30 builder | `test_steering_rtp_menu_chords.test_working_layouts_are_generated_including_stored_order` | — | None |

- [ ] **R150: the build audit is clean, on every version.** `python3 -m tools.audit_build`
      runs the four audits below on both variants and exits 0 only when all
      pass. No version ships with a failing line.

      | Audit | Script | Clean means |
      |---|---|---|
      | Budget audit | `audit_command_budget.py` | Three entries per input, no banned activators, and no layer command on an inverted D-pad stick edge ([§3](#3-activators)) |
      | Window audit | `audit_inheritance.py` | No undecided layer command under an Always On window ([§8](#8-inheritance-and-blocking), [§9](#9-always-on-layers)) |
      | Flow audit | `audit_flow_inheritance.py` | A chain of adding bindings reaches every layer, no cover finding is open, and no changed layer has an unread inherited input ([§5](#5-stick-touch-release), [§8](#8-inheritance-and-blocking)) |
      | Cleanup audit | `audit_cleanups.py` | Every cleanup function and release follows the six cleanup rules, no layer hides another's exit, and every layer has the cleanup functions R169 to R171 require ([§7](#7-cleanup)) |

      What a clean build audit doesn't prove: it follows the intended flows,
      not every runtime interleaving, missed release or timer race. The
      scenario tests below run the sequences somebody wrote down, and nothing
      runs the rest.
- [ ] **A new layer needs no declaration.** The audits pick it up from the
      layout. If no binding adds it, the Flow audit reports it as a coverage
      gap. Only two things go in
      [flow_config.json](../steam_layout/flow_config.json): a cover whose
      title doesn't end in a cover suffix, and an entry in the
      [exceptions register](#exceptions-register). An exception that no
      longer matches anything is reported as stale.
- [ ] **R164:** the change report is read. `python3 -m tools.change_report --out findings/<date>-<slug>/`
      compares each working layout with its newest snapshot, layer by layer
      and input by input, and writes the result into the release's findings
      folder. A change nobody decided is looked at before the release ships.
- [ ] **R154:** the tests pass, and a new invariant gets a new test.
- [ ] **R154:** the change is recorded in `findings/<date>-<slug>/`.
- [ ] **R165:** the new layer's press sequences are scenario tests, in a
      `tests/test_scenarios_*.py` file. They cover an input held across the
      change, a press inside the layer, and a release missed while the Steam
      menu is open. The check behind this rule is narrower: it fails while a
      layer that is new or changed since the newest snapshot is on the stack
      in no scenario. Whether the three kinds of sequence are there is read
      by a person.
- [ ] **R166:** every Steam behaviour the change depends on has a row in
      [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md), with
      what rests on it. A scenario names the assumptions its outcome rests on
      (`rests`), and one the layout must work either way under is run both
      ways (`either`). The tests fail on an ID that has no row; they can't
      tell that a behaviour was never written down.
- [ ] **R167:** the release's record lists the assumptions that aren't
      verified. `python3 -m tests.scenario --out findings/<date>-<slug>/`
      writes `unverified-assumptions.txt` there: each assumption with the
      rules and the scenarios that rest on it. A layer whose tests pass but
      rest on one of them is done, and listed (author, 2026-10-02).
- [ ] **R151:** the [layout-apply skill](../skills/steam-layout-apply/SKILL.md)
      has run: description, version bump, `to-ids`, VDF export and snapshot.

**What the checks don't prove.** A scenario test passes on a simulator that
does what the assumptions say Steam does. So it proves the layout's bindings
give the expected result for one written sequence, if those assumptions hold.
It doesn't cover a sequence nobody wrote, an interleaving of two inputs in the
same millisecond beyond the two orders it tries (A32), or a timer race. And it
says nothing about whether an assumption is true: each assumption has one
procedure for settling that, in its row, and its status changes only when
somebody has run it.

## 11. Stateful layers

This section applies only when a stateful layer is added or changed. The
structure is in [Stateful Layer Transitions](Stateful%20Layer%20Transitions.md).
It was agreed on 2026-10-01 and is built since 90.10. Its press sequences are
scenario tests ([test_scenarios_90_10.py](../tests/test_scenarios_90_10.py)).

The check is whether the transitions behave as that document says.
[test_stateful_transitions.py](../tests/test_stateful_transitions.py) asserts
it on the 90.10 build, [test_cursor_gyro.py](../tests/test_cursor_gyro.py) on
90.21 and [test_gamepad.py](../tests/test_gamepad.py) on 90.22, where all four
gestures are taken.

| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |
|---|---|---|---|---|---|---|
| R157 | A stateful layer is entered and left through a transition, by one of the four menu-plus-stick-click gestures. Stateful layers never add each other directly. `Gyro` is the one stateful layer outside this: the Modifier 2 Release toggles it | Start plus left-stick click enters `Steering`: the click's Release adds `Transition Set 1`, and that layer's Start Release adds `Steering` | Author, 2026-10-01 | `test_stateful_transitions.test_entry_point_clicks_release_into_their_transition`; `test_stateful_transitions.test_transition_menu_releases`; `test_cursor_gyro.test_select_in_the_cross_transition_adds_gyro_and_then_the_layer`; `test_gamepad.test_entry_point_clicks_lead_to_their_transition`; `test_gamepad.test_transition_menu_releases_and_their_feedback`; Scenario tests (part) | A7 | Gyro's Modifier 2 toggle bypasses transitions. Since 90.44 Steering survives its own Modifier 2 clear and Cursor Gyro survives all six Gyro/Steering release clears (author, 2026-10-10); since 90.57 the Steering Modifier 2 Release clears nothing but its own layer (R159). Steering's hold exit, from 90.11 to 90.32, is gone (author, 2026-10-04). Historically, from 90.35 through 90.41, `Steering` and its fallback guard normally swapped by adding the other before removing themselves (90.38 also permits the author-requested additive fallback edge return): on the device the guard's eight-way stick did not take effect over `Steering`'s four-way one (author, 2026-10-06; A51). That pair was entered and left as one stateful layer; the fallback was replaced by direct full-deflection Steering-family exits in 90.42, protected by Entry Guard since 90.43. So does `Cursor Gyro`'s both-sticks exit, and its entry also adds `Gyro` underneath (author, 2026-10-03). `Menu Keys` is entered by holding both menu buttons for 150 ms and has three exits of its own; only its menu-plus-click exit goes through the clear transition (author, 2026-10-03 and 2026-10-04) |
| R158 | Inside a stateful layer, any menu button plus any stick click clears it and everything above Base except `Gyro`. The layer has its own Entry Points for that | In `Steering` and in `Cursor Gyro`, both stick clicks in both `Stateful` Entry Points lead to `Transition Set 0`, the clear. The two layers share the pair since 90.21 | Author, 2026-10-01 | `test_stateful_transitions.test_entry_point_clicks_release_into_their_transition`; `test_cursor_gyro.test_every_entry_point_click_clears_the_layer_and_keeps_gyro`; `test_gamepad.test_a_stick_click_with_a_menu_button_held_enters_the_clear` (part); Scenario tests (part) | A45 | `Gamepad` has no Entry Points: a chord on each stick click, on Start or Select held, enters the clear transition at the click's press (2026-10-03). `Menu Keys` does the same, so that no Double Tap window can land on it (90.25, for the author to confirm) |
| R159 | The Modifier 2 quick tap toggles `Gyro` and removes no other stateful layer. Until 90.43 it was the clear to Base from every state | From Base it adds `Gyro`; in `Gyro`, and in `Cursor Gyro` with `Gyro` on, the four Gyro Modifier 2 Releases remove `Gyro` and their own helpers. In `Steering` the second driver's Release removes only its Modifier 2 layer since 90.57: `Steering`, `Gyro` and the first driver's layer stay | Author, 2026-09-30, 2026-10-01, 2026-10-04, 2026-10-10 and 2026-10-12 | `test_steering_fallback_guard.test_the_gyro_modifier_2_quick_tap_clears_to_base` (part); `test_steering_fallback_hold.test_only_steering_the_clears_and_the_hold_name_the_hold` (part); `test_cursor_gyro.test_the_gyro_modifier_2_quick_tap_also_removes_the_layer` (part); `test_scenarios_90_57.test_the_second_driver_has_one_release_with_one_remove_and_no_timer`; `test_scenarios_90_57.test_the_gyro_modifier_2_releases_name_only_what_can_be_on_the_stack`; Scenario tests (part) | — | The rule's history, kept in the register. Since 90.44 Steering survives its own Modifier 2 cleanup and Cursor Gyro survives every dual-driver release clear; dedicated stick/menu exits remain. Since 90.57 the Steering Modifier 2 Release is no clear at all (author, 2026-10-12: "I don't want to be cleared out of steering in mod 2"), and the same holds in `Cursor Gyro`: no Modifier 2 Release removes it, and inside it the quick tap only toggles `Gyro`. `Gamepad` is not left by the Modifier 2 quick tap: its bumpers and triggers are gamepad buttons (author, 2026-10-03). Nor is `Menu Keys`, which closes the modifier buttons (author, 2026-10-03) |
| R160 | No layer is entered from a transition: every input that would add a layer underneath is cleared | `Transition Set 1` clears both bumpers, so no modifier can be entered while it is on | Author, 2026-10-01 | `test_stateful_transitions.test_nothing_is_entered_from_a_transition`; `test_gamepad.test_nothing_is_entered_from_a_transition`; Scenario tests (part) | — | None |
| R161 | Every menu Release in a transition beeps and gives a low pulse (since 90.41), and shows no name on screen. So do a stateful layer's own exits and the `Menu Keys` entry. The beep is the second of a layer command's two flags; until 90.28 the layouts set the first, which shows the name, and stayed silent | `Transition Set 1`'s Start Release has `haptic_intensity` 1, and its `add_layer` of `Steering` ends in `0 1` | Author, 2026-10-02; the flag corrected 2026-10-04 | `test_quiet_resets_and_beeps.test_every_transition_and_every_stateful_exit_beeps_on_the_second_flag`; `test_steering_fallback_guard.test_the_gyro_modifier_2_quick_tap_clears_to_base` (part); `test_quiet_resets_and_beeps.test_menu_keys_is_entered_with_the_beep_and_the_pulse_from_both_chains`; `test_quiet_resets_and_beeps.test_no_layer_command_shows_a_name_without_a_beep`; `test_stateful_transitions.test_every_transition_beeps_and_pulses_on_its_menu_release`; `test_cursor_gyro.test_select_in_the_cross_transition_adds_gyro_and_then_the_layer` (part); `test_gamepad.test_transition_menu_releases_and_their_feedback`; Scenario tests (part) | A49 | None |
| R162 | At entry a stateful layer has no Release and no delayed binding on Start or Select. A repeating press that adds its Entry Point is allowed | `Steering` adds its Entry Points with a repeating press, as Base does | Author, 2026-10-01 | `test_stateful_transitions.test_base_and_steering_add_their_entry_points_with_a_repeating_press` (part); `test_cursor_gyro.test_its_menu_presses_add_the_stateful_entry_points_with_a_repeating_press` (part); Scenario tests (part) | — | `Gamepad`'s Start and Select have a Long Press. The commit is the menu button's own Release, so it can't be running at entry (2026-10-03) |
| R163 | Entering a transition clears every layer that can be on the stack there, keeping `Gyro`, and adds the transition last. Until 90.57 the clear named every layer but `Gyro`, 89 removes; since 90.58 it names the layers that were on the stack at least once when it fired, and those that could not be ruled out (R132). The same holds for the chords that enter `Gamepad` and `Menu Keys` and the ones that leave them: fourteen binds in all. A layer left on by something no press sequence produces is no longer wiped by entering a mode; it goes with its own cleanup function. A short clear can go stale when a layer is added, which a whole list could not: the walk test is the guard ([record](../findings/2026-10-12-removes-that-never-take-a-layer-off/README.md)) | The left-stick click Release in `Menu Right: Entry Point` removes the 27 layers that can be on the stack there, never `Gyro`, then adds `Transition Set 1` | Author, 2026-10-02 ("you should always clean everything below you that is possible"); cut to what is possible 2026-10-12 ("trim") | `test_stateful_transitions.test_entry_point_clicks_release_into_their_transition`; `test_gamepad.test_entry_point_clicks_lead_to_their_transition`; `test_gamepad.test_a_stick_click_with_a_menu_button_held_enters_the_clear`; `test_scenarios_90_58.test_a_clear_names_every_layer_that_is_on_the_stack_when_it_fires`; `test_scenarios_90_58.test_the_fourteen_clears_name_5_to_27_layers`; Scenario tests (part) | — | None |
| R168 | A layer whose inputs use a Long Press or a Double Press is closed: it binds every input that carries a layer command in the layers under it, and its only layer commands are its exit. So no layer can be added over it | `Gamepad` binds every input of Base and `Gyro`, and its only layer commands are the two stick-click chords that enter the clear transition | Author, 2026-10-03 | `test_gamepad.test_gamepad_is_closed`; Scenario tests (part) | A2, A43, A44 | None |

Since 90.41, all explicit enabled haptic intensity settings use **Low (1)**.
Explicit Off settings remain Off. Ordinary and Stateful Fn-layer adds have
their beep flag cleared; other mode-transition beeps remain as specified.
Since 90.43 each Gyro Modifier 2 quick clear requests only the Gyro-removal
beep. In 90.44 both Steering Modifier 2 clears retain Steering and lose their
Steering-removal beep; all six Gyro/Steering release clears retain Cursor Gyro.
Steering Modifier 0/1 releases, their automatic Double Tap completions, W/S
owned activators and W/S entry activators are explicitly haptic Off.

Since 90.57 the two-driver release order is built
([record](../findings/2026-10-12-driver-handover-and-fewer-removes/README.md)).
In a Steering Modifier 2 layer the second driver's Release removes that layer
and nothing else: no clear, no 200 ms timer, no cover, no bump. The first
driver's Release hands over to the other driver's layer (R174). The same
holds in `Cursor Gyro`: no Modifier 2 Release removes it, and inside it the
quick tap only toggles `Gyro`. So the Modifier 2 quick tap removes no
stateful layer but `Gyro` (R159).

- [ ] **Gesture (R157).** The layer is entered by one of the four menu-plus-stick-click
      gestures, and the gesture map is updated.
- [ ] **Entry (R157, R163).** The Base Entry Point sends that click's Release to the right
      transition, and the transition's menu Release adds the layer.
- [ ] **Transition feedback (R161).** Every menu Release in a transition beeps and
      gives a low haptic pulse (author, 2026-10-09, 90.41), entering or clearing:
      `haptic_intensity` 1 on the Release, and the beep flag on the stateful
      layer's `add_layer`, or on the transition's own removal when nothing
      is added. No on-screen notification: the command ends in `0 1`, the
      name flag and then the beep flag (A49).
- [ ] **Exit (R158).** Inside the layer, every one of the four gestures leads to the
      clear transition. The layer has Entry Points for that, added by its own
      menu press.
- [ ] **Modifier 2 (R159).** The Modifier 2 quick tap does not remove the
      layer. If the layer retypes the modifier buttons, a Release there that
      takes one's layer off under the other follows R174.
- [ ] **Clean entry (R162).** At entry the layer has no Release or delayed binding on
      Start or Select. A repeating press that adds its Entry Point, like
      Base's, is allowed (author, 2026-10-01).
- [ ] **No layer is entered from a transition (R160).** Every layer-adding input
      underneath is blocked with an empty binding.
- [ ] **Recipes (R111, R112).** Nothing depends on a chord handing over when the chord
      button is released, or on an inverted edge of a D-pad stick adding or
      removing a layer outside the exact registered exceptions ([§3](#3-activators)).
- [ ] **Closed layer (R168).** If the layer uses a Long Press or a Double Press, it
      binds every input that carries a layer command underneath, and its only
      layer commands are its exit. The R108 exception names its inputs.
- [ ] **Tests (R154, R165).** The layer has its own test file, like
      `test_gamepad.py`, and scenario tests.

**Exceptions (author, 2026-10-01 and 2026-10-03):**
- `Gyro` is toggled by the Modifier 2 release and is left on by the clear.
- Gyro's Modifier 2 toggle and Steering's full up/down clear skip the transition.
  Steering's historical W/S hold exit ended in 90.33. Since 90.44 Steering
  survives its own Modifier 2 cleanup and Cursor Gyro survives all six
  Gyro/Steering Modifier 2 release clears. Since 90.57 the Steering Modifier 2
  Release is no clear: four release clears are left, the two drivers in each
  Gyro Modifier 2 layer, and they remove no stateful layer but `Gyro`.
- `Cursor Gyro` also ends when both sticks are pushed out, as Temp Cursor
  Gyro does, and its entry adds `Gyro` underneath. An extra exit like these
  is allowed; the menu-plus-click clear is never dropped.
- `Gamepad` is not left by the Modifier 2 clear, has no Entry Points (a chord
  on each stick click enters the clear), and has a Long Press and a Double
  Press on Start and Select. All three are in the
  [exceptions register](#exceptions-register).
- `Menu Keys`, the menu stateful layer (90.25), doesn't use this structure: both menu buttons held for 200 ms enter it (150 ms in 90.25).

See: [Stateful Layer Transitions](Stateful%20Layer%20Transitions.md) ·
[brainstorm record](../plans/2026-10-01-stateful-layer-transitions.md) ·
[runtime rules](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30)

## Open questions

None. The Steam behaviours that are still unverified are in
[Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md), each with
what rests on it.
