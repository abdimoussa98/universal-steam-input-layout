# Plan: the left edge's cleanup without inverted chords

**Status, 2026-10-11:** not built. The author chose the simpler way: "switch
back to normal clean ups for all besides the steering entry guard". 90.56 has
the press and its guard chord on all ten edges, and the Entry Guard keeps its
inverted chord
([record](../findings/2026-10-11-edge-cleanup-press-and-guard/README.md)). The
text below is the plan as it was offered.

The author, 2026-10-11: revert to the older cleanup pattern on the left
stick's edge, except in the layers that assume the stick is deflected, like
the two stick modifiers and the Entry Guard. Those get a repeating Soft Press
on the inner stick.

## Why

On 90.55 a thumb lifting in the Steering stick modifiers cleared the W or S
layer and ended `Steering`. The author suspects the chord with Invert
Activation fires after a `remove_layer` call although a bumper is held. Ten
such chords can remove the W or S layer
([audit](../findings/2026-10-11-stick-touch-and-cleanup-audit/README.md)).
After this plan no chord has Invert Activation, and nothing on the left edge
that lacks a bumper guard can remove the W or S layer.

## Terms

- **Driver:** R1 for W and L1 for S in `Steering` (the triggers' soft pull in
  the alternative layout).
- **Older pattern:** on the edge, a repeating Regular Press that removes the
  cleanup list, held back by an empty Chorded Press on the drivers (its
  guard). The shape of 90.54.
- **Inner Soft Press:** a Soft Press with Invert Activation. It is down while
  the stick is inside its threshold.

## Which layers

Eleven layers have an inverted chord on the left edge. You named the two
stick modifiers and the Entry Guard as assuming the stick is out. Four more
do: each is only on while the stick is held up or down.

| Layer | Assumes the stick is out | Left edge after the plan |
|---|---|---|
| `Steering \| R1: W Key`, `Steering \| L1: S Key` | No: a bumper is held, the stick can be centred | Older pattern |
| `Steering \| R1!L1: Modifier 2`, `Steering \| L1!R1: Modifier 2` | No | Older pattern |
| `Steering \| LS Up: Modifier 1`, `Steering \| LS Down: Modifier 0` | Yes | Inner Soft Press, and the 200 ms timer as it is |
| `Steering \| LS: Tap Cover` | Yes (missed in your list) | Inner Soft Press |
| `Steering \| LS Up: Scroll Up`, `Steering \| LS Down: Scroll Down` | Yes (missed) | Inner Soft Press, and the 150 ms timer as it is |
| `Steering \| LS: Double Tap Cover` | Yes (missed) | Inner Soft Press |
| `Steering \| LS: Entry Guard` | Yes | Inner Soft Press, and its edge Release as it is |

The two stick windows are the opposite case: they are on while the stick is
centred between taps. They keep their empty edge.

## The binds

**Older pattern**, in the W layer (the S layer mirrors it):

- Regular Press, repeating: remove the W layer and the six stick layers, the
  list the inverted chord has today.
- Chorded Press on R1, empty, not interruptible.

The two Modifier 2 layers the same, with their list of three and the chord on
R1 or L1. The outer ring stays at Steam's default, so this press can only
fire with the stick at the rim.

**Inner Soft Press**, in `Steering | LS Up: Modifier 1` (the same in the
other six, each with its own layer):

- Soft Press, Invert Activation, Hold to Repeat, not interruptible, no
  haptics: remove `Steering | LS Up: Modifier 1`.

It removes its own layer and nothing else. It has no bumper guard and runs
whenever the stick is centred, so it must not list the W or S layer. Layers
stacked on each other clear one after the other: the Tap Cover first, then
the modifier under it.

## One decision: when the inner Soft Press starts

The normal end of a tap is up's Release: it opens the window that scrolls.
The inner Soft Press must not get there first, or the modifier is gone before
its Release runs.

| | A. As you described | B. With a short delay (my pick) |
|---|---|---|
| Threshold | 10000, about 30%: under the stick's 40% deadzone, so on the way back the Release comes first | 13276, the same 40% as the timers |
| Fire Start Delay | None | 50 ms |
| A stale layer clears | At once | 50 ms after the stick is centred |
| If Steam handles the edge and the direction in the same instant | The cleanup can beat the Release, and the W layer's repeating chord puts the modifier straight back: the two fight | Nothing: the Release removes the layer and the delay never ends |
| New value in the file | 10000, lower than any Soft Press the layouts hold, at the bottom of the range the file is taken to allow | None |
| On the simulator (a prototype of each) | Loops: the simulator presses the direction before the edge, and the entry chord and the cleanup remove and add the modifier without end | The stick, cleanup and Entry Guard scenarios pass, apart from one that states the inverted chord's timing. With the edge let go up to 120 ms before the direction, every tap still scrolls once. A stale Tap Cover and modifier are gone after 80 and 140 ms, and the W layer is left alone |

The simulator's loop in A comes from its own order of events, which a real
stick may never produce. It still shows what happens whenever the stick
counts as inside while the direction counts as pressed.

## What it costs

- **Your rule R111 bans this** on a D-pad stick: an inverted edge may not add
  or remove a layer, because on 2026-10-01 you saw the stick's return to
  centre missed there sometimes (A19). Here a miss only delays a backup: each
  of the seven layers still ends on its own Release. The seven go into the
  register as exceptions, as your decision of today. The eleven entries for
  the inverted chords go out.
- **The W and S layers' edge press** is the kind of bind that could drop W
  under a held bumper before 90.53, when it sat at 40% and fired on every
  deflect. At the default ring it is reached only at the rim.
- **A stale W or S layer** (a bumper release Steam missed) clears when the
  stick reaches the rim, on a stick touch, or on the next bumper press. With
  the inverted chord it cleared as soon as the stick was centred.
- **The Entry Guard** leaves 50 ms after a centred entry (option B), not at
  once.
- The stick touch cleanups stay as they are.

## What I need

**A or B** for the inner Soft Press. B is what I would build.

## Build steps

1. A builder in a new findings folder, reading the 90.55 snapshot: the four
   edges back to the older pattern, the seven inner Soft Presses, then the
   fix pipeline.
2. Tools: the flow model reads the inner Soft Press as a cancellation (R135:
   it removes only itself, repeats, has no guard), also with a start delay;
   the Cleanup audit takes it as the edge's cleanup in these seven layers
   (R170).
3. Register and rules: seven R111 entries in, eleven out; R133's exception
   text; an assumption row for a repeating inner Soft Press on the D-pad
   stick's edge, beside A19.
4. Scenarios for 90.56: taps and holds in any order, also with the edge let
   go before the direction; a stale stick layer clears with the stick
   centred and never takes the W or S layer; a thumb lifting at every stage
   with the thumbs resting before the bumper; the Entry Guard. The 90.55
   scenarios are frozen to their candidate.
5. Build audit, VDFs, snapshot, record.

## On the Deck afterwards

1. Rest both thumbs on the sticks, hold R1, push the stick up halfway, lift
   the right thumb: W stays and `Steering` stays.
2. Hold a bumper and tap the stick up and down twenty times: one wheel step
   each.
3. Flick the stick to the rim and around it with a bumper held: W or S stays.
