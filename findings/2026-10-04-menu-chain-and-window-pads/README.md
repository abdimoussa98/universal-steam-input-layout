# The menu chain on every press, and the right pad's touch in a window (90.28)

**Status:** built and installed as 90.28 on 2026-10-04. Not run on the Deck.
Build audit clean; the tests pass. Extends the
[90.27 builder](../2026-10-04-pad-bump-removal/README.md), which stays frozen.

Two changes the author approved on 2026-10-04. Select is Menu Left and Start
is Menu Right.

## 1. The chorded menu chain runs on every press

### What was wrong

The author's report from the Deck, on 90.26: holding one menu button and
tapping the other "just fires enter. Or backspace", and the hold didn't reach
`Menu Keys`.

In 90.25 the chain's Entry Point (`Menu Left!Right: Entry Point`) was added
once, together with the Fn layer, and removed itself on its first Release.
Nothing put it back while the first button stayed held. So only the first
press of the second button went through the chain. Every later press went to
the Fn layer's own bind, which typed the key at once and held it: no tap, no
double tap, and no `Menu Keys`.

That was my change to the author's design, which had the Fn layer add the
entry point ("from the FN layer, it'll automatically add the menu layer",
2026-10-03). I had put it beside the Fn layer to leave the Fn layers alone,
because `Steering` and `Cursor Gyro` share them, and listed the result as a
deviation to confirm. The scenarios only tried the first press.

### What changed

| Layer | Until 90.27 | 90.28 |
|---|---|---|
| `Menu Left: Fn Layer`, Start with Select held | Types Enter | Adds `Menu Left!Right: Entry Point` |
| `Menu Right: Fn Layer`, Select with Start held | Types Backspace | Adds `Menu Right!Left: Entry Point` |
| `Menu Left: Entry Point`, `Menu Right: Entry Point`: the 200 ms hold and the two stick-touch Releases | Add the Fn layer and the chain's Entry Point | Add the Fn layer alone, as before 90.25 |
| The same layers: the other button's press, before the Fn layer is up | Adds the Fn layer, then the chain's Entry Point | The same |
| `Stateful \| Menu Left: Entry Point`, `Stateful \| Menu Right: Entry Point` | Add the shared Fn layers | Add `Stateful \| Menu Left: Fn Layer` and `Stateful \| Menu Right: Fn Layer`, new |

The two new layers are the Fn layers as they were: the other button types its
key at once. So `Steering` and `Cursor Gyro` behave as before, and `Menu Keys`
is still entered from Base and `Gyro` only. They are at the end of the layer
list: 89 layers, and no runtime ID moves.

The chain itself (its Entry Point, window, second-press layer and cover) and
`Menu Keys` are unchanged.

### What it does now

Hold Select, tap Start, then hold Start, on the simulator:

| Time | You | What happens |
|---|---|---|
| 0 ms | Select down | `Menu Left: Entry Point` |
| 200 ms | | `Menu Left: Fn Layer` |
| 400 ms | Start down | The Fn layer adds `Menu Left!Right: Entry Point` |
| 460 ms | Start up | The Entry Point removes itself and opens `Menu Left!Right: Double Tap` |
| 510 ms | | The window types Enter |
| 610 ms | | The window ends; the Fn layer is on top again |
| 860 ms | Start down | The Fn layer adds the Entry Point again |
| 1060 ms | Start still held | Everything is cleared, `Menu Keys` comes on, beep |

### What it rests on

The chain's Entry Point now always lands on a button that is already down:
the press that adds it. That is the shape of Base adding `Menu Left: Entry
Point` on Select.

- Its Release fires in the layer that landed (A7, verified).
- Its 200 ms delay runs from the landing (A6 and A16; A6 verified).
- Its chord with the first button is read as the layer lands (A36,
  unverified). The author's observation that the Fn layer typed its key when
  it landed on a held button (A10) is the same mechanism.

It also takes out a fault I suspected and couldn't confirm. When the second
button went down before the Fn layer was up, the Fn layer and the Entry Point
landed together, and the Fn layer's key bind may have typed as it landed (A10).
The Fn layer has no key there now, and a layer command doesn't fire on a
button that is already down (A5).

## 2. In a window the right pad's touch follows the stick touches

The author, 2026-10-04: the Double Tap windows block the pad clicks and
replace the left pad's swipes with their keys, and that should be a known list
of replacements used every time a pad is overridden. For the right pad's
touch, which has an Entry Point, "we should follow the same pattern that the
RST and LST are doing".

