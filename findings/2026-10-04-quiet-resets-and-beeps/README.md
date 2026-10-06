# The silent Tap Cover resets and the beep flag (90.29)

**Status:** built and installed as 90.29 on 2026-10-04. Not run on the Deck.
Build audit clean; the tests pass. Extends the
[90.28 builder](../2026-10-04-menu-chain-and-window-pads/README.md), which
stays frozen.

Two faults the author found on the Deck with 90.28, both in what you feel and
hear and neither in what the layers do. No layer is added, removed or moved:
89 layers.

## 1. A pulse at every touch of the right pad

### What was wrong

The **Tap Cover reset** is the press bind on the touch of `LST: Entry Point`,
`RST: Entry Point` and `RTP: Entry Point` that removes that layer's Tap Cover
and repeats every 200 ms (90.25). It restarts the Tap Cover's 150 ms delay if
that delay got stuck (A12).

I built it without a haptic setting. Every other layer command on the pad's
touch states `haptic_intensity` 0. On the right pad Steam gave the unstated one
a pulse.

It pulsed at every touch because the bind repeats: a repeating bind fires as
its layer lands on an input that is already held (A6), and `RTP: Entry Point`
lands on the thumb.

### What changed

All three resets state `haptic_intensity` 0. The reset stays on all three, the
pad's included (author, 2026-10-04: "I want to keep the pulsing delay fix
cleanup. I just don't want it to be having a bump").

### The reset and the trackball

Until 90.24 the pad had no reset, because repeated layer removals on its touch
had interfered with the trackball glide (A28, the author's observation).

When the reset went on in 90.25 I wrote that it never fires on a normal touch
(A48). That was wrong, and the pulse showed it. What it does on a normal touch:

| Time | What happens |
|---|---|
| 0 ms | The thumb lands. Base's touch adds `RTP: Entry Point`. The reset fires once as that layer lands: it removes `RTP: Tap Cover`, which isn't on |
| 150 ms | `RTP: Tap Cover` comes on and takes the touch over. The reset no longer answers the touch |
| 200 ms | The reset's first repeat would be here. It doesn't happen |

So it is one removal per touch, at the start, and no repeats, as the author
said on 2026-10-04. It repeats only while the Tap Cover fails to land, which is
the case it exists for. A48 now says this.

## 2. No beep entering `Menu Keys`

### What was wrong

A layer command ends in two flags:

```
controller_action add_layer 88 1 0, ,
```

This repo's documentation had the first as the beep and the second as the
on-screen notification, since February 2026. It is the other way round. In the
installed Steam client the message for this command lists its fields as
`display`, then `beep`, and the dialog shows "Display name when changed" above
"Beep when changed".

Rule R161 asks for a beep and no on-screen notification, so every such command
was written `1 0`. That shows the layer's name and doesn't beep. It is what the
author heard: nothing.

Both adds of `Menu Keys` did carry the flag, on both chains' Entry Points. It
was the wrong flag.

Two things in the layouts agree with the new reading:

- **`Gyro`'s toggle** is `1 1`, the author's own since the July layout. It
  beeps under either reading.
- **The Fn layers' delayed add** is `0 1`, the author's own since February
  2026. Under the new reading the Fn layer beeps as it comes up.

### What changed

Every layer command written `1 0` is `0 1`: 22 in each layout
([default](default-feedback-changed.txt),
[alternative](alternative-feedback-changed.txt)).

| Where | Commands |
|---|---|
| `Menu Left!Right: Entry Point`, `Menu Right!Left: Entry Point`: the 200 ms hold adds `Menu Keys` | 2 |
| `Menu Keys`: its ten exits | 10 |
| `Transition Set 0`, `1` and `2`: the two menu Releases of each | 6 |
| `Steering \| LS: Fallback Hold`: the 1.5 s exit, up and down | 2 |
| `Cursor Gyro`: the both-sticks exit, on each stick | 2 |

`Gyro`'s `1 1` and the Fn layers' `0 1` are left alone.

So until 90.28 none of the transitions beeped either: entering and leaving
`Steering`, `Cursor Gyro` and `Gamepad` had the same fault.

### What it rests on

A49: the first flag is the name, the second the beep. It is read from the
client's code and fits what the author heard; it has not been heard on the Deck
yet.

### The pulse

The author also felt no pulse entering `Menu Keys`. The hold bind states
`haptic_intensity` 3, as the transitions' Releases do, and nothing about it
changes here. If the beep comes with 90.29 and the pulse still doesn't, that is
a separate fault. What sets this bind apart from the transitions' Releases: it
is a delayed chord, and its list has 89 commands.

## How it is built

[build_candidate.py](build_candidate.py) puts one class in front of the 90.28
builder's. Its `finish` changes the finished layout in two steps:
`quiet_cover_resets` and `beep_flags`. Each checks what it expects to find and
stops the build otherwise: three resets with no haptic stated, and 22 commands
with the name flag alone.

## Rules, assumptions and the simulator

| What | Change |
|---|---|
| R156 | The working layouts are this builder's output; `test_quiet_resets_and_beeps.test_working_layouts_are_this_build` |
| R120 | A reset on a pad's or a stick's touch states `haptic_intensity` 0 |
| R161 | The beep is the second flag; the command ends in `0 1`. Rests on A49 |
| A48 | Reworded: the reset fires once as the thumb lands, and doesn't repeat. Reported by the author |
| A49 | New: the two flags are the name and then the beep. Unverified on the Deck |
| A28 | Its note follows A48 |
| The simulator | Logs a beep for the second flag. So the Fn layer's add now logs one |
| [Steam Input JSON Structure](../../resources/Steam%20Input%20JSON%20Structure.md#controller_action-command-syntax) | The command syntax section has the flags in the right order |

## Tests

- `tests/test_quiet_resets_and_beeps.py`: the three resets' settings; every
  layer command on a pad states its haptic; no command shows a name without
  beeping; every transition and stateful exit beeps on the second flag;
  `Menu Keys` is added with the beep and the pulse from both chains; and 90.28
  with its 22 flags moved and its three resets silenced equals this build.
- `tests/test_scenarios_90_29.py`: Q1, the Fn hold beeps and a tap doesn't;
  Q2, `Menu Keys` beeps and pulses coming on and beeps going off.
- The older tests of the transitions' feedback build the older builders, which
  still write `1 0`; their comments say so.

## On the Deck, in this order

1. **The pad.** Touch the right pad: no pulse. Flick the cursor and lift: it
   still glides.
2. **The Fn layer.** Hold Select alone for a moment: a beep as the Fn layer
   comes up. This is the quickest check of A49. No beep there, on a bind that
   has been `0 1` for months, means A49 is wrong.
3. **`Menu Keys`.** Hold Select and Start: a beep and the strong pulse. Push
   both sticks out: a beep, and Base.
4. **The transitions.** Enter and leave `Steering`, `Cursor Gyro` and
   `Gamepad`: a beep each time, and no name on screen.

If step 3 stays silent while step 2 beeps, the flag isn't the cause and the
next thing to try is `1 1`, the pair `Gyro`'s toggle uses.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-feedback-changed.txt` | The three resets and the 22 commands |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.28 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
