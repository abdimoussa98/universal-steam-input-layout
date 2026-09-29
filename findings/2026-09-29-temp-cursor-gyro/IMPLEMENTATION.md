# Temp Cursor Gyro implementation

Implemented 2026-09-29 in both Neptune JSON layouts, starting from `c820d22`.
Version remains 90.2. VDFs and the July reference are unchanged.
[Design](../../plans/2026-09-29-temp-cursor-gyro.md) ·
[Deck checklist](../../manual-testing.md#temp-cursor-gyro)

## Behavior and properties

Default L1/R1 and alternative L2/R2 each have a new **Temp Cursor Gyro** overlay,
shared by the regular and Gyro versions of that modifier. A 300 ms primary hold
applies it; either stick-touch release completes that apply immediately before
removing the corresponding LST/RST helpers. The primary release clears the owner
family without entering its tap/Double Tap flow.

The normal Tap Cover remains the override for the existing thirteen face,
D-pad, click, menu-button, and opposite-modifier paths per owner. Both-stick
edge chords add the same cover. Once it is applied, its primary and touch input
replacements prevent lower cursor-entry commands from being inherited. It
restores these properties explicitly, even if the cursor overlay remains below:

| Serialized gyro property | Temp Cursor Gyro | Normal Tap Cover |
|---|---:|---:|
| `gyro_precision_speed` | 750 | 0 |
| `haptic_intensity` | 3 | 0 |
| `flickstick_haptic_bump_per_angle` | 1 | 5 |
| `mouse_move_threshold` | 10 | 0 |

Cursor values come from active group 370 in the July reference's `Gated Gyro`.
Both profiles use `gyro_to_mouse` and `layer: "1"`. They leave natural sensitivity
inherited at 300, retain the current calibration/vertical scaling, and do not
copy Gated Gyro's activation mask. Regular and Gyro owners therefore retain
their existing distinct activation selections and Any/All rules.

The cursor and normal overlays have no Always On action or independent timer.
Each replaces both touch inputs with three entries: held-owner empty guard,
interruptible repeating family recovery, and release removal of that stick's
three helpers. No touch release inside either overlay adds a layer. Their
partial stick groups contain only `touch` and `layer: "1"`; direction, click, edge,
movement settings, and mode-shift behavior remain inherited.

## Layer order and scope of changes

New keys `Preset_1000135` and `Preset_1000136` place the two cursor overlays
after the three modifier Tap Covers, within the existing cover group. Existing
layer keys are retained. Turning Ramp Up 0 and 1 remain the first two layers.
Each layout now has one action set and 55 layers, with matching preset order and
sequential preset IDs. Fourteen new source groups per layout provide the cursor
profiles/lifecycle and the normal covers' restoration/touch replacements.

Per layout:

- Retargeted four primary delayed additions and eight stick-touch release
  additions. The latter still execute add-first, before their helper removals.
- Preserved the other thirteen normal-cover paths per owner and their outputs.
- Added eight edge chords across four owner variants and both sticks.
- Extended 140 existing cleanup entries with 204 removal subcommands; new overlay
  lifecycle/recovery entries account for the remaining new removals.
- Current active removal-entry count is 360, including 207 guarded repeating
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
   stick's deflection**, adding the normal cover without repeat.
3. Interruptible, repeating removal of the four-target owner family.

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
| Normal/cursor overlays | Inherit owner edge/click/direction actions; replace primary and touch lifecycle; override four gyro properties only |
| Mod 2 and combined cover | Both normal covers are applied before entering Mod 2; its own touch/edge bindings remain in charge; released-side exits preserve the valid opposite side |
| Scroll, menu entry, Fn, Transition | Keep their existing touch/edge replacements and cleanup scopes; menu gyro remains disabled |
| Seven Double Tap windows | Explicit LS/RS edge blocks and complete touch replacements prevent inherited layer changes; existing self-first exits and add-last entry stay intact |
| Fn stick-click mode shifts | Their explicit touch/edge blocks remain intact |
| Base trackpad-touch mode shifts | Existing face/D-pad key-only groups 1039/1043 remain unchanged; they do not add normal covers |

The last row is retained baseline behavior, not an author-confirmed intentional
cursor exclusion. Test it explicitly rather than assuming all mode-shifted
face/D-pad outputs have the normal modifier's cover action. Broadly changing
those shared groups would affect other contexts and protected windows.

## Normal-value verification

Normal precision speed 0 is explicit in both layouts' active Base gyro group 576.
The other three normal values are omitted there. They were verified by read-only
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
- All 18 unit tests pass. New checks cover cursor/normal property pairing, inherited
  sensitivity/gates, exact entry and override routes, owner cleanup scope, and
  explicit overlay input replacements; existing tests retain Always On ordering
  and both-edge blocks.
- Actual CLI `to-titles` before editing; actual CLI `to-ids` after validation.
  Each layout resolves 1,803 runtime references and round-trips exactly back to
  the edited title-form text. Layer/preset ordering and unique titles pass.
- Independent semantic review reconstructs every original existing group after
  removing only the intended cleanup, routing, and edge changes. Base, existing
  output keys, timed groups, and unrelated settings remain unchanged.

These checks establish saved configuration. Pending-delay cancellation at the
300 ms boundary, simultaneous override/touch-release dispatch, missed-owner
recovery, inherited mode shifts, and physical stick behavior require the
[manual checklist](../../manual-testing.md#temp-cursor-gyro).
