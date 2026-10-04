# The required cleanups: three rules and their check (R169 to R171)

**Status, 2026-10-04:** built and installed in `neptune/` as **90.24**, with the
snapshot in `versions/neptune/90.24/`. Device status: **untested**. The build
audit is clean and the tests pass.

The rules are in the
[Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md#7-cleanup)
and the Cleanup audit enforces them. They were enforced first, with 90.23
failing on purpose; the [fixes](suggested-fixes.md) were then tried on scratch
copies, the author made the five decisions, and 90.24 applies them
([what 90.24 changed](#what-9024-changed)).

A cleanup function is the backup exit for a stuck layer: on one input, a chord
with the button that keeps the layer on, beside a repeating Regular Press that
removes the layer when that button isn't held (R133).

## The rules

The author decided them on 2026-10-04. Until then only the stick-touch Release
was required in every layer (R116), and stick-edge cleanups were "only where
needed" (R134, now retired).

| ID | A layer has a cleanup function on | Left out |
|---|---|---|
| R169 | Both stick touches. Covers too: none passes by inheriting | The six stick-touch helpers |
| R170 | A stick edge it binds or blocks. Both edges when it binds or blocks a face button, a D-pad direction, Start, Select or a back button | |
| R171 | Every button it retypes or blocks: those buttons, the bumpers, and each trigger's pull and full pull | The layer's own button, and a button that removes the layer by cancellation |

Left out of all three: Always On windows, stateful layers and ramp layers.

Details the author settled:

- **A block counts as a retype.** A stuck `L1: Scroll Down` that silences Start
  is as bad as one that retypes it.
- **The layer's own button** is the one whose Release removes the layer.
  Nothing can guard a cleanup there.
- **The Temp Cursor layers pass R171.** Each button there removes the cursor
  layer, which exposes the modifier's own cleanup.
- **Transitions are included**, guarded by either menu button. Since 90.10 a
  stuck one only ended on the next menu tap.

## Exceptions the author decided

Three entries in the exceptions register, all to R170:

| Layer | Input left without one | Why |
|---|---|---|
| `Menu Buttons: Left Stick Guard` | Right-stick edge | Each guard handles only its own stick. The other edge stays open so the Entry Point's add of the other guard comes through |
| `Menu Buttons: Right Stick Guard` | Left-stick edge | The same |
| `Steering \| LS: Entry Guard`, `Steering \| LS: Fallback Hold` | Left-stick edge | The left stick being out keeps them on, so nothing can guard a cleanup there. Theirs goes on the right-stick edge |

## The check

Three new checks in the Cleanup audit
([required_cleanups.py](../../steam_layout/required_cleanups.py)), printed with
the other eight by `python3 -m tools.audit_cleanups <layout>`:

| Check | Rule |
|---|---|
| Touch without cleanup | R169 |
| Edge without cleanup | R170 |
| Button without cleanup | R171 |

- **It reads each layer on its own.** No stacks are needed, so it adds no time.
- **A cleanup function counts** when it is on that input and removes the layer
  itself.
- **A ramp layer** is one that no button, thumb or stick keeps on and that a
  cancellation or a return to centre ends. A layer with no keeper and no such
  exit is not left out, so a layer that nothing ends still fails.
- **"Covers nothing"** is said of a blocked button when neither the action set
  nor any layer the chains put under this one binds that input.
- **An exception** is a register entry for R169, R170 or R171 with the layers
  and the inputs (`joystick/edge`). One that matches nothing is reported as
  stale.
- **Not read:** a group in another mode than the layer below also blocks an
  input (A2). That depends on the stack, so the hidden-exit check covers it
  (R136).
- `--no-required` leaves the three checks out. The tests use it for toy
  layouts that only show a list or an exit; the build audit never does.

## What it finds on 90.23

Inputs without a cleanup function, after the three exceptions:

| Check | Default | Alternative |
|---|---|---|
| Touch without cleanup | 48 in 24 layers | 48 in 24 layers |
| Edge without cleanup | 42 | 42 |
| Button without cleanup | 84 | 106 |
| **Total** | **174** | **196** |

- **Touches:** 10 covers and `Steering | LS: Fallback Hold` leave both touches
  to the layer below. 13 layers bind the touch with only its Release: the four
  menu Entry Points, both Fn layers, `Menu Left: Escape`, `Menu Right: Tab`,
  `RTP: Entry Point`, the three transitions and `Steering | LS: Entry Guard`.
- **Edges:** the menu Entry Points, second-press layers and their covers, the
  transitions, the stick guards' own edge, `Menu Buttons: Tap Cover`, and ten
  Steering layers.
- **Buttons, default:** 38 are the trigger's full pull, blocked in 19 layers,
  and every one covers nothing. The other 46 are scroll on the bumpers, Start
  and Select, and the transitions' and Fn layers' blocks.
- **Buttons, alternative:** the modifiers there retype the bumpers, and the
  full-pull blocks in the menu layers do cover something.
- **Passing already:** the eight modifiers apart from their full-pull blocks,
  the pad layers, and the single Tap Covers.

## What 90.24 changed

No layer was added, so no runtime ID moved. 45 layers changed in each layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt));
`default-inputs-changed.txt` and `alternative-inputs-changed.txt` list every
input with its shape.

- **174 inputs in the default layout and 196 in the alternative** got a cleanup
  function, in the seven shapes of [suggested-fixes.md](suggested-fixes.md).
  No input has more than three entries.
- **15 new stick groups**, in Base's mode, on nine layers that had none.
- **The two Steering stick windows type Tab and Escape themselves** (R140).
- **The `cleanup_lists` fix** then filled the new lists (R128, R129).

The author's five decisions:

| # | Decision |
|---|---|
| 1 | The full-pull blocks that cover nothing stay and get a cleanup. Whether they can go is a [to-do](../../todos.md#investigations) |
| 2 | `RTP: Tap Cover` gets its right-stick group. Five covered exits are accepted in the register (R136) |
| 3 | In the Steering W and S layers the bind that adds the Modifier 2 layer moved into the guard chord |
| 4 | The left edge of the two Steering stick covers is guarded by either driver |
| 5 | The stick guards keep inheriting L1 and R1 (and the triggers) from the Entry Point under them, accepted in the register (R139) |

## What changes for the player

A layer left on by a missed release now ends on the next stick touch, stick
push or button press, and that press then does what it does underneath. With
the layer's button held, nothing changes. Four things do behave differently:

- **A stuck transition ends on a stick or a bumper.** From 90.10 to 90.23 only
  the next menu tap ended it, and that tap committed it (scenario 90.10 T4).
- **`Steering | LS: Entry Guard` only lasts while the left stick is out.** Its
  cleanups are guarded by the left stick being out. After an entry with the
  stick centred it is removed about 100 ms after it lands, by the cleanup's
  repeat on the resting thumb (A6), and a Start press removes it too. The first
  push then gets the Fallback Hold, with its pulses and its exit, where 90.23
  held W with no exit until the stick had been back to centre once. With the
  stick out at entry nothing changed (scenarios 90.11 F7 and F11).
- **The right-stick click starts no transition under `RTP: Tap Cover`**
  (called out by the author). The cover's new right-stick group is in mouse
  mode and the menu Entry Point's right stick is a D-pad. The Fn layer on top
  inherits the click from the Entry Point, and nothing is inherited across the
  mode change (A2). It happens when the right pad is touched first and the
  menu button is pressed before the cover lands at 150 ms, and lasts while the
  thumb stays on the pad. With the menu button pressed first, `RTP: Entry
  Point` already hid the click before 90.24 (scenario 90.24 K6).
- **A stale menu cover under a held right pad clears one step later.** With
  the pad held, `RTP: Tap Cover` now answers both stick touches, guarded by
  the thumb on the pad. On 90.23 the touch reached `Menu Buttons: Tap Cover`
  and cleared the stale menu layers at once. They now go on the first stick
  touch after the thumb leaves the pad (scenario 90.23 C3).

## Scenarios and tests

- `tests/test_scenarios_90_24.py`, K1 to K7: a stuck layer ended by a stick
  touch in six groups, and left alone while its button is held; a stuck
  Steering layer ended by a stick push; a button press that ends a stuck layer
  and then acts underneath; the other driver in the W and S layers; the pad
  cover over a menu layer; the Steering windows' Tab and Escape.
- Five older scenarios changed: 90.10 T4, 90.11 F7 and F11, MB10 and 90.23 C3.
  Each says in a comment what 90.23 did.
- `tests/test_required_cleanups_build.py`: the build is the working layout
  (R156), the new groups, the decisions, and what did not change.
- `test_neptune_recovery.py` and `test_neptune_cursor.py` describe the new
  shapes of the transitions, the Entry Points and the cursor layers.

## Assumptions

None new. The new cleanups rest on what every cleanup function rests on (A25,
A27, A30), on chords latching (A17) and on a repeat firing in a layer added
over a held input (A6). `unverified-assumptions.txt` lists what isn't verified
(R167).

## Files changed for the check

| File | Change |
|---|---|
| `steam_layout/required_cleanups.py` | New: the three checks |
| `tools/audit_cleanups.py` | Prints and counts them; `--no-required` |
| `steam_layout/exceptions.py`, `flow_config.json` | The scope for R169 to R171; the three entries above |
| `steam_layout/rules.py` | The Cleanup audit's checks are declared in two modules |
| `resources/Layer Definition of Done.md` | Rows R169 to R171; R134 retired |
| `tests/test_required_cleanups.py` | 44 tests: tiny layouts, the frozen 90.23 snapshots, the command |
| `tests/test_tap_cover_stick_touches.py`, `tests/test_scenario_registry.py` | The pinned build test moved to the 90.24 build's file; the list of scenarios for R136 gained K6 |
| `tests/test_cleanups.py`, `tests/test_native.py` | Their toy layouts run the command with `--no-required` |
| `tests/test_scenarios_triggers_and_recovery.py` | Scenario LR1 names R170 in place of R134 |
| `docs/tools.md`, the two skills, `Steam Input JSON Structure.md` | The rules and the check |

## What failed on purpose until 90.24

- `python3 -m tools.audit_build`: the Cleanup audit failed on both 90.23
  layouts.
- `test_required_cleanups.test_the_working_layouts_have_every_required_cleanup`.

## Files

- `build_candidate.py`: the builder. It extends the 90.23 builder, which stays
  frozen. Its `Fixes` class gives each input its shape.
- `install_neptune.py`, `*-required-cleanups.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `*-inputs-changed.txt`: every input the builder changed, with its shape.
- `single-set-*-changes.txt`: the change report against 90.23 (R164).
- `unverified-assumptions.txt`: the assumptions that aren't verified (R167).
- `suggested-fixes.md`: the fixes group by group, the trial, and the five
  decisions.
- `trial_fixes.py`: runs the builder's fixes on scratch copies of the working
  layouts and runs the four audits. It installs nothing. On 90.24 it finds
  nothing to change.
