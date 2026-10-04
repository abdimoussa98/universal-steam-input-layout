# Standard hold delays, the pad clicks' reset, touch layers with no delay (90.26)

**Status:** built and installed as 90.26 on 2026-10-04, rebuilt once the same
day (the first build had the resets at their delay + 5 ms). Not run on the
Deck. Build audit clean; the tests pass. Extends the
[90.25 builder](../2026-10-04-pad-bumps-and-menu-keys/README.md), which stays
frozen.

## What it changes

The author's decisions, 2026-10-04, after the audit below:

1. Every hold delay over 200 ms is 200 ms: the bumper Modifier 0 and 1 (300 ms)
   and the Steering Modifier 0 and 1 (250 ms).
2. Both menu buttons into `Menu Keys` take 200 ms, not 150.
3. Every reset still repeats at its delay + 50 ms (R121).
4. The second-press covers and the touches stay at 150 ms. The ramp-up layers
   are not touched at all.
5. The two Click Entry Points get a reset for their 5 ms outer ring bind, on
   the pad's touch.
6. The two touch layers lose that 5 ms delay: their outer bind starts where
   the inner one ends.

Twelve layers differ from 90.25
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)): eight
hold delays with their reset rates, and the four pad layers. The description's
three hold times follow.

Terms. A **hold delay** is a delayed `add_layer` that has a reset. A **reset**
is an entry that removes only that layer, with Hold to Repeat (R120, the
author's fix for a delay that gets stuck, A12). The **margin** is how long
after the delay the reset repeats. A **touch layer** is the hand-over layer a
pad's touch adds (`RTP: Touch Entry Point`, `LTP: Touch Entry Point`).

## The audit: every delayed add with a reset

The same numbers in both layouts, as delay / reset in ms.

| Hold | Layers | Adds | 90.25 | 90.26 |
|---|---|---|---|---|
| Modifier 0, 1 | `L1: Modifier 0`, `R1: Modifier 1`, their `Gyro \|` copies | `L1: Temp Cursor Gyro`, `R1: Temp Cursor Gyro` | 300 / 350 | 200 / 250 |
| Steering Modifier 0, 1 | `Steering \| LS Down: Modifier 0`, `Steering \| LS Up: Modifier 1` | `Steering \| LS: Tap Cover` | 250 / 300 | 200 / 250 |
| Both menu buttons | `Menu Left!Right: Entry Point`, `Menu Right!Left: Entry Point` | `Menu Keys` | 150 / 200 | 200 / 250 |
| Modifier 2 | `L1!R1: Modifier 2`, `R1!L1: Modifier 2`, their `Gyro \|` copies | `L1&R1: Tap Cover` | 200 / 250 | the same |
| Steering Modifier 2 | `Steering \| L1!R1: Modifier 2`, `Steering \| R1!L1: Modifier 2` | `R1: Tap Cover`, `L1: Tap Cover` | 200 / 250 | the same |
| Fn | `Menu Left: Entry Point`, `Menu Right: Entry Point`, their `Stateful \|` copies | `Menu Left: Fn Layer`, `Menu Right: Fn Layer` | 200 / 250 | the same |
| Menu stick guards | `Menu Buttons: Left Stick Guard`, `Menu Buttons: Right Stick Guard` (Select and Start in each) | `Menu Buttons: Tap Cover` | 200 / 250 | the same |
| Second-press layers | `L1: Scroll Down`, `R1: Scroll Up`, `Menu Left: Escape`, `Menu Right: Tab`, `Menu Left!Right: Enter`, `Menu Right!Left: Backspace` | their Double Tap Cover | 150 / 200 | the same |
| Touches | `LST: Entry Point`, `RST: Entry Point`, `RTP: Entry Point` | their Tap Cover | 150 / 200 | the same |
| Turning | `Turning Ramp Up 0` (a Soft Press) | `Turning Ramp Up 1` | 250 / 300 | untouched |
| Pad clicks, outer bind | `RTP: Click Entry Point`, `LTP: Click Entry Point` | `RTP: Mouse Buttons`, `LTP: Arrow Keys` | 5 / no reset | 5 / 55, on the touch |

The other delayed activators add no layer, have no reset and keep their time:
5 ms on `Gyro Off Ramp Up` and three in the Steering left-stick layers; 50 ms
on the six Double Tap window outputs; 150 or 200 ms on the eleven windows' own
timers; 150 ms on the two scroll repeats in `RTP: Mouse Buttons`; 1500 ms on
the two in `Steering | LS: Fallback Hold`.

## The pads

### The Click Entry Points' reset

The outer ring bind waits 5 ms, which gives the inner one priority where the
two ranges overlap. It had no reset. Now the pad's touch has one, beside its
Release (the author: "you can put it on the touch bind it doesn't need to be
on the edge"):

| Layer | Touch, new entry |
|---|---|
| `RTP: Click Entry Point` | Regular Press, removes only `RTP: Mouse Buttons`, Hold to Repeat every 55 ms, Interruptable off, no haptic |
| `LTP: Click Entry Point` | The same, removing only `LTP: Arrow Keys` |

On the simulator it fires once, as the layer lands on the thumb, on a layer
that isn't there. The outer bind fires 5 ms later and removes the Click Entry
Point, so the reset never repeats
([scenario P2](../../tests/test_scenarios_90_26.py)). The Click Entry Point
doesn't come back while the outer layer is on, so the reset can't remove a
layer in use.

### The touch layers' ring

In 90.25 the touch layers had the Click Entry Point's two ring binds, the 5 ms
delay included. There both binds do the same thing, remove the touch layer and
add the pad's Entry Point, and only the inner one bumps; the delay decided the
bump where the ranges overlapped. Now the outer bind starts at the inner one's
threshold, 24996, with no delay: exactly one of the two is active wherever the
thumb lands.

| Thumb | Touch | Click |
|---|---|---|
| Inside 23000 | Bump | Centre click |
| 23000 to 24996 | Bump | Centre click: the inner bind has priority |
| Outside 24996 | No bump | Outer buttons, 5 ms later |

The bump is where a click is the centre click, as before. A touch at the rim
hands over as the thumb lands, where it took 5 ms. No delayed add is left in
these layers, so they need no reset.

The simulator's `press_between`, a thumb between 23000 and 24996, now leaves
out a normal Soft Press whose threshold is at or past the inverted one's.

## What the margin does

All of this is the simulator. It rests on A13 (any removal restarts a start
delay that is counting), the author's report.

A hold that nothing disturbs lands at its delay, and its reset never repeats.
A removal from outside, later than the margin into the hold, pushes the add
past the reset's first repeat. The reset then restarts it (A12), and it lands
one delay after the reset: **delay + margin + delay**, 450 ms for a 200 ms
hold. Inside the margin the removal costs only its own time.

The removals that reach a hold are the pads'. Every hold layer binds both
stick touches and none binds a pad. Since 90.25 a pad touch removes its touch
layer, and `RTP: Entry Point` has a reset of its own.

A pad touch 10 to 190 ms into the hold, or the hold 10 to 190 ms after the
touch. Times are from the hold's press:

| Hold | 90.24 | 90.25 | 90.26 |
|---|---|---|---|
| Modifier 0, then a left pad touch | 300 | 310 to 650 | 210 to 450 |
| Fn or Modifier 2, then a left pad touch | 200 | 210 to 450 | 210 to 450 |
| Modifier 0, then a right pad touch | 300 | 310 to 650 | 210 to 950 |
| Fn or Modifier 2, then a right pad touch | 200 | 210 to 950 | 210 to 950 |
| A right pad touch, then Modifier 0 | 300 | 300 to 650 | 200 to 700 |
| A right pad touch, then Fn or Modifier 2 | 200 | 200 to 700 | 200 to 700 |
| A left pad touch, then any hold | as alone | as alone | 200 |
| Steering Modifier 0, then a left pad touch | 250 | 260 to 550 | 210 to 450 |
| Steering Modifier 2, then a left pad touch | 200 | 210 to 450 | 210 to 450 |
| Either Steering modifier and the right pad | as alone | as alone | 200 |

The right pad's range is its reset and the hold's reset restarting each other:
the pad's ticks every 200 ms until `RTP: Tap Cover` lands, the hold's every
250 ms, and each layer needs a gap as long as its delay. The simulator counts
a reset's repeat that removes nothing as a removal like any other. If Steam
doesn't, every "hold first" row is 210 to 450 and every "touch first" row is
200 ([scenario D3](../../tests/test_scenarios_90_26.py) pins the simulator's
reading).

### Three margins, with every hold at 200 ms

The same gestures on a copy of the layout with only the reset rates changed:

| Reset repeats at | Hold, then a left pad touch | Hold, then a right pad touch | A right pad touch, then the hold |
|---|---|---|---|
| delay + 50 (built) | 210 to 450 | 210 to 950 | 200 to 700 |
| delay + 5 (the first build) | 405 | 405 to 1020 | 200 to 815 |
| twice the delay + 5 | 210 to 390 | 210 to 390 | 200 |

- **+ 5** shortened the second lap by 45 ms and made every touch after the
  first 5 ms pay for it. It also needed Steam to run a delayed add before a
  reset due 5 ms later, which nobody has checked. The author took it back.
- **Twice the delay + 5** never meets a hold that one removal restarted. What
  it gives up is the recovery the reset is there for: a delay that is stuck
  (A12) is restarted at 405 ms, not at 250. Not built.

## Left to the author

- [ ] One R139 entry in the exceptions register, written while building: the
  right pad's ring under nine layers, read because their hold delay or
  `RTP: Click Entry Point`'s touch changed (`steam_layout/flow_config.json`,
  "90.26 build").

## Not verified

- A40 now also carries the touch layers: a normal Soft Press at 24996 has to
  read the way the one at 23000 does. If it doesn't, a touch near the rim
  stays in the touch layer until the thumb lifts, and the pad does nothing.
- A12, A13 and A46 as before. [The list](unverified-assumptions.txt).

## On the Deck, in this order

1. **The touch layers.** Touch each pad in the centre, about three quarters
   of the way out, and at the rim, ten times each. A light bump in the first
   two, none at the rim, and the cursor or the swipes work after every touch.
2. **The clicks.** Click each pad in the same three places: centre click,
   centre click, outer button. Hold an outer click for a second: the button
   stays down.
3. **The holds.** Hold L1, then Select, then L1 and R1: the pulse at 200 ms.
4. **A pad touch during a hold.** Hold L1 and drop a thumb on the left pad,
   then on the right. A cursor at about 450 ms means A13 holds for the touch
   layer's removal. Close to a second, on the right pad only, means a reset's
   repeat that removes nothing restarts other delays too.
5. Then [90.25's order](../2026-10-04-pad-bumps-and-menu-keys/README.md#on-the-deck-in-this-order).

## Code changed outside the builder

| File | Change |
|---|---|
| `steam_layout/simulator.py` | `press_between` leaves out a normal Soft Press whose threshold is at or past the inverted one's |
| `steam_layout/flow_config.json` | One R139 entry |
| `tests/` | `test_standard_delays.py` and `test_scenarios_90_26.py` are new. The cursor and 90.25 tests have the new times; R156's test moved to the new build's |

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder: `standardize`, `click_resets` and `touch_rings` after the 90.25 build |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-delays-changed.txt` | The eight holds and the four pad layers, before and after |
| `*-changes.txt` | The change report against 90.25 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
