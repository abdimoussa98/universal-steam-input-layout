# Plan: the Steering stick deflect on the bumper lifecycle, and a held pad click that drops when a thumb leaves a stick

**Status, 2026-10-10:** part 1 is built as 90.52, both layouts
([record](../findings/2026-10-10-stick-lifecycle-on-bumper-pattern/README.md)).
Not run on the Deck. Part 2 is not built: it waits for the Deck trial.

One line of this plan was wrong: a roll from up into a side inside 200 ms
does not scroll. The side direction goes down before up lets go and adds the
hold marker, so the roll is a hold (scenario 90.52 S5).

Two parts:

1. Rebuild the stick modifiers' sequence in `Steering` on the L1 and R1
   modifier lifecycle. On 90.51 a deflect still scrolls once and then not again
   (author, 2026-10-10).
2. A pad click that is already held drops when a thumb lifts from a stick:
   letting go of the pad then gives no release bump (author, 2026-10-10, on
   90.51). Not diagnosed. It needs a short Deck trial before a design.

The author's decisions, 2026-10-10:

- The window scrolls at 50 ms, as on the bumpers.
- Follow the bumper pattern as closely as possible: the second deflect gets
  its own layer, as `L1: Scroll Down` is for the bumper. Two new layers.
- Windows keep overriding the pad clicks (R149, R172). No hand-over from a
  window to a pad click.

Read from `neptune/single-set-default_hold-gyro_latest.json` (90.51). The
alternative layout has the same shapes with L2 and R2 for L1 and R1.

## Terms

- **Lifecycle input**: the one input whose press, hold and release drive the
  sequence. L1 for the bumper modifier, the stick's up direction for
  `Steering | LS Up: Modifier 1`.
- **Self-chord**: a chord whose chord button is the bound input itself. It is
  how the layouts put a start delay on a press.
- **Hold marker**: the layer the timer adds after 200 ms. It takes over the
  Release, so a hold opens no window.
- **Window**: the short Always On layer a quick tap opens. It scrolls one step.
- **Ring**: the stick's outer ring input (`edge`), at radius 13276 in these
  layers.
- **Stick tap**: a thumb on a stick's cap for less than 150 ms, with or
  without a deflect.

---

## Part 1: the stick deflect

### The bumper lifecycle (L1; R1 mirrors it)

| Step | Layer | On L1 |
|---|---|---|
| 1. Entry | `Base` | Self-chord, repeats every 50 ms: add `L1: Modifier 0` |
| 2. Timer | `L1: Modifier 0` | Reset (repeats every 250 ms): remove the hold marker. Self-chord, 200 ms: add the hold marker `L1: Temp Cursor Gyro` |
| 3a. Quick release | `L1: Modifier 0` | Release: remove the marker and the modifier, add `L1: Double Tap` |
| 3b. Late release | `L1: Temp Cursor Gyro` or `L1: Tap Cover` | Release: remove the marker and the modifier. No window |
| 4. Window | `L1: Double Tap` | Always-on at 50 ms: scroll. Always-on at 150 ms: remove the window. A press of L1: remove the window, add `L1: Scroll Down` |
| 5. Second tap | `L1: Scroll Down` | Press: scroll. Reset (repeats every 200 ms): remove the cover. Self-chord, 150 ms: add `L1: Double Tap Cover`. Release: remove the layer, add the window again |
| 6. Held second tap | `L1: Double Tap Cover` | Press repeats the scroll every 50 ms, no chord. Release: remove it and `L1: Scroll Down` |

Every step is on L1, every chord on L1 is a self-chord, and L1 never carries a
cleanup function. The other buttons carry the cleanup functions, each guarded
by a chord on L1.

### The stick lifecycle on 90.51 (up, with R1 held; down mirrors it)

