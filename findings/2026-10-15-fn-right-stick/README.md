# The right stick in the Fn layers (90.74)

Built on 2026-10-15 from the **90.73** snapshot, both layouts, on the author's
word: "these are the ones i want now go ahead and build these" ([plan](../../plans/2026-10-14-key-layer-click-and-fn-right-stick.md), part 2).
90 layers in each layout. Device status: **untested**.

| | Default | Alternative |
|---|---|---|
| Layers changed | 4 | 4 |
| Removes, adds | unchanged (2,965 and 469) | unchanged (3,023 and 469) |

## Why

The author, 2026-10-14: in the Fn layer the right stick's directions "arent
having haptic … nor are the correct binds there either". 2026-10-15: the left
stick there works, and `;` `'` `.` `,` are the keys wanted.

By the binds, all four Fn layers already had those keys, each with a Low bump
(haptic 1): in the JSON, in the exported VDF and in the July layout. The
simulator typed them from every mode with an Fn layer, and 3,000 random walks
found no layer taking the right stick from Fn other than the menu double-tap
windows. The two sticks' groups have the same shape. Only the right one stated
`deadzone` 13276 and `requires_click` 0; the Steam client shows Requires Click
for trackpads only. So this build copies the pattern that works: the left
stick's settings.

## The change

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against 90.73.

| Layers | Group | 90.73 | 90.74 |
|---|---|---|---|
| `Menu Left: Fn Layer`, `Menu Right: Fn Layer`, `Stateful \| Menu Left: Fn Layer`, `Stateful \| Menu Right: Fn Layer` | right stick settings | `layer` 1, `layout` 0, `edge_binding_radius` 21000, `edge_binding_invert` 0, `deadzone` 13276, `requires_click` 0 | the left stick's: the same without `deadzone` and `requires_click` |

The binds are unchanged: `;` up, `'` down, `.` right, `,` left, each chorded on
the layer's menu button with haptic 1, beside the R3 guard (button 20), and the
edge and touch cleanups.

## What is not known

The cause of the fault is not found. This build removes the only difference
from the stick that works. If the Deck still shows no keys or no bump, the next
step is a Deck observation with a key tester open: what the right stick types on
the first push and on a second, and whether the thumb was on the stick before
the menu button was held.

## Audits and tests

- Build audit: clean on both layouts.
- Full suite: 1,333 tests pass (25 expected failures).
- `tests/test_scenarios_90_74.py`: the group's settings and binds; each direction
  types its key from each Fn layer, in Base and in `Steering`, with the thumb
  landing after the hold and with it already resting on the stick.
- Scenario coverage: every layer is on the stack in a scenario; none changed is
  missing (R165). The assumptions not verified are in
  [unverified-assumptions.txt](unverified-assumptions.txt).

## On the Deck

Confirm the configurator's title shows `:: 90.74` first.

1. Hold Select for half a second, push the right stick each way: `;` `'` `.` `,`,
   each with a Low bump. The same with Start.
2. The same in `Steering` and in Cursor Gyro.
3. The same with the thumb already resting on the right stick before the hold.
