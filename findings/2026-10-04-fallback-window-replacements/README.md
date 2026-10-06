# Replacements in the fallback's window (90.32)

**Status:** built and installed as 90.32 on 2026-10-04. Not run on the Deck.
**Walked back in [90.33](../2026-10-05-steering-fallback-guard/README.md)**,
which deleted the window. Its scenario tests are in
[archived/fallback-window](../../archived/fallback-window/README.md).
Build audit clean. Extends the
[90.31 builder](../2026-10-04-fallback-window/README.md), which stays frozen.

One change, to one layer. 90 layers, as in 90.31.

The **fallback's window** is `Steering | LS: Fallback Window`: the one second
after the left stick goes up or down in `Steering` with no driver held. A
**driver** is R1 or L1 in the default layout and a trigger in the alternative.

## What changed

The author, 2026-10-04, after 90.31 was built: "we should just be blocking
until the window is completed ... tab and escape, like those can be an
override. And then we can have the bumpers be scroll override."

| Input in the window | 90.31 | 90.32 |
|---|---|---|
| Start | Removed the window; the Fallback Hold then cleared the Steering layers | Tab |
| Select | The same | Escape |
| The W driver (R1, or the right trigger) | The same | Scroll up |
| The S driver (L1, or the left trigger) | The same | Scroll down |

No layer changes on those four inputs now. The only things that change a layer
in the window are its timer and its Releases (up, down, the edge, the
touches), which take the Fallback Hold along.

`Steering | LS: Fallback Hold` is as it was in 90.31.

## What it does

With the stick held up:

| You | 90.31 | 90.32 |
|---|---|---|
| Tap Start inside the second | Out of `Steering` | Tab. `Steering` stays and the second runs on |
| Tap a driver inside the second | Out of `Steering` | One scroll step. `Steering` stays |
| Press one inside the second and hold it past the end | Out at the press | Out when the second ends |
| Press one after the second | Out at the press | The same |

The third row is the Fallback Hold answering a button that is already down.
Its bind for the drivers and the menu buttons repeats, so it fires there at
once or within 50 ms (A6, and A9 either way).

## Why it is sounder

- It is what every other window does: an input that would change a layer gets
  its replacement (R140).
- 90.31 needed the Fallback Hold's bind to fire on a button that was pressed
  over the window. That path is only left for a button held past the second.
- A stray press in the first second no longer leaves `Steering`.

## What it costs

- A driver pressed in the first second sends a scroll step to the game.
- Start and Select type Tab and Escape inside the second and leave `Steering`
  after it.

## How it is built

[build_candidate.py](build_candidate.py) puts one class in front of the 90.31
builder's. Its `finish` replaces the four binds in the finished layout. It
finds the two drivers from the layers `Steering` adds for them, and stops the
build if any of the four is not the press that removes the window.

## Rules

| Rule | Change |
|---|---|
| R137 | In the window a driver scrolls and Start and Select type their keys, so nothing lands over the Fallback Hold there |
| R156 | The working layouts are this builder's output; `test_fallback_window_replacements.test_working_layouts_are_this_build` |

The description says what the drivers and the menu buttons do inside the
second and after it.

## Tests

- `tests/test_fallback_window_replacements.py`: the four outputs; only the
  timer and the Releases change a layer in the window; the Fallback Hold is as
  in 90.31; against 90.31 only those four inputs change.
- `tests/test_scenarios_90_32.py`, R1 to R4: a tap inside the second; several
  taps and letting go; a button held past the second; a press after it.
- Changed with it: 90.31 F4, 90.11 F6 and F8, 90.10 D4.

## On the Deck

After [90.31's order](../2026-10-04-fallback-window/README.md#on-the-deck-in-this-order),
with its step 4 replaced by:

1. Hold the stick up and tap Start, Select and each driver inside the first
   second: Tab, Escape and one scroll step each, and still in `Steering`.
2. Hold the stick up, press a driver inside the second and keep it down: out
   of `Steering` when the second ends.
3. Hold the stick up past the second and press a driver: out at once.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-binds-changed.txt` | The four binds |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.31 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
