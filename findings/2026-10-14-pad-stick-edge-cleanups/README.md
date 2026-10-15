# Stick-edge cleanups on the pad layers, and pad-click stand-ins (90.72)

Built on 2026-10-14 from the **90.71** snapshot, both layouts, on the
author's word: "go ahead and first create the plan" ([plan](../../plans/2026-10-14-pad-stick-edge-cleanups.md)).
90 layers in each layout. Device status: **untested**.

A first 90.72 put twenty plain edge cleanups on the ten pad layers. The suite
showed what they hid (below); it was replaced the same day by this build.

| | Default | Alternative |
|---|---|---|
| Layers changed | 27 | 27 |
| Removes, 90.71 to 90.72 | 2,891 to 2,961 | 2,949 to 3,019 |
| Adds, 90.71 to 90.72 | 460 to 469 | 460 to 469 |

## Why

An audit of every layer that binds a stick edge as a cleanup found no pad
layer among them. The author: the pad layers get a cleanup on the stick
edges, "not all controllers that might use this layout will have stick
touch". With stick touch, the stick-touch cleanups already clear a stuck pad
layer; the edges are for a controller without it.

**What the first build showed.** While a pad layer is on with its thumb on
the pad, its empty guard chord answers the stick edges, so the edge binds of
the layers below don't run. On the simulator: in Steering, R1 and the left
stick up with a right-pad click held, `Steering | LS: Tap Cover` never came
(its 200 ms timer is a Soft Press on the left edge), and recentring the stick
scrolled once; with the right stick at the rim and a left-pad click held, the
ramp layers stayed on after the stick came back. The author's direction:
cleanups may wait, since a deflect with everything released still cleans up;
what would be lost is done on the pad's click by the layer that owns it.

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.71.

**1. Edge cleanups, 16 a layout.** A copy of each layer's stick-touch cleanup:
a repeating, interruptible Regular Press of removes beside an empty guard
chord on the pad's touch (legacy `chord_button` 16 left, 17 right).

| Layers | Edges | Removes |
|---|---|---|
| `LTP: Click Entry Point`, `LTP: Arrow Keys`, `LTP: Middle Click` | both | the layer, and the four key layers (cleanup rules, below) |
| `Escape`, `Tab`, `Backspace`, `Enter` | left only | the layer |
| `RTP: Click Entry Point`, `RTP: Mouse Buttons`, `RTP: Middle Click` | both | the layer, `RTP: Circular Scroll`, `RTP: Entry Point`, `RTP: Tap Cover` |

The key layers have no right edge (author: "leave them off"): a swipe has no
click to carry a stand-in.

**2. Stand-ins.** Silent Soft Presses on a pad's click, each in a new layered
group (`layer` 1, Base's pad mode) that binds only the click.

| Layer | Its hidden edge bind | Its click |
|---|---|---|
| `Steering \| LS Up: Modifier 1`, `LS Down: Modifier 0` | 200 ms Soft Press adds `Steering \| LS: Tap Cover` | right pad: adds `Steering \| LS: Tap Cover` |
| `Steering \| LS Up: Scroll Up`, `LS Down: Scroll Down` | timer Soft Press adds `Steering \| LS: Double Tap Cover` | right pad: adds `Steering \| LS: Double Tap Cover` |
| `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover` | — | right pad: as Base's, a repeating add of `RTP: Click Entry Point` every 50 ms, so the click carries on |
| `Gyro Off Ramp Up`, `Turning Ramp Up 0`, `Turning Ramp Up 1` | the ramp's steps and exits on the right edge | left pad: removes the three, then adds `LTP: Click Entry Point` (so it does not rest on A9) |

No stand-ins on `L1: Modifier 0`, `R1: Modifier 1` or their Gyro versions:
their stick-edge chords add the L1/R1 Tap Cover only with LB or RB held and
the other stick deflected, which a thumb on a pad rules out. A prototype with
them widened 36 cleanup lists, let `L1: Tap Cover` land over
`L1: Temp Cursor Gyro` and hide its LB exit, and gave 100 Flow "varies".

**3. Menu pad blocks (R172).** `Menu Left: Entry Point`, `Menu Right: Entry
Point`, the two `Stateful` ones, and `Menu Left!Right: Enter`, `Menu
Right!Left: Backspace` (which can also land on Base): both pad clicks
blocked, the left pad's swipes type their keys, the left pad's touch cleared.
The right pad's touch is left as it is: the window pattern's Release removes
the layer itself, which here would end a menu hold on a right-thumb lift.

**4. Right-pad touch Releases (author, 2026-10-14).** Every layer that blocks
the right pad's click binds the pad's touch to a Release that removes the
right pad's touch layers (`RTP: Entry Point`, `RTP: Tap Cover`,
`RTP: Circular Scroll`) that can be under it. A window removes itself first
(R146); no other layer does, so a right-thumb lift never ends a menu hold.
With the touch defined, Base's touch press does not come through, so no tap,
double tap or Circular Scroll opens over these layers: the route
touch → Double Tap → Circular Scroll → its click (Circular Scroll has to keep
its own click bind: its pad is a scroll wheel, and a pad in another mode blocks
the one below, A2) is closed. New on the six menu layers; the Steering
LS Up/Down and stick Double Tap windows keep what they had, the rules finding
nothing more under them. `Steering | LS: Entry Guard` keeps its touch block:
no touch layer can be under it, and the block already keeps the tap chain out.
`RTP: Double Tap`'s Start and Select Releases lose the menu layers, which it
can no longer open over.

