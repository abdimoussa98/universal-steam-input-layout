# Changelog

Every release, newest first: one section per controller and version, headed
`## <controller> <version>`. `ibex` is the Steam Controller 2, `neptune` the
Steam Deck and `dse` the DualSense Edge. Pushing the tag
`<controller>-v<version>` publishes the release with its section as the notes
([publishing](docs/publishing.md)). A conversion's section names the Ibex
release it is made from, as `From ibex <version>.`

## dse 1.0

The first DualSense Edge layout. From ibex 1.0, by the Edge's conversion rules
(R180 to R185; [record](findings/2026-10-15-ibex-base/README.md)):

- **No stick touch:** the eight stick-touch layers go.
- **The grips trade places:** Shift and Space on the back paddles (L5, R5),
  Ctrl and Alt on the front buttons (L4, R4).
- **One touchpad:** both trackpads and their layers go. The whole pad takes the
  left pad's gestures with six new `CTP:` layers: swipes into Escape, Enter,
  Tab and Backspace, and a click into the arrow keys, with nothing in the
  centre. Every click on it is a Regular Press.
- **Mute is the middle mouse button.**
- **In Gyro mode the gyro is always on** (Player Space), with no enable button;
  the gyro off layer still turns it off. Base keeps its enable button, so with
  no stick touch Base has no gyro of its own.

Not yet checked on an Edge ([to-do](todos.md)).

## neptune 90.75

From ibex 1.0. The gyro turns by yaw and roll (Yaw + Roll) in every
gyro-to-mouse group, for the Deck held in both hands; Base had Player Space.
Nothing else changes ([record](findings/2026-10-15-ibex-base/README.md)).

## ibex 1.0

The first Steam Controller 2 layout, and the base layout from now on: every
change is made here and converted to the Deck and the Edge (R177). It is
Neptune 90.74 with the Steam Controller 2's Steam names and Player Space stated
in all eleven gyro-to-mouse groups
([record](findings/2026-10-15-ibex-base/README.md)). Not yet checked on a
Steam Controller 2.

## neptune 90.74

The first release published by the release pipeline. What changed since 90.70:

- **90.74:** the right stick of the four Fn layers takes the left stick's
  settings; its keys and bumps are unchanged
  ([record](findings/2026-10-15-fn-right-stick/README.md)).
- **90.73:** in the Escape, Tab, Backspace and Enter layers the left pad's
  click removes the layer, so the click carries on into the arrow keys as it
  does from Base ([record](findings/2026-10-15-key-layer-click/README.md)).
- **90.72:** the pad layers clean up on the stick edges too, for controllers
  without stick touch; the pad clicks do nothing while a menu button is held
  ([record](findings/2026-10-14-pad-stick-edge-cleanups/README.md)).
- **90.71:** the pad click layers work on touch, with one bump on the final
  click ([record](findings/2026-10-14-pad-click-touch-layers/README.md)).

None of the four has been checked on the Deck yet ([to-do](todos.md)).
