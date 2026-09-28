# Plan: remove the Start / Select gyro mode shifts and reshuffle the nav keys in both Neptune layouts

- **Date:** 2026-09-27
- **Status:** Steps 1–5 done on 2026-09-27. Both `neptune/*.json` files are edited and pass the static checks. Waiting on step 6 (VDF conversion and in-game testing on the Deck); step 7 follows once testing is confirmed.
- **Parity:** the regular layers' Start / Select inputs match July after chord decoding. Each `(Gyro)` copy matches its regular layer, and the alternative matches the default with roles swapped.

## Context

The July exploratory layout made two changes to the modifier layers that the Neptune files don't have yet ([audit](../findings/2026-09-27-exploratory-layout-audit/AUDIT.md) §3 and §4):

1. **Start / Select gyro mode shifts removed.** Holding Start or Select inside a modifier layer used to switch the gyro to a separate mode-shift group. July relies on the Base gyro activation mask instead.
2. **Nav keys reshuffled.** Insert / Delete / Home / End / PgUp / PgDn moved between Mod 0, Mod 1, and Mod 2.

This plan ports both changes to `neptune/single-set-default_hold-gyro_latest.json` and `neptune/single-set-alternative_hold-gyro_latest.json`. It builds on the trigger / ramp-up port (commit `4c351cd`, branch `neptune-trigger-rampup-port`). The two plans touch different inputs, so they don't interact.

Names used below:

- **Start** is Menu Right, `button_escape`.
- **Select** is Menu Left, `button_menu`.
- **The 8 modifier layers:**
  - **Default:** L1: Modifier 0, R1: Modifier 1, L1!R1: Modifier 2, R1!L1: Modifier 2, plus their `(Gyro)` copies.
  - **Alternative:** the same layers named L2 / R2.

The two files are structurally identical here. They have the same group IDs and the same binding shapes. The only difference is the chord button: LB / RB in the default, LT / RT soft pull in the alternative.

## Decisions (defaults I picked; say if you want them flipped)

