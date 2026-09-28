# Audit: exploratory layout vs. committed Neptune layout

- **Date:** 2026-09-27
- **Committed baseline:** [`neptune/single-set-default_hold-gyro_latest.json`](../../neptune/single-set-default_hold-gyro_latest.json): `single-set-default :: always-gyro :: 85.8`, revision 12896, `controller_neptune` (Steam Deck), last changed 2026-02-04
- **Exploratory layout:** [`MOST_RECENT_LAYOUT.post-fix.json`](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json): `single-set-default :: always-gyro :: example`, revision 14001, `controller_triton`, description *"fix ramp up being disabled due to stuck rtp entry layer"*
- `MOST_RECENT_LAYOUT.pre-fix.json` has the same content. Only the four layers from the July finding are reordered, so everything below applies to it too.
- None of these changes are in the alternative variant (`neptune/single-set-alternative_*`).

Line links below (`post-fix.json:N`) point into the exploratory file.

## Method

- **Normalizing:** I converted both files to a title-based form. Neptune's numeric runtime IDs were resolved in list order; the exploratory file already uses `{{Base::…}}` tokens. Chords were decoded to button names (see the [appendix](#appendix-chord-and-mask-decoding)).
- **Matching layers:** Layers were matched by title. Renamed layers were matched by content and by their slot in the GUI list.
- **Scope:** Only groups that are actually live were compared: `active` groups plus mode-shift targets. Dormant `inactive` groups are unused alternate modes Steam keeps around, so they were skipped.

## Summary

| | Layers |
|---|---|
| **Removed** | L2, R2, (Gyro) L2, (Gyro) R2 |
| **Renamed** | (Gyro) L1: Modifier 0 → `*L1: Modifier 0`, and the same for `*R1: Modifier 1`, `*L1!R1: Modifier 2`, `*R1!L1: Modifier 2` |
| **Emptied and renamed** | (Gyro) Turning Ramp Up 0 / 1 → `DEPRECATED` ×2 |
| **Replaced** | Gyro Off → Gyro Off Ramp Up (same slot in the list; still disables gyro, plus new ramp-up logic) |
| **New** | Split Stick, Split Stick Fallback, Split Stick: W Key, Split Stick: S Key, Gated Gyro, RTP: Middle Mouse Click |
| **Changed** | Base, L1 / R1 / both Mod 2 layers, all four `*` layers, Gyro, Turning Ramp Up 0 / 1, LTP: Arrow Keys, RTP: Mouse Buttons, RTP: Circular Scroll, RTP: Entry Point, Tab / Backspace / Escape / Enter, RST / LST: Double Tap, L1&R1: Tap Cover, both Fn layers, Transition Set 1 |
| **Unchanged (24)** | All tap covers except L1&R1, RST / LST / Menu Buttons entry points, temporary gyros, double taps and double-tap covers (L1, R1, RTP, Menu Left / Right), scroll layers, Menu Left: Escape, Menu Right: Tab, Transition Set 0 |

The main changes:

1. **Trigger layers are gone.** Each trigger is now a single analog-pull bind (left or right mouse button).
2. **Ramp-up gyro logic moved into Base.** A right-stick edge adds Gyro Off Ramp Up. If a trigger is held, it goes straight to Turning Ramp Up 0 with gyro still on.
3. **New steering stateful set (Split Stick).** Bumpers hold W / S. You enter it with Menu Right + LS click.
4. **All Start / Select gyro mode shifts are removed.** The base gyro activation mask now covers that case.
5. **WASD modifier scaffold** added on the base left stick.
6. **Trackpad layers are now tap-to-open, one-shot layers.**
7. **Stuck RTP: Entry Point fix.** This is the fix named in the layout's description.
8. **Other:** the Insert / Delete / Home / End / PgUp / PgDn keys were reshuffled across the modifier layers, and a new Gated Gyro toggle was added.

## Todo status

Checked against the current [`todos.md`](../../todos.md).

