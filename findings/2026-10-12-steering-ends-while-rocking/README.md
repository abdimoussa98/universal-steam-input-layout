# `Steering` ends while the bumpers are rocked with the stick up (90.58)

Read-only, 2026-10-12, on the author's report. This record changed nothing
in the layouts and installed nothing, and nothing here ran on the Deck.

Every number is from the 90.58 snapshot in `versions/neptune/90.58/`. While
this was written another session installed
[90.59](../2026-10-12-repeating-guards-on-the-stick-layers/) into the working
layouts: the same binds, with Hold to Repeat on 18 guard chords. The gap and
the right pad gesture below give the same counts on it.

The report, on 90.58: in `Steering`, R1 held for W, the stick up, rocking
between L1 (S) and R1 (W). Sometimes `Steering` and all its layers are
cleared. "With that rocking behavior, it should be blocking."

    PYTHONPATH=. python3 findings/2026-10-12-steering-ends-while-rocking/probe.py
    PYTHONPATH=. python3 findings/2026-10-12-steering-ends-while-rocking/trial_exit.py

Their output is in [results.txt](results.txt) and
[trial-exit.txt](trial-exit.txt). The first takes about five minutes.

## Terms

- **Driver:** R1 for W and L1 for S in `Steering` (the triggers' soft pull in
  the alternative layout). The **W layer** is `Steering | R1: W Key`, the
  **S layer** its twin.
- **Rock:** one bumper held, the other pressed, the first let go, and round
  again.
- **Steering's exit:** up or down past 29,031 of 32,767, about nine tenths of
  the way out, while `Steering` itself answers the stick. It removes
  `Steering` with a beep and a low bump.
- **Bare `Steering`:** no layer above `Steering` answers the stick.
- **A9:** whether a bind fires at once when the layer above it is removed
  while its input is held. Unverified, so every replay runs both ways.

## The cause

Two things remove `Steering`: its own exit, and a stick click inside the
Start or Select menu layers (results, section 1). A rock touches neither
menu button, so every clear here is the exit.

The W layer, the S layer, the two Modifier 2 layers and every stick layer
bind up and down, and so block the exit. The exit gets through when all of
them are off for a moment with the stick at the rim. `Steering` then has two
repeating binds due inside 50 ms: the exit, and the add of the held
bumper's layer. On the simulator the exit runs first whenever both are due.

## With a bumper always down and nothing else touched, it never ends

24,000 random rocks, both layouts, both readings of A9: `Steering` stays in
all of them (section 2). The hand-over of 90.57 does what it was built for.

## Three ways the stick meets bare `Steering`

| | Gesture | When it ends |
|---|---|---|
| 1 | **A gap.** The held bumper comes up before the other goes down | A9 true: any gap, also 0 ms. A9 false: a gap of 50 ms or more (section 3) |
| 2 | **A short touch of the right pad.** Under 150 ms, it opens `RTP: Double Tap` for 150 ms. The second bumper goes down inside that window | The first bumper comes up inside the window, or (A9 false) up to 50 ms after it closes (section 4). A bumper is down throughout |
| 3 | **A stick window.** The stick leaves up inside 200 ms of a hand-over, a bumper comes up inside the stick's 150 ms window, and the stick is back at the rim inside 50 ms | A9 false only (section 5) |

**1, the gap.** The W layer's own Release removes the W layer and the stick
layers. Nothing is left above `Steering`. The audit of 2026-10-11 recorded
this as designed: "the last driver let go with the stick at the rim ends
`Steering`". In a rock it is the same state reached by accident.

**2, the right pad.** `RTP: Double Tap` binds both bumpers: a wheel step on
the press, and a Release that names no Steering layer. So the second
bumper's press scrolls one step and never enters Modifier 2, and the held
bumper's key is let go while the window is on. Then:

- The first bumper comes up inside the window. The window answers the
  Release, and the first bumper's layer stays on with its bumper up. Its
  cleanup press on the second bumper is no longer guarded, fires, and removes
  the layer. `Steering` is bare under the held second bumper.
- The first bumper comes up just after the window closes. Modifier 2 waits
  for the next repeat of the entry chord, so the first bumper's own Release
  answers and removes its layer.

With the stick at centre or to the side the same gesture is harmless:
`Steering` adds the held bumper's layer back.

**3, the stick window.** After a hand-over the stick modifier lands afresh
and its 200 ms timer starts again, so a stick that leaves up inside 200 ms
counts as a tap and opens the window, however long it had been held. A
bumper let go inside a stick window removes both driver layers. That is
R174's to-do in the register (author, 2026-10-12: "just dont touch the
window for now").

## None of it is new in 90.58

The gap and the right pad touch end `Steering` the same way on 90.38, 90.48,
90.54, 90.56 and 90.57 (section 6). Until 90.57 letting go of the first
bumper at the rim ended `Steering` every time, so a rock there never got far
enough to show them.

## Two trials, in memory, not installed

- **The cleanup press on the other bumper also adds that driver's layer**,
  stored last so that it runs first (R174's shape; that bumper is certainly
  held when the press fires). Of 1,496 timings of the right pad gesture,
  `Steering` ends in 468 on 90.58 and 104 with the change. The 364 with
  the first bumper up inside the window are gone. The 104 just after the
  window, under A9 false, stay (section 7).
- **The exit without Hold to Repeat** ([trial-exit.txt](trial-exit.txt)).
  If A9 is false, the gap and the right pad gesture never end `Steering` (0
  of 20 and 0 of 198), a fresh push to the rim still exits, and a bumper let
  go at the rim keeps `Steering` until the stick comes back and goes out
  again. If A9 is true, nothing changes. The repeat is there by R114
  (`test_threshold_exits_that_change_layers_repeat`), so this is the
  author's call. Loaded on the Deck it would also settle A9.

Not trialled: `Steering | LS: Entry Guard` added by the last bumper's
Release. It already covers a stick held out through the entry, types W or S
from the stick, and hands over on a bumper press.

## What the simulator can't say

- It holds a control or not: "stick up" is the stick at the rim.
- Whether the exit or the add of the held bumper's layer runs first on bare
  `Steering` is its own ordering. On the Deck it may go either way, which
  would also read as "sometimes".
- **A fourth candidate it can't show: a guard that comes up late.** This is
  the suspicion 90.59 was built on the same day, for `Steering` ending while
  the stick is thrown about with R1 held: a layer lands on a thumb that is
  already down, its repeating cleanup press fires at once, and its guard
  chord is not up yet. On the simulator the guard always wins (A36,
  unverified). A rock at the rim is full of such landings. Each hand-over
  lands the Modifier 2 layer, then the W or S layer and the stick modifier,
  then the Tap Cover 200 ms later, all on a stick that is out with a thumb on
  it. 90.59 makes the guard repeat in the stick modifier and the Tap Cover.
  The W layer, the S layer and the two Modifier 2 layers have the same pair
  on four inputs each (the left edge, both stick touches, the right edge),
  and are not in it: 16 guards.

## On the Deck

On 90.59, which is what is loaded now. With the stick up at the rim and R1
held:

1. Press L1 fully, then let go of R1, then press R1, then let go of L1.
   Slowly, ten times, the right thumb off the pad. By the simulator
   `Steering` never ends.
2. Let go of R1 and then press L1, a clear gap. It should end, with the
   exit's beep.
3. Tap the right pad and rock at once. A wheel step as the second bumper
   goes down means the window answered it.

If step 1 ends `Steering` with the right thumb off the pad and no gap, none
of the three routes explains it and the late guard is what is left: the 16
guards above are the next thing to make repeat.
