# Plan: the fourteen tests that fail on 90.56

**Status, 2026-10-11:** built the same day, on the author's go-ahead, with one
change from the text below. `test_working_layouts_are_generated_including_stored_order`
is the registered check of rule R156 (the working layouts equal the current
builder's output), which this plan missed. Frozen to 90.42 it would have left
R156 unchecked. It stays on the working layout and finds the builder by the
version in the layout's title; the 90.42 comparison of section C is a second
test beside it. R156's example in the rule table names the current builder.
Every rewritten test was shown to fail on a broken input (eleven cases).

## The answer

The author's reading is right: in all 14 the assertion is out of date, and
none shows a fault in 90.56. Each was checked against the layout and against
the release it was written for. They are 9 test functions in five modules,
and they went stale in three different ways, so the fix differs.

Two terms:

- **Working layout:** `neptune/*_latest.json`, now 90.56.
- **Frozen:** the test reads its own release's stored build
  (`<variant>-candidate.json` in that release's findings folder) and not the
  working layout. The 90.49 to 90.55 scenarios already work this way
  (`frozen_layout_data` in `tests/scenario.py`).

## A. The layer was renamed; the requirement still holds (3 tests)

`tests/test_steering_rtp_menu_chords.py` looks up
`Steering | LS: Fallback Guard`. 90.43 replaced it with
`Steering | LS: Entry Guard`. All three pass on the working layout once the
name is right (run in memory, no file changed).

| Test | Still true on 90.56 | Fix |
|---|---|---|
| `test_menu_entry_conditions_repeat_and_do_not_repeat_key_output` | Start and Select are one repeating chord in `Base`, `Steering` and `Cursor Gyro`; the chained entries repeat; the Fn key does not | Take the guard out of the owner list. The Entry Guard binds Start and Select as a silent Start Press by design, and `test_steering_entry_feedback` checks that |
| `test_steering_inherits_pad_and_direction_soft_presses_clear_its_family` | `Steering` has no right pad group; up and down are the Soft Press at 29031 that removes the family, the Entry Guard included, `Steering` last, never `Gyro` | Name the Entry Guard in the removal list. Check "no right pad group" on `Steering` only: the Entry Guard blocks the pads by design |
| `test_inverted_edge_exception_rejects_changed_action_selector_repeat_or_owner` | The Budget audit allows exactly one inverted chord, the Entry Guard's, and rejects all four altered copies (selector, repeat, target, owner) | Point it at the Entry Guard |

## B. A later decision changed the expected value (4 tests, 9 results)

| Test | What it expects | What changed it | Fix |
|---|---|---|---|
| `test_neptune_gyro`: `test_base_and_ramp_tuning_match_reference_without_replacing_modifier_edges` (6 results) | The right stick at 100, 150, 200 in `Base` and the two turning ramps, from the July reference file | 90.45, the author's sensitivity change: 150, 200, 250, vertical scale 75% and 60% | Keep comparing every other setting with the reference, and state the 90.45 values for these two. `test_steering_entry_quiet_drivers` already has this exact check and passes |
| `test_layer_report`: `test_a_modifier_on_the_default_layout` | `Gyro Off Ramp Up` can be under `L1: Modifier 0` | 90.46: a bumper pressed in that ramp layer removes the ramps, so no ramp is ever under a bumper modifier | Assert that no ramp layer is under the modifier, and use `LST: Entry Point` as the example of a layer that is. The rest of the test passes as it is |
| `test_steering_rtp_menu_chords`: `test_delayed_targets_complete_before_rtp_cleanup_including_touch_completion` | 18 binds that add their pending layer first and then clear the right pad: 3 each in the four Steering modifier layers and the two stateful menu entries | The author's rule that the Steering modifier layers remove no right pad layer (90.49 to 90.55). The six in the stateful menu entries remain and pass | Expect 6 and say which. The rule itself is checked in `test_scenarios_90_53.py` and `test_scenarios_90_55.py` |
| `test_steering_entry_quiet_drivers`: `test_all_driver_owned_activators_are_off_with_only_mod2_repeat_added` | The W and S layers hold exactly the 90.43 binds, plus the repeat on the Modifier 2 chord | 90.49 to 90.55 reshaped those layers: up and down lost the cleanup and its guard, the stick's ring went back to the default | Split it in two (below) |

The split of the last one:

- **On the working layout:** what "quiet drivers" still requires. Every bind
  in the W and S layers states haptics Off, the stick group's override is
  Off, and the Modifier 2 chord repeats every 50 ms. All of it holds on
  90.56 (23 binds a layer, none loud).
- **Frozen on 90.48:** the bind-for-bind comparison with the 90.43 build. It
  holds in full on 90.46 to 90.48 and nowhere later.

## C. The comparison could never stay true (2 tests)

| Test | What it compares | Why it must fail | Fix |
|---|---|---|---|
| `test_steering_rtp_menu_chords`: `test_working_layouts_are_generated_including_stored_order` | The working layout with what the 90.42 builder generates | True for 90.42 only | Compare the 90.42 builder's output with the stored 90.42 build. It matches today. It also keeps that builder honest: the frozen 90.42 scenarios run on it |
| `test_fallback_window_backport`: `test_candidates_are_reproducible_including_stored_order` | The 90.39 builder's rules with a stored copy | The builder starts from the live exceptions register and adds three entries; the register has grown from 40 to 51 entries since. The layout half of the test still matches | Compare only the three entries the builder adds |

## What I would not do

- **Delete any of them.** Each still protects something: a live rule, or an
  old builder that frozen scenarios depend on.
- **Point a test at `versions/neptune/`.** Those files are backups. The
  stored builds in the findings folders are the same bytes (checked for
  90.42 and 90.48).
- **Touch the layout, the rules or the register.** Tests only.

## Files

- `tests/test_steering_rtp_menu_chords.py` (5 tests)
- `tests/test_neptune_gyro.py`, `tests/test_layer_report.py`,
  `tests/test_fallback_window_backport.py`,
  `tests/test_steering_entry_quiet_drivers.py` (1 each)
- `tests/scenario.py`: `'90.48'` in the stored builds of `frozen_layout_data`
- `todos.md`: the entry on the five failing modules closes

## Checks

1. The five modules alone: 14 results turn green and nothing else in them
   changes.
2. Each rewritten assertion is made to fail once on purpose (the old layer
   name, 18 for 6, a loud bind), so a test that can't fail isn't left behind.
3. The full suite, about 40 minutes: 0 failing, 25 expected failures.

## One choice for the author

The frozen half of the quiet drivers test (section B). The alternative is to
drop that half and keep only the live half. I would keep it: it costs nothing
and it is the only test of the 90.46 to 90.48 shape of those layers.
