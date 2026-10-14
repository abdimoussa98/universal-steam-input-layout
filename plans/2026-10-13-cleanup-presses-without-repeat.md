# Plan: no Hold to Repeat on the cleanup presses in Steering; the Entry Guard add out again

**Status, 2026-10-13:** built as **90.69**, from 90.68, as a trial off the line
(author: "build 90.69 but also build 90.70";
[release record](../findings/2026-10-13-steering-cleanup-presses-without-repeat/README.md)).
It is not installed: 90.70, also from 90.68, is the working layout. The
editor check in question 2 was not run first. One thing below turned out
wrong: on the simulator a stale layer under an input that is already held
does not clear on a repeat on 90.68 either, so the cost in "What you would
feel" is what I expect on the Deck, not something a test shows.

**Scope, decided by the author, 2026-10-13:** "all in steering". Every
cleanup press in the Steering layers, and none outside them. The plan was
first written for every cleanup press in the layout; the counts and costs
below are for the Steering scope.

The author, 2026-10-13: "create a plan. To have all of the cleanup functions
no longer have the regular press be repeating and undo the change to add
the layer the entry guard in the cleanup functions for now." Before it:
"we've never tried just making the regular press no longer repeating. Still
interruptible, but no longer repeating."

## Terms

- **Cleanup function:** on one input, an interruptible Regular Press that
  removes layers, beside an empty chord on the layer's owner buttons (its
  guard chord). While an owner is held the chord is active and holds the
  press back (A27).
- **The press:** that Regular Press. Today every one has Hold to Repeat on.
- **The leak:** the press running although an owner is held, because a
  burst of `remove_layer` calls failed the chord (A69, confirmed on the
  Deck).
- **Driver:** R1 or L1 in `Steering` (R2 and L2 in the alternative).

## Why

Every build that had the press had it repeating; checked in every saved
version from 90.24 to 90.68. A press that is interruptible and does not
repeat is the one combination that has not been on the Deck. The idea: a
repeating press tries again for as long as its input is held, so any failed
chord evaluation in that time lets it through. One that does not repeat
has only the moment its input is pressed.

## The change

| Bind | 90.68 | 90.69 |
|---|---|---|
| Every cleanup press in a Steering layer | Hold to Repeat on | Hold to Repeat off; still interruptible |
| The press on the left edge of the same ten layers | Adds the Entry Guard, then removes its list (90.67) | Removes its list only, as on 90.66 |
| Every guard chord | Not repeating | Unchanged |
| Cleanup presses outside the Steering layers | Hold to Repeat on | Unchanged |

How many, counted in 90.68 by the Cleanup audit's own reading; the same in
both layouts:

| | Presses |
|---|---|
| Cleanup presses in the layout | 529 default, 555 alternative |
| **Of them in Steering layers, changed** | **90** |
| On a stick touch | 20 |
| On a stick edge | 16 |
| On buttons, D-pad, stick clicks | 54 |

By layer: 7 in each driver layer (`Steering | R1: W Key`, `Steering | L1:
S Key`), 16 in each of the two Modifier 2 layers and the two stick
modifiers, 3 in each of the Tap Cover, the Double Tap Cover and the two
stick scroll layers. `Steering` itself, the Entry Guard and the two
Double Tap windows have no cleanup press.

Adds go back to 370 a layout; removes stay at 2,885 and 2,943.

Not touched:

- **Cleanup presses in every other layer** (439 and 465).
- **The other repeating Regular Presses,** which are not cleanup functions:
  delay resets, repeating removals that are not interruptible, repeating
  adds.
- **The Entry Guard's inverted chord,** its only cleanup; it is a chord.
- **90.68's order** in the Entry Guard's driver chords: add first, then
  remove the guard.
- **Start delays:** none comes back.

## What you would feel

Nothing while an owner is held. The difference is when a stale layer
clears, which is what a cleanup function is for:

| The input is | 90.68 | 90.69 |
|---|---|---|
| Pressed after the layer went stale | Clears at once | Clears at once |
| Already held when the layer goes stale, or when a stale layer lands or is uncovered under it | Clears on the next repeat | Stays until the input is pressed again |

