# Plan: port the trigger/ramp-up rework and the findings fixes to both Neptune layouts

- **Date:** 2026-09-27
- **Status:** Steps 1–5 done on 2026-09-27. Both `neptune/*.json` files are edited and pass the static checks. Waiting on step 6 (VDF conversion and in-game testing on the Deck); step 7 follows once testing is confirmed.
- **Parity with July (default variant):** the ported inputs match July after chord decoding, with two intended exceptions. The Base stick-edge Full_Press keeps `haptic_intensity 0`, and July's Mod 2 release lists also remove Split Stick layers that Neptune doesn't have.

## Context

The July exploratory layout (`findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json`, Triton) made two changes:

- It removed the trigger layers.
- It moved the ramp-up gyro handling into Base.

The committed Deck layouts, `neptune/single-set-default_hold-gyro_latest.json` and `neptune/single-set-alternative_hold-gyro_latest.json`, still use the old trigger-layer design, and they lack the fixes documented under `findings/`. This plan ports both changes and those fixes to both variants.

The alternative variant swaps roles: its bumpers act as the triggers, and L2/R2 (soft pull) are the modifiers. Otherwise the two files are parallel: they have the same Preset keys, list order, and group IDs for every group touched here.

**Decisions:**

- **Layer order:** renumber `Preset_` keys in their current list order. The Steam layer list doesn't change.
- **Tap-cover fix:** apply it to all four Mod 2 layers, regular and `(Gyro)`.
- **Start/Select gyro mode shifts:** keep them. They're out of scope for this pass.

## References used

- **Skills:**
  - `steam-layout-prep`: pre-flight check, `to-titles` before any structural edit.
  - `steam-layout-apply`: `to-ids`, the leftover-token check, and the VDF handoff.
  - `steam-binding-order`: the order of every edited binding array.
  - `steam-layer-duplicate`'s rule for new groups (id = max+1) covers the one group this plan creates. No layers are duplicated.
- **Docs:**
  - `README.md`: variant roles and the load-order hazard.
  - `resources/Steam Input JSON Structure.md`: execution order, *Interrupted Delayed Layer Applies* (including the RTP exception), and *Empty Bindings and Stuck Layer Cleanup*.
  - `archived/Ramp Up Layers Comparison.md`: the alternative's trigger and modifier roles inside the ramp-up layers.
- **Findings:**
  - `2026-07-11-layer-order-swap`: list order must match `Preset_` numbering; titles must be unique.
  - `2026-09-27-rtp-entry-ramp-up`: `RTP: Entry Point` stick-edge cleanup (July group 204).
  - `2026-09-27-r1-tap-cover`: the 250 ms repeating removal of the two-bumper tap cover, the 50 ms repeat on Base and Gyro modifier entry, and the RTP exception.
  - `2026-09-27-exploratory-layout-audit`: the source shapes for the port (July groups 5, 43, 299, 417) and the chord decode table.

## Roles per variant

| | Default | Alternative |
|---|---|---|
| Trigger (fires LMB/RMB) | LT/RT `edge` (analog pull) | LB/RB press |
| Modifier entry (Base, Gyro) | LB/RB self-chord in `switch` | LT/RT `edge` Full_Press |
| "Trigger held" chords (`chord_button`) | 5, 6, 7, 8 | 1, 2 |
| "Modifier held" chords | 1, 2 | 5, 6, 7, 8 |
| Trigger layers to delete | L2, R2, (Gyro) L2, (Gyro) R2 | L1, R1, (Gyro) L1, (Gyro) R1 |

July encodes each chord group as a single bitmask activator. Neptune's `chord_button` takes one button, so the port uses **one chord activator per button**.

## Changes (both files, roles from the table)

### 1. Remove the trigger layers

- **Delete six layers:** the four trigger layers plus `(Gyro) Turning Ramp Up 0/1`. Remove each layer's `action_layers` entry, its preset block, and all of its groups.
  - Checked on 2026-09-27: every reference to these layers appears only in Base, Gyro, Turning Ramp Up 0/1, and the deleted layers themselves. None are in other layers, dormant groups, or the 50 orphan groups, and no group is shared between presets.
