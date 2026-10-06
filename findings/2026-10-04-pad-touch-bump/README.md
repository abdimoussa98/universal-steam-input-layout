# The pad touch bump: how it was built (90.25 and 90.26)

**Status, 2026-10-04:** in the layouts from 90.25 to 90.26. The author decided
the same day to take it out ("I don't like the new trackpad changes") and
asked for this record in case it comes back. It came out in 90.27
([record](../2026-10-04-pad-bump-removal/README.md)). Nothing here was run on
the Deck.

The build records are
[90.25](../2026-10-04-pad-bumps-and-menu-keys/README.md) and
[90.26](../2026-10-04-standard-delays/README.md). The snapshots
`versions/neptune/90.25/` and `versions/neptune/90.26/` are the layouts with
the bump in them.

## What it did

A thumb landing on a pad gave a light bump when a click at that spot would be
the centre click (middle mouse on the right pad, Caps Lock on the left), and
no bump nearer the rim. The idea was to feel which click you would get before
pressing.

## How it worked

A **touch layer** is the layer a pad's touch added first:
`RTP: Touch Entry Point` and `LTP: Touch Entry Point`. It read where the thumb
was once, bumped or didn't, and handed over to the pad's Entry Point.

| Layer | Pad mode | What it bound |
|---|---|---|
| Base, right pad | Mouse, as before | Only the touch: a repeating, silent press that adds `RTP: Touch Entry Point`. No click |
| Base, left pad | D-pad, no click needed, haptics off | Only the touch: adds `LTP: Touch Entry Point`. No swipes, no click |
| `RTP: Touch Entry Point`, `LTP: Touch Entry Point` | D-pad, no click needed | Two Soft Presses on the ring, below. A touch Release that removes the layer |
| `RTP: Entry Point` | Mouse | As before, plus the click: a Soft Press with the strong pulse, repeating every 50 ms, that adds `RTP: Click Entry Point` |
| `LTP: Entry Point` (new) | Swipes | The four swipes, each removing this layer and then adding its key layer; the click, repeating, adds `LTP: Click Entry Point`; a touch Release that removes the layer |
| `Steering` | Mouse, touch cleared | Its own copy of the click's add, with no repeat: no touch layer runs there |
| `LTP: Click Entry Point`, `LTP: Middle Click`, `LTP: Arrow Keys` | As before | Their touch Release and stick-touch cleanups also remove `LTP: Entry Point` |

The two ring binds of a touch layer. Both do the same thing: remove the touch
layer, then add the pad's Entry Point. Only the inner one bumps.

| Bind | Active when the thumb is | Haptic | 90.25 | 90.26 |
|---|---|---|---|---|
| Inner | Inside 24996 (inverted Soft Press) | 1, low | Repeats every 50 ms, no delay | The same |
| Outer | Outside its threshold | 0 | Threshold 23000, 5 ms delay | Threshold 24996, no delay |

24996 of 32767 is where the Click Entry Point's inner bind ends, so the bump
matched the centre click. In 90.25 the two ranges overlapped between 23000 and
24996 and the outer bind's 5 ms delay let the inner one win there, as in the
Click Entry Point. In 90.26 the outer bind started where the inner one ended,
so no priority and no delay were needed.

One touch on the right pad, in the centre:

| Step | What happens |
|---|---|
| Thumb lands | Base's touch adds `RTP: Touch Entry Point` |
| At once | The inner bind fires as the layer lands on the thumb (a repeating bind always fires, A6): bump, the touch layer removes itself, `RTP: Entry Point` comes on |
| 150 ms | `RTP: Tap Cover`, as before |
| A click | `RTP: Entry Point`'s click adds `RTP: Click Entry Point`, which picks the centre or the outer layer as before |

## The decisions behind it

All by the author, 2026-10-03 and 2026-10-04:

- **A layer on the touch, not a D-pad Base.** "Keep the right trackpad as a
  mouse and the only thing on there is the touch bind that adds the dpad that
  has the edge binds. the inner bind add rtp entry point with a bump the outer
  does it without the bump, both first remove the dpad layer first before
  adding the entrypoint. This allows inheritence futher down the stack."
