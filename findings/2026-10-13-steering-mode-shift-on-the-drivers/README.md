# The drivers mode-shift `Steering`'s up and down to empty binds (90.66)

Built on 2026-10-13 from the **90.65** snapshot, both layouts, on the author's
word: "We need to have steering have a mode shift on bumper/trigger dependent
on the layout. in steering base if you are pressing bumper/triggers the up
and down on left stick will be empty binds, this protects from that edge case
kicking us out of the steering stateful set accidently. I also want you to
remove the 5sec delay that you added", then "Just build it". 90 layers in
each layout. Nothing here has run on the Deck.

It builds the [plan](../../plans/2026-10-13-steering-mode-shift-on-the-drivers.md),
for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).

| | Default | Alternative |
|---|---|---|
| New groups | 1 | 1 |
| Driver binds changed in `Steering` | 2 | 2 |
| Left-edge presses without their 5 ms | 10 | 10 |
| Removes in 90.65 | 2,885 | 2,943 |
| **Removes in 90.66** | **2,885** | **2,943** |

## Terms

- **Driver:** R1 or L1 in the default layout; R2 or L2, on the trigger's soft
  pull, in the alternative.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key`.
- **Bare `Steering`:** `Steering` with no driver layer over it.
- **The exit:** in bare `Steering`, the left stick pushed up or down past
  29031 removes `Steering`. It repeats every 50 ms.
- **Mode shift:** a bind that, while its button is held, swaps one input
  source (here the left stick) for another group of binds.
- **The leak:** a cleanup press running past its guard chord with the driver
  held.

## Why

Confirmed by the author on the Deck, 2026-10-13 (**A69**): a `remove_layer`
call makes a chord evaluate again, and in a burst of them an evaluation can
fail, so the interruptible bind beside the chord runs. It is rare. In
`Steering` it took the driver's layer off with the driver held and the stick
up, and the exit underneath then ended `Steering`.

Five builds tried to stop the leak (90.59, 90.60, 90.61, 90.63, 90.65). This
one leaves it alone and takes away what it costs. A mode shift is not a
chord, so the leak cannot reach it.

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.65: 11 layers, 13 changes each.

| Bind | 90.65 | 90.66 |
|---|---|---|
| `Steering`, each driver | One repeating chord on itself that adds its driver layer | A Regular Press, not interruptible, quiet, that mode-shifts the left stick; then the same chord |
| `Steering`, a new left stick group, a mode-shift target | None | `Steering`'s own stick settings; left A, right D; up and down an empty bind |
| The cleanup press on the left edge of ten Steering layers | Starts 5 ms late | No start delay; the press and guard are 90.58's again |

- The press is **not interruptible** because the chord beside it is active
  whenever the driver is held and would hold an interruptible one back
  (A27). That also keeps it out of A69's reach.
- Both drivers shift to the same group (13360 in the default layout, 13373
  in the alternative).
- Each driver has two command entries of the three allowed (R109).

Not touched: the driver layers and everything above them, the guard chords,
the Entry Guard, the exit when no driver is held.

## What you would feel

Nothing in normal play: pressing a driver adds its layer at once, and that
layer has its own stick binds. After a leak:

| Step | 90.65 | 90.66 |
|---|---|---|
| The W layer leaks off, R1 held, stick up | `Steering` ends | Up is empty: `Steering` stays |
| Within 50 ms | Too late | R1's repeating chord adds the W layer again: W |

A and D stay down through it. With no driver held, up and down end
`Steering` as before.

## The simulator changed

- **A mode shift bound in a layer is modelled** (it was listed as
  unsupported). It is on while its layer answers the held driver, and it
  swaps only that layer's own group for the source. The Base set's four mode
  shifts stay unsupported, as before.
- **`drop`** takes layers off by hand, for a leak the simulator never
  produces itself.

## Rules, the register and the tests

- **R175** is new: while a driver is held, bare `Steering` has no exit on
  the left stick.
- **A69** (confirmed) and **A70** (unverified: what a mode shift in a layer
  does) are new. **A34** names the new group. **A68** (the 5 ms) rests on
  nothing since this build.
- **New tests,** [`tests/test_scenarios_90_66.py`](../../tests/test_scenarios_90_66.py),
  ten: the group's four binds; the press before each driver's chord; no
  other layer has a mode shift; the ten presses are 90.58's; only the two
  drivers and ten edges differ from 90.65, and no remove; and scenarios
  90.66 S1 to S5 (the leak with the stick up or down keeps `Steering` and
  the driver layer comes back; the same leak ends `Steering` on the 90.65
  build; the exit with no driver held; A and D through the leak; the stick
  still scrolls in the driver layer).
- **On the 90.65 build** (`frozen`): the 90.65 shape tests and scenarios
  90.65 P2 and P3, which state the 5 ms.

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **Random walks, the whole log compared** with 90.65 ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with one release
  in ten missed.

  | Layout, releases missed | Walks that finish | Log differs | A layer left on, 90.65 | 90.66 | After a thumb on each stick |
  |---|---|---|---|---|---|
  | Default, none | 11,715 | 257 | 21 | 21 | 0 and 0 |
  | Default, one in ten | 11,722 | 273 | 298 | 299 | 0 and 0 |
  | Alternative, none | 12,000 | 252 | 23 | 23 | 0 and 0 |
  | Alternative, one in ten | 12,000 | 264 | 187 | 188 | 0 and 0 |

- **The walks that differ,** from 1,500 default walks with no release
  missed, 33 of them differing, each replayed to its first difference:
  - 25 press a driver in bare `Steering` with the stick left or right. A
    or D is handed to the shift's group and then to the driver's layer, in
    the same instant. Whether the key blips on the Deck is not known.
  - 7 have a driver held with `Steering` answering the stick, and the
    stick goes up or down: 90.65 ends `Steering`, 90.66 does not. That is
    R175.
  - 1 was not classified.
- **Full suite:** 1,278 tests in 113 modules, with the same 25 expected
  failures. Three registry tests failed on the wording of the new rule and
  assumption rows (a checker name, A69's status cell, R133 not naming A69);
  the rows are fixed and the tests pass.
- **Unverified assumptions:** 51, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 406 scenarios.

## What it rests on

- **A70, unverified.** The layout never had a mode shift inside a layer.
  The plan offered a two-gesture check in the Steam editor first; the build
  went ahead without it. Three things have to hold on the Deck:
  1. The shift does not reach the driver layer's stick. If it does, the
     stick's scroll taps stop while a driver is held.
  2. The shift is on at the moment of the leak, or comes on when `Steering`
     is uncovered under the held driver.
  3. In the second case it comes on before the exit answers the stick.
- **The simulator assumes all three,** and it never leaks a guard, so the
  scenarios force the leak. They show the binds do what was asked if A70
  holds, not that the fault is gone.
- **The leak still happens.** The driver's key drops for up to 50 ms when
  it does.
- **Up and down no longer end `Steering` whenever a driver is held,** also
  where no leak is involved: a driver held under a layer that leaves the
  stick to `Steering`. The walks above found that case.

## On the Deck

Check first that the configurator's title shows `:: 90.66`.

1. Hold R1 and tap the stick up a few times, then down: one wheel step per
   tap, as before. None means the shift reaches the driver layer's stick.
2. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays.
3. With no driver held, push the stick fully up: `Steering` ends.
4. Rock R1 and L1 with the stick out: W, S, W, S.
