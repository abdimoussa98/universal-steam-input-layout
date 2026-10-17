# Trial 90.76: the Entry Points' right stick without `requires_click`

Made on 2026-10-16 from the Neptune **90.75** snapshot, both layouts, on the
author's word: "remove this from the joystick on the entry points
"requires_click 0" then give me the 76 layout not tests. i just wanna test it so
the 9076 layout should not be published". A Deck trial off the line: not
installed, no snapshot under `versions/`, no tag, no tests. The working layouts
stay Neptune 90.75 and Ibex 1.0. [build_trial.py](build_trial.py) writes the
four files in this folder.

## Why

On the Deck the right stick types nothing in the Fn layers. The left stick
works there, and the July layout's right stick worked
(`MOST_RECENT_LAYOUT.post-fix-1.vdf`, the binds of
[the July post-fix layout](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json)).
Under the Fn layer, the menu Entry Point's right stick is the one group unlike
the left stick's and July's: since 90.10 a D-pad with `deadzone` 13276,
`requires_click` 0 and four empty directions, where July's was in mouse mode
with no directions. On the simulator both layouts type the keys.

## The change

| Layers | Group | 90.75 | 90.76 |
|---|---|---|---|
| `Menu Left: Entry Point`, `Menu Right: Entry Point`, `Stateful \| Menu Left: Entry Point`, `Stateful \| Menu Right: Entry Point`, `Menu Left!Right: Entry Point`, `Menu Right!Left: Entry Point` | right stick settings | `requires_click` 0 | no `requires_click` |

Nothing else differs from 90.75 in either variant, JSON or VDF: the binds,
`deadzone` 13276 and the empty directions stay.

## On the Deck

Confirm the configurator's title shows `:: 90.76` first. Hold Select for half a
second and push the right stick each way: `;` `'` `.` `,`, each with a Low bump.
If not: does the camera move, or does nothing happen?
