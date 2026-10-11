# The Steering stick: timers on the drivers, the entry and the left edge (90.53)

Built on 2026-10-10 and 2026-10-11 from the 90.52 snapshot, both layouts, on
the author's "implement the plan" and the answers that followed
([first plan](../../plans/2026-10-10-w-layer-drop-chord-rule-and-fn-bumps.md),
[timer plan](../../plans/2026-10-10-stick-hold-timer-on-the-driver.md)). No
layer is added or removed: 90 in each layout. Nothing here has run on the
Deck as built.

**Status, 2026-10-11:** a snapshot, not the working layout. The same day the
author asked for 90.54, built from 90.52 with one change
([record](../2026-10-11-hold-timer-on-the-edge/README.md)).

Not built, by the author's choice: the Fn hold bumps (first plan, part 5) and
the trackpad clicks (part 7).

## Why

Two faults on the Deck (author, 2026-10-10).

- **A deflect scrolled once and then not again** (90.50 to 90.52). The author
  found the cause on the Deck: the 200 ms hold timer was owned by stick up or
  down, and after one quick deflect it landed at once on every later one. On
  the bumper it behaves like the L1, R1 and trigger modifiers (A63). The
  simulator never showed the fault.
- **Flicking the stick with a driver held sometimes dropped the W or S layer**,
  and stick up or down then left `Steering`. Not diagnosed. This build removes
  the binds that could do it.

## What changed

12 layers and 56 changed inputs or groups per layout, among them new groups
for the drivers in the two scroll layers
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

| What | Layers | Change |
|---|---|---|
| Timers | The two stick modifiers, the two stick scroll layers | The delayed chord leaves the stick's direction. Each driver carries, in these four layers, what its own layer has on it, the key and the Release, and between them the delayed chord on the left stick's deflect: 200 ms for `Steering \| LS: Tap Cover`, 150 ms for `Steering \| LS: Double Tap Cover`. The reset stays on the stick's direction |
| The other driver | The same four layers | Each driver's key press also adds the Modifier 2 layer of the other order and removes the host and its marker or cover. Only a fresh press runs it (A5) |
| Entry | The W and S layers, up and down | The cleanup press is gone. The one chord that adds the stick modifier needs the driver and the left stick's deflect, both, where it needed the driver alone |
| Right pad | The two stick modifiers, the two Steering Modifier 2 layers | 12 binds lose their `RTP:` removes: the 200 ms chords and both stick touch Releases. The Modifier 2 Release, the clear to Base, keeps them |
| A and D | The two stick modifiers, left and right | They send the key and no longer add `Steering \| LS: Tap Cover`. The stick clicks keep that add |
| Radius | Ten Steering layers | The left stick states no outer ring radius, as in the Temp Cursor Gyro layers. It was 13276. All fourteen Steering layers now use Steam's default |
| Edge | The W and S layers, the two stick modifiers, `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover`, the two stick scroll layers, the two Steering Modifier 2 layers | On the left stick's edge, the repeating cleanup press and its empty guard chord become one chord with Invert Activation on the same drivers |
| Lists | 25 binds | The cleanup fix followed the new binds: the drivers' Releases in the four timer layers list only what can be on with them, the W and S layers' cleanup functions no longer remove the stick layers (both drivers keep those alive now, and a W cleanup is guarded by one), and the cover's cleanups also remove the two scroll layers |

Unchanged: `Steering`, `Steering | LS: Entry Guard`, the two stick windows
(apart from the radius), and every right-stick edge and stick touch, which
keep the press-and-guard shape.

## The timers: one shared modifier

The author chose one stick modifier for both drivers over a copy per driver.
A layer that binds a driver replaces everything under it on that driver, so
the four timer layers repeat the key and the Release of the W and S layers.
The reset stays on the stick's direction, as in the author's test on the
Deck. Moved to the driver as well, two held drivers kept restarting each
other's timer on the simulator and the Tap Cover never landed.

## The other driver: straight into Modifier 2

With both drivers bound in the stick modifiers, the first candidate made the
other driver type its key until the stick came back. The author, 2026-10-11:
"you won't be able to get into mod two if you're deflecting the stick".

So in the four timer layers each driver's key press also carries the commands
that the other driver's layer has on that input to enter the Modifier 2
layer. Two things keep them apart:

- **The held driver never runs them.** A layer that lands on a held input
  doesn't run its immediate layer command there (A5, verified by the author);
  the key goes down all the same (A10).
- **A fresh press runs them.** While a stick layer is on, a fresh press can
  only be the other driver's.

Hold R1, push up, press L1: `Steering | R1!L1: Modifier 2` at once, as until
90.52. What it costs:

- **The other driver's key shows for a moment**, S here, until the Modifier 2
  layer takes the input over.
- **Both drivers already down when the stick layer lands**: neither press is
  fresh, so Modifier 2 waits for the stick to come back. This needs the
  drivers and the stick to arrive together, as when `Steering` is entered
  with all three held.
- **The audits don't follow these presses** (`relay` in
  `steam_layout/flow_model.py`): the chain walk can't tell a held driver from
  a fresh press, and the stack a fresh press gives is the one the layer
  underneath gives by its own entry.

## The entry chord: one change from the plan

The plan had the entry as a chord on the deflect alone. With that, a missed
driver release looped: with the W layer stuck and the stick held up, a face
button's cleanup removed the stick modifier and the W layer's up added it
again, without end (90.43 D4). Asked on 2026-10-10, the author chose the
chord on the driver and the deflect, both. The stick modifiers' stick clicks
have chorded on the same two since 90.38.

