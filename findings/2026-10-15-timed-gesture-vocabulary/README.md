# Timed-gesture vocabulary implementation — 2026-10-15

Implemented the approved **Hold / Tap, then hold** wording. The central
[vocabulary](../../resources/Layout%20Vocabulary.md#timed-gestures) defines
Initial hold, Release window and Second hold, and keeps a single Tap output
distinct from the second hold.

The shared Rust timeline now shows Hold, Tap and Tap, then hold outcomes at
the same time. Its stage and status text uses the new wording. The bundled
profile export calls menu entry controls “Timed gesture” where the diagram
cannot fit the full phrase. The timeline gives the full sequence and outputs.
This is a display wording change; input handling, recipe timings and layout
bindings were not edited.

Maintained documentation updated: root and controller READMEs, viewer README,
reading guide, Stateful Layer Transitions, Steam Input JSON Structure, Delay
Timers and Repeat Rates, Layer Definition of Done, current overlay plan and
findings, and the live TODOs. Other maintained technical passages continue to
refer to exact layer names. `Tap Cover`, `Double Tap`, `Double Tap Cover`, Steam's
`Hold to Repeat`, serialized phase values and historical records remain exact
technical references. Historical tests and old plans also preserve the
wording they used at the time.

TDD: the UI outcome test first failed because the three-outcome formatter did
not exist; the exporter test first failed on the old “Tap / hold” label. Both
then passed. The exporter has nine passing tests and reported zero unavailable
bindings. The native Rust suite passes, including the companion HTTP test;
desktop and WASM clippy pass. Packaged browser and companion checks pass at
default and 720 px widths. The [default preview](timeline-wide.png) and
[narrow preview](timeline-narrow.png) were visually inspected: all three
outcomes and stage labels remain readable. New vocabulary links resolve.

The viewer profile covers the bundled Ibex default layout. Alternative trigger
modifier terminology is documented in the root/controller guides; a separate
alternative viewer profile is not yet implemented. Real gameplay timing remains
subject to the existing hardware acceptance gates in the
[overlay findings](../2026-10-15-keybind-overlay/README.md).
