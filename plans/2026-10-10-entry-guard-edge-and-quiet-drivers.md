# Stateful layer cleanup and Steering feedback plan

Status: implemented on 2026-10-10 as **90.44**, extending both **90.43**
layouts. Both JSON/VDF pairs are validated, exported and backed up. The
[release record](../findings/2026-10-10-steering-entry-and-quiet-drivers/README.md)
documents the changes, full/targeted validation results and native checks.

Add an inverted left-stick edge chord that silently removes Entry Guard,
and make the requested Steering releases and W/S driver bindings explicitly
silent. Also remove the Steering stateful-layer removal from both Steering
Modifier 2 release clears and preserve Cursor Gyro through the dual-bumper
or dual-trigger gesture, as requested on 2026-10-10. Reuse Entry Guard's
existing slot and retain **88 action layers**. Preserve the right-stick
sensitivity values requested from the July reference; both live variants
already match them, as detailed below.

The approved interpretation matches the old fallback's **Any** driver
condition: L1 **or** R1 in default, L2 **or** R2 in alternative. Both held
also satisfy it. The clear removes **only Entry Guard**, leaving Steering
and any existing Gyro layer in place. For haptics, the scope is all
bindings owned by the W/S layers, plus their entry activators; Modifier 0/1
changes cover Release activators and their automatic Double Tap completion.
The author authorized implementation after these defaults were recorded.

## How Entry Guard will work

Keep the [90.43 entry sequence](2026-10-09-steering-entry-guard.md): remove
the transition, add Steering, then add Entry Guard on top. Entry Guard keeps
plain four-way WASD and protects an already-held movement, or the first push
after centered entry, until its release. Resting or lifting a thumb alone
does not consume that protection.

Add one Chorded Press to Entry Guard's `joystick/edge`, alongside its existing
normal outer-edge Release. Invert **only the new activator**. The stick group
stays non-inverted, so the normal Release and the four direction Releases
retain their current meaning. Keep the current default edge radius; the
`29031` directional clear threshold is a separate setting in Steering.

| New edge chord setting | Default | Alternative |
|---|---|---|
| Driver selector | L1 or R1 | L2 or R2 |
| `gyro_ratchet_button_mask` | `12` | `50331648` |
| `gyro_ratchet_button_requireany_or_all` | `0` meaning Any | Same |
| Activator `edge_binding_invert` | `1` | Same |
| `hold_repeats` | `1` | Same |
| `interruptable` | `0` | Same |
| `haptic_intensity` | `0` | Same |
| Command | Remove Entry Guard, name/beep flags `0 0` | Same |

These are the settings of the
[old fallback chord](../findings/2026-10-08-steering-rtp-and-menu-chords/build_candidate.py),
with its action adapted to the current stack. Steering is already underneath
Entry Guard, so removing the guard is sufficient; no Steering add or layer
swap is needed. Retain the old chord's unspecified repeat rate rather than
introducing a new timing value. Repeating permits recovery when the binding
becomes exposed under an already-active input. Once the guard leaves, its
chord is no longer the effective binding.

| Situation | Intended result |
|---|---|
| Enter centered, with neither driver held | Guard stays and protects the first push. |
| Enter with a full up/down push already held, with neither driver held | Guard stays until the existing direction/edge Release. |
| Inward edge chord is active with either driver held | Remove Guard silently; keep Steering and existing Gyro. |
| Enter centered with both drivers already held | The new chord can remove Guard even though the two opposite-driver guards suppress W/S acquisition. This does not clear Steering or redesign Modifier 2. |
| A normal W/S driver handoff wins first | Its existing command sequence removes Guard before adding the driver layer; the extra edge removal is unnecessary. |
| A direction or normal outer edge is released | Existing silent Guard removal remains available without a driver. |
| Guard is gone and Steering receives a full up/down push | Existing Steering-family clear at `29031`, with its beep and Low bump. |

Keep the explicit driver and fresh-menu handoffs. They prevent a new upper
layer from hiding Entry Guard's exits. Keep the current pad-helper/ramp
restrictions while protection is active. A single driver already removes
the guard through its normal handoff, so the new edge chord is an additional
recovery path, not the sole way to reach driving.

Do not rely on pressing a chord button after the inward edge was already
active to retroactively start its chord, or on releasing a driver to undo a
latched chord. Those cases retain the existing driver handoffs and real
Release exits. The broader two-driver release-order redesign stays deferred;
its old proposal to exit Steering in either order must be reconsidered against
the new requirement to preserve Steering in Modifier 2 cleanup.

## Keep Steering active after Modifier 2 cleanup

Remove only `remove_layer {{Base::Steering}} 0 1` from the existing
release-clear array in each of these layers:

| Default layer and input | Alternative equivalent |
|---|---|
| `Steering \| R1!L1: Modifier 2`, L1 Release | `Steering \| R2!L2: Modifier 2`, L2 Release |
| `Steering \| L1!R1: Modifier 2`, R1 Release | `Steering \| L2!R2: Modifier 2`, R2 Release |

