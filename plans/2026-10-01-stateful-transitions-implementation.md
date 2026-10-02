# Plan: build the stateful transition structure

Status: built and installed as 90.10 on 2026-10-01
([build record](../findings/2026-10-01-stateful-transitions/README.md)). The
author chose to build all six steps without waiting for the Deck gates, so
both gates are still assumed and nothing has run on the Deck. Reviewed with
the author three times; the outcomes are folded in below and listed in
[Review decisions](#review-decisions-author-2026-10-01). Decisions 11 to 14
are from the second review and 15 to 19 from the third.
Design: [Stateful Layer Transitions](../resources/Stateful%20Layer%20Transitions.md)
· [decision record](2026-10-01-stateful-layer-transitions.md)
· [Definition of Done §11](../resources/Layer%20Definition%20of%20Done.md#11-stateful-layers)

## Assumptions

Both Deck gates are **assumed to pass** (author, 2026-10-01). They are still
checked on the Deck in step 7.

1. A stick input is inherited from a layer in the middle of the stack. The
   only contrary evidence is a
   [2022 community report](https://steamcommunity.com/app/353370/discussions/0/3468361193665969286/)
   about 360 controllers.
2. An edge Release fires in a layer that was added while the stick was
   already out.

Two more behaviours are relied on and haven't been tested in isolation:

3. A key output fires on an input that was already held when its layer was
   added. Fn's Backspace and Enter and the Steering windows' W and S need it.
   The author's experience is that it works
   ([scope note](../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes)).
4. A key output carries on when a removal exposes it under a held input. W
   and S need it when a Steering window times out.

Two more come from keeping the Entry Point under a guard, where today's
layout swaps it out:

5. **Established (author, 2026-10-01), no longer an assumption.** A layer
   that binds a button while a delay is running on that button eats the
   delayed action. So a guard that lands before the Entry Point's Fn delay
   ends cancels it, and Fn can't land on a guard.
6. A delay that was eaten starts again when the layer that ate it comes off
   and the button is still held. The repeating reset is what restarts it;
   that a removal re-evaluates a held input is unverified. Two places need
   it:
   - the Entry Point's Fn delay, when the last guard comes off
   - a guard's Tap Cover delay, when a second guard landed on top of it and
     then came off before the cover landed

If any of these fails, see [Fallbacks](#fallbacks).

## Scope

**In:** the menu Entry Points and Fn layers, the two stick guards and the
menu Tap Cover, the two transition layers, Steering's menu behaviour and its
S hold exit, Steering's left-stick recipe, the new audit check, tests and
docs. Both layouts.

**Out:** Gamepad, stateful Cursor Gyro and the Menu stateful layer. Until the
first two exist their gestures clear. Transition 0 comes with Gamepad.

## Where the work goes

The working layouts are generated: the frozen pre-steering copy, then
[build_candidate.py](../findings/2026-09-30-steering-lean/build_candidate.py)
(class `Lean`), then `install_neptune.py`, which runs the
[fix pipeline](../steam_layout/fixes/__init__.py). Hand edits to
`neptune/*_latest.json` would be lost on the next install.

- **New generator folder** `findings/<date>-stateful-transitions/`, with a
  builder that extends `Lean` the way `Lean` extends the 09-29 baseline, its
  own install script, and a README as the change record.
- **Menu and transition work** replaces `Lean.build_menu`, which today builds
  the protected Entry Points, their Tap Covers, the Base deflection chord and
  the `Transition Set 1` commit.
- **Steering work** changes `build_core`, `build_strokes`, `build_consumed`,
  `build_windows`, `build_repeats` and `build_touch_cleanup`.
- **Builder guard:** `Lean.finish()` raises on any new Always On layer and the
  manifest pins the count at 0. The new builder lifts both for the two
  Steering windows.
- **Fix pipeline:**
  - Retire `transition_set_0` (the generator writes the transition layers
    whole).
  - `menu_combo_keys` is unchanged. It swaps every overlay add for its key,
    wherever it finds one. The builder writes the Entry Points' other-button
    chord as "add Fn" only, so the fix finds nothing there; in the Fn layers
    it still swaps in the key ([step 1](#step-1-entry-points-all-four)).
  - `window_pads` and `window_routes` pick up the two new Always On windows.
    Both raise if a window lacks a group for a source they touch, and the
    Steering windows only have stick groups today. The generator gives them
    trackpad, `switch` and trigger groups.
  - `window_routes` also changes the two existing menu windows, because
    Steering can now sit under them ([step 5](#step-5-steerings-menu-behaviour)).

## Layers: one added, six repurposed

The layer count goes from 69 to 70. The new layer goes at the end of the
list, and every existing layer keeps its position, so no runtime ID shifts.

| Today | Becomes | Title (author, 2026-10-01) |
|---|---|---|
| `Transition Set 1` | Transition 1, cross gestures | unchanged for now |
| `Transition Set 0` | Transition 2, clear | unchanged for now |
| `Steering \| Menu Left: Entry Point` | Steering's Menu Left Entry Point | unchanged |
| `Steering \| Menu Right: Entry Point` | Steering's Menu Right Entry Point | unchanged |
| `Steering \| Menu Left: Tap Cover` | Left-stick guard | `Menu Buttons: Left Stick Guard` |
| `Steering \| Menu Right: Tap Cover` | Right-stick guard | `Menu Buttons: Right Stick Guard` |
| `Steering \| LS: Entry Point` | Same job, clearer name | `Steering \| LS: Entry Guard` |
| (new, appended) | The one menu Tap Cover | `Menu Buttons: Tap Cover` |

- `Lean` already calls `Steering | LS: Entry Point` "Entry Guard" internally.
- The clear lives in the layer titled `Transition Set 0` for now. In the
  design's numbering, 0 is the same-side transition that arrives with
  Gamepad, so the transition titles get sorted out then.

## Step 1: Entry Points (all four)

`Menu Left/Right: Entry Point` and Steering's pair share everything except
where the clicks lead. Shown for Menu Right; Left mirrors it.

| Input | Entry | Does |
|---|---|---|
| Start | Release | Unchanged: remove the Entry Point, add the Double Tap window last |
| Start | Chord on itself, `delay_start` 200 (was 300) | Add `Menu Right: Fn Layer` |
| Start | Regular Press, repeating 250 (was 350), uninterruptible | Remove Fn (the reset) |
| Select | Chord on Start | Add Fn, and nothing else. It no longer types Backspace itself |
| Select | Regular Press, repeating | Unchanged: the recovery |
| LS click, RS click | **Release** only | Run the clear list, then add the transition |
| LS edge, RS edge | Chord on Start, Hold to Repeat every 50 ms | Add that stick's guard. No longer swaps the Entry Point out |
| LS, RS touch | Unchanged | Release completes Fn and clears the trio |

- **Backspace and Enter live in the Fn layers only** (author, 2026-10-01).
  The Entry Point's own key came from the 90.9 overlay removal. Before the
  split the chord only added Fn and Fn's own chord typed the key, which is
  the shape this returns to. It relies on assumption 3.
- **Right stick becomes a D-pad:** `mode: dpad` with four empty directions.
  Its settings are copied from Fn's right-stick group (`requires_click` 0,
  `layout` 0, `deadzone` 13276), with radius 4915 and not inverted. The left
  stick's Entry Point group can't be the source: it only holds radius and
  invert, and takes the rest from Base, which the right stick can't inherit
  across modes. Radius 4915 on both sticks (the right stick used 7209 for
  mouse-mode hysteresis).
- **Click targets:**

  | Entry Point | LS click | RS click |
  |---|---|---|
  | `Menu Left: Entry Point` | Transition 2 for now (Gamepad later) | Transition 1 |
  | `Menu Right: Entry Point` | Transition 1 | Transition 2 for now (Gamepad later) |
  | Steering's pair | Transition 2 | Transition 2 |

- **Clear list at the click:** one list for all four Entry Points: every
  layer except Base and `Gyro`, both transitions included. The transition is
  added last. Generated, not hand-written.
- **Base:** Start and Select keep the repeating add of the Entry Point and
  lose the deflection chord that added the protected Entry Point.
- **A stick that is already out when the menu button goes down** is the
  common case (walking, then Start). The Entry Point is added over an edge
  that is already held, so its guard add doesn't fire at once; it fires on
  the first Hold to Repeat tick. The guard has to land before the 200 ms Fn
  delay ends, so that it eats the delay (assumption 5). That is why the edge
  chord states `repeat_rate` 50, where today's has none. If the guard landed
  late, Fn would be up first and its own edge binds would hide the guard add.

## Step 2: Fn layers

- Remove the `click` binds from both stick groups in both Fn layers (four
  repeating chords per layout). Fn then inherits the Entry Point's.
- Remove the switch-group `left_stick_click` and `right_stick_click` mode
  shifts and their two mode-shift groups per Fn layer.
- Fn's chords keep Backspace and Enter. They are now the only binds that type
  them.
- Fn's release and recoveries remove both Entry Point variants, both guards
  and the menu Tap Cover.

## Step 3: stick guards and the menu Tap Cover

Author, 2026-10-01: a guard behaves like the Entry Point for the menu button
that is held. The only difference is what the hold brings in: the Tap Cover
where the Entry Point would bring in Fn. A menu release in a guard still
opens the Double Tap window.

**Each stick guard.** Shown for the left-stick guard; the right one mirrors
it. One guard per stick serves both menu sides and all four Entry Points.

| Input | Entry | Does |
|---|---|---|
| Start, Select | Release | Remove the guards and Entry Points, add that button's Double Tap window last |
| Start, Select | Chord on itself, `delay_start` 200 | Add the menu Tap Cover |
| Start, Select | Regular Press, repeating 250, uninterruptible | Remove the menu Tap Cover (the reset) |
| LS edge | Release | Remove this guard |
| LS, RS touch | Release | Add the menu Tap Cover, then clear that stick's trio |
| LS, RS touch | Chord on either menu button (Any), uninterruptible | Empty. The guard is valid while a menu button is held |
| LS, RS touch | Regular Press, repeating | The recovery: remove both guards, the menu Tap Cover and all four Entry Points |

- The left stick's group is a D-pad with the same settings and radius as the
  Entry Point's. The clicks and the other stick's edge are inherited.
- **Both stick groups are D-pads in every layer that can sit above an Entry
  Point during a menu hold:** each guard's own-stick and other-stick group,
  the menu Tap Cover's two stick groups and both Fn layers. A group in
  another mode would block the click and touch inheritance
  ([mode rule](../resources/Layer%20Definition%20of%20Done.md#a-source-mode-change-blocks-inheritance)).
  A guard's other-stick group binds only touch; the Tap Cover's two groups
  bind only the edge.
- When a stick recentres, its guard comes off. If the Tap Cover hasn't landed
  the player is back in the Entry Point and Fn can arrive (assumption 6). If
  it has landed, it stays until the menu button is released.
- With both sticks out, the second guard eats the first guard's Tap Cover
  delay and starts its own. If the second stick recentres before the cover
  lands, the first guard's cover depends on its reset (assumption 6).
- Both guards' menu releases and the Tap Cover's release also remove both Fn
  layers. Fn can't be above them (assumption 5); the removal only covers a
  stale Fn.
- **Stale guard** (author, 2026-10-01): if a menu release is missed, touching
  either stick with no menu button held removes the stale guard, Tap Cover
  and Entry Points. This is the guarded recovery today's protected Entry
  Point has, and what
  [Definition of Done §5](../resources/Layer%20Definition%20of%20Done.md#5-stick-touch-release)
  asks of a layer that binds stick touch. It uses all three entries on both
  touch inputs. The menu Tap Cover inherits it.
- **The guards are not cover-type.** They bind both stick touches and carry
  their own recovery, so they don't go in `covers.titles`.

**The one menu Tap Cover.** It follows `L1&R1: Tap Cover`: one cover that
binds both buttons.

| Input | Entry | Does |
|---|---|---|
| Start, Select | Regular Press, uninterruptible | Empty. This hides the guard's hold and reset |
| Start, Select | Release | Remove the cover, both guards and all four Entry Points. No key, no window |
| LS edge, RS edge | Regular Press | Empty, so no guard can be added on top of the cover |

- Cover-type for [Definition of Done §5](../resources/Layer%20Definition%20of%20Done.md#5-stick-touch-release).
  Its title ends in `: Tap Cover`, so the Flow audit's cover suffix matches.

**Accepted (author, 2026-10-01):**

- Both menu buttons have the same binds in a guard, so with a stick out and
  one menu button held, a bump of the other one types its key through its
  Double Tap window.
- Under the menu Tap Cover, a bump of the other menu button removes the
  cover, the guards and the Entry Points while the first button is still
  held. Base re-adds the Entry Point, and the guard and cover return within
  about 200 ms. A release of the first button inside that gap types its key.

## Step 4: transition layers

Both are identical in the two layouts apart from the layer titles in their
lists.

| Input | Transition 1 | Transition 2 |
|---|---|---|
| Start release | Remove Transition 1, add `Steering`, add the Entry Guard last | Remove Transition 2 |
| Select release | Remove Transition 1 (Cursor Gyro later) | Remove Transition 2 |
| Bumpers, both trigger stages | Empty | Empty |
| Stick clicks, edges | Empty | Empty |
| Stick touch | Release clears that side's trio | Same |
| Left stick directions | W, A, S, D pass through, as today | Same |
| Gyro, both trackpads | Disabled | Disabled |

- Drop the Select-press cancel and the stick-touch guarded recovery. A
  transition that is stuck with no menu button held ends on the next tap of
  either menu button. This is the transition's recovery; the design document
  is reworded to say so.
- Face buttons, D-pad and back grips are not bound and keep their Base keys.
- **Accepted (author, 2026-10-01):** a bump of the other menu button while in
  Transition 1 commits to the other destination on its release. The first
  button is still held over Base, so its repeating press starts a fresh menu
  hold.

## Step 5: Steering's menu behaviour

- **`Steering`, no driver held:** Start and Select add Steering's Entry Point
  with a repeating press, like Base (author, 2026-10-01: the repeats stay).
  Steering is no longer removed. Definition of Done §11 is reworded to allow
  the repeat.
- **`Steering | … W Key` and `… S Key`:** Start is `key_press TAB`, Select is
  `key_press ESCAPE`. Plain Regular Press.
- **Modifier 0 to 2:** the keys are unchanged; they already match the normal
  modifiers. Step 6 changes how Modifier 0 and 1 guard them.
- **Steering may sit under the two menu Double Tap windows** (author,
  2026-10-01). This drops the 90.6 rule that Steering never reaches an Always
  On window. The only Steering binds that would show through are left-stick
  up and down (W or S plus the hold-exit clock), so
  `Menu Left: Double Tap` and `Menu Right: Double Tap` bind left-stick up and
  down as plain W and S. `window_routes` derives exactly that.
- **S hold exit:** left-stick south in `Steering` gets the same two chorded
  delays as north (warning from 1000 ms, exit at 2500 ms).
- **[flow_config.json](../steam_layout/flow_config.json):**
  - no families to update: since 2026-10-01 the audits build their stacks
    from the layout (backward chains), and the `families` section is gone
  - the two guards are not covers and need no entry
    ([step 3](#step-3-stick-guards-and-the-menu-tap-cover))
  - narrow the driver-inheritance `allow` to Modifier 0 and 1; the windows
    bind the drivers themselves after step 6. Optional since 2026-10-01:
    differing inherited bindings are listed as information and no longer
    fail the Flow audit

## Step 6: Steering's left stick

Author, 2026-10-01: follow the pattern the normal `L1: Modifier 0` and
`R1: Modifier 1` already use. Shown for R1 and stick up; L1 and stick down
mirror it.

- **Edge settings in every Steering layer:** not inverted, radius 4915
  (engages near 25%, releases near 5%). Today: inverted, radius 6553.
- **No `LS: Tap Cover` from the drivers.** `Steering`'s driver press adds the
  W or S layer only. Entering and leaving Modifier 2 add no `LS: Tap Cover`
  either. The cover is only ever added from inside Modifier 0 or 1, where the
  stick is out, so its edge Release can always remove it.
- **`R1: W Key` and `L1: S Key`:** stick up and down are a repeating add of
  Modifier 1 and 0. This replaces the 5 ms delayed add and its reset.
  - A stick already held when the driver goes down enters the modifier at
    once. Held 250 ms, the cover lands and recentring is silent. Recentred
    sooner, it counts as a tap.
- **Modifier 0 and 1:**

  | Input | Entry | Does |
  |---|---|---|
  | Entering direction | Chord on Any driver, `delay_start` 250 | Add `Steering \| LS: Tap Cover` |
  | Entering direction | Regular Press, repeating 300 | Remove the Tap Cover (the reset) |
  | Opposite direction | Regular Press | Remove this modifier. It never adds the other one |
  | East, West | Regular Press | A or D, and add the Tap Cover in the same bind. The modifier stays |
  | LS edge | Release | Remove the modifier and Tap Cover, add its Double Tap window last |
  | Start, Select, stick clicks | Two All-chords, then repeating cleanup | Each chord carries the key and the Tap Cover add in one array |

  The Any-driver chord uses the existing driver mask. The two All-chords are
  LS deflection (bit 30) plus one driver:

  | Layout | Left driver | Right driver |
  |---|---|---|
  | Default | L1, bit 3 | R1, bit 2 |
  | Alternative | L2 soft pull, bit 25 | R2 soft pull, bit 24 |

  Soft pull stays on at full pull (author, 2026-10-01). The alternative
  layout already relies on it: 256 chords test partial pull alone, and 12
  All-chords pair a stick deflection bit with a soft-pull bit.

- **`Steering | LS: Tap Cover`:** up and down are empty, left and right send
  A and D. The edge Release removes the cover, Modifier 0 and Modifier 1. No
  window.
- **`Steering | LS: Double Tap Cover`:** its direction release and its edge
  Release remove the cover and add nothing, like `L1: Double Tap Cover`.
- **Entry Guard:** the edge Release removes it; rename as above.
- **Double Tap windows become Always On windows.** Shown for
  `LS Up: Double Tap`; the Down window mirrors it. The window binds all of
  these itself, so nothing that changes layers is inherited
  ([§9](../resources/Layer%20Definition%20of%20Done.md#9-always-on-layers)).

  | Input | Does |
  |---|---|
  | `always_on_action`, 150 ms | Send one scroll-up, remove only the window |
  | Stick up | Remove the window first, then add `LS: Double Tap Cover` |
  | Stick down | Remove the window. Nothing else: no scroll, no modifier |
  | Stick left, right | A or D. The window stays |
  | R1 (R2 soft pull) | Regular Press sends W. Release removes the window first, then the family. `Steering` stays |
  | L1 (L2 soft pull) | Regular Press sends S. Release removes the window first, then the family. `Steering` stays |

  - After stick down removes the window, the W or S layer's repeating add
    brings in the other modifier.
  - No chords on the drivers, so Modifier 2 can't be entered during the
    window. A bump of the other driver sends its key, and its release runs
    the removals; `Steering`'s repeating driver press then restores the
    owner layer.
  - The W and S hand-over at the window's add and removal relies on
    assumptions 3 and 4.
  - Seven Always On windows become nine.
- **Audit check:** fail on any layer command on an inverted edge of a
  D-pad-mode stick. Mouse-mode sticks are out of scope: the three ramp layers
  use inverted-edge layer commands there. Add it to
  [audit_command_budget.py](../audit_command_budget.py), which already fails
  on Long and Double Press, with a test.
  - **It reports in its own list, like `banned_activators`,** and the CLI
    fails on it. It must not go into `violations`: `Lean.finish()` raises on
    that list, and four tests assert it is empty on the frozen 09-29 and
    09-30 builds, which carry the seven inverted-edge layers.
  - A per-activator `edge_binding_invert` counts as inverted too. Only
    Base's WASD modifier and the ramp layers state it that way today, and
    neither is a layer command on a D-pad stick.
  - **Inverted means the layer's own stick group says so**
    (`edge_binding_invert: 1`; author, 2026-10-01). A group that doesn't
    state it passes. By that rule the seven Steering layers above are the
    only violators in either layout today.
  - Not covered: `L1: Temp Cursor Gyro` and `R1: Temp Cursor Gyro` remove a
    layer on a left-stick edge, don't state the setting, and sit over Base's
    inverted edge. Whether they pick it up from Base needs a Deck check
    ([todo](../todos.md#cursor-gyro)).
  - The two Fn layers' right sticks have the same shape (a recovery on the
    edge, no setting stated). Nothing below them is inverted, so they are
    safe either way; the new builder states `edge_binding_invert` 0 there.

## Step 7: verify and ship

- **New test** `tests/test_stateful_transitions.py`, both layouts:
  - each Entry Point's click-release target
  - each transition's two menu-release results
  - no layer-adding input left unblocked in a transition
  - Fn layers and guards bind no stick click
  - both Entry Point sticks are D-pads with matching radii, and both stick
    groups of the guards, the menu Tap Cover and the Fn layers are D-pads
  - every Entry Point edge chord repeats at 50 ms
  - every driver bind in a Steering window removes the window first
  - no Entry Point bind types Backspace or Enter
  - both guards carry the touch recovery on both sticks: an empty Any chord
    on the menu buttons and a repeating removal of the guards, Tap Cover and
    Entry Points
- **Tests that pin today's behaviour and need updating:**
  `test_fixes.py`, `test_neptune_recovery.py`,
  `test_neptune_held_inputs.py`, `test_flow_inheritance.py` (its CLI test
  counts 15 covers and 67 reached layers),
  `test_audit_inheritance.py` with [traced_stacks.json](../traced_stacks.json),
  `test_double_tap_windows.py` (asserts seven windows and checks every
  window's pads) and `test_neptune_gyro.py` (names the affected layers). Two
  deprecated `timed_*` tests read the working layouts: `test_timed_spec.py`
  asserts six mode-shift groups, and step 2 removes four of them;
  `test_timed_reduction.py` replays a 300 ms menu hold on the default
  layout.
- **`test_steering_lean.py` stays as it is.** It loads the 09-30 `Lean`
  builder, not the working layouts, and `Lean` stays frozen, as the 09-29
  baseline did. The two rules steps 5 and 6 reverse
  (`test_steering_never_reaches_an_always_on_window` and
  `test_no_new_ao_and_existing_ao_sources_unchanged`) are asserted the new
  way in the new builder's test file.
- **Test to rewrite, not update:**
  `test_menu_entry_early_chord_types_its_key_itself` in
  `test_neptune_held_inputs.py`, which reads the working layouts. It is
  inverted, so it asserts the Entry Point adds Fn and types nothing.
- **Build audit:** `python3 audit_build.py` is clean. It runs the Budget,
  Window and Flow audits on both layouts.
- **Docs:** move the built parts of the structure document from "not built"
  to built; Definition of Done type table (Always On windows, guards, the
  menu Tap Cover); steering behaviour matrix (sideways keeps the modifier,
  menu press keeps Steering, S exit, the opposite direction inside a window
  drops the pending scroll, sideways inside a window is plain A or D);
  `Steam Input JSON Structure.md` where it describes the protected entry and
  the Entry Point's key; the Fn timing in Definition of Done §6 (300 and 350
  become 200 and 250).
- **Deck section in manual-testing.md:**
  - the two assumed gates above
  - each gesture from Base, from `Gyro` and from Steering
  - menu button released first cancels
  - a release missed while the Steam menu is open, in each transition
  - guard on and off for each stick, both together, and Fn arriving after
    (assumption 6)
  - push a stick about 150 ms into a menu hold: Fn must not land on the
    guard (assumption 5)
  - hold the left stick north, then hold Start for 500 ms: no `\` is typed.
    This is the timing check for the 50 ms edge repeat; the silent-release
    check below can't tell the Tap Cover from Fn, because both release
    silently
  - both sticks out, recentre the second one before 200 ms, keep holding:
    the release is still silent (assumption 6 for the guards)
  - a release missed while the Steam menu is open with a guard on: touching
    a stick clears it, and the next menu tap behaves normally
  - under the menu Tap Cover, bump the other menu button: the cover returns,
    and a release inside the gap types its key (accepted)
  - with a stick out: a quick menu tap types Tab or Escape, a 200 ms hold or
    a thumb lift makes the release silent
  - K1 reworded: hold Start, press Select before Fn is up: exactly one
    Backspace, repeating while held. Mirror for Enter
  - Tab and Escape while driving; S hold exit
  - rolling to A and D inside Modifier 0 and 1; both double taps
  - hold a driver, flick the stick once: W or S carries on through and after
    the window. Release the driver inside the window: back on `Steering`
- **Release:** the layout-apply skill (version, `to-ids`, VDF, snapshot).

## Order

Steps 1 to 5 depend on each other: the click binds point at the transitions,
and the guards and Steering's Entry Points reuse the layers of the protected
flow. Step 6 is independent of them.

**One release** (author, 2026-10-01): steps 1 to 6 ship together, so the
inverted-edge audit check goes in with no known violations left.

**Build order** (third review, then changed by the author): the review
proposed building steps 1 to 5 first and putting that candidate on the Deck
for the two gates before step 6, because gate 2 has no fallback and all of
step 6 rests on it. The author then asked for the whole layout to be built
and released at once, so 90.10 carries all six steps with the gates still
open. Gate 1 can also be checked on 90.9: hold R1,
press A so `R1: Tap Cover` lands, then click the left stick. Mouse Back
means the click came from `R1: Modifier 1` in the middle of the stack; Q
means it came from Base.

## Fallbacks

- **Gate 1 fails (sticks skip the middle layer):** the guards and Fn layers
  need their own copies of the click binds. A guard can't know which Entry
  Point is under it, so the guards would be split per Entry Point pair.
- **Gate 2 fails (no Release for an edge that was already out):** the guards
  and Steering's modifiers need another way to end. Nothing is designed for
  that yet.
- **Assumption 3 fails (no key on an input held at add):** the Entry Points
  go back to typing Backspace and Enter themselves, as in 90.9. The Steering
  windows would lose W or S for their 150 ms.
- **Assumption 4 fails (no key after a removal):** W or S drops when a
  Steering window times out, until the driver is pressed again. Nothing is
  designed for that yet.
- **Assumption 6 fails (an eaten delay doesn't come back):** after a guard
  comes off, Fn never arrives and the player stays in the Entry Point until
  the menu button is pressed again. With two guards, the Tap Cover may not
  land after the second one comes off, so a long hold with a stick out ends
  in Tab or Escape through the Double Tap window. Mild; no design needed.

## Worked out during the build

These aren't blockers, but the plan doesn't pin them down yet:

- **The repeat rate of the W and S layers' modifier add.** Today's reset on
  that input repeats at 50 ms.
- **The other blocks for the two new Always On windows.** The stick and the
  drivers are listed in step 6. `window_routes` derives the rest (pads,
  anything else underneath) from the built layout.
  - Since 2026-10-01 it does this from backward chains, which reach the
    Steering windows with no config
    ([record](../findings/2026-10-01-backward-chain-stacks/README.md#under-the-steering-windows)).
    On today's layout they already show what it will ask for: the trigger
    edges in the default layout, and the trigger clicks and both bumpers in
    the alternative, because a ramp layer can be added while in Steering.
- **The Steering windows' touch releases.** Always On windows remove
  themselves first, then that side's trio
  ([§5](../resources/Layer%20Definition%20of%20Done.md#5-stick-touch-release)).
- **The flow checker's centre rule.** [flow_model.py](../steam_layout/flow_model.py)
  recognises a centre exit as a repeating removal on an inverted edge. It
  has to recognise the edge Release instead. Neither audit needs anything
  for nine windows: the chains already treat a Release removal like a centre
  exit, and need no config per window or per layer.
- **Whether the two All-chord guards are interruptible.** Undecided by the
  author; the default is uninterruptible, like today's chords.
- **Entry Guard with the stick centred at entry.** Its edge isn't out, so it
  stays until the first push and return or a driver press. It only binds
  plain W, A, S and D, so this is harmless.
- **Face buttons and D-pad in Steering's Modifier 0 and 1.** Today they have
  the same shape as Start and Select; the default is to give them the same
  two All-chords.

## Settled with the author

- Layer titles: as in the table above, including `Menu Buttons: Tap Cover`.
- One release for everything.
- The release number is set when the layout-apply skill runs.

## Review decisions (author, 2026-10-01)

Each line is the author's answer from the plan review.

1. **Steering's Tap Cover follows the L1 and R1 pattern.** It is added only
   in Modifier 0 and 1: by the entering direction (Any-driver chord, 250 ms,
   with the 300 ms reset), by left and right together with A and D, and by a
   mapped button. Never by a driver press.
2. **The W and S layers add the modifier with a repeating bind.**
3. **The Steering windows bind the drivers themselves:** W and S, and a
   Release that removes the window first and then the family. No chords and
   nothing inherited. `Steering` stays.
4. **In a Steering window:** the own direction goes to the Double Tap Cover,
   the opposite direction only removes the window, and left and right are
   plain A and D.
5. **Steering may sit under the menu Double Tap windows,** which bind
   left-stick up and down as plain W and S.
6. **The menu buttons keep their repeating presses,** in `Steering` as in
   Base.
7. **The Entry Points only add Fn.** Backspace and Enter live in Fn alone.
   The held-input rule is scoped to the layer API and doesn't cover outputs.
8. **A bump of the other menu button in a transition is accepted.**
9. **Two stick guards and one menu Tap Cover.** A guard's menu release still
   opens the Double Tap window; the hold and a thumb lift apply the Tap
   Cover. A bump of the other menu button with a stick out types its key,
   which is accepted.
10. **Soft pull stays on at full pull,** so the alternative layout's
    All-chords are fine as planned.

Second review, after the plan was checked against the layouts:

11. **The guards carry the touch recovery.** Touching a stick with no menu
    button held clears a stale guard, Tap Cover and the Entry Points.
12. **The Entry Point staying under a guard adds two assumptions** (5 and
    6), each with a Deck check.
13. **The inverted-edge check counts a layer only when its own stick group
    says inverted.** Temp Cursor Gyro is left alone, with a Deck check to
    settle whether it picks up Base's inverted edge.
14. **A bump of the other menu button under the menu Tap Cover is
    accepted,** like the bump under a guard. One Tap Cover stays.

Third review, a check of the plan against the builder, the fix pipeline and
both layouts:

15. **A layer that binds a button mid-delay eats the delayed action**
    (author's runtime fact). Assumption 5 is established and its fallback is
    gone. Assumption 6 now also covers a guard's Tap Cover delay.
16. **The Entry Points' edge chords repeat every 50 ms,** so the guard lands
    inside the Fn delay when a stick is already out.
17. **Every layer above an Entry Point keeps both sticks in D-pad mode,**
    and the test checks it.
18. **The inverted-edge check gets its own list** in the Budget audit, so
    the frozen builders and their tests keep passing.
19. **Steps 1 to 5 are built and put on the Deck for the gates first;** step
    6 follows. Still one release.
