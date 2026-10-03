# Neptune chorded button IDs

**Status, 2026-10-03:** corrected against release 90.19 and the
[exploratory layout audit](../findings/2026-09-27-exploratory-layout-audit/AUDIT.md#appendix-chord-and-mask-decoding).
The earlier table had 14 and 15 the wrong way round (as "View" and "Menu") and
most rows unknown.

These are the values of `chord_button`, the older way to name the one button a
chord waits for. They are selector IDs, not bit positions, and they don't
follow the order of Steam's menu. The layouts also use a bitmask
(`gyro_ratchet_button_mask`) for chords on several buttons and for stick
deflection, which has no `chord_button` ID; see
[Command Entry Budget](Steam%20Input%20JSON%20Structure.md#command-entry-budget).

| `chord_button` | Button | Mask bit | How it is known |
|---|---|---|---|
| 1 | Left bumper | 3 | Same bind in both exports; 130 chords in 90.19 |
| 2 | Right bumper | 2 | Same bind in both exports; 130 chords in 90.19 |
| 5 | Left trigger, full pull | 1 | Inferred: always used with 6 |
| 6 | Right trigger, full pull | 0 | Inferred: always used with 5 |
| 7 | Left trigger, soft pull | 25 | Mask bit checked in Steam's chord menu |
| 8 | Right trigger, soft pull | 24 | Mask bit checked in Steam's chord menu |
| 9 | Left stick click | 22 | Same bind in both exports |
| 14 | Menu Right (`button_escape`) | 14 | The hold on `button_escape` in `Menu Right: Entry Point` is a chord on 14 |
| 15 | Menu Left (`button_menu`) | 12 | The hold on `button_menu` in `Menu Left: Entry Point` is a chord on 15 |
| 16 | Left pad touch | 19 | Same bind in both exports |
| 17 | Right pad touch | 20 | The delayed touch in `RTP: Entry Point` is a chord on 17 |
| 20 | Right stick click | 26 | Same bind in both exports |
| 23 | Left stick touch | 46 | The delayed touch in `LST: Entry Point` is a chord on 23 |
| 24 | Right stick touch | 47 | The delayed touch in `RST: Entry Point` is a chord on 24 |
| none | Left stick deflection | 30 | Inferred from the left-stick chords |
| none | Right stick deflection | 31 | Inferred |

"Same bind in both exports" means the bind appears in the Neptune export with
this `chord_button` and in the Triton export with this mask bit.

**Not known:** L4, R4, L5, R5, A, B, X, Y, left and right pad click, and the
four D-pad directions. The layouts don't chord on them.

`neptune_chord_ids.json` and `.vdf` in this folder are the probe layout the
first IDs were read from. In it, the two inputs Steam lists as "Left Stick or
Trackpad Touch" and "Right Stick or Left Pad Touch" are the left and right
stick edge.
