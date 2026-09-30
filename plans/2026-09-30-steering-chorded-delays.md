# Steering: replace Long Press with chorded delays

Status: **implemented in 90.6 (2026-09-30); Deck gates C1–C5 untested.** See the
[steering README](../findings/2026-09-30-steering-lean/README.md#chorded-delays-906).
As planned, the Mod 0/1 consume got the 250/300 reset. The Tap Cover was then
simplified so it never adds a bank and is always added fresh on top; see
[Simplified Tap Cover](../findings/2026-09-30-steering-lean/README.md#simplified-tap-cover-906).

## Why

Steering's hold timers should follow the pattern the modifier layers already
use: a **chord with `delay_start`**, plus a scoped repeating removal when the
delayed action applies a layer. Long Press and Double Press are banned
repo-wide because they misbehave with Steam's layer API; see
[allowed activation types](../resources/Steam%20Input%20JSON%20Structure.md#allowed-activation-types).
The older `RTP: Mouse Buttons` Long Press and the inactive touch Double Presses
are tracked separately in the todo list.

Stick directions can't be chord buttons, but **stick deflection can**: bit 30
(`1073741824`) is LS deflection, as the modifier RS-edge recovery chord already
uses ([structure doc](../resources/Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape)).

Reference pattern, from each `Steering | …!…: Modifier 2` opposite input:

| Activator | Settings | Action |
|---|---|---|
| chord (owner button) | `delay_start 200`, haptic 3 | add the opposite Tap Cover |
| Full_Press | `hold_repeats 1`, `repeat_rate 250` | remove that cover (interrupted-delay reset) |

## Current Long Press uses (6 per variant)

| Layer | Input | Long Press | Purpose | Builder |
|---|---|---|---|---|
| `Steering` | LS up (`dpad_north`) | 1000 ms, repeat 250, haptic 3 | Fallback warning | `build_core`, line 139 |
| `Steering` | LS up (`dpad_north`) | 2500 ms, haptic 3 | Fallback exit (`exit_all(beep=True)`) | `build_core`, line 142 |
| `Steering \| LS Down: Modifier 0` | `dpad_south` | 250 ms | Hold uses up the tap: add `Steering \| LS: Tap Cover` | `build_strokes`, line 169 |
| `Steering \| LS Up: Modifier 1` | `dpad_north` | 250 ms | Same | `build_strokes`, line 169 |
| `Steering \| LS Up: Double Tap` | `edge` (radius 32767, inverted) | 150 ms | Window expiry: one wheel up, remove window | `build_windows`, line 239 |
| `Steering \| LS Down: Double Tap` | `edge` (radius 32767, inverted) | 150 ms | Same, wheel down | `build_windows`, line 239 |

Builder line numbers refer to `findings/2026-09-30-steering-lean/build_candidate.py`.

## Replacements

### 1. Fallback warning and exit (`Steering`, LS up)

| Activator | Settings | Action |
|---|---|---|
| Full_Press | `interruptable 0` | `key_press W` (unchanged) |
| chord, mask LS deflection (`1073741824`, Any) | `delay_start 1000`, `hold_repeats 1`, `repeat_rate 250`, haptic 3, `interruptable 0` | empty binding (warning pulses) |
| chord, mask LS deflection | `delay_start 2500`, haptic 3, `interruptable 0` | `exit_all(beep=True)` |

- Budget stays at 3 entries.
- Neither chord adds a layer, so no interrupted-delay reset is needed.
- `Steering | LS: Entry Point` stays. Fire Start Delay still fires over an
  input held when its layer is added ([held-input rule](2026-09-29-held-input-rule-followups.md)),
  so a W carried in through entry would otherwise run out the exit. The Entry
  Point overrides `dpad_north` with plain W until center or a driving press.

### 2. Modifier 0/1 hold consume (250 ms)

On `dpad_south` in `Steering | LS Down: Modifier 0` and `dpad_north` in
`Steering | LS Up: Modifier 1`:

| Activator | Settings | Action |
|---|---|---|
| chord, mask LS deflection | `delay_start 250`, `interruptable 0` | add `Steering \| LS: Tap Cover` |
| Full_Press | `hold_repeats 1`, `repeat_rate 300`, `interruptable 0` | remove `Steering \| LS: Tap Cover` (interrupted-delay reset) |

- The budget goes from 1 to 2 entries.
- Reset rate: pick the first repeat past the 250 ms delay, as Mod 2 uses
  200/250. Confirm 300 against the repo's reset convention before building.
- Once applied, the Tap Cover overrides this direction, which stops the
  reset. Check that the reset can never remove a Tap Cover that another path
  (reversal, driver acquisition, Mod 2 exit) placed **below** the bank. The
  restore path reasserts the cover last, so it should always sit on top.
  Verify this in title form before building.
- Precedent: the original 36-layer builder already used
  `delay_start=HOLD_MS` for this consume
  (`findings/2026-09-29-steering-implementation/build_candidate.py:337`).

### 3. Double-tap window expiry (150 ms)

This timer runs with the stick **centered** (the widened inverted edge counts
as held), so an LS-deflection chord would fire at the wrong time. The
windows exist only while a driver is held, because owner release clears the
whole steering family. So chord on the drivers instead:

| Activator | Settings | Action |
|---|---|---|
| chord, mask either driver, Any (Default `12` = L1\|R1; Alternative `50331651` = L2\|R2 bits) | `delay_start 150`, `interruptable 0` | `flush_window(...)`: wheel tick, remove window (unchanged) |

- No layer is added, so no reset is needed.
- The masks match `self.mask` in the 36-layer builder. Re-derive them from
  `opposite_mask` rather than trusting this table.
- **Main risk:** the edge is already held when the window layer is added.
  If Steam measures `delay_start` from the physical press instead of from
  the layer add, the window expires instantly. Deck gate C3 below must pass
  before this ships. Long Press is not an allowed fallback. If C3 fails,
  move the clock to an input that is pressed fresh, or make the expiry a
  layer-based timed exit like the existing Double Tap windows.

## Implementation steps

1. **Builder:** in `findings/2026-09-30-steering-lean/build_candidate.py`,
   add `LS_DEFLECT = 1 << 30` and a per-variant driver Any-mask, then replace
   the three sites above.
2. **Builder guard:** in `finish()`, raise if any `Steering` / `Steering | …`
   group contains a `Long_Press` or `Double_Press` activator, alongside the
   existing no-new-Always-On check. Also stop the builder from leaving
   unreferenced orphan groups (six per variant in 90.5 still hold Long Press
   copies).
3. **Tests** (`tests/test_steering_lean.py`):
   - Replace the `long_press_time` assertions at lines 130–131, 149–150
     and 275–281 with chord mask, `delay_start`, repeat and haptic
     assertions.
   - Add the reset assertions for Mod 0/1.
   - Add a test that no steering layer has `Long_Press`.
4. **Regenerate** both variants (`build_candidate.py --vdf`). Run
   `audit_command_budget.py` (exit 0), the full Python and Node suites, and
   the pre-flight checks.
5. **Install:** copy the regenerated candidates over
   `neptune/*_hold-gyro_latest.json`, re-apply the release title and
   description, and confirm that only the six inputs (plus the two Mod 0/1
   resets) differ from 90.5.
6. **Release:** bump to **90.6**, or refresh 90.5 if it was never loaded
   into Steam. Keep the description's timings unchanged, since behavior is
   meant to be identical. Export the VDFs, save the snapshot, and update
   `neptune-installation.json`.
7. **Docs:** update the lean
   [README](../findings/2026-09-30-steering-lean/README.md) timing section,
   which says "ordinary Long Press on a widened inverted stick edge", the
   [ACCEPTANCE](../findings/2026-09-30-steering-lean/ACCEPTANCE.md) gates
   below, and the memory note on Long Press timing.

## Deck gates (all untested)

| Gate | Exercise | Required result |
|---|---|---|
| C1 fallback | In fallback, hold LS up; release at 0.8 s, 2.0 s and 3 s; drift the stick so deflection drops while W stays | Warning pulses from 1 s, exit at 2.5 s with a single beep; early release cancels both; if the deflection bit drops before the dpad threshold, the timer cancels instead of firing late |
| C2 entry carry | Enter Steering with W held for more than 3 s | No warning or exit until center and a fresh push (Entry Point still protects) |
| C3 window clock | Short flick to center, wait; flick, pause, flick again | One scroll at about 150 ms after center, measured from the window's add, not the original press; second flick still reaches repeat |
| C4 consume | Hold down or up past 250 ms; release at about 240 ms; tap repeatedly | Consume only past 250 ms; interrupted holds leave no Tap Cover; no map flicker from the reset |
| C5 reset vs cover | Reverse, acquire a driver, or leave Mod 2 with the stick held | The reset never strips an active Tap Cover; no resurrected tap or scroll |

A failed gate blocks promotion. Keep 90.5 as the fallback build.
