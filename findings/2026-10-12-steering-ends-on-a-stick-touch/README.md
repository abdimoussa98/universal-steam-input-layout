# `Steering` ends on a right stick touch with a bumper held

The record of a Deck fault found on 2026-10-12 on **90.58**: what was tried,
what each try showed, and how it led to **90.61**, **90.63**, **90.65**, **90.66**, **90.67** and **90.68**.
The cause is confirmed (A69). 90.68 has not run on the Deck.

Everything under "on the Deck" is the author's own testing. The simulator
never reproduced the fault at any point.

## Terms

- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key`, on
  while its bumper is held in `Steering`.
- **Stick layers:** the six layers the left stick brings on over a driver
  layer: the two stick modifiers, `Steering | LS: Tap Cover`, `Steering | LS:
  Double Tap Cover` and the two stick scroll layers.
- **Cleanup function:** a repeating, interruptible Regular Press that only
  removes layers, with a **guard** beside it on the same input: a chord on
  the bumpers that is not interruptible, meant to hold the press back while
  a bumper is held.
- **The exit:** `Steering`'s own bind on up and down, past 29,031 (close to
  the rim), repeating every 50 ms. Since 90.58 it removes `Steering` alone.

## The fault

1. In `Steering`, hold R1. W is held.
2. Tap the right stick touch, repeatedly.
3. Flick the left stick to the rim.

`Steering` ends, with the exit's beep. W is held again afterwards.

## The answer so far

The driver layer's own cleanup on the left stick's edge runs although its
bumper is held. The author: while the right stick touch keeps "sending those
remove binds", and the stick hits the edge, "sometimes it just doesn't notice
that RB is still being held. And it triggers the cleanup."

The sequence, as the layout reads:

1. Each right stick touch Release sends three `remove_layer` calls for the
   stick's helper layers, whether or not they are on.
2. The left stick reaches its edge. The W layer's cleanup function there is a
   press that removes the W layer, with a guard on R1.
3. The guard does not hold, and the press removes the W layer.
4. `Steering` is bare with the stick at the rim, and the exit removes it.
5. R1's repeating add puts the W layer back, now over Base.

Why the guard does not hold is not known.

## What was tried, in order

| # | What | Result | What it showed |
|---|---|---|---|
| 1 | On the Deck, 90.58: R1 held, stick moved fast in every direction, right stick touch tapped rapidly | `Steering` ends. W stops first, then the beep. Half deflected, it stays | The W layer is dropped under a held bumper, and the exit does the rest. Half deflection is safe because the exit needs 29,031 |
| 2 | In the Steam editor: the guard's chord mode on those inputs | "Any" for L1 and R1 | The guard is not misconfigured |
| 3 | Layout check: chords with Invert Activation on the sticks | One, on the Entry Guard, removing only itself | Not an inverted chord |
| 4 | Layout audit of every guard | Each has one sub-command (343 guards in the default layout, 331 in the alternative). Every cleanup press beside a guard repeats and is interruptible (321 and 309) | The press and guard have the intended shape everywhere |
| 5 | **Built 90.59:** Hold to Repeat on the guards of the six stick layers (18 chords) | On the Deck the fault happened every time. W held again afterwards. Stick centred, tapping does nothing | A repeating guard is worse, not better. Not carried on |
| 6 | Layout audit: do other guards repeat? | None. One empty repeating chord exists on Base's right edge, beside the ramp adds; it is not a cleanup's guard | 90.59 was the only build with repeating guards |
| 7 | On the Deck, 90.58 again: R1 held, right stick touch tapped, stick pushed slowly to the rim | It triggers, and only in the 200 ms before the stick's cover lands | A right stick touch Release during the push is part of it |
| 8 | Compared with the bumper modifiers outside `Steering` | Their stick touch Release has the same pattern (one add, three removes) and works | The Release's shape alone is not the cause |
| 9 | Layout audit: guards set to "All" | Four per layout, all on the right stick's edge of the two stick modifiers | None is on an input of the gesture |
| 10 | 24,000 random walks of the gesture on the simulator, on each of 90.57, 90.58 and 90.59 | `Steering` stayed on in every one | The simulator decides a guard the instant its layer lands, so it cannot show this |
| 11 | **Built 90.60:** the W and S layers taken out of the cleanups of the eight layers above them (50 binds, 68 removes), as an exception to R128 | On the Deck the fault stayed | A stick layer's cleanup is not what drops the driver layer |
| 12 | Layout read on 90.60: what can remove the W layer with R1 held | Only the W layer's own seven cleanups: both stick touches, both edges, Start, Select, the other bumper's press | The fault is inside the driver layer |
| 13 | Trial simulator with a guard that is late when its layer lands on a held input | Every press of R1 with a thumb on a stick loops at once | Ruled out: the Deck does not do that |
| 14 | Trial simulator with a guard that is late when its bind is exposed by a layer leaving | The W layer's left-edge cleanup drops it; R1 puts it back | Possible, not shown |
| 15 | **In the Steam editor, on 90.60:** up and down in the W layer overridden with an empty bind, same gesture | `Steering` still ends | No stick layer can land, so it is the W layer's own edge bind. This settled it |
| 16 | Compared the planned bind with 90.55's | 90.55 had one inverted chord on the same ten edges, with 3 to 7 sub-commands each | See "90.55" below |
| 17 | **Built 90.61:** one inverted chord in place of the press and guard on the left edge of ten Steering layers | Not yet on the Deck | |
| 18 | **Built 90.63** (from 90.62): the ring inverted on those ten left edges, so the chord runs at the rim with no driver held | Not yet on the Deck | |
| 19 | **Built 90.65** (from 90.64): the press and its guard chord back on those ten edges, on a normal ring, the press 5 ms late | Not yet on the Deck | The bind the fault happened on, plus the delay |
| 20 | **The author, on the Deck:** spamming `remove_layer` makes a chord evaluate again, and an evaluation can fail | Confirmed | A69. The guard cannot be made safe |
| 21 | **Built 90.66** (from 90.65): each driver in `Steering` mode-shifts the left stick to a group with empty up and down; the 5 ms is off | Not yet on the Deck | The leak may still happen; it no longer ends `Steering` if A70 holds |
| 22 | **Built 90.67** (from 90.66, the author's change of mind the same day): the mode shift is out; each of the ten left-edge cleanup presses adds `Steering \| LS: Entry Guard` before it removes | Not yet on the Deck | The leak may still happen; what it leaves on top is the Entry Guard, whose driver chord puts the driver's layer back |
| 23 | **Built 90.68** (from 90.67): in the Entry Guard each driver's chord adds the driver's layer first, then removes the guard | Not yet on the Deck | `Steering` is not the top layer between the two commands |

## What was learned

- **A guard does not always hold on the Deck.** While another input's
  Release is sending `remove_layer` calls, a press on a guarded input can run
  with its owner held. This goes against A27 and A36 for that moment.
- **The damage depends on what is under the layer.** Dropping the W layer
  would be harmless, since R1 puts it back within 50 ms. It ends `Steering`
  because a stateful layer's exit sits on the same stick directly below.
- **Repeating guards make it worse** (90.59). No guard in the layout repeats.
- **Shortening the lists above did not help** (90.60). The bind at fault was
  one layer down from where the first two builds worked.
- **Clearing a bind in the Steam editor and retesting localises a fault
  faster than a build.** Step 15 did in one test what two builds had not.
- **The simulator cannot judge this class of fault.** It reads a guard, and
  an inverted chord, as always seeing a held button.
- **Since 90.58 the exit removes `Steering` alone,** so after the fault the
  W layer is left on over Base and W stays held. On 90.57 and before, the
  exit wiped the whole family.

## 90.55

The same ten left edges had one inverted chord in 90.55. 90.56 put the press
and guard back after this report: with a bumper held and the stick up or
down, a thumb lifting from a stick cleared the W or S layer and `Steering`
ended. The author suspected the inverted chord fires after a `remove_layer`
call although a bumper is held (A66). That was never isolated on the Deck.

90.55 differs from 90.61 beyond the edge:

- **Sub-commands:** every one of its ten chords had several (the W layer's
  had seven). A repeating chord with more than one sub-command does not fire
  its repeat (author, 2026-10-10). In 90.61 the two driver layers' chords
  have exactly one, which 90.55 never tested.
- **The exit** removed all fourteen family layers.
- **The lists** of nearly every Steering cleanup were longer (90.57, 90.58).

So 90.55 is weaker evidence against the inverted chord than it looks. Both
faults do share one thing: they need a stick touch Release, which is what
sends the removes.

## Still open

- **Why the guard misses the held bumper: answered.** The author, on the
  Deck, 2026-10-13: a `remove_layer` call makes a chord evaluate again, and
  in a burst of them an evaluation can fail, so the interruptible press
  beside it runs (A69). Rare. No guard chord can be made safe against it, so
  the [plan](../../plans/2026-10-13-steering-mode-shift-on-the-drivers.md)
  takes away what the leak costs: `Steering`'s exit on up and down while a
  driver is held.
- **Whether an inverted chord misses it too** (A66). The chord asks "is no
  bumper held?" itself. On 90.61 and 90.62 it is live whenever the stick is
  off the rim; on 90.63 and 90.64 only at the rim, where the fault happened.
  Since 90.65 no chord is there to ask.
- **What a mode shift in a layer does on the Deck** (A70). 90.66 rested
  on it; 90.67 has no mode shift and does not.
- **Whether the Entry Guard holds at the rim** (A61) and its driver chord
  runs on a driver that is already held. 90.67 rests on both.
- **The stick touches of the driver layers** keep the press and guard. They
  are pressed far less often than the edge.

## The two trials that are gone

Their builders, tests and snapshots were removed on the author's word,
2026-10-12 ("reverting all the changes"). This table is their record.

| | 90.59 | 90.60 |
|---|---|---|
| From | 90.58 | 90.58 |
| Change | Hold to Repeat on 18 guard chords in the six stick layers | The W and S layers out of 50 cleanup functions in the six stick layers and the two Modifier 2 layers; 68 removes fewer a layout |
| Rule | None | An exception to R128; the Cleanup audit and `cleanup_lists` fix were taught to read it, and that code is reverted too |
| On the Deck | The fault happened every time | The fault stayed |

## What is built for it

[90.61](../2026-10-12-inverted-chord-on-the-steering-left-edge/README.md),
from 90.58: on the left edge of ten Steering layers the press and its guard
are one chord with Invert Activation, carrying the press's list. There is no
press on the edge left for a guard to miss.

[90.63](../2026-10-12-inverted-ring-on-the-steering-left-edge/README.md)
then inverts the ring of those ten groups: the chord runs at the rim with no
driver held, where the press ran, and nowhere else.

[90.65](../2026-10-13-steering-left-edge-press-and-guard/README.md) goes
back to the press and its guard on a normal ring, and starts the press 5 ms
late (author, 2026-10-13).

[90.66](../2026-10-13-steering-mode-shift-on-the-drivers/README.md) takes
the 5 ms off and leaves the leak alone: while a driver is held, `Steering`'s
up and down are empty binds by a mode shift (R175).

[90.67](../2026-10-13-entry-guard-before-the-left-edge-cleanup/README.md)
takes the mode shift out again and still leaves the leak alone: each of the
ten left-edge cleanup presses adds the Entry Guard before it removes, so a
press that runs past its guard leaves that guard answering the stick (R176).

A related fault is with another session:
[`Steering` ends while rocking L1 and R1](../2026-10-12-steering-ends-while-rocking/README.md).
