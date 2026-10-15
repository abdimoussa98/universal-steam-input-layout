# The pad click layers on touch, the bump on the final click (90.71)

Built on 2026-10-14 from the **90.70** snapshot, both layouts, on the
author's word after comparing 90.70 with the old layout
(`findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json`):
"We are good to start building". [Plan](../../plans/2026-10-14-pad-click-touch-layers.md).
90 layers in each layout. Device status: **untested**.

| | Default | Alternative |
|---|---|---|
| Layers changed | 6 | 6 |
| Changes | 19 | 19 |
| Removes, 90.70 to 90.71 | 2,885 to 2,891 | 2,943 to 2,949 |
| Adds | unchanged | unchanged |
| `hold_layer` | 4, unchanged | 4, unchanged |

Removes: ten Releases in (four directions and the centre, on two D-pad
layers), four inverted repeating removals out.

## Terms

- **Click Entry Point:** `LTP: Click Entry Point`, `RTP: Click Entry Point`.
- **D-pad layers:** `LTP: Arrow Keys`, `RTP: Mouse Buttons`.
- **Middle Click layers:** `LTP: Middle Click`, `RTP: Middle Click`.
- **Final layers:** the D-pad layers and the Middle Click layers.
- **Adders:** the binds that add a Click Entry Point on a pad click:
  `Base` on both pads and `RTP: Circular Scroll`.
- **Haptic levels:** 0 Off, 1 Low, 2 Medium, 3 High. A D-pad group's
  override 0 silences its binds; 5 is "Activator Pref" (read from the
  Steam client's settings UI, 2026-10-14).

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.70.

| Layer | Input | 90.70 | 90.71 |
|---|---|---|---|
| Adders | click | Soft Press adds the Click Entry Point, haptic 0, once | The same, with Hold to Repeat every 50 ms |
| Click Entry Points | all | | Unchanged: silent, the two hand-overs, the 55 ms touch reset for the delayed ring hand-over |
| D-pad layers | settings | `requires_click` not set: click required (author, confirmed in the configurator) | `requires_click "0"` |
| D-pad layers | four directions | Full Press, haptic 1 | Full Press, haptic 0; Release removes the layer, haptic 0 |
| `RTP: Mouse Buttons` | up, down | Full Press haptic 1; chord repeat haptic 0 | Full Press haptic 0; chord repeat haptic 1; Release removes the layer |
| D-pad layers | edge (centre) | `empty_binding` | `empty_binding`; Release removes the layer, haptic 0 |
| D-pad layers | click | `hold_layer` self, haptic 0; inverted repeating removal | `hold_layer` self, **haptic 3**, not interruptible; the removal deleted |
| Middle Click layers | click | Full Press output, haptic 1; `hold_layer` self, haptic 0; inverted repeating removal | Soft Press output, haptic 0, not interruptible; `hold_layer` self, **haptic 3**, not interruptible; the removal deleted |
| Final layers | touch Release | | Unchanged |

`Up` and `Down` in `RTP: Mouse Buttons` have three entries, the R109 maximum.
The adders' repeat rate was not set by the author: 50 ms, as 90.16's
repeating add and the entry points' hand-overs.

What it reverses: 90.20's single add on `Base` (the repeat is silent now,
so it only re-enters), the note that the pad layers move only on Soft
Presses and the touch Release, and the inverted repeating removal of 90.19
to 90.70. The R101 exception keeps the four self-holds.

## On the simulator

