# Ibex: Steam Controller 2

The default layout puts timed modifier gestures on L1/R1; the alternative
puts them on L2/R2. See [Hold / Tap, then hold](../resources/Layout%20Vocabulary.md#timed-gestures)
for the gesture sequence and the distinction from a single tap.

The base layout (R177). Every layout change is made here: a builder in
`findings/<date>-<slug>/` writes the two working layouts, and
`python3 -m tools.convert neptune` and `python3 -m tools.convert dse` make the
Steam Deck's and the DualSense Edge's layouts from an Ibex release by their
rules ([Layer Definition of Done §12](../resources/Layer%20Definition%20of%20Done.md#12-controllers-and-conversions)).

| | |
|---|---|
| Steam's `controller_type` | `controller_triton` |
| Working layouts | `ibex_single-set-default_hold-gyro_latest` and `ibex_single-set-alternative_hold-gyro_latest`, JSON and VDF. Generated |
| Snapshots | `versions/ibex/<version>/`, one per release |
| Version | Its own line from 1.0. 1.0 was made once from Steam Deck 90.74 |
| Gyro | Player Space in every gyro-to-mouse group |

The registry entry is in [controllers.py](../steam_layout/controllers.py). The
Steam Controller 2 is expected to have the Deck's inputs (A72) and to read the
Deck's chord encoding (A73); neither has been checked on the controller yet.
