# The Steering stick: Soft Press timers on the edge, the edge cleanup, and the removes (90.55)

Built on 2026-10-11 from the **90.54** snapshot, both layouts, on the author's
plan and answers of the same day
([plan](../../plans/2026-10-11-edge-soft-press-timers-and-steering-removes.md)).
No layer is added or removed: 90 in each layout. Nothing here has run on the
Deck as built.

## Why

- **90.54 works on the Deck** (author, 2026-10-11): with the 200 ms timer on
  the left stick's edge, a deflect scrolled "on every scroll attempt". On
  stick up or down it had scrolled once and then not again (A63). So the edge
  can own a start delay (A64).
- The author then asked for the timer as a Soft Press, the same in the two
  scroll layers, the right pad removes out, the Entry Guard's edge cleanup in
  the other Steering layers, an audit of the removes, and the fixes of 90.53
  that 90.54 lacked.

## What changed

12 layers and 42 changed inputs or groups per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

| What | Layers | Change |
|---|---|---|
| Timers | The two stick modifiers, the two stick scroll layers | One Soft Press on the left stick's edge each: threshold 13276, not interruptible, Fire Start Delay 200 ms for `Steering \| LS: Tap Cover` and 150 ms for `Steering \| LS: Double Tap Cover`. It adds that one layer and removes nothing. In the scroll layers the 150 ms chord leaves up or down, which goes from four entries to three. The reset and the Release stay on the direction |
| Edge | The W and S layers, the two stick modifiers, `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover`, the two stick scroll layers, the two Steering Modifier 2 layers | The repeating cleanup press and its empty guard chord become one chord with Invert Activation on the same drivers and the same list, the Entry Guard's pattern |
| Radius | Ten Steering layers | The left stick states no outer ring radius, as in the Temp Cursor Gyro layers. It was 13276. All fourteen Steering layers now use Steam's default |
| Right pad | The two stick modifiers, the two Steering Modifier 2 layers | 12 binds lose their `RTP:` removes, 54 in all: the 200 ms timers and both stick touch Releases. The Modifier 2 Release, the clear to Base, keeps them |
| W and S layers | Up and down | The cleanup press is gone. The chord that adds the stick modifier is unchanged, on the driver alone |
| A and D | The two stick modifiers, left and right | They send the key and no longer add `Steering \| LS: Tap Cover`. The stick clicks keep that add |
| Modifier 2 entry | The W layer's chord on the other driver, and the S layer's | Three of twelve removes go: the other order's hold marker, the other order's Modifier 2, and the Modifier 2 the entry then adds. Nine stay: the eight stick layers and the hold marker of the Modifier 2 it enters |

The fix pipeline changed nothing after these steps.

Unchanged: `Steering`, `Steering | LS: Entry Guard`, the two stick windows
(apart from the radius), and every right-stick edge and stick touch, which
keep the press-and-guard shape.

## The Soft Press

The shape is turn assist's: `Turning Ramp Up 0` adds a layer from a Soft
Press with a 250 ms start delay on the right stick's edge.

- **Threshold 13276** (author: "40%"): the stick's D-pad deadzone in these
  layers, so the timer starts when up or down registers, as before. Every
  other Soft Press in the layouts is between 23000 and 29031.
- **Its own threshold starts it**, so the outer ring's move to Steam's default
  does not move the timer (A65, unverified on this stick).
- **Not a chord.** In 90.54 the timer was a chord on the deflect, which is
  always out at the edge, and so shut off the edge's cleanup press (A27).
- **Haptics:** not stated, as on the chord it replaces.

## The remove audit

176 binds carry removes in the 14 Steering layers of each layout.

- **Taken out:** the 54 right pad removes above, and six in the two Modifier 2
  entries. For those six, every scenario was run on a build that still had
  them, counting whether one ever found its layer on the stack or named the
  target of a running start delay. Over 370 scenario tests the two entries
  fired 900 times and none of the six ever did either
  (`build_candidate.py --keep-entry-removes` writes that build).
- **Kept:** the clear to Base, each stick window's right pad Release,
  `Steering`'s exit (16 removes, each a Steering layer or a Modifier 2 hold
  marker), and the cleanups and Releases, whose 145 lists the Cleanup audit
  checks.
