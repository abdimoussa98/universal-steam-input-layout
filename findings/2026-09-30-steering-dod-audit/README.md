# Steering layers vs. the Layer Definition of Done

Audited 2026-09-30 against the working-tree
[Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md)
(**DoD**), all 16 steering layers, both variants, installed **90.6**
(`neptune/*_hold-gyro_latest.json`). Read-only: no layout was changed.

**Update: fixed in 90.7** (see [Resolution](#resolution-907)). The audit below
describes 90.6.

**Verdict (90.6): not done.** §2, §3 and the §6 reset rules pass. There is one §9 failure
(an Always On window over steering), and the covers break the §1/§7 overlay
scope. §8 has gaps that the existing audit can't see.

| § | Section | Result | Findings |
|---|---|---|---|
| 1 | Layer type | ❌ | [F2](#f2-overlays-carry-owner-recovery), [F4](#f4-mod-2-quick-exit-removes-gyro), [F5](#f5-the-windows-have-no-dod-type) |
| 2 | Placement | ✅ | |
| 3 | Activators | ✅ | |
| 4 | Entry | ✅ | |
| 5 | Stick-touch release | ✅ | Covers over-comply ([F2](#f2-overlays-carry-owner-recovery)) |
| 6 | Hold, tap, double tap | ⚠️ | [F6](#f6-recipe-deviations-are-not-recorded) |
| 7 | Cleanup | ❌ | [F2](#f2-overlays-carry-owner-recovery), [F3](#f3-windows-hard-code-14-base-outputs) |
| 8 | Inheritance and blocking | ⚠️ | [F7](#f7-pending-timers-leave-rs-edge-open), [F8](#f8-the-inheritance-audit-cannot-reach-steering) |
| 9 | Always On | ❌ | [F1](#f1-rtp-double-tap-inherits-steering-layer-commands) |
| 10 | Ship it | ⚠️ | [§10](#10-ship-it) |

## Layer types (§1)

The default titles are shown below; the alternative uses L2/R2.

| Layer | DoD type | Added on top of |
|---|---|---|
| `Steering` | Stateful | Base or Gyro |
| `Steering \| LS: Entry Point` | Overlay (disposable entry guard) | Steering |
| `Steering \| R1: W Key`, `L1: S Key` | Owner | Steering |
| `Steering \| LS Down: Modifier 0`, `LS Up: Modifier 1` | Owner (map; applies `LS: Tap Cover`) | W/S Key |
| `Steering \| R1!L1: Modifier 2`, `L1!R1: Modifier 2` | Owner (applies `L1:`/`R1: Tap Cover`) | W/S Key + `LS: Tap Cover` |
| `Steering \| LS: Tap Cover` | Overlay | Mod 0/1, or W/S Key directly |
| `Steering \| LS Up: Double Tap`, `LS Down: Double Tap` | **None fits** ([F5](#f5-the-windows-have-no-dod-type)) | W/S Key |
| `Steering \| LS: Double Tap Cover` | Overlay | W/S Key |
| `Steering \| Menu Left/Right: Entry Point` | Owner | Base/Gyro + `Menu … : Entry Point` |
| `Steering \| Menu Left/Right: Tap Cover` | Overlay | Its protected entry |

The protected menu layers are pre-entry helpers. Inside steering, Start/Select
removes `Steering` and adds the ordinary menu entry, so the protected menu layers never sit on a
steering stack.

## What passes

- **§2 Placement:** in both variants, all 16 layers come after the frozen pre-steering maximum
  (`Preset_1000155`). The list order matches the `Preset_` order, titles are
  unique, and the layers are mirrored in the alternative. There's no `hold_layer` or
  `CHANGE_PRESET` in any steering layer.
- **§3 Activators:** only Regular, Chord and Release are used. `audit_command_budget.py`
  passes in both variants, and none of its four allowed 4th entries is a steering layer.
- **§4 Entry:** every add that must land over a held input uses a delay
  (5/150/200/250/300 ms). Every layer command that must run on a held input repeats:
  acquisition 50 ms, and Entry Point, Tap Cover and Double Tap Cover edges at 50 ms.
  Every entry adds the new layer last.
- **§5 Stick-touch release:** all 16 layers define both touch releases with the exact
  side trio. Mod 0/1, Mod 2 and the protected entries add their pending cover
  first. Covers are cleanup-only.
- **§6 Resets:** all 10 delayed layer applies have a scoped repeating removal of
  the same target on the same input, with `interruptable 0`. Each reset interval is longer than its delay, and
  the applied target overrides the input:

  | Parent / input | Delay → reset | Target |
  |---|---|---|
  | W/S Key, LS up/down | 5 → 50 | Mod 1 / Mod 0 |
  | Mod 2, opposite driver | 200 → 250 | `L1:` / `R1: Tap Cover` |
  | Mod 0/1, own direction | 250 → 300 | `LS: Tap Cover` |
  | Protected menu, Start/Select | 300 → 350 | Menu Tap Cover |

## Findings

### F1. RTP Double Tap inherits steering layer commands

**§9 rule 2, both variants. ❌** The right trackpad is open in every steering
layer, so `RTP: Entry Point` → `RTP: Double Tap` (Always On) can open on top of
a steering stack. Under it, the left stick inherits layer commands:

| Input | Comes from |
|---|---|
| LS up | `Steering` (2.5 s exit chord), W/S Key (Mod 1 selector), Mod 1, the window, Double Tap Cover |
| LS down | W/S Key (Mod 0 selector), Mod 1, the window, Double Tap Cover |
| LS left/right | Mod 1, the window, Double Tap Cover |

The audit's `blocks_needed` says **clear** all four, because the lower outputs differ
per stack. Clearing them in `RTP: Double Tap` also drops WASD for its 150 ms
in normal play. **Decision needed:**
- (a) clear them in the window and accept the 150 ms movement gap;
- (b) block RTP touch entry while steering (the steering layers clear
  `right_trackpad/touch`);
- (c) record an `allow` with a reason.

The derived search never found this because it can't reach steering
([F8](#f8-the-inheritance-audit-cannot-reach-steering)).

### F2. Overlays carry owner recovery

**§1/§7, both variants. ❌** The DoD says an overlay removes "itself, or a local pair. The
owner handles recovery." It also says overlays "inherit broader recovery instead of duplicating every
cleanup binding". The steering overlays instead each carry, on both sticks,
the full 13-layer branch exit with an either-driver guard. Each also has a
`right_joystick` group that exists only for that:

| Overlay | Inputs (default) | Owner below already has |
|---|---:|---|
| `LS: Tap Cover` | 7 | Mod 0/1 or W/S Key guarded recovery |
| `LS: Double Tap Cover` | 7 | W/S Key guarded recovery |
| `Menu Left/Right: Tap Cover` | 14 (alternative 16) | **Full clone** of the protected entry; only `button_menu` and the touch releases differ |

For comparison, `L1: Double Tap Cover` and `Menu Left: Double Tap Cover` define one input each.
§5 allows covers to inherit touch. Cause: `build_touch_cleanup` treats every
new layer the same, and `build_menu` uses `clone()`. The fix is in
[the slim-covers plan](../../plans/2026-09-30-steering-slim-covers.md).

### F3. Windows hard-code 14 Base outputs

**§7/§8, both variants. ❌** Each `LS Up/Down: Double Tap` rebinds every face button, D-pad
direction, back button and both stick clicks to *remove window ; scroll ; key*.
That's 21 inputs and 18 wheel commands per window. Nothing underneath needs
blocking: none of those 14 inputs has a layer command in Base, Gyro, Steering
or W/S Key. So the §8 default (inherit) applies. The hard-coded keys will also go stale
if Base changes. Fix: [the slim-covers plan](../../plans/2026-09-30-steering-slim-covers.md).

### F4. Mod 2 quick exit removes Gyro

**§1, both variants. ⚠️ decision.** A quick uncovered opposite-driver release in
`Steering | …: Modifier 2` clears every layer except Base, including `Gyro`. §1
says other layers' cleanup never removes a stateful layer. The
[steering plan](../../plans/2026-09-29-steering-implementation-plan.md) also says
"Preserve unrelated persistent Gyro". The same gesture in `Gyro | …: Modifier 2`
also removes Gyro, so this may be the intended "clear to Base" gesture. If so, record
it as an exception in §1. If not, drop `Gyro` from `base_exit_targets`.

### F5. The windows have no DoD type

**§1. ⚠️** The steering Double Tap windows aren't Always On: their clock is
a 150 ms chord on the drivers, on a widened inverted LS edge. The DoD's only window type is
"Always On window (only itself)". They need a row, and the row has to say what their cleanup scope is. Today
they carry the full owner recovery on touch, like the covers do.

### F6. Recipe deviations are not recorded

**§6. ⚠️** §6 requires the full recipe "or record which part it leaves out and
why". Steering differs from the recipe in four ways:

| Recipe | Steering |
|---|---|
| Release opens the window | True center (LS edge) opens it; the cardinal release doesn't |
| Always On window | Driver-chorded clock, no Always On |
| Second press → second-press layer → 150 ms chord → Double Tap Cover | Second press → Double Tap Cover directly; no hold stage or reset |
| Release from the second-press layer reopens the window | Double Tap Cover release adds `LS: Tap Cover` (no chaining) |

The [lean README](../2026-09-30-steering-lean/README.md) explains the chorded
clock, but nothing records these deviations against §6.

### F7. Pending timers leave RS edge open

**§6 "other delays" / §8. ⚠️ decision.** Steering has pending timers: Mod 0/1
250 ms, the window 150 ms, Mod 2 200 ms and W/S 5 ms. While they run, the steering layers inherit
Base's RS edge (turn-assist ramp layers) and the trackpad layer routes.
The trackpad routes are repo-wide: `L1: Modifier 0` and `Menu Left: Entry Point`
leave them open too. **RS edge is steering-only:** `L1: Modifier 0` doesn't inherit
it. Decide whether turn assist while steering is intended (then record an `allow`) or
should be blocked.

### F8. The inheritance audit cannot reach steering

**§8 tooling. ⚠️** At depth 5 the derived search finds **0 stacks** for the
windows, Double Tap Cover and Mod 0/1. It is **unsaturated** for `LS: Tap
Cover`, W/S Key, Mod 2 and the Menu Tap Covers. So
`test_audit_inheritance.py` doesn't guard steering at all, and F1 went
unnoticed. This audit used hand-declared canonical stacks instead
([canonical-stacks.json](canonical-stacks.json)). Fix: add those stacks to
`traced_stacks.json` with decisions, or make the search target-directed.

### Recorded design choices (not findings)

- `L1:`/`R1: Tap Cover` (Base overlays) also remove `Steering | …: Modifier 2`
  on release. §7 discourages adding to other lists; this one is deliberate
  ([reused covers](../2026-09-30-steering-lean/README.md#reused-single-side-mod-2-tap-covers)).
- `LS: Tap Cover` inherits the Mod 0/1 map and that map's recovery: modified actions stay
  usable while the tap is spent. That's the intended overlay inheritance.
- Start/Select inside steering removes `Steering` and opens the ordinary menu. This
  is Steering's own deliberate exit.

## Resolution (90.7)

Author decisions on 2026-09-30; implementation in the
[steering 90.7 record](../2026-09-30-steering-lean/README.md#slim-overlays-and-dod-fixes-907).

| Finding | Status |
|---|---|
| F1 RTP Double Tap over steering | ✅ `Steering` clears right-pad touch, the only route into `RTP: Entry Point`. Pad clicks and the cursor are unchanged |
| F2 Overlays carry owner recovery | ✅ The four covers define only their own controls and inherit touch |
| F3 Windows hard-code Base outputs | ✅ Mapped-button flushes removed (D1). Sideways in the window keeps today's flush (D2, author) |
| F4 Mod 2 quick exit removes Gyro | ✅ Kept by design; recorded as a DoD §1 exception |
| F5 Windows have no DoD type | ✅ "Chorded window" row added to DoD §1 |
| F6 Recipe deviations unrecorded | ✅ Recorded in the steering README and linked from DoD §6 |
| F7 Pending timers leave RS edge open | ✅ Windows, Mod 0/1 and Mod 2 clear RS edge (author: block). Steering and W/S Key keep turn assist |
| F8 Audit can't reach steering | ⚠️ Mitigated: `tests/test_steering_lean.py` walks canonical steering stacks and fails if any can add an Always On window. `audit_inheritance.py`'s derived search still can't reach steering |

Checks after the fix: both variants pass `audit_command_budget.py` and
`audit_inheritance.py`; 31 steering tests pass; only 11 steering layers differ
from 90.6, with identical layer order. Deck checks are in
[manual-testing.md](../../archived/manual-testing.md#907-slim-steering-overlays).

## Per-layer summary

✅ pass · ⚠️ decision or record needed · ❌ fails. §2/§3 pass for every layer.

| Layer | §1 | §4 | §5 | §6 | §7 | §8 | §9 |
|---|---|---|---|---|---|---|---|
| Steering | ⚠️ F4 | ✅ | ✅ | ✅ | ✅ | ⚠️ F7 | ❌ F1 |
| LS: Entry Point | ✅ | ✅ | ✅ | – | ✅ | ⚠️ F7 | – |
| W Key / S Key | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ F7 | ❌ F1 |
| Mod 0 / Mod 1 | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ F7 | ❌ F1 |
| Mod 2 ×2 | ⚠️ F4 | ✅ | ✅ | ✅ | ✅ | ⚠️ F7 | – |
| LS: Tap Cover | ❌ F2 | ✅ | ✅ | – | ❌ F2 | ⚠️ F7 | – |
| LS Up/Down: Double Tap | ⚠️ F5 | ✅ | ✅ | ⚠️ F6 | ❌ F3 | ⚠️ F7 | ❌ F1 |
| LS: Double Tap Cover | ❌ F2 | ✅ | ✅ | ⚠️ F6 | ❌ F2 | ⚠️ F7 | ❌ F1 |
| Menu Entry ×2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ repo-wide | – |
| Menu Tap Cover ×2 | ❌ F2 | ✅ | ✅ | – | ❌ F2 | ✅ repo-wide | – |

In the §9 column, ❌ means the layer contributes an inherited route under `RTP: Double Tap`.

## §10 Ship it

| Check | Result |
|---|---|
| `audit_command_budget.py`, both variants | ✅ exit 0 |
| `audit_inheritance.py`, both variants | ✅ exit 0 on the derived search, but it doesn't cover steering (F8). With the canonical stacks: exit 1 (F1, F7) |
| Python suite | 410 tests, 1 error: untracked `tests/test_timed_audit.py` needs `z3` (unrelated work in progress) |
| Node suite | ✅ 8/8 |
| Findings recorded | ✅ [steering-lean](../2026-09-30-steering-lean/README.md), [cleanup audit](../2026-09-30-steering-lean/CLEANUP-AUDIT.md) |
| Deck section | ⚠️ present in [manual-testing.md](../../archived/manual-testing.md), C1–C5 unchecked; no steering item for "release missed while the Steam menu is open" |
| Applied and snapshotted | ✅ `versions/neptune/90.6/` |

## Reproduce

```sh
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json \
  --stacks findings/2026-09-30-steering-dod-audit/canonical-stacks.json --depth 0
python3 convert_runtime_ids.py to-titles neptune/single-set-default_hold-gyro_latest.json -o /tmp/d.json
python3 findings/2026-09-30-steering-dod-audit/static_checks.py default /tmp/d.json \
  findings/2026-09-30-steering-lean/pre-steering/neptune/single-set-default_hold-gyro_latest.json
```

Repeat with `alternative` for the other variant. The canonical stacks cover Base and Base+Gyro for each owner,
with a bank, the cover, a window, the Double Tap Cover, and Mod 2 with its cover. They're
hand-built, so they show routes that do exist; they don't prove there are no others.