- **The nav-key reshuffle also goes into the `(Gyro)` copies.** July only changed the regular layers. The audit flagged that drift ([Issue 2](../findings/2026-09-27-exploratory-layout-audit/AUDIT.md#issues-to-check)): the same combo would give a different key in Gyro mode.
- **Delete the dormant gyro mode-shift groups.** July removed the bindings and left the groups in place, unreferenced. This plan deletes all 20 per file: the 9 targets, plus 11 older leftovers in the same layers that nothing references today. This follows the previous plan's rule of deleting dead config rather than leaving it dormant. No behavior depends on it.
- **No gyro mask changes.** This matches July.

## References

- **Skills:**
  - `steam-layout-prep`: pre-flight, `to-titles` before editing.
  - `steam-layout-apply`: `to-ids`, the leftover-token check, and the VDF handoff.
  - `steam-binding-order`: the edited binding arrays keep their order.
- **Findings:**
  - `2026-09-27-exploratory-layout-audit`:
    - §3: the gyro mask and the 9 shift targets
    - §4: the nav-key table
    - Issue 2: the `*` copies drifting from the regular layers
    - Issue 3: two or three shifts on one press
  - `2026-07-11-layer-order-swap`: key order must match list order. It already does after the port, and this plan doesn't add, delete, or move any layer.
- **Todos:** the carried-over item "Make base gyro activation dependent on … all being held at the same time. This removes the need for mode shifts everywhere we want to hold Start and Select."

## Change 1: remove the Start / Select gyro mode shifts

### Where they are (identical in both files)

In every modifier layer's `switch` group, the Start and Select inputs have a `Full_Press` list:

- `[0]` is the cleanup (removes the modifier layers and tap covers). **It stays.**
- Every entry after it holds nothing but a `mode_shift gyro <group>` binding. **These go.**

| Layer (default / alternative) | Switch group | Mode shifts per button | Target groups |
|---|---|---|---|
| L1 / L2: Modifier 0 | 59 | 1 | 1302 |
| R1 / R2: Modifier 1 | 160 | 1 | 1304 |
| L1!R1 / L2!R2: Modifier 2 | 599 | 2 | 1307 (D-pad), 1308 |
| R1!L1 / R2!L2: Modifier 2 | 603 | 1 | 1310 |
| (Gyro) … Modifier 0 | 12911 | 2 | 1302, 12927 |
| (Gyro) … Modifier 1 | 12931 | 2 | 1304, 12946 |
| (Gyro) … L!R: Modifier 2 | 12950 | 3 | 1307, 12957, 1308 |
| (Gyro) … R!L: Modifier 2 | 12961 | 2 | 1310, 12970 |

That's 28 mode-shift activators and 9 target groups per file. The `(Gyro)` copies also fire the regular layer's shift, which is a leftover from duplicating the layers.

Because Mod 2 fires two or three shifts on one press, it hits audit Issue 3 (whichever one Steam applies last wins). Removing them all resolves that too.

### Edits

1. **Drop the shift activators.** In each of the 16 Start / Select inputs above, drop `Full_Press[1:]`. The single cleanup activator that remains is stored as a plain object, not a one-item list, which matches July.
2. **Delete the groups.** In the same 8 layers, delete all 20 `gyro inactive modeshift` groups and their `group_source_bindings` entries:
   - the 9 targets
   - the 11 unreferenced leftovers: 1301, 1303, 1305, 1306, 1309, 12926, 12945, 12954, 12955, 12956, 12969
3. **Leave everything else alone.**
   - The other mode shifts stay: Base trackpad touch, and the Fn-layer stick clicks.
   - The Menu layers have no gyro shifts (their gyro is `disabled`), so there's nothing to do there.
   - No gyro mask changes.

### Why no mask change, and what changes in play

**Base's mask is already there.** Base gyro group 576 already lists Start, Select, LS / RS touch and LS / RS deflect with "require all" (`gyro_ratchet_button_requireany_or_all: 1`). "All" means Start or Select on their own never satisfy the mask. The regular modifier layers have no gyro group of their own, so they use this one.

**Gyro mode has its own gates.** In Gyro mode, each `(Gyro)` modifier layer has its own active gyro group, gated by *any* LS / RS touch or deflect, with no Start / Select bits. So Start / Select don't affect those either.

**After the change, Start and Select no longer change the gyro in any modifier layer.** The gyro behaves exactly as it does in that layer when they aren't held. July behaves the same way.

**What the old shifts did can't be fully settled from the file.** The targets are layer groups that store only `gyro_button_invert: 0`, or, in Mod 2, a D-pad with no bindings. Layer groups appear to store only their differences from Base's group. In-game check 3 is where you confirm the new behavior is what you want.

## Change 2: nav-key reshuffle

Swap only the key token in the existing chord bindings. Each binding keeps its second command (the tap-cover `add_layer`), its chord button, and its settings. All 16 are plain `"key_press KEY, , "` strings with no custom labels.

| Modifier (default / alternative layer) | Start + modifier | Select + modifier |
|---|---|---|
| Mod 0 (L1 / L2: Modifier 0) | PAGE_UP → **INSERT** | PAGE_DOWN → **DELETE** |
| Mod 1 (R1 / R2: Modifier 1) | INSERT → **HOME** | DELETE → **END** |
| Mod 2 (both L!R and R!L layers) | HOME → **PAGE_UP** | END → **PAGE_DOWN** |

This applies to the regular layers and their `(Gyro)` copies: 16 bindings per file.

## Execution

1. **Pre-flight both files.** Expected: all OK, since the port already fixed the key order.
2. **Convert to titles.** Run `convert_runtime_ids.py to-titles --output` into a scratchpad working copy.
3. **Run a one-off edit script,** built the same way as the port's:
   - It finds groups by (layer title, source) and asserts the current shape before each edit. Examples: the Full_Press list is cleanup plus only gyro mode shifts, and each old key is exactly what the table above says.
   - It removes the shift activators and the 20 groups.
   - It swaps the 16 keys.
   - It writes with `json.dumps(indent="\t", ensure_ascii=False)` and no trailing newline.
4. **Convert back and check.**
   - Run `to-ids --output`.
   - Run the leftover-token grep. It should print 0.
   - Run pre-flight.
   - Run `to-titles` on the result. It should reproduce the edited title-form file.
5. **Copy over `neptune/*.json`.** No layers are added or removed, so no runtime IDs shift. The numeric diff stays small and can be reviewed directly.
6. **Your part:** convert both files to VDF with `pfwobcke.vscode-vdf`, load them fresh on the Deck, and run the in-game checks.
7. **After testing:** check off the carried-over todo "Make base gyro activation dependent on … Start all being held at the same time." Its mask part was already done (audit todo table), and this plan removes the mode shifts it was meant to replace.

## Verification

**Static checks (before handoff):**

- **Layout checks:** pre-flight is OK and the token round trip is clean.
- **Mode shifts:**
  - No `mode_shift gyro` binding remains in either file.
  - Exactly 8 mode-shift activators remain: Base trackpad touch ×4 and the Fn stick clicks ×4.
  - None of the 20 deleted group IDs appears anywhere, in bindings or in `group_source_bindings`.
- **Semantic diff (old vs new):**
  - Only the 8 modifier layers change.
  - Within them, only the Start / Select inputs and the gyro mode-shift entries change.
- **Nav keys:**
  - Every binding matches the table.
  - The regular layers match July after chord decoding.
  - Each `(Gyro)` copy matches its regular layer.

**In-game checks (both variants, fresh load):**

1. **Nav keys, Base:**
   - Mod 0 + Start / Select gives Insert / Delete.
   - Mod 1 + Start / Select gives Home / End.
   - Mod 2, entered either way, + Start / Select gives PgUp / PgDn.
   - In the alternative, use LT / RT instead of LB / RB.
2. **Nav keys, Gyro mode:** the same results, since this plan puts the reshuffle in the `(Gyro)` copies too.
3. **Gyro with Start / Select held:** in each modifier layer, in Base and in Gyro mode, holding Start or Select doesn't change what the gyro does. This is the behavior to confirm you want. If it isn't, the fix goes in a gyro mask, not back into mode shifts.
4. **Unchanged behavior:**
   - After a nav chord, releasing the modifier still doesn't fire its tap / scroll action (the tap cover still gets added).
   - Start / Select alone in a modifier layer still clears the modifier as before.

## Not included (other July changes nearby)

- Mod 2 LS click + bumper: NUM_LOCK → empty
- Mod 0 / Mod 1 LS edge → empty (the WASD modifier scaffold)
- Removing the Base trackpad-touch mode shifts and the Fn-layer stick-click mode shifts
- The Gyro layer's trigger mode shifts, and Gated Gyro
- RTP: Mouse Buttons up / down → PgUp / PgDn (a trackpad change, not the modifier layers)
- Base gyro tuning (flick-stick rotation, precision speed)

## Files

- **Modified:**
  - `neptune/single-set-default_hold-gyro_latest.json`
  - `neptune/single-set-alternative_hold-gyro_latest.json`
  - Their `.vdf` files (regenerated by you)
  - After testing: `todos.md`
- **Scratchpad only:** the edit script and working copies.
