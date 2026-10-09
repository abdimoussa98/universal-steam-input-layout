# Delays, and what interrupts them

**Status:** an audit of 90.36, both layouts, on 2026-10-06, asked for by the
author. Read-only: no layout, VDF, version, rule or to-do changed. It reads the
JSON and the backward chains. Nothing was run on the Deck.

**Later on 2026-10-06:** the author deferred the [test rig](../../plans/2026-10-06-delay-test-layout.md)
to [todos](../../todos.md#deferred-delay-tests-and-the-menu-entry-issue).
The [Base menu activator difference](../2026-10-06-menu-base-chords/README.md)
is now the candidate cause to investigate for the missing menu Fn layer.
This does not retract the historical delay fault or establish its cause.

The author's question: "audit all of the layers that have delays and the
interactions with the delayed layer ... was the interruption by a release of
owner of the delay or by another button ... removing the layer that initiated
the delay, or covering it with the layer that was intended by the delay, or
covered by a random other layer ... when each was introduced."

- Every delay, with every line: [INVENTORY-default.md](INVENTORY-default.md),
  [INVENTORY-alternative.md](INVENTORY-alternative.md).
- The data behind them: [interruptions.json](interruptions.json).
- The scripts: [audit.py](audit.py), [report.py](report.py), [check.py](check.py).
- What Valve and users have written about delays and layers: [ONLINE.md](ONLINE.md).

## Terms

| Term | Meaning | Example |
|---|---|---|
| **Delay** | One activator entry with Fire Start Delay | LB in `L1: Modifier 0`: after 200 ms it adds `L1: Temp Cursor Gyro` |
| **Host** | The layer the delay is bound in: the layer that started it | `L1: Modifier 0` |
| **Own input** | The input the delay is bound to: the owner of the delay | LB |
| **Target** | The layer the delay adds: the layer it intended | `L1: Temp Cursor Gyro` |
| **Pending** | From the moment the host's binding answers the held input until the delay ends | The 200 ms after LB goes down |
| **Line** | The counting unit: one delay, one other entry that can fire while it is pending, and what that does to it | LB's delay, A's chord in `L1: Modifier 0`, covered by `L1: Tap Cover` |

What a line does to the delay:

| Effect | Meaning | Rests on |
|---|---|---|
| **Host removed** | The host leaves the stack, and the delay with it | A1 |
| **Target lands** | Another entry adds the delay's target, and the target takes the input | R122, R123 |
| **Covered** | Another layer lands and takes the input. The delayed action never fires | A15, verified |
| **Restart** | A `remove_layer` fires and nothing else changes for the delay: it starts again | A12 for its target, verified. A13 for any other layer, reported |
| **Host stays** | Only for the own input let go: the delay is dropped and the host is still on | |

Whether a line can fire while the delay's own buttons are held:

| Verdict | Meaning |
|---|---|
| **Yes** | Nothing holds it back |
| **Held back** | An interruptible Regular Press, and a chord on the same input is met by the delay's own button (A27). This is a cleanup function behind its guard: it fires only if the guard fails |
| **Only with X held too** | A chord that needs another button |
| **Only while X is not held** | Another interaction's cleanup function. It fires when that layer was left over |

**Since** is the first version in which the same line exists: the same delay,
the same layer and input for the binding, the same activator type, effect,
covering layer and verdict. A line that changes one of these is a new line.

## What was run

- `audit.py` lists every entry with a start delay. For each one it takes the
  stacks where the host answers the delay's input, from the backward chains
  with one extra press, and looks at every other entry that answers an input
  on those stacks. It applies that entry's commands and sees what happened to
  the delay.
- It does the same on every older version, for the "since": the 33 snapshots
  90.4 to 90.36, sixteen commits before them, and the July reference for the
  default layout. About 50 seconds in all.
- `check.py` replays one gesture per class on the press simulator.

**56 delays per layout: 39 on a held input and 17 window timers** (in 11
windows). 2,461 lines in the default layout and 2,463 in the alternative. Of
the default's lines, 1,159 name the host, the target or a cover; the other
1,302 are removals of unrelated layers, kept as one line per layer.

The July reference has 33 delays; 30 of today's 56 are in it. Its three others
are `Split Stick`'s two 100 ms adds and `RTP: Middle Mouse Click`'s 50 ms.

**The alternative layout has the same shape**, with L2 and R2 for L1 and R1.
The one difference: 12 delays have one or two more held-back cleanup functions,
on the triggers' two stages (387 against 367). What follows uses the default
layout's names.

The labels for the versions before the first snapshot:

| Label | Commit | Date | What it was |
|---|---|---|---|
| 85.8 Feb | `5eae4dc` | 2026-02-04 | The Neptune layouts before the port |
| 85.8 port | `4c351cd` | 2026-09-27 | The trigger and ramp-up rework, ported |
| 85.8 menu split | `a4c2fe5` | 2026-09-27 | One menu Entry Point becomes a left and a right one |
| 90.1, 90.2 | `7cee48d`, `2fee9ee` | 2026-09-27 | |
| 90.2 (52494a0) | | 2026-09-28 | The left-stick edge cleanups |
| 90.2 (50758b3) | | 2026-09-29 | The temporary cursor gyro |
| 90.2 (5bf46a7) | | 2026-09-29 | The cursor's cancellation, reworked |

## The answer in one table

The 39 delays on a held input. A cell counts the delays that have at least one
such line.

| Interrupted by | Host removed | Target lands | Covered by another layer | Restart |
|---|---|---|---|---|
| Its own input let go | 35. For the other 4 the host stays | | | |
| Its own input, another entry on it | | | | 29: the reset (R120) |
| A button its chord needs, let go | 12 | | | |
| Another input, and it can fire | 18 by a bind in the host, 17 by a bind in another layer | 27, always by a bind in the host | 8 by a bind in the host, 33 by a bind in another layer | 39 by an unrelated removal, 6 by a removal of the target |
| Another input, held back by the delay's own button | 29 by a bind in the host, 10 by a bind in another layer | | | 4 |

## Findings

The numbers are the tool's. Where a sentence is my reading, it says so.

### 1. Its own input let go: the host goes, except for four

| What the Release does | Delays | Which |
|---|---|---|
| Removes the host, and that button's Double Tap window lands on the input | 23 | The modifier, second-press, menu, stick-guard and menu-chain holds, and the three touch Entry Points |
| Removes the host, and `Gyro` lands | 2 | `L1!R1: Modifier 2`, `R1!L1: Modifier 2`: the Release turns `Gyro` on |
| Removes the host, and a lower layer answers | 6 | The two `Gyro \|` Modifier 2 layers, Steering's two, and `Steering \| LS: Double Tap Cover`'s two scroll binds |
| No Release. An inverted bind removes the host once the input is back at rest | 4 | `Gyro Off Ramp Up`, `Turning Ramp Up 0`, and the two Click Entry Points, which hand over to the Middle Click layer |
| Nothing: the host stays | 4 | `RTP: Mouse Buttons`' two ring scrolls, and the two Steering stick modifiers |

For the two Steering stick modifiers the exit is on the stick's edge, not on
the direction the delay is on: the edge's Release removes the host and opens
the stick's window.

All but the Steering and menu-chain ones are in the July reference, unchanged.

### 2. Another button removing the host: almost always held back

367 bindings on other inputs would remove a pending delay's host. All 367 are
cleanup functions that the delay's own button holds back (A27), on 29 delays.
By first version: 124 from 85.8 Feb, 12 from 90.2, 28 from 90.5, 10 from
90.10, 12 from 90.12, 6 from 90.14, **82 from 90.24** (the required cleanups,
R169 to R171), **90 from 90.25** (the menu chain, 64 of them in the two Fn
layers), 3 others.

The ones that can fire while the own input is held come from a handful of
bindings, each a designed exit:

| Binding | Hosts it removes | Since |
|---|---|---|
| A stick click let go, in a menu Entry Point: the transition | The menu Entry Points, the stick guards, the menu chain, and the pad layers on top | 90.10; `Transition Set 2` 90.22; the chain 90.25 |
| LB or RB pressed, in `Turning Ramp Up 0`. LT or RT pressed, in `Gyro Off Ramp Up` | The ramp layer | 85.8 port. In July |
| The chord's other button let go | The Modifier 2 layers, Steering's modifiers, `Menu Left!Right: Entry Point`, the ring scrolls (the thumb off the pad) | 85.8 Feb; Steering 90.5 and 90.10; the chain 90.25; the pad 90.16 |
| A stick guard's own stick edge let go, or the other menu button let go | The stick guard | 90.10 |
| The pad let go, or its click let go (an inverted bind) | The Click Entry Points, `RTP: Mouse Buttons` | 90.14, 90.16 |
| A driver button let go, in `Steering` | `Steering \| LS: Double Tap Cover`, the Steering stick modifiers | 90.5, 90.10 |
| Select and Start together, or a stick click in `Menu Keys` | The pad layers | 90.27 |
| LB or RB pressed in `Steering` with the right stick out | The ramp layers | 90.35 |

The Steering stick modifiers' own cleanup functions read "depends": the delay
is chorded with either bumper, and each cleanup is guarded by one of them.

### 3. The target landing by another route: always the host's own bind

27 delays. Three routes, all in the host:

| Route | Delays | Since |
|---|---|---|
| A thumb lifting off either stick: the touch Release completes the add (R123) | All 27 | 85.8 Feb, in July: Modifier 2, the second-press holds, the pad's touch, the menu Entry Points. The cursor: 90.2 (50758b3). Steering: 90.5, 90.6. The stick guards: 90.10. The chain's second press: 90.25. The stateful Entry Points: 90.28 |
| A face button, D-pad direction, stick click, Start or Select, chorded | The four Modifier 2 layers, Steering's two, the Steering stick modifiers | 85.8 Feb, in July; Steering 90.5 and 90.10 |
| The other menu button | The menu Entry Points and the stick guards | 85.8 Feb, in July; guards 90.10; the stateful ones 90.28 |

The other 12 have no such route: the hold to `Menu Keys`, the stick-touch
Entry Points, the ramp layers, the pad click layers and the delayed scrolls.

Until 90.2 (c820d22) the face buttons under a held modifier were this route
too: the target was the Tap Cover. Since 90.2 (50758b3) the target is the
cursor, and they are finding 4.

### 4. Covered by a layer the host itself adds: 8 delays

| Host | Input | Cover | Since |
|---|---|---|---|
| The four modifier layers | A, B, X, Y, the D-pad, a stick click, Start, Select; or both sticks out | Its Tap Cover, in place of the cursor | 90.2 (50758b3) |
| The four modifier layers | The other bumper | The Modifier 2 layer | 85.8 Feb. In July |
| The four menu Entry Points | A stick out | That stick's guard, in place of the Fn layer | 90.10 |

### 5. Covered by a layer some other layer adds: 33 delays

These are the "random other layer" cases. Three sources:

| Source | What covers | Delays | Since |
|---|---|---|---|
| **A tap on the right pad.** `RTP: Entry Point`'s touch Release opens `RTP: Double Tap`, which binds or blocks LB, RB, Select, Start and most other inputs | The window | 25: every hold on a bumper or a menu button but Steering's own modifiers, and `LTP: Click Entry Point` | 85.8 Feb, in July, for the 14 holds that existed then. The others with their hold: 90.5, 90.10, 90.16, and 90.27 for the menu chain |
| **Another button's window.** LB, RB, Select, Start or a stick let go opens its window, which blocks the pads and the sticks | That window | 8: the three touch Entry Points, the two Click Entry Points, the two ring scrolls, `Gyro Off Ramp Up` | 85.8 Feb for the stick and pad touches. 90.14 and 90.16 for the pad click layers |
| **A hold that starts underneath.** `Base`, `Gyro`, `Cursor Gyro` or `Steering` adds a layer that binds the delay's input | A modifier, a menu Entry Point, `RTP: Entry Point`, a Click Entry Point, a swipe layer, the other stick's guard, the fallback guard | 10: the two stick-touch Entry Points (16 covers each), the pad's, the two ramp layers, the stick guards, `RTP: Click Entry Point` | The modifiers and the pad: 85.8 Feb, in July. The menu Entry Points: 90.10 in this form. Click Entry Points: 90.14. `Cursor Gyro`: 90.21. The fallback guard: 90.34 and 90.35 |

The tool doesn't read time. The pad's Release opens its window only in the
first 150 ms of a touch; after that `RTP: Tap Cover` answers it.

On the simulator: LB held, the right pad tapped at 50 to 100 ms. The window
takes LB, so the cursor's delay ends. When the window ends, the delay starts
again and the cursor lands at 450 ms, not 200. That it starts again is A14,
unverified.

### 6. Restarts

- **The reset.** 29 of the 35 delayed adds have their reset on the own input
  (R120). `Gyro Off Ramp Up` and the three touch Entry Points have none, which
  is the R120 exception; the two Click Entry Points have theirs on the pad's
  touch (55 ms, since 90.26). First versions: Modifier 2 and
  `Turning Ramp Up 0` 85.8 port, the menu Entry Points 85.8 menu split, the
  modifiers 90.2 (5bf46a7), the second-press holds 90.6.
- **Unrelated removals.** All 39 delays have some: a Release, a cleanup
  function or a hand-over of another interaction. Each costs one restart, if
  A13 holds. R126 asks that these be blocked and has no check; the per-delay
  rows are that list.
- **No repeating removal is left running over a delay.** A removal that
  repeats, is unguarded and stays the answer after it fired would restart a
  delay again and again. The only ones on a stack where a delay is pending are
  other holds' resets (200 to 300 ms) and the Click Entry Points' 55 ms reset.
  A reset stops when its own target lands; a Click Entry Point hands over
  within 5 ms. None has an unstated rate.
- **A late restart meets the delay's own reset.** On the simulator: LB held,
  the right pad clicked at 100 ms and kept down. The hand-over's removal
  restarts the cursor's delay to 300 ms. LB's reset fires at 250 ms and
  restarts it again: the cursor lands at 450 ms. If only the target's removal
  restarts a delay (A13 false), it lands at 200. This is the 50 ms margin of
  R121.

### 7. The window timers are closed

For all 17, the only lines are the window's own: its input pressed again, a
thumb let go of a stick or the right pad (the pad since 90.28), and in
`RTP: Double Tap` a bumper or menu button let go (90.30). Nothing covers a
window's timer and no unrelated removal fires inside one. That is what R146 to
R149 ask for.

### 8. The menu Entry Point, and a thumb already on a stick

Tool: bindings in `Menu Left: Entry Point` that would remove it while Select
is held, all held back by Select:

| Versions | Inputs |
|---|---|
| July reference | The right stick's edge |
| 85.8 Feb to 90.4 | The right stick's edge; Start from the menu split; the left stick's edge from 90.2 (52494a0) |
| 90.5 to 90.23 | Start |
| 90.24 to 90.36 | Start, both stick touches, both stick edges, LB, RB, both triggers' full pull |

My reading: this is the path behind "a thumb on a stick and a menu button
held, the Fn layer never came" (A52). With the thumb down first, the Entry
Point lands on a touch that is already held. Its cleanup repeats, so it fires
as it lands (A6) unless Select's chord holds it back. That chord is decided at
that moment (A36, unverified). Before 90.24 the Entry Point's stick touch had
only the chord and the Release, so a resting thumb could not remove it. The
simulator holds it back, and Fn lands 200 ms after Select. The stored order
(A52) and A36 are two separate things that could break it; 90.36 fixed only
the order.

## The delays, by family

Mirrored delays have the same lines; `report.py --summary` checks that.

| Family | Delays | Delay, reset | Target | History |
|---|---|---|---|---|
| Modifier hold | `L1: Modifier 0`, `R1: Modifier 1`, and their `Gyro \|` twins | 200, 250 | Its Temp Cursor Gyro | 85.8 Feb: 300 ms, to its Tap Cover. 90.2 (50758b3): to the cursor. 90.26: 200 ms. July: 300 ms, Tap Cover |
| Modifier 2 | The two orders, and their `Gyro \|` twins | 200, 250 | `L1&R1: Tap Cover` | 85.8 Feb. July: the same |
| Second press held | `L1: Scroll Down`, `R1: Scroll Up`, `Menu Left: Escape`, `Menu Right: Tab` | 150, 200 | Its Double Tap Cover | 85.8 Feb. July: the same |
| Menu chain, second press | `Menu Left!Right: Enter`, `Menu Right!Left: Backspace` | 150, 200 | Its Double Tap Cover | 90.25 |
| Menu Entry Point | `Menu Left`, `Menu Right`, and the two `Stateful \|` ones | 200, 250 | Its Fn layer | 85.8 Feb: 300 ms, in the one Entry Point. 90.10: 200 ms. July: 300 ms. The stateful ones: 90.5 as Steering's, 90.28 to their own Fn layer |
| Stick guard | The two guards, Select and Start on each | 200, 250 | `Menu Buttons: Tap Cover` | 90.10 |
| Menu chain | `Menu Left!Right: Entry Point`, `Menu Right!Left: Entry Point` | 200, 250 | `Menu Keys` | 90.25: 150 ms. 90.26: 200 ms |
| Stick touch | `LST: Entry Point`, `RST: Entry Point` | 150, none | Its Tap Cover | 85.8 Feb. July: the same. A reset in 90.25 to 90.29 |
| Right pad touch | `RTP: Entry Point` | 150, none | `RTP: Tap Cover` | 85.8 Feb. July: the same. A reset in 90.25 to 90.29 |
| Ramp, first stage | `Gyro Off Ramp Up` | 5, none | `Turning Ramp Up 0` | 85.8 port. July: the same |
| Ramp, second stage | `Turning Ramp Up 0` | 250, 300 | `Turning Ramp Up 1` | 85.8 Feb. July: the same |
| Steering stick modifier | `Steering \| LS Down: Modifier 0`, `LS Up: Modifier 1` | 200, 250 | `Steering \| LS: Tap Cover` | 90.6: 250 ms. 90.26: 200 ms |
| Steering Modifier 2 | The two orders | 200, 250 | `L1: Tap Cover` or `R1: Tap Cover` | 90.5 |
| Pad click hand-over | `LTP: Click Entry Point`, `RTP: Click Entry Point` | 5, 55 on the touch | `LTP: Arrow Keys`, `RTP: Mouse Buttons` | 90.16 |
| Ring scroll | `RTP: Mouse Buttons`, up and down | 150 | The scroll wheel | 90.6 |
| Stick scroll | `Steering \| LS: Double Tap Cover`, up and down | 5 | The scroll wheel | 90.5 |

Nineteen delays that some version had are gone, most of them Steering's; they
are at the end of the inventory.

## When the lines came in

The default layout's lines that name the host, the target or a cover, by first
version. `report.py --summary` prints the counts.

| First version | New delays | Lines | Mostly |
|---|---|---|---|
| 85.8 Feb | 29 | 304 | The Releases, 124 held-back cleanups, the touch-Release route, Modifier 2's chords, the pad window over the button holds |
| 85.8 port, menu split | 1 | 26 | `Gyro Off Ramp Up`, the ramp's bumper and trigger exits, the first resets |
| 90.2, four commits | 0 | 82 | The cursor as the modifiers' target: 56 "covered by the Tap Cover" lines; the left-stick edge cleanups; the modifiers' reset |
| 90.5, 90.6 | 10 | 86 | Steering's holds; the resets on the second-press holds |
| 90.10 | 6 | 202 | The stick guards; the transitions on a stick click's Release (100 host-removed lines); the menu Entry Points over the stick-touch and ramp delays |
| 90.12 | 0 | 12 | Stick-touch cleanups on Modifier 2 |
| 90.14 to 90.18 | 2 | 91 | The pad click layers: the 5 ms hand-over, and other buttons' windows over it |
| 90.21, 90.22 | 0 | 38 | `Cursor Gyro`'s menu Entry Points; the third transition |
| 90.24 | 0 | 116 | The required cleanups: 82 held back, 34 in Steering's driver layers |
| 90.25 | 8 | 130 | The menu chain: 90 held back |
| 90.26 to 90.30 | 0 | 56 | The 55 ms reset on the pad touch; the chain over the pad layers; the stateful Fn layers; the pad window's button Releases |
| 90.34, 90.35 | 0 | 16 | The fallback guard |

A line can also say "not in 90.25 to 90.26". In those two versions the pad's
touch went through a Touch Entry Point, one press more than the chains follow,
so the line was out of the tool's reach. I can't tell from this whether it was
gone on the Deck.

## What the tool does not see

- **Time.** An entry that can fire on a stack where the delay is pending is
  listed, however unlikely the gesture. "Keeps firing" means the entry repeats
  and still answers after it fired, not that it runs for long.
- **More than one extra press.** The stacks are the chains' with one arrival.
- **Chords, when building stacks.** The chains follow every add as if its
  chord could fire, so a stack that can't happen may be listed. The verdict
  column does read the chords, against the delay's own buttons only.
- **What can't be held together.** Opposite stick directions, or a trigger's
  full pull without its soft pull. `LS up pressed` appears under a delay on
  `LS down`.
- **`hold_layer` and mode shifts.** Not followed (A42, A34).
- **What happens next.** A covered delay coming back when its cover leaves
  (A14) is not traced. `check.py` shows it for two gestures.
- **Renames.** `(Gyro) X`, July's `*X`, the one menu Entry Point and
  Steering's menu Entry Points are matched to today's names. Any other rename
  would read as a new line.

Each effect is an assumption about Steam, by ID in the Terms table. A15 and
A12 are verified; A13 is reported; A14 and A36 are not verified.

## Reproduce

```bash
python3 findings/2026-10-06-delay-interruptions/audit.py             # 50 s: writes interruptions.json
python3 findings/2026-10-06-delay-interruptions/report.py --summary  # writes the two inventories, prints the counts
python3 findings/2026-10-06-delay-interruptions/check.py             # thirteen gestures on the simulator
python3 findings/2026-10-06-delay-interruptions/audit.py --layer "Menu Left: Entry Point"   # one host, as JSON
```

`audit.py` stops if the working layouts are not the newest snapshot: its
history ends at the snapshots.
