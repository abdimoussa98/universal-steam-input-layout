# The left edge's cleanup back to the press and its guard (90.56)

Built on 2026-10-11 from the **90.55** snapshot, both layouts, on the author's
instruction: "switch back to normal clean ups for all besides the steering
entry guard". 90 layers in each layout. Nothing here has run on the Deck.

## Why

On 90.55 a thumb lifting in the Steering stick modifiers cleared the W or S
layer, and with the stick up or down `Steering` then ended (author,
2026-10-11). The author suspects the chord with Invert Activation on the left
edge fires after a `remove_layer` call although a bumper is held (A66). Ten
such chords could remove the W or S layer
([audit](../2026-10-11-stick-touch-and-cleanup-audit/README.md)). The
simulator never showed the fault: it assumes the chord stays off.

## The one change

On the left stick's edge of ten Steering layers the chord with Invert
Activation is gone, and the cleanup is what 90.54 had there
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt): 10
layers, 10 changed inputs each).

| Edge entry | 90.55 | 90.56 |
|---|---|---|
| Cleanup | One Chorded Press on the drivers with Invert Activation, repeating | A repeating Regular Press with the same list |
| Guard | The same chord | An empty Chorded Press on the drivers, not interruptible |
| Timer, in the four timer layers | Soft Press, 13276, 200 or 150 ms | Unchanged, stored after the two |

The ten layers: the W and S layers, the two stick modifiers,
`Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`, the two stick
scroll layers and the two Steering Modifier 2 layers.

Left as they are:

- **`Steering | LS: Entry Guard`** keeps its inverted chord. It is the only
  one left in the layouts, and it removes only the guard.
- **The outer ring** stays at Steam's default in all fourteen Steering layers
  (author, 2026-10-10). In 90.54 these edges sat at 13276, so the press now
  runs only with the stick at the rim.
- Everything else of 90.55: the Soft Press timers, no right pad removes in
  the modifier layers, no cleanup on up and down in the W and S layers, A and
  D sending only their key, the shorter Modifier 2 entries.

The fix pipeline changed nothing.

The plan of the same day for an inner Soft Press in the layers that assume
the stick is out was not built
([plan](../../plans/2026-10-11-edge-cleanup-without-inverted-chords.md)); the
author chose the press and its guard for all ten.

## What you would feel

- A thumb lifting from a stick with a bumper held and the stick out should
  no longer end `Steering`, if the inverted chord was the cause.
- A W or S layer left on by a missed bumper release clears when the stick
  reaches the rim, on a stick touch, or on the next bumper press. In 90.55 it
  cleared as soon as the stick was centred.
- Nothing else: on the simulator the 384 logged points of the 90.54 record
  are the same as on 90.55.

## Rules, the register and the tests

- **A66** (new, unverified and doubted by the author): a chord with Invert
  Activation stays off while a chord button is held, also after a removal.
  Nothing rests on it since this build.
- **R111, R133:** the ten register entries for the inverted edge chords and
  their R133 entry are out. R133 has no exception left; R111 keeps the Entry
  Guard's and the old Fallback Guard's.
- **Tests:** the edge cleanup scenarios of 90.55 (C1 to C4) and its edge
  shape test run on the 90.55 candidate (`frozen`). The rest of the 90.55
  scenarios stay on the working layout.

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup).
- **Scenarios:** `tests/test_scenarios_90_56.py`, 6 tests, pass: flicking the
  stick with a bumper held, a missed bumper release, a thumb lifting at every
  stage with the thumbs resting before the bumper, and the shapes.
- **Full suite:** 1191 tests, 14 failing. They are the same 14 that failed
  before this build, in five older modules (`test_fallback_window_backport`
  1, `test_layer_report` 1, `test_neptune_gyro` 6,
  `test_steering_entry_quiet_drivers` 1, `test_steering_rtp_menu_chords` 5).
  Nothing new fails.

## On the Deck

1. Rest both thumbs on the sticks, then hold R1. Push the stick up about
   halfway and lift the right thumb: W stays and `Steering` stays. This is
   the fault of 90.55.
2. Hold a bumper and tap the stick up and down several times: one wheel step
   each, as on 90.55.
3. Flick the stick to the rim and around it with a bumper held: W or S
   stays. The press on the edge is the bind that runs there.
