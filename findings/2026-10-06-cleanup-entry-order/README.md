# One order for the entries of a cleanup input (90.36)

**Status:** built and installed as 90.36 on 2026-10-06. Not run on the Deck.
Build audit clean. Extends the
[90.35 builder](../2026-10-06-steering-fallback-swap/README.md), which stays
frozen. 88 layers. It follows the
[audit of the menu Entry Points](../2026-10-06-menu-entry-point-stick-touches/README.md).

- **Cleanup function:** a repeating, interruptible Regular Press that only
  removes layers. It is for a release that was missed.
- **Guard:** a chord on the same input that holds the cleanup function back
  while the layer's button is held.
- **Cleanup input:** an input that has a cleanup function. 523 in the default
  layout and 549 in the alternative.
- **Stored order:** the order of an input's entries in the file, which is the
  order the Steam editor lists them in.

## Why

The author, 2026-10-06: "when I'm touching a stick, and I'm holding the menu
button ... on the first load of the layout, when I booted in, the menu FN
layer wasn't applying, like the delayed action was never applying. So my
suspicion is that the regular press actually isn't being interrupted. And that
the release needs to go last ... the order: repeated removal of a regular
press, then the guard, then a release. That's how it should always be."

Since 90.24 the stick touches of the four menu Entry Points had the Release
stored between the cleanup function and its guard. If Steam then does not let
the guard interrupt the Regular Press, the Entry Point is removed as often as
it is added while a thumb is on a stick, and its 200 ms Fn delay never ends.

## What changed

One thing: on every cleanup input the entries are stored as **Regular Press,
guard, Release**. No bind, setting or command changes.

121 inputs in each layout had another order:

| Was stored as | Inputs | Where |
|---|---|---|
| Regular Press, Release, guard | 8 | Both stick touches of the four menu Entry Points |
| Release, Regular Press, guard | 4 | Both stick touches of `L1: Scroll Down` and `R1: Scroll Up` |
| guard, Regular Press | 109 | Stick edges and clicks, face buttons, D-pad, bumpers and menu buttons in 27 layers: the eight modifier layers, the menu Entry Points and Fn layers, the Steering modifiers, the Temp Cursor Gyro and Scroll layers, and `RTP: Entry Point` |

The other 402 inputs (428 in the alternative) already had it.

The exported VDF has the same order: checked on the Entry Points' left-stick
touch in both layouts.

## What is not known

- **Whether the order matters to Steam.** The simulator does not read it, so
  no test can show a difference in behaviour. This release is the experiment
  (A52).
- **The 109 "guard first" inputs worked.** They include the bind for the other
  bumper in the eight modifier layers. They are reordered because the author
  asked for one order everywhere; if a modifier behaves differently on the
  Deck, look there first.

## How it is built

[build_candidate.py](build_candidate.py) puts one class in front of the 90.35
builder's. Its `finish` takes every input the Cleanup audit reads as having a
cleanup function and stores its three entry types in the order above. It stops
if such an input has a fourth type.

## Rules and assumptions

| What | Change |
|---|---|
| R133 | The cleanup function's shape now includes its stored order |
| A52, new | The author's suspicion: a Release stored between a Regular Press and its guard stops the guard from interrupting it |
| R156 | The working layouts are this builder's output |

## Tests

- `tests/test_layout_rules.py`, one new test on the working layouts: every
  cleanup input is Regular Press, guard, Release. A later build that breaks
  the order fails it.
- `tests/test_cleanup_entry_order.py`: the order on the build; the Entry
  Points and the Scroll layers; 121 inputs move and nothing else differs from
  90.35; the working layouts equal the build, order included.
- No scenarios: the simulator does not read the stored order.

## On the Deck

1. Load the layout fresh. Rest a thumb on a stick, hold Select for a second:
   the Fn beep at 200 ms. The same with Start, and with the other stick.
2. Hold Select, put a thumb on a stick, keep holding: the beep at 200 ms.
3. The modifiers as usual: tap, hold, and both bumpers.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-binds-changed.txt` | The counts by old order |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.35 (R164): the 121 inputs, before and after |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