- **No click in Base.** "You'll never click without touching the pad." The
  click's add went into the Entry Point.
- **A low haptic** for the bump.
- **Repeats, not delays.** "just repeat it and itll fire we only need the 5 ms
  delay for outer edge bind." The click's add in the Entry Points repeats so
  that a click already down when the Entry Point lands still fires.
- **The left pad.** The plan put the bump on Base's own inverted ring. On the
  simulator that ring counts as on with no thumb on the pad, so the build gave
  the left pad a touch layer too (my change; listed for the author to confirm,
  never confirmed). Its swipes moved into `LTP: Entry Point`.
- **90.26:** the outer bind moved to the inner one's threshold and lost its
  delay, so a touch at the rim handed over at once.

## What it relied on

| Assumption | Status when written |
|---|---|
| A46: a Soft Press on a pad's ring is read on a touch alone, with no click | Unverified |
| A40, A41: a ring Soft Press reads the thumb's distance; the inverted one's radius is about 24996 | Unverified |
| A6: a repeating bind fires as its layer lands on a held input | Verified by the author |
| A47: a pad in swipe mode gives no touch Release | Reported by the author |

## What it cost

- **One layer removal at every pad touch.** Under A13 a removal restarts a
  hold that is still counting. On the simulator a pad touch late in a 200 ms
  hold moved it to 450 ms, and with the right pad up to 950 ms
  ([table](../2026-10-04-standard-delays/README.md#what-the-margin-does)).
- **The left pad's Entry Point could stay on** after a touch with no swipe and
  no click, because swipe mode gives no touch Release (A47). Until a stick
  touch cleared it, the next touch gave no bump.
- **Three layers**, named in the clear lists of fourteen others.

## Where the code is

| File | What |
|---|---|
| `findings/2026-10-04-pad-bumps-and-menu-keys/build_candidate.py` | `build_handover` (the touch layer), `entry_click` (the repeating click), `build_right_pad`, `build_left_pad`; the first three titles of `NEW`; `BUMP_HAPTIC`, `CLICK_REPEAT_MS` |
| `findings/2026-10-04-standard-delays/build_candidate.py` | `touch_rings`: the outer bind at the inner one's threshold |
| `steam_layout/fixes/window_pads.py` | `swipe_keys` reads the swipes from `LTP: Entry Point` when Base has none |
| `steam_layout/simulator.py` | `press_between`: a normal Soft Press at or past the inverted one's threshold stays off |
| `tests/scenario.py` | `press_pad` rests the thumb until the touch layer is gone |
| `tests/test_scenarios_90_25.py` | `PadTouch`, scenarios P1 to P8 |
| `tests/test_scenarios_90_26.py` | `Pads`, scenario P1 |
| `tests/test_pad_bumps_and_menu_keys.py` | `test_a_touch_adds_the_handover_layer_which_reads_the_ring_once`, `test_bases_right_pad_stays_a_mouse_and_the_click_moves_to_the_entry_point`, `test_bases_left_pad_is_a_dpad_and_the_swipes_are_in_the_entry_point` |
| `tests/test_standard_delays.py` | `test_the_touch_layers_two_ring_binds_meet_and_neither_waits` |

## To bring it back

1. In a new builder, run the 90.25 builder's `build_right_pad` and
   `build_left_pad` again, with the three titles in its list of new layers,
   and then 90.26's `touch_rings`.
2. Put the three layers at the end of the layer list, not where they were.
3. Check A46 on the Deck first: touch each pad in the centre and at the rim.
   If a ring Soft Press isn't read on a touch alone, the pad stays in the
   touch layer and does nothing until the thumb lifts.
4. Decide again whether the left pad gets it: `LTP: Entry Point` only exists
   for the bump.

## Not part of the bump

These came in the same releases and are separate decisions:

- `RTP: Middle Click` is a mouse pad, so the cursor moves while middle mouse
  is held (90.25).
- The Tap Cover reset on `RTP: Entry Point` and the two stick Entry Points
  (90.25).
- The reset for the Click Entry Points' outer ring bind, on the pad's touch
  (90.26).
- `Menu Keys` and the chorded menu chains (90.25).
