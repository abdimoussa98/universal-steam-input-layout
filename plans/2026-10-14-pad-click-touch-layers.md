# Plan: pad click layers on touch, the bump on the final click

**Status, 2026-10-14:** approved by the author ("We are good to start building"),
to be built as **90.71** from 90.70.

The author, 2026-10-14, after comparing 90.70 with the old layout
(`findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json`):
the layers that add the Click Entry Point add it with a repeating Soft Press
and no haptic; the entry point has no haptic; the only bump is on the final
layer's click, its `hold_layer`. The D-pad layers work on touch again
(Requires Click off), and each direction's Release removes the layer, like a
touch Release. No inverted repeating removal on any final click.

## Terms

- **Click Entry Point:** `LTP: Click Entry Point`, `RTP: Click Entry Point`.
- **D-pad layers:** `LTP: Arrow Keys`, `RTP: Mouse Buttons`.
- **Middle Click layers:** `LTP: Middle Click`, `RTP: Middle Click`.
- **Final layers:** the D-pad layers and the Middle Click layers.
- **Adders:** the binds that add a Click Entry Point on a pad click: `Base`
  on both pads and `RTP: Circular Scroll`.

## The changes (both variants)

| Layer | Input | 90.70 | 90.71 |
|---|---|---|---|
| Adders | click | Soft Press adds the Click Entry Point, haptic 0, once | Same, with Hold to Repeat every 50 ms |
| Click Entry Points | all | silent (override 0); hand-overs and the 55 ms touch reset | unchanged; the reset stays for the delayed ring hand-over |
| D-pad layers | settings | `requires_click` not set (click required) | `requires_click "0"` |
| D-pad layers | four directions | Full Press, haptic 1 | Full Press, haptic 0, and a Release that removes the layer itself, haptic 0 |
| `RTP: Mouse Buttons` | up, down | Full Press scroll, haptic 1; chord repeat, haptic 0 | Full Press scroll, haptic 0; chord repeat, haptic 1 (Low); Release removes the layer |
| D-pad layers | edge (centre) | `empty_binding` | `empty_binding`, and a Release that removes the layer itself, haptic 0 |
| D-pad layers | click | Soft Press `hold_layer` self, haptic 0; inverted repeating Soft Press remove | Soft Press `hold_layer` self, haptic 3 (High), not interruptible; the remove is deleted |
| Middle Click layers | click | Full Press output, haptic 1; Soft Press `hold_layer`, haptic 0; inverted repeating Soft Press remove | Two Soft Presses, both not interruptible: the output (Caps Lock / middle mouse), haptic 0; `hold_layer` self, haptic 3; the remove is deleted |
| Final layers | touch Release | removes the layer with its cleanup list | unchanged |

`Up` and `Down` in `RTP: Mouse Buttons` then have three entries (chord, Full
Press, Release), the R109 maximum.

The repeat rate of the adders is not set by the author: 50 ms, the rate of
90.16's repeating add and of the entry points' hand-overs.

## What it reverses

- **90.20** (one add on Base): the repeat went because it repeated the bump.
  The add is silent now, so the repeat only re-enters. While a final layer is
  on, its click binds cover the adder, so the add can't come back under it.
- **The note "pad layers move only on Soft Presses and touch Release":** the
  direction and centre Releases now remove the D-pad layers.
- **The inverted repeating removal (90.19 to 90.70)** on the four final
  clicks. The R101 exception keeps the four self-holds.

## The gesture

1. Click: the adder puts on the Click Entry Point, silent.
2. It hands over: centre to Middle Click (50 ms repeat), ring to the D-pad
   layer (5 ms delay).
3. The D-pad layer: the direction under the thumb fires; the click's
   `hold_layer` bumps High.
4. Slide out of the direction: its Release removes the layer. With the click
   still held, the adder's repeat re-enters (steps 1 to 3) and the new
   direction fires.
5. The click lets go: the `hold_layer` ends the layer. The thumb lifting: the
   touch Release.

## Unverified, for the Deck

- The final layer lands under a click that is already held. If Steam skips
  the `hold_layer` there, the High bump does not fire and the layer stays
  until the thumb leaves the zone or lifts. The author accepts either
  ("I don't care"); it is a Deck check, not a blocker.
- Re-entry on a slide passes through the adder's layer for up to 50 ms. On
  the left pad that is `Base`'s 2D scroll, whose swipes add the
  Escape/Enter/Tab/Backspace layers. The scenarios check what the simulator
  says; the Deck says what Steam does.

## Work

1. New builder `findings/2026-10-14-pad-click-touch-layers/build_candidate.py`,
   from the 90.70 snapshot, both variants.
2. Build audit and tests; tests and rules that hold the 90.70 shape (the
   inverted removal, Base's one add, Requires Click) are updated to the new
   shape, each named in the release record.
3. Scenarios for the gesture, release record, install, VDF export, the
   `versions/neptune/90.71/` snapshot, docs/building.md row.
