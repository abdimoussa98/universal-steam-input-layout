# The Fn layers take over from the Entry Points: Ibex 1.1, Neptune 90.77 and DSE 1.1

Built on 2026-10-16 from the **Ibex 1.0** snapshot, both variants, on the
author's word: "implement this plan"
([plan](../../plans/2026-10-16-fn-right-stick-owner.md)). Device status:
**untested** on all three controllers. No tag, no commit.

| Release | What it is | Layers | Removes, adds (default; alternative) |
|---|---|---|---|
| ibex 1.1 | Built by [build_candidate.py](build_candidate.py) from the Ibex 1.0 snapshot | 90 | 2,881, 477; 2,939, 477 (1.0: 2,965, 469; 3,023, 469) |
| neptune 90.77 | `python3 -m tools.convert neptune --version 90.77`. 90.76 is the [Deck trial](../2026-10-16-entry-point-requires-click/README.md) off the line, never released | 90 | as Ibex 1.1 |
| dse 1.1 | `python3 -m tools.convert dse` | 74 | 1,689, 381; 1,747, 381 (1.0: 1,777, 373; 1,835, 373) |

## Why

On the Deck the Fn layers' right stick typed nothing (90.74, 90.75), while the
left stick worked, and so did the July layout's right stick. The author,
2026-10-16: "fn is always going to inherit from entry point for that stick
since we've changed the mod from base so we cant have base = mouse -> entry =
dpad -> fn = dpad, and expect a partial inheritence in the fn layer. its just
inheriting everything." That is now assumption A77, reported: above the layer
that changed a source's mode (the owner), a group in the same mode doesn't
answer, and the owner answers the whole source.

| Stick | Base | Entry Point | Fn layer | On the Deck |
|---|---|---|---|---|
| Right, July | mouse | mouse | D-pad, the owner | works |
| Left, 90.75 | D-pad | D-pad | D-pad: no mode change | works |
| Right, 90.75 | mouse | D-pad, the owner | D-pad | nothing |
| Right, 1.1 | mouse | gone when Fn lands | D-pad, the owner | not yet checked |

## The change

Per variant, in the order the builder applies them; then the fix pipeline.
The change reports are in this folder (`*-changes.txt`): 38 layers in each of
the six layouts.

1. **No `requires_click` on a stick D-pad:** 28 groups. Seven of them become
   mouse groups in part 3. The pads and the D-pad keep theirs.
2. **`deadzone` 13276** on both sticks of the four Fn layers and the left stick
   of the six Entry Points: 14 groups.
3. **The hand-over:**
   - **The four Entry Points:**
     - Their right stick is a mouse group: `edge_binding_radius` 21000,
       `edge_binding_invert` 0 and `layer` 1, and nothing else stated, so the
       camera takes Base's settings. Its four empty directions are gone.
     - Each stick click adds the Entry Point's Fn layer at the press. It is a
       Regular Press, `haptic_intensity` 0, not interruptible, repeating every
       50 ms. It also removes the Entry Point, both guards and the Tap Cover,
       with the add stored last so it runs first.
     - The four existing adders also remove the Entry Point after their adds:
       the 200 ms chord, the chord on the other menu button and the two
       stick-touch Releases. That makes 24 hand-overs.
   - **Both stick guards and the Tap Cover:** the right stick is the same mouse
     group, and keeps its own touch and edge binds.
   - **The four Fn layers:**
     - Both sticks have the click Release of their Entry Point, the transition,
       command for command.
     - Each stick key's click guard is one empty chord on mask 71303168 (both
       stick clicks), Any, not interruptible, in place of the chord on its own
       stick's click.
     - Each Fn layer has copies of its Entry Point's two trackpad groups:
       eight new groups a variant, four on the Edge, which has no right pad.
4. **One Any chord** wherever two chords on an input had the same bind and
   settings, each on one button. That's 84 inputs, one entry fewer each:
   - 16 keys and both stick edges in each Fn layer (mask 20480, Select or
     Start);
   - both stick edges in the two combo Entry Points (20480);
   - both stick edges in the four Modifier 2 layers: 12 (L1 or R1) in the
     default, 50331648 (the soft pulls) in the alternative.

   `Steering | LS Up: Modifier 1` and `Steering | LS Down: Modifier 0` keep
   their All chords.

### What the fix pipeline did

`cleanup_lists` took out 140 removes per variant, each of a layer that can no
longer be on the stack there:

- the Entry Point from the 24 cleanup functions and Releases of each Fn layer;
- the Entry Point, both guards and the Tap Cover from each Fn layer's two click
  Releases;
- the plain Entry Point from the combo Entry Points' four edge and touch
  cleanups and from the Select or Start Release of the combo windows.

With the 56 removes the hand-over added, that is 84 fewer than 1.0.

### Three new entries in the exceptions register

- **R132,** the two Stateful Fn layers keep ten removes in their click
  Releases: the sticks' Tap Cover and Temporary Gyro, the two pad click layers,
  `LTP: Arrow Keys`, `RTP: Mouse Buttons`, `RTP: Tap Cover` and
  `RTP: Circular Scroll`. The two entries for the Stateful Entry Points kept
  them for the same reasons, which the chains can't see. Without the entry the
  fix took all ten out.
- **R136,** twice: the combo Double Tap windows cover the Fn layer's two stick
  clicks for their 150 ms. This is the entry the windows had over the Entry
  Point, now that the transitions are Fn's.

For 1.1 the old entries for the Stateful Entry Points' Releases and for the
windows over the Entry Points match nothing (the Cleanup audit prints them as
stale), and the frozen builders still need them, so they stay.

## What the chains show

