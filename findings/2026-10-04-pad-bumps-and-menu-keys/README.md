# Pad touch bumps, the middle-click mouse, Menu Keys and the Tap Cover resets (90.25)

**Status, 2026-10-04:** built and installed in `neptune/` as **90.25**, with the
snapshot in `versions/neptune/90.25/`. Device status: **untested**. The build
audit is clean and the tests pass.

The plan is [plans/2026-10-04-pad-bumps-and-menu-layer.md](../../plans/2026-10-04-pad-bumps-and-menu-layer.md),
built as one release (author, 2026-10-04). Twelve new layers, 78 to 90 per
layout. Where the build differs from the plan is in
[What differs from the plan](#what-differs-from-the-plan); four of those are
for the author to confirm.

During the build the author corrected the held-input rule: **a repeating
action always triggers** (A6). A binding with Hold to Repeat fires as its
layer lands on an input that is already held; it doesn't wait for its next
repeat, as the simulator and the docs had it. The simulator, A6, the pad
click scenarios and this build follow that
([what it changed](#the-held-input-rule-corrected)).

Select is Menu Left and Start is Menu Right.

## What it changes for the player

- **A pad touch bumps where a click would be the centre click.** A low bump
  when the thumb lands inside the centre, none nearer the rim. Both pads.
- **Middle mouse can drag.** With the right pad's centre click held, the
  cursor still moves.
- **Enter and Backspace from the menu buttons are a tap.** With Select held, a
  tap of Start types Enter; with Start held, a tap of Select types Backspace.
  A double tap and hold holds the key. Until 90.24 the press typed the key at
  once and held it.
- **Both menu buttons held for 150 ms enter `Menu Keys`**, with a beep and a
  strong pulse, from Base or `Gyro`; `Gyro` goes off. The D-pad is the arrow
  keys and A, B, X, Y are Enter, Escape, Backspace, Tab.
- **The centre click comes at once**, and it wins the ring where the two click
  ranges meet. Both follow from the corrected rule, not from a change to the
  click layers.

## The four parts

### 1. The bump: a hand-over layer on each pad

| Layer | Pad | What it binds |
|---|---|---|
| Base | Right: still a mouse. Left: now a D-pad | Only the touch, which adds the pad's Touch Entry Point (repeating, silent) |
| `RTP: Touch Entry Point`, `LTP: Touch Entry Point` | A D-pad that reads on touch | The Click Entry Point's own two Soft Presses on the ring, setting for setting. The inner one (inverted, 24996) repeats and bumps (`haptic_intensity` 1). The outer one (23000) has the 5 ms delay. Each removes the layer, then adds the pad's Entry Point. A touch Release removes the layer |
| `RTP: Entry Point` | A mouse, as before | Its touch, as before, and now the click's add of `RTP: Click Entry Point`, repeating every 50 ms |
| `LTP: Entry Point` (new) | Swipe mode | Base's four swipes, each removing this layer first; the click's add, repeating; a touch Release |
| `Steering` | A mouse whose touch is cleared | The click's add, with no repeat: no hand-over runs there |

Only the outer bind has the 5 ms delay, which gives the inner one priority
where the two ranges overlap (author, 2026-10-04). The inner bind and the
click's add repeat, so they fire on an input that is already held when their
layer lands (A6).

The hand-over's two binds are the Click Entry Point's, so the bump and the
click agree at every spot: whichever bind Steam fires first for a thumb there,
it is the same one in both layers. The plan's question of which radius the
bump uses is gone.

### 2. `RTP: Middle Click` is a mouse pad

Its pad group's mode went from `single_button` to Base's mouse mode. The
click's three entries and the touch Release are unchanged.

### 3. The chorded menu chains and `Menu Keys`

Each side is the Menu chain's recipe (R119) for the second button:

| Part | Select held, then Start | Start held, then Select | Built from |
|---|---|---|---|
| Entry Point | `Menu Left!Right: Entry Point` | `Menu Right!Left: Entry Point` | New: a Release that removes it and opens the window, the 150 ms hold, the hold's reset |
| Window | `Menu Left!Right: Double Tap` | `Menu Right!Left: Double Tap` | The pressed button's own window, typing Enter or Backspace |
| Second-press layer | `Menu Left!Right: Enter` | `Menu Right!Left: Backspace` | The pressed button's own (`Menu Right: Tab`, `Menu Left: Escape`) |
| Cover | `Menu Left!Right: Double Tap Cover` | `Menu Right!Left: Double Tap Cover` | The pressed button's own |

- The plain Entry Points add the chorded Entry Point in each of their four
  bindings that add the Fn layer, to land on top of it. The `Stateful` Entry
  Points don't, so inside `Steering` and `Cursor Gyro` both menu buttons type
  the key at once, as before.
- The hold removes every layer above Base, `Gyro` included, then adds
  `Menu Keys` with the beep flag and `haptic_intensity` 3.
- The window and the second-press layer block the first button, which is held
  under them. Its Release there ends its family: the window first, then the Fn
  layer and the Entry Point. The Fn layer's own Release of that button also
  removes the chorded Entry Point.
- The second-press layer and the cover keep the right stick in the Fn layer's
  mode, so the Entry Point's right-stick click isn't hidden.

`Menu Keys`:

| Input | Binding |
|---|---|
| D-pad, A B X Y | The key, and a chord on either stick being out that removes the layer with a beep |
| Both stick edges | A repeating chord on the other stick being out that removes the layer with a beep (`Cursor Gyro`'s exit) |
| Both stick clicks | Base's key, and a chord on Start or Select being held that runs the Entry Points' clear and adds `Transition Set 2` (`Gamepad`'s exit) |
| Start, Select, the modifier buttons, both stick touches | Empty |
| Everything else | Not bound: Base's |

### 5. The Tap Cover reset

The touch of `LST: Entry Point`, `RST: Entry Point` and `RTP: Entry Point` has
a third entry: a Regular Press that removes only its Tap Cover, Hold to Repeat
every 200 ms, not interruptible (R120). The register's exception for the pad's
touch is gone.

### 4. Tooling

`DEFAULT_EXTRAS` is 5. On 90.25, one layout:

| Extra presses | Stacks | Time, whole Cleanup audit | Memory at peak |
|---|---|---|---|
| 5 (default) | 827,266 | 4 s | 0.9 GB |
| 6 | 2,555,858 | 7 s | 2.3 GB |

The walk is about a third of 90.24's (7,728,211 stacks at six). I didn't trace
why. Fewer of Base's inputs add a layer now: the pad clicks and the left pad's
swipes moved off Base.

## What differs from the plan

For the author to confirm:

1. **The left pad has the hand-over layer too.** The plan put the bump on
   Base's own inverted ring. On the press simulator an inverted ring counts as
   on with no thumb on the pad, the same reading the click layers' backup
   removals use, so that bump would never come at a touch. The plan named the
   hand-over layer as the fallback. Base's left pad is still a D-pad, and
   `LTP: Entry Point` is as planned. One layer more than planned: twelve.
2. **`Menu Keys` has no Entry Points.** The plan reused the `Stateful` Entry
   Points for the menu-plus-click exit. An Entry Point's tap opens a Double
   Tap window, and a window that can land on `Menu Keys` must clear the face
   buttons and the D-pad on every stack, Base included (R140): they carry a
   layer command there, the stick-plus-button exit. So Start and Select are
   blocked and the exit is `Gamepad`'s chord on the stick clicks. It is an
   exception to R158 in the register.
3. **The stick touches do nothing in `Menu Keys`**, for the same reason: no
   stick-touch window may land there. Everything else does what it does on
   Base. So there is no Temporary Gyro in `Menu Keys`.
4. **The tap, hold and double tap are for the first press of a hold.** The
   chorded Entry Point removes itself on its Release, as every Entry Point
   does, which is what lets it pass R171 with three entries. Once its window
   has run out, with the first button still held, the next press is the Fn
   layer's own chord: the key at once, held for as long as the button is, as
   before 90.25. To reach `Menu Keys` again, let go of both and start over.

Decided by the author while building (2026-10-04):

- **Repeats, not delays.** The hand-over's inner bind and the click's add in
  the Entry Points repeat. The only 5 ms delay is on the outer ring bind.
- **The face buttons** are A Enter, B Escape, X Backspace, Y Tab.
- **One release.**

Settled by the rules, no decision needed:

- **The plain Entry Points add the chorded Entry Point, not the Fn layer**
  (already in the plan's final text).
- **The key is typed by the window**, 50 ms after it opens, as Tab and Escape
  are. Nothing types on a Release.
- **The window, the second-press layer and the cover are copies with their
  blocks**, not slimmed down. The blocks are what keeps a modifier or a menu
  layer from landing on them and hiding their exit (R136).
- **The stick-plus-button exit lets the press through.** The chord keeps
  `Menu Keys`' own key from being typed (A27). The removal then exposes Base's
  binding under the held button, and Base's key is typed (A11): F for A, 3
  for D-pad down.

## The held-input rule, corrected

A6 said a Hold to Repeat activator, in a layer that lands on an input already
held, "fires on its next repeat". The simulator read that as one repeat
interval later. The author, 2026-10-04: a repeating action always triggers.
It fires as the layer lands.

`steam_layout/simulator.py` now runs a repeating binding's commands when its
layer lands on a held input. A binding that a removal exposes is unchanged: it
fires at once or on its next repeat, which is A9. What that changed on the
simulator, in layers this build didn't touch:

| Before | Now |
|---|---|
| The middle click came 50 ms after the click, and a centre click shorter than that sent nothing | It comes at once |
| In the ring where the two click ranges overlap, the D-pad button won | The middle click wins: the outer bind's 5 ms delay gives the centre priority |
| A final click layer that landed on a pad no longer pressed stayed for one repeat | Its backup removal fires as it lands |
| `Steering \| LS: Entry Guard`, entered with the stick centred, left about 100 ms later | Its cleanup removes it as it lands |
| A reset first fired one interval after its layer landed | It also fires once as the layer lands; nothing is there to remove yet (R121) |

The open Deck check on which click wins the ring is closed by this.

## What it costs

Timed on the simulator, default layout. All of it rests on A13, the author's
report that any removal restarts a start delay that is counting.

- **Two new removals at the right pad**, each of which restarts every start
  delay that is still counting:

  - `RTP: Touch Entry Point` removes itself as the thumb lands (the hand-over).
  - `RTP: Entry Point` removes `RTP: Tap Cover` every 200 ms until the cover
    lands (the pad's reset, R120).

  A delay they push late then meets its own layer's reset as well, which in
  90.24 it always beat (300 ms before 350, 200 before 250):

  | Gesture | Layer waited for | Added by | 90.24 | 90.25 |
  |---|---|---|---|---|
  | 1. Hold L1, touch the right pad 200 ms in | `L1: Temp Cursor Gyro` | `L1: Modifier 0`, 300 ms delay | 300 ms | 700 ms |
  | 2. Hold Select, touch the right pad 60 ms in | `Menu Left: Fn Layer` | `Menu Left: Entry Point`, 200 ms delay | 200 ms | 450 ms |
  | 3. Touch the right pad, hold Select 60 ms later | `Menu Left: Fn Layer` | `Menu Left: Entry Point`, 200 ms delay | 200 ms after Select | 700 ms after Select |
  | 4. Hold L1, touch the left stick 200 ms in | `L1: Temp Cursor Gyro` | `L1: Modifier 0`, 300 ms delay | 300 ms | 300 ms: `L1: Modifier 0` binds the stick touches |

  The removals behind each row, with the time the waited-for layer is then
  due. "Not on" is a removal of a layer that isn't on the stack; the simulator
  counts it under A13 like any other.

  | Row | At | Layer that acts | Command | Waited-for layer due |
  |---|---|---|---|---|
  | 1 | 200 ms | `RTP: Touch Entry Point` | removes itself, adds `RTP: Entry Point` | 500 ms |
  | 1 | 350 ms | `L1: Modifier 0` | removes `L1: Temp Cursor Gyro` (not on) | 650 ms |
  | 1 | 400 ms | `RTP: Entry Point` | removes `RTP: Tap Cover` (not on) | 700 ms |
  | 2 | 60 ms | `RTP: Touch Entry Point` | removes itself, adds `RTP: Entry Point` | 260 ms |
  | 2 | 250 ms | `Menu Left: Entry Point` | removes `Menu Left: Fn Layer` (not on) | 450 ms |
  | 3 | 200 ms | `RTP: Entry Point` | removes `RTP: Tap Cover` (not on) | 400 ms |
  | 3 | 310 ms | `Menu Left: Entry Point` | removes `Menu Left: Fn Layer` (not on) | 510 ms |
  | 3 | 400 ms | `RTP: Entry Point` | removes `RTP: Tap Cover` (not on) | 600 ms |
  | 3 | 560 ms | `Menu Left: Entry Point` | removes `Menu Left: Fn Layer` (not on) | 760 ms, 700 after Select |

  In row 3 `RTP: Touch Entry Point` is gone before Select goes down, and
  `RTP: Tap Cover` lands at 550 ms, not 150, which ends the pad's reset.
  Scenario 90.24 K6 and 90.23 C1 show the same. Timed with one cause out:

  | Row | As built | `RTP: Entry Point` without its Tap Cover reset | If A13 is false |
  |---|---|---|---|
  | 1 | 700 ms | 650 ms | 300 ms |
  | 2 | 450 ms | 450 ms | 200 ms |
  | 3 | 700 ms | 200 ms | 200 ms |

  In row 1 the delayed add and `L1: Modifier 0`'s next reset are both due at
  700 ms. The simulator runs the add first; in the other order
  `L1: Temp Cursor Gyro` lands at 1000 ms.
- **A rim tap shorter than 5 ms opens no Double Tap window** on the right
  pad: the thumb lifts in the hand-over layer. In the centre the hand-over is
  done as the thumb lands.
- **After a clear under a held pad click the click comes back** either way
  (scenarios 90.16 X3 and 90.17 S1), with the touch bump and the click bump
  again. From 90.20 to 90.24 it came back only if Steam fires an exposed add
  (A9).
- **No bump on the left pad while `LTP: Entry Point` is still on** from a
  touch that ended with no swipe, no click and no touch Release (A47). The
  next stick touch removes it.

## Exceptions register

| Rule | Entry | Decided |
|---|---|---|
| R120 | Removed: the right pad's touch has the reset | Author, 2026-10-04 |
| R159 | `Menu Keys` isn't left by the Modifier 2 quick tap | Author, 2026-10-03 |
| R158 | `Menu Keys` has no Entry Points | Mine, building; to confirm |
| R157 | The existing entry names `Menu Keys`' entry and exits | Author, 2026-10-03 and 2026-10-04 |
| R139 | Eight entries: the inherited inputs of new and changed layers, read one by one | Mine, reading the Flow audit; to confirm |
| R136 | Two entries: each chorded window over its plain Entry Point, whose stick clicks it clears for 150 ms | Mine, reading the Cleanup audit; to confirm |

The hidden-exit check sets aside 247 pairs under the touchpad exception, 76
more than on 90.24: the three new pad layers are touchpad layers.

## Code that changed outside the builder

| File | Change |
|---|---|
| `steam_layout/fixes/cover_resets.py` | Accepts four or six second-press layers |
| `steam_layout/fixes/window_pads.py` | Reads the swipe keys from `LTP: Entry Point` when Base has no swipes |
| `steam_layout/simulator.py` | A repeating binding runs its commands when its layer lands on a held input (A6, as the author corrected it) |
| `tests/scenario.py` | `press_pad` rests the thumb until the touch's hand-over is done, then clicks; `rest=False` clicks with the touch |
| `steam_layout/cleanups.py` | `DEFAULT_EXTRAS` 5 |

The builder puts its class under the frozen `RequiredCleanups` one, so the
required cleanups (R169 to R171) run last, over the new layers. The chain's
second-press layers and covers get theirs before the fix pipeline reads them,
because its hidden-cleanup step has nothing to copy from a layer that is only
blocks.

## Checks

| Check | Result |
|---|---|
| Build audit (Budget, Window, Flow, Cleanup with five extra presses) | Clean on both layouts |
| `tests/test_pad_bumps_and_menu_keys.py` | 17 tests on the generated candidates |
| `tests/test_scenarios_90_25.py` | 25 scenarios: P1 to P8, T1 and T2, M1 to M8, K1 to K7 |
| Older scenarios changed | 33, for the corrected rule and the new stacks; each says so in a comment. Five simulator tests too |
| Every changed layer is in a scenario (R165) | Yes. `RST: Temporary Gyro` is the one layer no scenario reaches |
| [Change report](single-set-default_hold-gyro_latest-changes.txt) | 18 layers changed besides the 12 new ones |
| [Unverified assumptions](unverified-assumptions.txt) | 29, three of them new |

## On the Deck, in this order

1. **A46, the hand-over.** Touch each pad in the centre and at the rim, ten
   times each. A light bump every time in the centre, never at the rim, and
   the cursor or the swipes work after each touch. If the cursor doesn't move
   after a touch, the ring isn't read on a touch and the pads need 90.24.
2. **A48, the glide.** Flick the cursor and lift: it should still glide. If
   not, the reset comes off `RTP: Entry Point`.
3. **The ring.** Touch just inside the rim of the centre, where the two click
   ranges meet, and click: a bump, then the centre click. A D-pad button there
   means the outer bind fired first, against A6 as corrected.
4. **The chorded menu.** Hold Select and tap Start: one Enter. Double tap and
   hold: Enter held. Hold both: `Menu Keys` after the beep.
5. **`Menu Keys`' exits.** Both sticks out; a stick plus A (one F is typed,
   A11); Start held plus a stick click.
6. **A47.** Touch the left pad without swiping, lift, touch its centre again:
   a bump means swipe mode does give a touch Release.
7. The three checks of the
   [Tap Cover reset investigation](../../todos.md#investigations).

## Files

| File | What |
|---|---|
| `build_candidate.py` | The builder. `--vdf` also exports the candidates |
| `install_neptune.py` | Writes `neptune/`; `--deck` writes a trial copy to `deck/` |
| `default-…`, `alternative-pad-bumps-and-menu-keys.json` | The candidates, with numeric IDs; `.readable.json` has titles |
| `…-inputs-changed.txt` | What the required cleanups gave each new input |
| `…-changes.txt` | The change report against 90.24 |
| `manifest.json`, `neptune-installation.json` | Hashes |
| `unverified-assumptions.txt` | What rests on an assumption that isn't verified |
