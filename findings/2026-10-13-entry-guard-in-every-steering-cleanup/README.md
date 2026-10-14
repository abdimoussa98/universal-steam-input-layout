# Every cleanup function in the Steering layers adds the Entry Guard (90.70)

Built on 2026-10-13 from the **90.68** snapshot, both layouts, on the author's
word: "for 90.70 keep the changes from 90.68 and have all the steering
cleanups add the entry steering guard". 90 layers in each layout.

**On the Deck, 2026-10-13, the author:** "the only solution that works is 90.70. we will get leaks and this precaution works".
Which of the other builds were tried, and the separate checks at the end
of this record, are not on record.

It is the working layout. [90.69](../2026-10-13-steering-cleanup-presses-without-repeat/README.md),
the trial without Hold to Repeat, is a separate build from 90.68 and is
not part of this one. Both are for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).

| | Default | Alternative |
|---|---|---|
| Cleanup presses in the Steering layers | 90 | 90 |
| Had the add since 90.67 (the left edge) | 10 | 10 |
| **Get the add in 90.70** | **80** | **80** |
| Adds, 90.68 to 90.70 | 380 to 460 | 380 to 460 |
| Removes, unchanged | 2,885 | 2,943 |

## Terms

- **Cleanup function:** on one input, a repeating, interruptible Regular
  Press that removes layers (the press), beside an empty chord on the
  layer's owner buttons (its guard chord), which holds the press back
  while an owner is held (A27).
- **The leak:** the press running although an owner is held, because a
  burst of `remove_layer` calls failed the chord (A69, confirmed on the
  Deck).