[`tests/test_scenarios_90_71.py`](../../tests/test_scenarios_90_71.py),
both layouts, both pads. The D-pad layout is Radial Without Overlap
(`layout` 0, from the client's settings UI), so a slide on the ring lets the
old direction go before the new one presses.

| Scenario | Shows |
|---|---|
| P1 | A click on a direction: the entry point, 5 ms later the D-pad layer, the output once, no bump |
| P2 | A ring slide with the click held: the Release takes the layer off, the adder's repeat puts the entry point back at once (A6, A9), 5 ms later the D-pad layer and the new output once. Base's swipes don't run in the gap |
| P3 | The click let go with the thumb resting: the layer stays (A5) and nothing is sent; lifting ends it |
| P4 | A slide through the centre with the click held hands over to Middle Click and sends its output: Caps Lock on the left pad, middle mouse on the right. The layer then stays until the thumb lifts |
| P5 | A centre click: the middle output once; the layer stays until the thumb lifts |
| P6 | A held scroll: the first step silent, the repeats bump Low |
| P7 | A click release the layout never sees (A25): at the centre the layer stays until the thumb lifts; off a direction its Release takes it off, unless the exposed add re-enters (A9) |
| P8 | The touch Release before the click's: if the exposed add fires (A9), Middle Click lands with no thumb on the pad, sends its output (from a direction) and stays; the next touch and lift take it off |
| P9 | A modifier and a click leave each other alone, either first |
| P10 | A click in `Steering` ends on the lift; `Steering` stays |
| P11 | A click in Circular Scroll is Middle Click, and stays Middle Click until the thumb lifts: in 90.70 the click's release went back to scrolling |

P2 runs both ways on A9. If Steam does not fire the exposed add, a slide
waits for the add's next repeat (50 ms); on the left pad Base's swipe of the
new direction runs first (a slide up types Tab).

No scenario bumps High. The final layer always lands on a click that is
held, and on the simulator a binding that lands on a held input runs its
outputs but not its layer commands (A5), and not its haptic. Whether Steam
bumps there is the first Deck check.

Compared with 90.70 on the same gestures:

- A slide through the centre, clicked, sent nothing in 90.70; now it sends
  Caps Lock or middle mouse (P4).
- The click let go with the thumb resting on the left pad: 90.70 removed
  the layer and Base's swipe under the thumb added `Escape` and typed it;
  90.71 keeps the layer until the thumb moves (P3).
- After that, moving the thumb unclicked leaves the layer on the
  direction's Release, and Base's swipe of the new direction runs, as a
  swipe on `Base` does.

## The author's decisions, 2026-10-14

- **A stuck final layer is accepted.** The final layer leaves by its
  self-hold when the click lets go. If it is stuck (the hold didn't run, a
  release was missed, the touch Release came first), the touch Release
  takes it off, and on a D-pad layer touching a direction sends it and the
  direction's Release takes the layer off. No inverted removal comes back.
- **A clicked pad isn't slid** ("that release would never fire unless that
  layer is stuck"): the direction Releases are the stuck layer's way out,
  and the repeating add stays. P2 and P4 record what a slide would do.

## Tests changed

Pinned to the 90.70 build with `frozen="90.70"` (their behaviour is 90.70's;
the 90.71 counterparts are P3, P7 to P11): 90.14 P4, P8, P10, P11, P12;
90.16 X1, X2; 90.17 S2, S3; 90.18 H2, H4; 90.19 K1 to K3. The shape checks
of 90.49 (the bump on the final outputs) and 90.51 (the ring pads' haptics)
read the 90.70 build. 90.50 C1 allows the held scroll's Low bumps. The
hygiene test of the scroll inputs expects the Release and the Low repeat;
the held-input test no longer expects an inverted exit in the D-pad layers.
90.70's shape test no longer compares with the installed layout.

## Audits and tests

- Build audit on both candidates, against the 90.70 snapshot: clean.
- The fix pipeline changed nothing.
- Scenarios P1 to P11 and the shape checks pass, both ways on A9.
- Build audit on the installed layouts: clean.
- The full suite: 1,315 tests pass (25 expected failures, as before).
- Every layer is on the stack in a scenario; none changed without one (R165).
  [Unverified assumptions](unverified-assumptions.txt) written.
- Snapshot: `versions/neptune/90.71/`, JSON and VDF, both layouts.

## On the Deck

1. Click a pad on a direction: is there a High bump? If not, Steam skips the
   `hold_layer` on a held click (A5) and the click is silent.
2. Let go of the click with the thumb resting: does the layer stay (the arrow
   stays down, or nothing is sent) until the thumb moves?
3. Slide along the ring with the click held: one output per direction.
4. Slide through the centre with the click held: Caps Lock (left) or middle
   mouse (right) is sent.
5. Hold right-pad up: Low bumps on the repeating scroll.
6. In Circular Scroll, click and let go with the thumb down: back to
   scrolling (the hold ran) or still Middle Click until the lift (A5).
