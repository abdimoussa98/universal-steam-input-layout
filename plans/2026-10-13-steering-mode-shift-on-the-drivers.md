# Plan: the drivers mode-shift `Steering`'s up and down to empty binds

**Status, 2026-10-13:** built as **90.66**, from 90.65, on the author's word
("Just build it";
[release record](../findings/2026-10-13-steering-mode-shift-on-the-drivers/README.md)).
The editor check under "What it rests on" was not run first; its two
gestures are the release's Deck checks, and the three open points are A70.

The author, 2026-10-13: "We need to have steering have a mode shift on
bumper/trigger dependent on the layout. in steering base if you are pressing
bumper/triggers the up and down on left stick will be empty binds, this
protects from that edge case kicking us out of the steering stateful set
accidently. I also want you to remove the 5sec delay that you added."

"5sec" is read as the 5 ms start delay of 90.65.

## Terms

- **Driver:** R1 or L1 in the default layout; R2 or L2, on the trigger's soft
  pull, in the alternative.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key`.
- **Bare `Steering`:** `Steering` on top of the stack, with no driver layer
  over it.
- **The exit:** in bare `Steering`, the left stick pushed up or down past
  29031 removes `Steering`. It repeats every 50 ms.
- **Mode shift:** a bind that, while its button is held, swaps one input
  source (here the left stick) for another group of binds.
- **The leak:** a cleanup press running past its guard chord with the driver
  held (A69, below).

## Why

Confirmed by the author on the Deck, 2026-10-13, and recorded as **A69**: a
`remove_layer` call makes a chord evaluate again, and in a burst of them an
evaluation can fail, so the interruptible bind beside the chord runs. It is
rare.

What it costs in `Steering`, with R1 held and the stick up:

| Step | Stack above Base | What happens |
|---|---|---|
| R1 held, stick at the rim | `Steering`, W layer | W |
| The W layer's edge cleanup leaks | `Steering` | The W layer is gone |
| The exit answers the stick | none | `Steering` ends |

Five builds tried to stop the leak itself (90.59, 90.60, 90.61, 90.63,
90.65). This plan leaves the leak alone and takes the third row away. A mode
shift is not a chord, so the leak cannot reach it.

## The change

Mirrored for both drivers, in both layouts.

| Bind | 90.65 | New |
|---|---|---|
| `Steering`, each driver | One repeating chord on itself that adds its driver layer | The same, and before it a Regular Press, not interruptible, that mode-shifts the left stick |
| `Steering`, a new left stick group, used only during the shift | None | D-pad, the settings of `Steering`'s stick: left A, right D, up and down an empty bind |
| The left edge of the ten Steering layers, the cleanup press | Starts 5 ms late | No start delay, as on 90.58 |

- The Regular Press is **not interruptible** because the chord beside it is
  active whenever the driver is held and would hold an interruptible one
  back (A27). It also keeps the press out of A69's reach.
- Both drivers shift to the **same** group: one new group a layout.
- Left and right keep A and D during the shift. Only up and down go empty,
  as the author said.
- Each driver then has two command entries of the three allowed (R109).
- No remove is added or taken out: 2,885 and 2,943 stay.

Not touched: the driver layers and everything above them, the guard chords,
the Entry Guard, the exit itself when no driver is held.

## What you would feel

Nothing in normal play: pressing a driver adds its layer at once, and that
layer has its own stick binds. After a leak:

| Step | 90.65 | New |
|---|---|---|
| The W layer's edge cleanup leaks, R1 held, stick up | `Steering` ends | Up is empty: `Steering` stays |
| Within 50 ms | Too late | R1's repeating chord adds the W layer again: W |

The exit still works the moment no driver is held.

## What it rests on

Steam's behaviour for a mode shift bound inside an action layer is not on
record here. The layout has four mode shifts, all in the Base set, none in a
layer (A34, unverified). Three things are open:

1. **Does the shift reach the driver layer's stick?** The driver layer has
   its own left stick group, where up and down add the stick modifiers
   (scroll). If a shift held from `Steering` underneath replaces that group
   too, the stick's scroll taps stop working while a driver is held.
2. **Is the shift on at the moment of the leak?** Either it stays on under
   the driver layer for as long as the driver is held, or it ends when the
   driver layer takes the driver over and has to start again when `Steering`
   is uncovered. In the second case it starts on a driver that is already
   held, as a key does (A10).
3. **If it has to start again, does it beat the exit?** Both come due as
   `Steering` is uncovered. If the exit runs first, the fault stays.

One check in the Steam editor answers all three before anything is built.
On 90.65, in the `Steering` layer, add to R1 a second command: Regular
Press, Mode Shift, Left Joystick, a D-pad with left A, right D and nothing
on up and down. Then:

- Hold R1 and tap the stick up a few times. Wheel steps as before means the
  shift does not reach the driver layer (point 1).
- Hold R1, tap the right stick touch rapidly and flick the left stick to
  the rim, for as long as it took to see the fault before. `Steering`
  staying means points 2 and 3 are fine.

## Tools, rules and tests

- **Simulator:** it does not model `mode_shift` (it lists the bind as
  unsupported). It needs the shift modelled for a bind in a layer, by the
  answers above. It will still never leak a guard, so a scenario forces the
  leak: the driver layer is taken off by hand with the driver held and the
  stick up, and `Steering` has to stay and the driver layer come back.
- **Audits:** the new group has no layer command, so the Window, Flow and
  Cleanup audits should read the layout as before; the build shows whether
  they do. The Cleanup audit keeps reading a delayed cleanup press, for the
  90.65 build.
- **Rules:** a new rule row for `Steering`: while a driver is held, bare
  `Steering` has no exit on the stick. **A70**, new: what a mode shift in a
  layer does, with the status the editor check gives it. **A68** (the 5 ms)
  is no longer relied on.
- **Tests:** the shape (two entries on each driver, the group's four binds,
  no start delay on the ten presses); the forced-leak scenario for both
  drivers and both directions; the exit with no driver held; the 90.65
  scenarios that state the 5 ms (P2, P3) frozen on 90.65.

## Build steps

1. The editor check above, by the author.
2. A builder in a new findings folder, reading the 90.65 snapshot: the new
   group, the two presses, the ten delays out.
3. The simulator's mode shift, then the tests.
4. Build audit, full suite, random walks against 90.65, VDFs, snapshot,
   record.

## Questions

1. **Run the editor check before the build, or build first?** If the shift
   reaches the driver layer's stick (point 1), the build breaks the stick's
   scroll while a driver is held and has to be redone another way. **My
   pick: the check first.** It is two gestures on the Deck.
2. **If the shift does reach the driver layer's stick, what then?** The
   design would need another shape, since up and down in the driver layers
   start the stick's scroll. **My pick: decide this only if the check says
   so.**
