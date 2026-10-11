# Plan: move the stick's hold timer onto the driver

**Status, 2026-10-11:** built in **90.53**
([record](../findings/2026-10-10-steering-entry-and-edge-chords/README.md)):
one shared stick modifier, both timers on the drivers, the reset left on the
stick's direction. Nothing has run on the Deck as built. The text below is the
brainstorm and the author's answers, in the order they came.

## The finding (author, on the Deck, 2026-10-10)

In `Steering` with a driver held, a deflect up or down starts a 200 ms delay
that adds `Steering | LS: Tap Cover`. Let the stick go before the 200 ms once,
and that deflect scrolls. On every later deflect the Tap Cover lands at once,
so no deflect scrolls again. This is the "scrolls once, then not again" fault
of 90.50 to 90.52.

The cause is where the delay sits: on stick up or down. With the delayed bind
moved to the bumper, the fault is gone and the sequence behaves like the L1
and R1 modifiers and the trigger modifiers.

So: **a Fire Start Delay must not be owned by a stick direction.** This
replaces my lead of the same day, that the W layer's entry chord stopped
firing (A62). That lead was wrong.

## Terms

- **Driver:** R1 for W and L1 for S in `Steering` (the triggers' soft pull in
  the alternative).
- **W layer:** `Steering | R1: W Key`. `Steering | L1: S Key` is its twin.
- **Stick modifier:** `Steering | LS Up: Modifier 1` or
  `Steering | LS Down: Modifier 0`.
- **Hold marker:** `Steering | LS: Tap Cover`. Once it is on, letting the
  stick go doesn't scroll.
- **Hold timer:** the 200 ms delayed chord that adds the hold marker, with
  its reset (a repeating press that removes the marker).
- **Cover timer:** the 150 ms delayed chord in the two stick scroll layers
  that adds `Steering | LS: Double Tap Cover`, with its reset.
- **Owner:** the input whose bind carries a delay. Today the stick direction;
  the chord's button is a different thing.

## Where a delay is owned by a stick direction today

| Layer | Input | Delay | Adds |
| --- | --- | --- | --- |
| `Steering \| LS Up: Modifier 1` | up | 200 ms | the hold marker |
| `Steering \| LS Down: Modifier 0` | down | 200 ms | the hold marker |
| `Steering \| LS Up: Scroll Up` | up | 150 ms | `Steering \| LS: Double Tap Cover` |
| `Steering \| LS Down: Scroll Down` | down | 150 ms | `Steering \| LS: Double Tap Cover` |

The author reported the first two. The last two have the same shape; whether
they misbehave the same way is not reported.

## What has to stay as it is

1. A deflect with a driver held puts the stick modifier's buttons on at once.
2. Back before 200 ms: the window opens, one scroll at 50 ms.
3. Held past 200 ms: the hold marker; coming back doesn't scroll.
4. A stick click or a modifier button during the deflect makes it a hold at
   once.
5. A second deflect inside the window scrolls on the press; held past 150 ms
   it repeats; let go before, the window opens again.
6. The other driver pressed during a deflect enters the Modifier 2 layer.
7. The driver released at any point ends everything, and W or S lets go.
8. W or S stays down throughout, with no second press.
9. Both drivers, both layouts.

## The constraint

The stick modifiers are shared by the two drivers and bind neither bumper:
R1 and L1 fall through to the W or S layer. A delay owned by the driver has to
sit in a layer that lands at the deflect and binds that driver. A layer that
binds a bumper replaces everything under it on that bumper: the W key, the
Release that ends the hold, and, for the other bumper, the Modifier 2 entry.

## Option A: a stick modifier per driver (recommended)

Each stick modifier becomes two, one for R1 and one for L1. The copy binds
only its own driver, in the shape `L1: Modifier 0` has on L1. Two new layers
for the hold timer; two more if the cover timer moves as well.

