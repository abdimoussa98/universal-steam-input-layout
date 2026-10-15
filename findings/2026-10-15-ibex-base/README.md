# Ibex as the base layout: Ibex 1.0, Neptune 90.75 and DSE 1.0

Built on 2026-10-15 from the **Neptune 90.74** snapshot, both variants, on the
author's word: "go ahead and start implementing this"
([plan](../../plans/2026-10-15-controller-dirs-and-release-pipeline.md), parts 3
and 4). Device status: **untested** on all three controllers.

| Release | What it is | Layers | Removes, adds (default; alternative) |
|---|---|---|---|
| ibex 1.0 | The base layout (R177): Neptune 90.74 with the Steam Controller 2's Steam names and Player Space in all eleven gyro-to-mouse groups. Built by [build_candidate.py](build_candidate.py) | 90 | 2,965, 469; 3,023, 469 (as 90.74) |
| neptune 90.75 | The Deck conversion of Ibex 1.0 (R179): Yaw + Roll in every gyro-to-mouse group | 90 | as 90.74 |
| dse 1.0 | The DualSense Edge conversion of Ibex 1.0 (R180 to R185) | 74 | 1,777, 373; 1,835, 373 |

From here on a layout change is built on Ibex, and `python3 -m tools.convert
neptune` and `tools.convert dse` make the other two
([building](../../docs/building.md)).

## Ibex 1.0, the bootstrap

The one change that goes from the Deck to Ibex. Against 90.74, per variant:

- `controller_type` `controller_triton`, `controller_caps` `1096859647` (what
  Steam wrote for the Steam Controller 2 in the exploratory layout of
  2026-07-11), no Workshop link (`url` empty), the title's version 1.0. The
  description is the Deck's, word for word: the two have the same inputs (A72).
- `gyro_to_2d_conversion_style` 4, Player Space, in all eleven gyro-to-mouse
  groups. Base stated it since 90.4; the other ten now state it too.
- No bind changes. The fix pipeline changes nothing: 90.74 was a fixed point.
- Chords keep the Deck's encoding, `chord_button` for one button (A73).

## Neptune 90.75

`python3 -m tools.convert neptune`: Ibex 1.0 with Neptune's Steam names and
Workshop links, and Yaw + Roll (2) in every gyro-to-mouse group. The change
report against 90.74 shows only the eleven gyro styles in each variant: Base's
4 becomes 2, the ten unset ones are set to 2 (C3, the round trip). The
simulator does not model gyro output, so no scenario changes.

## DSE 1.0

`python3 -m tools.convert dse`, the rules in order:

