# Both drivers held in Steering (audit of 90.56)

Read-only, 2026-10-11, on the author's report. Nothing in the layouts
changed, and nothing here ran on the Deck. The changes it leads to are in the
[plan](../../plans/2026-10-11-two-drivers-in-steering.md), which is not built.

The report, on 90.56: with R1 held for W and L1 pressed for Modifier 2,
letting go of R1 with the stick still up or down ends `Steering` before the S
layer applies, although L1 is held. And applying Modifier 2 should take you
out of the stick's scroll layer and out of its window.

    PYTHONPATH=.:tests python3 findings/2026-10-11-two-drivers-in-steering/traces.py [variant] [layout.json]
    PYTHONPATH=.:tests python3 findings/2026-10-11-two-drivers-in-steering/matrix.py [variant] [layout.json]
    python3 findings/2026-10-11-two-drivers-in-steering/prototype.py <out dir> [changes]

Their output is in [results.txt](results.txt). `prototype.py` writes trial
layouts for the other two; it installs nothing.

## Terms

- **Driver:** R1 for W and L1 for S in `Steering` (the triggers' soft pull in
  the alternative layout). The **first driver** is the one held first, the
  **second** the one pressed while it is held.
- **W layer, S layer:** `Steering | R1: W Key` and `Steering | L1: S Key`.
- **Stick window:** `Steering | LS Up: Double Tap` or
  `Steering | LS Down: Double Tap`, open for 150 ms after a stick tap.
- **Steering's exit:** up or down past 29031 in `Steering` itself, which
  removes `Steering` with a beep.
- **Quick tap:** the second driver let go inside 200 ms. The Modifier 2
  layer's own Release answers (R159).
- **Gesture:** one press sequence of `matrix.py`. One driver is held, the
  stick is brought to one of eight states (centre, out, a window, a scroll
  layer), the other driver is pressed for 100 or 400 ms, the stick is moved or
  not, one driver is let go and then the other. 640 per layout, half with a
  bind exposed under a held button firing at once and half on its next repeat
  (A9).
- **Flag:** one thing wrong in one gesture, such as `Steering` gone while a
  driver is held. A gesture can carry several.

## What 90.56 does

Both layouts give the same counts: 664 flags in 640 gestures.

| Fault | Gestures | When |
|---|---|---|
| `Steering` ends when the first driver is let go | 128 | The stick at the rim, up or down, from every stick state and for both press lengths. The reported fault (T1) |
| `Steering` ends on the quick tap | 56 | The second driver let go after 100 ms with the stick at the rim (T3) |
| The second driver types its drive key before Modifier 2 | 288 | It is pressed while a stick window is open (T2). In 96 of them W and S are down together and Modifier 2 has not come 100 ms after the press |

No gesture leaves a layer or a key behind at the end, and the held driver's
key is never missing while `Steering` stays.

**The first driver let go (T1).** `Steering | R1!L1: Modifier 2` binds only
L1, so the W layer's own R1 Release answers. It removes the Tap Cover, the
Modifier 2 layer and the W layer. `Steering` is then the top layer with L1
held and the stick at the rim. Its exit and its repeating L1 bind are both
due; the exit runs first under both A9 readings, and the S layer never comes.
With the stick at centre the S layer comes.

**The quick tap (T3).** The quick tap's list removes the W layer too, and
`Steering` meets the stick the same way. With the stick at centre
`Steering`'s R1 bind adds the W layer again.

**The window (T2).** A stick window retypes both drivers as plain,
uninterruptible W and S (author, 2026-10-01: "There are no chords, so
Modifier 2 can't be entered during the window"). L1 pressed there types S
beside W until the window closes itself. The W layer's chord is then exposed
under the held L1 and adds Modifier 2. Its 200 ms cover timer starts only
then, so an L1 hold of up to 350 ms can still end as a quick tap.

**Already as asked.** From a stick modifier, `Steering | LS: Tap Cover`, a
scroll layer or `Steering | LS: Double Tap Cover`, the second driver's press
removes those layers and adds Modifier 2 at once. None of them binds a
driver, so the W or S layer's chord answers.

**As designed, and left alone.** The last driver let go with the stick at
the rim ends `Steering`: no driver is held, and a full push is the exit.

## The prototype

`prototype.py` applies the plan's three parts to the 90.56 snapshot.

| Parts applied | Flags, default layout |
|---|---|
| None (90.56) | 664 |
| 1: the first driver's Release hands over | 536 |
| 1 and 2: the window's chord adds Modifier 2 | 32 |
| 1, 2 and 3: the quick tap leaves the first driver's layer on | 0 |

The alternative layout also has 0 with all three. The other shape of part 2
(the chord only removes the window) and of part 3 (the quick tap keeps its
whole list and adds the layer back) give 0 as well: the simulator can't tell
them apart. T4 is the rocking sequence, T5 a window entered from the S layer,
T6 a missed release of the second driver.

Part 3 is decision D2 of the
[owner release audit](../2026-10-11-owner-release-audit/README.md#6-decisions-for-the-author)
of the same day, whose `first_driver.py` replays the same choice on shorter
lists and finds the same: `Steering` stays when the layer is left on or put
back, and ends when it is taken off.

**The audits.** The prototype files are written without the fix pipeline. In
a scratch copy of `steam_layout/` with the two model changes of the plan's
part 4, the pipeline changed four binds per layout (the Steering Modifier 2
layer leaves the stick touch cleanups of `L1: Tap Cover` and
`R1: Tap Cover`), the build audit was clean on both layouts, and the sweep
still gave 0. Without the model changes the pipeline lengthens 46 cleanup
lists for part 2 and trims most of the quick tap's list for part 3.

**The tests.** The suite passes on 90.56 as it is (1,193 tests, 25 expected
failures). On the prototype, 24 test modules run in the scratch copy fail in
at least five tests that state the old behaviour; the plan's part 5 names
them. The
whole suite could not be run there, because the frozen builders put the
repository itself back on the import path.

## What the simulator can't say

- It holds a control or not. "Stick out" is the stick at the rim; a half push
  in Modifier 2 scrolls and does not reach `Steering`'s exit.
- It runs one array as one step, so it can't show a bind firing between two
  commands. Part 1 puts its add first for that reason.
- A repeating bind always repeats. The author's report of 2026-10-10, that a
  repeating chord with more than one sub-command does not fire its repeat, is
  not modelled; the W and S layers' Modifier 2 chords have ten.