**5. One remove trimmed.** `RTP: Entry Point`'s right-edge cleanup no longer
removes `RTP: Click Entry Point`, which now answers that edge itself whenever
it is on top (R132).

**The cleanup rules.** The fix pipeline widened twelve lists: the three left
click layers' stick-touch and stick-edge cleanups also remove `Escape`,
`Tab`, `Backspace` and `Enter`. The route: a left swipe opens a key layer,
the right stick at the rim puts the ramp layers over it, and a left click
reaches the ramp's stand-in, whose Click Entry Point lands over the key layer.
48 removes a layout. It also took `LTP: Arrow Keys` and `LTP: Middle Click`
and, with the right touch bound, `RTP: Mouse Buttons`, `RTP: Middle Click`,
`RTP: Tap Cover` and `RTP: Circular Scroll` out of the Stateful Entry Points'
stick-click clears. Nothing can land on top of those Entry Points now, but a
click or Circular Scroll on before Start or Select stays under them: the
random walks of the 90.58 clear check find the click layers and the Tap
Cover there, and a direct sequence finds Circular Scroll (scroll, hold Start,
click a stick). An R132 entry keeps all six.

**Register.** A second R139 entry, my reading, for the author to confirm: the
two menu stick guards inherit the right-pad touch Release from the Entry
Point under them, whose list differs between the plain and the Stateful ones.
And an R139 entry, decided by the author: the three right-pad click
layers inherit the Steering stick layers' face buttons, D-pad, Start, Select,
stick clicks and left-stick directions, 16 inputs on each. 90.71 already put
them over the Steering stack through Base's click; the stand-ins let the
chains see it. R170's notes record the edge cleanups beyond the rule.

Not changed: the Click Entry Points hand over add-first, then remove (90.19);
the touch Release lists; Circular Scroll.

## On the simulator

[`tests/test_scenarios_90_72.py`](../../tests/test_scenarios_90_72.py),
both layouts.

| Scenario | Shows |
|---|---|
| E1 | Each pad layer on with no thumb on its pad, a stick edge pushed with no touch seen: the layer goes, except a key layer on the right edge |
| E2 | Steering, R1 and the left stick up, a right-pad click: `Steering \| LS: Tap Cover` on the click, the click carries on, recentring does not scroll |
| E3 | The same in a Steering scroll layer: the Double Tap Cover on the click |
| E4 | The ramp on, a left-pad click: the ramp layers go, Left Arrow is sent; after the click, with the stick still out, the ramp comes back |
| E5 | Start or Select held: the pad clicks add nothing, a left swipe types Tab with no key layer |
| E6 | Circular Scroll, a click into Mouse Buttons, the thumb off the direction: back to scrolling; the lift clears all |
| E7 | Both pads clicked: lifting the right thumb clears only the right pad's layers |
| E8 | Start or Select held: a right tap, swipe and click open nothing; Circular Scroll on before the menu button is cleared by the lift, and the menu hold stays |

E2 to E4 run both ways on A9. Not new in 90.72: on 90.71 too, with A9 the
other way, the E2 gesture leaves `Steering | R1: W Key` on after everything
is let go.

Tests changed: 90.50 C1 passes again (the Tap Cover comes on the click); the
90.70 count of cleanup functions outside Steering is 455 and 481 (was 439
and 465). Pinned to the 90.71 build with `frozen="90.71"`, because they open
the right pad's tap chain during a menu hold, which 90.72 closes (E8 is the
counterpart): 90.23 C1 and C3, 90.24 K6, 90.26 D3, 90.30 W1 and W6.

## Audits and tests

- Build audit on both candidates against 90.71, and on the installed
  layouts: clean.
- The full suite: 1,326 tests pass (25 expected failures, as before).
- Every layer is on the stack in a scenario; none changed without one (R165).
  [Unverified assumptions](unverified-assumptions.txt) written.
- Snapshot: `versions/neptune/90.72/`, JSON and VDF, both layouts.

## On the Deck

1. A stuck pad layer clears on a stick push (needs a stick whose touch isn't
   seen).
2. Steering: hold the stick up with R1, click the right pad, let everything
   go: no scroll.
3. Turn at the rim, click the left pad: turn assist stops and the click works;
   let go of the left pad with the stick still out: it starts again (A6, A9).
4. Hold Start or Select: the pad clicks do nothing; a left swipe types its key;
   a right double tap does not start Circular Scroll; lifting the right thumb
   does not end the menu hold.