| Step | Layer | On the stick |
|---|---|---|
| 1. Entry | `Steering \| R1: W Key` | Up: a cleanup function, and a chord on R1 that repeats every 50 ms: add `LS Up: Modifier 1` |
| 2. Timer | `LS Up: Modifier 1` | Up: the reset, and a chord on **L1 or R1**, 200 ms: add the hold marker `LS: Tap Cover` |
| 3a. Quick release | `LS Up: Modifier 1` | **The ring's** Release: remove the marker and the modifier, add `LS Up: Double Tap`. Up has no Release |
| 3b. Late release | `LS: Tap Cover` | **The ring's** Release: remove both modifiers and the marker |
| 4. Window | `LS Up: Double Tap` | One always-on at 150 ms: scroll and remove the window together. Up: remove the window, add `LS: Double Tap Cover` |
| 5. Second deflect | none | |
| 6. Held second deflect | `LS: Double Tap Cover` | Up: a cleanup function, and a chord on **L1 or R1**, 5 ms, that repeats the scroll every 50 ms. Up's Release and the ring's Release: remove it |

The timer's chord has been on L1 or R1 since at least 90.38. It was never on
the deflect.

### Where they differ

| | Bumper | Stick on 90.51 |
|---|---|---|
| A. The timer's chord button | L1 itself | The driver's bumper, which is held through every deflect |
| B. The input that ends a tap | L1, which started it | The ring, a second input with its own threshold |
| C. Cleanup functions on the lifecycle input | None | On up in the marker and the cover, and on the ring in all of them |
| D. The window | Scrolls at 50 ms, closes at 150 ms | Scrolls and closes at 150 ms |
| E. The second tap | Its own layer, which reopens the window on Release | Straight to the cover |

**What is not known.** I can't show from the files which difference makes it
scroll only once: the press simulator scrolls on every deflect on 90.50 and
90.51. The plan removes all five. If it still scrolls once on the Deck, the
cause is outside these layers' binds.

### The revised stick lifecycle

Up with a driver held. Down mirrors it with `LS Down: Modifier 0`,
`LS Down: Double Tap` and `LS Down: Scroll Down`.

| Step | Layer | On up | Change from 90.51 |
|---|---|---|---|
| 1. Entry | The W or S layer | A cleanup function, and a chord on the driver that repeats every 50 ms: add `LS Up: Modifier 1` | None. Here up is "another button" of the driver's layer, the shape those have in `L1: Modifier 0` |
| 2. Timer | `LS Up: Modifier 1` | The reset (repeats every 250 ms). A chord on **the left stick's deflect**, 200 ms: add `LS: Tap Cover` | The chord button (A) |
| 3a. Quick release | `LS Up: Modifier 1` | **Up's Release**: remove the marker and the modifier, add `LS Up: Double Tap` | Moved from the ring (B) |
| 3b. Late release | `LS: Tap Cover` | **Up's and down's Release**: remove both modifiers and the marker | Moved from the ring (B). The cleanup function and its guard come off up and down (C) |
| 4. Window | `LS Up: Double Tap` | Always-on at 50 ms: scroll. Always-on at 150 ms: remove the window. Up: remove the window, add `LS Up: Scroll Up` | The scroll at 50 ms (D). Up goes to the new layer (E). A thumb's lift only closes the window |
| 5. Second deflect | **`Steering \| LS Up: Scroll Up`** (new) | Press: scroll. Reset (repeats every 200 ms): remove the cover. A chord on the deflect, 150 ms: add `LS: Double Tap Cover`. Release: remove the layer, add `LS Up: Double Tap` | New (E) |
| 6. Held second deflect | `LS: Double Tap Cover` | The scroll, repeating every 50 ms, no chord. Release: remove the cover and both new layers | No chord, no 5 ms delay. The cleanup function comes off up and down (C) |

**The ring.** In the two modifiers, the marker, the cover and the two new
layers the ring keeps a cleanup function and its guard, and has no Release. It
can't keep a Release that removes the modifier: the ring lets go before or
with up, so the modifier would be gone before up's Release could open the
window.

**The two new layers.** `Steering | LS Up: Scroll Up` and
`Steering | LS Down: Scroll Down`, named after `R1: Scroll Up` and
`L1: Scroll Down`. Their other inputs follow `L1: Scroll Down`: a cleanup
function guarded by a chord, and a thumb's lift that adds the cover. They
don't bind the drivers, so W or S stays held from the layer below. They join
every removal list that names the cover today: the drivers' Release,
`Steering`'s exit, and the cleanup functions around them.

### What you would feel

