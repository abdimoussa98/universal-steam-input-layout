# Hidden exit: a layer on top covers the lower layer's exit (brainstorm)

**Status, 2026-10-02:** prototype only, not an audit. Rule and discussion from
the 90.11 Fallback Hold work ([record](../2026-10-02-steering-fallback-hold/README.md)).

## The rule

A lower layer's **exit** is a Release that removes it. A finding is a layer the
backward chains can put on top of it that binds the same input (or blocks it
with a different source mode) and whose binding there doesn't remove the
lower layer. Letting go while that layer is up leaves the lower layer on the
stack. The stack is taken after the whole binding that added the upper layer
has run, and the finding names the layer that actually answers the input.
Chords and timing are ignored.

**Correction, 2026-10-02.** The first prototype looked at the stack partway
through a binding. L1 Modifier 0's R1 chord adds `R1: Modifier 1`, then
`R1: Tap Cover` and Modifier 2 on top; judged at `R1: Modifier 1`, it looked
like R1's modifier hid L1's Release. Eight such modifier pairs were reported
and wrongly put down to chords. Judged after the whole binding, Modifier 2
answers both bumpers and its Releases remove both modifiers, so they pass.
Total pairs went from 108 to 100.

The first 90.11 build is the motivating case: the menu Double Tap windows,
the Steering Entry Points and the Fn layers covered the Fallback Hold's stick
up, down and edge Releases. The prototype flags all of them; the final 90.11
(and 90.12) have no Fallback Hold or Entry Guard finding.

## Keeper rule (author, 2026-10-02) and result on 90.13

