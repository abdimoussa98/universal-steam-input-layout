# DualSense Edge

A conversion of the Ibex layout ([ibex/](../ibex/README.md)), made by
`python3 -m tools.convert dse` and never edited by hand (R177). The rules are
R178 and R180 to R185 in the
[Layer Definition of Done §12](../resources/Layer%20Definition%20of%20Done.md#12-controllers-and-conversions).

| | |
|---|---|
| Steam's `controller_type` | `controller_ps5_edge` |
| Working layouts | `dse_single-set-default_hold-gyro_latest` and `dse_single-set-alternative_hold-gyro_latest`, JSON and VDF. Generated |
| Snapshots | `versions/dse/<version>/`, one per release |
| Version | Its own line from 1.0 |
| Gyro | Player Space, always on; the gyro off layer still turns it off |

What the conversion changes from Ibex:

- **No stick touch.** Everything bound to a stick touch goes, and so do the
  eight stick-touch layers (`LST:` and `RST:`).
- **The grips swap.** L4 and R4 are on the front of the Edge, L5 and R5 on the
  back, so Shift and Space go on the back paddles and Ctrl and Alt on the
  front buttons.
- **One touchpad.** Both trackpads and their layers go. The whole touchpad
  takes the left pad's gestures with six new `CTP:` layers: swipes into Escape,
  Enter, Tab and Backspace, and a click into the arrow keys, with no middle
  click or Caps Lock in the centre. Every click on it is a Regular Press.
- **Mute is the middle mouse button.**
- **Gyro is always on**, with no enable button.

The registry entry is in [controllers.py](../steam_layout/controllers.py).
