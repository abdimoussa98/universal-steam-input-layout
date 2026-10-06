# `Steering` and its fallback guard swap places (90.35)

**Status:** built and installed as 90.35 on 2026-10-06. Not run on the Deck.
Build audit clean. Extends the
[90.34 builder](../2026-10-05-steering-four-way-and-open-edges/README.md),
which stays frozen. 88 layers, as before.

- **Steering base:** `Steering` with nothing of its own on top.
- **The fallback guard:** `Steering | LS: Fallback Guard`.
- **Driver:** R1 and L1 in the default layout, the triggers in the
  alternative. The same two are the **modifier pair**.
- **Hand over, hand back:** a bind that adds the other layer and then removes
  its own.
- **Ramp layers:** `Gyro Off Ramp Up` and the two `Turning Ramp Up` stages,
  which turn assist puts on while the right stick is at the rim.

## Why

The author tried 90.34 on the Deck: the guard's eight-way left stick did not
take effect over `Steering`'s four-way one. "I'm not able to override because
I set the four-way in the steering layer. And then I revert it back to the
eight-way. And you've done that correctly. It's just not working ... in Steam
input. So what I'm going to do is just remove the layer in between."

The design, 2026-10-06: "remove the steering base when adding the fallback
layer ... in the fallback layer, when removing the fallback layer to first add
back the steering layer ... the fallback layer will be added first, then
it'll remove the steering layer. In the same way in the fallback layer." And
of the two stick-touch cleanups: "it would keep them and they would first add
steering back and remove fallback."

## What changed

| | 90.34 | 90.35 |
|---|---|---|
| `Steering`, up and down | Adds the guard | Adds the guard, then removes `Steering` |
| The guard, a bumper with the stick at centre | Removes the guard | Adds `Steering`, then removes the guard |
| The guard, a thumb put on either stick with the left stick at centre | Removes the guard | Adds `Steering`, then removes the guard |
| The guard, Start and Select | Not bound: `Steering`'s came through | `Steering`'s binds, as its own: they add the `Stateful \|` Entry Points |
| The guard, right pad | Not bound: `Steering`'s came through | `Steering`'s, as its own: the mouse, with the touch blocked |
| The Gyro Modifier 2 quick tap | Beeps on `Steering`'s removal | Beeps on the guard's removal too |
| `Steering`, a driver's press | Adds the driver's layer | Removes the three ramp layers, then adds the driver's layer |

So the stack holds `Steering` or the guard, never both. The guard sits on
Base, whose left stick states no layout.

## What you should notice

- **The fallback's stick is eight-way**: W and A together on a diagonal.
- **A bumper at centre drives a little more surely.** `Steering` lands on the
  held bumper, and its repeating bind fires as it lands. In 90.34 it had to
  fire on being uncovered, which is not verified (A9).
- Everything else is as in 90.34.

## One thing added on my own

**A driver's press now removes the ramp layers.** The driver's layer binds the
right stick's edge, and that is where a ramp layer ends. With a ramp layer
left under it, the gyro stayed off until the driver was let go. Two ways in:

- Since 90.34: the driver pressed inside the 5 ms between the right stick
  reaching the rim and the first ramp stage. I missed this in 90.34.
- New with the swap: `Steering` handed back while a ramp stage is on, which
  puts `Steering` on top of the stage.

It is what the hidden-exit rule asks of a layer that covers another's exit
(R136). A side effect: no ramp stage can be under a Steering stick window any
more, so the fix pipeline stopped writing the firing buttons into those two
windows. They inherit Base's mouse buttons again, as from 90.13 to 90.33.

## What differs from what I told the author

- **No second exception was needed.** I said the hand-back on the stick
  touches would need one, because a cleanup function would remove a stateful
  layer. The Cleanup audit does not object to a layer's cleanup function
  removing its own layer.
- **The quick tap keeps `Steering` in its list** by the register entry of
  90.33, although `Steering` is never on with a Gyro modifier now.

## What it rests on

| Assumption | Where |
|---|---|
| A51: the author found on the Deck that an eight-way group over a four-way one stayed four-way | The reason for the swap. The guard is over Base now, which states no layout |
| A10, reported: a key fires as its layer lands on a held input | W or S as the guard takes over |
| A6, reported: a repeating bind fires as its layer lands | The driver after a hand-back; the guard after a driver is let go with the stick up |
| A36, unverified: a chord is decided as its binding starts answering a held input | The guard's chords on the left stick being out |
| A49, unverified: the beep is the second flag | The quick tap's beep |

A bind that removes its own layer part-way through its commands is already
how the pad click Entry Points hand over.

## Rules and the register

| What | Change |
|---|---|
| R157 | A register entry: the two add each other directly. They are still entered and left as one stateful layer |
| R132 | The quick tap's two entries keep `Steering` as well |
| R169 to R171 | The Cleanup audit now counts the guard as a stateful layer, which these rules leave out. Its two touch cleanups stay, by the author's word |
| R173 | Checked on the working layouts by one test, `test_layout_rules.test_every_value_is_one_the_editor_can_set` |
| R156 | The working layouts are this builder's output |
| A51 | The Deck finding is recorded |

## Still open from the Deck

The drivers' layers and the Steering stick modifiers sit over the four-way
`Steering` and state no layout. If the four-way carried into the guard, it
probably carries into them. Not checked.

## Tests

- `tests/test_steering_fallback_swap.py`: the hand-over; every removal of the
  guard hands back; the two only ever swap; the guard's menu buttons and
  right pad; the quick tap's flags; the drivers' ramp removal; what differs
  from 90.34.
- `tests/test_scenarios_90_35.py`: S1 a whole round with one of the two on;
  S2 a bumper at centre; S3 the touch; S4 the menu buttons and the pad; S5
  the quick tap; S6 a driver ends turn assist.
- Changed with it: 90.6 S4, 90.10 D4 and D8, 90.15 M1, 90.33 G1, 90.34 E3,
  and the two Steering window checks in `tests/test_double_tap_windows.py`.
- The Window audit's speed check went from 3 s to 5 s: the audit takes about
  3.2 s on this layout (2.9 s on 90.34), with 18,502 stacks to walk.

## On the Deck, in this order

1. In `Steering`, push up, then tilt toward the left: W and A together.
2. Let go, press R1: the pulse, and R1 drives.
3. Push up, hold Select, click a stick, let go: out of `Steering`, `Gyro` as
   it was.
4. Push up, quick tap of both bumpers: Base, with the beep.
5. While holding R1, try a diagonal on the left stick: is it one direction or
   two? (The open point above.)

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-binds-changed.txt` | What each step did |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.34 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
