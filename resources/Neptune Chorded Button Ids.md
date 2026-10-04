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

## Mask bits from the Steam client

Read on 2026-10-03 from the enum `k_eGamepadButtonBitMask_…` in the installed
Steam client (macOS, `steamui/chunk~2dcc5aaf7.js`, file dated 2026-09-25). It
is the list the chord and gyro-button pickers are built from, and it agrees
with every bit in the table above, so the two "inferred" stick deflection rows
are confirmed. A web search the same day found no published table.

| Mask bit | Button | Mask bit | Button |
|---|---|---|---|
| 0 | Right trigger, full pull | 16 | R5 (right lower grip) |
| 1 | Left trigger, full pull | 17 | Left pad click |
| 2 | Right bumper | 18 | Right pad click |
| 3 | Left bumper | 19 | Left pad touch |
| 4 | Y (north) | 20 | Right pad touch |
| 5 | B (east) | 22 | Left stick click |
| 6 | X (west) | 24 | Right trigger, soft pull |
| 7 | A (south) | 25 | Left trigger, soft pull |
| 8 | D-pad up | 26 | Right stick click |
| 9 | D-pad right | 30 | Left stick deflection |
| 10 | D-pad left | 31 | Right stick deflection |
| 11 | D-pad down | 41 | L4 (left upper grip) |
| 12 | Select / View (Menu Left) | 42 | R4 (right upper grip) |
| 13 | Steam | 46 | Left stick touch |
| 14 | Start (Menu Right) | 47 | Right stick touch |
| 15 | L5 (left lower grip) | 50 | Quick Access |

The four face buttons and the four D-pad directions together are bits 4 to 11,
`4080`. The legacy `chord_button` IDs of these buttons are still not known;
the layouts don't chord on them. That a chord on these bits behaves like the
ones in use is not tested on the Deck.

`neptune_chord_ids.json` and `.vdf` in this folder are the probe layout the
first IDs were read from. In it, the two inputs Steam lists as "Left Stick or
Trackpad Touch" and "Right Stick or Left Pad Touch" are the left and right
stick edge.
