# The ring inverted on the left edge of ten Steering layers (90.63)

Built on 2026-10-12 from the **90.62** snapshot, both layouts, on the author's
word: "We need to invert the left stick edge for the chorded inverted clean
functions we just added to the left stick edge bind. every where in steering
except in entry steering guard", then "just do it". 90 layers in each layout.
Nothing here has run on the Deck.

It is for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).

| | Default | Alternative |
|---|---|---|
| Groups changed | 10 | 10 |
| Removes in 90.62 | 2,885 | 2,943 |
| **Removes in 90.63** | **2,885** | **2,943** |

## Terms

- **Inverted chord:** a Chorded Press with Invert Activation. It runs while
  its own input is released and no chord button is held (A61). The author,
  2026-10-12: "if the chord or the button is pressed then the bind doesn't
  fire, otherwise it will always fire."
- **The ring:** the stick's outer ring, the edge input. **Inverted ring:**
  the group's Outer Ring Binding Invert. The edge then counts as pressed
  while the stick is inside the ring and released at the rim.
- **The ten layers:** the two driver layers (W and S), the two stick
  modifiers, `Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`,
  the two stick scroll layers and the two Steering Modifier 2 layers.

## The one change

In each of the ten layers the left stick's group gets Outer Ring Binding
Invert ([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)). No bind,
list or activator setting changes; the fix pipeline changed nothing.

| When the edge's cleanup chord runs | 90.61, 90.62 | 90.63 |
|---|---|---|
| A driver held, stick anywhere | Never | Never |
| No driver, stick off the rim | Runs | Never |
| No driver, stick at the rim | Never | Runs |

That is where the press of 90.58 ran. `Steering | LS: Entry Guard` keeps its
normal ring.

**The timers.** Four of the ten edges also hold a Soft Press: the hold timer
of the two stick modifiers (200 ms) and the cover timer of the two scroll
layers (150 ms). The author: "soft presses dont respect the inversion so its
fine" (A67, new). They state no inversion of their own and run past 13276 as
before.

## What you would feel

Nothing changes while a driver is held. After a missed driver release, the
layer left on clears when the stick reaches the rim, a thumb touches a stick
or a bumper is pressed. On 90.62 it cleared with the stick anywhere off the
rim.

## Two tools changed

Both read "inverted" as the group's setting or the entry's. Now:

- **Simulator:** a Soft Press is inverted only by its own setting (A67). A
  chord with Invert Activation on an inverted ring runs at the rim with no
  chord button held.
- **Budget audit** (R111): a Soft Press on an inverted ring is not counted as
  an inverted edge unless it says so itself. One new test.

Every Soft Press on an inverted ring in the earlier snapshots states its own
inversion too (116 of them), so no older build reads differently.

## Rules, the register and the tests

- **R111:** the ten chords were registered in 90.61 and 90.62 and match
  as they are. The rule's row says the ring is inverted there since 90.63.
- **R133:** its entry for the ten edges says where the chord now runs.
- **A67** is new. **A19** (an inverted ring misses some returns to centre,
  the author's Deck test of 2026-10-01), **A61** and **A66** name these ten
  edges.
- **New tests,** [`tests/test_scenarios_90_63.py`](../../tests/test_scenarios_90_63.py),
  seven: only the ten groups differ from 90.62, by that one setting; no
  other Steering layer has an inverted ring; the timers state no inversion;
  and scenarios 90.63 G1 to G4 (the rim with a driver held keeps the driver
  layer; a missed release clears at the rim and not before; pressing the
  driver again shuts the chord off; the timers still run with the stick
  out).
- **On the 90.62 build** (`frozen`): scenario 90.61 E2, which states that a
  missed release clears off the rim.

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **Rocking the bumpers:** the nine tests of `tests/test_modifier_rocking.py`
  and the 90.62 rocking scenarios pass.
- **Random walks, the whole log compared** with 90.62 ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with one release
  in ten missed.

  | Layout, releases missed | Walks that finish | Log differs | A layer left on, 90.62 | 90.63 | After a thumb on each stick |
  |---|---|---|---|---|---|
  | Default, none | 11,715 | 0 | 21 | 21 | 0 and 0 |
  | Default, one in ten | 11,723 | 34 | 298 | 299 | 0 and 0 |
  | Alternative, none | 12,000 | 0 | 23 | 23 | 0 and 0 |
  | Alternative, one in ten | 12,000 | 36 | 186 | 188 | 0 and 0 |

  With no release missed the two builds play alike.
- **The walks that differ** ([`diverge.py`](diverge.py),
  [`diverge.txt`](diverge.txt)): 72 are listed. In every one the first
  difference is the edge chord removing a Steering layer nobody holds: in
  34 the 90.62 build does it first, off the rim, and in 38 the 90.63 build
  does, at the rim.
- **Full suite:** 1,252 tests in 110 modules pass, with the same 25 expected
  failures.
- **Unverified assumptions:** 49, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 395 scenarios. The
  report was written with 90.64 installed, which has the same binds.

## What it rests on

- **The chord is live exactly where the fault happened.** On 90.58 the press
  ran at the rim although a bumper was held, and `Steering`'s exit below
  ended `Steering`. 90.61 could not run at the rim at all. Here the chord
  can, so it has to see the held bumper every time (A66, unverified).
- **A67,** the author's report. If a timer did follow the ring, the stick's
  tap and hold would break in the four timer layers.
- **A19.** An inverted ring missed some returns to centre on the Deck. A miss
  here leaves the cleanup off at the rim, or running at centre with no
  driver held. The stick touches' cleanups are unchanged.
- **The simulator cannot show the fault.** It never misses a held driver.

## On the Deck

Check first that the configurator's title shows `:: 90.63`.

1. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays, W stays.
2. Hold R1 and tap the stick up eight times, with a hold past 200 ms in
   between: one wheel step per tap, none for a hold (A67).
3. Hold R1, push the stick up or down halfway, lift a thumb from either
   stick: `Steering` stays, W stays.
4. Rock R1 and L1 with the stick out: W, S, W, S.
