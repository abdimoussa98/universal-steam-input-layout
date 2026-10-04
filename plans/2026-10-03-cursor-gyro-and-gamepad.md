# Plan: the stateful Cursor Gyro layer and the Gamepad layer

**Status, 2026-10-03:** plan only, nothing built. Asked for by the author on
2026-10-03, who answered every decision the same day
([list](#decisions)). Starts from 90.20, which is installed in `neptune/` but
not yet committed.
Design it has to fit: [Stateful Layer Transitions](../resources/Stateful%20Layer%20Transitions.md)
· [Definition of Done §11](../resources/Layer%20Definition%20of%20Done.md#11-stateful-layers)

Names used below: **Select** is Menu Left (`button_menu`), **Start** is Menu
Right (`button_escape`). A **stateful layer** is one that stays on until it is
left on purpose, like `Steering`.

## Summary

Three new layers, 75 to 78 per layout: `Cursor Gyro`, `Gamepad`, and the third
transition layer. No helper layers for either.

| | Cursor Gyro | Gamepad |
|---|---|---|
| **In** | Select + right-stick click. Turns `Gyro` on as well | Start + right-stick click, or Select + left-stick click (the two same-side gestures) |
| **Out 1** | Any menu button + any stick click. Ends in `Gyro` | Any menu button held + any stick click. Keeps `Gyro` if it was on |
| **Out 2** | Modifier 2 quick tap (both bumpers; both triggers in the alternative). Ends in Base | None. The bumpers and triggers are gamepad buttons there (author, 2026-10-03) |
| **Out 3** | Both sticks pushed out about a quarter, as Temp Cursor Gyro ends. Ends in `Gyro` | None |

Every way in is the existing gesture: hold the menu button, click the stick,
let go of the click, then let go of the menu button. The beep and the strong
pulse come on that last release. All four gestures are then taken:

| Gesture | Destination |
|---|---|
| Start + LS click | `Steering` (built) |
| Select + RS click | `Cursor Gyro` |
| Start + RS click | `Gamepad` |
| Select + LS click | `Gamepad` |

## Cursor Gyro

**A thin layer that always sits on `Gyro`** (author, 2026-10-03). Entering it
adds `Gyro` first and `Cursor Gyro` second. It binds only the gyro response
and its exits; the gate and the modifiers come from `Gyro`, and everything
else from Base.

| Source | What `Cursor Gyro` binds |
|---|---|
| Gyro | `gyro_to_mouse` with the four settings of `L1: Temp Cursor Gyro` (group 13058): precision speed 750, haptic intensity 0, haptic bump 1, movement threshold 5. It states no gate, like the temp layers: `Gyro` underneath supplies it, so the pointer moves while a thumb touches or pushes either stick. Sensitivity 300 and the rest stay inherited from Base |
| Start, Select | A repeating press that adds a clear Entry Point, as `Steering` does. No Release, no delay (R162) |
| Left-stick edge | Radius 4915, not inverted. One chord, on the right stick being out, repeating and uninterruptible: removes `Cursor Gyro`, with the beep flag |
| Right-stick edge | Radius 7209. The same chord on the left stick being out |
| Bumpers, triggers | Nothing. `Gyro`'s binds add the `Gyro \| …` modifiers |

**Entry.** `Transition Set 1`'s Select Release, which only clears today,
becomes one array: remove the transition, add `Gyro`, add `Cursor Gyro` with
the beep flag. One beep. If `Gyro` is already on, its add does nothing (A3:
re-adding a layer doesn't move it).

**The Modifier 2 clear (R159).** Because `Gyro` is always underneath, the
modifiers are always the `Gyro | …` family, whose uncovered Modifier 2 release
already clears everything to Base. That release, in both
`Gyro | … Modifier 2` layers, also removes `Cursor Gyro` (author, 2026-10-03).

**The menu-plus-click exit (R158).** `Cursor Gyro` reuses Steering's two Entry
Points (author, 2026-10-03), renamed `Stateful | Menu Left: Entry Point` and
`Stateful | Menu Right: Entry Point`. Its own Start and Select presses add
them. Their clicks both lead to the clear transition. They differ from Base's
only in the click targets and in typing W and S on stick up and down, which
Base does too. `Cursor Gyro` goes into the clear list of all four Entry
Points; the cleanup audit decides the rest.

**The both-sticks exit is only in `Cursor Gyro`** (author, 2026-10-03). The
primary exits are the menu button plus stick click and the Modifier 2 quick
tap. A layer on top that binds the stick edges answers instead, and is not
changed for it:

- A held modifier: both sticks add its Tap Cover, as today. `Cursor Gyro`
  stays.
- A held menu button: the stick guards, as today.
- A Double Tap window: both edges are empty for its 150 ms. The chord repeats,
  so the exit follows when the window closes if the sticks are still out.
- The stick-touch helpers and the pad layers don't bind the edges, so the exit
  works through them.

**Consequences**

- Entering from Base turns `Gyro` on, and two of the three exits leave it on.
  The menu-plus-click clear keeps `Gyro` by rule, and the both-sticks exit
  removes only `Cursor Gyro`. The Modifier 2 quick tap is the way back to
  Base.
- No ramp-up while `Cursor Gyro` is on (accepted by the author, 2026-10-03).
  The both-sticks exit takes the right-stick edge, which in Base adds
  `Gyro Off Ramp Up`. The stick still moves the pointer.
- Entering with both sticks already pushed out leaves again at once: the two
  edge chords repeat.
- The pointer stops while a menu button is held (the Entry Points disable
  gyro), as the camera does today.
- Holding a modifier 300 ms still adds the Temp Cursor Gyro layer on top. Same
  settings, so nothing changes in feel.

## Gamepad

One layer, the same in both layouts. It binds **every** input, so nothing from
Base comes through and no layer can be added over it. The map is the archived
Gamepad action set's (`archived/universal-layout-default__hold-gyro__latest.json`).

| Input | In `Gamepad` |
|---|---|
| A, B, X, Y | Gamepad A, B, X, Y |
| D-pad | Gamepad D-pad |
| L1, R1 | LB, RB |
| L2, R2 | Analog LT, RT. Click and edge empty |
| Left stick, right stick | Left and right joystick. Clicks are L3 and R3 |
| L4, R4, L5, R5 | B, Y, L3, A (archived map) |
| Left pad click, right pad click | Select, Start, at once with no tap window (archived map) |
| Stick touches, stick edges, pad touches | Empty |
| Gyro | Disabled |
| Start, Select | Three native activators, below |

**Start and Select (author, 2026-10-03).** No window, cover or Fn layers. The
same three gestures as in Base, built from Steam's own activators:

| Gesture | Base today | `Gamepad` |
|---|---|---|
| Tap | Tab / Escape, from the Double Tap window | Regular Press, interruptible: gamepad Start / Select |
| Double press and hold | The key held (`Menu Right: Tab`) | Double Press: Start / Select held for as long as the button is |
| Hold | The menu hold: Fn and the stick-click gestures | Long Press: an empty binding with a light pulse. It swallows the tap and tells you the stick click will now exit |

Times: Long Press 200 ms (the Fn delay), Double Press 200 ms.

**Exit.** Each stick click has two entries: the Regular Press (L3 or R3), and
a chord on *Start or Select held* (mask 20480, Any; uninterruptible). The
chord runs the Entry Points' clear list plus `Gamepad`, then adds the clear
transition. The menu button's Release in the transition ends it with the beep
and pulse, as every clear does.

**Entry.** A new transition layer, a copy of `Transition Set 1` whose two menu
Releases both remove it and add `Gamepad` with the beep flag. In
`Menu Left: Entry Point` the left-stick click Release, and in
`Menu Right: Entry Point` the right-stick click Release, point at it instead
of the clear. Steering's Entry Points keep the clear.

**Titles.** The design document numbers them 0 same-side, 1 cross,
2 clear, and says the titles get sorted out when Gamepad arrives. Today's
`Transition Set 0` is the clear. It is renamed `Transition Set 2`, and the new
layer takes `Transition Set 0`. No position or runtime ID moves.

**Consequences**

- A single Start or Select tap is late by the Double Press time. The pad
  clicks send them at once.
- The exit fires at the click's **press**, not its Release. If the menu button
  is let go before the stick click, Base is live under a held click and may
  type one Q or E (A11, unverified).
- Leaving `Gamepad` with a quick press-and-click sends no Start: the transition
  binds the menu button and eats the pending tap (established: an override
  eats a pending delay).
- If both menu buttons are held at the commit, the one still held lands in
  `Gamepad` and may send its button once (A10).
- `Gyro` stays underneath and is back after the exit.

## Rules and exceptions

| Rule | What changes |
|---|---|
| R108, no Long or Double Press | **New exception**, scoped to Start and Select in `Gamepad` (author, 2026-10-03: nothing is layered over Gamepad). The Budget audit and `test_layout_hygiene` read it from the exceptions register; everywhere else they still fail |
| R158, own Entry Points for the clear | **New exception** for `Gamepad`: a chord on the click enters the clear transition directly |
| R159, Modifier 2 clears every stateful layer | The open "todo" entry becomes an **allow** for `Gamepad`. `Cursor Gyro` follows the rule, through the `Gyro \| … Modifier 2` releases |
| R162, no delayed bind on Start or Select at entry | **New exception** for `Gamepad`'s Long Press. The commit is the menu button's own Release, so the button is up when the layer lands |
| R157, exits without a transition | `Cursor Gyro`'s both-sticks exit joins the existing entry (author, 2026-10-01) |
| New rule, next free ID after R167 | `Gamepad` binds every input that carries a layer command in Base or `Gyro`, and its only layer command is the exit chord. This is what makes the R108 exception safe. Checked by a new static test |

## Assumptions to add

Rows in [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md),
each with a Deck procedure. All unverified; `Gamepad` relies on the first two.

| ID | Behaviour | If it fails |
|---|---|---|
| A43 | On a button with an interruptible Regular Press, a Double Press and a Long Press: a tap sends the Regular Press once, after the Double Press time; a hold sends only the Long Press; a double press and hold sends only the Double Press, for as long as it is held | Start and Select stay on the pad clicks alone; the menu buttons become empty in `Gamepad` and only arm the exit. No layer added |
| A44 | Long Press and Double Press behave in a layer that nothing is added over (the limit of A20) | The same fallback |
| A45 | A chord reads Start or Select as held while that button carries Long and Double Press activators | Entry Points for `Gamepad`, the layers this plan avoids |

`Cursor Gyro` adds no assumption. Its entry rests on A3, which is verified,
and its edge chords are the Temp Cursor Gyro pattern (it states
`edge_binding_invert` 0, so it doesn't rely on A38).

## Decisions

Answered by the author on 2026-10-03:

| Question | Decision |
|---|---|
| Cursor Gyro's gate | Entering `Cursor Gyro` also applies `Gyro`: `Gyro` first, `Cursor Gyro` on top. The `Gyro \| … Modifier 2` layers also remove `Cursor Gyro` |
| No ramp-up in Cursor Gyro | Accepted. The exit is on both stick edges, as in Temp Cursor Gyro |
| Entry Points for Cursor Gyro | Reuse Steering's pair, added by `Cursor Gyro`'s own menu presses |
| Gamepad's Start and Select | Tap sends the button, double press and hold holds it, hold arms the exit. 200 ms for both times |
| Releases | Two: 90.21 is Cursor Gyro, 90.22 is Gamepad |
| Transition titles | No preference; the rename stands: the clear becomes `Transition Set 2`, the Gamepad transition is `Transition Set 0` |
| Grip buttons and pad clicks in Gamepad | The archived map: L4, R4, L5, R5 are B, Y, L3, A; the pad clicks are Select and Start |
| The Entry Points' new titles | `Stateful \| Menu Left: Entry Point` and `Stateful \| Menu Right: Entry Point` |
| Cursor Gyro's third exit | Both sticks out, in `Cursor Gyro` only. Nothing on top carries it. Wider versions (a stick plus a button; carrying it in the windows or the modifiers) were discussed and dropped as too complicated |

## Build steps

Each release follows [building](../docs/building.md): a new builder folder
copied from the one before, both layouts, the fix pipeline, scenarios before
the snapshot (R165), then the change report (R164).

**Before either:** commit 90.20.

**90.21, Cursor Gyro** (`findings/<date>-cursor-gyro/`)

1. Add `Cursor Gyro` at the end of the layer list: the gyro response, the two
   edge chords and the two menu presses.
2. `Transition Set 1`: the Select Release adds `Gyro`, then `Cursor Gyro`.
3. Add it to the Entry Points' clear list and the two `Gyro | … Modifier 2`
   releases. Rename Steering's Entry Points to `Stateful | …`.
4. Run `audit_build`. Read the new layer's "varies", "needs review" and
   "exit to review" entries and fix or accept each
   (`python3 -m tools.audit_layer … "Cursor Gyro"`).
5. `tests/test_stateful_transitions.py`: the Select Release adds `Gyro` below
   `Cursor Gyro`, the three exits, no gate of its own, and the four response
   settings.
6. `tests/test_scenarios_90_21.py`: enter from Base and from `Gyro`, with
   `Gyro` underneath both times; the menu-plus-click and both-sticks exits end
   in `Gyro`; the Modifier 2 tap ends in Base; a modifier hold over it; entry
   with both sticks out.

**90.22, Gamepad** (`findings/<date>-gamepad/`)

1. Exceptions register: R108, R158, R159, R162. Teach the Budget audit's
   banned-activator check to read the R108 entry. Add the new rule's row.
2. Simulator: Long Press and Double Press, modelled as A43 says. The scenarios
   that use them rest on A43.
3. Rename the clear transition; add the new `Transition Set 0` and `Gamepad`
   at the end of the layer list.
4. Retarget the two same-side click Releases in Base's Entry Points.
5. Add `Gamepad` to every Entry Point's clear list.
6. `audit_build`, then the review of the new layers' entries as above.
7. `tests/test_stateful_transitions.py`: all four gestures, three transitions,
   the closed-layer rule, the exit chord, the times.
8. `tests/test_scenarios_90_22.py`: both ways in; tap, double press and hold,
   hold on each menu button; exit with each of the four menu and click pairs;
   exit with the menu button released first; the Modifier 2 tap does nothing
   but LB and RB; entry and exit with `Gyro` underneath.

**Both:** `python3 -m tests.scenario --out findings/<date>-<slug>/` for the
unverified list (R167), the README for the build, the snapshot under
`versions/neptune/`.

## Documents to update

- `resources/Stateful Layer Transitions.md`: gesture map, transition table and
  titles, the exceptions table, "Tests".
- `resources/Layer Definition of Done.md`: R108, R157 to R159 and R162 rows,
  the new rule, the exceptions register.
- `resources/Steam Behaviour Assumptions.md`: A43 to A45; A20's note.
- `resources/Steam Input JSON Structure.md`: the allowed-activators section
  names the one exception.
- `todos.md`: the Gamepad, Cursor gyro and Global stateful behavior items.
- `docs/building.md`: the chain table and the layer count.
