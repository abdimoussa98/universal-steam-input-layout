# No Hold to Repeat on the cleanup presses in the Steering layers (90.69, a trial)

Built on 2026-10-13 from the **90.68** snapshot, both layouts, on the author's
word: "we've never tried just making the regular press no longer repeating.
Still interruptible, but no longer repeating", "have all of the cleanup
functions no longer have the regular press be repeating and undo the change
to add the layer the entry guard in the cleanup functions for now", scope
"all in steering", then "build 90.69 but also build 90.70". 90 layers in
each layout.

**Outcome, 2026-10-13:** not adopted. The author, on the Deck: "the only solution that works is 90.70. we will get leaks and this precaution works".
The build stays as a snapshot. Noted by the author as an assumption (A71):
a press that does not repeat leaks less often. It has not been counted.

**It is not installed.** 90.70 is built from 90.68 as well and is the
working layout. 90.69 is a trial off the line, saved for the Deck:

- `versions/neptune/90.69/single-set-default_hold-gyro_90.69.vdf`
- `versions/neptune/90.69/single-set-alternative_hold-gyro_90.69.vdf`

It builds the [plan](../../plans/2026-10-13-cleanup-presses-without-repeat.md),
for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).

| | Default | Alternative |
|---|---|---|
| Cleanup presses in the layout | 529 | 555 |
| **In the Steering layers, Hold to Repeat taken off** | **90** | **90** |
| Left-edge presses that lose the Entry Guard add | 10 | 10 |
| Adds, 90.68 to 90.69 | 380 to 370 | 380 to 370 |
| Removes, unchanged | 2,885 | 2,943 |

## Terms

- **Cleanup function:** on one input, an interruptible Regular Press that
  removes layers, beside an empty chord on the layer's owner buttons (its
  guard chord). While an owner is held the chord is active and holds the
  press back (A27).
- **The press:** that Regular Press.
- **The leak:** the press running although an owner is held, because a
  burst of `remove_layer` calls failed the chord (A69, confirmed on the
  Deck).
- **Driver:** R1 or L1 in `Steering` (R2 and L2 in the alternative).

## The changes

[Default](single-set-default_hold-gyro_90.69-changes.txt) and
[alternative](single-set-alternative_hold-gyro_90.69-changes.txt), against
90.68: 10 layers, 90 changes each.

| Bind | 90.68 | 90.69 |
|---|---|---|
| Every cleanup press in a Steering layer | Hold to Repeat on | Off; still interruptible |
| The press on the left edge of the same ten layers | Adds the Entry Guard, then removes | Removes only, as on 90.66 (asserted by the builder) |
| Every guard chord | Not repeating | Unchanged |
| Cleanup presses in every other layer (439 and 465) | Hold to Repeat on | Unchanged |

By layer: 7 presses in each driver layer, 16 in each of the two Modifier 2
layers and the two stick modifiers, 3 in each of the Tap Cover, the Double
Tap Cover and the two stick scroll layers. 20 are on a stick touch, 16 on
a stick edge, 54 on buttons, the D-pad and stick clicks.

Kept from 90.68: the Entry Guard's driver chords add the driver's layer
first, then remove the guard.

## Why

Every build that had the press had it repeating (checked in every saved
version from 90.24 to 90.68). A repeating press tries again for as long as
its input is held, so any failed chord evaluation in that time lets it
through. One that does not repeat has only the moment its input is
pressed. Whether that is enough is what the Deck has to say.

## One tool changed

The Cleanup audit knew a cleanup function by its repeat. It now also reads
an interruptible Regular Press of removes beside a chord as one
([`steam_layout/flow_model.py`](../../steam_layout/flow_model.py)). Up to
90.68 no press of removes without a repeat has a chord beside it, so no
earlier build reads differently. With that the build audit is clean on
both candidates.

## Tests

[`tests/test_scenarios_90_69.py`](../../tests/test_scenarios_90_69.py),
five, all on the 90.69 build: the 90 presses are interruptible, do not
repeat and only remove; every cleanup press outside the Steering layers
still repeats; only those presses differ from 90.68; scenarios 90.69 N1 (a
stale driver layer clears when the stick reaches the rim, and no guard
lands) and N2 (with the driver held no cleanup runs at the rim or on a
stick touch).

No rule row changed for it: R133 names the trial, and its shape stands on
the working layout.

## Validation

- **Build audit:** clean on both candidates, against 90.68.
- **Pre-flight:** both VDFs exported and verified against their JSON.
- **Random walks** with 90.68 and 90.70, in
  [the 90.70 record](../2026-10-13-entry-guard-in-every-steering-cleanup/README.md#validation).
- **Full suite:** run once for both builds; see the same record.

## What it rests on

- **Whether it narrows the leak is not known.** The fault's gesture flicks
  the stick to the rim while removes arrive, so a fresh press can still
  meet a failed evaluation.
- **A leak costs what it did on 90.65.** With the Entry Guard add out, the
  driver's layer goes and `Steering` ends if the stick is up or down. That
  makes the fault's gesture a clean test of this one change.
- **A stale layer under an input that is already held** should stay until
  that input is pressed again, where a repeating press would clear it on
  its next repeat. That is my expectation for the Deck from the author's
  held-input rule. The simulator does not show it: there the stale layer
  stays on 90.68 as well, because the simulator does not run a held-back
  repeating press when its guard goes.
- **The simulator never leaks a guard,** so no test here says anything
  about the fault.

## On the Deck

Load the 90.69 VDF and check that the title shows `:: 90.69`.

1. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction, for as long as it took
   to see the fault before. W dropping or `Steering` ending means a press
   that does not repeat still leaks.
2. Rock R1 and L1 with the stick out: W, S, W, S.
3. Normal driving for a while: does any Steering layer stay on after its
   button is let go, until you press something else?
