# Remove banned activators and dead groups

Status: **implemented in 90.6 (2026-09-30); Deck gates D1–D5 untested.** See the
[record](../findings/2026-09-30-dead-group-prune/README.md). The RTP fix and prune
run inside `findings/2026-09-30-steering-lean/install_neptune.py`, so steering
reinstalls repeat them.
Steering's own Long Presses are covered by the
[chorded-delay plan](2026-09-30-steering-chorded-delays.md); this plan covers
everything else.

## Goals

1. Remove the remaining banned activators outside steering (see
   [allowed activation types](../resources/Steam%20Input%20JSON%20Structure.md#allowed-activation-types)).
2. Delete dead groups: unreferenced groups and plain-inactive source slots.
   Steam never runs them, but they hide banned activators and make audits noisy.
3. Stop the steering builder from creating new orphans, and make the audit
   fail if any of this comes back.

Runtime behavior must stay the same everywhere except the RTP scroll change,
which is meant to be equivalent.

## Survey (2026-09-30, title form)

| | Default | Alternative |
|---|---:|---:|
| Groups | 684 | 693 |
| Unreferenced groups | 116 (80 non-empty) | 114 (78 non-empty) |
| of which steering-builder orphans (IDs 13045+) | 56 | 54 |
| Plain-inactive source slots | 153 (20 non-empty) | 152 (20 non-empty) |
| Groups shared between active and inactive slots | 0 | 0 |
| Mode-shift targets (`inactive modeshift`, referenced by `mode_shift`) | 6 | 6 |
| Layers never added | only `Base` | only `Base` |
| Non-empty `disabled_activators` banks | 0 | 0 |

Where the unreferenced groups come from:

- **Deleted action sets:** IDs 0–44 are empty or near-empty per-set group
  templates, plus older strays such as 85, 139, 145, 174–192, 10 and 17–38.
- **Earlier edits:** 627, 777, 781, 1161–1162, 1247, 1260–1261 and 1320 are
  replaced copies of live groups.
- **Steering builder:** 13045–13164. `group()` in the builder unbinds a
  layer's old group and appends a new one without deleting the old one. Six
  of these still hold copies of the steering Long Presses.

The 20 non-empty plain-inactive slots are the same group IDs in both variants:
`195, 600, 613, 790, 791, 12984, 12985, 12958, 12962, 12963, 12964, 587, 732,
586, 731, 13026, 13027, 683, 924, 1025`. They include the four Double Press groups.

## Violation 1: `RTP: Mouse Buttons` Long Press (live)

Right trackpad in dpad mode, group `242`, identical in both variants. The layer
is held by a Soft Press on the pad click (`hold_layer`), with a repeating
self-removal.

| Input | Now | Replacement |
|---|---|---|
| `dpad_north` | Full_Press wheel up (immediate tick) + Long_Press 150 ms, `hold_repeats` | Full_Press unchanged + **chord**, mask right-pad touch (bit 20, `1048576`), Any, `delay_start 150`, `hold_repeats 1`, `haptic_intensity 0`, wheel up |
| `dpad_south` | Same, wheel down | Same, wheel down |

- Tap: one tick. Hold: repeating ticks from 150 ms. That matches today's behavior.
- Touch is the chord condition because it is always true while a direction
  registers. The click bit (18, `262144`) could drop below full click while
  the Soft Press still holds the layer.
- Copy the Long Press's settings exactly (no `repeat_rate`), so the repeat
  cadence stays Steam's default. The budget stays at 2 entries per input.
- No layer is added, so no interrupted-delay reset is needed.
- Bit indices come from the installed Steam UI bundle's
  `k_eGamepadButtonBitMask_*` table (`chunk~2dcc5aaf7.js`, the same bundle as the
  [chord selector verification](../findings/2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md)).
  The relevant bits are: RightPadClicked 18, CapSenseRightTouchPad 20,
  AxisDeflectionLeftStick 30 and AxisDeflectionRightStick 31. Add this table
  to the verification record when implementing.

## Violation 2: stick-touch Double Press (dead)

All four are in plain-inactive slots, so none of them run:

| Owner layer | Slot | Group | Double Press (300 ms) |
|---|---|---|---|
| `Gyro` | `joystick inactive` | 12985 | add `LST: Temporary Gyro` |
| `Gyro Off Ramp Up` | `joystick inactive` | 13027 | add `LST: Temporary Gyro` |
| `LST: Temporary Gyro` | `right_joystick inactive` | 732 | add `RST: Temporary Gyro` |
| `RST: Temporary Gyro` | `joystick inactive` | 731 | add `LST: Temporary Gyro` |

These are leftovers from the old double-touch temporary-gyro design, which the
layer-based LST/RST Double Tap windows replaced. **Delete them; no
replacement is needed.** Step 2 removes them as part of the dead-group prune.

## Steps

### 1. Cleanup script (`prune_dead_groups.py`, repo root)

Make it idempotent and runnable on title-form or ID-form JSON, with
`--dry-run` and `--json` reports. Per file:

1. Remove every **plain-inactive** entry (state exactly `inactive`) from each
   `preset[].group_source_bindings`.
2. Keep entries whose state is `active` or contains `modeshift`. Also keep any
   group that a `mode_shift` binding references, whatever its state.
3. Delete every group that no longer has any reference.
4. Don't renumber group IDs or touch layers, presets, `actions` or
   `action_layers`. Runtime IDs can't shift.

Decision to confirm while implementing: three `inactive modeshift` slots are
not targeted by any `mode_shift` binding (Base `button_diamond` 86,
`right_joystick` 212, `left_trackpad` 246). This plan **keeps** them to limit
scope. Removing them is a separate, optional step.

`disabled`-mode groups (639 `Menu Left: Fn Layer` gyro, 856 `RST: Double Tap`
left_trackpad) are **active** slots that disable a source on purpose. Keep them.

### 2. Apply

1. Fix RTP (Violation 1) in title form.
2. Run the prune.
3. Report counts. Expected: 0 unreferenced groups and 0 plain-inactive slots,
   with the mode-shift count unchanged at 9 slots and 6 targets.

### 3. Prove no behavior change

Write a one-off equivalence check (kept under `findings/<date>-dead-group-prune/`):

- For every preset, the set of `active` / `modeshift` slots and their group
  contents are identical before and after. The only exception is group 242's
  `dpad_north` and `dpad_south`.
- Layer list, titles, preset order, `to-titles` → `to-ids` roundtrip and
  command-budget results are unchanged.
- No `Long_Press` or `Double_Press` remains outside steering. After the
  steering plan lands, none remain anywhere.

### 4. Stop regressions

- **Builder:** in `findings/2026-09-30-steering-lean/build_candidate.py`
  (`group()`), delete the replaced group when no other preset still references
  it. It must not delete orphans that were already in the input, which the prune
  script owns.
- **Audit:** extend `audit_command_budget.py` to fail (exit 1) on any
  `Long_Press` or `Double_Press` in any group, and to report unreferenced and
  plain-inactive counts. The `steam-layout-apply` pre-flight already requires
  exit 0, so the rule is then enforced on every export. Turn the failure on
  only after both plans have landed, or current layouts can't export.
- **Tests:** add `tests/test_layout_hygiene.py` for both variants: no banned
  activators, no unreferenced groups, no plain-inactive slots, RTP chord shape
  (mask, `delay_start`, `hold_repeats`), and a check that every `mode_shift`
  target exists.

### 5. Sequencing with the steering plan

The steering builder rebuilds from the **frozen pre-steering backup**, which
still contains all of this dead code and the RTP Long Press. Any direct edit
to `neptune/*` is lost the next time steering is reinstalled. So:

1. Build and install steering with chorded delays, following that plan.
2. Run this plan (RTP fix, then prune) on the installed `neptune/*` files.
3. Validate, update metadata, export and snapshot once for both plans.
   Release as **90.6**, or refresh 90.5 if it was never loaded into Steam.
4. Add "run `prune_dead_groups.py` and the RTP fix" to the steering install step,
   so any later reinstall repeats it. Alternatively, move the RTP fix into a
   script both paths call.

### 6. Docs and metadata

- Empty the known-violations list in
  [allowed activation types](../resources/Steam%20Input%20JSON%20Structure.md#allowed-activation-types)
  and note that the audit enforces the rule.
- Add the full bitmask table to the chord selector verification record.
- Description: no user-visible change beyond RTP scroll, which behaves the
  same. Review it anyway, following the publishing rules.
- Update `todos.md` and `manual-testing.md` with the Deck gates below.

## Deck gates (all untested)

| Gate | Exercise | Required result |
|---|---|---|
| D1 fresh load | Load 90.6 fresh in both variants; open each layer in the editor | Loads without error; no missing or blank sources; layer binds match 90.5 apart from steering and RTP |
| D2 RTP scroll | Click the right pad; tap up/down; hold up/down for 1 s; release the direction but keep clicking; release the click | Tap gives one tick; hold gives one tick, then repeats from 150 ms at the old cadence; nothing continues after the direction or click is released |
| D3 RTP edges | Forward/back and edge middle click while scrolling | Unchanged |
| D4 mode shifts | Exercise the Base dpad/face mode shifts and the Menu Left/Right Fn stick mode shifts | Unchanged |
| D5 temporary gyro | Double-touch each stick in Gyro, Gyro Off Ramp Up and the LST/RST temporary gyro layers | Same as 90.5. The deleted inactive Double Press groups never ran, so nothing changes |

If D1 fails, the load depends on something that was pruned. Restore from
`versions/neptune/90.5/` and bisect the prune by category: first the templates
from deleted action sets, then earlier-edit orphans, builder orphans and
inactive slots.
