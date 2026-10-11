# Plan: Soft Press timers on the stick's edge, the Steering removes, and what 90.53 had

**Status, 2026-10-11:** built as **90.55**, from the 90.54 snapshot, both
layouts ([record](../findings/2026-10-11-edge-soft-press-timers/README.md)).
The author's answers: the threshold at 40% (13276), both recommended rows of
part 5 in, and 90.54 scrolled on every attempt on the Deck. The text below is
the plan as it was approved.

The author's requests (2026-10-11), on 90.54:

1. Take the right pad removes out.
2. Make the timer a Soft Press, and do the same in the left stick's scroll up
   and scroll down layers.
3. Audit the Steering layers for unnecessary removes.
4. The left stick cleanups of the entry layer become how the other Steering
   layers do it.
5. Say which fixes of 90.53 are missing.

## Terms

- **Driver:** R1 for W and L1 for S in `Steering` (the triggers' soft pull in
  the alternative layout). **W layer:** `Steering | R1: W Key`; the **S layer**
  is its twin.
- **Stick modifiers:** `Steering | LS Up: Modifier 1` and
  `Steering | LS Down: Modifier 0`.
- **Scroll layers:** `Steering | LS Up: Scroll Up` and
  `Steering | LS Down: Scroll Down`.
- **Timer:** the delayed bind that adds `Steering | LS: Tap Cover` (200 ms,
  stick modifiers) or `Steering | LS: Double Tap Cover` (150 ms, scroll
  layers).
- **Cleanup:** a bind that removes layers left on by a missed release.

## Parts 1 and 2: the timers

In 90.54 the stick modifiers' timer is a Chorded Press on the edge with three
right pad removes, and the scroll layers' timer is still a Chorded Press on up
or down. After this plan all four are one Soft Press on the edge that adds
one layer:

| Layer | Edge, Soft Press | Adds |
|---|---|---|
| `Steering \| LS Up: Modifier 1` | Fire Start Delay 200 ms, not interruptible | `Steering \| LS: Tap Cover` |
| `Steering \| LS Down: Modifier 0` | The same | `Steering \| LS: Tap Cover` |
| `Steering \| LS Up: Scroll Up` | Fire Start Delay 150 ms, the same otherwise | `Steering \| LS: Double Tap Cover` |
| `Steering \| LS Down: Scroll Down` | The same | `Steering \| LS: Double Tap Cover` |

Up or down keeps what it has apart from the timer. In the stick modifiers
that is the reset and the Release. In the scroll layers it is the Release,
the scroll press and the reset: three entries where there are four.

The shape is the one turn assist already uses: a Soft Press with a start
delay on the right stick's edge that adds a layer (`Turning Ramp Up 0`,
250 ms).

Being a Soft Press and not a chord, the timer no longer shuts off the edge's
cleanup (the side effect I reported on 90.54).

**The threshold.** A Soft Press needs one. I would set **13276**, the stick's
D-pad deadzone in these layers, so the timer starts when up or down
registers, as today. The Soft Presses in the layouts are all between 23000
and 29031. With 23000 a shallow push held for a second would never become a
hold and would scroll on release. 13276 is inside the range the file is taken
to allow (10,000 to 32,000) but lower than any Soft Press the layouts hold,
so the slider is worth a look once it is loaded.

## Part 4: the left stick's edge cleanup

I read this as the decision of 2026-10-10: the Entry Guard's edge bind is the
pattern, and the other Steering layers copy it.

| | Today, ten layers | `Steering \| LS: Entry Guard`, and the ten after this plan |
|---|---|---|
| Edge | Regular Press, repeating: the cleanup list. Chorded Press on the drivers, empty: its guard | One Chorded Press on the drivers with Invert Activation, repeating: the cleanup list |

The ten layers: the W and S layers, the two stick modifiers,
`Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`, the two scroll
layers and the two Steering Modifier 2 layers. `Steering` binds no edge. The
two stick windows keep their empty edge.

With it, as decided the same day: no Steering layer states an outer ring
radius on the left stick, like the Temp Cursor Gyro layers. Ten state 13276
today. The Soft Press has its own threshold, so the timers don't move with
the radius.

Not included: the left stick's touch keeps the cleanup press and its guard.
An inverted chord there would run while the thumb is off the stick, which is
a different thing.

Known and set aside by the author: a repeating chord with more than one
sub-command may not fire its repeat. The Entry Guard's list is one remove;
the ten lists are four to seven.

