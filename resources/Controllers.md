# Controllers

What is true of the three controllers the layouts are made for: Steam's names
for them, their inputs, and the gyro setting each one uses. The rules that make
one layout from another are in the
[Layer Definition of Done §12](Layer%20Definition%20of%20Done.md#12-controllers-and-conversions);
the registry the tools read is [controllers.py](../steam_layout/controllers.py).

## The three

| Directory | Controller | `controller_type` | `controller_caps` | Gyro style |
|---|---|---|---|---|
| `ibex/` | Steam Controller 2, the base layout (R177) | `controller_triton` | `1096859647` | Player Space (4) |
| `neptune/` | Steam Deck | `controller_neptune` | `23117823` | Yaw + Roll (2) |
| `dse/` | DualSense Edge | `controller_ps5_edge` | `852975615` | Player Space (4) |

`controller_triton` and `controller_ps5_edge` are Steam's internal names, read
from the Steam client on this Mac on 2026-10-15; the author named the Steam
Controller 2's directory Ibex. Each `controller_caps` is the value Steam wrote
in its own export for that controller: the Deck's in the working layouts, the
Steam Controller 2's in the exploratory layout of
[2026-07-11](../findings/2026-07-11-layer-order-swap/FINDINGS.md), the Edge's in
the old Edge layouts in [archived/dse/](../archived/dse/).

## Inputs

The Deck layout binds ten sources: both sticks (click, edge, touch), both
trackpads (click, touch, D-pad directions), the right trackpad's scroll, both
triggers, the D-pad, the face buttons, the gyro, and in `switch` the four grips,
`button_escape`, `button_menu`, the bumpers and both trackpad touches.

| Input | Steam Controller 2 | Steam Deck | DualSense Edge |
|---|---|---|---|
| Two trackpads, click and touch | Expected yes (A72): Valve's `chord_triton.vdf` has both pads as sources | Yes | One touchpad. The whole pad is `center_trackpad`, its touch `center_trackpad_touch` (A76). Valve's PS5 templates and the old Edge layouts bind `center_trackpad` |
| Stick touch | Expected yes (A72): the exploratory layout binds it | Yes | **No** (author, 2026-10-15: touching a stick never did anything with the old Edge layouts) |
| Four grips | Expected on the back (A72) | On the back | Steam's same four names, but L4 and R4 are on the front and L5 and R5 on the back (author, 2026-10-15) |
| Mute button | — | — | `button_capture` (A75) |
| Chords | `chord_button`, as the Deck (A73) | `chord_button` for one button, a mask for several | As the Deck; a mask where there is no `chord_button` ID |

The grips' Steam names: L4 `button_back_left_upper`, L5 `button_back_left`,
R4 `button_back_right_upper`, R5 `button_back_right`.

### Mask bits beyond the Deck's

The [Deck's chord IDs and mask bits](Neptune%20Chorded%20Button%20Ids.md)
come from the same table in the Steam client. Three more bits matter to the
Edge; none has a `chord_button` ID:

| Mask bit | Button |
|---|---|
| 27 | Centre pad touch: the whole touchpad (A76) |
| 28 | Centre pad click |
| 29 | Mute; labelled capture only for Switch controllers (A75) |

## Gyro conversion style

A gyro group's `gyro_to_2d_conversion_style`, "3DOF to 2D Conversion Style" in
Steam's editor, says how turning the controller becomes mouse movement. The
values, read from the Steam client on this Mac on 2026-10-15:

| Value | Style | Steam's description, shortened |
|---|---|---|
| 0 | Yaw | Turn the controller around its own vertical axis |
| 1 | Roll | Lean it around its forward axis |
| 2 | Yaw + Roll | The lean and the turn added together; tilting up and down moves the mouse vertically |
| 3 | Local Space | (advanced) |
| 4 | Player Space | Yaw + Roll around the gravity axis for horizontal output, local pitch for vertical |
| 5 | World Space | All rotation around the gravity axis |
| 6 | Laser Pointer | Like a laser pointer |

The Deck is held in both hands, so turning and leaning it both aim: Yaw + Roll
(author, 2026-10-15). The two controllers use Player Space. Every layout
states its style in all eleven gyro-to-mouse groups: until Neptune 90.74 only
Base's did (4, since 90.4), and Steam's default for an unset style is not in the
client's code.