| Todo | Status | Evidence in the exploratory layout |
|---|---|---|
| Move gamepad layer → Menu Right + RS click / Menu Left + LS click | Not started | There is no gamepad layer. Both combos already reach a layer: Menu Right + RS click → Transition Set 0, and Menu Left + LS click → Transition Set 1. The matching release binds on those layers are still empty, so that is where the gamepad hook would go. |
| Add steering stateful set | **Done** | Split Stick, plus Fallback, W Key, and S Key. See [§2](#2-steering-split-stick-new). |
| Add steering layer → Right Menu + LS click | **Done** | Menu Right: Fn Layer + LS click → Transition Set 1. Releasing Menu Right then adds Split Stick ([post-fix.json:16450](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L16450)). |
| W / S on bumpers or LS up / down (bumpers primary, LS as fallback without exiting) | **Done** | RB → W Key and LB → S Key, both using always-on key holds. Holding LS up / down → Split Stick Fallback (W / S back on the stick). Pressing a bumper with the stick centered returns to bumper steering. |
| Duplicate bumper mod 0 / 1 layers (and your Mod0 / Mod1 notes) | Partial | Steering reuses the `*` copies of the modifier layers (formerly the "(Gyro)" copies). W / S live in standalone W Key / S Key layers, and the opposite bumper jumps straight to `*` Mod 2. There are no Mod 0 / Mod 1 copies that carry W / S, and no Mod 0 → 1 → 2 stepping. |
| Scroll wheel on joystick; hold up / down to exit | Partial, needs verifying | A held bumper in Split Stick mode-shifts LS to a scroll-wheel group. A second mode shift fires on the same press, though (see [Issue 3](#issues-to-check)). Holding LS up / down enters Fallback. Leaving Split Stick entirely is done by releasing from `*` L1 + R1. |
| Add menu stateful set | Not started | Nothing in the file. |
| Stateful menu gyro / temporary menu gyro | Not started | The closest piece is the new Gated Gyro toggle (L1 + R1 + RS click). Its entry and exit are different from what the todo describes. |
| Remove trigger layers and chorded ramp ups | **Done** | L2, R2, (Gyro) L2, and (Gyro) R2 are deleted. The (Gyro) Turning Ramp Up layers are emptied (now `DEPRECATED`). The full-pull binds are removed from Base and Gyro. |
| Move ramp-up gyro on / off logic to base layer | **Done** | Base RS edge → Gyro Off Ramp Up, or → Turning Ramp Up 0 if a trigger is held ([post-fix.json:696](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L696)). |
| In ramp-up layers, trigger removes the gyro-off layer | **Done** | In Gyro Off Ramp Up, LT / RT → removes the layer itself. |
| Convert triggers to proper hip-fire triggers | Partial | The full-pull layer binds are gone and each trigger is one analog-pull bind (LMB / RMB). No hip-fire soft-press style is set on the triggers. |
| Left stick cleanups to match right stick | Not started | In the modifier layers, RS edge has a cleanup that only fires when the bumper isn't held. LS edge only has the new empty bind. |
| WASD modifier scaffold | Partial | Base LS inner-zone soft press → `KEYPAD_ASTERISK`, labeled "Inner WASD Modifier" ([post-fix.json:584](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L584)). It uses a placeholder key rather than an empty bind. It is blocked in Mod 0 / Mod 1 and all `*` layers, but not in the regular Mod 2 layers. |
| Haptics on FN layers (LS / RS) | Not started | The Fn layers only lost their stick-click mode shifts. |
| L1 + R1 clears all stateful sets (except gamepad) | Partial | Releasing from `*` Mod 2 removes Gyro, Split Stick, and Split Stick Fallback. Gated Gyro is never cleared. From Base, L1 + R1 release *adds* Gyro, so it works as a toggle rather than a global clear. |
| Fix tap cover / menu entry bug (start delay interrupt) | Not started | Menu Buttons: Entry Point and the tap-cover layers are unchanged. |
| Fix tap covers not re-adding after interrupt | Unclear | Only nearby changes: the base and Gyro LB / RB modifier chords now repeat every 50 ms while held, and `*` Mod 2 clears L1&R1: Tap Cover on an opposite-bumper press. |
| Split menu entry layer into Menu Left / Menu Right layers | Not started | Still a single Menu Buttons: Entry Point, unchanged. |
| *(carried over)* Base gyro activation = all of LS / RS deflect + touch + Select + Start | **Done, can check off** | The mask was already in Neptune ([post-fix.json:2609](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L2609)). The exploratory layout removes all 9 Start / Select gyro mode-shift targets the mask was meant to replace. |
| *(carried over)* Handle cursor gyro layer | Not started | Nothing in the file. |
| *(carried over)* Clear unnecessary layers on action set swap | Not applicable | Single action set. |
| *(carried over)* Temp gyro on both stick touches | **Done (already in Neptune)** | RST / LST: Double Tap → touch → Temporary Gyro + Entry Point. Unchanged. |

Fixes in the exploratory layout that aren't on the todo list:

- The stuck RTP: Entry Point fix ([§6](#6-trackpads))
- The trackpad one-shot rework
- The nav-key reshuffle and NUM_LOCK removal
- Gated Gyro
- Ramp-up and gyro tuning
- Double-tap W / S

## What changed, by area

### 1. Triggers and ramp-up

**Neptune (before):**

- Base RS edge (soft press at 32255) added both Turning Ramp Up 0 and Gyro Off.
- A full trigger pull cleared ramp-up and Gyro Off, then added the L2 / R2 layer. Inside L2 / R2, an RS edge chorded with that trigger → Turning Ramp Up 0 with gyro kept on.
- The Gyro set had its own copies of all of this: (Gyro) L2 / R2 and (Gyro) Turning Ramp Up 0 / 1.

**Exploratory (after):**

- **Base RS edge** has three activators:
  - Full press → add **Gyro Off Ramp Up**
  - Chord with *any* trigger (full or soft pull) → add **Turning Ramp Up 0** (gyro stays on)
  - Chord with either bumper → empty
- **Gyro Off Ramp Up** ([post-fix.json:13476](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L13476)):
  - Gyro is disabled.
  - Pushing further (29031, 5 ms delay) → Turning Ramp Up 0.
  - Letting the stick back in (inverted at 25807) → removes the layer itself.
  - LT / RT → removes the layer itself, so gyro comes back mid-turn.
- **Triggers:** the full-pull binds are removed from Base and Gyro, and the `adaptive_threshold` setting is dropped. Each trigger is now only an analog pull → LMB / RMB.
- **Turning Ramp Up tuning:**

  | Layer | Sensitivity | Vertical scale |
  |---|---|---|
  | Turning Ramp Up 0 | 130 → 150 | 77 → 80 |
  | Turning Ramp Up 1 | 160 → 200 | 63 → 67 |

- **Turning Ramp Up 0** has a new RS edge full press that repeats every 300 ms and removes Turning Ramp Up 1.
- **Bumpers inside the ramp-up layers** now only clear ramp-up state (ending in an empty bind). They no longer add L1 / R1 Modifier directly. At the same time, the base and Gyro LB / RB chords gained `repeat_rate: 50` on top of the existing `hold_repeats` ([post-fix.json:14037](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L14037)). The likely intent is that the modifier gets re-added once the ramp-up layer is gone.
- **Cleanup lists** in every ramp-up bind now target `DEPRECATED` ×2 and Gyro Off Ramp Up instead of the (Gyro) ramp-ups and Gyro Off.

### 2. Steering: Split Stick (new)

**Entry:** Hold Menu Right (Fn layer) and click LS → Transition Set 1. Releasing Menu Right then adds Split Stick.

| In Split Stick | Result |
|---|---|
| Hold RB | Split Stick: W Key, which holds W through an always-on action ([post-fix.json:17637](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L17637)) |
| Hold LB | Split Stick: S Key, which holds S |
| W Key + LB | `*R1!L1: Modifier 2` |
| S Key + RB | `*L1!R1: Modifier 2` |
| W Key + LTP click | Swaps to S Key (reverse) until your finger leaves the pad |
| Either bumper | LS is mode-shifted, with up / down → mouse wheel (see [Issue 3](#issues-to-check)). RS is mode-shifted to block ramp-up. |
| Hold LS up / down (~100 ms, chorded with LS deflect) | **Split Stick Fallback**: LS up / down = W / S again ([post-fix.json:13314](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L13314)) |
| In Fallback: bumper with the stick centered | Removes Fallback and returns to bumper steering |
| In Fallback: bumper + LS deflected | `*L1: Modifier 0` / `*R1: Modifier 1`. This chord requires *all* of the listed buttons ([post-fix.json:17560](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L17560)) |
| **Exit** | Release a bumper from either `*` Mod 2 → removes Split Stick, Fallback, and Gyro |

The W Key and S Key layers also blank LS up / down and RS edge, so there is no ramp-up while driving. W Key keeps the base LTP swipe binds.

### 3. Gyro

- **Base gyro activation:** unchanged. It still requires *all* of Menu Left, Menu Right, LS / RS touch, and LS / RS deflect.
- **Base gyro tuning:**
  - Flick-stick rotation: 4653 → 3853
  - `gyro_precision_speed`: 0 → 300
  - New `gyro_to_2d_conversion_style: 4`
  - New `gyro_speed_deadzone: 0`
- **Start / Select gyro mode shifts are removed.** All 9 mode-shift targets are gone (groups 1302, 1304, 1307, 1308, 1310, 12927, 12946, 12957, 12970) from L1, R1, both Mod 2 layers, and all four `*` copies.
- **Gyro stateful set (the "Gyro" layer):**
  - Removed: its trigger → (Gyro) L2 / R2 binds and its own RS-edge ramp-up. It now uses the base ramp-up flow.
  - Added: mode shifts on the gyro source for the triggers (full pull and threshold) ([post-fix.json:17387](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L17387)). See [Issues 3 and 4](#issues-to-check).
  - Unchanged: its gyro is gated by *any* LS / RS touch or deflect.
- **Gated Gyro (new layer):**
  - `gyro_to_mouse`
  - Activation: *any* of Menu Left, Menu Right, LS / RS touch, LS / RS deflect (the same buttons as Base, but "any" instead of "all")
  - Precision speed 750, haptics 3 plus a flick-stick haptic bump, mouse-move threshold 10
  - **Toggle:** hold L1 + R1 (L1&R1: Tap Cover) and click RS ([post-fix.json:12560](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L12560)). The toggle beeps and shows a notification. Nothing else removes this layer.

### 4. Modifier layers (L1 / R1 / Mod 2)

**Navigation keys reshuffled** (regular layers only; see [Issue 2](#issues-to-check)):

| Layer | Menu Right + bumper | Menu Left + bumper |
|---|---|---|
| L1: Modifier 0 | PAGE_UP → **INSERT** | PAGE_DOWN → **DELETE** |
| R1: Modifier 1 | INSERT → **HOME** | DELETE → **END** |
| L1!R1 / R1!L1: Modifier 2 | HOME → **PAGE_UP** | END → **PAGE_DOWN** |

Other changes:

- **Mod 2:** LS click chorded with a bumper changed from NUM_LOCK to an empty bind. This applies to the regular and `*` layers.
- **Mod 0 / Mod 1** (regular and `*`): new LS edge → empty bind, which stops the base Inner WASD Modifier from firing while a bumper is held.
- **Start / Select gyro mode shifts:** removed (see §3).
- **`*` copies:** renamed from "(Gyro) …". The Gyro set still uses them, and Split Stick now does too. Compared with the regular layers they differ in three ways:
  - They add their own gated gyro group.
  - They chain to the other `*` layers.
  - Their Mod 2 bumper release *removes* Gyro, Split Stick, and Split Stick Fallback, where the regular Mod 2 release *adds* Gyro.
- **New in `*` Mod 2 only:** an opposite-bumper full press that repeats every 250 ms and removes L1&R1: Tap Cover ([post-fix.json:17159](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L17159)).

### 5. Left stick

- **Base LS "edge":**
  - The empty full press became a soft press: threshold 26610, inverted edge, `soft_press_sytle: 2`.
  - It now presses `KEYPAD_ASTERISK`, labeled "Inner WASD Modifier".
- **New group settings:** `edge_binding_radius: 21700` and `analog_emulation_duty_cycle_pct: 50`.
- **W / A / S / D directions** are now non-interruptable.

### 6. Trackpads

- **Base:** LTP click and RTP click changed from `hold_layer` to `add_layer`, so a tap opens the layer instead of holding it. The LTP 2D-scroll `sensitivity: 50` setting was dropped (back to default).
- **LTP: Arrow Keys:**
  - Each arrow's release removes the layer (one-shot).
  - The center changed from the on-screen keyboard to **CAPSLOCK**.
  - Lifting your finger removes the layer, and also removes Split Stick: S Key.
  - Haptics moved from the arrows (3 → 0) to the click (0 → 3).
- **RTP: Mouse Buttons:**
  - Up / down changed from scroll wheel (with long-press repeat) to **PAGE_UP / PAGE_DOWN**.
  - Forward / back are unchanged.
  - The center gives a middle click with no chord needed.
  - Each release removes the layer. Lifting your finger removes it along with RTP: Circular Scroll.
- **RTP: Entry Point:** an RS edge *without* RTP touch now removes RTP: Entry Point and RTP: Tap Cover ([post-fix.json:7723](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L7723)). With RTP touch, it's still empty. This is the "stuck RTP entry layer" fix from the layout description. The stuck layer's empty RS-edge bind had been blocking the base ramp-up.
- **Tab / Backspace / Escape / Enter** (LTP swipe layers): LTP click → empty bind. This stops the now-sticky Arrow Keys layer from opening mid-swipe.
- **RTP: Circular Scroll:** a haptic tick (1) on each scroll step.
- **RTP: Middle Mouse Click (new):** a delayed middle click on RTP click. Nothing adds this layer (see [Issue 5](#issues-to-check)).

### 7. Menu / Fn layers

- **Menu Left / Right Fn layers:** the stick-click mode shifts (LS / RS turning into a punctuation D-pad) are removed. Punctuation is still available on the stick directions while Menu is held, and stick click with Menu held still goes to Transition Set 0 / 1.
- **Transition Set 1:** Menu Right release changed from an empty bind to add Split Stick + remove itself. Transition Set 0 is still inert.

### 8. Small layer tweaks

- **RST / LST: Double Tap:** LS up / down → W / S added. The purpose isn't clear from the file alone. Only up / down were added, which suggests it's related to Split Stick.

### 9. Housekeeping and device

- **Device/export:** `controller_neptune` → `controller_triton` (the new Steam Controller). This snapshot stores chords as bitmasks instead of legacy `chord_button` IDs (see the [appendix](#appendix-chord-and-mask-decoding)). Modern Deck clients also support the mask selector; porting to Neptune does not require expanding a mask into separate commands. See the [command-budget correction](../2026-09-27-neptune-command-budget/AUDIT.md).
- **Groups: 604 → 421.**
  - 50 unreferenced groups were dropped, including the two `system_key_1` binds.
  - Dormant `inactive` groups went from 189 to 37.
  - All 15 of Neptune's mode-shift targets are gone. The 5 in the exploratory file are all new.
- **Base trackpad-touch mode shifts removed:** their D-pad / face-button groups were identical to the base binds anyway.
- **Metadata:**
  - Title: `… :: 85.8` → `… :: example`
  - Workshop URL cleared
  - Revision: 12896 → 14001

## Issues to check

1. **Probable typo: RTP: Mouse Buttons center release removes LTP: Arrow Keys.** ([post-fix.json:1704](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L1704)) Every other release in this layer removes RTP: Mouse Buttons. As written, the layer stays up after a middle click until you lift your finger, and it silently closes Arrow Keys if that layer is open.
2. **The `*` modifier layers have drifted from the regular ones.** Gyro mode and Split Stick both use the `*` copies, so the same buttons behave differently depending on which stateful set you're in:
   - The nav-key reshuffle wasn't copied over. `*L1` still has PgUp / PgDn ([post-fix.json:16784](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L16784)) against L1's Insert / Delete ([post-fix.json:14122](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L14122)). `*R1` still has Insert / Delete, and `*` Mod 2 still has Home / End.
   - The LS-edge empty bind is in `*` Mod 2 but not in regular L1!R1 / R1!L1 ([post-fix.json:4418](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L4418)). The Inner WASD Modifier therefore fires through regular Mod 2.
   - The opposite-bumper "remove L1&R1: Tap Cover" bind (repeats every 250 ms) exists only in `*` Mod 2.
3. **Two mode shifts on the same source from one press.** Whichever Steam applies last probably wins, which would make one of each pair dead:
   - **Gyro layer, triggers:** gyro → group 373 (D-pad mode, meaning no gyro output) *and* → group 374. Group 374 has the same gated `gyro_to_mouse` settings as the layer itself. If 374 wins, the trigger shift does nothing.
   - **Split Stick, bumpers:** LS → group 408 (up / down = mouse wheel) *and* → group 409 (up / down blank, A / D, Q, cleanups) ([post-fix.json:17494](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L17494)). If 409 wins, there's no scroll wheel, which is the behavior your "scroll wheel on joystick" note asks for.
   - Neptune's Mod 2 layers used the same pattern (groups 1307 D-pad + 1308 gyro), so it may be leftover from GUI editing. Worth confirming in the GUI which group actually applies.
4. **`Right_Trigger` casing.** In the Gyro layer's switch group, the right-trigger mode-shift input is `Right_Trigger` ([post-fix.json:17399](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L17399)), while the others are lowercase (`left_trigger`, `*_trigger_threshold`). Steam wrote it this way, but confirm the right trigger's full-pull shift fires.
5. **RTP: Middle Mouse Click is unreachable.** ([post-fix.json:366](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L366)) It has 2 `remove_layer` references and 0 `add_layer`. Either wire it in or delete it.
6. **`DEPRECATED` ×2.**
   - Both share one title, so `to-ids` collapses them to a single ID.
   - In active groups they are only ever removed (12 times; 4 more removes sit in dormant groups). The 5 `add_layer {{Base::DEPRECATED}}` references are all in dormant `inactive` groups (Gyro, DEPRECATED, and Split Stick Fallback right-joystick alternates). The July finding described these as live `add_layer` binds, but they're unreachable. Deleting both layers is safe once the runtime IDs are remapped.
7. **Menu Left + LS click does nothing yet.** Both Fn layers add Transition Set 1 on LS click, but only Menu Right's release does anything there. The Menu Left path just clears on the next stick touch. That empty release is the natural hook for the planned gamepad combo.

## Appendix: chord and mask decoding

The compared Neptune export stores chords as legacy `chord_button: N`; the Triton
snapshot uses `gyro_ratchet_button_mask` bitmasks, the same format gyro activation
buttons use. This describes those exports, not a device limitation. Modern Deck
clients also support multi-button selectors. The [command-budget follow-up](../2026-09-27-neptune-command-budget/AUDIT.md)
corrects the earlier recommendation to expand masks into separate Neptune
commands. Pairs marked "paired" come from the same bind appearing in both files.
Pairs marked "inferred" come from context.

| Button | Neptune `chord_button` | Triton mask bit (value) | Source |
|---|---|---|---|
| LB | 1 | 3 (8) | paired |
| RB | 2 | 2 (4) | paired |
| RT / LT full pull | 6 / 5 | 0 / 1 (1 / 2) | inferred (always used together) |
| LT / RT soft pull | 7 / 8 | 25 / 24 | mask bits verified in Steam UI; corrected from the earlier inference |
| LS click | 9 | 22 (4194304) | paired |
| **Menu Right** (`button_escape`) | 14 | 14 (16384) | paired |
| **Menu Left** (`button_menu`) | 15 | 12 (4096) | paired |
| LTP touch | 16 | 19 (524288) | paired |
| RTP touch | 17 | 20 (1048576) | paired |
| RS click | 20 | 26 (67108864) | paired |
| LS touch | 23 | 46 | paired |
| RS touch | 24 | 47 | paired |
| LS deflect | – | 30 | inferred (used by the left-stick Split Stick chords) |
| RS deflect | – | 31 | inferred |

- **`gyro_ratchet_button_requireany_or_all`:** `"1"` means *all*, and `"0"` means *any* (the default). Initially inferred from Split Stick Fallback; the Any/All values are now verified directly in the installed Steam chord UI schema. See the [selector verification](../2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md), which also confirms the exact trigger and bumper mask bits.
- **Masks in use:**
  - `211109453778944` = Menu Left + Menu Right + LS / RS touch + LS / RS deflect (Base with "all"; Gated Gyro with "any")
  - `211109453758464` = the four stick bits only (the Gyro layer and the `*` layers' gyro)
- **Side note:** [`resources/Neptune Chorded Button Ids.md`](../../resources/Neptune%20Chorded%20Button%20Ids.md) labels 14 as "View" and 15 as "Menu". The layout's own binds show 14 = `button_escape` = your Menu Right, and 15 = `button_menu` = Menu Left. For example, in Menu Buttons: Entry Point, holding `button_escape` for 300 ms (a chord on 14) opens Menu Right: Fn Layer.