- **A check that misled:** the audits' stack model names 70 removes of a layer
  that "can never be on". 66 are needed: the stick touch Releases removing the
  thumb's helper layers, and Start and Select removing the gyro ramp layers.
  Both kinds land inside `Steering` on the simulator. The model does not
  follow chords and delayed adds.

## What you would feel

- Every quick deflect scrolls once and every hold past 200 ms does not, in
  any order, as on 90.54. A second deflect held past 150 ms repeats.
- A quick up or down rolled into A or D inside 200 ms scrolls once: it is a
  tap. Until 90.54 the side key made it a hold.
- With a driver held, nothing on the left stick's edge, up or down removes
  the W or S layer.
- The right pad's layers stay on when the stick's 200 ms hold or Modifier 2's
  lands, and when a thumb lifts from a stick in those layers.
- A W or S layer left on by a missed driver release clears when the stick is
  inside the ring with no driver held.

## Rules, the register and the tools

- **A64:** reported by the author on the Deck. **A65** (new, unverified): a
  Soft Press on a D-pad stick's edge fires at its own threshold whatever the
  outer ring radius, and with a start delay waits its full time on every
  entry.
- **R120:** the reset of the four timers is on the stick's direction, the
  timer on the edge. `steam_layout/flow_model.py` reads a repeating removal on
  a direction as the reset of a delayed add on that stick's edge.
- **R111:** the register's entries for the W layer, the S layer and
  `Steering | LS: Double Tap Cover` hold the lists of this build; the other
  seven are as in 90.53.
- **Tests:** the stick scenarios of 90.53 and the scenarios of 90.54 now run
  on their own candidates (`frozen`). The Entry Guard scenarios of 90.53 stay
  on the working layout.
- Set aside by the author: whether a repeating chord with more than one
  sub-command fires. Each of the ten edge lists is longer than one
  (`todos.md`).

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup).
- **Against 90.54 on the simulator:** the 384 logged points of the 90.54
  record replayed on both builds. They differ in 32, all of them a quick up or
  down rolled into A or D, which now scrolls once.
- **Scenarios:** `tests/test_scenarios_90_55.py`, 19 tests, pass: taps and
  holds in any order, second deflects and the 150 ms cover, a press during a
  deflect, the side keys, the right pad through a hold, the other driver from
  every stick layer, the driver let go at every stage, a missed driver
  release, and the shapes. Every layer that changed is on the stack in a
  scenario (R165). The assumptions that aren't verified, with what rests on
  each, are in [unverified-assumptions.txt](unverified-assumptions.txt).
- **Not simulated:** a shallow push. The simulator presses the edge with the
  direction, so the Soft Press starting at its own threshold is A65, for the
  Deck.
- **Full suite** on the installed 90.55, 2026-10-11: 1185 tests, 25 expected
  failures (the `old_inverted_chord` scenarios), 22 failing.
  - 14 fail on 90.52 as well, in five modules: `test_fallback_window_backport`
    (1), `test_layer_report` (1), `test_neptune_gyro` (6),
    `test_steering_entry_quiet_drivers` (1), `test_steering_rtp_menu_chords`
    (5).
  - 8 were one test on the edge of the four timer layers, in both layouts:
    `test_layout_rules.test_a_cleanup_input_stores_the_regular_press_then_the_guard_then_the_release`
    knew three kinds of entry on a cleanup input, and that edge now also
    holds the timer's Soft Press, stored after the cleanup. The test allows
    it there now and passes; the suite was not run again after that.

## On the Deck, in this order

1. Load fresh. Hold a driver in `Steering` and tap the stick up eight times,
   with a hold past 200 ms in between: one wheel step per tap, none for a
   hold. The same downwards (A64, A65).
2. Tap, then deflect again inside the window and hold: one wheel step on the
   press, repeating after 150 ms, every time.
3. Push the stick less than halfway, hold it for a second, let go: no wheel
   step. A wheel step means the Soft Press waits for the outer ring (A65).
4. Flick the stick about with a driver held for ten seconds: W or S stays,
   and `Steering` stays.
5. Up, then roll to the left inside 200 ms: A, and one wheel step.
6. Rest a thumb on the right pad and hold up past 200 ms: the pad still
   scrolls.
7. With R1 held and the stick up, press L1: the Modifier 2 layer at once.