| Pad input | In Base | Known replacement |
|---|---|---|
| Left pad, the four swipes | Add `Escape`, `Enter`, `Tab`, `Backspace` | Type the key directly |
| Left pad, click | Adds `LTP: Click Entry Point` | Blocked |
| Left pad, touch | Nothing | Cleared |
| Right pad, click | Adds `RTP: Click Entry Point` | Blocked |
| Right pad, touch | Adds `RTP: Entry Point` | No press bind, and a Release that removes the window, then `RTP: Entry Point`, `RTP: Tap Cover`, `RTP: Circular Scroll` |

Only the last row is new; it was a block. The list is rule R172, with R149
reworded to point at it.

Thumb resting on the right pad, tap L1, lift the thumb inside the window:

| | Until 90.27 | 90.28 |
|---|---|---|
| Lift the thumb | Nothing fires | The window, `RTP: Entry Point` and `RTP: Tap Cover` go |
| End | `RTP: Entry Point` and `RTP: Tap Cover` left on with no thumb on the pad | Base |

A touch that starts inside a window still does nothing until the window ends.

Which windows have which list:

| Windows | The touch Release removes |
|---|---|
| `L1: Double Tap`, `R1: Double Tap`, `Menu Left: Double Tap`, `Menu Right: Double Tap`, `Menu Left!Right: Double Tap`, `Menu Right!Left: Double Tap` | The window and the pad's three layers |
| `LST: Double Tap`, `RST: Double Tap`, `Steering \| LS Up: Double Tap`, `Steering \| LS Down: Double Tap` | The window alone |
| `RTP: Double Tap` | No touch bind: it is the pad's own window |

The builder writes all four removals in the ten windows; the fix pipeline's
cleanup-list step drops the pad's layers where they can never be under the
window. A thumb resting on the pad covers the stick touches, so no stick
window opens over the pad's layers, and `Steering` clears the pad's touch.

## How it is built

[build_candidate.py](build_candidate.py) has two classes.

- `EveryPress` sits inside the 90.25 build. It overrides that build's last
  step (`build_chain_cleanups`) to run first: after that step the
  required-cleanup fixes number new groups themselves, and a group added by
  the builder afterwards takes a number already in use. At that point the
  key is still an overlay layer's (`Menu Right: Enter`); the fix pipeline
  types it in place (R138), in the new copies as well.
- `Front` sits in front of the 90.27 class: it creates the two layers with
  the others, so the whole-layout clears list them, and it changes the
  windows in the finished layout. The pipeline's `window_pads` fix leaves a
  mouse-mode pad in a window as it finds it.

## Exceptions register

- **R139, the Fn layers' stick clicks:** two entries removed. The plain Fn
  layers are only ever over Base's Entry Points now, so the clicks under them
  no longer differ.
- **R139, the right pad's touch:** in the entry for the menu layers, the two
  Fn layers are replaced by their `Stateful` copies, which sit over `Steering`
  (touch cleared) or `Cursor Gyro` (Base's touch).

## Tests

- `tests/test_menu_chain_and_window_pads.py`: the two layers at the end; the
  Fn layers' bind; where the chain's Entry Point is added; the `Stateful`
  copies; every window's right pad; the stick pattern; the left pad and the
  clicks; what differs from 90.27.
- `tests/test_scenarios_90_28.py`: M1 to M6, the chain on later presses, the
  quick press, the thumb lift, and Steering and Cursor Gyro; W1 to W4, the
  windows.
- 90.25 M5 now has the hold bringing the Fn layer alone. The window test of
  `test_double_tap_windows.py` has the touch Release.

## On the Deck, in this order

1. **The chain.** Hold Select and tap Start three times: Enter each time.
   Then hold Start: `Menu Keys`, with the beep. Then the same with Start held
   and Select: Backspace.
2. **A quick press of both.** Press Select and Start almost together and
   hold: `Menu Keys`, and nothing typed.
3. **Steering or Cursor Gyro.** Hold Select and press Start: Enter at once,
   held, and no `Menu Keys`.
4. **A window.** Rest a thumb on the right pad, tap L1, lift the thumb at
   once, touch the pad again and move: the cursor moves, and a click works.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-windows-changed.txt` | The ten windows |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.27 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