That is two Steering command removals per variant. The modifier, driver,
cover, Entry Guard and other existing cleanup removals retain their current
order and targets, apart from the additional Cursor Gyro exclusion below.
Keep the existing Gyro removal, activator conditions, delays, held-use
protection and the other driver's release behavior.

The Steering removal currently carries the array's only beep. Removing that
command also removes that beep; do not move it to another cleanup command.
These two Release activators already have haptics explicitly Off.
Gyro Modifier 2 keeps its toggle and single beep while gaining the Cursor
Gyro preservation described below.

After cleanup, Steering remains available, and a still-held driver may
reacquire W/S through its existing repeating entry. Verify that recovery
does not leave stale modifiers/covers behind. Steering's independent full
up/down clear remains armed: if cleanup exposes it beneath a still-held
full deflection, that separate binding may legitimately clear Steering.
Test this separately from a centered release so the result is not mistaken
for a remaining Modifier 2 stateful-clear command.

## Preserve Cursor Gyro through the dual driver gesture

Remove `remove_layer {{Base::Cursor Gyro}} 0 0` from every Modifier 2
release binding used by the dual-bumper/trigger gesture that currently
contains it. In each variant this is six command removals:

| Layer family | Bindings affected per variant |
|---|---|
| Both `Gyro \| …: Modifier 2` layers | Both driver Releases in each layer, four entries total |
| Both `Steering \| …: Modifier 2` layers | Their existing release clears, two entries total; these also lose the Steering removal above |
| Ordinary Base Modifier 2 layers | No Cursor Gyro removal exists; retain their current behavior |

The gesture's mode change happens on Release in these bindings, even though
it is initiated by pressing both drivers. Cover both press orders and both
release orders. Preserve the other cleanup commands, held-use protection,
timings, and each remaining command's flags. Match the exact stateful title
`Cursor Gyro`; ordinary `L1/R1: Temp Cursor Gyro` overlays and their L2/R2
equivalents keep their existing cleanup.

The ordinary Gyro toggle still changes `Gyro`. Cursor Gyro retains its
response settings and its place on the stack. Because it normally enters
with Gyro underneath and inherits activation selectors, test the newly
retained `Base + Cursor Gyro` stack after toggling Gyro off, then toggle Gyro
back on and verify activation/response inheritance. Do not silently re-add
Gyro or reapply Cursor Gyro to compensate for the removed command.

Cursor Gyro's deliberate exit using both stick edges, and its menu/stateful
transition clears, remain available. Its removed commands are silent, so
this addition does not change the Gyro toggle's single beep or add feedback.

## Haptic changes by layer

Write explicit Off values. Removing a haptic field would restore an
unspecified/default value and would not establish silence.

| Layer or path | Planned change |
|---|---|
| `Steering \| LS Down: Modifier 0` | Set its LS-edge Release to `haptic_intensity: "0"`. Its two stick-touch Releases are already Off. Keep its cleanup and Double Tap transition unchanged. |
| `Steering \| LS Up: Modifier 1` | Same treatment for its LS-edge Release; preserve its existing touch-release Off settings and transition. |
| `Steering \| LS Up: Double Tap` and `Steering \| LS Down: Double Tap` | Set their automatic 150 ms completion activators to Off as the continuation of the release gesture. Preserve self-first removal, the wheel step and the delay; other window feedback is outside this change. |
| `Steering \| R1: W Key` and `Steering \| L1: S Key` | Make their own activators explicitly Off, including both driver Releases, movement, modifier entry and recovery. Use the L2/R2 equivalents in alternative. |
| W/S entry in `Steering` and `Entry Guard` | Explicitly silence the four incoming driver-add activators per variant, so entering the quiet layer cannot still bump from its parent. |
| W/S left-stick source settings | Set the D-pad mode's supported `haptic_intensity_override` to Off, covering mode-level direction feedback separately from activator feedback. |

The current W/S layers own 25 active activators each in both variants. Across
the pair, four are explicitly Off and 46 omit the intensity. None explicitly
enables haptics. Their four incoming adds and the two Modifier 0/1 edge
Releases also omit intensity. This supports making silence explicit; it
does not identify which native default produced a reported bump.
The two Double Tap completions following those modifier Releases also omit
intensity, so they are included to keep the automatic continuation quiet.

Inspect any shared groups, inactive alternatives and disabled banks before
writing settings so a W/S-local change cannot mute another owner. Avoid
inventing mode settings for switches, triggers or mouse-mode sticks. Existing
key/mouse outputs, cleanup targets, command order, chord conditions and
timings stay identical. Fn bumps, Steering's deliberate full-clear feedback,
mode-transition feedback and Gyro's single-beep changes from 90.43 stay intact.
The two Steering Modifier 2 release beeps leave with their removed Steering
commands, as specified above.
Unrelated inherited pad or Fn interactions keep their own feedback.