| Entry | `L1: Modifier 0`, on L1 | The R1 copy of a stick modifier, on R1 |
| --- | --- | --- |
| Release | Remove the marker and the modifier, open the window | The W layer's Release: remove the W layer and the stick family |
| Hold timer | Self-chord, 200 ms: add `L1: Temp Cursor Gyro` | Self-chord, 200 ms: add the hold marker |
| Output | None | W, so the key stays down |
| Reset | Repeats every 250 ms: remove the marker | The same, for the hold marker |

Up or down in the copy keeps only its Release, which ends a tap and opens the
window. The timer and its reset leave the stick.

Hold R1 and flick up:

1. The W layer's up adds the R1 copy. One command, as today.
2. The copy lands on the held R1: W is handed over and stays down, the reset
   fires once, and the 200 ms start on the bumper.
3. Stick back before 200 ms: up's Release removes the copy, and its timer with
   it, and opens the window. One scroll.
4. Stick held past 200 ms: the timer adds the hold marker. Stick back: the
   marker's Release removes the marker and the copy. No scroll.
5. L1 pressed during the deflect: the copy doesn't bind L1, so the W layer's
   L1 answers and enters the Modifier 2 layer, as today.
6. R1 released during the deflect: the copy's Release ends everything.

Costs:

- **Layers:** 92, or 94 with the cover timer. The stick modifiers' button
  maps exist twice.
- **Four entries on the driver** (Release, timer, W, reset), one over the
  budget of three. It is the shape `L1: Scroll Down` already has on L1, where
  the reset is the fourth entry and is dropped in the desktop configuration.
- **W is handed from one layer to the next once more per deflect** (A37,
  unverified). The stick windows have handed W over the same way since 90.47.
- **Lists:** every list that removes the two stick modifiers removes four.

## Option B: a small timer layer per driver

The stick modifiers stay shared. Two new layers, one per driver, bind only
that driver, with the same four entries as in option A. The stick modifier
adds the matching one as it lands: on its own direction two repeating chords,
one per driver, replace the timer and the reset. Its Release removes them.

- **For it:** the button maps stay single, and one timer layer serves up and
  down.
- **Against it:** one more step in the chain (the modifier lands, its chord
  adds the timer layer, the timer starts), each step resting on "a repeating
  bind fires at once on a held input". It puts new chords on the stick
  direction, with no delay. The cover timer has another delay and another
  target, so it needs its own pair: four layers either way.

## Option C: the shared stick modifiers bind both bumpers

No new layer. Each stick modifier binds R1 and L1 the way the stick windows
do, plus the timer: the key, the self-chord, the Release, the reset.

- **Cost:** point 6 is lost. While the stick is held up or down, the other
  bumper types its key and does not enter the Modifier 2 layer. Keeping that
  entry as well needs five entries on each bumper.

## Not on the bumper: an Always On timer

For completeness. The stick modifier could count its 200 ms with an Always On
action, as the windows count their 50 and 150 ms. No new layer and no bumper
bind. But it is not what was tested on the Deck, and the audits treat every
layer with an Always On action as a window, so the rules would have to change.

## The author's answers, 2026-10-10

- **The test:** the delayed add was put inside the stick modifier, on the
  bumper.
- **The cover timer:** yes, it moves the same way.
- **The timer, in the author's words:** in the stick modifier the add of the
  Tap Cover "is going to exist on the bumper", "kicked off on the bumper being
  a chorded button with a left stick deflect": a Chorded Press on the driver
  whose chord button is the left stick's deflect, 200 ms. It starts as the
  modifier lands, because the driver is held and the stick is out. This is the
  timer of options A and C, with the deflect as the chord's button where the
  tables above say self-chord.

## Decided: one shared modifier (author, 2026-10-10)