The second row is the cost. It is largest on the stick touches, where a
thumb rests for seconds: a Steering layer left on by a missed release
then stays until that thumb lifts and comes back, or the stick reaches
the rim. It follows from your held-input
rule: a layer command that does not repeat does not run on an input that
was already held.

## What a throwaway candidate showed

Built outside the repo from 90.68, not installed, with **every** cleanup
press in the layout changed, so it overstates the Steering scope.

- **Random walks on the simulator,** 800 a layout at each rate, against
  90.68 without its Entry Guard add:

  | Layout, releases missed | Log differs | A layer left on after everything is let go | After a thumb on each stick |
  |---|---|---|---|
  | Default, none | 1 of 775 | 0, was 0 | 0 |
  | Default, one in ten | 7 of 776 | 23, was 23 | 0 |
  | Alternative, none | 1 of 800 | 0, was 0 | 0 |
  | Alternative, one in ten | 6 of 800 | 13, was 13 | 0 |

  My reading: on the simulator the repeat rarely matters. The simulator
  decides a guard once and never leaks, so this says nothing about the
  fault.
- **The build audit fails,** and only for one reason: the audit knows a
  cleanup function by its repeat. Without it the audit sees no cleanup
  function anywhere: 64 touch, 47 edge and 31 button findings (R169 to
  R171), 192 hidden exits (R136), and the Flow audit's review list.
  Budget and Window pass.

## Tools, rules and tests

- **Classifier** (`steam_layout/flow_model.py`): an interruptible Regular
  Press that only removes, beside a chord on the same input, is a cleanup
  function with or without Hold to Repeat. The five presses that remove
  without repeating today (in the Double Tap windows) have no chord, so
  they stay what they are. The `CLEANUP_GUARDS` reading of 90.67 stays for
  the 90.67 and 90.68 builds.
- **Fix pipeline:** `cleanup_lists` writes a repeating press when it
  copies a cleanup; it writes a non-repeating one from 90.69.
- **Simulator:** no change. It already runs a non-repeating layer command
  only on a fresh press.
- **R133** (the cleanup shape) says "with Hold to Repeat". Its row changes
  to "without" from 90.69, on the author's word, as a trial. **R176** (the
  Entry Guard add) is retired with a "for now". **A6** and **A9**, where a
  cleanup's repeat is what they are relied on for, are checked row by row.
- **Tests:** 51 test modules read `hold_repeats`. The ones that state a
  repeating cleanup press read the 90.68 build; scenarios that wait for a
  repeat to clear a stale layer under a held input are rewritten to press
  again, or read 90.68 where the old behaviour is the point. The 90.67
  tests read the 90.67 build. New: every cleanup press is interruptible
  and not repeating; no cleanup function adds a layer; only those presses
  differ from 90.68.

## What it rests on

- **Whether it narrows the leak is not known.** The fault's gesture flicks
  the stick to the rim while removes arrive, so a fresh press can still
  meet a failed evaluation. Whether a press that does not repeat also
  runs when its chord fails in the middle of a hold is not on record. The
  Deck decides.
- **With the Entry Guard add out, a leak costs what it did on 90.65:** the
  driver's layer goes and `Steering`'s exit ends `Steering` if the stick
  is up or down. That makes the fault's gesture a clean test of this one
  change.
- **Stale layers under a held input stay longer** (above). The random
  walks end by letting everything go and touching both sticks, so they do
  not measure how long.

## Build steps

1. A builder in a new findings folder, reading the 90.68 snapshot: the
   ten adds out (asserted equal to 90.66's presses), then Hold to Repeat
   off on every cleanup press, counted against the table above.
2. The classifier and the fix, then the tests.
3. Build audit, full suite, random walks against 90.68, VDFs, snapshot,
   record.

## Questions

1. **Answered:** the scope is every cleanup press in the Steering layers.
2. **A quick editor check first?** On 90.68 in `Steering | R1: W Key`,
   turn Hold to Repeat off on the left edge's Regular Press, hold R1, spam
   the right stick touch and flick the left stick. W dropping means the
   press still leaks without its repeat, and the build would not help.
   **My pick: run it first.** It is one setting and one gesture.