## Part 3: the remove audit

Each layout has 176 binds with removes in the 14 Steering layers.

**Unnecessary, to take out:**

| What | Where | Count |
|---|---|---|
| Right pad removes | The stick modifiers and the two Steering Modifier 2 layers: the 200 ms timers and both stick touch Releases | 12 binds, 54 removes |
| Three of the twelve removes in the Modifier 2 entry | The W layer's L1 chord: `R1: Tap Cover`, `Steering \| L1!R1: Modifier 2`, and `Steering \| R1!L1: Modifier 2`, the layer it then adds. The S layer's R1 chord: the mirror | 2 binds, 6 removes |

The other nine in each Modifier 2 entry remove the stick's layers and the
Modifier 2 hold marker, which can be on when the second driver is pressed.

**Kept, each with a job:**

- The right pad removes of the Modifier 2 clear to Base, and the one in each
  stick window's right pad Release.
- The other cleanups and Releases. The Cleanup audit checks all 145 lists
  and passes.
- `Steering`'s exit on a full push up or down: 16 removes, each a Steering
  layer or a Modifier 2 hold marker.
- The rest remove one layer each: their own, or the cover they reset.

**A check that misled.** Asking the audits' stack model which removes target
a layer that can never be on gave 70. 66 of them are needed: the stick touch
Releases removing the thumb's helper layers (`LST: Tap Cover` and the like),
and Start and Select removing the gyro ramp layers. On the simulator both
kinds do land inside `Steering`. The model does not follow chords and delayed
adds, so it cannot see them. The other four are in the table above.

## Part 5: what 90.53 has that 90.54 does not

| 90.53 | In this plan |
|---|---|
| Right pad removes out of the four modifier layers | Yes, part 3 |
| Left edge: one inverted chord in ten layers, default radius | Yes, part 4 |
| The 150 ms timer off stick up and down in the scroll layers | Yes, part 2, on the edge |
| The 200 ms timer off stick up and down | Done in 90.54, on the edge |
| **W and S layers, up and down: no cleanup press.** These binds can remove the W or S layer under a held driver, which is the "flick the stick and W drops" fault | **Recommended.** The chord that adds the stick modifier stays as it is, on the driver |
| **A and D in the stick modifiers send only the key**, no add of `Steering \| LS: Tap Cover` (author, 2026-10-10) | **Recommended.** A quick up rolled into A or D then scrolls once |
| Both drivers bound in the stick layers, with the timers on them | No. The edge replaces it |
| The second driver's entry into Modifier 2 from the stick layers | Not needed: the stick layers bind no driver here, so the W or S layer still answers |
| Cleanup lists recomputed | Follows from the fix pipeline |

The tool changes of 90.53 (the corrected inverted chord in the simulator, the
audits) are in the repository already.

## What I need

1. **The threshold:** 13276, or the value you want.
2. **The two recommended rows of part 5:** in or out.
3. **90.54 on the Deck:** did every tap scroll with the timer on the edge?
   This plan assumes yes (A64 is still marked unverified).

## Build steps

1. A builder in a new findings folder, reading the 90.54 snapshot: parts 1 to
   4 and the accepted rows of part 5, then the fix pipeline.
2. Before trimming the Modifier 2 entry: replay the scenario suite with and
   without the six removes. Any difference keeps the remove.
3. Tools: the flow model reads a delayed Soft Press on the stick's edge as
   the hold timer whose reset sits on the direction (R120); the register's
   ten R111 entries are regenerated for the new lists.
4. Assumption rows: a Soft Press on a D-pad stick's edge fires at its own
   threshold whatever the outer ring radius, and with a start delay waits
   its full time on every entry.
5. Tests: scenarios for 90.55 (taps and holds in any order in both
   directions, second deflects and the 150 ms cover, a shallow hold, the
   driver let go, the other driver, a missed release, the right pad through a
   hold). The 90.53 scenarios are frozen to their candidate; the older tests
   are set to what 90.55 does.
6. Build audit, VDFs, snapshot, record.

## On the Deck afterwards

1. Hold a driver, tap up eight times with a hold in between: one wheel step
   per tap, none for a hold. The same downwards.
2. Tap, then deflect again inside the window and hold: scrolling starts and
   repeats after 150 ms, every time.
3. A shallow push held past 200 ms, then back: no wheel step.
4. Flick the stick about with a driver held: W or S stays.
5. Rest a thumb on the right pad and hold up past 200 ms: the pad still
   scrolls.