The implementation uses the recorded **all W/S-owned haptics** scope,
including incoming entry feedback and W/S D-pad mode feedback.

## Right-stick sensitivity from the July reference

The author requested Base and Ramp Up sensitivity from
[`MOST_RECENT_LAYOUT.post-fix.json`](../findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json).
Comparison on 2026-10-10 found that both live 90.43 variants already match
the reference's entire active `right_joystick` settings objects in these
layers:

| Layer | `sensitivity` | `sensitivity_vert_scale` |
|---|---|---|
| `Base` | `100` | Unspecified in both reference and live layouts |
| `Turning Ramp Up 0` | `150` | `80` |
| `Turning Ramp Up 1` | `200` | `67` |
| `Gyro Off Ramp Up` | Inherited; no local override | Inherited; no local override |

Base's response-curve settings (`curve_exponent: "0"`,
`custom_curve_exponent: "59"`) and deadzone settings also match exactly.
No sensitivity edits are needed. Carry these values into the next release
and verify they remain equal to the reference after the build. Retain the
current bindings, modes, timing and inheritance; do not copy the historical
groups or presets wholesale.

The reference passed layer-order, preset-order and sequential-ID checks.
It has duplicate historical `DEPRECATED` titles but is already in title
form; the comparison used the unambiguous Base/Ramp Up presets and their
active source groups without converting or modifying the reference.
Both live layouts passed all preflight checks, including unique titles.

## Implementation and validation

1. Extend the 90.43 builder with a new release component. Preflight both
   layouts and edit title-form data. Preserve runtime slot 65, all other
   runtime IDs and the layer count. Store the new edge chord before the
   existing Release; the input has two command entries, within the limit.
2. Register a precise R111 exception for Entry Guard's inverted LS-edge
   chord removing itself, with the exact selector, quiet flags and repeat
   settings. The requested inverted command overrides the general ban for
   this binding only; retain the historical fallback exception for old
   builders. Update A54 and Entry Guard's R170 explanation for the additional
   exit without turning it into unconditional centered cleanup.
3. Audit the inherited edge below the guard and all routes above it. Include
   driver/menu handoffs, both-held entry, Gyro on/off, stale stacks, and
   protected windows. Preserve the 90.43 W/S and Modifier 0/1 recovery fixes.
   Remove the two Steering commands and six Cursor Gyro commands per variant
   from the specified Modifier 2 releases, retaining the other cleanup
   targets and activator settings. Review Cursor Gyro with Gyro both present
   and absent, including inherited driver and gyro settings.
   Require the normal fix pipeline to leave the intended bindings unchanged.
4. Add scenarios for centered first-push protection, held up/down entry,
   each driver and both drivers carried into entry, either driver pressed
   after entry, inward/outward crossings, missed movement Releases, guard
   re-exposure, and both driver press/release orders. Run both variants and
   both Gyro states, including both modeled held-input exposure/order cases.
5. Check quiet release and driver-entry activators statically; compare their
   non-haptic settings and command arrays with 90.43. Verify no extra beep
   requests, preserved Fn bumps, and the existing full Steering clear.
   For both Steering Modifier 2 orders, verify the modified releases retain
   Steering at center, clean their existing targets, permit valid driver
   reacquisition and emit no clear beep. Check quick/held use and missed
   releases. With up/down held, trace the separately inherited Steering
   clear. Assert each modified Steering release array equals its 90.43 array
   minus exactly the Steering and Cursor Gyro removals; each modified Gyro
   release loses only Cursor Gyro. Update the old B2 beep/exit expectation
   while retaining Gyro toggle coverage. From Cursor Gyro, test both driver
   press/release orders, short taps, held/covered use and missed releases;
   require Cursor Gyro to survive the dual-driver gesture, the intended
   Gyro toggle to work, and both-stick/menu exits to remain functional.
   Compare the four Base/Ramp Up active right-stick settings objects with
   the July reference; they already match and must stay unchanged.
   Run the scenario suite and Budget, Window, Flow and Cleanup audits, then
   record the change report and changed-layer coverage.
6. On implementation, review descriptions and bump both variants together
   to the next release, expected **90.44** if no other release intervenes.
   Export both VDFs and save matching JSON/VDF backups after validation.

An in-memory feasibility check of the proposed Any-driver chord passed
32 modeled combinations: centered first push, held up entry, centered entry
with both drivers held, and deflected entry with both held; both variants,
Gyro on/off and both A9 exposure behaviors. No live layout was changed.
This is preliminary evidence, not the complete acceptance suite.

Native checks remain necessary for activator-local inverted D-pad edges:
the older A19 report found missed inward events, and A54 remains unverified.
Retaining ordinary Releases and driver/menu handoffs provides independent
exits. A fresh Deck load must check inward detection, centered first-push
protection, trigger soft/full-pull selection, and the requested silence.