- **Driver:** R1 or L1 in `Steering` (R2 and L2 in the alternative).
- **The Entry Guard:** `Steering | LS: Entry Guard`. Its stick types W, S,
  A and D. It leaves on a direction's or the edge's Release, on a driver
  (whose chord adds the driver's layer and then removes the guard), and
  by itself while the stick is inside the ring and no driver is held.
- **The ten layers:** the two driver layers, the two stick modifiers, the
  Tap Cover, the Double Tap Cover, the two stick scroll layers and the two
  Steering Modifier 2 layers.

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.68: 10 layers, 80 changes each.

| Bind | 90.68 | 90.70 |
|---|---|---|
| The cleanup press on the left stick's edge of the ten layers | Adds the Entry Guard, then removes | Unchanged |
| Every other cleanup press of the ten layers: both stick touches, the right stick's edge, buttons, D-pad, stick clicks | Removes its list | Adds the Entry Guard, then removes its list |
| Settings of every press, every guard chord | | Unchanged |

The add is stored last, so it runs first (A4). Cleanup functions outside
the Steering layers carry no add.

## What it does

On a leak, whichever input it happens on, the Entry Guard lands before the
layers go, so the guard answers the stick and not `Steering`'s exit. The
held driver's chord in the guard then adds its layer and removes the
guard. 90.67 covered only a leak on the left stick's edge; the stick
touches, where the removes of the fault's gesture come from, were open.
This paragraph is read from the binds. No test runs a leak.

In an ordinary cleanup, on the simulator, with a driver's release missed:

| Then | 90.68 | 90.70 |
|---|---|---|
| A thumb touches the right stick, left stick at centre | The stale layer goes | The same; the guard lands and takes itself off in the same instant, with no key |
| A is pressed with the left stick held up | The stick modifier goes, then the driver layer by its own left edge, which leaves the guard: W, `Steering` stays | The stick modifier goes and the guard lands over the stale driver layer: W, `Steering` stays |
| The stick comes back to centre | Bare `Steering` | Bare `Steering` |

The second row is new: a cleanup that removes only its own layer can
leave a stale driver layer **under** the guard until the stick comes back.
It ends the same.

## Rules and tests

- **R176** now says every cleanup function in a Steering layer adds the
  Entry Guard first, and none outside does. **R133** and **A69** name both
  builds.
- **New tests,** [`tests/test_scenarios_90_70.py`](../../tests/test_scenarios_90_70.py),
  five: every Steering cleanup press repeats and stores the add last; no
  cleanup function outside the Steering layers adds a layer; against
  90.68 exactly 80 presses gain the add and nothing else differs;
  scenarios 90.70 J1 and J2 (the first two rows of the table above).
- **On the 90.67 build** (`frozen`): the 90.67 shape tests, which state
  the add on the left edge only.
- No tool changed for 90.70: the Cleanup audit already reads a press that
  adds only the Entry Guard as a cleanup function, and the chains do not
  follow that add.

## Validation

- **Build audit:** clean on both installed layouts (Budget, Window, Flow,
  Cleanup), and on both 90.69 candidates.
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **Random walks, the whole log compared** with 90.68 ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with
  one release in ten missed. The same run has 90.69.

  | Layout, releases missed | Walks that finish | Log differs, 90.69 | Log differs, 90.70 | A layer left on: 90.68, 90.69, 90.70 | After a thumb on each stick |
  |---|---|---|---|---|---|
  | Default, none | 11,715 | 2 | 20 | 21, 21, 21 | 0 on all three |
  | Default, one in ten | 11,723 | 49 | 154 | 299, 299, 299 | 0 on all three |
  | Alternative, none | 12,000 | 2 | 16 | 23, 23, 23 | 0 on all three |
  | Alternative, one in ten | 12,000 | 46 | 144 | 189, 188, 189 | 0 on all three |

- **The 90.70 walks that differ,** from 6,000 default walks (45 differ,
  29 of them in what is typed, not only in layers going on and off). The
  four with no release missed were read step by step, the others only
  counted. Each of the four is a cleanup that runs with the left stick
  out and no driver held; a Steering layer was stale there without a
  missed release, because a Double Tap window had answered the driver's
  Release. On 90.70 the guard then stays until the stick comes back:
  - `Steering` no longer ends. In one walk a thumb on the right stick
    cleared a stale S layer with the stick down: 90.68 ended `Steering`
    50 ms later, 90.70 types S and keeps it.
  - While the guard is on, its binds answer: the stick types W, S, A or
    D, the right pad's entry is blocked, and the left pad types the
    guard's keys (Escape in that walk).
- **The 90.69 walks that differ** were not replayed.
- **Full suite:** 1,301 tests in 117 modules, with the same 25 expected
  failures. Two older tests failed and state 90.70 now; both modules pass
  run again, and the whole suite was not run a second time:
  - `test_steering_entry_feedback` listed the removes of the stick
    modifiers' 26 button cleanups without the add.
  - Scenario 90.7 S4 stated that a right stick touch clearing a stale
    driver layer with the stick up ends `Steering`. It keeps `Steering`
    now, with the guard on until the stick comes back.
- **Unverified assumptions:** 51, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 416 scenarios.

## What it rests on

- **A4:** the add runs before the removes because it is stored last.
- **A61:** the guard's inverted chord takes it off with the stick inside
  the ring and no driver held, and does not run at the rim. Most cleanups
  on the 80 new presses happen with the stick at centre, so on the Deck
  the guard should come and go unseen there. If the chord is slow, the
  guard's binds show for that long: both trackpads blocked or retyped,
  the right stick's edge blocked.
- **A driver's chord in the guard runs on a driver that is already held**
  when the guard lands. It has two commands, and the author called out on
  2026-10-10 that such a chord does not fire its repeat. If it does not
  run, the guard stays until the stick comes back.
- **The audits do not see the guard landing from a cleanup:** the chains
  follow no cleanup function's add.
- **The leak still happens,** and nothing here shows the fault is gone:
  the simulator never runs a press past its guard.

## On the Deck

Check first that the configurator's title shows `:: 90.70`.

1. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays. W may
   blink.
2. Drive normally with a thumb coming on and off the right stick and the
   pads in use: nothing is blocked and no stray W, S, A or D is typed.
3. Rock R1 and L1 with the stick out: W, S, W, S.
4. With no driver held, push the stick fully up: `Steering` ends.
