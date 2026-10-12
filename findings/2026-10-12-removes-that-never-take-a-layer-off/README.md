# The removes that never take a layer off, taken out (90.58)

Built on 2026-10-12 from the **90.57** snapshot, both layouts, on the author's
word: "start building". 90 layers in each layout. Nothing here has run on the
Deck.

It builds the
[plan](../../plans/2026-10-12-removes-that-never-take-a-layer-off.md), which
follows the [audit of every remove](../2026-10-12-remove-list-audit/README.md)
on 90.57.

| | Default | Alternative |
|---|---|---|
| Removes in 90.57 | 4,013 | 4,083 |
| Taken out | 1,162 | 1,174 |
| Added | 0 | 0 |
| **Removes in 90.58** | **2,851** | **2,909** |

## Terms

- **Bind:** one activator entry on one input of one layer. Its **list** is
  the layers its `remove_layer` commands name. Its **host** is the layer it
  sits in.
- **Never there:** the audit's chains say the named layer and the host are
  never on the stack together, and the bind fired 30 times or more in the
  random walks without meeting it.
- **Answers first:** the named layer binds the bind's own input and only
  ever sits above the host. While it is on, it answers that input and the
  bind underneath does not run (R132 as tightened in 90.57).
- **Clear:** one of the fourteen binds that enter a transition, `Gamepad` or
  `Menu Keys`, or leave the last two. Each named every layer but one.
- **Modifier family:** the 19 layers a bumper owns outside `Steering` (the
  triggers' soft pull in the alternative).

## Why

The author, 2026-10-12:

1. "I want you to audit whether all these removes are necessary", after the
   ten largest lists were counted.
2. "I want to make sure that this is reductive and not additive. So we're
   not going to be adding any layer removals right now. We're just reducing
   them."
3. On the plan's two questions, the clears and the bumpers' own cleanup
   functions: "1. trim 2. are you asking me if i want to trim, if so yes i
   want to trim".

## Nothing is added

Every bind has its 90.57 commands with some removes taken out. Nothing else
in the layout differs but the title.

- **The builder stops** if a bind gains a command, loses anything but a
  remove, loses all its commands, changes the order of what stays, or if any
  other key differs ([`build_candidate.py`](build_candidate.py),
  `only_removes_gone`).
- **The fix pipeline changes nothing,** and the builder stops if it does.
- **A test states it** of the stored candidates against the 90.57 build
  (`test_every_bind_has_its_90_57_commands_less_some_removes_and_nothing_else_differs`).
- **What goes is a stored list:** [`taken-out-default.json`](taken-out-default.json)
  and [`taken-out-alternative.json`](taken-out-alternative.json), one row a
  bind, cut from the audit's rows by [`select_removes.py`](select_removes.py).
  A rerun of the audit does not change what 90.58 is.

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt): 34 layers
changed in each, 142 binds in the default layout and 154 in the alternative.

| Where | Binds | Removes taken out | Why none of them took a layer off |
|---|---|---|---|
| The fourteen clears | 14 | 950 | Never there (934) or behind a window that blocks the stick clicks (16) |
| `Steering`'s exit on up and down | 2 | 26 | Each of its thirteen family layers binds up and down |
| The W and S layers' cleanup functions | 12 | 48 | The six Steering stick layers each have a cleanup of their own on the same input |
| The four modifiers' cleanup functions | 68 | 76 | The cursor layer binds 17 of those inputs as a cancel; the cover binds both stick touches |
| The four Modifier 2 layers' cleanup functions | 8 (16) | 8 (16) | `L1&R1: Tap Cover` binds the input |
| The two bumper scroll layers, on a stick touch | 4 | 4 | Their Double Tap Cover binds both touches |
| The Entry Guard's two menu presses | 2 | 6 | The three ramp layers: the guard binds the right stick's edge, so none comes on with it |
| The Steering stick modifiers and scroll layers, the Fn layers, the stick guards, the two ramp layers, the right pad's layers | 32 | 44 | A cover or second-press layer above binds the same input |
| **All** | **142 (154)** | **1,162 (1,174)** | |

