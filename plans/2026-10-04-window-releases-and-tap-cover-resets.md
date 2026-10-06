# Plan: the pad window's Releases, the fallback's edge, and the Tap Cover resets come off

**Status, 2026-10-04:** built the same day as **90.30**, one release
([record](../findings/2026-10-04-window-releases-and-tap-cover-resets/README.md)).
It is installed in `neptune/` with its snapshot; it has not run on the Deck.
The author decided the three parts from what 90.29 did on the Deck.

What differs from the plan as written: the fix pipeline's cleanup-list step
shortens nothing in the window's four Releases, so the lists are the full 21
menu layers and 17 modifier layers, not the 14 and 16 the sweep had found left
on. The longer lists add the menu stick guards, the menu Tap Cover, the
chains' second-press layers and covers, and `L1&R1: Tap Cover`.

Start and Select are the menu buttons. A **delay fix** is the repeating press
that removes a delayed add's target, so that a stuck delay starts again (the
rule calls it a reset, R120).

## Summary

| # | Part | What changes |
|---|---|---|
| 1 | The right pad's Double Tap window | Start, Select, L1 and R1 get a Release there. A button let go inside the window no longer leaves its layers on |
| 2 | The Steering fallback hold | The Release on the stick's outer edge comes off. The Releases on up and down stay and are the only way the stick leaves the layer |
| 3 | The Tap Cover delay fix | It comes off `RTP: Entry Point`, `RST: Entry Point` and `LST: Entry Point`, for now |

No layer is added or removed: 89 layers.

**Not in this plan (author, 2026-10-04):** the four cleanup binds that 90.24
gave `Steering | LS: Fallback Hold` stay. I had proposed taking them out; the
author said no.

## 1. The right pad's Double Tap window

### The fault

`RTP: Double Tap` is on for 150 ms after a touch of the right pad shorter than
150 ms. It binds Start and Select to nothing and L1 and R1 to the scroll
wheel. A button that was already down when the window came on, and is let go
inside it, has its Release covered. The layers it holds stay on with nothing
held.

The author saw it on the Deck: touching the pad and a menu button together,
"the subsequent click will just immediately go to the FN layer."

On the simulator, 304 of 304 cases of a button let go inside the window leave
a layer on
([window_left.py](../findings/2026-10-04-stick-touch-and-menu-buttons/window_left.py)).
The 90.9 snapshot does the same. It is the touchpad exception to the
hidden-exit rule (R136), set aside on 2026-10-02.

### The change

In `RTP: Double Tap`, each of the four buttons gets a Release. It removes the
window first and then the layers that button's pair can be holding. The press
binds stay as they are.

| Button | Press, unchanged | Release, new |
|---|---|---|
| Start, Select | Nothing | Removes `RTP: Double Tap`, then the menu layers |
| L1, R1 | Scroll wheel | Removes `RTP: Double Tap`, then the modifier layers |

The layers, as the sweep found them left on:

- **The menu layers (14):** for each side the Entry Point, the Fn layer, the
  second-press layer (`Menu Left: Escape`, `Menu Right: Tab`), its Double Tap
  Cover, the chain's Entry Point, and the two `Stateful |` layers.
- **The modifier layers (16):** for each bumper its modifier, cursor layer,
  Tap Cover, scroll layer and Double Tap Cover, the two Modifier 2 layers, and
  the four `Gyro |` modifier layers.

The fix pipeline's cleanup-list step may shorten the lists to what can be
under the window, as it did in 90.28.

It is the pattern the stick touches and the pad's touch have in the other
windows (R172): the window goes first, so no other layer changes under an
Always On layer.

### What it does

With Select held and the Fn layer up, tap the pad and let go of Select 50 ms
after the thumb:

| | 90.29 | 90.30 |
|---|---|---|
| Select up, inside the window | Nothing | The window ends; `Menu Left: Entry Point` and `Menu Left: Fn Layer` go |
| Afterwards | The Fn layer stays on; the next Select press is in Fn at once | Base |

The prototype has 0 of 304 cases leaving a layer on
([window_proto.py](../findings/2026-10-04-stick-touch-and-menu-buttons/window_proto.py)).

### What it costs

- **A tap is still lost.** A menu tap that ends inside the window types
  nothing, as today. The Release can't tell a tap from the end of a hold.
- **The window can end early.** Letting go of one of the four buttons inside
  it ends it. A second pad touch for circular scroll then has to come before
  that.
- **One bumper clears both.** With both bumpers held, the first one let go
  inside the window clears both bumpers' layers. The one still held gets its
  modifier back from Base's repeating add within 50 ms. This touches the
  bumper rocking order only inside the pad's window; the rocking tests must
  still pass.

### What it rests on

A7 (verified): a Release in a layer that was added over a held button fires
when that button is let go.

## 2. The Steering fallback hold

The author, 2026-10-04: the Release belongs on up and down. "The outer edge
shouldn't contain the release that removes that layer ... I want the second
you get out of W that you're gone. And the A and the D should just be A and
D."

