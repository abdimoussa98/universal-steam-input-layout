# Banned activators and dead groups removed (90.6)

Date: 2026-09-30. Implements the
[plan](../../plans/2026-09-30-banned-activators-and-dead-groups.md) together with
the [steering chorded delays](../../plans/2026-09-30-steering-chorded-delays.md).
Static checks pass; **Deck gates D1–D5 are untested.**

## Result

| | Default | Alternative |
|---|---:|---:|
| Groups before (90.5) | 684 | 693 |
| Replaced groups the steering builder now deletes | 66 | 64 |
| Plain-inactive slots removed | 155 | 154 |
| Groups removed by the prune | 203 | 202 |
| Groups after (90.6) | 415 | 427 |
| Unreferenced groups / plain-inactive slots after | 0 / 0 | 0 / 0 |
| Long Press / Double Press after | 0 / 0 | 0 / 0 |

Kept: every `active` slot (including the two `disabled`-mode groups 639 and 856,
which switch a source off on purpose), every `modeshift` slot, and all six
`mode_shift` targets. The three `inactive modeshift` slots that nothing targets
(Base 86, 212, 246) were kept as planned. Group IDs, layers, presets, `actions`
and `action_layers` are unchanged, so no runtime ID moved.

The four inactive stick-touch Double Press groups (12985, 13027, 732, 731)
were among the pruned inactive slots. They never ran.

## RTP scroll

`RTP: Mouse Buttons` right trackpad (group 242), `dpad_north` / `dpad_south`:
the immediate Regular Press wheel tick stays; the 150 ms Long Press became a
chord on right-pad touch (bit 20, `1048576`, Any) with `delay_start 150`,
`hold_repeats 1`, `haptic_intensity 0`. It adds no layer, so it has no reset,
which matches RTP's deliberate trackball-momentum exception.

## Equivalence proof

`check_equivalence.py` compared every live slot input (1245 Default, 1301
Alternative), mode/settings with group ID, mode-shift targets, layer order and
titles, and preset order against `versions/neptune/90.5/`. The only differences
are the seven intended inputs:

- `Steering` LS up (warning and exit)
- `LS Up: Modifier 1` up, `LS Down: Modifier 0` down (consume + reset)
- `LS Up: Double Tap` and `LS Down: Double Tap` edge (window clock)
- `RTP: Mouse Buttons` pad up and down

```sh
python3 findings/2026-09-30-dead-group-prune/check_equivalence.py \
  versions/neptune/90.5/single-set-default_hold-gyro_90.5.json \
  neptune/single-set-default_hold-gyro_latest.json \
  --allow "Steering|joystick active|dpad_north" \
  --allow "Steering | LS Up: Modifier 1|joystick active|dpad_north" \
  --allow "Steering | LS Down: Modifier 0|joystick active|dpad_south" \
  --allow "Steering | LS Up: Double Tap|joystick active|edge" \
  --allow "Steering | LS Down: Double Tap|joystick active|edge" \
  --allow "RTP: Mouse Buttons|right_trackpad active|dpad_north" \
  --allow "RTP: Mouse Buttons|right_trackpad active|dpad_south"
```

Other checks: command budget and banned-activator audit pass (exit 0),
pre-flight order/ID checks pass, no unresolved tokens, VDF export verified, and
86 Python and 8 Node tests pass. The held-input scanner now reports no
findings, because the old steering Long Presses were its only entries.

## Tools

- [`prune_dead_groups.py`](../../prune_dead_groups.py) (repo root): generic and
  idempotent, with `--dry-run` and `--json`.
- [`steam_layout/fixes/rtp_scroll.py`](../../steam_layout/fixes/rtp_scroll.py): idempotent RTP fix.
- [`check_equivalence.py`](check_equivalence.py): live-binding diff with an
  allow-list.
- [`install_neptune.py`](../2026-09-30-steering-lean/install_neptune.py) runs the
  RTP fix and prune on every steering install, because the builder's frozen
  pre-steering source still contains both.

## Deck gates (untested)

| Gate | Exercise | Required result |
|---|---|---|
| D1 fresh load | Load 90.6 fresh in both variants; open each layer in the editor | Loads without error; no missing or blank sources |
| D2 RTP scroll | Click the right pad; tap up/down; hold 1 s; release direction, then click | Tap gives one tick; hold gives one tick, then repeats from 150 ms at the old cadence; stops on release |
| D3 RTP edges | Forward/back and edge middle click while scrolling | Unchanged |
| D4 mode shifts | Base dpad/face mode shifts and Menu Left/Right Fn stick mode shifts | Unchanged |
| D5 temporary gyro | Double-touch each stick in Gyro, Gyro Off Ramp Up and the LST/RST temporary gyro layers | Same as 90.5 |

If D1 fails, restore `versions/neptune/90.5/` and bisect the prune by category
(deleted-action-set templates, earlier-edit orphans, builder orphans, inactive
slots).
