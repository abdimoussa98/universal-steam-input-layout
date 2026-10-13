# Plan: rocking in `Steering` the way the bumper modifiers do it

**Status, 2026-10-12:** built as **90.62**, from 90.61, on the author's word
("start building";
[release record](../findings/2026-10-12-steering-rocking-like-the-bumper-modifiers/README.md)).
The check asked for under "Answers so far" came back: with R1 held, pressing
and letting go of L1 leaves W held, so an uncovered layer types its key.

The author, 2026-10-12, on the Deck: holding W, pressing L1 and letting go of
R1 gives S, "and that is working. But if I try and go back, it isn't." Then:
"compare how we do rocking and mod two outside of steering ... if I'm in R1
and I hit L1, it's like adding S ... even though it's getting overwritten."
And: "go ahead and write that up. As a fix."

## Terms

- **Rocking:** holding one bumper, pressing the other, letting go of the
  first, and so on back and forth, with one bumper down at all times.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key` (R2 and
  L2 in the alternative layout).
- **Modifier 2:** the layer on top while both bumpers are held:
  `Steering | R1!L1: Modifier 2` when R1 went down first, `Steering | L1!R1:
  Modifier 2` when L1 did.
- **Hand-over:** since 90.57, the first bumper's Release inside Modifier 2
  **adds** the other driver's layer and removes its own.

## The fault

On the Deck, W to S works and S back to W does not. What exactly happens on
the way back is not yet reported (question 1). The simulator plays both
directions, on 90.58 and on 90.61, and the two directions are mirror images
bind for bind.

## What is different outside `Steering`

Starting with R1 held:

| Step | Bumper modifiers (works on the Deck) | `Steering` today |
|---|---|---|
| Press L1 | One chord adds R1's cover, **`L1: Modifier 0`**, L1's cover, then Modifier 2 on top | One chord adds Modifier 2 |
| Stack | R1 modifier, **L1 modifier**, Modifier 2 | W layer, Modifier 2 |
| Release R1 | Removes only. The L1 modifier is uncovered | **Adds** the S layer, removes Modifier 2 and the W layer |

Outside `Steering` no layer is ever added on a Release during a rock. The
second bumper's layer lands during that bumper's own press, covered by
Modifier 2.

In `Steering` the S layer lands on R1's Release, with L1 held since before
the layer existed. The way back then starts with a chord on L1 inside that
layer. It is the only place in the layout where a bumper's layer is entered
that way, and it is the step that fails. That it is the cause is a guess: the
layout does not show why it would fail.

## The change

Mirrored for L1 first. Shown for R1 first:

| Bind | 90.61 | New |
|---|---|---|
| W layer, L1's chord on R1 | Removes six stick layers, adds Modifier 2 | The same, and adds the **S layer** just before Modifier 2, so it sits under it |
| Modifier 2, R1's Release | Adds the S layer, removes Modifier 2 and the W layer | Removes Modifier 2 and the W layer |
| Modifier 2, L1's Release | Removes Modifier 2 | Removes Modifier 2 and the **S layer** |
| Modifier 2, its sixteen cleanup functions | Remove Modifier 2 and the W layer | Also remove the S layer (the cleanup rule for a layer below, R128; the fix pipeline adds it) |

Per layout: two adds move from a Release to a chord, and 34 removes are
added (2 by hand, 32 by the pipeline). Removes go from 2,851 to 2,885 in the
default layout and from 2,909 to 2,943 in the alternative. Counted on a trial
built in memory from 90.61.

Not touched: `Steering`'s own bumper binds, the driver layers' Releases, the
stick layers, the left-edge chords of 90.61 (beyond the one list above), the
bumper modifiers outside `Steering`.

## What it plays like

On the simulator, on the trial, both ways of A9:

| Step | Stack above `Steering` | Key |
|---|---|---|
| Hold R1 | W layer | W |
| Press L1 | W layer, S layer, Modifier 2 | W |
| Release R1 | S layer | S |
| Press R1 | S layer, W layer, Modifier 2 | S |
| Release L1 | W layer | W |
| Press L1, then release L1 again | W layer | W throughout |
| Release R1 | none | none |

Nothing changes in which key is held when. While both bumpers are down the
first one's key stays, as today: Modifier 2 answers both bumpers.

After a missed release:

- **Second bumper's release missed, first let go:** the second driver's
  layer is left on, typing nothing. A thumb on a stick, the stick moved off
  the rim after it reached it, or a bumper press clears it. On 90.61 the
  hand-over's layer cleared itself at once (scenario 90.61 E7); here it
  waits, because an inverted chord does not start when its layer is
  uncovered (A61).
- **First bumper's release missed, second let go:** the first driver's layer
  is left on until a thumb is on a stick. As on 90.61.

## Rules, the register and the tests

- **R174** (the hand-over, 90.57) is reworded: the second driver's layer is
  added by the second driver's press under Modifier 2, and a Release in
  Modifier 2 only removes.
- **R111:** the two Modifier 2 layers' left-edge chords gain a remove, so
  their two register entries are rewritten for the new exact lists. Without
  that the Budget audit fails (checked on the trial).
- **R128:** met by the 32 removes the pipeline adds. The Cleanup audit is
  clean on the trial after the pipeline.
- **Tests:** the hand-over scenarios of 90.57 (M1 to M3) and 90.61 E7 are
  frozen on 90.61; new scenarios play the table above, the four orders of
  letting go, and the two missed-release cases.

## What it costs

- **34 more removes a layout,** against the standing goal of fewer. 32 of
  them are in cleanup functions that run only after a missed release.
- **A possible flash of the second key.** The chord adds the S layer and
  then Modifier 2 in one list. If Steam ever lets a frame pass between the
  two, S is typed for that frame while W is held. The bumper modifiers'
  chord has the same shape with no key behind it, so the Deck has never
  shown whether this happens.
- **A repeating chord with eight sub-commands.** It has seven today. Its
  repeat may not fire either way (author, 2026-10-10); the first run does.
- **It rests on a guess** about why the way back fails.

## Build steps

1. A builder in a new findings folder, reading the 90.61 snapshot.
2. The two R111 entries, then the fix pipeline; the builder records what the
   pipeline adds and stops at anything else.
3. Tests as above, the nine rocking tests, random walks against 90.61 with
   the differing logs replayed.
4. Build audit, full suite, VDFs, snapshot, record.

## Answers so far

The author, 2026-10-12: "1. s stays just like how if we started with w then w
would stay 2. add them".

- **Question 2: add the 32 removes.** The rule is kept.
- **Question 1, first half: S stays when R1 is pressed.** So the chord on L1
  is not missed: Modifier 2 lands and types S. The fault is at the next
  step, letting go of L1, where Modifier 2's Release adds the W layer over a
  held R1. This plan changes that step: the W layer is already underneath,
  added during R1's own press, and the Release only uncovers it.
- **Still open: what happens when L1 is let go** (W, nothing, or `Steering`
  ends), and whether a key is typed when its layer is uncovered under a held
  bumper. The new design relies on that. It can be checked on 90.61 today:
  hold R1, press L1, let go of L1. If W is still held, an uncovered layer
  types its key.

## Questions

1. **What happens on the way back today?** L1 held and S going after one
   hand-over: when you press R1, does S stay, stop, or become W at once?
   When you then let go of L1: W, nothing, or `Steering` ends? If S stops or
   flips on the press, the chord on L1 is being missed, and this plan is
   aimed at the right bind. If S stays and it goes wrong on the Release, the
   fault is somewhere this plan does not change. **I'd wait for this answer
   before building.**
2. **The 32 removes in Modifier 2's cleanup functions.** Keep the rule and
   add them, or leave the second driver's layer out of those cleanups, as an
   exception, and let a thumb on a stick clear it? **My pick: keep the rule
   and add them.** They only run after a missed release, and leaving them
   out is the 90.60 exception again.

## On the Deck afterwards

1. Rock R1, L1, R1, L1 without letting both go: W, S, W, S each time.
2. The same starting with L1.
3. While both are held: only the first key, no flash of the other.
4. Hold both, let go of the second one first: the first key stays.
5. Rock with the left stick pushed up, and with a thumb tapping the right
   stick: `Steering` stays.