A **pair** is a lower layer plus a layer that can sit on top of it and covers
one of its exits (example: `Tab` under `L1: Double Tap`; lifting your thumb off
the left pad inside the window misses `Tab`'s Release). Rule: a pair is a
**finding** only if it covers an exit on what keeps the lower layer alive (its
keeper, from the cleanup audit) and the top layer doesn't remove the lower
layer there. A cleanup function removing it later does **not** count (author,
2026-10-02), and "stops the upper one landing" is a fix, not an exception.

Result, both variants:

| | Pairs |
|---|---|
| Findings outside the touchpad exception | 0 |
| Information: the menu Tap Cover over each stick guard covers the stick recentre, but its Start and Select Releases remove the guard | 2 |
| Touchpad, still covering a keeper exit | 68 |
| Touchpad, now information: a pad layer over a menu Entry Point or the right stick guard covers the right-stick click or edge, not Start or Select | 26 |

The 68: 36 Double Tap windows over a left-pad or RTP layer (lifting the
thumb), 4 windows over `RTP: Tap Cover`, 28 `RTP: Double Tap` over a button
layer (releasing a bumper, menu button or stick click). The 26 aren't stuck
layers, since Start or Select still removes the Entry Point, but they still
block the right-stick click Release, the transition gesture.

## Result on 90.12 (both variants the same)

**90.13:** 96 pairs, 94 set aside as touchpad, 2 findings left, both passing
(menu Tap Cover over a stick guard). The 4 turn-assist pairs are gone:
`Steering` blocks the right-stick edge (author, 2026-10-02). The tables below
are the 90.12 run.

100 pairs on 39 lower layers; 72 pairs cover every exit. Unchanged from 90.11:
`cleanup_lists` only edits cleanup lists, not Releases or what can land on top.

| Upper layer | Lower layer has a cleanup function | Pairs |
|---|---|---|
| Always On window | yes | 56 |
| Always On window | **no** | 12 |
| ordinary layer, binds the input | yes | 7 |
| ordinary layer, mode block | yes | 25 |

The 12 window cases with no cleanup are the ones closest to the Fallback Hold
bug: `RTP: Double Tap` over `Menu Left: Escape`, `Menu Right: Tab`, the
Double Tap Covers, the combined bumper Tap Cover and `Menu Buttons: Tap
Cover`; and the L1, R1 and menu windows over `RTP: Tap Cover`.


## Touchpad exception

**Decided by the author, 2026-10-02: the touchpads are an exception for now,
with a to-do to address them** ([todos.md](../../todos.md)). A pair is set
aside, not a finding, when either layer is a touchpad layer (every binding
that adds it is on a trackpad: `Tab`, `Escape`, `Backspace`, `Enter`,
`RTP: Entry Point`, `RTP: Circular Scroll`, `RTP: Double Tap`) or the covered
exit is a trackpad input. The prototype applies it and lists the set-aside
pairs after the findings.

- **Set aside: 94 of 100.** Every window case is touchpad-related: either
  `RTP: Double Tap` is the window, or the lower layer is a left-pad or RTP
  layer whose exit is a pad touch. That includes all 12 window cases with no
  cleanup function, the worst ones.
- **Left: 6,** both kinds with a cleanup function on the lower layer:
  - 2 `Menu Buttons: Tap Cover` over a stick guard. Hold Start, push the
    left stick out (the guard lands), keep holding 200 ms (the cover lands),
    recentre: the guard's edge Release goes to the cover's empty edge, so the
    guard stays. Release Start: the cover's Release removes the cover, both
    guards and the Entry Points. Passes on condition 3.
  - 4 turn assist over the drivers. Base's right-stick edge blocks the normal
    ramp with an either-bumper chord, but its either-trigger chord adds
    `Turning Ramp Up 0` directly and the bumper chord doesn't stop it. Hold R1
    (W), hold a trigger, push the right stick out: the ramp lands on
    `Steering | R1: W Key` and binds R1 (a bumper press cancels the ramp).
    Let go of R1 there and the W layer's Release is lost until its cleanup
    function runs at the next stick touch. The ramp's R1 bind is a repeating
    removal, so with R1 held it may take itself off again and the trigger
    chord put it back (unverified). Mirror on L1 and the S layer; in the
    alternative, the drivers are the triggers and the bumpers fire.

## Proposal for the touchpad exception (2026-10-02, not decided)

The 94 set-aside pairs on 90.13 come from three mechanisms.

| Group | Pairs | What covers what | Proposal |
|---|---|---|---|
| A. A window over a pad layer | 40 | Every Double Tap window clears both pads' touch (`window_pads`), so lifting a thumb off a pad inside a window misses the Release of `Tab`, `Escape`, `Backspace`, `Enter`, `RTP: Entry Point`, `RTP: Circular Scroll` or `RTP: Tap Cover` | Pass on a cleanup function: 36 already have one (a stick touch with the pad untouched removes them). Give `RTP: Tap Cover` the same guarded stick-touch cleanup `RTP: Circular Scroll` has (4 pairs) |
| B. The right-pad window over a button layer | 28 | `RTP: Double Tap` (150 ms) binds the bumpers, the menu buttons and the stick clicks, so their Releases miss the modifiers, covers, second-press layers, menu Entry Points, stick guards and Fn | Each of those binds gets a self-first Release: remove `RTP: Double Tap` first, then the layers that button keeps that can be under it (chains). Same shape as the Steering stick windows' driver Releases |
| C. A pad layer over the menu hold | 26 | Holding a menu button inherits Base's pads, so the left-pad layers and `RTP: Entry Point` can land on an Entry Point. Their right-stick groups are in mouse mode and block the Entry Point's right-stick click Release and the right stick guard's edge Release | The four menu Entry Points keep the pads off the layer API, as `window_pads` does for windows: left-pad directions type Tab, Enter, Backspace and Escape as keys, pad clicks and the right-pad touch are empty, and the right pad stays the mouse. Fn and the guards inherit it |

Not proposed for A: a self-first Release on the pad touch in every window. A
thumb leaving a pad is constant, and it would end windows early: a menu tap
lost before its 50 ms Tab, a modifier double tap cut short.

## Proposed pass conditions (open)

A covered exit passes if (1) the lower layer stops the upper one landing,
(2) the upper layer's bind also removes it, (3) another exit on the same
button still works, or (4) a cleanup function guarded by that button removes
it later. Open question for the author: is (4) good enough? With the touchpad
exception it only decides the turn-assist case. The 12 window cases moved to
the touchpad to-do.

```bash
python3 findings/2026-10-02-hidden-exit/prototype.py neptune/single-set-default_hold-gyro_latest.json
```

`default.txt` and `alternative.txt` hold the full output for 90.13: the findings, then every pair with the touchpad ones included.
