# The stick touch Releases and the cleanup functions (audit of 90.55)

Read-only, 2026-10-11, on the author's request. Nothing in the layouts
changed. **Since then:** 90.56 put the press and its guard chord back on the
ten left edges
([record](../2026-10-11-edge-cleanup-press-and-guard/README.md)); the numbers
below are 90.55's. Both layouts give the same counts unless stated; the layer names are
the default layout's.

    PYTHONPATH=. python3 findings/2026-10-11-stick-touch-and-cleanup-audit/touch_releases.py
    PYTHONPATH=. python3 findings/2026-10-11-stick-touch-and-cleanup-audit/cleanup_shape.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-stick-touch-and-cleanup-audit/thumb_sweep.py
    PYTHONPATH=. python3 findings/2026-10-11-stick-touch-and-cleanup-audit/driver_layer_removes.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-stick-touch-and-cleanup-audit/suspicion_probe.py

Their output is in [results.txt](results.txt).

## Terms

- **Stick touch Release:** the Release Press on a stick's touch. It fires when
  that thumb lifts.
- **Helpers:** the stick's own three layers, `LST: Entry Point`,
  `LST: Tap Cover` and `LST: Temporary Gyro` (`RST:` on the right).
- **Cleanup function:** a repeating Regular Press that only removes layers,
  held back by a chord on the button that keeps those layers alive (its
  guard).

## 1. Stick touch Releases that add a layer

160 stick touch Releases in 91 layers. 104 only remove. 56 add a layer:

- **2 are needed:** `LST: Entry Point` and `RST: Entry Point` open their own
  double tap window.
- **54, in 27 layers, add the target of the layer's own timer.** Lifting
  either thumb from either stick finishes that layer's hold at once. This is
  rule R123 (author, 2026-09-29).

**They are needed** (author, 2026-10-11): the Release is about to call
`remove_layer`, and a removal resets the running timers (A13), so the Release
adds the timer's target first. I had called them unnecessary because each
layer has its own timer for the same target; that missed the reset. The
table stays as the list of what a thumb lift adds, layer by layer.

| Layers | A thumb lift adds | The layer's own timer |
|---|---|---|
| `L1: Modifier 0`, `Gyro \| L1: Modifier 0` | `L1: Temp Cursor Gyro` | L1, 200 ms |
| `R1: Modifier 1`, `Gyro \| R1: Modifier 1` | `R1: Temp Cursor Gyro` | R1, 200 ms |
| `L1!R1: Modifier 2`, `R1!L1: Modifier 2`, and their two `Gyro \|` twins | `L1&R1: Tap Cover` | The second bumper, 200 ms |
| `Steering \| R1!L1: Modifier 2`, `Steering \| L1!R1: Modifier 2` | `L1: Tap Cover`, `R1: Tap Cover` | The second bumper, 200 ms |
| `Steering \| LS Up: Modifier 1`, `Steering \| LS Down: Modifier 0` | `Steering \| LS: Tap Cover` | The left edge, 200 ms |
| `Steering \| LS Up: Scroll Up`, `Steering \| LS Down: Scroll Down` | `Steering \| LS: Double Tap Cover` | The left edge, 150 ms |
| `L1: Scroll Down`, `R1: Scroll Up` | `L1: Double Tap Cover`, `R1: Double Tap Cover` | The bumper, 150 ms |
| `Menu Left: Escape`, `Menu Right: Tab`, `Menu Left!Right: Enter`, `Menu Right!Left: Backspace` | Their own Double Tap Cover | Select or Start, 150 ms |
| `Menu Left: Entry Point`, `Menu Right: Entry Point` | `Menu Left: Fn Layer`, `Menu Right: Fn Layer` | Select or Start, 200 ms |
| `Stateful \| Menu Left: Entry Point`, `Stateful \| Menu Right: Entry Point` | Their `Stateful \|` Fn layer | Select or Start, 200 ms |
| `Menu Buttons: Left Stick Guard`, `Menu Buttons: Right Stick Guard` | `Menu Buttons: Tap Cover` | Select or Start, 200 ms |
| `RTP: Entry Point` | `RTP: Tap Cover` | The right pad's touch, 150 ms |

Also on these Releases: the four of the two `Stateful | Menu …: Entry Point`
layers each remove six right pad layers. They are the only stick touch
Releases that still do.

