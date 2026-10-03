# The Click Entry Point hands over (90.18)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.18**, with the
snapshot in `versions/neptune/90.18/`. Played on the Deck: it works as intended,
but the haptics repeat while a click is held. [90.19](../2026-10-03-pad-click-holds/README.md)
swapped the hand-over's order and gave the final layers a hold. Device status: **untested**. The build
audit is clean and the tests pass.

## The changes (author, 2026-10-03)

| Layer | Pad input | 90.17 | 90.18 |
|---|---|---|---|
| Click Entry Point | edge, centre | Soft Press adds the Middle Click layer | Removes the Click Entry Point, then adds the Middle Click layer |
| | edge, outer | Soft Press adds the D-pad layer | Removes the Click Entry Point, then adds the D-pad layer |
| | click | Inverted, repeating Soft Press removes the Click Entry Point | Not bound |

The Soft Presses keep their settings: both repeat every 50 ms, both are
uninterruptible, no haptics, and the outer one has its 5 ms delay.

So the Click Entry Point is on from the press until one of the two fires, and
never under the layer it chose. The stack during a click is `Base`, then the
Click Entry Point alone, then the chosen layer alone.

Two things follow, and are done here:

- **The chosen layers no longer name the Click Entry Point.** Their Soft Press
  exit, their touch Release and their stick-touch cleanup removed it first.
  It can't be on the stack with them now, so those removals are gone (R132).
- **Base doesn't bring it back under a chosen layer.** Base's repeating add is
  on the pad's click, and a D-pad or single-button pad on top blocks Base's
  mouse-mode click (a different pad mode). Scenario H1 holds a click for a
  second and the entry point stays away.

Six layers and 20 bindings changed per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

## What ends the Click Entry Point now

It binds no click, so letting go of the pad doesn't end it. Three things do:

1. A hand-over: the outer Soft Press 5 ms after it lands, or the centre one on
   its 50 ms repeat.
2. The thumb lifting off the pad (the touch Release).
3. The stick-touch cleanup, when a stick is touched with no thumb on the pad.

## What to know about a very short click

A click that ends before the hand-over (5 ms at the rim, 50 ms at the centre)
leaves the Click Entry Point on with the pad no longer pressed. On the
simulator:

- **Thumb still on the pad** (scenario H2). The Soft Press hands over anyway,
  because it only reads where the thumb is. The chosen layer lands on a pad
  that isn't pressed and its own Soft Press exit removes it on its next
  repeat. Nothing is sent. For that short time the pad is a D-pad or a single
  button, not the mouse.
- **Thumb lifts** (scenario H3). The touch Release removes it.
- **The touch Release is seen before the click lets go** (scenario H4). The
  touch Release removes it, Base adds it again under the click that still
  reads as pressed, and then nothing is touching the pad. What ends it is the
  centre Soft Press handing over with no thumb there. That needs an inverted
  Soft Press to count as true on an untouched pad, which is part of A40 and
  not known. If it doesn't, the Click Entry Point stays on until the pad is
  touched again; the next touch hands over and clears it.

Until 90.17 the removed Soft Press exit on the click covered all three cases.

## Scenarios and tests

- `tests/test_scenarios_90_18.py`, H1 to H4: the entry point is gone once the
  chosen layer is on, on both pads; a click that ends before the hand-over;
  the thumb lifting; a touch Release seen before the click lets go.
- The 90.14, 90.16 and 90.17 scenarios that expected the Click Entry Point
  under the chosen layer now expect the chosen layer alone.
- `tests/test_pad_click_handoff.py`: the bindings above, on the generated
  candidates.

## Files

- `build_candidate.py`: the builder. It extends the 10-03 Soft Press only
  builder, which stays frozen.
- `install_neptune.py`, `*-pad-click-handoff.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.17 (R164).
- `unverified-assumptions.txt`: 22 assumptions that aren't verified; 63 of the
  114 scenarios rest on one (R167).
