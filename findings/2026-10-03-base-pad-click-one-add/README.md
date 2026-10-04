# Base adds the Click Entry Point with one Soft Press (90.20)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.20**, with the
snapshot in `versions/neptune/90.20/`. Device status: **untested**. The build
audit is clean and the tests pass.

The author played [90.19](../2026-10-03-pad-click-holds/README.md): it works
and looks good.

## The change (author, 2026-10-03)

In `Base`, each pad's click had two Soft Presses that both add the Click Entry
Point. The author saw the pair in Steam and asked for one.

| `Base` pad click | 90.19 | 90.20 |
|---|---|---|
| First Soft Press | Adds the Click Entry Point, haptic 3, no Hold to Repeat | Kept as it is |
| Second Soft Press | Adds it again every 50 ms, no haptic | Removed |

One layer and two bindings changed per layout
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)).

## Which of the two was kept

The author described them as "one repeating at 50, one repeating at 100" and
asked to keep the one at 100. In the file only the second one repeats, at
50 ms. The first has Hold to Repeat off and states no rate, so 100 is what
Steam shows for a rate that isn't set. That first one is the one kept, exactly
as it was: it adds the layer once per press, with the bump.

If the add should repeat, it needs Hold to Repeat turned on. On this one
binding that would also repeat the bump, which is why 90.16 split it in two.

## Why there were two

90.16 added the second one at the author's request, as a safety net: if
something removed the Click Entry Point while the pad was still pressed, the
repeat put it back. It was a separate, silent binding so that the bump stayed
on the press alone.

Since 90.18 the Click Entry Point removes itself when it hands over, so a
repeat that puts it back works against the hand-over. With one add, Base is
back to the shape of 90.14, 90.15 and 90.13's hold: one layer command per
press.

## What changes in behaviour

Only one case, on the simulator: every layer is cleared while the pad is still
pressed (the Modifier 2 quick tap, a menu-plus-stick-click clear). Until 90.19
the repeat brought the click layer back within 50 ms. Now it comes back only
if Steam fires the add it exposed under the held click (A9, unverified).
Otherwise the next click brings it. Scenarios 90.16 X3 and 90.17 S1 were
rewritten to say so.

## Scenarios and tests

- `tests/test_scenarios_90_20.py`, B1 and B2: a click held for two seconds
  adds the Click Entry Point once and bumps once, on both pads; three clicks
  in a row each work.
- `tests/test_base_pad_click_one_add.py`: the binding above, and that nothing
  else changed against 90.19.

## Files

- `build_candidate.py`: the builder. It extends the 10-03 holds builder, which
  stays frozen.
- `install_neptune.py`, `*-base-pad-click-one-add.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.19 (R164).
- `unverified-assumptions.txt`: the assumptions that aren't verified, with
  what rests on each (R167).
