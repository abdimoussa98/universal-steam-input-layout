# Steering base: open edges, a four-way stick, and the fallback at once (90.34)

**Status:** built and installed as 90.34 on 2026-10-05. The author tried it on
the Deck on 2026-10-06: the guard's eight-way stick did not take effect over
`Steering`'s four-way one. [90.35](../2026-10-06-steering-fallback-swap/README.md)
makes the two swap places, and has a driver's press remove the ramp layers.
Build audit clean. Extends the
[90.33 builder](../2026-10-05-steering-fallback-guard/README.md), which stays
frozen. 88 layers, as in 90.33.

- **Steering base:** `Steering` with nothing of its own on top.
- **Driver:** the button that drives: R1 and L1 in the default layout, the
  triggers in the alternative. The same two are the **modifier pair**.
- **The fallback guard:** `Steering | LS: Fallback Guard`.
- **Turn assist:** the right stick at its rim turns the gyro off and ramps the
  turn speed, through `Gyro Off Ramp Up` and the two `Turning Ramp Up` stages.

## The author's design

2026-10-05, after 90.33 was built: "update the steering base to no longer
block the edge binds for left or right stick. I want that to be blocked in the
other steering layers. The base steering layer should also have the left stick
be switched from an 8way dpad to a 4 way. ... the fall back layer should be
triggered in the base steering layer by pushing up or down on left stick with
a repeated add layer. In the fallback layer we'll be overriding the stick to
be a 8way back to default settings. Also in the fallback the gyro mod 0&1 will
be chorded based on the stick being deflected and there will be a repeated
removal regular press to remove the fallback layer.

so the behavior is kind of swapping the up and down behavior on the stick with
the left and right behavior on the bumper/triggers. If you deflect the stick
up or down you be in fall out unless you press the bumpers/trigger and if you
are in steering base itll be the opposite."

And, asked whether the fallback is one of the other Steering layers: "no the
fallback is not one that would get the edges blocked."

## What changed

| | 90.33 | 90.34 |
|---|---|---|
| `Steering`, both stick edges | Blocked with an empty binding | Not bound: the action set's edge binds come through |
| `Steering`, left stick | No layout stated: eight-way | Four-way (`layout` 0, "Radial Without Overlap") |
| `Steering`, up and down | A chord, 100 ms delay, strong pulse: adds the guard. A reset every 150 ms | A press repeating every 50 ms, uninterruptible, strong pulse: adds the guard |
| The fallback guard, left stick | No layout stated | Eight-way (`layout` 1, "Radial With Overlap") |

The guard's bumpers are as 90.33 built them, which is what the design asks: a
chord on the left stick being out adds the Gyro modifier, and a repeating
press removes the guard.

No other Steering layer needed a block. Each already binds both edges, except
the two stick covers, which leave the right edge to the driver's layer under
them.

## What it does

| You | 90.33 | 90.34 |
|---|---|---|
| Push up or down in Steering base | The guard, the pulse and W after 100 ms | At once |
| Push the stick up, then a driver, however quickly | Inside 100 ms the driver drove | The fallback: the driver is a modifier |
| Press a driver, then the stick | Driving | The same |
| Steer with the stick tilted a little up or down, no driver | Up or down counted too, and brought the fallback | A or D alone, until past the diagonal |
| Right stick to the rim in Steering base or in the fallback | Nothing | Turn assist, as in Base |
| Right stick to the rim while a driver is held | Nothing | The same: the driver's layer binds the edge |
| Left stick's edge in Steering base or in the fallback | Nothing | Base's WASD Modifier slot, which is empty today |

## What follows from the open right edge

- **A driver ends turn assist.** With the right stick at the rim, pressing a
  bumper removes the ramp layers and then drives.
- **In the alternative layout a soft trigger pull does not drive while the
  right stick is ramping.** The ramp stages block a trigger's pull there, as
  they do in Base; only the full pull ends them, and then the trigger drives.
