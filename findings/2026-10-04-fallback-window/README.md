# The fallback window, the outer ring and the Entry Guard (90.31)

**Status:** built and installed as 90.31 on 2026-10-04. Not run on the Deck.
**Walked back in [90.33](../2026-10-05-steering-fallback-guard/README.md)**,
which deleted the window and the Fallback Hold; parts 2 and the builder stay.
Its scenario tests are in [archived/fallback-window](../../archived/fallback-window/README.md).
[90.32](../2026-10-04-fallback-window-replacements/README.md) changed what a
driver or a menu button does inside the window, the same day.
Build audit clean. Extends the
[90.30 builder](../2026-10-04-window-releases-and-tap-cover-resets/README.md),
which stays frozen. The plan, with the author's words, is
[plans/2026-10-04-fallback-window.md](../../plans/2026-10-04-fallback-window.md).

The **fallback** is what the left stick does in `Steering` with no driver
held. A **driver** is the button that drives: R1 and L1 in the default layout,
the triggers in the alternative. A **window** is a layer with an Always On
timer that removes it.

One layer is added, at the end of the list: 90.

## 1. The fallback's second is a window

### What was wrong

- The fallback's exit was written as a 1500 ms delay with a reset at 1550 ms.
  The editor stops at 1000 ms, so both probably ran at 1000 ms and collided.
- The Fallback Hold carried the key, the timer, the pulse and the reset, and
  all of it had to start as the layer landed on a stick that was already out.
  On the Deck the author found up and down dead at times and the exit
  unreliable.

### What it does now

`Steering`'s up and down add `Steering | LS: Fallback Hold` and then, on top,
the new `Steering | LS: Fallback Window`.

In the window, the first second:

| You | What happens |
|---|---|
| Hold up or down | W or S, with a strong pulse every 250 ms |
| Let up or down go, or the edge lets go, or a thumb leaves a stick | The window goes, then the Fallback Hold. `Steering` stays |
| Press a driver or a menu button | The window goes; the Fallback Hold underneath clears the Steering layers |
| Stay for the full second | The window removes itself and the Fallback Hold is on top |

In the Fallback Hold, after the second:

| You | What happens |
|---|---|
| Keep holding | W or S |
| Let up or down go | The Steering layers are cleared, with the beep and the strong pulse |
| Press a driver or a menu button | The same |
| Touch a stick, or push the right stick out, with the left stick at centre | The same: the cleanup binds, for a Release that was missed |

So leaving `Steering` is: hold up or down for a full second, then let go.

### The binds

`Steering | LS: Fallback Window`:

| Input | Bind |
|---|---|
| Always On | 1000 ms: removes the window |
| Up, down | W or S; a chord on the left stick being out that pulses every 250 ms; a Release that removes the window, then the Fallback Hold |
| Left, right | A, D |
| Outer edge | A Release that removes the window, then the Fallback Hold |
| Both stick touches, the right pad's touch | A Release that removes the window, the Fallback Hold and that input's own touch layers |
| The two drivers, Start, Select | A press that removes the window, and nothing else |

`Steering | LS: Fallback Hold`:

| Input | Until 90.30 | 90.31 |
|---|---|---|
| Up, down | W or S; the 1500 ms exit; a Release that removed the layer | W or S; a Release that clears the Steering layers |
| Outer edge | The pulse; the reset | Nothing |
| The two drivers | Nothing of its own | A repeating press that clears the Steering layers |
| Start, Select | Tab or Escape with the stick out; a cleanup bind | A repeating press that clears the Steering layers. No Tab or Escape |
| Both stick touches, the right stick's edge | A cleanup bind that removed the layer | A cleanup bind that removes the layer and `Steering`, held back while the left stick is out |

The driver and menu binds in the Fallback Hold repeat. In the window the
button is pressed over the window, which then goes; a repeating bind is what
fires on a button that is already down (A6, and A9 either way).

### Two things the fix pipeline did

- **It shortened the lists.** The Release on up and down removes the Fallback
  Hold, the window and `Steering`: nothing else of Steering can be on while
  the Fallback Hold answers the stick. The driver and menu binds keep the
  whole list.
- **It first took `Steering` out of the cleanup binds.** A cleanup function
  never removes a stateful layer (R131). The author asked for these to clear
  the Steering layers, so the register has an entry that keeps the removal,
  and the Cleanup audit now honours such an entry for a removal that is
  outside the guard. Before, it only did for one that is never there.

## 2. The outer ring radius

