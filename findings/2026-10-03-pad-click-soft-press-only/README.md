# Pad clicks on Soft Presses only (90.17)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.17**, with the
snapshot in `versions/neptune/90.17/`. [90.18](../2026-10-03-pad-click-handoff/README.md)
made the Click Entry Point remove itself when it adds the chosen layer. Device status: **untested**. The build
audit is clean and the tests pass.

The author played [90.16](../2026-10-03-pad-click-exits/README.md): the
haptics are right. Three changes came out of it, and one open point: there are
still issues without `hold_layer`, which the author hasn't described yet.

## The changes (author, 2026-10-03)

| Layer | Pad input | 90.16 | 90.17 |
|---|---|---|---|
| Click Entry Point, Middle Click, D-pad layer | click | Inverted, repeating Soft Press removal, and a Release removal | The Soft Press removal only |
| Click Entry Point | edge, outer | Soft Press at 23000, 5 ms delay, no repeat | The same, and it repeats every 50 ms |
| `LTP: Middle Click` | click | Show Keyboard | Caps Lock |

Six layers and eight bindings changed per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

- **No Release on the pad click.** A Release fires when the pad's full click
  lets go. The layers are added at the Soft Press threshold, which is a
  different, lighter pressure. A press that passes the Soft Press threshold
  and never reaches a full click adds the layers and would never see that
  Release. So the click itself moves no layer: every add is a Soft Press, and
  the exits are the inverted, repeating Soft Press and the thumb lifting off
  the pad. No pad click in the layout has a Release now
  (`test_no_release_on_any_pad_click`).
- **Both Soft Presses of the Click Entry Point repeat.** 90.16 dropped the
  outer one's repeat when it got its 5 ms delay, because a delayed add fires
  on its own over a held input (R115). The author wants it back: if the D-pad
  layer goes while the pad is still pressed at the rim, it returns within
  50 ms (scenario S1). The 5 ms delay stays.
- **Caps Lock on the left centre.** It was Show Keyboard since before 90.4.

Unchanged from 90.16: Base's bump and its silent repeating add, both Soft
Presses uninterruptible, the centre one with no delay, the touch Release on
every click layer, and the haptic settings.

## How 90.13 did it, with `hold_layer`

The author asked for the exact life of a pad click before the Click Entry
Point existed. This is read from the 90.13 snapshot, for the right pad; the
left pad is the same with `LTP: Arrow Keys`. What the file says is certain.
What Steam does with `hold_layer` is marked as a reading.

**The bindings**

| Layer | Pad input | Activator | Does |
|---|---|---|---|
| `Base` (pad is the mouse) | touch | Regular Press, repeats | Adds `RTP: Entry Point` (tap and double-tap logic, not part of the click) |
| | click | Soft Press, haptic 3 | `hold_layer RTP: Mouse Buttons` |
| `RTP: Mouse Buttons` (pad is a D-pad, deadzone 23000, inverted outer ring at the default radius) | click | Soft Press, uninterruptible, haptic 0 | `hold_layer RTP: Mouse Buttons`: the layer holds itself |
| | click | Soft Press, inverted, repeats, uninterruptible, haptic 0 | `remove_layer RTP: Mouse Buttons` |
| | left, right | Regular Press, haptic 3 | Back, Forward |
| | up, down | Regular Press, haptic 0 | One scroll step |
| | up, down | Chord with a thumb on the pad, 150 ms delay, repeats | Keeps scrolling |
| | outer ring (inverted: the centre) | Chord with the pad's click, haptic 3 | Middle mouse |
| | both stick touches | Chord with a thumb on the pad beside a repeating Regular Press | Removes the layer when a stick is touched with no thumb on the pad |
| `RTP: Circular Scroll` | click | Soft Press, haptic 0 | `hold_layer RTP: Mouse Buttons` |

**The life of one click**

1. **The thumb rests on the pad.** Base's touch adds `RTP: Entry Point`. The
   pad moves the mouse.
2. **Pressure passes the Soft Press threshold**, before the full click. Base's
   Soft Press fires once: one bump, and `hold_layer` puts `RTP: Mouse Buttons`
   on. A held layer is on for as long as the activator that holds it is
   active.
3. **The layer lands and the pad becomes a D-pad.** That is a different pad
   mode, so none of Base's pad inputs answer any more, including the Soft
   Press that is holding the layer. The layer's own click has the same
   `hold_layer` on a Soft Press: from here the layer holds itself. Reading:
   this is what keeps it on once Base's hold is covered. Whether Steam drops
   Base's hold at that moment isn't known; the self-hold makes it not matter.
4. **Pressure reaches the full click.** The D-pad's buttons need a click.
   Where the thumb is decides the output, and nothing is decided earlier:
   - past the deadzone: the direction's button, with its bump;
   - inside the inverted outer ring: the centre chord fires, because the pad's
     click is its chord button, and sends middle mouse with its bump;
   - in the ring where those two overlap: both.
   Moving the thumb while clicked changes which buttons are down.
5. **Pressure falls back under the Soft Press threshold.** Two things end the
   layer, both tied to that same threshold:
   - the self-hold's Soft Press is no longer active, so the hold lets go and
     Steam takes the layer off by itself;
   - the inverted Soft Press becomes true and removes the layer, again on
     every repeat. It is the backstop for a hold that didn't let go.
   The pad is the mouse again. `RTP: Entry Point` was underneath all along and
   carries on.

**What made it simple**

- **One layer, one threshold.** The same Soft Press threshold adds the layer
  and takes it off. There was no Release anywhere.
- **No layer command had to fire on an input that was already held.** The one
  layer command was Base's, on a fresh press. Everything inside the layer was
  an output. That is the part the Click Entry Point changed: it has to add a
  second layer after it lands, with the thumb already in place, which is why
  it needs repeats or a delay.
- **No decision.** The centre and the directions were live together, which is
  the boundary problem the Click Entry Point was built for.

**What it cost**

- R101: the author's rule against `hold_layer`.
- The chains, the Flow and Cleanup audits and the press simulator don't
  follow `hold_layer`, so the two layers were outside every check.

## If the pad clicks go back to `hold_layer`

Not built. What the 90.13 shape would look like with the Click Entry Point
kept: Base's click holds the Click Entry Point; the Click Entry Point holds
itself on its click and removes itself on the inverted Soft Press; its two
edge Soft Presses hold the Middle Click layer or the D-pad layer, and each of
those holds itself the same way. Open point: an edge Soft Press that holds a
layer is covered as soon as that layer lands, as Base's is in step 3, so each
branch needs its own self-hold on the click.

## Scenarios and tests

- `tests/test_scenarios_90_17.py`, S1 to S3: the D-pad layer comes back under
  a held click; the left centre holds Caps Lock and lets go with the click;
  each click layer clears by its Soft Press exit with the thumb still down.
- `tests/test_scenarios_90_14.py`: P3 expects Caps Lock on the left centre.
- `tests/test_pad_click_soft_press_only.py`: the bindings above, on the
  generated candidates.

The simulator has one "click" per pad and can't tell the Soft Press threshold
from the full click. It can't show the problem the click's Release had.

## Files

- `build_candidate.py`: the builder. It extends the 10-03 pad click exits
  builder, which stays frozen.
- `install_neptune.py`, `*-pad-click-soft-press-only.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.16 (R164).
- `unverified-assumptions.txt`: 22 assumptions that aren't verified; 59 of the
  110 scenarios rest on one (R167).