- Under the four Fn layers, 1,108 stacks a variant: none has a menu Entry
  Point, a guard or the Tap Cover, and the right stick under Fn is in mouse
  mode in every one. On 1.0 all 1,108 had the Entry Point's D-pad there. A
  contract test holds it (`tests/contracts/shared/test_fn_right_stick_owner.py`).
- The A77 scan (same-mode groups over a mode change):
  - On 1.0 it listed the right stick of 13 menu layers over an Entry Point's
    D-pad.
  - On 1.1 the four Fn layers, both guards and the Tap Cover are gone from it.
  - The combo Entry Points, `Menu Left!Right: Enter`, `Menu Right!Left:
    Backspace` and the two combo Double Tap Covers now sit over Fn's D-pad in
    the same way. So do the combo windows' pad groups over Fn's pad copies.
  - Their own touch and edge binds don't answer there by A77, as they didn't
    over the Entry Point. The plan leaves these out.
- The chains now find 458 more stacks under `L1: Double Tap` and
  `R1: Double Tap`: a pad layer under `Gyro`. Those stacks were reachable on
  1.0 too. The chains keep one shortest chain per stack, and the transitions'
  chain is now one step longer (through Fn's click). With that, the bystander
  replay finds these stacks.

## Audits and tests

- **The build audit is clean** on all six working layouts. The Cleanup audit's
  one finding, the windows over Fn's clicks, is accepted by the two R136
  entries above.
- **The new tests pass:**
  - `tests/scenarios/ibex/test_scenarios_ibex_1_1.py`, F1 to F11, on Neptune's
    layouts, on Ibex's with `SCENARIO_CONTROLLER=ibex`, and F11 on the Edge's.
  - `tests/contracts/shared/test_fn_right_stick_owner.py`, on all six layouts.
    Both of its tests fail on 1.0.
  - `tests/releases/ibex/test_shapes_ibex_1_1.py`, 1.0 against 1.1:
    - every Fn adder hands over;
    - each Fn click Release is its Entry Point's less the four removes;
    - the pad groups are copies;
    - each of the 84 merged chords fires exactly when one of the two it
      replaced did.
- **On the simulator, every stick-click transition ends where it did on 1.0:**
  both variants, from Base, `Steering` and Cursor Gyro, both menu buttons and
  both sticks, from Fn, the Entry Point, either guard and the Tap Cover. That
  is 120 gestures.
- **The full suite:** 1,481 tests in eight shards (3 expected failures), and
  the 8 Node tests.
  - **R165:** every one of the 38 changed layers is on the stack in a live
    scenario, for Neptune against 90.75 and for the Edge against DSE 1.0, in
    both variants. Scenario F12 brings the Edge's in.
  - **`tools.release check`** passes for ibex 1.1, neptune 90.77 and dse 1.1.
  - **The unverified assumptions** are in
    [unverified-assumptions.txt](unverified-assumptions.txt).
- **Existing tests that read the old shapes now read the new ones,** each with
  a note:
  - the Fn adds' bumps (the eight click presses are silent) and the handed-over
    stacks under Fn: scenarios 90.24, 90.25, 90.26, 90.28 and 90.30;
  - the Entry Point's chords and right stick, and the merged Modifier 2 guards
    (`test_neptune_held_inputs`, `test_neptune_recovery`);
  - the 90.74 shape, the 90.58 clears (now in the Fn layers) and
    `requires_click` (`test_static_checks`, `test_steering_entry_quiet_drivers`);
  - the Edge's version.
- **One behaviour change these show:** a stick click inside a quick menu tap
  brings Fn in, so the menu release types nothing, as after Fn is up. On 1.0
  the release opened the Double Tap window and typed the tap's key (scenario
  90.10 T3).

### What the simulator can't show

- **A77.** The simulator and the audits follow A1, under which 1.0 typed the
  keys too. The contract test checks the shape that makes A77 not matter.

### The click guard: A78, verified on 2026-10-17

Each Fn stick direction has two binds: its key, a chord on Select or Start, and
the click guard, an empty chord on the stick clicks that is not interruptible,
so a stick pushed while a click is held types nothing. That rests on A78: a
chord that is not interruptible holds back an interruptible chord on the same
input. A27 had left two chords on one input open, and the simulator ran both,
so there the key typed. The author verified A78 on 2026-10-17 ("I can confirm
that an interuptible chord will be interupted by an uninnteruptible chord"),
and the simulator models it since.

- **Scenario F4** checks that nothing types: in Fn with either stick clicked,
  and with the other stick out when the click brings Fn in.
- **1.0 relied on the guard as well.** New in 1.1 is one gesture where only the
  guard stops a key: the left stick pushed up under the guard (`W`, as in
  Base), then a right stick click before Fn's half second. On 1.0 the click
  left that stick alone and `W` went on. On 1.1 the click brings Fn in over
  the stick that is up: `W` stops until the click's Release, and the guard
  holds back Fn's `\`.
- **One other input has the same pair:** Base's right stick edge, where the
  empty chord on L1 or R1 (either trigger in the alternative) holds back the
  add of `Turning Ramp Up 0` on a trigger (on a bumper in the alternative). On
  the simulator a bumper and a trigger held together added the ramp until
  2026-10-17; now, as on the Deck, nothing. The layouts didn't change.

## On the Deck

Confirm the configurator's title shows `:: 90.77` first.

1. Hold Select for half a second, then push the right stick each way: `;` `'`
   `.` `,`, each with a Low bump. The same with Start, in `Steering` and in
   Cursor Gyro, and with the thumb already on the stick.
2. Hold Select and move the right stick: the camera moves until Fn comes in at
   half a second. Push it out first: the camera still moves.
3. Hold Select and click a stick before half a second: no bump at the click,
   and on letting go of the click the transition happens, as from Fn.
