# Pad click layers: more exits, a 5 ms outer delay, quieter haptics (90.16)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.16**, with the
snapshot in `versions/neptune/90.16/`. Played on the Deck: the haptics are
right. [90.17](../2026-10-03-pad-click-soft-press-only/README.md) took the
click's Release out again, made the outer add repeat and put Caps Lock on the
left centre. Device status: **untested**. The build
audit is clean and the tests pass.

This is a trial (author: "let's see if this works"). If pad click layers
still get stuck, the author goes back to `hold_layer` for the pad clicks.

## What the Deck showed on 90.14 and 90.15

The author played the pad click layers of
[90.14](../2026-10-03-pad-middle-click/README.md) and reported two things:

- **Layers got stuck.** Which layer, and after which gesture, wasn't recorded.
- **A click gave three or four bumps**, where 90.13 gave two.

Neither was reproduced on the press simulator: there every exit fires and a
click logs one bump on Base. So the causes below are guesses, and the changes
are insurance, not a diagnosed fix.

## The changes (author, 2026-10-03)

The intermediate layer stays, and so do `add_layer` and `remove_layer`
(R101). The author first asked for `hold_layer` again and then chose this.

| Layer | Pad input | 90.15 | 90.16 |
|---|---|---|---|
| `Base` | click | One Soft Press adds the Click Entry Point, haptic 3 | The same, plus a second Soft Press that adds it again every 50 ms, haptic 0 |
| Click Entry Point | edge, centre | Soft Press, inverted at 24996, repeats every 50 ms, uninterruptible | Unchanged |
| | edge, outer | Soft Press at 23000, repeats every 50 ms, interruptible | Soft Press at 23000, **5 ms start delay, no repeat, uninterruptible** |
| | pad settings | No haptic setting | `haptic_intensity_override: 0` |
| Click Entry Point, Middle Click layer, D-pad layer | click | Inverted, repeating Soft Press removes the layers | The same, plus a **Release** that removes the same layers |
| | touch | Not bound | A **Release** removes the same layers, and on the right pad `RTP: Circular Scroll`, `RTP: Entry Point` and `RTP: Tap Cover` |

Seven layers and 18 bindings changed per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)); the fix
pipeline changed none of them further.

Why each one:

- **Base repeats the add** (author). If something removes the Click Entry
  Point while the pad is still pressed, it comes back within 50 ms. The first
  Soft Press keeps the bump; the repeating one is silent, so a repeat never
  bumps.
- **Both Soft Presses uninterruptible** (author). The priority by
  interruption (A39) is dropped; nothing rests on A39 now.
- **5 ms on the outer one only** (author). A delayed add fires on its own
  when its layer lands on an input that is already there (R115), so it needs
  no repeat. It has no reset, like the 5 ms hand-off from `Gyro Off Ramp Up`.
- **The centre one keeps its repeat.** The author asked for no delay there.
  It is an inverted entry whose condition is already true when the layer
  lands, and such an entry only fires on a repeat (R114, which a test
  enforces for every inverted layer command).
- **Three exits per layer** (author). The inverted, repeating Soft Press is
  the 90.13 exit. The click's Release sits where 90.13 had the layer's hold of
  itself. The touch Release is new: the 90.13 D-pad layers never had one. The
  author asked for it as extra insurance.

## Two things that follow

**1. Where the two ranges overlap, the simulator sends the D-pad button.**
The centre range runs to 24996 and the outer one starts at 23000. In between,
both Soft Presses are active. The outer one fires at 5 ms. The centre one has
no delay, but by A5 it doesn't fire when the layer lands and waits for its
50 ms repeat. The D-pad layer lands first and covers the edge, so the middle
click never comes there. If the Deck fires the centre one at once, the middle
click wins instead. Either way it is one output (scenario P5). To give the
ring to the middle click under A5, the centre one needs the shorter delay,
for example 5 ms against 15 ms.

**2. The thumb-lift Release takes the right pad's touch layers with it.**
A click layer covers the touch Release of `RTP: Entry Point`, `RTP: Tap Cover`
and `RTP: Circular Scroll`, so a thumb that lifted during a click used to
leave them on until the next touch. The click layers' touch Release now
removes them, and no Double Tap window opens after a click. That carries
those three exits for the hidden-exit check.

## Haptics

What a click should give, as in 90.13: one bump when the pad is pressed
(Base, 3) and one from the output (3). Scroll steps give none.

| Where | Setting | Note |
|---|---|---|
| `Base` click, first Soft Press | 3 | The press |
| `Base` click, repeating Soft Press | 0 | New |
| Click Entry Point, every activator | 0 | As in 90.14 |
| Click Entry Point, pad settings | override 0 | **New.** 90.14 stated nothing here |
| Middle Click, the output | 3 | As the 90.13 centre |
| Middle Click, exits | 0 | |
| D-pad layer, arrows, Back, Forward | 3 | Unchanged since 90.13 |
| D-pad layer, scroll, exits, edge | 0 | |

The likeliest source of the extra bumps is the Click Entry Point's pad. It is
a D-pad pad, and 90.14 gave it no `haptic_intensity_override`, which left its
haptics to Steam's default. Every other D-pad pad in the layout states 0 or 3.
This is a guess: no source says what the default is. If a click still gives
more than two bumps, the next suspect is the pressure hovering at the Soft
Press threshold, which would remove and re-add the Click Entry Point and bump
on Base each time.

## Audits

- R101 stays clean: no `hold_layer`.
- R139: Base changed again, and the entries accepted for 90.14 cover what it
  feeds. Nothing new came up for review.
- R136: the touchpad exception now holds 99 pairs on a keeper's exit, up from
  71, and the same 56 others. Three are gone: the click layers carry the
  touch Release of the three layers under them. 31 are new, all of one kind:
  a Double Tap window over a pad click layer. The new touch Release is an
  exit, and a window clears the pad's touch, as it already did for the other
  pad layers (40 such pairs before). In that case the click layer's inverted,
  repeating Soft Press removes it once the window is gone. No pair is a
  finding outside the exception.

## Scenarios and tests

- `tests/test_scenarios_90_16.py`, X1 to X5: a thumb that lifts clears the
  click layers and what is under them, also in Circular Scroll; Base brings
  the Click Entry Point back under a click that is still held; the outer
  buttons at 5 ms and the middle click at 50 ms; one bump on Base and none
  from the Click Entry Point.
- `tests/test_scenarios_90_14.py`: P5 (the overlap) and P7 (a very short
  click) were rewritten for the new timing, and P6 went with A39.
- `tests/test_pad_click_exits.py`: the bindings above, on the generated
  candidates.

## What to check on the Deck

1. Do pad click layers still get stuck? If so, note which gesture.
2. How many bumps does a click give, at the centre and at the rim?
3. Which output comes about three quarters of the way out, where the ranges
   overlap?
4. Does a quick centre click still send the middle click? It lands 50 ms
   after the press on the simulator.

## Files

- `build_candidate.py`: the builder. It extends the 10-03 menu second-press
  builder, which stays frozen.
- `install_neptune.py`, `*-pad-click-exits.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.15 (R164).
- `unverified-assumptions.txt`: 22 assumptions that aren't verified; 56 of the
  107 scenarios rest on one (R167).
