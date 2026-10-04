# Suggested fixes for the 12 hidden exits on 90.22

**Status, 2026-10-04:** the author chose **fix A**. It is built as 90.23
([record](../2026-10-04-tap-cover-stick-touches/README.md)). The rest of this
page is as it was written before the decision, when both fixes had been tried
on scratch copies of the two working layouts.

## What the audit reports

`python3 -m tools.audit_cleanups neptune/single-set-default_hold-gyro_latest.json`
fails on 12 hidden exits (R136), the same in both layouts:

| Layer the audit names | Layer left on | Exit that is lost |
|---|---|---|
| `Menu Left: Entry Point`, `Menu Right: Entry Point`, `Stateful \| Menu Left: Entry Point`, `Stateful \| Menu Right: Entry Point` | `RST: Entry Point`, `RST: Tap Cover`, `RST: Temporary Gyro` | The right-stick touch Release |

All 12 are one gap, in the layouts since 90.10.

## The cause

`Menu Buttons: Tap Cover` has its own right-stick group: D-pad mode, with an
empty binding on the outer edge and nothing on the touch. It was allowed to
inherit the stick touches as a cover-type layer (R116).

That works when the layer under it is a menu stick guard, which is also in
D-pad mode. Seven layers can land between the guard and the Tap Cover and keep
the right stick in mouse mode: `RTP: Entry Point`, `RTP: Click Entry Point`,
`LTP: Click Entry Point`, `Escape`, `Enter`, `Tab` and `Backspace`. Nothing is
inherited across a mode change (A2), so nobody answers the right-stick touch
and lifting the right thumb is not seen.

On the press simulator: right thumb on the stick, hold Select or Start, push
the left stick, touch the right pad, lift the right thumb. `Base > RST: Entry
Point` is left behind.

## Fix A (recommended): the Tap Cover binds both stick touches itself

`Menu Buttons: Tap Cover` gets a touch input on both sticks, the same as the
two stick guards have, without the guard's add of the Tap Cover:

| Stick | Activator | Settings | What it does |
|---|---|---|---|
| Right and left | Regular Press | Hold to Repeat | Removes both stick guards, the Tap Cover and the four menu Entry Points. This is the menu cleanup function |
| | Chorded Press | Select or Start, not interruptible | Empty binding. It is the cleanup's guard |
| Right | Release | No haptics | Removes `RST: Entry Point`, `RST: Tap Cover`, `RST: Temporary Gyro` |
| Left | Release | No haptics | Removes `LST: Entry Point`, `LST: Tap Cover`, `LST: Temporary Gyro` |

- **Why this one:** it is R116 with no exception for this layer. The Tap
  Cover no longer depends on what happens to sit under it.
- **Three entries on each input,** inside the budget (R108).
- **One behaviour changes.** In the stacks where a pad layer sits directly
  under the Tap Cover, the left-stick touch was answered by that pad layer.
  It is now answered by the Tap Cover. The thumb lift does the same thing.
  Touching the left stick with no menu button held now runs the menu cleanup,
  not the pad layer's.

## Fix B: the right-stick touch only

The same, on the right stick alone. It is the smallest change that clears the
12 pairs. The left-stick touch keeps being inherited, which works in every
stack today because every layer under the Tap Cover is in D-pad mode on the
left stick. It leaves the layer short of R116.

## What the trial showed

Scratch copies of both working layouts, the whole build audit on each:

| | 90.22 | Fix A | Fix B |
|---|---|---|---|
| Hidden exits | 12 | 0 | 0 |
| Exits to review | 0 | 0 | 0 |
| Other Cleanup audit findings | 0 | 0 | 0 |
| Budget, Window and Flow audits | pass | pass | pass |
| Simulator, the gesture above | `Base > RST: Entry Point` | `Base` | `Base` |

The two pairs "the Tap Cover over a stick guard's edge exit" are already
accepted in the exceptions register, so changing the Tap Cover adds nothing to
review.

## Not suggested

- **Removing the Tap Cover's stick groups.** They are there so that no guard
  can be added on top of it.
- **Keeping the pad layers from landing during a menu hold.** It would take a
  block on every pad input in the guards and the Entry Points, and the pads
  would go dead while a menu button and a stick are held.

## What applying it takes

- A new version (90.23) with its change report and snapshot.
- R116's list of cover-type layers in the Definition of Done:
  `Menu Buttons: Tap Cover` no longer inherits the stick touches.
- A scenario test for the gesture, since the layer changes (R165).
- A Deck check of the gesture on 90.22 first would also confirm A2 on a
  stick; it was verified on a pad.