In brackets: the alternative layout, where it differs.

### 1. The clears

| Bind | 90.57 | 90.58 |
|---|---|---|
| `Menu Left: Entry Point` and `Menu Right: Entry Point`, either stick click's Release | 89 | 27 |
| `Stateful \| Menu Left: Entry Point` and `Stateful \| Menu Right: Entry Point`, either stick click's Release | 89 | 26 |
| `Menu Left!Right: Entry Point` and `Menu Right!Left: Entry Point`, the chord that enters `Menu Keys` | 89 | 23 |
| `Menu Keys`, either stick click chord | 89 | 14 |
| `Gamepad`, either stick click chord | 89 | 5 |

Each keeps every layer that was on the stack at least once when it fired in
48,000 random walks, and every layer the audit could not rule out. A bumper
layer is in none of them: a modifier retypes Start and Select, so a menu
Entry Point cannot come on while one is on.

### 2. `Steering`'s exit

Up or down at the rim with no driver held removed the whole Steering family,
14 layers, the two windows first (90.42). It removes `Steering`. Each of the
other thirteen binds up and down itself, so the exit only runs with
`Steering` bare, and none was ever under `Steering` when it was added.

### 3. Cleanup functions

A cleanup function removes its host, what is below it inside its guard, and
a layer above it that leaves the input alone (R128, R129). It named layers
above it that bind the input as well. Those answer first: 172 removes (184).

The author's two cases:

- **`L1: Modifier 0` and `L1: Tap Cover`.** On Start, Select, R1, the face
  buttons, the D-pad and the stick clicks the modifier still removes its
  cover: it was on the stack nearly every time one of those fired. Only on
  the two stick touches the cover is gone from the modifier's list, because
  the cover binds both touches and removes itself and the modifier there.
- **Rocking in the plain and `Gyro` Modifier 2 layers.** No Release, reset,
  hold or entry bind of the modifier family changed. All 88 (96) are in
  cleanup functions, which their guard holds back while the bumper is held.

### Left as they are

- **2,006 needed** and **768 not shown either way** (default). A remove met
  on the stack even once stays.
- **77 fixed by a rule:** the timer resets (R120), a layer's own hold target
  in its Release, the stick touch trio (R123).
- **16 at the two Stateful Entry Points:** a stick's Tap Cover and Temporary
  Gyro. The chains call them never there; the walks met them. A register
  entry keeps them.