| Rule | What it did, per variant |
|---|---|
| R180 | `controller_ps5_edge`, `controller_caps` `852975615` (Steam's value in the old Edge layouts), no Workshop link, the Edge's description, version 1.0; Player Space stays |
| R181 | The grips trade places in 9 groups: Shift and Space on L5 and R5 (the back paddles), Ctrl and Alt on L4 and R4 (the front buttons) |
| R183 | The left pad's binds move to `center_trackpad` in every layer; its six layers become `CTP: Click Entry Point`, `CTP: Arrow Keys`, `CTP: Escape`, `CTP: Tab`, `CTP: Backspace`, `CTP: Enter`, in their places. The Click Entry Point loses its centre press; its ring press is a Regular Press on the pad's outer ring at 23000, the Soft Press threshold it had. Every click on the whole pad is a Regular Press: Base's, the three ramp layers', `Gamepad`'s Select, the arrow layer's self-hold and the four key layers' |
| R182 | 511 activators dropped: 426 on the stick touches (213 a stick), 97 on the right pad, 12 of them on both |
| R178 (b to e) | The left pad's touch chord, `chord_button` 16 in the eight stick-edge guards of the `CTP:` layers, becomes mask bit 27. Base's gyro mask loses the stick touches (d), `Gyro`'s and its modifiers' lose them too (b) |
| R184 | Base binds the mute button, `button_capture`, to the middle mouse button |
| R185 | The gyro enable mask comes off `Gyro` and its four modifiers. Base keeps its own (author: "no does not include base"), now all of Select, Start and both sticks' deflection: Base's gyro does not aim, since no stick touch brings the `Temporary Gyro` layers |
| R178 (f) | 16 layers deleted, with every command naming them: the eight `LST:` and `RST:` layers, the seven right-pad layers and `LTP: Middle Click`. 75 presets with Base |

The fix pipeline then changes nothing: DSE 1.0 is a fixed point (R152).

### One correction to the plan

The plan moved the left pad's touch switch to a switch input
`center_trackpad_touch`. There is no such layout input: the Steam client's list
of layout input names has `left_trackpad_touch` and `right_trackpad_touch` and
no `center_trackpad_touch`, which is only a field of its controller state
message. The old always-gyro Edge layout (`archived/dse/`) binds
`center_trackpad` and mode-shifts the touchpad's halves from those two
switches, so on the Edge they are the left and right halves. The conversion
leaves both as they are: Base's two mode shifts, the D-pad and the face
buttons, follow a thumb anywhere on the pad, and `Gamepad` still blocks them.
A76 and R183 say so now. The whole pad's touch inside its own groups is
`(center_trackpad, touch)`, and its chord bit is 27: Steam wrote that bit as
the old layout's gyro enable button.

## The audits on a converted layout

The audits read the exceptions register through a view of the layout's
controller (`exceptions.for_layout`; R178 g). For the Edge it renames the left
pad's layers to the whole pad's, moves inputs as the conversion does, and
leaves out what the layout lacks: deleted layers, absent inputs, and R169,
since there is no stick touch. For Ibex and the Edge an entry whose `until` is
a Neptune release before the base layout is over. The Cleanup audit sets the
whole pad's exits aside as the two pads' are (R136's touchpad exception), and
the required-cleanup check asks nothing about an input the controller lacks.

`tools.audit_build` is clean on all six working layouts. The Edge's Cleanup
audit walks 6,549 stacks with five extra presses, Neptune's and Ibex's
1,755,568: the stick touches open most of them.

## Tests

- `tests/test_convert.py`: each rule on a small layout, and on the real ones
  C1 (each conversion is what `tools.convert` makes from its Ibex release),
  C2 (the build audit on Ibex and the Edge), C3 (the round trip) and C5 (each
  `CTP:` layer is its model with only R183's changes).
- `tests/test_scenarios_dse_1_0.py`: the Edge's scenarios E1 to E8 on the
  simulator: swipes, the ring click, the centre click, a click in a key layer,
  mute, the gyro, the grips, and a missed release that clears at the next stick
  push to the edge, where Neptune clears it at the next stick touch (R170).
- `tests/test_controllers.py`: every gyro-to-mouse group states its
  controller's style.
- The R156 test holds Ibex's working layouts to this builder, and Neptune's to
  its builders up to 90.74 only.

## The Deck's scenarios on the other layouts (C4)

[c4_scenarios.py](c4_scenarios.py) runs every scenario of `tests/` that runs on
the working layout twice more; [c4-scenarios.txt](c4-scenarios.txt) has the
results. It is a recorded run, not a test in the suite: it repeats the whole
scenario suite twice, about 25 minutes.

- **Ibex 1.0:** all 535 pass. Its binds are Neptune 90.74's.
- **The Edge stopped after R180 to R182** (its header, the grips, no stick
  touch; the Deck's two pads still there): 53 of 535 do not pass, and each
  needs a stick touch. 46 press one on the simulator, 2 start on
  `LST: Double Tap`, which the Edge deletes, and 5 count or read binds that
  include the stick touches'. Most are a release missed while the Steam menu
  was open and cleared at the next stick touch: on the Edge the next stick
  push clears it (E8). The grip swap failed none: there a scenario's L4
  presses the Edge's L5, where Shift is.

The first run found a fault in the scenario helper itself: a record that
builds a `Pad` without its constructor had no grip swaps. A default on the
class fixed it.

## On the devices

Nothing here has been on a device. In this order:

1. **Steam Deck, 90.75:** with 90.75 in the configurator's title, turning the
   Deck and leaning it both move the aim. Nothing else should feel different.
2. **DualSense Edge, DSE 1.0:** the mute button gives a middle click (A75).
   A swipe on the touchpad gives its key, and lifting ends it; a click on the
   pad's ring gives that direction's arrow key; a click in the centre gives
   nothing (A76). With a thumb on the pad the D-pad and face buttons change as
   on the Deck. Shift is on the left paddle, Ctrl on the left front button.
   In Gyro mode, with both sticks centred, the gyro aims; pushing the right
   stick to its edge stops it. In Base it does not aim.
3. **Steam Controller 2, Ibex 1.0, when one is at hand:** both pads, both
   stick touches and the four grips answer (A72); Base's LB chord into
   `L1: Modifier 0` names LB in the configurator and works (A73).