Up and down have had that Release since 90.11. The one on the outer edge was
my addition then, a backstop for a missed up or down Release (choice 4 of
[the build record](../findings/2026-10-02-steering-fallback-hold/README.md#choices-made-while-building),
never confirmed).

The left stick in `Steering | LS: Fallback Hold`:

| Input | Bind | 90.29 | 90.30 |
|---|---|---|---|
| Up, down | Press: W or S | Yes | Unchanged |
| Up, down | Chord, 1.5 s: the exit | Yes | Unchanged |
| Up, down | Release: removes the layer | Yes | Unchanged |
| Left, right | Not bound: `Steering`'s plain A and D | Yes | Unchanged |
| Outer edge | Chord, repeating: the pulse | Yes | Unchanged |
| Outer edge | Press, every 1550 ms: the delay fix | Yes | Unchanged |
| Outer edge | Release: removes the layer | Yes | **Removed** |
| Touch | The 90.24 cleanup bind and its chord | Yes | Unchanged (author) |

What it costs: if an up or down Release is missed, nothing on the stick
removes the layer as it returns to centre. The next push up or down uses the
layer, and its Release clears it.

I don't expect this to cure the dead up and down. The edge lets go at 15% of
the stick's travel and up at 40%, so on the way back to centre up's own
Release fires first.

## 3. The Tap Cover delay fix comes off, for now

### What the author saw

On the Deck with 90.29:

- "the menubuttons weren't working when touching them" (the sticks).
- "after releasing the stick touches the menu buttons were immediately beeping
  as if the fn layer was applied."

The author's reading: the repeated removal of the delay fix on the stick
touches is behind it. "I do think they're causing problems."

### Why it could be

The delay fix on the three Entry Points removes the layer's Tap Cover and
repeats every 200 ms (90.25). By the layout it fires once, as the thumb lands,
and is then covered: by the Tap Cover at 150 ms, or by a menu Entry Point the
moment a menu button goes down. The simulator has it that way, and there a
menu hold lands at 200 ms in every case.

It would fire on every repeat only if Steam keeps a repeat running after a
layer covers its input. Nothing here has checked that. If it does, each
removal restarts the Fn layer's 200 ms delay (A13): no Fn while a thumb rests
on a stick, and the Fn beep within 200 ms of the thumb coming off. That is
what the author saw
([findings](../findings/2026-10-04-stick-touch-and-menu-buttons/README.md)).

Taking the delay fix off is the Deck test of that reading.

### The change

| Layer | Touch, 90.29 | Touch, 90.30 |
|---|---|---|
| `RTP: Entry Point`, `RST: Entry Point`, `LST: Entry Point` | Release; the delayed Tap Cover; the delay fix | Release; the delayed Tap Cover |

That is the touch of 90.24 on all three.

Not touched: the delay fix on the two Click Entry Points' touch (90.26), which
serves the 5 ms outer ring bind. It answers the touch only while a pad is
clicked. **Note for the author:** say if it should go too.

### What it costs

The Tap Cover's 150 ms delayed add has no delay fix again. If that delay gets
stuck, the Tap Cover doesn't come and a second touch can open the Double Tap
window or Temporary Gyro where it shouldn't (A12). That was the state until
90.24.

On the simulator a right-pad touch no longer postpones a hold: the 210 to
950 ms rows of [the 90.27 record](../findings/2026-10-04-pad-bump-removal/README.md#what-it-does-to-a-hold)
become 200 ms.

## Rules, register and assumptions

| What | Change |
|---|---|
| R120 | An exception for the Tap Cover of the three Entry Points: no delay fix, for now (author, 2026-10-04). Until 90.24 the pad's was the one exception |
| R136 | The touchpad exception shrinks: `RTP: Double Tap` no longer covers the four buttons' exits. The register entry and its count follow the audit |
| R137 | The Fallback Hold's exits are the up and down Releases and the 1.5 s exit; the edge Release is gone |
| R156 | The working layouts are the new builder's output |
| A48, A28 | Nothing rests on them once the pad's delay fix is off |
| A12 | The three Tap Covers rest on their delay not getting stuck |

## Build steps

1. A new builder under `findings/2026-10-04-<slug>/`, extending the 90.29
   builder by file path. The earlier builders stay frozen.
2. Three steps on the finished layout, each checking what it expects to find
   and stopping the build otherwise:
   - **The window:** the four Releases in `RTP: Double Tap`, in both layouts.
   - **The fallback:** remove the outer edge's Release in
     `Steering | LS: Fallback Hold`.
   - **The delay fix:** remove the repeating press from the touch of the three
     Entry Points.
3. Tests, static and scenarios:
   - A button let go inside the pad's window leaves nothing on: each of the
     four, with the Fn layer up, with a modifier up, with both bumpers, and
     the gesture repeated inside one hold.
   - The fallback: up and down leave the layer at once; rolling to the side
     ends it and `Steering` stays; the stick back at centre leaves nothing on.
   - The three Entry Points' touch equals 90.24's.
   - Against 90.29 only these layers change.
   - The bumper rocking tests and the older scenarios pass, or change with a
     comment saying why.
4. The build audit, the change report against 90.29 and the unverified
   assumption list, in the build folder.
5. Install as 90.30, export the VDFs, save `versions/neptune/90.30/`.
6. Documents: the Definition of Done rows above, the assumptions, the
   exceptions register, `docs/building.md`, `todos.md`, and the build's
   README with the Deck order.

## On the Deck, after the build

1. **The menu buttons with a thumb on a stick.** Rest a thumb on the right
   stick. Tap Select: Escape. Hold Select: the Fn beep at 200 ms. This is the
   test of part 3.
2. **The pad window.** Hold Select until the Fn beep, tap the right pad, let
   go of Select at once, press Select again: a normal tap or hold, not the Fn
   layer at once. The same with L1.
3. **The fallback.** In `Steering`, hold the stick up: W and the pulses. Let
   it back to centre and push up again, several times. Roll to the side and
   back.
4. **The Tap Cover.** Tap each stick quickly a few times, then rest a thumb on
   it: no Temporary Gyro and no stray scroll.

## Still open after this plan

- The stick guards hold the Fn layer off from 15% of a stick's travel.
- A stick's Double Tap window blocks Start and Select for 200 ms after a short
  touch, and after the right stick is pushed and let go.
- A right-thumb lift during the fallback hold moves the exit from 1.5 s to
  3.05 s.
- Whether `Menu Keys` beeps and pulses on entry since 90.29.
