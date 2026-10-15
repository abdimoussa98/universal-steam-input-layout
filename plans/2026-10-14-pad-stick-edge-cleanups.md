# Plan: stick-edge cleanups on the pad layers, and pad-click stand-ins for what they hide

**Status, 2026-10-14:** approved by the author ("go ahead and first create the
plan"), to be built as **90.72** from 90.71. A first 90.72 (twenty edge
cleanups and nothing else) was installed and failed the suite: it is replaced
by this one.

The author, 2026-10-14, after an audit of every layer that binds a stick edge
as a cleanup: the pad layers get a cleanup function on the stick edges,
because "not all controllers that might use this layout will have stick
touch". When the first build showed those edges hiding binds of the layers
under them, the author's direction: cleanups may be hidden ("if you release
all buttons and you just deflect a stick, I want to go all the way back to a
stateful base"); what would be lost is done on the pad's click instead, by the
layer that owns it.

## Terms

- **Cleanup function:** on one input, a repeating, interruptible Regular
  Press that removes layers, beside an empty chord on the layer's owner (its
  guard), which holds the press back while the owner is held (R133).
- **Pad touch guard:** the legacy `chord_button` 16 (left pad touch) or 17
  (right pad touch), as on the pad layers' stick-touch cleanups. The touch,
  not the click: the click's chord bit is the full click, and the pad layers
  move on Soft Presses.
- **Hidden:** while a pad layer is on and its thumb is on the pad, the guard
  chord answers the stick edge, so a lower layer's edge bind does not.
- **Stand-in:** a silent Soft Press on a pad's click, in the layer whose edge
  bind would be hidden, that does what that bind would have done.

## The changes (both variants)

**1. Edge cleanups (16 a layout).** Each copies the layer's stick-touch
cleanup: the same repeating removal and list, the same guard.

| Layers | Edges | The list |
|---|---|---|
| `LTP: Click Entry Point`, `LTP: Arrow Keys`, `LTP: Middle Click` | both | the layer |
| `Escape`, `Tab`, `Backspace`, `Enter` | left only (author: "leave them off" the right; a swipe has no click for a stand-in) | the layer |
| `RTP: Click Entry Point`, `RTP: Mouse Buttons`, `RTP: Middle Click` | both | the layer, `RTP: Circular Scroll`, `RTP: Entry Point`, `RTP: Tap Cover` |

The right pad's touch layers get none; `RTP: Entry Point` keeps its
right-edge cleanup and `RTP: Double Tap` its edge blocks (R140).

**2. Stand-ins.** In each layer, a new layered group on the pad (Base's mode,
`layer` 1) that binds only the click:

| Layer | Edge bind hidden | Stand-in |
|---|---|---|
| `Steering \| LS Up: Modifier 1`, `LS Down: Modifier 0` | 200 ms Soft Press adds `Steering \| LS: Tap Cover` | right-pad click adds `Steering \| LS: Tap Cover` |
| `Steering \| LS Up: Scroll Up`, `LS Down: Scroll Down` | timer Soft Press adds `Steering \| LS: Double Tap Cover` | right-pad click adds `Steering \| LS: Double Tap Cover` |
| `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover` | (added by a stand-in) | right-pad click as Base's: a repeating Soft Press, every 50 ms, that adds `RTP: Click Entry Point`, so the click carries on |
| `Gyro Off Ramp Up`, `Turning Ramp Up 0`, `Turning Ramp Up 1` | their ramp steps and exits on the right edge | left-pad click removes all three; Base's click then adds `LTP: Click Entry Point` |

All silent (author: "yes").

Not given stand-ins: `L1: Modifier 0`, `R1: Modifier 1` and their Gyro
versions. Their stick-edge chords add the L1/R1 Tap Cover only with LB or RB
held and the other stick deflected, which needs both thumbs on the sticks, so
it cannot happen during a pad click. Giving them stand-ins widened 36 cleanup
lists, hid `Temp Cursor Gyro`'s exit and gave 100 Flow "varies" (prototype,
2026-10-14). Cancellations (`Cursor Gyro`, `Temp Cursor Gyro`, `Menu Keys`),
the menu stick guards' Releases and every lower cleanup may wait.

**3. Menu Entry Points.** `Menu Left: Entry Point`, `Menu Right: Entry Point`
and the two `Stateful` ones take the windows' pad blocks (R172): both pad
clicks blocked, the left pad's swipes type their keys, the left pad's touch
cleared. The right pad's touch is left as it is: the window pattern's Release
removes the layer itself, which here would end a menu hold on a right-thumb
lift.

**4. Right-pad touch Releases** (author, 2026-10-14: "every layer that block
click should just bind the right pad touch to a release press that releases
all the right track pad touch layers"). On every layer that blocks the right
pad's click: a touch Release removing the right pad's touch layers that can
be under it; a window removes itself first, no other layer does. Closes the
route over a menu: touch → Double Tap → Circular Scroll → its click. Where no
touch layer can be under the layer (`Steering | LS: Entry Guard`), its
existing touch block stays.

**5. Register.** An R139 entry, decided by the author: the three right-pad
click layers inherit the Steering stick layers' face buttons, D-pad, Start,
Select, stick clicks and left-stick directions (48 "varies" a layout). The pad
layers pass everything but their pad through; 90.71 already puts them over
the Steering stack, and the stand-ins only let the chains see it. R170's notes
record the edge cleanups beyond the rule.

## Not changed

- The Click Entry Points hand over add-first, then remove (90.19; author:
  "I like that").
- The touch Release lists: each clears every layer of its own pad that can be
  under it.
- Circular Scroll: its click adds the Click Entry Point; nothing on the click
  removes Circular Scroll; the touch Release does.

## Scenarios

1. A stuck pad layer, no stick touch seen: a stick push clears it.
2. Steering, R1 and the left stick up, a right-pad click held: the Tap Cover
   comes on the click, and recentring does not scroll.
3. The same through the scroll layers: the Double Tap Cover comes on the click.
4. The right stick at the rim (ramp on), a left-pad click: the ramp layers go,
   the click carries on; the ramp comes back after the click if the stick is
   still out.
5. A menu Entry Point: pad clicks do nothing, the left swipes type their keys.
6. Scroll, click into Mouse Buttons, back to scroll, lift: all clear.
7. A touch Release with both pads in use clears only its own pad.

## On the Deck

1. A stuck pad layer clears on a stick push (needs a stick whose touch isn't
   seen).
2. Steering: hold the stick up with R1, click the right pad, let everything
   go: no scroll.
3. Turn at the rim, click the left pad: turn assist stops; let go of the left
   pad with the stick still out: it starts again (A6, A9).
