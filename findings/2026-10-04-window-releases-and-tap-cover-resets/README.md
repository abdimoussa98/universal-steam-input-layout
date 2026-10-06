# The pad window's Releases, the fallback's edge, and the Tap Cover resets off (90.30)

**Status:** built and installed as 90.30 on 2026-10-04. Not run on the Deck.
Build audit clean; the tests pass. Extends the
[90.29 builder](../2026-10-04-quiet-resets-and-beeps/README.md), which stays
frozen. The plan is
[plans/2026-10-04-window-releases-and-tap-cover-resets.md](../../plans/2026-10-04-window-releases-and-tap-cover-resets.md).

Three changes the author decided on 2026-10-04, from what 90.29 did on the
Deck. Five layers change and none is added or removed: 89 layers. Start and
Select are the menu buttons.

## 1. The right pad's Double Tap window

### What was wrong

`RTP: Double Tap` is on for 150 ms after a touch of the right pad shorter than
150 ms. It binds Start and Select to nothing and the two modifier buttons to
the scroll wheel. A button that was down when the window came on, and was let
go inside it, had its Release covered. Its layers stayed on with nothing held.

The author on the Deck: touching the pad and a menu button together, "the
subsequent click will just immediately go to the FN layer."

### What changed

| Button in `RTP: Double Tap` | Press, unchanged | Release, new |
|---|---|---|
| Start, Select | Nothing | Removes the window, then the 21 menu layers |
| The two modifier buttons | Scroll wheel | Removes the window, then the 17 modifier layers |

The modifier buttons are the bumpers in the default layout and the triggers'
soft pull in the alternative.

- **The menu layers:** every layer with "Menu" in its title, but for the four
  menu windows and `Menu Keys`.
- **The modifier layers:** every L1 and R1 layer, but for the two bumper
  windows and Steering's.

A test keeps both lists complete.

### What it does now

Select held, the Fn layer up, a tap of the pad, Select let go 50 ms after the
thumb:

| | 90.29 | 90.30 |
|---|---|---|
| Select up, inside the window | Nothing | The window ends; the Entry Point and the Fn layer go |
| Afterwards | The Fn layer stays on; the next press is in Fn at once | Base |

On the simulator 304 of 304 cases of a button let go inside the window left a
layer on in 90.29 (default layout), and none do in 90.30 in either layout
([window_left.py](../2026-10-04-stick-touch-and-menu-buttons/window_left.py)).

### What it costs

- **A tap is still lost.** A menu tap that ends inside the window types
  nothing, as before.
- **The window can end early.** Letting go of one of the four buttons inside
  it ends it.
- **One modifier button clears both.** With both held, the first one let go
  inside the window clears both buttons' layers. The one still held gets its
  modifier back from Base's repeating add within 50 ms.

## 2. The fallback hold leaves by up and down only

The author: "The outer edge shouldn't contain the release that removes that
layer ... I want the second you get out of W that you're gone."

`Steering | LS: Fallback Hold`'s outer edge keeps the pulse and the reset and
loses its Release. Up and down keep theirs, which they have had since 90.11.

If an up or down Release is missed, the layer stays on as the stick returns to
centre. The next push uses it, and its Release clears it.

The four cleanup binds of 90.24 stay in the layer. I had proposed taking them
out; the author said no.

## 3. The Tap Cover reset is off the three Entry Points, for now

### What the author saw

On the Deck with 90.29: "the menubuttons weren't working when touching them"
(the sticks), and "after releasing the stick touches the menu buttons were
immediately beeping as if the fn layer was applied." The author's reading: the
reset's repeated removal on the stick touches is behind it.

On the simulator the reset fires once per touch and is then covered, so the
simulator doesn't show it. It would happen if Steam keeps a repeat running
after a layer covers its input
([findings](../2026-10-04-stick-touch-and-menu-buttons/README.md)). Taking the
reset off is the Deck test of that reading.

### What changed

`LST: Entry Point`, `RST: Entry Point` and `RTP: Entry Point` have the touch of
90.24 again: the Release and the delayed Tap Cover.

The reset on the two Click Entry Points' touch (90.26) is not touched.

### What it costs

The Tap Cover's delayed add has no reset. If that delay gets stuck, the Tap
Cover doesn't come (A12). That was the state until 90.24.

On the simulator a right-pad touch no longer postpones a hold: it lands at
200 ms in every case, where 90.27 to 90.29 had 210 to 950 ms.

## How it is built

[build_candidate.py](build_candidate.py) puts one class in front of the 90.29
builder's. Its `finish` changes the finished layout in three steps:
`window_releases`, `fallback_edge` and `cover_resets_off`. Each checks what it
expects to find and stops the build otherwise.

The fix pipeline's cleanup-list step leaves the four Releases as written.

## Rules, register and assumptions

| What | Change |
|---|---|
| R156 | The working layouts are this builder's output; `test_window_releases_and_tap_cover_resets.test_working_layouts_are_this_build` |
| R120 | An exception, in the register: the three Tap Covers have no reset, for now |
| R136 | The touchpad exception shrinks: the pairs set aside for covering a keeper's exit go from 125 to 87 |
| R137 | The Fallback Hold leaves by its up and down Releases and its exit |
| R170 | The register's reason for the two Steering stick layers no longer says the edge Release is the Fallback Hold's exit |
| A48, A28 | Nothing rests on them now |

## Tests

- `tests/test_window_releases_and_tap_cover_resets.py`: the four Releases and
  their lists; the lists are complete; the fallback's Releases; the three
  touches equal 90.24's; against 90.29 only five layers change.
- `tests/test_scenarios_90_30.py`: W1 to W6, a button let go inside the pad's
  window; F1 and F2, the fallback; T1 and T2, holds and Tap Covers without the
  reset.
- Older tests changed, each with a comment:
  - 90.26 D3 was the pad's reset trading restarts with a hold's. It is now a
    pad touch costing a hold nothing.
  - 90.23 C3 is back to its 90.24 form: a stale menu cover under the pad's
    Tap Cover goes on the first stick touch after the thumb has left the pad.
    The pad's reset had changed the order the two covers land in.
  - The cursor test that keeps a reset out of the windows lets the pad
    window's new Release through.

## On the Deck, in this order

1. **The menu buttons with a thumb on a stick.** Rest a thumb on the right
   stick. Tap Select: Escape. Hold Select: the Fn beep at 200 ms. This is the
   test of part 3.
2. **The pad window.** Hold Select until the Fn beep, tap the right pad, let
   go of Select at once, press Select again: an ordinary tap or hold, not the
   Fn layer at once. The same with L1.
3. **The fallback.** In `Steering`, hold the stick up: W and the pulses. Back
   to centre and up again, several times. Roll to the side and back.
4. **The Tap Cover.** Tap each stick quickly a few times, then rest a thumb on
   it: no Temporary Gyro and no stray scroll.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-binds-changed.txt` | The four Releases, the edge and the three resets |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.29 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