**In the Steering stick modifiers, on the simulator:** a deflect during which
either thumb lifts does not scroll (0 wheel steps in 4 runs, where 4 are
expected). That includes a flick where the thumb leaves the stick before it
is back.

**Not an add, but the same gesture:** each double tap window's stick touch
Release removes the window. In the two Steering stick windows a thumb that
lifts inside the first 50 ms after the stick is back takes the window off
before it scrolls. So a tap scrolls only when the thumb stays on the stick
until 50 ms after it is back. That is the 90.52 design (the thumb-lift scroll
of 90.49 was taken out).

## 2. The W or S layer dropping on a stick touch

The author, 2026-10-11: in the Steering stick modifiers a thumbstick touch
release cleared the W or S layer, and with the stick up or down `Steering`
then ended.

**What the binds can do.** No stick touch Release removes the W or S layer.
20 binds on the stick touches do: the cleanup function's Regular Press on
both sticks in ten Steering layers (the W and S layers, the two stick
modifiers, `Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`, the
two stick scroll layers, the two Steering Modifier 2 layers). Each is guarded
by an empty chord on the drivers.

**The simulator does not show it.** 1600 runs: every stage of the stick
sequence, five thumb events (the left thumb off, off and on again, the right
thumb lifting, touching, lifting and touching), both drivers, both
directions, all sixteen settings of the either-way assumptions. The driver's
layer and `Steering` stay every time.