## What you would feel

- Every quick deflect scrolls once and every hold past 200 ms does not, in
  any order.
- With a driver held, nothing on the left stick's edge, up or down can remove
  the W or S layer: those binds hold no removal that a held driver has to
  hold back.
- A quick up or down rolled into A or D inside 200 ms scrolls once: it is a
  tap. Until 90.52 the side key made it a hold. Past 200 ms nothing scrolls,
  as before.
- The right pad's layers stay on when the stick's 200 ms hold lands or a
  thumb lifts from a stick in a Steering modifier layer.
- The edge is near the rim again. A W or S layer left on by a missed driver
  release clears when the stick has been to the rim and back, on a stick
  touch, or when the driver is pressed again. Until 90.52 the edge cleared it
  from about 40% of travel.

## The Entry Guard

The simulator had the inverted chord backwards: it ran the chord while a
chord button was held. It now runs it while none is (A61). The Entry Guard's
bind is unchanged since 90.44, but what the simulator says it does has
changed:

| How `Steering` is entered | What the guard does |
|---|---|
| Stick at centre, no driver | It is added and removed in the same moment. The first full push up or down is `Steering`'s own exit |
| Stick held at the rim | It stays, and the stick keeps typing its key. It leaves when the stick comes back |
| A driver pressed while it is on | The driver's layer takes over |

The author, 2026-10-11: "I only want the guard to protect a stick held at
entry." A first push after a centred entry is not meant to be guarded. So the
bind stands, and 90.53 G1 to G3 state it. The older scenarios that state a
guarded first push, and those of the frozen 90.33 to 90.41 builds whose
Fallback Guard used the same chord, are marked `old_inverted_chord` in
`tests/scenario.py` and run as expected failures.

## Rules, the register and the simulator

- **A61** (new): a chord with Invert Activation runs while its input is
  released and no chord button is held. From the author and from Steam's own
  text for the setting. A54, the 90.44 note and `steam_layout/simulator.py`
  said the opposite until now.
- **A63** (new, from the author's Deck test): a start delay owned by a stick
  direction lands at once after one interruption; on a bumper or trigger it
  does not.
- **A62** (new, unverified): the entry chord starts on every new deflect. It
  was built on a lead that the author's finding replaced; the entry stands as
  built.
- **R120:** the reset of these four timers is on the stick's direction, not on
  the driver that owns the delay. `steam_layout/flow_model.py` reads it as the
  reset of a delay chorded on that stick's deflect, and the `cover_resets` fix
  leaves such a chord alone.
- **R133:** on these ten edges the cleanup function is one inverted chord.
  `steam_layout/flow_model.py` reads it as a cleanup function, and its chord
  buttons as its guard, so the Cleanup audit checks its list as before.
- **R111:** ten register entries, one per chord, exact to the list and the
  settings. The Budget audit now reads register titles through the
  alternative's renaming.
- **R130:** the left-out clause names up and down in the W and S layers.
- Set aside by the author: whether a repeating chord with more than one
  sub-command fires. Every one of the ten lists is longer than one
  (`todos.md`).

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup).
- **Scenarios:** `tests/test_scenarios_90_53.py`, 22 tests, pass. Every layer
  that changed is on the stack in a scenario (R165). The assumptions that
  aren't verified, with what rests on each, are in
  [unverified-assumptions.txt](unverified-assumptions.txt).
- **Full suite**, on a copy of the repository with 90.53 installed,
  2026-10-11: 1160 tests, 25 expected failures (the `old_inverted_chord`
  scenarios), 18 failing.
  - 14 fail on 90.52 as well, in five modules: `test_fallback_window_backport`
    (1), `test_layer_report` (1), `test_neptune_gyro` (6),
    `test_steering_entry_quiet_drivers` (1), `test_steering_rtp_menu_chords`
    (5).
  - 2 came from this build's wording in the rule tables and are fixed: R120
    named the Deck, and R120 and A63 did not name each other
    (`test_rule_registry`).
  - 2 are one test on both layouts,
    `test_layout_hygiene.test_only_second_press_cover_resets_use_a_last_fourth_entry`:
    it expects the two stick scroll layers to hold a fourth entry on up or
    down, which they lost here with the 150 ms chord. Not changed: 90.54, the
    working layout, has that entry again.

## On the Deck, in this order

1. Load fresh. Enter `Steering`, hold a driver and flick the stick about for
   ten seconds, to the rim and around it: W or S stays, and `Steering` stays.
2. With the driver held, deflect up four times and down four times, with a
   hold past 200 ms in between: one wheel step for each tap, none for a hold
   (A63). W or S stays down throughout.
3. With R1 held and the stick up, press L1: the Modifier 2 layer at once, and
   the stick scrolls. Then the same with L1 held and R1 pressed. If Modifier 2
   comes as soon as the stick goes up, with one driver held, A5 does not hold
   here.
4. Up, then roll to the left inside 200 ms: A, and one wheel step. Hold up
   past 200 ms, then roll: A, no wheel step.
5. Rest a thumb on the right pad, hold up past 200 ms: the right pad still
   scrolls.
6. Enter `Steering` with the stick at centre and no driver, then push up to
   the rim: does `Steering` stay? This is the Entry Guard question above.
