# Temp Cursor Gyro implementation

Implemented 2026-09-29 in both Neptune JSON layouts, starting from `c820d22`.
Version remains 90.2. VDFs and the July reference are unchanged.
[Current design](../../plans/2026-09-29-cursor-self-removal.md) ·
[Deck checklist](../../manual-testing.md#temp-cursor-gyro)

The self-removal follow-up is implemented. It supersedes the original normal-cover
property restoration and cursor touch replacements in `50758b3`; the
[original plan](../../plans/2026-09-29-temp-cursor-gyro.md) is retained as history.

## Behavior and properties

Default L1/R1 and alternative L2/R2 each have a new **Temp Cursor Gyro** overlay,
shared by the regular and Gyro versions of that modifier. A 300 ms primary hold
applies it; either stick-touch release completes that apply immediately before
removing the corresponding LST/RST helpers. The primary release clears the owner
family without entering its tap/Double Tap flow.

Each cursor overlay has thirteen cancellation inputs: face buttons, D-pad,
stick clicks, Start/Select, and the opposite modifier. Each has one uninterruptible,
repeating Regular Press removing **only itself**, with no key output or layer add.
The exposed parent's held input supplies its output and normal-cover addition.
Two guarded stick-edge inputs also remove cursor on the dual-stick gesture.
This uses the author's held-input rule; output handoff still needs Deck validation.

In each of the four regular/Gyro parents, the twelve ordinary inputs now have
three entries: an uninterruptible owner-held output chord, an uninterruptible
owner-held repeating cover-add chord, and existing interruptible repeating family
recovery. That is 48 splits per layout. Output settings and repeat behavior are
preserved; command-only repeats have no haptic feedback. The opposite-modifier
transition stays separate and repeats; two missing repeats in alternative's R2
regular/Gyro parents are fixed without changing their targets or array order.

The normal cover latches cursor off for the rest of the hold. Its primary and
touch replacements prevent inherited cursor entry. It has **no active gyro
source**: cursor removal exposes the normal response below, with no duplicated
restoration profile to maintain.

| Serialized gyro property | Temp Cursor Gyro override | Normal inherited response |
|---|---:|---:|
| `gyro_precision_speed` | 750 | 300 |
| `haptic_intensity` | 3 | 0 |
| `flickstick_haptic_bump_per_angle` | 1 | 5 |
| `mouse_move_threshold` | 10 | 0 |

Cursor values come from active group 370 in the July reference's `Gated Gyro`.
Cursor groups use `gyro_to_mouse` and `layer: "1"`. They leave natural sensitivity
inherited at 300, inherit Base's reference calibration/vertical scaling, and do not
copy Gated Gyro's activation mask. Regular and Gyro owners therefore retain
their existing distinct activation selections and Any/All rules.

The cursor and normal overlays have no Always On action or independent timer.
Both replace the primary input with release-only family cleanup. Normal covers
replace both touches with a held-owner empty guard, interruptible repeating family
recovery, and release removal of that stick's three helpers. Cursor groups omit
`touch`, inheriting the parent's cursor-add-before-helper-removal release. Their
partial stick groups define only click/edge exits and `layer: "1"`; movement and
edge geometry remain inherited. No new Always On action or delayed timer is added.

## Reference tuning and gyro inheritance follow-up

The author's follow-up copies the July reference's active Base gyro settings and
Base/ramp right-stick settings into both layouts. The initial cursor commit kept
rotation calibration 4653 and normal precision 0; current values below supersede
that initial baseline. Only settings change in this follow-up; existing bindings,
activation selections, delays, and cleanup remain intact.

| Source / reference group | Setting | Current value in both layouts |
|---|---|---:|
| Base gyro / 60 | `gyro_natural_sensitivity` | 300 |
| Base gyro / 60 | `flickstick_rotation_sensitivity` | 3853 |
| Base gyro / 60 | `gyro_vertical_horizontal_ratio` | 200 |
| Base gyro / 60 | `gyro_to_2d_conversion_style` | 4 |
| Base gyro / 60 | `gyro_speed_deadzone` | 0 |
| Base gyro / 60 | `gyro_precision_speed` | 300 |
| Base gyro / 60 | `gyro_ratchet_button_mask` | 211109453778944 |
| Base gyro / 60 | `gyro_ratchet_button_requireany_or_all` | 1 |
| Base RS / 5 | `curve_exponent` / `custom_curve_exponent` | 0 / 59 |
| Base RS / 5 | `edge_binding_radius` / `output_joystick` | 32767 / 2 |
| Base RS / 5 | `deadzone_inner_radius` / `deadzone_outer_radius` | 3280 / 32000 |
| Base RS / 5 | `deadzone_enable_type` / `sensitivity` | 2 / 100 |
| Turning Ramp Up 0 RS / 43 | `layer` / `sensitivity` / `sensitivity_vert_scale` | 1 / 150 / 80 |
| Turning Ramp Up 1 RS / 58 | `layer` / `sensitivity` / `sensitivity_vert_scale` | 1 / 200 / 67 |
| Gyro Off Ramp Up RS / 417 | `layer` | 1 |

Base RS and Gyro Off Ramp Up RS already matched the reference. Ramp sensitivities
change from 130/77 and 160/63 to the values above. Single-modifier RS sensitivity
75 and its local edge radius 7209 remain intentional overrides; no reference
stick bindings or thresholds are transplanted into those layers.

Follow the reference's sparse gyro inheritance: regular modifier owners omit an
active gyro override; persistent Gyro and all four Gyro modifier variants change
only activation selection/Any-All; LST/RST Temporary Gyro change only their touch
selector. Temp Cursor Gyro changes only its four response/haptic properties.
Normal Tap Covers now omit active gyro entirely. The prior explicit restoration
groups were unshared and are removed. Natural sensitivity, calibration, conversion, and vertical scale stay
inherited. All 15 intentional active `disabled` gyro sources in the current
menu/transition/Gyro Off contexts remain disabled. Inactive reference modes and
its old trigger mode-shift wiring are not copied.

This is a settings audit, not a Deck result. Verify the reference response feel,
activation-only layers over both responses, cursor removal, and both
ramp stages using the [manual checklist](../../manual-testing.md#reference-gyro-and-right-stick-tuning).

## Delayed-apply reset follow-up

The initial implementation in `50758b3` deferred the four single-modifier resets
per layout. The author's follow-up identified that omission. Each parent now
has a third primary-input entry: Regular Press removes **only its own Temp Cursor
Gyro** with `hold_repeats: "1"`, `repeat_rate: "350"`, and `interruptable: "0"`.
The existing 300 ms chord and release exit retain their settings. This follows
the existing Menu Entry 300/350 ms pattern; touch-release completion and the
chord's Interruptable Off setting do not substitute for the separate retry.

The reset belongs to the parent while the cursor apply is pending. It never
removes the normal Tap Cover, owner, other modifier, or stick-helper families.
Both normal and cursor overlays explicitly replace the entire primary input
with their release lifecycle, which is the intended stopping condition for
both the delayed apply and reset. A normal-cover override must therefore remain
latched until the next modifier hold. All seven Double Tap windows explicitly
replace both primary controls, preserving Always On isolation. Mod 2 also
replaces both controls; its existing combined-cover resets stay unchanged.

Coverage rises from 7 to 11 of the 19 delayed-add paths per layout. Other missing
reset paths remain in their existing review scope, including the confirmed RTP
trackball exclusion. Static tests check target scope, command count, overlay
replacement, and protected-window input replacement. Deck checks must confirm
interrupted holds can retry and that the reset retires after cursor entry,
early touch completion, or normal override, including held-across-transition
and timer-boundary cases. This follow-up adds no layers or gyro-property changes.

## Layer order and scope of changes

New keys `Preset_1000135` and `Preset_1000136` place the two cursor overlays
after the three modifier Tap Covers, within the existing cover group. Existing
layer keys are retained. Turning Ramp Up 0 and 1 remain the first two layers.
Each layout now has one action set and 55 layers, with matching preset order and
sequential preset IDs. The initial addition used fourteen new source groups per
layout. The self-removal follow-up deletes the two unshared restoration groups,
reuses cursor primary/stick groups, and adds partial cancellation and RTP blocking
groups. Current totals are 549 groups / 661 inputs in default and 552 / 697 in
alternative; the difference reflects trigger versus bumper owner sources.

Per layout:

- Retargeted four primary delayed additions and eight stick-touch release
  additions. The latter still execute add-first, before their helper removals.
- Preserved thirteen normal-cover paths per owner and their outputs; twelve
  ordinary paths now split their output and cover-add chords.
- Added eight edge chords across four owner variants and both sticks, now repeating.
- Added thirteen repeating self-cancellation inputs and two guarded edge exits
  to each cursor overlay, and removed its two local touch replacements.
- Added ten explicit no-op inputs to RTP Double Tap, protecting its timer from
  inherited cursor removals and repeating cover additions.
- Extended 140 existing cleanup entries with 204 removal subcommands; new overlay
  lifecycle/recovery entries account for the remaining new removals.
- Added four cursor-entry reset entries in the follow-up above, each targeting
  only its own cursor overlay.
- Current active removal-entry count is 390, including 207 guarded repeating
  Regular Press recoveries. Command entries never exceed three per input.

## Cleanup ownership

| Existing entry type | Entries/layout | Added cleanup |
|---|---:|---|
| Single-modifier guarded recovery | 68 | Own cursor overlay |
| Uncovered single release into Double Tap | 4 | Own cursor overlay, before adding the timed window |
| Mod 2 current-branch recovery | 56 | Both cursor overlays |
| Uncovered Mod 2 release | 8 | Both cursor overlays; preserve its existing Gyro change |
| Single normal-cover release | 2 | Own cursor overlay |
| Combined-cover released-side exit | 2 | Only the released owner's cursor overlay |

Single-family recovery now removes four targets. Mod 2 current-branch recovery
removes eleven, retaining its exclusion of the opposite order. Combined-cover
release removes nine and preserves the opposite single family and both of its
overlays. Uncovered Mod 2 release clears thirteen modifier/cover targets plus
its existing persistent-Gyro operation.

Periodic combined-cover resets still remove only their pending combined cover.
Scroll/menu recovery and Double Tap self-exits were not widened. Normal covers
remove themselves before their dependent cursor/owner cleanup; cursor overlays
remove themselves first on primary release. Timed windows are still added last.

## Stick edges and inheritance

Each single-owner edge now has three command entries:

1. An interruptible empty chord requiring the held modifier.
2. An uninterruptible All chord requiring that modifier **and the opposite
   stick's deflection**, repeatedly adding the normal cover.
3. Interruptible, repeating removal of the four-target owner family.

Cursor edges use the same two chord conditions but remove only cursor in their
stronger chord and lost-owner fallback. The empty owner guard stays interruptible
so the dual-stick chord can win. Both uninterruptible chords on ordinary inputs
do not change this edge-guard convention.

The local edge supplies its stick condition. Requiring the owner in the stronger
chord prevents two deflected sticks from adding a cover and blocking stale-state
recovery after the modifier is lost. Default masks retain LB/RB bits 3/2; alternative
retains LT/RT soft-pull bits 25/24. Opposing LS/RS deflection uses bits 30/31, verified
in the installed Steam picker. It does not require a full trigger pull.

Only these four single-modifier LS/RS pairs change edge geometry, to LS radius
4915 and RS radius 7209. These account for the modes' different hysteresis to
target roughly 25% engagement; see the evidence below. Base movement,
the WASD scaffold, ramp-up settings, other recovery layers, and shared mode-shift
groups are unchanged. Physical threshold calibration and overlapping-chord
arbitration remain Deck checks.

| Upper stack | Intended inheritance/protection |
|---|---|
| Normal covers | Inherit gyro and owner output/cover repeats; replace primary and touch lifecycle |
| Cursor overlays | Override only four gyro response properties; repeat self-removal on cancellation inputs and guarded edges; inherit both touches and movement |
| Mod 2 and combined cover | Both normal covers are applied before entering Mod 2; its own touch/edge bindings remain in charge; released-side exits preserve the valid opposite side |
| Scroll, menu entry, Fn, Transition | Keep their existing touch/edge replacements and cleanup scopes; menu gyro remains disabled |
| RTP Double Tap | Can remain above a modifier/cursor after quick RTP touch release; ten new face/D-pad/stick-click blocks stop inherited mutations and temporarily suppress those outputs; existing primary/edge/touch replacements and ordered exits remain |
| Other six Double Tap windows | No demonstrated single-modifier/cursor coexistence route: owning release clears that family first, or parent replacements intercept the Base entry input. Existing blocks and ordered exits stay intact; stale/injected stacks remain a runtime check |
| Fn stick-click mode shifts | Their explicit touch/edge blocks remain intact |
| Base trackpad-touch mode shifts | Groups 1039/1043 are marked `inactive modeshift` and contain key-only bindings without normal-cover additions; enabled Base commands reference them, but their activation under modifiers is unverified |

The [per-window inheritance review](SELF-REMOVAL-INHERITANCE.md) records all seven
windows and surrounding stacks. RTP Entry/Cover/Circular Scroll can inherit
cancellation intentionally. A cursor removal during RTP Entry can restart its
150 ms delay; verify it without adding a reset to the author-excluded RTP touch.
RTP Double Tap's existing right-trackpad mode replacement also needs device
verification; the new ordinary-input blocks do not prove every source isolated.

Review correction: the earlier explanation overstated the last row as a confirmed
cursor behavior gap. The saved references and missing cover actions are established;
whether Steam activates those inactive mode-shift targets under the modifier stack
has not been established. Treat this as a verification task first. On the Deck,
check actual activation and cover behavior before and after the 300 ms cursor apply,
including trackpad touches held across transitions. Only design a fix if the bypass
is reproduced; otherwise close the concern without changing bindings. If a fix is
needed, review its inheritance through protected windows before adding layer
mutations to any shared mode-shift group.

## Normal-value verification

Normal precision speed 300 is explicit in both layouts' active Base gyro group
576 after the reference-tuning follow-up; the initial value was 0. The other
three normal values are omitted there. They were verified by read-only
inspection of the installed Steam client's native gyro constructors:

- File: `/Users/abdi/Library/Application Support/Steam/Steam.AppBundle/Steam/Contents/MacOS/steamclient.dylib`
- SHA-256: `21059b1c2bf03286e715e1f2693dd0cdc0f3608ef82fcbe5bfe8c3c61cb697aa`
- Inspected x86_64 slice of the universal Mach-O; addresses below refer to the
  extracted thin binary. No Steam layout was loaded or mutated by this inspection.

The native setting table at `0x1849aa0` maps the property enums to their serialized
names. RTTI identifies `CGyroToMouseMode` constructor `0x7264ba`, which calls
`CGyroTo2DMode` constructor `0x71f848`. Their registered integer tuples are:

| Property | Enum | Registration | Tuple address | Current/default/min/max |
|---|---:|---|---|---|
| `haptic_intensity` | 3 | `0x71fd73` | `0x1569260` | 0/0/0/3 |
| `flickstick_haptic_bump_per_angle` | 139 | `0x71fdaf` | `0x156c060` | 5/5/0/360 |
| `mouse_move_threshold` | 44 | `0x726511` | `0x156bc10` | 0/0/0/40 |

The hardware-specific adjustment function at `0x7207ca` does not change these
three defaults. Reproduce the tuple reads without executing Steam code:

```sh
lipo '/Users/abdi/Library/Application Support/Steam/Steam.AppBundle/Steam/Contents/MacOS/steamclient.dylib' \
  -thin x86_64 -output /tmp/cursor-defaults-steamclient-x86.dylib
```

```python
import struct
from pathlib import Path

binary = Path('/tmp/cursor-defaults-steamclient-x86.dylib').read_bytes()
for offset in (0x1569260, 0x156c060, 0x156bc10):
    print(hex(offset), struct.unpack_from('<4i', binary, offset))
```

The installed `steamui/chunk~2dcc5aaf7.js` also contains the picker mappings
`[30,"GyroLeftStickDeflect"]` and `[31,"GyroRightStickDeflect"]`. These verify the
selector identities, not their physical activation threshold. Confirm normal
property values and threshold behavior after a fresh load on the target Deck.

## Edge threshold verification

The same native build uses different hysteresis for the two active stick modes.
For an outer edge, common helper `0x70c988` engages above
`radius + 32767 × hysteresis / 100`, and releases at or below the corresponding
subtracted value. The implementation accounts for that:

| Source / mode | Radius | Hysteresis | Calculated entry | Calculated release |
|---|---:|---:|---:|---:|
| LS / `dpad` | 4915 | ±10% | ~25% | ~5% |
| RS / `joystick_mouse` | 7209 | ±3% | ~25% | ~19% |

Both calculations use radial input after source/hardware calibration and before
the mode's movement deadzone. Thus Base LS `deadzone:13276` does not clamp this
edge check. A shared nominal radius 8192 would instead engage near 35%/28% in
this build, so it was replaced with the two radii above before final validation.

Native locations:

- `CDPadMode` edge initialization `0x71b464–0x71b48f` configures member `+0x4c8`
  with the edge radius, hysteresis 10, and range 32767. Movement deadzone state
  is separate at `+0x4f0`. Frame update `0x71c3bc` supplies radial magnitude to
  edge update `0x71c1cc` before movement filtering.
- `joystick_mouse` uses `CJoystickMoveMode`, constructor `0x72e34a`, mode 7.
  Edge initialization `0x72e1b5–0x72e1e7` configures member `+0x288` with radius
  property 7, hysteresis 3 (constant `0x1558670`), and range 32767. The check at
  `0x730193–0x7301c9` uses the source's int16 x/y radial magnitude, rather than
  the mode's deadzoned output position.

These are static calculations, not measured physical travel on the Deck.
The threshold behind the **opposing-stick deflection selector** remains
unverified. Both edge behavior and the full two-stick condition must be checked
on device; selector identity alone does not establish its threshold.

## Validation

- Both complete command-budget scans pass, including inactive/unreferenced groups
  and disabled activator banks; maximum three enabled entries per input.
- All 26 unit tests pass. They cover exact split outputs and chord settings,
  repeating cover additions, self-only exits, cursor touch inheritance versus
  cover touch blocking, no cover gyro sources, opposite-modifier transition order,
  RTP's ten blocks, owner cleanup, and existing Always On boundaries. Reset and
  reference-tuning tests preserve their target/timing, exact settings, and allowed
  gyro override categories.
- Actual CLI `to-titles` before editing; actual CLI `to-ids` after validation.
  Each layout resolves 1,813 runtime references and round-trips exactly back to
  the edited title-form text. Layer/preset ordering and unique titles pass.
- Semantic review compares against the working baseline from before self-removal,
  retaining the earlier reset/tuning changes. Output strings and settings, primary
  apply/reset/release entries, normal-cover touches, timer entry/exit arrays, and
  unrelated source settings are preserved. Only RTP's ten no-op inputs change
  timed-window coverage.

These checks establish saved configuration. Pending-delay cancellation at the
300 ms boundary, both same-selector uninterruptible chords firing together,
output delivery/release after self-removal, simultaneous override/touch-release
dispatch, missed-owner recovery, inherited mode shifts, and physical stick behavior require the
[manual checklist](../../manual-testing.md#temp-cursor-gyro).