Option C. No new layer. What follows is that design in detail, replayed on a
prototype in the press simulator (default layout, on the 90.53 candidate;
`shared_proto.py` in the session's scratch folder, not kept). Nothing is
built.

### What each bumper carries

In the two stick modifiers, on R1 and on L1 alike:

| Entry | On R1 | On L1 |
| --- | --- | --- |
| Key | W, not interruptible | S, not interruptible |
| Timer | Chord on the left stick's deflect, 200 ms: add the hold marker | The same |
| Release | The W layer's Release list | The S layer's Release list |

The two stick scroll layers get the same three, with 150 ms and
`Steering | LS: Double Tap Cover`. The two stick windows already bind both
bumpers with the key and a Release. The stick direction loses its delayed
chord in all four layers and keeps its Release.

### The sequences (R1 held; L1 and down mirror them)

**A tap.**

1. Hold R1: `Steering` adds the W layer. W is down.
2. Push up: the W layer's up adds `Steering | LS Up: Modifier 1`.
3. The modifier lands on the held R1: W is handed over and stays down, and
   the 200 ms start on R1, because R1 is held and the stick is out.
4. Stick back before 200 ms: up's Release removes the modifier, its timer with
   it, and opens the window.
5. The window scrolls at 50 ms and closes at 150 ms.

Four taps in a row scroll four times on the prototype: every deflect lands a
fresh modifier and a fresh timer on the bumper.

**A hold.** Steps 1 to 3, then the timer adds the hold marker at 200 ms. Stick
back: the marker's Release removes the marker and the modifier. No scroll.

**A stick click or a modifier button during the deflect.** It adds the hold
marker at once, as today. The deflect is a hold; the next tap scrolls.

**A second deflect inside the window.** The window's up adds the scroll
layer: one scroll on the press. The scroll layer lands on the held R1 and its
150 ms start on R1. Back before 150 ms: the window opens again. Held past
150 ms: the cover repeats the scroll until the stick is back.

**R1 let go at any point.** The Release on R1 in whichever layer answers it
removes the W layer and the stick family. As today.

**L1 pressed while the stick is held (the one change).** Today the W layer's
L1 enters `Steering | R1!L1: Modifier 2` at once. With the modifier binding
L1, S goes down beside W and no Modifier 2 comes. When the stick is back and
no stick layer answers L1 any more, the W layer's L1 enters Modifier 2 and S
lets go; after a tap that is once the window has closed. This is what a
second bumper already does inside the 150 ms window today. A tap of L1 during
the deflect types S, and its Release drops the stick modifier, which comes
straight back because the stick is still out.

### Two ways to place the reset

The reset is the repeating press that removes the hold marker; it stops when
the marker lands and takes its input over.

| | 1. The reset moves with the timer | 2. The reset stays on the stick |
| --- | --- | --- |
| On the bumper | Four entries: key, timer, Release, reset. The allowed shape of `L1: Scroll Down` | Three entries |
| On up and down | Only the Release | The reset and the Release, as today |
| The hold marker and the cover | Must bind both bumpers too (key and Release), so that the reset stops | Unchanged: they bind only the stick |
| Against the bumper pattern | The same shape as `L1: Modifier 0` | The reset is not on the input that owns the delay (R120) |
| With both bumpers down during a deflect, on the prototype | The two resets keep restarting both timers, the marker never lands, and letting the stick go scrolls even after a long hold | The marker lands at 200 ms; Modifier 2 comes when the stick is back |
| On the Deck | Not tested | Tested by the author if the reset was left on the stick in the test; to confirm |

Everything else in the sequences above is the same in both on the prototype.

## The author's answers, 2026-10-11

- **The reset:** in the test it stayed on stick up and down. Where it lives is
  left to my judgment ("I don't care where it lives and it shouldn't
  matter"). Built as way 2: on the stick, as tested.
- **W in the test:** it stayed down.
- **90.53:** no preference. Built as one release.
- **Modifier 2 (2026-10-11):** "the bumpers are both bound in the mod zero and
  one, and so it seems like you won't be able to get into mod two if you're
  deflecting the stick." Built: in the four timer layers each driver's key
  press also carries the other driver's layer's entry into Modifier 2. The
  held driver never runs it (A5); a fresh press does. The sequence "L1
  pressed while the stick is held" above is therefore as until 90.52, apart
  from the other driver's key showing for a moment
  ([record](../findings/2026-10-10-steering-entry-and-edge-chords/README.md#the-other-driver-straight-into-modifier-2)).