- **8 in the right pad's layers:** `RTP: Middle Click` and `RTP: Mouse
  Buttons` come on by `hold_layer`, which neither the chains nor the
  simulator follow.
- **Two places where a layer is left on** would need a remove added: `RTP:
  Double Tap` answering a bumper's Release in `Steering`, and a stick
  window's right pad touch Release (author: "leave it").

## What you would feel

Nothing new: on the simulator every log is the same as 90.57's.

What is different is outside what the simulator can produce. If Steam ever
leaves a layer on with no press sequence behind it, entering a mode no
longer wipes it, and `Steering`'s exit no longer wipes a Steering layer
under `Steering`. That layer goes with its own cleanup: a thumb on a stick.

## Rules, the register and the tests

- **R163, reworded:** entering a transition clears every layer that can be
  on the stack there. The author's words when it was made: "clean everything
  below you that is possible".
- **R132** now reads the same for a clear. Its row records the sixteen and
  the eight.
- **The register:** one new R132 entry keeps the sixteen. Cut short, a clear
  is no longer exempt from the Cleanup audit's "never there" check, and the
  fix pipeline would take them out.
- **New tests,** [`tests/test_scenarios_90_58.py`](../../tests/test_scenarios_90_58.py),
  eleven: the constraint, the count, the clears' sizes; 120 seeded walks and
  every three-step bumper sequence, log for log against 90.57; **the guard
  for R163** (in 240 seeded walks, every layer on the stack when a clear
  fires is one it names, apart from the one it keeps); no cleanup function
  names a layer its rules do not ask for; and four scenarios (90.58 M1 to
  M3, C1).
- **On the 90.57 build** (`frozen`): 90.42 S3, which seeds a stack no press
  reaches and expects `Steering`'s exit to clear it; the contract test of
  `test_steering_touch_windows`; and a copy of the family clear's shape
  test.
- **Rewritten for what holds now:** `test_fn_feedback_steering_clear` (the
  exit removes `Steering`), `test_steering_rtp_menu_chords` (the same),
  `test_steering_entry_feedback` (the guard's menu press),
  `test_neptune_recovery.recovery_specs` (a modifier's cleanup names itself
  and its cover; used by 57 subtests there and in `test_neptune_cursor`).
- **No audit check yet** for "answers first". Inside the Cleanup audit it
  would also run in the fix pipeline and change what the builders of earlier
  releases rebuild. The test is its statement; the to-do stays.

## Validation

- **Build audit:** clean on both installed layouts (Budget, Window, Flow,
  Cleanup).
- **Pre-flight:** layer order, preset blocks and preset ids OK, no duplicate
  titles, no unresolved token; both VDFs exported and verified against
  their JSON.
- **Only removes are gone,** on the installed files and on the snapshot,
  against the 90.57 snapshot: 142 binds differ in the default layout and
  154 in the alternative, by 1,162 and 1,174 removes taken out; commands
  added 0, order changed 0, and the title is the only other difference.
- **The builder against the trial.** Its layouts equal, key for key apart
  from the title, the trial layouts the audit's proofs ran on.
- **Random walks, the whole log compared** (every key, wheel step, haptic
  and beep, every layer on or off, with its time). On the trial: 48,000
  walks a layout, no log different. On the built files, on seeds the audit
  did not use ([`proof.py`](proof.py), [`proof.txt`](proof.txt)): 24,000
  walks a layout, half with one release in ten missed. 23,438 finish in the
  default layout and all 24,000 in the alternative; no log differs. (562
  default walks are stopped by the simulator, which gives up on a sequence
  it cannot play; the audit's walks met the same, at its ramp loop.)
- **Is anything left on?** The same walks, after everything is let go, and
  then after a thumb on each stick:

  | Layout, releases missed | 90.57 | 90.58 | After a thumb on each stick |
  |---|---|---|---|
  | Default, none | 24 | 24 | 0 and 0 |
  | Default, one in ten | 301 | 301 | 0 and 0 |
  | Alternative, none | 22 | 22 | 0 and 0 |
  | Alternative, one in ten | 181 | 181 | 0 and 0 |

- **Rocking the bumpers** (on the trial,
  [`rocking.txt`](../2026-10-12-remove-list-audit/rocking.txt)): the nine
  tests of `tests/test_modifier_rocking.py` pass. Every sequence of five
  steps of L1, R1 and A, 236,196 a layout, and every sequence of four steps
  with missed releases and a thumb on the right stick, 25,600 a layout:
  no log differs.
- **Scenarios:** `tests/test_scenarios_90_58.py`, 11 tests, pass. 379
  scenarios in all; every layer is on the stack in one (R165).
- **Full suite:** 1,224 tests in 107 modules, with the same 25 expected
  failures as before the build. One test failed: R163's row in the rule
  table had a note in its exceptions cell, which must read "None" when the
  register has no entry for the rule. The note moved into the rule's text,
  and that module and the four others that read the rule table and the
  register were rerun and pass. The whole suite was not run again after
  that one-cell change.
- **Unverified assumptions:** 48, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). This build adds
  none.

## On the Deck

Everything above is the simulator's. There is nothing new to feel, so these
check that nothing went missing:

1. Enter and leave `Cursor Gyro`, `Steering`, `Gamepad` and `Menu Keys`
   from each side, with a thumb resting on a pad: nothing is left on.
2. Rock L1 and R1 in Base and in `Gyro`: no scroll.
3. Hold a bumper for a moment, open the Steam menu, let go inside it and
   close it. Press A, twice at most: the layout is back to normal.
4. The same with both bumpers held, then a thumb on the right stick.
5. In `Steering`, push the stick up to the rim with no bumper held:
   `Steering` ends with one beep, and `Gyro` is as it was.
