# The two trackpad clicks, audited (90.56)

Read-only, 2026-10-11, asked for by the author: the sequence of a pad click,
its cleanup guards, what the stick touch binds do, and what could make a
click bump on entry and not on exit "depending on what you do while you're
holding down the button". No layout, rule or test changed. Nothing here ran
on the Deck. Both layouts have the same binds in the six click layers.

    python3 findings/2026-10-11-pad-click-audit/binds.py                      # binds-default.txt
    PYTHONPATH=.:tests python3 findings/2026-10-11-pad-click-audit/probe.py      # results.txt
    PYTHONPATH=.:tests python3 findings/2026-10-11-pad-click-audit/suspicion.py  # suspicion.txt

## Terms

- **Entry point:** `LTP: Click Entry Point` or `RTP: Click Entry Point`. It
  is on for an instant, picks the final layer and removes itself.
- **Final layer:** the layer that holds the output. Centre: `LTP: Middle
  Click` (Caps Lock), `RTP: Middle Click` (middle mouse). Ring: `LTP: Arrow
  Keys`, `RTP: Mouse Buttons` (Back, Forward, wheel).
- **Entry bump, exit bump:** the output's Regular Press asks for a Low bump.
  Steam pulses when that bind starts and when it ends. No other bind in the
  six layers states a bump.
- **Window:** a 150 ms Always On layer a quick tap opens (`L1: Double Tap`
  and eight more).

## The sequence

| Step | Layer that answers | Bind | Does |
|---|---|---|---|
| 0. Thumb lands (right pad only) | `Base` | Touch, repeating | Adds `RTP: Entry Point`; 150 ms later that adds `RTP: Tap Cover` |
| 1. Click reaches the Soft Press point | `Base` (also `RTP: Circular Scroll`) | Click, Soft Press, no repeat, no bump | Adds the entry point |
| 2a. Thumb in the centre | Entry point | Ring, inverted Soft Press at 24996, repeating | Adds the Middle Click layer, removes the entry point |
| 2b. Thumb on the ring | Entry point | Ring, Soft Press at 23000, 5 ms delay, repeating | Adds the ring layer, removes the entry point. Where the two ranges overlap the centre wins |
| 3. Output | Final layer | Click (centre) or a direction (ring), Regular Press, Low bump | The key or mouse button, held |
| 4. Pad let go | Final layer | Click, inverted Soft Press, repeating | Removes the final layer. **This is the exit that works on every click** |
| 5. Thumb lifts | Final layer | Pad touch Release | Removes the final layer again; on the right also `RTP: Circular Scroll`, `RTP: Entry Point`, `RTP: Tap Cover` |

Two more binds: the entry point's pad touch repeats a removal of the ring
layer every 55 ms (the reset for the 5 ms delay), and each final layer holds
itself with `hold_layer` on the click's Soft Press (the R101 exception). The
hold lands on a click that is already down, so by A5 it never fires.

## The cleanup guards

All six layers have the same pair on **both stick touches**: a repeating
Regular Press that removes the layer, and an empty Chorded Press, not
interruptible, that blocks it.

| Layers | Chord that blocks the cleanup | The cleanup removes |
|---|---|---|
| The three left pad layers | The left pad's touch | The layer itself |
| The three right pad layers | The right pad's touch | The layer itself, `RTP: Circular Scroll`, `RTP: Entry Point`, `RTP: Tap Cover` |

A thumb is on the pad for as long as it is clicked, so the guard is always
up during a click. The cleanup can run only after a pad release that Steam
missed. No other input in the six layers has a cleanup function: they bind
nothing but their pad and the two stick touches.

## The stick touch binds

- **Press:** the pair above. It also means a thumb that lands on a stick
  during a click adds nothing: the click layer answers the touch, so `Base`
  never adds the stick's Entry Point (no temporary gyro, no stick tap).
- **Release:** removes that stick's three helpers (`Entry Point`,
  `Tap Cover`, `Temporary Gyro`). It adds nothing: these layers have no
  timer to complete (R123).
- **So a lift removes real layers only when the thumb was on the stick
  before the click.** Then the helpers sit under the click layer. With the
  click first, the three removals find nothing.

## Binds elsewhere that remove a click layer