- **Default Base:** drop the LT/RT `click` input (the add-L2/R2 cleanup bind). The `edge` → LMB/RMB bind stays.
- **Alternative Base:** make LB/RB Full_Press plain `mouse_button LEFT` / `mouse_button RIGHT`, with no settings. The current `hold_repeats` must not carry over, or the mouse button would act as turbo.
- **Gyro layer:** the default drops LT/RT `click` (→ (Gyro) L2/R2), and the alternative drops LB/RB (→ (Gyro) L1/R1). The trigger then falls through to Base.

### 2. Move ramp-up gyro logic into Base (July shape)

- **Rename** `Gyro Off` → `Gyro Off Ramp Up`. It stays the same layer (not a new one) and keeps its disabled gyro; update every token that references it.
- **Gyro Off Ramp Up gains two things:**
  - **A new `right_joystick` group** (id = max+1, `settings: {"layer": "1"}`), added to its preset as `right_joystick active`. Its `edge` gets two Soft_Press activators, copied from July group 417:
    - [0] 25807, inverted, `hold_repeats` → remove Gyro Off Ramp Up
    - [1] 29031, `delay_start: 5` → add Turning Ramp Up 0
  - **A trigger removal:** `{hold_repeats: 1, interruptable: 0}` → remove Gyro Off Ramp Up. In the default it goes on LT/RT `edge` Full_Press (July group 299). In the alternative it goes on LB/RB Full_Press in the layer's `switch` group.
- **Base RS `edge`:** replace the Soft_Press (→ TRU0 + Gyro Off) with:
  - Full_Press `{hold_repeats: 1, haptic_intensity: 0}` → add Gyro Off Ramp Up. The `haptic 0` is kept from Neptune's old bind.
  - One chord per "trigger held" button, `{hold_repeats: 1}` → add Turning Ramp Up 0.
  - One chord per "modifier held" button, `{hold_repeats: 1, interruptable: 0}` → `empty_binding`.
- **Gyro layer:** delete its RS `edge` input and set that `right_joystick` group inactive, as July does. Gyro mode then uses Base's flow.
- **Turning Ramp Up 0/1:**
  - **Cleanup lists:** drop the `(Gyro)` TRU and trigger-layer entries, and change `Gyro Off` → `Gyro Off Ramp Up`.
  - **Modifier inputs** (default LB/RB; alternative LT/RT `click`): make them cleanup followed by `empty_binding`, instead of adding the regular modifier. The set's own modifier entry, which repeats, then re-adds the correct variant: regular in Base, `(Gyro)` in Gyro mode. This is what lets the `(Gyro)` TRU layers go.
  - **TRU0:** add RS `edge` Full_Press `{hold_repeats: 1, repeat_rate: 300, interruptable: 0}` → remove Turning Ramp Up 1, as in July group 43. It pairs with the 250 ms delayed apply of TRU1, which is the same reset pattern as the tap cover.
  - **Alternative TRU layers:** keep `edge` → empty, so a partial pull still can't enter a modifier mid-ramp while a full pull exits it. Their `switch` groups stay unbound, so the bumpers keep firing mouse buttons.
- **Base and Gyro modifier entry:** add `repeat_rate: "50"` on top of the existing `hold_repeats`. In the default that's the LB/RB chords; in the alternative, LT/RT `edge` Full_Press.

### 3. Fixes from findings

- **`RTP: Entry Point`** (group 1163 in both files): the RS `edge` becomes
  - a chord `{chord_button: 17 (RTP touch), interruptable: 0}` → `empty_binding`, and
  - a Full_Press `{hold_repeats: 1}` → [remove RTP: Entry Point, remove RTP: Tap Cover].

  No repeating removal is added on the RTP touch path, which honours the trackball-momentum exception.
- **Tap-cover delayed-apply reset, in all four Mod 2 layers:** on the input that carries the 200 ms apply chord, add Full_Press `{hold_repeats: 1, repeat_rate: 250, interruptable: 0}` → remove the two-button cover. None of these inputs has a Full_Press today.
  - **Default:** `right_bumper` in L1!R1 and (Gyro) L1!R1; `left_bumper` in R1!L1 and (Gyro) R1!L1. Target: `L1&R1: Tap Cover`.
  - **Alternative:** `right_trigger` `edge` in L2!R2 and (Gyro) L2!R2; `left_trigger` `edge` in R2!L2 and (Gyro) R2!L2. Target: `L2&R2: Tap Cover`.
- **Layer order:** after the deletions, reassign the sorted set of the 50 remaining layer keys in list order. Update `preset[].name` to match and resequence the preset `id` fields to 0..50. Base stays `Preset_1000001`. Preset keys are referenced nowhere else (checked).
- **Unique titles:** deleting the layers, rather than emptying them into `DEPRECATED` as July did, keeps every title unique.

