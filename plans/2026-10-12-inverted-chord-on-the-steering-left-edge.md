# Plan: one inverted chord as the left-edge cleanup in the Steering layers

**Status, 2026-10-12:** built as **90.61** on the author's word ("I think
we're good to start building", keeping 90.58's remove lists;
[release record](../findings/2026-10-12-inverted-chord-on-the-steering-left-edge/README.md)).
The three questions were settled as: build it; delete the 90.59 and 90.60
files; call it 90.61. The section on 90.55 below overstates it: the record
says how 90.55 differed.

The author, 2026-10-12: "working from 90.58 and reverting all the changes to
the documentation and updating them. also reverting the changes we made to
the tests. i want you to update the edge clean up binds to instead of using a
repeating regular press that's interruptible, and a chord that is a guard, I
want you to just use a single inverted chord that is repeating ... all we're
doing is updating the edge cleanup bind on the left stick. And all the
steering layers."

## Terms

- **Press and guard:** what the left edge has on 90.58. A repeating,
  interruptible Regular Press that removes layers, and beside it an empty
  Chorded Press on the bumpers that is not interruptible and holds the press
  back. It can run only with the stick **at** the rim.
- **Inverted chord:** a Chorded Press with Invert Activation. It runs while
  its own input is released and **no** chord button is held (A61). On the
  edge that means: stick **off** the rim and no bumper held.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key` (R2 and
  L2 in the alternative layout).
- **The ten layers:** the Steering layers whose left edge has a press and
  guard on 90.58: the two driver layers, the two stick modifiers,
  `Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`, the two
  stick scroll layers and the two Modifier 2 layers.

## Why

The fault
[`Steering` ends on a right stick touch with a bumper held](../findings/2026-10-12-steering-ends-on-a-stick-touch/README.md).
The author found on the Deck that the driver layer's own left-edge cleanup
fires although its bumper is held: while right stick touch Releases send
`remove_layer` calls, a press of the edge sometimes "doesn't notice that RB
is still being held". With an inverted chord there is no press on the edge
for the guard to miss.

## The change

On the left edge of the ten layers, in both layouts:

| Edge entry | 90.58 | New |
|---|---|---|
| Cleanup | Regular Press, repeating, interruptible, removes the list | One Chorded Press on the same bumpers with Invert Activation, repeating, not interruptible, quiet, removes the same list |
| Guard | Empty Chorded Press on the bumpers | Gone |
| Timer, in the four timer layers | Soft Press at 13276, 200 or 150 ms | Unchanged |

- **Per layout:** 10 inputs change; 10 press entries and 10 guard chords go,
  10 inverted chords come in. The remove lists are 90.58's, command for
  command, so the count of removes stays 2,851 and 2,909.
- **The chord's settings** are the ones `Steering | LS: Entry Guard` has
  today and these ten edges had in 90.55: the layer's bumper mask, "Any",
  Invert Activation, Hold to Repeat, not interruptible, haptics off.
- **Not touched:** both stick touches, the right edge, the buttons, the
  bumper Releases, `Steering`'s exit, the Entry Guard, the two stick Double
  Tap windows (their left edge is a plain block), the outer ring radius.

## What changes in play

| | 90.58 | New |
|---|---|---|
| Bumper held, stick anywhere | Nothing runs, if the guard holds | Nothing runs, if Steam sees the bumper |
| No bumper, stick at the rim | The cleanup runs | Nothing runs |
| No bumper, stick off the rim | Nothing runs | The cleanup runs, and repeats |

A driver or stick layer left on by a missed bumper release clears as soon as
the stick is off the rim, where today it waits for the rim, a stick touch or
the next bumper press.

## This was built before, and taken out

It is 90.55's left edge on the same ten layers. 90.56 put the press and guard
back the next day, on the author's word, after this report on 90.55: with a
bumper held and the stick up or down, **a thumb lifting from a stick cleared
the W or S layer and `Steering` ended**. The author suspected the inverted
chord fires after a `remove_layer` call although a bumper is held (A66,
unverified).

Today's finding points the same way for both shapes: around `remove_layer`
calls Steam can miss that a bumper is held.

- **A press and guard** then misfires only if the edge is pressed at that
  moment, so only at the rim.
- **An inverted chord** asks "is no bumper held?" itself, and is live
  whenever the stick is off the rim, which is most of a deflect. On 90.55
  one thumb lift was enough.

So this change may bring the 90.55 fault back, and may make today's fault
easier to hit. It is planned as the author described it, and the first
question below asks about this.

## Rules and the register

- **R111** (an inverted edge on a D-pad stick never adds or removes a
  layer): ten register entries, as 90.55 had, for the exact chords. The
  Budget audit matches them.
- **R133** (a cleanup function is a press beside a guard chord): one entry
  for these ten edges, as 90.55 had.
- **R170** (a cleanup on each stick edge): the Cleanup audit already reads
  an inverted chord on an edge as that layer's cleanup there; it did for
  90.55, whose builder the tests still run.
- **A66** gets these ten layers back under "rests on".
- **A repeating chord with more than one sub-command does not fire its
  repeat** (author, 2026-10-10). Eight of the ten lists have two to five
  removes; only the two driver layers have one. The first run still happens
  when the chord becomes live. Kept as 90.58's lists, as the author asked
  for one change only.

## The reverts

Everything since commit `a34f4a4` (90.58) is uncommitted. Going back:

| What | Action |
|---|---|
| Installed layouts and VDFs | Back to 90.58, then the new build |
| The R128 exception: register entries, `cleanups.py`, `exceptions.py`, `cleanup_lists.py`, `audit_cleanups.py`, R128's row | Reverted with `git checkout` |
| `docs/building.md`, `todos.md`, `tests/scenario.py` | Reverted, then updated for the new build |
| `tests/test_scenarios_90_59.py`, `tests/test_scenarios_90_60.py` | Deleted |
| The 90.59 and 90.60 builders, records and snapshots; the 90.60 plan | Deleted (question 2) |
| The fault record | Kept and updated: it is the only place that says what 90.59 and 90.60 tried and that neither helped |
| The other session's folder (`steering-ends-while-rocking`) | Not touched |

Untracked files are not in git, so deleting them cannot be undone.

## Build steps

1. The reverts above.
2. A builder in a new findings folder, reading the 90.58 snapshot. It
   asserts: ten inputs change per layout, each chord carries exactly the
   press's 90.58 list, nothing else differs but the title.
3. The register entries, then the fix pipeline. It must change nothing.
4. Tests: the edge's shape on the ten layers; the scenarios of 90.55 for the
   inverted edge (C1 to C4), now on the working layout again; the scenarios
   of 90.56 that state the press and guard, frozen on 90.58; the fault's
   gesture.
5. Random walks against 90.58, logs compared. Differences are expected
   wherever no bumper is held in one of the ten layers; they are listed.
6. Rocking tests, build audit, full suite, VDFs, snapshot, record.

## What it costs

- **The 90.55 fault may return** (above).
- **The simulator cannot judge it.** It reads an inverted chord as off while
  a bumper is held, always. Every result here is "as designed", not "as the
  Deck does it".
- **Twelve register entries** for R111 and R133 come back.

## Questions before building

1. **The 90.55 fault.** Hold R1, push the stick up, lift a thumb from a
   stick: on 90.55 that ended `Steering`, and you had this bind taken out
   for it. Build it anyway as a Deck trial, or first try the smaller change:
   no cleanup at all on the left edge of the two driver layers (2 binds, 2
   removes fewer, nothing left there to misfire)? **My pick: the smaller
   change first.** If you say build it, I build it as described.
2. **The 90.59 and 90.60 files.** Delete their builders, records, tests and
   snapshots, or keep them as history of two trials that did not help? They
   are not committed, so deleting is final. **My pick: delete them, and keep
   their story in the fault record.**
3. **The version number.** Layouts titled 90.59 and 90.60 have been on your
   Deck. Call the new build 90.61, or reuse 90.59? **My pick: 90.61**, so
   no two different layouts ever carried the same number.

## On the Deck afterwards

1. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays, W stays.
2. The 90.55 gesture: hold R1, stick up or down, lift a thumb from either
   stick. `Steering` stays, W stays.
3. Rock L1 and R1 in `Steering` with the stick out.
4. Let go of everything with the stick centred: `Steering` alone, no key
   held.
