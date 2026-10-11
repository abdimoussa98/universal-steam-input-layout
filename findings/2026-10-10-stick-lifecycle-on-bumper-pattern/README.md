# The Steering stick deflect on the bumper lifecycle (90.52)

Built on 2026-10-10 from the 90.51 snapshot, both layouts, on the author's
"implement the plan"
([plan](../../plans/2026-10-10-stick-lifecycle-and-pad-click-after-stick-tap.md),
part 1). Two layers are added: 90 in each layout. Nothing here has run on the
Deck. Part 2 of the plan, the held pad click that drops when a thumb leaves a
stick, is not built: it waits for the Deck trial T1 to T4.

## Why

On 90.51 a stick deflect in `Steering` still scrolled once and then not again
(author). The cause is not known: the press simulator scrolls on every deflect
on 90.50, 90.51 and 90.52. The author asked for the stick's sequence to follow
the L1 and R1 modifier lifecycle as closely as it can. This build removes
every difference the plan lists.

## The sequence now

Up with a driver held. Down mirrors it.

| Step | Layer | On up |
|---|---|---|
| 1. Entry | The W or S layer | Unchanged: a cleanup function, and a chord on the driver that adds `Steering \| LS Up: Modifier 1` |
| 2. Timer | `Steering \| LS Up: Modifier 1` | The reset. A chord on the left stick's deflect, 200 ms: add `Steering \| LS: Tap Cover` |
| 3a. Quick release | The modifier | Up's Release: remove the cover and the modifier, add `Steering \| LS Up: Double Tap` |
| 3b. Late release | `Steering \| LS: Tap Cover` | Up's or down's Release: remove both modifiers and the cover |
| 4. Window | `Steering \| LS Up: Double Tap` | Scroll at 50 ms, close at 150 ms. Up: remove the window, add `Steering \| LS Up: Scroll Up` |
| 5. Second deflect | `Steering \| LS Up: Scroll Up` (new) | Scroll on the press. A chord on the deflect, 150 ms: add `Steering \| LS: Double Tap Cover`, with its reset. Release: back to the window |
| 6. Held second deflect | `Steering \| LS: Double Tap Cover` | The scroll every 50 ms, no chord. Release: remove the cover and the scroll layer |

## What changed

19 layers and 56 changes per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

| Layers | Change |
|---|---|
| The two stick modifiers | The 200 ms chord is on the left stick's deflect, not on the drivers. The Release that opens the window moves from the ring to the modifier's own direction |
| `Steering \| LS: Tap Cover` | Up and down hold only a Release. The cleanup function and its guard come off them. The ring's Release is gone |
| The two stick windows | Two always-on entries, 50 ms and 150 ms. The own direction goes to the scroll layer. A thumb's lift no longer scrolls |
| `Steering \| LS Up: Scroll Up`, `Steering \| LS Down: Scroll Down` | New, the last two layers. Copies of the cover's two stick groups with the own direction of `R1: Scroll Up`. They bind only the two sticks |
| `Steering \| LS: Double Tap Cover` | Up and down repeat the scroll with no chord and end on their Release. No cleanup function on them. The ring's Release is gone |
| 12 other layers, 42 bindings | Every binding that removes the cover also removes the two scroll layers: the W and S layers, `Steering`'s exit, the two Steering Modifier 2 layers, the menu Entry Points, `Gamepad`, `Menu Keys` |

## What you would feel

- A quick deflect scrolls 50 ms after the stick comes back, not 150 ms.
- A second deflect inside the window scrolls on the press, and a run of
  deflects keeps scrolling. Held, it repeats.
- **The modifier map no longer stays through a roll to the side.** Until
  90.51, holding up and rolling to the left kept the up modifier's buttons
  until the stick was back inside the ring. Now it ends as up lets go. While
  the stick is in the diagonal, up is still held and the map stays.
- A roll into a side doesn't scroll: the side direction goes down before up
  lets go and adds the hold marker. The plan said it would scroll inside
  200 ms; the simulator shows it doesn't.
- Reversing from a held down to up and back to centre inside 200 ms scrolls
  up once: the short up is a tap of its own.
- A thumb lifted inside the window before 50 ms loses the scroll.

## Rules and the register

- **R130** has a left-out clause: a layer's own input, the one whose press,
  hold and Release run its sequence, carries no cleanup function, as R171
  leaves out a layer's own button. Three register entries name the stick
  layers' own directions (status allow). They replace 90.51's two to-do
  entries, and close the to-do "normalize the stick cleanup functions". **The
  author has not read the rule text yet.**
- **R139:** one entry for the inputs the scroll layers inherit from the W or S
  layer (the drivers, Start, Select, the right stick's edge). Between the two
  stacks only the owner differs.
- **R125** is now checked by a scenario (90.52 S6).
- `cover_resets` accepts eight second-press layers.
- **A59** (the deflect chord starts at the direction's press) and **A60** (a
  direction's Release fires in a layer added over the held direction) are new
  and unverified.

## Validation

- The fix pipeline changed nothing. The four audits pass on both layouts,
  against the 90.51 baseline and as installed.
- `tests/test_scenarios_90_52.py`: eight stick scenarios for every driver and
  direction, six shape checks, and one guard for the held pad click. Each
  stick scenario repeats its gesture inside one driver hold.
- Ten older test modules encoded the old sequence and were updated in
  place, each with a note of what 90.52 changed. `90.49 S1` (a thumb's lift
  scrolls) is frozen on the 90.49 candidate.
- Full run, 101 modules: five fail, each with exactly the failing tests it
  had on 90.51 (`test_fallback_window_backport`, `test_layer_report`,
  `test_neptune_gyro`, `test_steering_entry_quiet_drivers`,
  `test_steering_rtp_menu_chords`). `test_double_tap_windows`, which failed on
  90.51, passes.
- 91 of 91 layers (Base included) are on the stack in a scenario in each
  layout. [unverified-assumptions.txt](unverified-assumptions.txt) lists what
  rests on an unverified assumption.
- Both VDFs exported with key, value and order verification. The four files
  are in `versions/neptune/90.52/`. The descriptions were read and kept.

## On the Deck

Load the layout fresh and look at the two new layers' binds first.

| Check | Expect | If not |
|---|---|---|
| Hold a driver in `Steering`. Deflect up four times, then down four times | One wheel step each | Once only: the cause is outside these binds. None: A60 |
| Deflect twice fast, then hold the second | A step, then a running scroll while held | |
| Hold up past 200 ms and let go | No scroll | A scroll: A59 |
| Hold up, roll to the left, come back | A steers. No scroll | |
| Deflect to the rim with the driver held | `Steering` stays | It ends: a cleanup function in the driver's layer fires with the driver held |
