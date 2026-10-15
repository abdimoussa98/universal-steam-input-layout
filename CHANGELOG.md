# Changelog

Every release, newest first: one section per controller and version, headed
`## <controller> <version>`. `ibex` is the Steam Controller 2, `neptune` the
Steam Deck and `dse` the DualSense Edge. Pushing the tag
`<controller>-v<version>` publishes the release with its section as the notes
([publishing](docs/publishing.md)). A conversion's section names the Ibex
release it is made from, as `From ibex <version>.`

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
