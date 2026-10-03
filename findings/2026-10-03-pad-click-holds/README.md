# The final pad click layers hold themselves (90.19)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.19**, with the
snapshot in `versions/neptune/90.19/`. Device status: **untested**. The build
audit is clean and the tests pass.

The author played [90.18](../2026-10-03-pad-click-handoff/README.md): it works
as intended, but the haptics seem to repeat while a click is held.

## The changes (author, 2026-10-03)

| Layer | Pad input | 90.18 | 90.19 |
|---|---|---|---|
| `LTP: Arrow Keys`, `RTP: Mouse Buttons`, `LTP: Middle Click`, `RTP: Middle Click` | click | Inverted, repeating Soft Press removes the layer | A Soft Press that holds the layer itself (`hold_layer`), and behind it the same inverted, repeating removal |
| Click Entry Point | edge, both Soft Presses | Remove the Click Entry Point, then add the chosen layer | Add the chosen layer, then remove the Click Entry Point |

Six layers and six bindings changed per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

- **The hold is the 90.13 self-hold, unchanged** (author: "keep it as 90.13
  had it since that was working"): a Soft Press on the click, uninterruptible,
  no haptic, no start delay and no repeat. A test compares its settings with
  the 90.13 snapshot.
- **What the hold is for** (author): it tracks the removal. The author expects
  a hold to behave like a Release with a removal: when the Soft Press is no
  longer active, the layer goes. It fires once, so nothing about it can
  repeat.
- **The inverted removal is the backup**, because holds are unreliable.
- **The Click Entry Point gets no hold.** `add_layer` still puts every layer
  on. Base, the thumb-lift Releases, the outputs and the timings are as in
  90.18.

## The exception to R101

R101 says never `hold_layer`. The author made an exception for the trackpad
click layers. It is in the exceptions register as accepted, with four
commands per layout, each a layer holding itself. A test fails if any other
layer holds, or if one of these holds another layer
(`test_only_the_four_final_pad_layers_hold_and_only_themselves`).

The layers stay inside the audits: `add_layer` is what adds them, so the
chains still reach them. The audits don't follow the holds themselves.

## What isn't known

- **Whether the hold fires at all in an ordinary click.** A final layer
  always lands on a pad that is already pressed. By the held-input rule (A5)
  a layer command with no delay and no repeat doesn't fire on an input that
  was already held. The author chose the 90.13 shape knowing that. If the hold
  doesn't fire, the backup removal does all the work, as in 90.18.
- **Whether a hold removes a layer that `add_layer` put on.** In 90.13 Base's
  own hold put the layer on first. This is assumption A42, new, unverified,
  and the layout works either way.
- **Why the haptics repeated in 90.18.** Not found. The suspect was Base's
  repeating add putting the Click Entry Point back on every 50 ms once the
  layer removes itself; the author said not to change that, so Base is
  untouched. If the haptics still repeat on 90.19, that is the next thing to
  try.

## The press simulator

It refused `hold_layer` until now. It runs it since 90.19: the layer goes on
when the hold's commands run, and comes off when the same press is let go. A
switch (`hold_releases`, A42) turns the second half off, and a hold that is
covered by another layer is left alone. On the simulator an ordinary click
never reaches the hold (A5), so the 90.14 to 90.18 scenarios pass unchanged.

## Scenarios and tests

- `tests/test_scenarios_90_19.py`, K1 to K3, each run with A42 both ways: an
  ordinary click on both pads; a fresh press inside a final layer, which is
  the one case where the hold fires on the simulator; the thumb lifting and a
  missed release.
- `tests/test_pad_click_holds.py`: the bindings above, on the generated
  candidates.
- `tests/test_simulator.py`: four tests for `hold_layer`.

## Files

- `build_candidate.py`: the builder. It extends the 10-03 hand-over builder,
  which stays frozen. The holds are written after the frozen builders finish,
  because the 90.14 builder refuses any `hold_layer`.
- `install_neptune.py`, `*-pad-click-holds.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.18 (R164).
- `unverified-assumptions.txt`: 23 assumptions that aren't verified; 66 of the
  117 scenarios rest on one (R167).