The editor's Outer Ring Command Radius on a D-pad goes from 10,000 to 32,000
(author, 2026-10-04). The layouts stated 4915 on the left stick in 34 layers,
and on the right stick 4915 in 7 and 7209 in 21: 62 stick groups.

All 62 state no radius now, and "not inverted". Steam's default applies. The
new window states none either.

What the edge means afterwards: it is pressed near the rim, not a quarter of
the way out.

| Layers | What changes |
|---|---|
| The four single modifiers | Both sticks at the rim, with the bumper held, end the cursor response |
| The menu Entry Points and their stick guards | Only a stick at the rim holds the Fn layer off |
| `Cursor Gyro`, `Menu Keys` | Both sticks at the rim leave the layer |
| The Steering stick modifiers | Left as they are: they end on the edge's Release, so a push that stops short of the rim leaves the map on until the driver is let go |
| Every cleanup bind on a stick's edge | It fires at the rim |

## 3. The Entry Guard

`Steering | LS: Entry Guard` ended only on the edge's Release. Up, down, left
and right each have a Release that removes it now, so any push ends it.

## What it rests on

| Assumption | Where |
|---|---|
| A36, unverified: a chord is decided as its binding starts answering a held input | At the 1000 ms mark the Fallback Hold's cleanup binds start answering thumbs resting on the sticks. The chord on the left stick being out must hold them back, or `Steering` ends there with the stick still up |
| A50, new, unverified: a stick group with no radius uses Steam's default | The 62 stick groups |
| A11, unverified: a key fires when a removal exposes it under a held input | W carries on past the second |
| A8, unverified: a stick's Release fires in a layer added while the stick was out | The window's Releases, and the exit |
| A10, reported: a key fires as its layer lands on a held input | W and S in the window |

After a missed Release the Fallback Hold stays on with the stick at centre.
Its guard chord latched while the stick was out (A17), so the cleanup binds
fire on the next fresh touch of a stick, not on the thumb that is still down.

## How it is built

[build_candidate.py](build_candidate.py) puts one class in front of the 90.30
builder's. Its `finish` changes the finished layout: the radius first, then
the new layer as a copy of `Steering | LS Up: Double Tap`'s groups, then
`Steering`, the Fallback Hold, the clear lists and the Entry Guard. The 31
binds that clear both Steering windows clear the new one too. Each step checks
what it expects to find and stops the build otherwise.

The window gets its blocks from the fix pipeline at install, like any window.

## Rules, register and assumptions

| What | Change |
|---|---|
| R173, new | A value in a layout is one the editor can set: at most 1000 ms, and a D-pad radius from 10,000 to 32,000 |
| R137 | The window is the one layer added over the Fallback Hold; in the Fallback Hold a menu button leaves `Steering` |
| R131, R132 | A register entry keeps `Steering` in the Fallback Hold's cleanup binds |
| R156 | The working layouts are this builder's output |
| R170 | The register's reason names the Entry Guard's new Releases |
| A50 | New |
| The Cleanup audit | Honours a kept removal that is outside the guard |
| The description | How to leave Steering by the stick; Fn waits only while a stick is at its rim |

## Tests

- `tests/test_fallback_window.py`: the new layer; `Steering`'s add; the
  window's timer, keys, pulse and exits; the Fallback Hold's binds; no radius
  the editor can't set; no delay or repeat rate over 1000 ms; the Entry
  Guard; what differs from 90.30.
- `tests/test_scenarios_90_31.py`: F1 to F8, the fallback; G1, the Entry
  Guard.
- The fallback scenarios of 90.11 and 90.30 and the older static tests
  change with it; each says so in a comment.

## On the Deck, in this order

1. **The one-second mark.** In `Steering`, rest both thumbs on the sticks and
   hold up for three seconds: W the whole time, and still in `Steering`. If
   `Steering` ends at about one second, the chord on the left stick being out
   is being missed (A36).
2. **The exit.** Let go: out of `Steering`, with the beep.
3. **Inside the second.** Push up and let go quickly, several times:
   `Steering` stays, W each time. Roll to A and back.
4. **A driver and a menu button.** Hold up and press one, inside the second
   and after it: out of `Steering` each time.
5. **The Fn layer and the sticks.** Outside `Steering`, rest a thumb on a
   stick and hold Select: the Fn beep at 200 ms. With that stick at the rim:
   no Fn until it comes off the rim.
6. **The Entry Guard.** Enter `Steering` with the stick held up, let it go,
   and push up again: the fallback's pulses start.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-binds-changed.txt` | What each step did |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.30 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
