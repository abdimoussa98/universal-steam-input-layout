# The Steering fallback guard (90.33)

**Status:** built and installed as 90.33 on 2026-10-05. Not run on the Deck.
[90.34](../2026-10-05-steering-four-way-and-open-edges/README.md) changed three
things the same day: the guard comes at once, not after 100 ms; `Steering`'s
left stick is four-way; and `Steering` no longer blocks the stick edges. The
tables below show 90.33.
Build audit clean. Extends the
[90.32 builder](../2026-10-04-fallback-window-replacements/README.md), which
stays frozen. The plan, with the author's words, is
[plans/2026-10-04-steering-fallback-layer.md](../../plans/2026-10-04-steering-fallback-layer.md).

It walks back the fallback window of 90.31 and 90.32, after the
[July layout](../2026-10-04-july-stick-clears/README.md#4-its-fallback).

- **Steering base:** `Steering` with nothing of its own on top.
- **Bumper:** one of the modifier pair, which are also Steering's drivers:
  L1 and R1 in the default layout, the triggers in the alternative.
- **The fallback guard:** `Steering | LS: Fallback Guard`, the layer the left
  stick's up and down bring in when no driver is held.

88 layers: two fewer than 90.32.

## What it does

In Steering base:

| You | What happens |
|---|---|
| Push the stick up or down, no driver held | After 100 ms: a strong pulse, the fallback guard, and W or S |
| Press a driver inside those 100 ms | The driver's layer takes the stick; no guard |

In the fallback guard:

| You | What happens |
|---|---|
| Stick up, down | W, S, at once |
| Stick left, right | A, D, from `Steering` |
| Let the stick go | The guard stays |
| Press a bumper with the stick out | Its Gyro modifier, over the guard. W or S carries on |
| Press a bumper with the stick at centre | A strong pulse, the guard goes, and the bumper drives |
| Let that bumper go with the stick up or down | Steering base, so the guard comes on again with its pulse |
| Quick tap of both bumpers | Everything is cleared, to Base, with the beep |
| Start or Select | `Steering`'s own: a tap is Tab or Escape, a hold is Fn |
| A menu button held plus a stick click | The clear: `Steering` and the guard go, `Gyro` stays |
| Put a thumb on either stick, left stick at centre | The guard goes: its cleanup function |

Leaving `Steering` by holding the stick is gone.

## What differs from the plan

- **After a bumper hold with the stick let go, the guard goes.** The plan said
  it would still be on. In the simulator the guard's cleanup function fires
  when the modifier leaves: the thumb is resting on the stick at centre, and
  the guard's touch bind starts answering it again. The same happens after a
  menu button is let go with the stick at centre. On the Deck it may stay
  instead (A36, A9). Either way the next bumper at centre drives, and the
  next push up brings the guard back.
- **A right thumb put on the right stick also removes the guard** when the
  left stick is at centre. The plan's row said "a thumb put back on a stick";
  this is the common case of it.
- **The register can scope an entry to a build.** The frozen builders read
  the same exceptions register as they build. An entry made for 90.33 changed
  what the 90.11 step produced, and taking out the Fallback Hold's entries
  stopped the 90.24 step. An entry can now name a layer it holds with
  (`where`).
- **The two window scenario files are archived**, not rewritten:
  [archived/fallback-window](../../archived/fallback-window/README.md).

## The binds

`Steering`:

| Input | 90.32 | 90.33 |
|---|---|---|
| Up, down | A repeating press that adds the Fallback Hold and its window | A chord on the left stick being out, 100 ms delay, strong pulse, uninterruptible: adds the guard. A press repeating every 150 ms, uninterruptible, silent: removes the guard (its reset, R120) |
| Each driver | A repeating press that removes the Fallback Hold and the Entry Guard and adds the driver's layer | A repeating press that adds the driver's layer |
| Each driver, the other one held | Removes the Entry Guard | Nothing: the other driver's layer answers |

`Steering | LS: Fallback Guard`, which was `Steering | LS: Entry Guard`:

| Input | 90.32, as the Entry Guard | 90.33 |
|---|---|---|
| Up, down | W or S, and a Release that removes the guard | W or S, uninterruptible. No Release |
| Left, right | A or D, and a Release that removes the guard | Not bound |
| Left stick's edge | A Release that removes the guard | Not bound |
| Each bumper | Not bound | A chord on the left stick being out, repeating every 50 ms, uninterruptible: adds its Gyro modifier. A press repeating every 50 ms, strong pulse: removes the guard |
| Start, Select | Tab or Escape with the stick out; a cleanup function | Not bound |
| Both stick touches | A cleanup function that removes the guard, held back while the left stick is out | The same |
| Right stick's edge | The same cleanup function | Not bound |

`Transition Set 1`: entering `Steering` adds `Steering` alone.

The two `Gyro | … Modifier 2` layers, the Release of each bumper:

| | Removes |
|---|---|
| 90.32 | Itself, the three Tap Covers, the two Gyro modifiers, `Cursor Gyro`, `Gyro` |
| 90.33 | The same, and the other Gyro Modifier 2, the four Base modifiers, the guard, `Steering` with the beep |

Deleted: `Steering | LS: Fallback Hold` and `Steering | LS: Fallback Window`,
with the 47 removals of them in other layers. The Fallback Hold was in the
middle of the list, so the 18 layers after it moved up by one and the presets
are numbered in a row again.

## What it rests on

| Assumption | Where |
|---|---|
| A36, unverified: a chord is decided as its binding starts answering a held input | The guard's chords on the left stick being out: a bumper's choice between the modifier and ending the guard, and the hold-back of the touch cleanup |
| A10, reported: a key fires as its layer lands on a held input | W or S as the guard comes on |
| A12, verified: a repeated removal restarts a delayed add | The add's reset |
| A14, unverified: a delay starts again when a removal exposes it | The guard coming back after a driver is let go with the stick up. The reset repeats, so it restarts either way |
| A15, verified: a layer that binds an input cancels its running delay | A driver inside the 100 ms |
| A6, reported: a repeating bind fires as its layer lands | The guard at entry with the stick held up |
| A49, unverified: the beep is the second flag | The quick tap's beep |

A8 and A11 no longer carry anything in the fallback.

## How it is built

[build_candidate.py](build_candidate.py) puts one class in front of the 90.32
builder's. Its `finish` changes the finished layout: it renames the Entry
Guard, rewrites `Steering`'s up, down and driver binds and the transition's
commit, deletes the window and the Fallback Hold, rebuilds the guard, and
extends the four quick taps. Each step checks what it expects to find and
stops the build otherwise.

## Rules, register and tools

| What | Change |
|---|---|
| R120 | The guard's add has its reset |
| R125, R173 | New examples |
| R132 | Two register entries keep the Base modifiers and the other Gyro Modifier 2 in the quick tap, by the author's words. The Fallback Hold's entry stays for the frozen builds |
| R137 | No temporary guard is left: the fallback guard has no Release to hide |
| R157, R159 | The hold exit is out; the Modifier 2 clear also runs from the Gyro modifiers |
| R170 | The Entry Guard's and the Fallback Hold's entry stays for the frozen builds |
| R156 | The working layouts are this builder's output |
| The register | `where`: an R132 or R169 to R171 entry holds only on a layout that has the named layer |
| A8, A10, A11, A14, A15, A16, A36, A50 | What rests on each is rewritten |
| The description | Steering's paragraph: walking, and how a bumper ends it |

## Tests

- `tests/test_steering_fallback_guard.py`: the two deleted layers and the
  rename; `Steering`'s add, reset and drivers; the entry; the guard's binds;
  what a bumper brings in leaves up and down alone; the quick tap's lists and
  flags; the editor's limits; what differs from 90.32.
- `tests/test_scenarios_90_33.py`: G1 to G4, the stick; B1 to B5, the
  bumpers; L1 to L5, leaving and the menu buttons; C1 and C2, the cleanup.
- Rewritten: 90.10 D4, 90.15 M1. Retired: 90.11 F1 to F9 and F11, 90.15 M2,
  90.30 F1 and F2, and the 90.31 and 90.32 files.

## On the Deck, in this order

1. In `Steering`, push up: a pulse and W after a tenth of a second. Let go
   and push again: W at once, no pulse.
2. Stick at centre, press R1: a pulse, and R1 drives.
3. Hold up, tap L1: a scroll step, W the whole time, no pulse.
4. Hold up, hold L1, let the stick go, let L1 go, press R1: R1 drives.
5. Hold up, quick tap of both bumpers: Base, with the beep. Try it with
   `Gyro` on and with it off.
6. Hold Select and click a stick: `Steering` is gone and `Gyro` is as it was.
7. Press R1 and push the stick up together, several times: R1 drives each
   time and no pulse comes.
8. Enter `Steering` with the stick held up: W after the pulse. Enter it with
   the stick held left and press R1: it drives.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-binds-changed.txt` | What each step did |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.32 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
