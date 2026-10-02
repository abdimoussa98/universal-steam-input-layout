# Stateful transitions build (90.10)

**Status, 2026-10-01:** all six steps of the
[implementation plan](../../plans/2026-10-01-stateful-transitions-implementation.md)
are built and installed in `neptune/` as **90.10**, with the snapshot in
`versions/neptune/90.10/`. Device status: **untested**. The plan's two Deck
gates were assumed, at the author's request, and are the first checks in
[manual-testing.md](../../manual-testing.md#9010-stateful-transitions).

Design: [Stateful Layer Transitions](../../resources/Stateful%20Layer%20Transitions.md).

## Files

| File | What it is |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder. `Stateful` extends the frozen 09-30 `Lean` builder |
| [install_neptune.py](install_neptune.py) | Runs the fix pipeline and installs into `neptune/`. `--deck` writes a candidate to `deck/` and leaves `neptune/` alone |
| `default-…` / `alternative-stateful-transitions.json` | Builder output before the fix pipeline, with `.readable.json` in title form |
| [manifest.json](manifest.json) | Hashes, new layers and timing |
| [neptune-installation.json](neptune-installation.json) | Hashes of the installed files |

```bash
python3 findings/2026-10-01-stateful-transitions/build_candidate.py
python3 findings/2026-10-01-stateful-transitions/install_neptune.py --version 90.10
python3 audit_build.py
python3 -m unittest discover -s tests
```

The working layouts are generated. A hand edit in `neptune/` is lost on the
next install, and `test_working_layouts_are_this_build` fails on it. The
description is the exception: the install carries it forward from the
working file.

## What changed from 90.9

70 layers (69 in 90.9). One layer is added at the end and three are renamed
in place, so no runtime ID shifts.

| 90.9 title | 90.10 |
|---|---|
| `Steering \| Menu Left: Tap Cover` | `Menu Buttons: Left Stick Guard` |
| `Steering \| Menu Right: Tap Cover` | `Menu Buttons: Right Stick Guard` |
| `Steering \| LS: Entry Point` | `Steering \| LS: Entry Guard` |
| (appended) | `Menu Buttons: Tap Cover` |

- **Entry Points (step 1).** All four share one shape.
  - Both sticks are D-pads with edge radius 4915. The right stick's
    directions are empty, so the camera is off while a menu button is held.
  - Each stick click has only a Release. It runs the clear list (every layer
    except Base and `Gyro`, 69 removals) and adds the transition last.
  - Each stick edge is a chord on the held menu button that adds that
    stick's guard, repeating every 50 ms.
  - The Fn hold is 200 ms with a 250 ms reset (300 and 350 before). The
    other menu button only adds Fn; the Fn layers type Backspace and Enter.
  - Base's Start and Select are a single repeating add; the deflection chord
    is gone.
- **Fn layers (step 2).** No stick click binds and no stick-click mode shifts
  (four mode-shift groups removed per layout). The release and every recovery
  also remove the Tap Cover, both guards and Steering's Entry Point.
- **Guards and the menu Tap Cover (step 3).** As in the plan's tables. Both
  stick groups are D-pads in the guards and the cover. The guards' and the
  cover's menu releases also remove both Fn layers.
- **Transitions (step 4).** Written whole and identical in both layouts.
  `Transition Set 1` commits to Steering on the Start release;
  `Transition Set 0` is the clear. Neither has a stick-touch or edge
  recovery any more.
  - Every menu release in a transition beeps and gives a high haptic pulse
    (author, 2026-10-02), entering or clearing, with no on-screen
    notification. Each Release has `haptic_intensity` 3. The beep flag is on
    `add_layer Steering` for the entry, and on the transition's own
    `remove_layer` for the three releases that add nothing.
- **Steering's menu (step 5).** `Steering` adds its own Entry Points with a
  repeating press. The W and S layers send Tab and Escape. Left-stick south
  has the hold exit too.
- **Steering's left stick (step 6).**
  - Every Steering stick group uses radius 4915, not inverted. Each edge
    that changes layers does it on its Release.
  - `LS: Tap Cover` is only added inside Modifier 0 and 1. A driver press
    and entering or leaving Modifier 2 no longer add it.
  - The W and S layers add the modifier with a bind that repeats every
    50 ms.
  - Modifier 0 and 1: the entering direction holds into the Tap Cover
    (Any-driver chord, 250 ms, reset 300 ms). The opposite direction removes
    only the modifier. Left and right send A or D and add the Tap Cover. The
    edge Release opens the Double Tap window.
  - Every mapped input in Modifier 0 and 1 (face buttons, D-pad, Start,
    Select, both stick clicks) has two All-chords, left-stick deflection plus
    one driver, each carrying the key and the Tap Cover add in one array,
    and then the repeating cleanup.
  - The two Double Tap windows are Always On windows (nine in total). Each
    binds the stick and both drivers itself.

## Decided during the build

The plan left these open; the defaults it named were used.

- The W and S layers' modifier add repeats every 50 ms.
- The two All-chords in Modifier 0 and 1 are uninterruptible.
- Face buttons and the D-pad in Modifier 0 and 1 get the same two All-chords
  as Start and Select.
- A window's timeout is one entry: remove the window, then the scroll. That
  is the order the 09-30 build used for its chorded timeout.
- The release number is 90.10, the next after 90.9.

## What the fix pipeline derived

- `Menu Left: Double Tap` and `Menu Right: Double Tap`: left-stick up and
  down replaced with plain W and S, because Steering can now sit under them.
- The two Steering windows: both trackpads as in the other windows. In the
  default layout the trigger edges keep the mouse buttons. In the alternative
  the bumpers keep the mouse buttons and the trigger clicks are cleared.
- **Replace or clear** (author, 2026-10-01, after the first 90.10 build). The
  rule is "one possible keybind: replace; more than one: clear". The audit had
  counted a stack with only a layer command as a second, empty keybind. Under
  `Gyro Off Ramp Up` a trigger soft pull only removes that layer, so the audit
  cleared the soft pulls in every default window, as it had since 90.6.
  `blocks_needed` now ignores such stacks. Result: the trigger edges in all
  nine default windows are left and right mouse (18 binds), and the bumpers in
  the alternative's two Steering windows are left and right mouse (4 binds).
  Replaced binds no longer carry an empty `settings` block.
- `transition_set_0` is retired from the pipeline. The module stays as the
  record of the 90.6 patch.

## Checks run

- Build audit on both working layouts: Budget, Window and Flow audits pass.
  The Budget audit now also fails on a layer command on an inverted edge of
  a D-pad-mode stick (`inverted_edges`); 90.9 has seven and 90.10 has none.
- [tests/test_stateful_transitions.py](../../tests/test_stateful_transitions.py):
  27 tests on the builder output after the fix pipeline, both layouts.
- `test_audit_inheritance` and `test_double_tap_windows` cover the replace
  rule and the mouse buttons in the windows.
- Tests that pinned 90.9 behaviour were updated: `test_fixes`,
  `test_neptune_recovery`, `test_neptune_held_inputs`, `test_neptune_cursor`,
  `test_flow_inheritance`, `test_audit_inheritance`, `test_double_tap_windows`
  and `test_timed_spec`. `test_steering_lean.py` is unchanged: it tests the
  frozen 09-30 builder.
- Full suite: 684 tests pass, 155 skipped.

## Not verified

Nothing here ran on a Deck. Still assumed:

1. A stick input is inherited from a layer in the middle of the stack
   (gate 1). The guards and the Fn layers need it for the stick clicks.
2. An edge Release fires in a layer that was added while the stick was
   already out (gate 2). The guards, Steering's modifiers, its covers and the
   Entry Guard all end that way. There is no fallback design.
3. A key output fires on an input that was already held when its layer was
   added (Backspace and Enter in Fn, W and S in a Steering window).
4. A key output carries on when a removal exposes it under a held input (W
   and S when a Steering window times out).
5. An eaten delay comes back through its repeating reset when the covering
   layer is removed (Fn after a guard comes off).
