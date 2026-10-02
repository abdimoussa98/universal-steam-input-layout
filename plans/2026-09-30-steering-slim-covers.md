# Steering: slim the Double Tap windows and the covers

Status: **executed in 90.7 (2026-09-30)** with D1 and D3 as recommended. D2: the author kept
today's sideways flush (option b, 2026-09-30). See the
[90.7 record](../findings/2026-09-30-steering-lean/README.md#slim-overlays-and-dod-fixes-907).
Originally audited against installed 90.6 (both variants identical in shape).
Covers findings F2/F3 of the [steering DoD audit](../findings/2026-09-30-steering-dod-audit/README.md);
F1 (RTP Double Tap over steering) and the other findings are separate.

## What is wrong

The steering overlays are much heavier than the repo's own covers. A cover
(an overlay, per [Layer Definition of Done §1](../resources/Layer%20Definition%20of%20Done.md#1-layer-type))
changes one control and inherits everything else, including owner recovery and
stick-touch release (§5 lets cover-type layers inherit touch). Reference shape:
`L1: Double Tap Cover` and `Menu Left: Double Tap Cover` each define **one** input.

| Layer | Inputs now | Wheel cmds | Problem |
|---|---:|---:|---|
| `LS Up: Double Tap` / `LS Down: Double Tap` | 21 each | 18 each | 14 mapped buttons rebound to *remove window ; scroll ; key* |
| `LS: Double Tap Cover` | 7 | 2 | Full branch-exit touch recovery on both sticks; lateral rebinds |
| `LS: Tap Cover` | 7 | 0 | Full branch-exit touch recovery on both sticks |
| `Menu Left/Right: Tap Cover` | 14 (16 alt) | 2 | Full clone of the protected entry; differs only on Menu button and touch |

### 1. The scroll binds (Double Tap windows)

`window_action_inputs` (`findings/2026-09-30-steering-lean/build_candidate.py:246`)
rebinds every face button, D-pad direction, back button and both stick clicks:

```
button_a  Full_Press -> -[LS Up: Double Tap] ; wheel SCROLL_UP ; key F
```

That is 14 inputs × 2 windows × 2 variants. The intent was "a mapped action
resolves the pending single early", but:

- The window already resolves the single on its own 150 ms clock (edge chord
  on the drivers), so the early flush only moves the tick forward by <150 ms.
- It hard-codes Base's key payload (`output_only`) into the window, so any
  future change to those buttons in Base/Gyro is silently shadowed here.
- Nothing underneath needs blocking: none of these 14 inputs has a layer
  command in Base, Gyro, Steering or W/S Key in either variant (checked), so
  per §8 they should simply inherit.

### 2. Covers duplicate owner recovery

`build_touch_cleanup` (`build_candidate.py:382`) gives **every** new layer,
covers included, both `touch` inputs with the full 13-layer branch exit,
a both-driver guard chord, and the trio release; plus a `right_joystick`
group that exists only for that touch input. For the covers this is pure
duplication of what they sit on:

- `LS: Double Tap Cover` is only added by the windows (after they remove
  themselves), so it sits on `W Key`/`S Key`, which already own an
  owner-guarded recovery and the trio release.
- `LS: Tap Cover` sits on Mod 0/1 or directly on `W Key`/`S Key`; both
  already define touch. Mod 0/1's release re-adds the Tap Cover, which is a
  no-op while it is active (Valve: re-adding an active layer does nothing).
- The test `test_all_new_layers_have_side_local_touch_release_cleanup`
  enforces touch on *every* new layer, which contradicts §5's cover exemption.

### 3. Menu Tap Covers are clones

`build_menu` (`build_candidate.py:324`) does `self.clone(normal, cover)`, so
each Menu Tap Cover copies the whole protected entry (triggers, gyro disable,
bumper wheels, stick edges/clicks, touch recovery). `audit_inheritance.py
--entries` shows it is only ever added by the protected entry (its 300 ms
chord and its touch releases), so everything except `button_menu` can inherit.

## Target shape

| Layer | Keep | Drop |
|---|---|---|
| `LS Up/Down: Double Tap` | LS `dpad_north`/`dpad_south` (same → Double Tap Cover; opposite → flush + switch bank), `edge` clock, LS/RS `touch` (windows aren't covers, §5) | all 14 mapped-button flushes (`window_action_inputs`), the `button_diamond`/`dpad`/`switch` groups, RS `click`; lateral per decision D2 |
| `LS: Double Tap Cover` | `dpad_north`/`dpad_south` (wheel 5 ms / 50 ms + release stop), `edge` stop | `dpad_east`/`dpad_west` (D3), `touch`, `right_joystick` group |
| `LS: Tap Cover` | `dpad_north`/`dpad_south` empty, `edge` center cleanup, `dpad_east`/`dpad_west` A/D (identical output in every stack; blocks Mod 0/1's lateral layer churn) | `touch`, `right_joystick` group |
| `Menu Left/Right: Tap Cover` | `switch` group with only `button_menu` (silent release cleanup; empty Regular Press hides the parent's 300 ms apply and 350 ms reset) | everything else (inherits from the protected entry) |

No layer count change (16/71). No new Always On. Budget can only go down.

## Decisions for the author

- **D1. Mapped button during a window.** Recommended: inherit. The key fires
  as normal and the single scroll still lands at 150 ms. (Today: scroll fires
  immediately, before the key.)
- **D2. Sideways during a window.** (a) Recommended for slimness: inherit A/D;
  the single scroll lands at 150 ms. Side effect: up → sideways → up inside
  150 ms counts as a double tap. (b) Keep today's flush + `LS: Tap Cover`.
  **Decided: (b)**, author 2026-09-30.
- **D3. Sideways during repeat scrolling.** Recommended: drop the lateral
  binds; `dpad_north`/`dpad_south` release already stops the cover. Side
  effect: a true diagonal (up+right held) keeps scrolling until up releases.

## Steps

1. **Builder** (`findings/2026-09-30-steering-lean/build_candidate.py`):
   - Delete `window_action_inputs` and its call in `build_windows`; apply D2.
   - `build_repeats`: drop the lateral loop (D3).
   - `build_menu`: build the Menu Tap Cover as a fresh layer with only the
     `switch`/`button_menu` group instead of `clone(normal, cover)`. Keep the
     same title and append position so runtime IDs don't move.
   - `build_touch_cleanup`: skip the cover set (`LS: Tap Cover`,
     `LS: Double Tap Cover`, both Menu Tap Covers). Make sure no
     `right_joystick` group is created for them, and that `prune_replaced_groups`
     drops the groups they no longer reference.
2. **Tests** (`tests/test_steering_lean.py`):
   - Exempt covers in `test_all_new_layers_have_side_local_touch_release_cleanup`
     and `test_delayed_cover_completion_precedes_touch_removals`; assert
     instead that covers define **no** touch and **no** `right_joystick`.
   - `test_mod2_is_direct_repeat_without_gesture_layers` (lines 210–215):
     replace the "button_a in the window emits one wheel" check with "the
     window defines no `button_diamond`".
   - `test_one_repeat_cover_…`: drop `dpad_east`/`dpad_west` from the
     no-wheel loop, or assert they're absent.
   - New test: each cover's defined inputs equal the "Keep" column above.
   - New test (stack-based, like `test_no_binding_adds_a_bank_…`): with a
     cover on top of each parent it can sit on, the effective `touch` is the
     parent's owner-guarded recovery plus the trio release.
3. **Regenerate and audit:** `build_candidate.py --vdf`, then
   `audit_command_budget.py` and `audit_inheritance.py` on both outputs (exit
   0; any new route goes to `traced_stacks.json` with a reason), full Python and
   Node suites.
4. **Install:** `install_neptune.py --version 90.7`; diff against 90.6 and
   confirm only the five steering overlay layers changed.
5. **Docs:** steering lean README (window resolution sentence, "Touch cleanup
   follow-up", Menu cover description), CLEANUP-AUDIT per-layer table rows for
   the five layers, `manual-testing.md` Deck section.
6. **Ship:** steam-layout-apply skill (to-ids, VDF, `versions/` snapshot).

## Deck checks

| Check | Exercise | Pass |
|---|---|---|
| S1 window keys | Flick up to center, press A within 150 ms | F fires once, one scroll ~150 ms after center, no stuck window |
| S2 repeat | Flick, flick-and-hold | Repeat scroll; release stops; next push gives no scroll until center |
| S3 cover touch | Hold up past 250 ms, lift LS thumb, return | LST trio cleared, Tap Cover stays until center, no phantom scroll |
| S4 stale recovery | Hold up past 250 ms, release driver while Steam menu is open, come back | Owner recovery on touch clears the branch through the cover |
| S5 menu cover | Hold Start past 300 ms in steering, release; lift a thumb during the hold | Silent release, protected entry and cover both gone, gyro stays disabled throughout |
| S6 lateral (D2/D3) | Up-center-right-up inside 150 ms; diagonal during repeat | Matches the chosen decision |
