# The pad touch bump comes out (90.27)

**Status:** built and installed as 90.27 on 2026-10-04. Not run on the Deck.
Build audit clean; the tests pass.

The author, 2026-10-04: "I don't like the new trackpad changes. To include
that bump." How the bump was built is kept in
[the record](../2026-10-04-pad-touch-bump/README.md), in case it comes back.

## What it changes

The pads go back to how they were in 90.24. Three layers are gone: 87, not 90.

| | 90.26 | 90.27 |
|---|---|---|
| Base, right pad | Mouse. Touch adds `RTP: Touch Entry Point`. No click | Mouse. Touch adds `RTP: Entry Point`. Click adds `RTP: Click Entry Point` |
| Base, left pad | D-pad. Touch adds `LTP: Touch Entry Point`. No swipes, no click | Swipe pad. The four swipes add `Escape`, `Enter`, `Tab`, `Backspace`. Click adds `LTP: Click Entry Point`. Nothing on touch |
| `RTP: Entry Point` | Has the click's add, repeating | No click |
| `Steering` | Its own copy of the click's add | Base's click, through the cleared touch |
| `LTP: Click Entry Point`, `LTP: Middle Click`, `LTP: Arrow Keys` | Also remove `LTP: Entry Point` | As in 90.24 |
| `RTP: Touch Entry Point`, `LTP: Touch Entry Point`, `LTP: Entry Point` | The bump's layers | Gone |

The clicks in Base are 90.24's: a Soft Press with the strong pulse and no
repeat.

Sixteen layers differ from 90.26
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)): the six
above, and ten whose clear lists named the three layers. The nine menu layers
that came after the three in the layer list move up three places; the build
renumbers every reference.

## What stays

Against 90.24 the pad bindings differ in three places only, each a separate
decision:

- `RTP: Middle Click` is a mouse pad, so the cursor moves while middle mouse
  is held (90.25).
- `RTP: Entry Point`'s touch has the Tap Cover reset, as the two stick Entry
  Points have (90.25).
- The two Click Entry Points' touch has the reset for the 5 ms outer ring
  bind (90.26).

Also unchanged: the 200 ms hold delays with resets at their delay + 50 ms, the
chorded menu chains and `Menu Keys`.

## What it does to a hold

A pad touch during a hold that is still counting, or the hold just after the
touch, on the simulator. Times are from the hold's press, for a 200 ms hold:

| | 90.26 | 90.27 |
|---|---|---|
| Hold, then a left-pad touch | 210 to 450 | 200 |
| A left-pad touch, then the hold | 200 | 200 |
| Hold, then a right-pad touch | 210 to 950 | 210 to 950, or 200 |
| A right-pad touch, then the hold | 200 to 700 | 200 to 700, or 200 |

Base's left pad binds no touch, so nothing happens under the hold. On the
right pad the touch layer's removal is gone, and what is left is the Tap Cover
reset on `RTP: Entry Point`: it fires as the layer lands on the thumb (A6) and
every 200 ms until the cover lands. It removes a layer that isn't on. If such
a removal restarts other delays, as the simulator has it, the first numbers
hold; if it doesn't, the hold lands at 200 ms. That reset is the author's
request of 2026-10-04 and stays for the Deck to judge (A48).

## A click still held when its layers are cleared

Base has the click's add again. If the click layers go while the click is
still down (the thumb's touch Release seen first, or a clear), Base's add is
exposed under the held click. If Steam fires an exposed bind (A9), the Click
Entry Point lands on the held click and its centre bind, which repeats, fires
at once (A6): the centre click comes straight back until the click lets go.
If it doesn't, nothing comes back. Scenarios 90.16 X1 to X3 and 90.18 H4 run
both ways. In 90.24 the tests showed nothing coming back at once; that was the
simulator's old reading of A6, not a different layout.

## How it is built

[build_candidate.py](build_candidate.py) puts a class in front of the 90.25
builder's. It answers that builder's two pad steps (`build_right_pad`,
`build_left_pad`) with nothing and leaves the three titles out of its list of
new layers. Then it runs the two steps of the 90.26 builder that don't belong
to the bump: `standardize` (the hold delays and reset rates) and
`click_resets`. 90.26's third step, `touch_rings`, changed the touch layers
and is not run. The 90.25 and 90.26 builders stay frozen.

## Rules, register and assumptions

| What | Change |
|---|---|
| R156 | The working layouts are this builder's output; `test_pad_bump_removal.test_working_layouts_are_this_build` |
| R139 | Seven entries removed from the exceptions register. Six were written for 90.25 and one for 90.26, all because the click's add sat in the pad's Entry Point and in `Steering`: the three bump layers; the right-pad click under fifteen layers; the pad click layers over Steering's layers; the pad touch under Steering's layers; the right pad's ring (two entries); the right stick's directions in `Menu Buttons: Left Stick Guard`. With Base's click back the Flow audit has no finding for any of them, against 90.26 or on its own |
| R139 and R136, the menu chains | The two R139 and two R136 entries of 90.25 for the chorded menu layers stay |
| A46 | Nothing rests on it now. It is the first thing to check if the bump comes back |
| A47 | Nothing rests on it now: Base's left pad binds no touch |
| A40 | Back to the Click Entry Points' two ranges alone |

## Tests

- `tests/test_pad_bump_removal.py`: the three layers are gone and the order of
  the rest is kept; every layer's pad bindings equal 90.24's but for the three
  later changes; Base's clicks, swipes and touch; no copy of the click
  elsewhere; what stays; against 90.26 only the pad layers and the clear lists
  change.
- `tests/test_scenarios_90_27.py`, B1 to B4: no bump and the Entry Point at
  once; the clicks from Base with one pulse; a swipe with no layer under it;
  Steering and the Tap Cover using Base's click.
- The bump's scenarios are out: 90.25 P1, P2, P4 and P6, and 90.26 P1. 90.26
  D1 is now the left pad costing a hold nothing.
- The older pad click scenarios (90.14, 90.16, 90.17, 90.18) are back to
  Base's click. 90.16 X1 and X2 and 90.18 H4 now run both ways under A9.

## On the Deck

1. Touch and click each pad in the centre and at the rim; swipe the left pad.
   No bump on touch, the strong pulse on a click, the same keys as before
   90.25.
2. Hold L1, then drop a thumb on the right pad. A cursor that comes late,
   up to about a second, means the Tap Cover reset on `RTP: Entry Point`
   restarts other delays, and it should come off.
3. Then [90.26's order](../2026-10-04-standard-delays/README.md#on-the-deck-in-this-order)
   without its first step.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-delays-changed.txt` | The eight holds and the two click resets, before and after |
| `*-changes.txt` | The change report against 90.26 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
