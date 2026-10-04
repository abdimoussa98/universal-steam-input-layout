# The stateful Cursor Gyro layer (90.21)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.21**, with the
snapshot in `versions/neptune/90.21/`. Device status: **untested**. The build
audit is clean and the tests pass.

Plan and the author's decisions:
[plans/2026-10-03-cursor-gyro-and-gamepad.md](../../plans/2026-10-03-cursor-gyro-and-gamepad.md).
Structure it fits: [Stateful Layer Transitions](../../resources/Stateful%20Layer%20Transitions.md).

Select is Menu Left and Start is Menu Right.

## What it is

One new layer per layout, `Cursor Gyro` (76 layers). It is a thin layer that
always sits on `Gyro`: it gives the gyro the Temp Cursor Gyro response until it
is left, and binds nothing else but its exits.

| | |
|---|---|
| **In** | Hold Select, click and release the right stick, release Select. Beep and strong pulse on that release |
| **Out 1** | Any menu button plus any stick click. Ends in `Gyro` |
| **Out 2** | The Modifier 2 quick tap. Ends in Base |
| **Out 3** | Both sticks pushed out about a quarter. Beeps. Ends in `Gyro` |

## What the layer binds

| Source | Binding |
|---|---|
| Gyro | `gyro_to_mouse` with precision speed 750, haptic intensity 0, haptic bump 1 and movement threshold 5, the four settings of the Temp Cursor Gyro layers. No gate: `Gyro` underneath supplies it |
| Start, Select | A repeating press that adds a `Stateful` Entry Point |
| Left-stick edge | Radius 4915, not inverted. A chord on the right stick being out (mask bit 31), repeating and uninterruptible: removes `Cursor Gyro`, with the beep flag |
| Right-stick edge | Radius 7209. The same chord on the left stick being out (bit 30) |

Everything else comes from `Gyro` and Base.

## What changed around it

- **`Transition Set 1`, Select Release.** It only cleared. Now it removes the
  transition, adds `Gyro`, then adds `Cursor Gyro` with the beep flag.
- **The two `Gyro | … Modifier 2` layers.** The uncovered release that clears
  to Base also removes `Cursor Gyro`.
- **Steering's two Entry Points are renamed** `Stateful | Menu Left: Entry Point`
  and `Stateful | Menu Right: Entry Point`, and `Cursor Gyro` uses them too.
  Their bindings are the same. The layers that name them in a removal list
  are most of the change report.
- **Every whole-layout clear lists `Cursor Gyro`:** the four Entry Points'
  click Releases and Steering's Modifier 2 quick tap.

Of the 63 changed inputs per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)), 62 differ
only by the new titles or by the added removal. The other one is the Select
Release above.

## The both-sticks exit is only in Cursor Gyro

The author settled this on 2026-10-03, after wider versions were discussed and
dropped: nothing on top carries the exit. A layer on top that binds the stick
edges answers instead.

| On top | Both sticks out |
|---|---|
| Stick-touch helpers, pad layers | They don't bind the edges. The exit works through them |
| A held modifier | Its own chord adds its Tap Cover, as before. `Cursor Gyro` stays |
| A held menu button | The stick guards, as before |
| A Double Tap window | Both edges are empty for its 150 ms |

The exit's chords repeat. So when the layer on top goes and both sticks are
still out, `Cursor Gyro` ends then (scenarios C5 and C6).

## Consequences

- Entering from Base turns `Gyro` on, and two of the three exits leave it on.
  The Modifier 2 quick tap is the way back to Base.
- No ramp-up while `Cursor Gyro` is on: the layer takes the right-stick edge,
  where Base adds `Gyro Off Ramp Up`. The stick still moves the pointer. When
  the layer ends with the stick still out, Base's edge is back and ramp-up
  comes on.
- Entering with both sticks already out leaves again at once, and `Gyro` stays
  on (scenario C9).
- The pointer stops while a menu button is held: the Entry Points disable gyro.

## Exceptions recorded

In `steam_layout/flow_config.json`:

- **R139**, the `Stateful` Entry Points' right-pad touch. Over `Cursor Gyro` it
  adds `RTP: Entry Point` from Base; over `Steering` it does nothing, because
  Steering clears it. Decided by me reading the Flow audit; not yet confirmed
  by the author.
- **R136**, `Menu Buttons: Tap Cover` over each stick guard. The pair is
  unchanged and was read as passing by the author on 2026-10-02. It came up
  again because both layers' lists name the renamed Entry Points.
- **R157**, the existing entry now also names the both-sticks exit and the
  entry that adds `Gyro`.

## Scenarios and tests

- `tests/test_scenarios_90_21.py`, C1 to C9: the entry from Base and from
  `Gyro`, the four menu gestures out, the Modifier 2 quick tap, both sticks in
  either order, a held modifier, a window, a menu tap, the temp cursor on top,
  and entering with both sticks out.
- `tests/test_cursor_gyro.py`: the layer's bindings, the entry, the clears, the
  rename, and that no other layer removes `Cursor Gyro`.
- Scenario 90.10 T1 is updated: Select plus the right-stick click no longer
  clears.

No new Steam assumption. The entry rests on A3 (verified). C4 rests on A36, and
C5, C6 and C9 are run both ways under A9.

## Files

- `build_candidate.py`: the builder. It extends the 90.20 builder, which stays
  frozen.
- `install_neptune.py`, `*-cursor-gyro.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.20 (R164).
- `unverified-assumptions.txt`: the assumptions that aren't verified, with
  what rests on each (R167).