- **The guard can land over a ramp stage**: fire with the right stick at the
  rim, then push the left stick up. Everything unwinds when the sticks come
  back (scenario E3).
- **The fix pipeline wrote into six windows**, by the window rule (R140):
  - The two Steering stick windows get the firing buttons' mouse buttons
    again, as until 90.12. The output is the one they inherited before.
  - In the alternative layout the two modifier windows block a trigger's full
    pull. Outside turn assist the full pull did nothing there.

This reverses 90.13 for Steering base. The author blocked the edge then
("just block it in the steering base") because a ramp stage could land with a
driver held and take the driver's release. The drivers' layers bind the edge
themselves since 90.24, so that case stays closed (scenario 90.13 N2).

## What it rests on

| Assumption | Where |
|---|---|
| A51, new, unverified: `layout` 0 is four-way, 1 is eight-way, and the top layer's group decides | Steering base's four-way stick. The simulator does not read the setting |
| A36, unverified: a chord is decided as its binding starts answering a held input | The order rule: the guard's chord reads the stick as out when a driver is pressed after it |
| A10, reported: a key fires as its layer lands on a held input | W or S as the guard comes on |
| A6, reported: a repeating bind fires as its layer lands or is exposed | The guard at entry with the stick up, and after a driver is let go |

Nothing rests on A14 or A15 in the fallback any more: the add has no delay.

## How it is built

[build_candidate.py](build_candidate.py) puts one class in front of the 90.33
builder's. Its `finish` makes the four changes to the finished layout and
checks what it expects to find first. The layout numbers were read from the
Steam client on this Mac, whose choices list `RadialWithOverlap` as 1 and
`RadialNoOverlap` as 0.

## Rules and assumptions

| What | Change |
|---|---|
| R120, R125 | Their examples no longer name the fallback: it has no delay |
| R173 | A D-pad layout is one of the editor's four |
| R156 | The working layouts are this builder's output |
| A51 | New |
| R139 | The register entry for the left stick's edge under `Menu Left: Escape` and `Menu Right: Tab` goes. It accepted two different empty binds underneath, Base's and `Steering`'s block; only Base's is left |
| A14, A15 | What rests on each is rewritten |
| The description | Steering's paragraph: walking comes at once; turn assist is off only while driving; the stick reads one direction at a time without a driver |

## Tests

- `tests/test_steering_four_way_and_open_edges.py`: the open edges and which
  Steering layers bind theirs; the two layouts; the add; the guard as in
  90.33; the editor's limits; what differs from 90.33.
- `tests/test_scenarios_90_34.py`: E1 to E3, turn assist in Steering base and
  in the fallback.
- Rewritten: 90.33 G1, G3 and G4; 90.10 D4; 90.13 N1 and N2; 90.24 K3.
- Changed with it: the two checks in `tests/test_double_tap_windows.py` on
  the Steering windows' firing buttons, which bind their mouse buttons again.

## On the Deck, in this order

1. In `Steering`, push up: the pulse and W at once.
2. Hold the stick left and tilt it slowly up: A alone until past the
   diagonal, then the pulse and W (A51).
3. Push up and press R1 right after: R1 is a modifier. Press R1 and push up
   right after: R1 drives.
4. Right stick to the rim with no driver: turn assist. Hold R1 and do it
   again: none.
5. Right stick at the rim, press R1: turn assist ends and R1 drives. In the
   alternative layout this needs the full pull.

## Files

| File | What |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder |
| [install_neptune.py](install_neptune.py) | Installs into `neptune/` |
| `*-binds-changed.txt` | What each step did |
| `*-inputs-changed.txt` | The inputs the required cleanups gave a cleanup function |
| `*-changes.txt` | The change report against 90.33 (R164) |
| [unverified-assumptions.txt](unverified-assumptions.txt) | What rests on each unverified assumption (R167) |
| `manifest.json`, `neptune-installation.json` | Hashes |