- A quick deflect scrolls 50 ms after the stick comes back, not 150 ms.
- A second deflect inside the window scrolls on the press, and its release
  opens the window again, so a run of deflects keeps scrolling as a run of L1
  taps does.
- Rolling from up into left or right ends the modifier there, with no scroll
  (corrected after the build). Until 90.51 the modifier stayed until the stick
  was back inside the ring.
- A thumb lifted inside the window before 50 ms loses the scroll, as on the
  bumpers. 90.49's scroll on that lift (R125) comes off.

### What it rests on

New rows for `resources/Steam Behaviour Assumptions.md`:

| | Assumption | If it fails on the Deck |
|---|---|---|
| A59 | A direction's chord on the left stick's deflect starts when that direction is pressed: the deflect counts as held at that moment. `LS Up: Modifier 1` already uses this chord button on the face buttons and the stick click | A hold never adds the marker, so a long hold scrolls on release |
| A60 | A direction's Release fires in a layer added while that direction was already held, as L1's Release does in `L1: Modifier 0`. `Steering \| LS: Entry Guard` and the cover already bind a direction's Release | No deflect scrolls, and the modifier stays on |

A55 (the ring ends a partial flick) and A8 (the ring's Release in a layer
added with the stick out) stop mattering for these layers. Without cleanup
functions on up and down, a driver release missed in the Steam menu is cleared
by the next other input (scenario S2 of 90.51).

### Rules

- **A new rule in place of the R130 exceptions:** the lifecycle input of a
  modifier carries no cleanup function in the modifier, its hold marker, its
  scroll layer and its cover. L1 and R1 already follow it. With it the two
  R130 entries of 90.51 leave the register, and the to-do "normalize the stick
  cleanup functions of the Steering stateful layers" is closed by this shape.
  The author reviews the rule text before the build uses it.
- R125 and `test_double_tap_windows`: the thumb-lift scroll comes off, which
  is what that test expects.
- Not changed: the thumb that leaves the stick first (R123). It still adds the
  marker, so a flick that ends with the thumb off the stick doesn't scroll.

---

## Part 2: a held pad click drops when a thumb leaves a stick

### The report

With a pad click held and a thumb on a stick, lifting that thumb drops the
click. Letting go of the pad afterwards gives no release bump (author,
2026-10-10, 90.51). Which pad, which part of it and which stick are not
stated; the four final click layers have the same shape, so I expect all of
them.

### What the files show

The four final click layers are `LTP: Arrow Keys`, `RTP: Mouse Buttons`,
`LTP: Middle Click` and `RTP: Middle Click`. Each one:

- holds itself with `hold_layer` on the click's Soft Press (the R101
  exception of 90.19), with an inverted repeating Soft Press that removes the
  layer as the backup
- binds both stick touches: a cleanup function, its guard (a chord on the
  pad's touch), and a Release that removes that stick's three layers
  (`Entry Point`, `Tap Cover`, `Temporary Gyro`)

So when the thumb lifts, the click layer's own Release runs three
`remove_layer` commands on layers that sit **under** it. Nothing in the binds
touches the click layer or its output.

On the press simulator the click holds through the lift in every order I
tried ([probe](../findings/2026-10-10-pad-click-after-stick-tap/probe.py),
[results](../findings/2026-10-10-pad-click-after-stick-tap/results.txt)). The
fault is therefore in a Steam behaviour the simulator assumes. Three
candidates, none verified:

| | Candidate | Assumption |
|---|---|---|
| 1 | Removing a layer under a layer that holds itself breaks the hold: the click layer comes off with it | A42 (`hold_layer`, which the author calls unreliable) |
| 2 | Any `remove_layer` makes Steam read held inputs again, and the click layer's own binds restart: the backup removal fires once | A18 (the author's hypothesis) |
| 3 | The Release bind itself does it, even when its removals match nothing | None yet |

The one order the simulator does fail is a different gesture: a click that
starts inside 200 ms of a stick tap's end waits for that stick's window to
close. That is the windows overriding the pad clicks, which stays as it is.

### The Deck trial, on 90.51 as installed

In a text field, hold the left pad's ring on the right side: the cursor runs
right while the click is held. "Drops" means the cursor stops. Feel for the
bump when the pad is let go.

