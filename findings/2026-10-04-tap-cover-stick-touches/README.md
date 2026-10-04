# The menu Tap Cover binds both stick touches (90.23)

**Status, 2026-10-04:** built and installed in `neptune/` as **90.23**, with the
snapshot in `versions/neptune/90.23/`. Device status: **untested**. The build
audit is clean and the tests pass.

How it was found, and the two fixes that were weighed:
[the hidden-exit check with six extra presses](../2026-10-03-simultaneous-cap/README.md)
and its [suggested fixes](../2026-10-03-simultaneous-cap/suggested-fixes.md).
The author chose fix A (2026-10-04).

Select is Menu Left and Start is Menu Right.

## The bug

Present from 90.10 to 90.22. `Menu Buttons: Tap Cover` has its own group on
each stick, in D-pad mode, with an empty binding on the outer edge. It had
nothing on the touch and inherited it from the menu stick guard under it, as a
cover-type layer may (R116).

A layer that lands between the guard and the cover can keep the right stick in
mouse mode: `RTP: Entry Point`, `RTP: Click Entry Point`,
`LTP: Click Entry Point`, `Escape`, `Enter`, `Tab` or `Backspace`. Nothing is
inherited across a mode change (A2). So no layer answered the right-stick
touch, and lifting the right thumb was not seen.

The gesture, on the press simulator:

| Step | Stack on 90.22 |
|---|---|
| Right thumb on the stick | `Base > RST: Entry Point` |
| Hold Start, push the left stick | … `> Menu Right: Entry Point > Menu Buttons: Left Stick Guard` |
| Touch the right pad before 200 ms | … `> RTP: Entry Point > Menu Buttons: Tap Cover > RTP: Tap Cover` |
| Lift the right thumb | Unchanged: `RST: Entry Point` stays |
| Let go of everything | `Base > RST: Entry Point` |

On 90.23 the lift removes `RST: Entry Point` and the gesture ends on `Base`.

## The change

One layer, two inputs, the same in both layouts
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).
`Menu Buttons: Tap Cover` gets a touch input on each stick. It is the stick
guard's touch input, without the guard's add of the cover in the Release.

| Stick | Activator | Settings | What it does |
|---|---|---|---|
| Both | Regular Press | Hold to Repeat | The menu cleanup function: removes both stick guards, the Tap Cover and the four menu Entry Points |
| Both | Chorded Press | Select or Start (mask 20480, Any), not interruptible | Empty. It guards the cleanup while a menu button is held (R133) |
| Right | Release | No haptics | Removes `RST: Entry Point`, `RST: Tap Cover`, `RST: Temporary Gyro` |
| Left | Release | No haptics | Removes `LST: Entry Point`, `LST: Tap Cover`, `LST: Temporary Gyro` |

Three entries on each input, inside the budget (R108). No layer was added, so
no runtime ID moved.

## What it changes for the player

- **The right-thumb lift is seen** in the stacks above.
- **A stale menu flow clears itself in one more case.** If the menu button's
  release is missed while the Steam menu is open (A25) and a pad layer sits
  under the cover, touching either stick now removes the stale menu layers. On
  90.22 the touch did nothing there and they stayed (scenario C3).
- **Nothing else.** Where the cover sits directly on a guard, the guard's touch
  input did the same thing before.

## Rules, exceptions and assumptions

| What | Change |
|---|---|
| R116 | `Menu Buttons: Tap Cover` no longer inherits the stick touches. It is still a cover-type layer by its title; the other cover-type layers are unchanged |
| R136 | The 12 hidden exits on 90.22 are gone. No exception was added |
| Exceptions register | Unchanged. The two accepted pairs "the Tap Cover over a stick guard's edge exit" are as they were |
| Assumptions | None new. The fix makes the layer stop depending on A2 here; A2 was verified on a pad, not on a stick |

## Checks

| Check | Result |
|---|---|
| Build audit (Budget, Window, Flow, Cleanup with six extra presses) | Clean on both layouts |
| Hidden exits | 12 on 90.22, 0 on 90.23 |
| Installed layout against the scratch copy that was audited before the decision | Identical apart from the title |
| Simulator, the gesture above with Start and with Select | Ends on `Base` |

## Scenarios and tests

`tests/test_scenarios_90_23.py`:

- **C1** (R116, R117, R136; rests on A2, A7): the gesture above with each menu
  button, and its mirror with the left thumb. The lift removes that side's
  trio and nothing else.
- **C2** (R116; rests on A27): with a menu button held and the cover on top,
  touching and lifting the right stick moves no layer.
- **C3** (R116, R133; rests on A2, A25, A27): a stale cover over a pad layer is
  cleared by a touch of either stick, and the next Start tap is normal.

`tests/test_tap_cover_stick_touches.py`, on the generated candidates: the
cover's two touch inputs, that its cleanup and chord are the stick guards',
that one layer changed against 90.22, and that `neptune/` is this build (R156).

`tests/test_cleanups.py` asserts that the working layouts have no hidden exit;
it failed on 90.22 on purpose and passes now.

## Files

- `build_candidate.py`: the builder. It extends the 90.22 builder, which stays
  frozen.
- `install_neptune.py`, `*-tap-cover-stick-touches.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.22 (R164).
- `unverified-assumptions.txt`: the assumptions that aren't verified, with
  what rests on each (R167).
