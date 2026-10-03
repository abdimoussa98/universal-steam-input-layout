# Pad middle click through a Click Entry Point (90.14)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.14**, with the
snapshot in `versions/neptune/90.14/`. 90.15 carries all of it; rebuilds go
through [findings/2026-10-03-menu-second-press-keys](../2026-10-03-menu-second-press-keys/README.md),
which extends this builder. Device status: **untested**. The build
audit is clean and the tests pass. Five things it depends on have not been
seen on a Deck; they are listed under [What to check on the Deck](#what-to-check-on-the-deck).

## The problem

Until 90.13 a pad click went straight to a D-pad layer (`LTP: Arrow Keys`,
`RTP: Mouse Buttons`), added with `hold_layer`. That layer held both the four
direction buttons and the centre bind (middle mouse on the right pad, Show
Keyboard on the left). Nothing arbitrated between them:

- The directions fired outside the D-pad deadzone, 23000 of 32767.
- The centre fired inside the inverted outer ring. The groups state no
  radius, so Steam's default applied, taken here as 24996
  ([The ranges](#the-ranges)).
- Between 23000 and 24996, about 70% to 76% of the way out, both were live. A
  click there could send both, and a thumb that rolled while pressing could
  send one and then the other.

## The design (author, 2026-10-02 and 2026-10-03)

A pad click is decided once. It adds a **Click Entry Point**, which only
decides, and that layer adds one of two layers that each own the whole pad.

| Layer | Pad input | Entry | Does |
|---|---|---|---|
| `Base`, `RTP: Circular Scroll` | click | Soft Press | Adds the pad's Click Entry Point. Haptic 3 on Base and 0 on Circular Scroll, as before |
| `LTP: Click Entry Point`, `RTP: Click Entry Point` (new) | edge | Soft Press, inverted, threshold 24996, repeats every 50 ms, Interruptible off | Adds the Middle Click layer. No haptic |
| | edge | Soft Press, threshold 23000, repeats every 50 ms, interruptible | Adds the D-pad layer. No haptic |
| | click | Soft Press, inverted, repeats, Interruptible off | Removes the Click Entry Point when the pad is let go |
| `LTP: Middle Click`, `RTP: Middle Click` (new, single-button pad) | click | Regular Press, haptic 3 | Show Keyboard on the left pad, middle mouse on the right |
| | click | Soft Press, inverted, repeats, Interruptible off | Removes the Click Entry Point, then itself |
| `LTP: Arrow Keys`, `RTP: Mouse Buttons` | the four directions | unchanged | Arrow keys; Back, Forward and scroll |
| | edge | Regular Press | Empty. The centre chord is gone |
| | click | Soft Press, inverted, repeats, Interruptible off | Removes the Click Entry Point, then itself |

Why each part is there:

- **The two Soft Presses repeat** (author, 2026-10-03). The Click Entry Point
  lands with the thumb already at its place, and a layer command doesn't fire
  on an input that was already held; one with Hold to Repeat fires on its
  next repeat (R113). The author asked for repeats, not start delays.
- **Interruptible off on the centre, on for the outer** (author). Where the
  two ranges overlap, the centre is meant to win. Whether Steam does that
  between two Soft Presses is assumption A39, unverified.
- **The D-pad layer's edge is empty, not left out.** Both it and the Click
  Entry Point are D-pad pads, so an unbound edge would inherit the two
  repeating Soft Presses, and sliding to the centre while a direction is held
  would add the Middle Click layer on top.
- **The Middle Click layer is a single-button pad.** A different pad mode
  blocks everything below it (A2), so the outer Soft Press can't fire once it
  is on.
- **Every exit removes the Click Entry Point first.** Its Soft Presses read
  only where the thumb is, not whether the pad is pressed. Left on after the
  click, it would add a layer again every 50 ms while the thumb rests there.
- **No haptics in the Click Entry Point** (author). A click gives the same two
  pulses as before: one from Base's press, one from the output.

The four new layers are appended after `Steering | LS: Fallback Hold`, so no
runtime ID shifts. Each layout has 75 layers.

## The ranges

The author asked for the centre and the directions to keep their 90.13 sizes.

- **Directions: certain.** The D-pad layers keep their group settings, so the
  deadzone is still 23000 and the direction binds are byte for byte the 90.13
  ones (`test_the_ranges_are_the_sizes_of_the_last_release`). The outer Soft
  Press copies that deadzone.
- **Centre: inferred.** The 90.13 groups set `edge_binding_invert` and no
  `edge_binding_radius`. No documentation states Steam's default. The Steam
  client ships templates in `controller_base/`: all 30 groups there that carry
  the setting are D-pad groups with **no outer ring bind**, and their values
  are 24995, 24996 or 24999. Nobody tunes a radius for a bind that isn't
  there, so that is the configurator's default written out. The 90.4 and 90.5
  layouts also have a group whose only setting is 24996. This is assumption
  A41. If the slider on 90.13's `RTP: Mouse Buttons` shows another number,
  change `CENTRE_RADIUS` in `build_candidate.py` and rebuild.

Two things follow that the author should know:

- With 24996, the two ranges overlap, as they did in 90.13. The design's
  priority (A39) is what gives that ring to the middle click.
- If A39 is false, the ring still sends **one** output, not two: the first
  layer to land covers the edge and the other add never runs. Which one lands
  isn't known. The press simulator lands the D-pad layer there (scenario P6).

## What changed outside the six pad layers

From the change report against 90.13
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)): 11 layers
changed, 25 changes, 4 layers added. Every change is one of these:

| Change | Where | Decided by |
|---|---|---|
| The pad click adds the Click Entry Point with `add_layer` | `Base` (both pads), `RTP: Circular Scroll` | The design |
| Centre chord replaced by an empty edge; the exit removes the Click Entry Point first; no self-hold | `LTP: Arrow Keys`, `RTP: Mouse Buttons` | The design |
| Stick-touch cleanup functions also remove the Click Entry Point | `LTP: Arrow Keys`, `RTP: Mouse Buttons` | The builder |
| Touch Release and stick-touch cleanup also remove the two new right-pad layers | `RTP: Circular Scroll` | The builder: it removed `RTP: Mouse Buttons` there already |
| The four new layers join the ten whole-layout clears | The four menu Entry Points (both stick clicks each), the two Steering Modifier 2 layers | Generated: the clears list every layer |
| **Stick-touch cleanup also removes `RTP: Circular Scroll`, `RTP: Entry Point` and `RTP: Tap Cover`** | `RTP: Mouse Buttons`, and the two new right-pad layers | **The `cleanup_lists` fix, on its own** (R128): the layer is in the audit's scope for the first time, and those three are under it and kept by the same thumb on the pad |
| **The right-stick edge cleanup also removes the three right-pad click layers** | `RTP: Entry Point` | **The `cleanup_lists` fix, on its own** (R129) |

The two rows in bold are the ones nobody decided by hand. They follow from the
cleanup rules once the pad layers are added with `add_layer`.

## What the audits needed

Moving off `hold_layer` brought the pad layers into the Flow, chain and
Cleanup audits for the first time (R145: nothing is out of scope now).

- **R139, inherited inputs to read.** Base changed, so every inherited input
  that Base feeds was put up for review: 60 entries per layout. They were
  read and are in the exceptions register as eleven entries, each with its
  reason, marked "not yet confirmed by the author":
  - L1 and R1 on the eight pad layers, the four left-pad key layers and the
    six stick-touch helpers: from Base, or from Gyro when Gyro is on. The
    rule's own example.
  - The firing inputs on the two ramp layers: by design.
  - Right-pad touch on the six menu layers: Base adds `RTP: Entry Point`,
    Steering clears it.
  - Stick clicks and the other stick's edge on the Fn layers and stick guards:
    by design.
  - **One is a real gap, recorded as `todo`:** see the next section.
- **R136, hidden exits.** The touchpad exception already set pad pairs aside.
  When 90.14 was built it covered 77 pairs on the keeper (68 in 90.13) and 56
  others (26). The nine new ones: each of the three right-pad click layers
  over the pad-touch Release of `RTP: Entry Point`, `RTP: Tap Cover` and
  `RTP: Circular Scroll`. `RTP: Mouse Buttons` did this in 90.13 as well; it
  wasn't counted while `hold_layer` kept it out. Since 90.15 the check names
  the layer that changed the pad's mode, so the same layout counts 71:
  `RTP: Click Entry Point` over those three, once. The 30 new others: the six
  pad click layers keep the right stick in mouse mode, which blocks the menu
  Entry Points' right-stick click Release, as the other pad layers do.
- **The Window audit takes about 1.9 s, up from 0.85 s.** The pad layers can
  be under every Double Tap window now, and the stacks it checks went from
  5,092 to 10,426. Its test allowed 1 s; the limit is now 3 s, with the
  reason in the test. A cache in `check_stack` gave byte-identical reports
  and no real gain, so it was not kept.

## Found on the way: a stuck layer in Steering (not fixed here)

The R139 review turned up a gap that has been there since 90.11 and has
nothing to do with the pads. In Steering: double-tap and hold Select or Start,
push the left stick up or down, let go of the menu button.
`Menu Left: Escape` or `Menu Right: Tab` inherits Steering's add of
`Steering | LS: Fallback Hold`. The hold lands on top and answers Start and
Select, so the menu button's Release is missed and the second-press layer
stays on. Reproduced on the press simulator on 90.13. In 90.14 it was a `todo`
under R139 in the register. **Fixed in 90.15**
([record](../2026-10-03-menu-second-press-keys/README.md)).

## Choices made while building

The author gave the design in conversation. These were filled in and should
be confirmed:

1. **The layer names**: `LTP: Click Entry Point`, `RTP: Click Entry Point`,
   `LTP: Middle Click`, `RTP: Middle Click`.
2. **The repeat is 50 ms**, the rate the layout already uses for adds that
   must land on a held input. The output therefore comes up to 50 ms after
   the press, and on the simulator a click shorter than that sends nothing
   (scenario P7). A shorter rate, or a 5 ms start delay, would shorten it.
3. **The left pad's centre stays Show Keyboard.** The author's first message
   said Caps Lock; both layouts had Show Keyboard there, and Caps Lock is the
   left-stick click under the L1 modifier.
4. **Base's click does not repeat**, as before. The layer commands that must
   fire on an already-held input are the two Soft Presses, and they repeat.
5. **The exits are pressure exits, not Releases**: an inverted, repeating Soft
   Press on the click, the shape the D-pad layers already had. The entry is a
   Soft Press, and a Release only fires after a full click.
6. **The eleven R139 entries** in the exceptions register, and the 3 s limit
   on the Window audit's test.
7. **The description** gained one paragraph on the pad clicks, marked "Deck
   testing pending".

## What to check on the Deck

Nothing here was run on a Deck. In order of how much depends on it:

1. **A10: the output fires on a click that is already down.** Until 90.13 the
   D-pad layer landed at Soft Press pressure and the full click came after.
   Now the layer with the output lands up to 50 ms later, usually on a click
   that is already down. Every pad click depends on this. Click each pad at
   the centre and at each rim.
2. **A39: the centre wins in the overlap.** Click about three quarters of the
   way out. Only the middle click should come.
3. **A40: the two Soft Presses read the thumb's distance**, and the inverted
   one fires reliably on a D-pad-mode pad. R111 bans that on a D-pad stick;
   the Budget audit's check looks at sticks only.
4. **A41: the centre radius.** Read the slider on 90.13.
5. **A short click.** Tap a pad as fast as you can at the centre and at a rim.

## Files

- `build_candidate.py`: the builder. It extends the 10-02 Fallback Hold
  builder, which stays frozen.
- `install_neptune.py`: candidate, release title and description, then the
  fix pipeline, the VDF export and the install record.
- `*-pad-middle-click.json`, `*.readable.json`, `manifest.json`: the candidates.
- `neptune-installation.json`: hashes of what was installed.
- `single-set-*-changes.txt`: the change report against 90.13 (R164).
- `unverified-assumptions.txt`: the assumptions that aren't verified, with
  the rules and scenarios that rest on each (R167). 22 assumptions; 51 of the
  99 scenarios rest on one.
- Tests: `tests/test_pad_middle_click.py` (15, on the generated candidates)
  and `tests/test_scenarios_90_14.py` (12 scenarios, P1 to P12).