## Execution

1. Run the pre-flight check on both files. Expected result: `layer order` out of order, preset blocks OK, ids OK, no duplicate titles.
2. Run `convert_runtime_ids.py to-titles --output` into a scratch working copy. This must come before any deletion, because the numeric IDs are positional.
3. Apply the changes with a one-off Python edit script, driven by one role config per variant.
   - It finds groups by (layer title, source, `active`), not hard-coded IDs.
   - It reuses the `find_max_group_id` pattern from `duplicate_layer.py` and the preset/group removal pattern (`find_groups_to_delete` + gsb cleanup) from `delete_action_set_complete.py`.
   - It writes with `json.dumps(indent="\t", ensure_ascii=False)` and no trailing newline. This was verified to reproduce both current files byte for byte.
   - Every array it writes follows `steam-binding-order`: cleanup removals below, the final action on top.
4. Run `to-ids --output`, then the leftover-token grep and the pre-flight check.
5. Copy the results over `neptune/*.json`.
   - The numeric diff will be large, because deleting layers shifts the runtime IDs of everything after them. Review the title-form diff instead.
6. **Your part:** convert both JSON files to VDF with `pfwobcke.vscode-vdf`, replacing `neptune/*.vdf`. Then load them fresh on the Deck and run the in-game checks below.
7. **Once testing is confirmed:**
   - Check off the three ramp-up/trigger todos.
   - Update the two sections of `resources/Steam Input JSON Structure.md` that still describe Neptune as lacking these fixes.

## Verification

**Static checks (before handing off):**

- **Pre-flight:** all OK, no duplicate titles.
- **Token round-trip:**
  - `to-ids` prints no warnings.
  - The leftover-token grep prints 0.
  - Running `to-titles` on the result reproduces the edited title-form file.
- **Deleted layers:** no token anywhere references one, including inactive and orphan groups.
- **Semantic diff (audit normalizer, old vs new):**
  - Changed layers are limited to Base, Gyro, Turning Ramp Up 0/1, Gyro Off → Gyro Off Ramp Up, RTP: Entry Point, and the four Mod 2 layers.
  - The six deleted layers are gone.
  - Every other layer is identical.
- **Parity:**
  - The default's ported bindings match July's after chord decoding.
  - The alternative's bindings match the default's with roles swapped.

**In-game checks (fresh load on the Deck, both variants):**

1. The triggers fire LMB/RMB (bumpers in the alternative). The menu buttons now also work while a trigger is held, because the trigger layers used to block them.
2. RS to the edge with no trigger held: gyro turns off, ramp-up stage 2 follows after about 250 ms, and moving the stick back in restores gyro and clears ramp-up.
3. RS to the edge with a trigger held: ramp-up with gyro still on.
4. Trigger pulled mid-turn: gyro comes back on and the first shot still fires. Gyro Off Ramp Up's trigger bind only removes the layer, so this relies on Base's held mouse bind taking over. The alternative's old L1/R1 layers already relied on the same behavior.
5. Modifier pressed during ramp-up: ramp-up exits and the correct modifier enters, regular in Base and `(Gyro)` in Gyro mode.
6. Stuck RTP: R1 → RTP touch → release both, in both orders → stick to the edge. Ramp-up works, and holding RTP still suppresses the edge.
7. Two-button tap cover: interrupt the 200 ms apply, then retry. The cover applies.
8. Toggling Gyro mode via Mod 2 still works, and there's no new haptic pulse at the stick edge.

## Not included (other July changes)

- Split Stick steering, Gated Gyro, the trackpad one-shot rework, the nav-key reshuffle, and the WASD modifier
- Removal of the Fn-layer stick-click mode shifts
- The Gyro layer's trigger mode shifts (audit issues 3–4)
- July's ramp-up sensitivity values (150/80 and 200/67) and base gyro tuning
- The Start/Select gyro mode-shift removal (kept by decision)

## Files

- **Modified:**
  - `neptune/single-set-default_hold-gyro_latest.json`
  - `neptune/single-set-alternative_hold-gyro_latest.json`
  - Their `.vdf` files (regenerated by you)
  - After testing: `todos.md` and `resources/Steam Input JSON Structure.md`
- **Not committed:** the one-off edit script and the working copies. The script can go in `archived/` if you want a record.
