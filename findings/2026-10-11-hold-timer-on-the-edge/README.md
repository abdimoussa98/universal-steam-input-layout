# The stick's hold timer on the left stick's edge (90.54)

Built on 2026-10-11 from the **90.52** snapshot, both layouts, on the author's
request: "working from 90.52 I want you to make one simple change". Nothing of
90.53 is in it. 90 layers in each layout.

**On the Deck (author, 2026-10-11):** "its working on every scroll attempt".
The edge can own the delay (A64). 90.55 continues from this build
([record](../2026-10-11-edge-soft-press-timers/README.md)).

## Why

In 90.52 the 200 ms delay that adds `Steering | LS: Tap Cover` is owned by
stick up or down, and after one quick deflect it lands at once on every later
one (author, on the Deck, 2026-10-10; A63). On a bumper it waits its full time.
90.53 moved it to the bumpers, which took a shared modifier and a second
entry into Modifier 2. This build tries the edge, the stick's outer ring bind,
as the owner, with nothing else changed (A64, unverified).

## The one change

In `Steering | LS Up: Modifier 1` and `Steering | LS Down: Modifier 0`, the
Chorded Press that adds the Tap Cover moves whole from the layer's own
direction (up in Modifier 1, down in Modifier 0) to the left stick's edge
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt): 2 layers,
4 changed inputs each).

| Input | 90.52 | 90.54 |
|---|---|---|
| Up (down in Modifier 0) | Reset, the timer, the Release | Reset, the Release |
| Edge | Cleanup press, its guard chord | Cleanup press, its guard chord, the timer |

The timer, as it was: Chorded Press, chord button the left stick's deflect,
Fire Start Delay 200 ms, not interruptible. It adds `Steering | LS: Tap Cover`
and removes `RTP: Entry Point`, `RTP: Tap Cover` and `RTP: Circular Scroll`.

Left as in 90.52, because the request was one change:

- The reset (every 250 ms, removes the Tap Cover) and the Release stay on up
  or down.
- The timer keeps its three right pad removes.
- The two stick scroll layers keep their 150 ms on up and down.
- The edge radius stays 13276, the same as the stick's deadzone.

## What to know about it

- **The edge's cleanup press in these two layers.** The timer's chord button
  is the deflect, which is always out when the stick is at the edge. An active
  chord shuts off an interruptible press on the same input (A27), so that
  cleanup press should no longer run. On the simulator a stale stick modifier
  still clears as in 90.52, by its other binds.
- **Three entries on the edge**, the limit (R109).
- The fix pipeline was not applied. Run on the result, it changes nothing
  (`*-build-report.json`).

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup).
- **Against 90.52 on the simulator:** the same gestures replayed on both
  builds, 384 logged points over both layouts and both drivers (taps and holds
  from 20 to 500 ms, rolls into A and D, a face button and both stick clicks
  during a deflect, the other driver, the driver let go, a missed release).
  No difference. The simulator does not model the fault, so this says only
  that the build is wired as 90.52 was.
- **Scenarios:** `tests/test_scenarios_90_54.py`, 6 tests, pass.
- **Full suite** on the installed 90.54, 2026-10-11: 1166 tests, 25 expected
  failures (the `old_inverted_chord` scenarios), 34 failing.
  - 14 fail on 90.52 as well, in five modules: `test_fallback_window_backport`
    (1), `test_layer_report` (1), `test_neptune_gyro` (6),
    `test_steering_entry_quiet_drivers` (1), `test_steering_rtp_menu_chords`
    (5).
  - 17 describe 90.53, which this build does not contain:
    `test_scenarios_90_53` (12), and the tests rewritten for 90.53 in
    `test_scenarios_90_52` (3), `test_scenarios_90_38` (1) and
    `test_scenarios_90_49` (1). Left as they are until the next build says
    which statements hold
    ([plan](../../plans/2026-10-11-edge-soft-press-timers-and-steering-removes.md)).
  - 3 were bookkeeping and are fixed: two in the rule tables (R120 named the
    Deck; R120 and A63 did not name each other) and one here (two scenarios
    named R166 and R167, which no scenario checks).

## On the Deck

1. Load fresh. Enter `Steering`, hold a driver, and tap the stick up eight
   times, with a hold past 200 ms in between. Every tap scrolls once and no
   hold does: the edge works as an owner (A64). The second tap does not
   scroll: the edge fails as the direction did.
2. The same downwards.
