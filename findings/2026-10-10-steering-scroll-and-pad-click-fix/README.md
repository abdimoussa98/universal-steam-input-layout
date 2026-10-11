# Steering scroll and trackpad clicks — 90.49

Both live variants were built from committed 90.48; the previous read-only
characterization is in [the audit](../2026-10-10-steering-scroll-and-pad-click-audit/README.md).
No layers were added or removed.

## Behavior changed

- The eight Steering driver/modifier/scroll-window joystick groups now state an
  outer-ring radius of **13276**, the same number as their D-pad deadzone. A
  partial up/down flick should therefore arm the edge Release that removes Mod
  0/1 and opens its single-scroll window. The steering base's separate
  full-deflection clear remains at 29031; Entry Guard's protection is unchanged.
  Rolling sideways while the stick remains out should retain the modifier.
- Lifting either stick thumb during a pending 150 ms Steering single-scroll
  window removes that window, emits its one wheel step, and then cleans the
  thumb's helper layers. A second same-direction push still enters the existing
  repeated-scroll cover; a long first hold still consumes the tap.
- A Mod 0/1 delayed Tap Cover or stick-touch completion no longer removes the
  three right-pad click layers. Its existing cleanup of right-pad touch/scroll
  layers remains. A held middle/back/forward click can therefore survive the
  200 ms transition and is not re-added by an exposed Base click binding.
- A pad click requests **one Low bump** from its click-entry binding. The two
  middle-click outputs, four left outer-pad arrows, right outer-pad Back/Forward
  outputs, and both outer-pad mode overrides no longer request additional
  feedback. A click while right circular scrolling enters through its own
  Soft Press, now with the same Low bump. Outputs and click recovery stay intact.

The change report in this directory compares every binding and setting with
the 90.48 snapshot. Both layout descriptions were reviewed; their existing
feature and variant-control summaries remain accurate. The release title is
90.49 in both variants.

## Validation and limit

The four build audits pass for both layouts. `test_scenarios_90_49.py` covers
thumb-lift completion, tap/hold continuity, equal configured thresholds,
click survival for both exposed-held-input outcomes, and one modeled click
entry bump. The broader relevant regression run passed **86 tests**. The
coverage runner found all **89 of 89** layers reached in each variant, with
no changed layer uncovered; its assumption report lists **320 scenarios**.
Both sibling VDFs exported with key, value, and order verification, and the
four final files were saved in `versions/neptune/90.49/` byte-for-byte.

The simulator treats stick direction and edge as binary inputs; it cannot
prove that their physical thresholds coincide on a Deck. A55 records that
assumption. It also does not count native trackpad mode feedback or haptic
requests from an output that starts as a layer lands on a held input. After
loading 90.49 fresh on the Deck, check partial up/down flicks, sideways rolls,
either thumb lifting during the scroll window, and center/outer clicks on both
pads while holding a steering modifier through 200 ms. Count physical click
bumps there; one configured entry bump is what this revision requests.