**So on the Deck a cleanup press ran while its guard should have held.** The
simulator takes that guard as given (A27, reported; A36, unverified). A thumb
lift changes the stack under the other thumb: the Release removes three
helpers and adds the Tap Cover, whose own cleanup lands on the stick the
other thumb is resting on. If Steam reads held inputs again when layers
change (A18, the author's hypothesis, unverified), that repeating press
starts again there and can beat its guard. This is a lead, not a diagnosis.

### The author's suspicion: the inverted chord

The author, 2026-10-11: "the inverted chord is getting triggered regardless
of the chorded button being held after a remove api is called."

**The inverted chords.** Eleven chords have Invert Activation, all on the left
stick's edge: `Steering | LS: Entry Guard` (since 90.44, removes only itself)
and the ten Steering layers of 90.55. All ten remove the W layer, the S layer
or both. Since 90.55 the outer ring is at Steam's default, near the rim, so
the edge counts as released through most of a deflect: the held bumper is all
that keeps each chord off.

**Every bind that removes the W or S layer** is listed by
`driver_layer_removes.py`. In short:

| Bind | Where |
|---|---|
| Chorded Press with Invert Activation, on the left edge | The ten Steering layers |
| Cleanup Regular Press with a guard chord, on both stick touches | The same ten |
| Cleanup Regular Press with a guard chord, on Start, Select and the right edge | The W and S layers |
| The same, on the face buttons, the D-pad, Start, Select, both stick clicks and the right edge | The two Steering Modifier 2 layers |
| Cleanup Regular Press on the other bumper, beside the Modifier 2 entry | The W and S layers |
| Release on the layer's own bumper | The W and S layers |
| Release on both bumpers | The two stick windows |
| Clears of a whole mode | `Steering`'s exit on a full push; the Modifier 2 quick tap; the stick click exits of the menu layers, `Gamepad` and `Menu Keys` |

**The simulator with the suspicion built in** (`suspicion_probe.py`: after a
bind takes a layer off, the chord on the edge that answers fires whatever the
bumpers are doing). It gives the author's fault in one case and nowhere else:

- the thumbs were resting on the sticks **before** the bumper went down, so
  the helpers are on the stack under the W layer
- the stick is up or down, inside the ring
- a thumb lifts: the Release takes the helpers off, the chord of
  `Steering | LS Up: Modifier 1` fires and removes the W layer, and
  `Steering`'s own up ends `Steering`

With the bumper down first the W layer answers the stick touches, the helpers
never land, the Release takes nothing off, and nothing drops.

The simulator as it stands assumes the chord stays off while a bumper is
held (A61), which is why the sweep above never showed the fault. The
author's notes of 2026-10-07 say Remove Layer does not bring back a chord
that a bumper **press** had stopped. Here the bumper was already down when
the layer landed, which those notes do not cover.

**On the Deck, to confirm it:**

1. Rest both thumbs on the sticks, then hold R1. Push the stick up about
   halfway and hold it. Lift the right thumb. Under the suspicion `Steering`
   ends.
2. The same with R1 held first and the thumbs resting after. Under the
   suspicion it stays. If it also ends, an add triggers the chord as well.

**If it holds:** a chord with Invert Activation cannot guard a cleanup under a
held bumper. The ten edges go back to the cleanup press and its guard chord,
as in 90.54. The Entry Guard's chord removes only itself and can stay.

**A fix for the stick touches, whatever the cause.** Since 90.55 each of these ten
layers has the inverted chord on the left stick's edge, which clears them
whenever the stick is inside the ring and no driver is held. The stick touch
cleanup adds nothing to that except the 20 binds above. Taking the press and
its guard off both stick touches in the ten layers, and keeping the Release,
leaves no stick touch bind that can remove the W or S layer. It needs an
exception to R169 from the author. It also leans on the inverted chord
working with a list longer than one remove, which the author has set aside
as unchecked (`todos.md`).

## 3. The cleanup functions against the Definition of Done

529 cleanup functions in 64 layers (default; 555 in the alternative): 290 on
buttons, 128 on stick touches, 87 on stick edges, 24 on stick clicks.

| Rule | What it asks | Checked by | Result |
|---|---|---|---|
| R127 | Removes only what its guard's buttons keep alive; one guard per layer | Cleanup audit | 0 findings |
| R128, R129 | Removes every layer below and above that the same buttons keep alive | Cleanup audit | 0 findings |
| R130 | A layer that binds an input with a cleanup below carries it | Cleanup audit | 0 findings |
| R131 | Never removes a stateful layer, a helper, a window, another button's layer | Cleanup audit | 0 findings |
| R132 | Lists only layers that can be on with it | Cleanup audit | 0 findings |
| R133 | A repeating, interruptible Regular Press that only removes, beside a guard chord; stored press, chords, Release | `cleanup_shape.py` | 0 findings |
| R136 | No layer on top hides a lower layer's exit | Cleanup audit | 0 findings |
| R169 to R171 | A cleanup on both stick touches, the edges, every retyped button | Cleanup audit | 0 findings |

**Passing by an exception in the register**, each decided by the author:

- **R136:** 174 pairs set aside under the touchpad exception. In 51 of them a
  layer on top covers a click layer's own exit on its pad's touch.
- **R132:** 14 removes kept in the two Gyro Modifier 2 quick taps.
- **R133:** the ten inverted chords on the left edge.
- **R130:** the own direction of six Steering stick layers.
- **R169, R170:** `Steering | LS: Entry Guard` (four inputs) and the two menu
  stick guards (one edge each).

**Housekeeping:** two register entries match nothing any more
(`Menu Buttons: Tap Cover` over each menu stick guard).

**The limit of "0 findings":** the checks that ask what can be on the stack
use a model that does not follow chords or delayed adds (found on
2026-10-11: it called 66 needed removes "never there"). They cannot see a
guard failing, which is section 2.

## 4. The pad click layers and the stick touches

The six click layers (`LTP: Click Entry Point`, `LTP: Arrow Keys`,
`LTP: Middle Click`, and the three `RTP:` ones) bind both stick touches the
same way:

- a cleanup function, guarded by a chord on the pad's own touch
- a Release that removes that stick's three helpers and adds nothing

No add, and nothing that touches the click layer. This is where the report
of 2026-10-10 stood (a held click drops when a thumb lifts from a stick):
the simulator holds the click through the lift in every order, three
candidates are open, and the four-step Deck trial that tells them apart has
no result yet
([trial](../../plans/2026-10-10-stick-lifecycle-and-pad-click-after-stick-tap.md#the-deck-trial-on-9051-as-installed)).
It is the same family as section 2: a thumb lift removes layers under a
layer that a held input keeps on.

One add nearby: with a thumb on the right pad, a thumb lifting from a stick
adds `RTP: Tap Cover` (section 1), which makes the pad touch a hold.

## What would settle sections 2 and 4

- **The W or S drop:** the two Deck steps under the author's suspicion,
  above.
- **The pad click:** trial steps T1 to T3.