| | Do | Tells |
|---|---|---|
| T1 | Right thumb on the right stick for a second. Click and hold the pad. Lift the right thumb | The report, confirmed with a visible output |
| T2 | Click and hold the pad first. Then touch the right stick and lift | The stick's layers were never added, so the Release removes nothing. A drop here is candidate 3 |
| T3 | Click and hold. Hold L1 for half a second and let go | Layers come and go **above** the click layer, with no window. A drop here is candidate 2; a hold with T1 dropping is candidate 1 |
| T4 | T1 on the left pad's centre (Caps Lock light) and on the right pad | Whether all four layers behave alike |

### The fix, by outcome

| Outcome | Fix to design |
|---|---|
| T1 drops, T2 and T3 hold (candidate 1) | The four layers lose the self-hold and end on the inverted repeating Soft Press alone, which is in them already as the backup. It ends the R101 exception. 90.18 ran that way and worked; its repeating bump came from haptics that 90.50 has since moved to the output |
| T3 drops (candidate 2) | The backup removal is what fires. It needs a shape that doesn't fire on a restart; to be designed with the result in hand |
| T2 drops (candidate 3) | The click layers stop binding the stick touches' Release, and the stick's own layers clear themselves. Needs R169's reading for these four layers |

Nothing for part 2 is built before the trial. Part 1 doesn't wait for it.

---

## Build steps

1. **Rule text first.** The lifecycle-input rule, in
   `resources/Layer Definition of Done.md`, for the author to read.
2. **Builder** `findings/<date>-stick-lifecycle-and-pad-click/build_candidate.py`
   from the 90.51 snapshot, both layouts:
   - the modifiers' own direction: chord button, Release; the ring's Release off
   - `Steering | LS: Tap Cover`: Release on up and down; cleanup and guard off
     them; the ring's Release off
   - the two windows: two always-on entries (50 ms, 150 ms); own direction to
     the new layer; the thumb-lift scroll off
   - the two new layers, with `tools.duplicate_layer` from the bumper scroll
     layers, kept in `action_layers` order (the layer-order swap of 2026-07-11)
   - `Steering | LS: Double Tap Cover`: plain repeating scroll, Release, no
     cleanup on up and down
   - the removal lists that name the cover
   - part 2's fix, if the trial's result is in by then
   - then `steam_layout.fixes.apply_all`
3. **Register and audits.** The two R130 entries out, the rule in the Cleanup
   audit and the `cleanup_lists` fix. `python3 -m tools.audit_build` on both
   layouts: Budget, Window, Flow, Cleanup. Review every "varies" entry of the
   two new layers.
4. **Scenarios** in `tests/test_scenarios_90_52.py`, each repeating the
   gesture inside one driver hold:
   - four quick deflects up, then down: one wheel step each at 50 ms
   - a second deflect inside the window: scrolls on the press, reopens the
     window
   - a second deflect held past 150 ms: repeats, and ends clean on release
   - a hold past 200 ms: no scroll
   - a roll from up into left inside 200 ms and after it
   - a missed driver release with the stick held
   - a held pad click with a thumb lifting from each stick, in the trial's
     three orders: the click holds (the simulator passes this today, so it
     guards the shape, not the fault)
   - 90.51's static check of the modifiers' direction moves to the new shape
5. **Export and records.** Both VDFs with verification, the snapshot in
   `versions/neptune/90.52/`, the build record, `docs/building.md`, the two
   assumption rows, `todos.md`.

## On the Deck, 90.52

| Check | Expect | If not |
|---|---|---|
| Hold a driver in `Steering`. Deflect up four times, then down four times | One wheel step each | Once only: the cause is outside these binds. None: A60 |
| Deflect twice fast, then hold the second | A step, then a running scroll while held | |
| Hold up past 200 ms and let go | No scroll | A scroll: A59 |
| Deflect to the rim with the driver held | `Steering` stays | It ends: a cleanup function in the driver's layer fires with the driver held |
| Hold a pad click, lift a thumb from a stick (only if part 2's fix is in) | The click holds, and the pad's release bumps | It drops: the candidate the trial pointed to is wrong |

## Open

1. Part 2: the results of T1 to T4.