Full list in [binds-default.txt](binds-default.txt). None can run from under
a click layer by a stick touch, because the click layer answers both.

- `RTP: Entry Point`, `RTP: Circular Scroll`: cleanup functions on the stick
  touches (and the right stick's edge), blocked by the right pad's touch.
- `Stateful | Menu Left: Entry Point` and its Right twin: Select or Start
  held 200 ms in a stateful layer brings in the Fn layer and removes the
  right pad's layers, a held right click with them. By design.
- Full clears on leaving a mode: a stick click's Release in the four menu
  entry points, the stick click chords of `Gamepad` and `Menu Keys`, the
  quick second bumper in the two Steering Modifier 2 layers, and the two
  chained menu entry points.

## What cuts a held click, by the binds alone

[probe.py](probe.py) holds each of the four clicks in `Base`, `Gyro`,
`Cursor Gyro` and `Steering`, then does one of 34 other things (1,088 runs,
A9 both ways). Three things end the output before the pad is let go:

| | What you do | What happens | Exit bump |
|---|---|---|---|
| 1 | Tap L1 or R1 (not in `Steering`), tap Select or Start, touch or click the right pad briefly during a left click, or flick the stick with a driver held in `Steering` | A window opens on top. Every window blocks both pad clicks (R149, R172), so the output stops for 150 ms | Pad let go inside the 150 ms: **none**, the window answers the release. Later: it depends on A11 (unverified), whether Steam restarts a Regular Press that is exposed under a held click |
| 2 | Ring clicks only: the thumb drifts into the centre (inside 70% of the radius) | The direction ends. The final layer has no hand-over, so nothing is live until the pad is let go | None at the let-go |
| 3 | Hold Select or Start 200 ms in `Cursor Gyro` or `Steering`, right pad | The Fn layer's entry removes the right click layers | None |

Everything else held on the simulator: stick touches and lifts in either
order, bumper holds, both bumpers, triggers, face buttons, the D-pad, the
back buttons, the other pad's click. No run left a layer or a key behind.

## What the simulator cannot show

The author's report of 2026-10-10 (a held click drops when a thumb lifts
from a stick) holds on the simulator in every order. Two candidates, both
about Steam and both unverified:

**A. The inverted Soft Press fires after a removal.** It is the author's
suspicion about the Steering edges (A66) carried over: the final layer's
working exit is an inverted bind, on the click. [suspicion.py](suspicion.py)
plays it ([table](suspicion.txt)):

| While a click is held | Drops, if only a removal that takes a layer off counts | Drops, if every `remove_layer` call counts |
|---|---|---|
| A thumb lifts from a stick it rested on before the click | Yes | Yes |
| A thumb lands on a stick and lifts | No | Yes |
| Any bumper press, tap or hold; Select or Start | Yes | Yes |
| The right pad touched during a left click; the other pad clicked | Yes | Yes |
| Triggers, face buttons, D-pad, back buttons | No | No |

One limit: a click lands by a removal (the entry point removes itself), and
clicks do land. So it cannot hold for every removal. It would have to spare
a layer that has just landed.

**B. The self-hold ends on a stack change (A42).** Only if the hold fires on
landing after all, against A5. Same triggers as A.

Either way the click stays dead after the drop only if `Base`'s click does
not fire again under the held click (A9, unverified). `Base`'s add doesn't
repeat, and a repeating one is what A6 says always fires.

## On the Deck, to tell them apart

Hold the left pad's ring on the right side in a text field: the cursor runs
while the output is on.

| | Do | If the cursor stops |
|---|---|---|
| 1 | Hold L1 for a second, let go (no window opens) | Candidate A or B |
| 2 | Tap L1 quickly, keep the pad down a second, let go | And 1 holds: the window, and A11 fails |
| 3 | Thumb on the right stick first, then the click, then lift the thumb | And 4 holds: only a removal that takes a layer off counts |
| 4 | Click first, then touch the right stick and lift | Every `remove_layer` call counts |
| 5 | Keep the click down and roll the thumb inward | Cause 2 of the table above |

The result of the 90.56 check (a thumb lifting in the Steering stick
modifiers) bears on candidate A: if the W layer now stays, an inverted bind
firing after a removal is the likelier cause here too.
