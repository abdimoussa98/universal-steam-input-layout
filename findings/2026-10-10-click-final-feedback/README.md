# Trackpad click feedback moved to the final output — 90.50

The user reported that 90.49 still gave more than one physical bump on a
trackpad click and asked for the bump to live in the last layer added. This
revision changes only feedback ownership in both live variants. It has no
new layers, click output changes, steering scrolling changes, or mode-feedback
changes.

- Base left/right click adds and the right Circular Scroll click add now
  request **Off** feedback.
- The final center-click outputs (`LTP: Middle Click` and `RTP: Middle Click`)
  request **Low** feedback.
- The four left outer-pad arrow outputs and four right outer-pad mouse/wheel
  outputs request **Low**. The right up/down wheel's delayed repeating chord
  remains **Off**, so holding to scroll does not pulse on each repeat.
- Both outer-pad mode overrides and every click routing/hold/recovery binding
  remain **Off**. Exactly one final output activator requests feedback for
  each center or outer click path.

The change report in this folder compares the six changed layers and 13
feedback settings with the 90.49 snapshot. The existing descriptions still
accurately summarize both variants; their release titles are now 90.50.

Both layouts pass the four build audits. The 56 directly relevant pad-click
scenario tests pass, including held right-pad clicks across Steering Mod 0/1
Tap Cover and stick-touch completion. Historical tests that specifically
assert Base owned the bump run against the validated 90.49 candidate. The
simulator can confirm the early adds are silent and the outputs remain active,
but cannot consistently emit haptics when an output layer first lands on a
held click. A56 records the native Deck behavior this placement depends on.
The full coverage runner found **89 of 89** layers reached in each variant,
with no changed layer uncovered, and recorded 320 scenarios. Both VDFs
exported with key, value, and order verification; the four release files
were copied byte-for-byte to `versions/neptune/90.50/`.

On a fresh Deck load, click each pad in its center and outer zones, including
right-pad up/down, then hold a right-pad click while Steering Mod 0/1 reaches
200 ms. Each click should produce one bump when the final output starts and
none while the click remains held. If the final output is silent on initial
landing, the haptic belongs on a different reliable activation point, and
the Deck result will identify it.
