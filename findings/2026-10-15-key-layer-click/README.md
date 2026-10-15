# The left pad's click in the key layers (90.73)

Built on 2026-10-15 from the **90.72** snapshot, both layouts, on the author's
word: "now go ahead and build these" ([plan](../../plans/2026-10-14-key-layer-click-and-fn-right-stick.md), part 1).
90 layers in each layout. Device status: **untested**.

| | Default | Alternative |
|---|---|---|
| Layers changed | 4 | 4 |
| Removes, 90.72 to 90.73 | 2,961 to 2,965 | 3,019 to 3,023 |
| Adds | 469, unchanged | 469, unchanged |

## Why

The author, 2026-10-14: after a swipe into `Escape`, `Tab`, `Backspace` or
`Enter`, "the click is not behaving the same way as from base. Click should
remove the layer you are in and it should be a repeated silent soft press then
by default you'll be going through the base left pad click."

In each key layer the left pad is a single-button group: the touch types the
key and its Release removes the layer. The click was not bound, and the group
replaces the whole pad, so a click there did nothing.

## The change

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against 90.72.

| Layer | Input | 90.72 | 90.73 |
|---|---|---|---|
| `Escape`, `Tab`, `Backspace`, `Enter` | left pad click | not bound | Soft Press that removes the layer itself: `haptic_intensity` 0, Hold to Repeat every 50 ms, `interruptable` 0 |

The settings are Base's click settings, with one addition: `interruptable` 0,
which the plan did not have. The Soft Press is the only entry on the click, so
nothing can interrupt it and it behaves the same either way. Left interruptible,
the tools read it as a cleanup function, which has to carry the layer's guard
chord (the fix pipeline stopped on "guard mismatch"). Not interruptible, they
read it as the layer's own exit, as they read the 90.71 final clicks.

## On the simulator

A swipe, then a click: the key layer comes off, Base's repeating click fires on
the held click (R114, both ways of A9) and adds `LTP: Click Entry Point`. At the
ring that is `LTP: Arrow Keys`, which types the direction's arrow; back at the
centre it is `LTP: Middle Click`. A swipe and a lift without a click are
unchanged. These are in `tests/test_scenarios_90_73.py`.

One older record changed (`90.71 P2`). It covers sliding round the ring with the
click held, a gesture the author doesn't make. With A9 false, on the left pad
the slide used to land in `Tab` and type Tab. It now lands in `LTP: Arrow Keys`
and types Up Arrow, as the right pad already did.

## Audits and tests

- Build audit: clean on both layouts.
- Full suite on 90.73: 1,330 tests, three failures. The snapshot lineage check
  passes once the snapshot is saved. The 90.72 check that the installed layout
  is that build now checks that build against its snapshot. `90.71 P2` is
  above. After those changes, the suite on 90.74 passes: 1,333 tests, 25
  expected failures.
- Scenario coverage: every layer is on the stack in a scenario; none changed is
  missing (R165). The assumptions not verified are in
  [unverified-assumptions.txt](unverified-assumptions.txt).

## On the Deck

1. Swipe right, then click at the ring: Return once, then Right Arrow; the only
   bump is the Arrow Keys self-hold (High).
2. Swipe up, slide back to the centre, click: Tab, then the Middle Click output.
3. Swipe and lift without a click: the key once, and back to Base.
