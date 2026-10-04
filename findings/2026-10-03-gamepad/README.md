# The Gamepad layer and the third transition (90.22)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.22**, with the
snapshot in `versions/neptune/90.22/`. Device status: **untested**. The build
audit is clean and the tests pass.

Plan and the author's decisions:
[plans/2026-10-03-cursor-gyro-and-gamepad.md](../../plans/2026-10-03-cursor-gyro-and-gamepad.md).
Structure it fits: [Stateful Layer Transitions](../../resources/Stateful%20Layer%20Transitions.md).

Select is Menu Left and Start is Menu Right.

## What it is

Two new layers per layout (78): `Gamepad`, and the transition that leads to
it. All four menu-plus-stick-click gestures are now taken.

| | |
|---|---|
| **In** | Hold Start, click and release the right stick, release Start. Or the same with Select and the left stick. Beep and strong pulse on that release |
| **Out** | Hold Start or Select, click either stick, release the button. Beep and pulse on the release. `Gyro` is as it was |
| **Not a way out** | The Modifier 2 quick tap. The bumpers and triggers are gamepad buttons in `Gamepad` (author, 2026-10-03) |

## What Gamepad sends

The same in both layouts. The map is the archived Gamepad action set's.

| Input | In `Gamepad` |
|---|---|
| A, B, X, Y | Gamepad A, B, X, Y |
| D-pad | Gamepad D-pad |
| L1, R1 | LB, RB |
| L2, R2 | Analog LT, RT. Click and edge are empty |
| Left stick, right stick | Left and right joystick. The clicks are L3 and R3 |
| L4, L5, R4, R5 | L3, B, A, Y |
| Left pad click, right pad click | Select, Start, at once |
| Stick touches, stick edges, pad touches | Empty |
| Gyro | Disabled |

The plan listed the grips as "L4, R4, L5, R5 are B, Y, L3, A". That was my
misreading of which grip is which; the build uses the archived map as it is,
which is the row above.

## Start and Select

No window, cover or Fn layers. Each button has three of Steam's own activators
(author, 2026-10-03):

| Gesture | Activator | What it does |
|---|---|---|
| Tap | Regular Press, interruptible | Sends Start or Select, after the Double Press time |
| Double press and hold | Double Press, 200 ms | Holds the button for as long as the second press is held |
| Hold | Long Press, 200 ms | An empty binding with a light pulse. It swallows the tap |

This is the one exception to R108. It is safe only because `Gamepad` is
**closed** (the new rule R168): it binds every input that carries a layer
command in Base or `Gyro`, and its only layer commands are its exit. So no
layer can be added over it, and the bug the ban is about is with layers (A20).

## The exit

Each stick click has two entries: the Regular Press (L3 or R3) and a chord on
Start or Select being held (mask 20480, Any, uninterruptible). The chord runs
the Entry Points' whole clear list, then adds the clear transition. The menu
button's Release in the transition ends it, as every clear does.

It differs from the other stateful layers in one way: the clear is entered at
the click's **press**, not its Release, because `Gamepad` has no Entry Point
layer to carry a Release.

## The transitions

| Title | Was | Select release | Start release |
|---|---|---|---|
| `Transition Set 0` | New, a copy of `Transition Set 1` | `Gamepad` | `Gamepad` |
| `Transition Set 1` | Unchanged | `Gyro`, then `Cursor Gyro` | `Steering` |
| `Transition Set 2` | The clear, titled `Transition Set 0` until 90.21 | Clear | Clear |

The clear kept its place in the layer list, so no runtime ID moved. In Base's
two Entry Points the same-side click Release now leads to the new
`Transition Set 0`. The `Stateful` Entry Points still lead to the clear.

## What changed besides the new layers

12 inputs per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)):

- The two same-side clicks in Base's Entry Points point at the new transition.
- Every whole-layout clear lists the two new layers: the eight click Releases
  of the four Entry Points, and Steering's Modifier 2 quick tap. The order of
  the rest is the same.
- The report matches layers by title, so it shows the renamed clear as
  "added" and the new `Transition Set 0` as a change of the old one.

Base, `Gyro`, `Cursor Gyro` and the modifiers are untouched.

## Consequences

- A single Start or Select tap arrives about 200 ms late. The pad clicks send
  them at once.
- If the menu button is let go before the stick click, Base is live under a
  held click and types one Q or E (scenario G5, A11).
- A quick press-and-click sends no Start: the transition binds the menu
  button, which ends the tap that was waiting (scenario G4, A15).
- If both menu buttons are held at the commit, the one still held lands in
  `Gamepad` held and may send its button once (A10). No scenario covers it.
- `Gyro` stays underneath and is back after the exit.

## Rules, exceptions and assumptions

| What | Change |
|---|---|
| R108 | Exception: Start and Select in `Gamepad`. The Budget audit reads it from the register and lists the four activators as allowed; anywhere else they still fail |
| R158 | Exception: no Entry Points; the chord on the stick clicks |
| R159 | The open to-do entry is now an exception: the Modifier 2 quick tap doesn't leave `Gamepad` |
| R162 | Exception: the Long Press is a delayed binding on a menu button |
| R168 | New: a layer that uses a Long Press or a Double Press is closed |
| R139 | The two Fn layers' entries now cover both stick clicks: the same-side click differs between Base's Entry Point and the `Stateful` one. Decided by me reading the Flow audit; not yet confirmed by the author |
| A43 | New, unverified: how a tap, a double press and a hold are told apart. `Gamepad` relies on it |
| A44 | New, unverified: Long Press and Double Press behave where no layer is added on top |
| A45 | New, unverified: a chord reads a button that carries those activators |

If A43 or A44 fails on the Deck, the fallback needs no layer: Start and Select
stay on the pad clicks alone, and the menu buttons become empty in `Gamepad`
and only arm the exit. If A45 fails, `Gamepad` needs Entry Points.

## Tools that changed

- `tools/audit_command_budget.py` reads R108 exceptions from the register
  (`allowed_native` in its report). A group shared with a layer outside the
  exception is not covered.
- `steam_layout/simulator.py` models a Long Press and a Double Press as A43
  says, and counts `xinput_button` as an output.

## Scenarios and tests

- `tests/test_scenarios_90_22.py`, G1 to G7: both ways in, from Base and from
  `Gyro`; a tap, a double press and a hold on each menu button; all four menu
  and click pairs out; a quick press-and-click; the menu button let go first;
  the Modifier 2 quick tap; every control, with no layer command at all.
- `tests/test_gamepad.py`: the map, the three activators, the closed layer,
  the exit chord, the three transitions and their feedback, and what changed
  against 90.21.
- Older scenarios and tests that named the clear by its old title are updated.

## Files

- `build_candidate.py`: the builder. It extends the 90.21 builder, which stays
  frozen.
- `install_neptune.py`, `*-gamepad.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.21 (R164).
- `unverified-assumptions.txt`: the assumptions that aren't verified, with
  what rests on each (R167).
