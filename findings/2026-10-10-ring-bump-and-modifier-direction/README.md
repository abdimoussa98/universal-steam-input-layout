# The ring's bump and the stick modifiers' own direction (90.51)

Built on 2026-10-10 from the 90.50 snapshot, both layouts, on the author's
go-ahead ("go ahead and build this as one"). No layer is added or removed.
Nothing here has run on the Deck. The reasons are in the
[investigation](../2026-10-10-pad-ring-bump-and-stick-tap/README.md) and the
[plan](../../plans/2026-10-10-pad-ring-bump-and-stick-tap.md).

## What changed

Four layers and six changes per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

| Layer | Input | 90.50 | 90.51 |
|---|---|---|---|
| `LTP: Arrow Keys`, `RTP: Mouse Buttons` | The pad's Haptic Intensity Override | Off (`0`) | Use Activator Settings (`5`) |
| The same two | The ring's empty block | No haptic stated | Off |
| `Steering \| LS Up: Modifier 1` | Up | A cleanup function, the hold marker's reset, the 200 ms add of the hold marker | The reset and the 200 ms add |
| `Steering \| LS Down: Modifier 0` | Down | The same | The same |

The **hold marker** is `Steering | LS: Tap Cover`. The cleanup function that
came off removed the modifier, the hold marker and both drivers' layers.

## Why

- **The ring.** At Off the pad silences its binds, which 90.50 had set to Low
  (A57, read from the Steam client). On 90.50 the centre bumped once and the
  ring not at all.
- **The stick modifiers.** On 90.50 a deflect scrolled once and then not
  again. W stayed held, pressing the driver again did not help, and a deflect
  to the rim could leave `Steering` with the driver held (author,
  2026-10-10). The cleanup's only guard was the 200 ms chord. If Steam lets
  the cleanup fire before that chord has fired (A58), each deflect removes the
  modifier and the driver's layer as the modifier lands. This is a suspect,
  not a diagnosis: it does not explain why the first deflect worked. The
  author chose to take the cleanup off and test.

## The exception

Without the cleanup the two modifiers hide the cleanup function the W and S
layers have on up and down, which R130 forbids. The register has two R130
entries, status todo, ended by the to-do "normalize the stick cleanup
functions of the Steering stateful layers". R130 had no exception form before:
`steam_layout/exceptions.py`, `cleanups.py` and the `cleanup_lists` fix now
read one (`cleanups.hidden`).

**The cost.** 90.43 added the cleanup for a driver release missed in the Steam
menu with the stick still held in that direction. That case is now left to the
layer's other cleanup functions: in scenario S2 the stick comes back and the
next button clears the modifier and the driver's layer.

## Not built

The thumb that leaves the stick first (part 2 of the plan) and anything for
`Steering | LS: Double Tap Cover`, whose up and down keep a cleanup beside a
5 ms chord.

## Validation

- The fix pipeline changed nothing. The four audits pass on both layouts,
  against the 90.50 baseline and as installed.
- `tests/test_scenarios_90_51.py`: four deflects in one driver hold scroll
  once each (S1), the missed release (S2), a ring click's output (C1) and two
  static checks. `test_scenarios_90_49.py` expects the override `5`.
- 323 scenarios; 89 of 89 layers are on the stack in a scenario in each
  layout, and no changed layer is uncovered.
  [unverified-assumptions.txt](unverified-assumptions.txt) lists what rests on
  an unverified assumption.
- The simulator scrolled on every deflect before this change too. It cannot
  show that the fix works. Only the Deck can.
- Both VDFs exported with key, value and order verification. The four files
  are in `versions/neptune/90.51/`. The descriptions were read and kept.

## Deck result, 2026-10-10

The deflect still scrolls only once (author). The cleanup on the modifiers'
own direction was not the cause. The ring bumps once a click. A pad click is
interrupted when a thumb leaves a stick
([what the files show](../2026-10-10-pad-click-after-stick-tap/README.md)). The follow-up
is [a plan](../../plans/2026-10-10-stick-lifecycle-and-pad-click-after-stick-tap.md)
to rebuild the stick's sequence on the bumper lifecycle.

## On the Deck

| Check | Expect | If not |
|---|---|---|
| Hold a driver in `Steering`, thumb on the stick. Deflect up four times, then down four times | One wheel step each. `Steering` stays | Once only: the suspect is ruled out, and the cleanup can go back |
| The same, to the rim | The same | `Steering` ends: something else uncovers its exit |
| Hold up past 200 ms and let go | No scroll | |
| Click both pads at the centre and on the four sides of the ring, slowly and fast | One bump a click | None on fast ring clicks: the layer lands after the click (A56) |
| Hold a ring click. Hold up or down on the right ring | No further bump | |
