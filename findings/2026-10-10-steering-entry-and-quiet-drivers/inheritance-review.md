# 90.44 inheritance and feedback review

Reviewed on 2026-10-10 against both live 90.43 inputs and the approved follow-up
plan. This independent review initially used the proposed binding changes in
memory; it did not alter a layout. The release's candidate tests and audit
artifacts provide the full-build checks. After both live JSON files were updated
to 90.44, this review repeated all 80 observations on those files successfully.
It also independently compared the six modified release arrays per variant with
the 90.43 backups: only the six Cursor and two Steering commands were removed,
with every other command and activator setting preserved. Cursor's own source
groups were unchanged, the 50 W/S activators and two LS mode overrides were Off,
the Guard source stayed non-inverted, and all 88 runtime slots retained order.

Both inputs passed layer-order, preset-order, sequential-preset-ID and unique-title
preflight. Numeric references were converted to titles in memory. Binding arrays
were read in execution order, bottom to top. Active source groups were inspected
separately from inactive groups, disabled activator banks and mode shifts.

## Retained Cursor Gyro

The six affected Release entries are in four layers per variant: both releases
in each Gyro Modifier 2 layer, and the existing broad release clear in each
Steering Modifier 2 layer. Removing the exact stateful `Cursor Gyro` target does
not change temporary cursor overlay cleanup.

Cursor Gyro has a `gyro_to_mouse` source with response overrides only. It has no
local activation selector and no driver entry override. Gyro has the same source
mode and changes only activation fields. Their ordering therefore has the
following result:

| Stack, bottom to top | Activation inherited from | Effective selector | Cursor response |
|---|---|---|---|
| Base, Gyro, Cursor Gyro | Gyro | `211109453758464`, Any | Retained |
| Base, Cursor Gyro | Base | `211109453778944`, All | Retained |
| Base, Cursor Gyro, Gyro | Gyro | `211109453758464`, Any | Retained |

Base's mask selects both menu buttons, both stick touches and both stick
deflections with All semantics. Gyro's mask selects the four stick conditions
with Any semantics. Consequently, preserving Cursor while switching Gyro off
preserves its response profile, not the persistent Gyro activation gate. Re-adding
Gyro above Cursor restores that gate without overriding Cursor's response. No
compensating re-add or stack reorder is needed.

The retained Cursor settings are precision speed `750`, haptic intensity `0`,
bump-per-angle `1` and movement threshold `5`. Base still supplies natural
sensitivity `300`, rotation calibration `3853`, vertical ratio `200`, conversion
style `4` and speed deadzone `0`.

The independent in-memory check performed **64** toggle observations across
both variants, both driver press orders, both release orders, both modeled
held-input exposure behaviors and both scheduler tie orders. Each sequence
toggled Gyro off, then back on. Cursor survived, Gyro matched the selected toggle
state, and the resolved response and selector settings matched the table.

Cursor's own two stick-edge exits are unchanged. Each repeats an All chord on
the other stick's deflection, removes only Cursor, has haptics Off, and retains
its existing **beep flag 1**. These are deliberate exits, so Cursor can still
leave after a dual-driver release exposes both already-deflected stick edges.
Upper modifiers, Tap Covers and Double Tap windows replace those edges while
they are active; the repeating Cursor exit can resume after those layers leave.
Menu/stateful transition cleanup and active disabled gyro contexts remain
unchanged.

## Entry Guard and held inputs

The new chord belongs to `Steering | LS: Entry Guard`'s LS edge. Its local
inversion does not invert the source group or the existing outer-edge Release.
Its Any mask is `12` for default and `50331648` for alternative. It removes only
Entry Guard, with quiet flags, Hold to Repeat and Interruptable Off.

| Boundary | Exposed behavior and intended result |
|---|---|
| Base, optional Gyro, Steering, Entry Guard; no driver | Four direction outputs and their Releases protect the first movement. Center alone does not remove Guard. |
| Same stack; either driver and inward edge active | The added edge chord removes Guard. Steering and the existing Gyro state survive the chord itself. |
| Both drivers carried into entry with a full up/down push | Both opposite-driver guards suppress W/S acquisition; inward chord is inactive while deflected. Direction/outer-edge Release or the subsequent inward edge removes Guard. |
| Normal W/S handoff | The existing driver command removes Guard before ramp cleanup and driver add. No Guard remains underneath the driver. |
| Fresh menu press | The existing Start Press removes Guard before adding the stateful menu entry. A menu button carried into entry does not retroactively count as a fresh press. |
| Stale upper layer hides Guard | The upper layer's effective edge wins. When it leaves, Guard's repeating chord can recover if the inward input and driver condition are active. |
| Guard is removed under a held full up/down direction | Steering's separate repeating Soft Press may become exposed and clear Steering. The new chord itself does not request that clear. |

Inspection of the ordinary guarded stack found only four effective layer-add
entries: the two driver handoffs and the two fresh-menu handoffs. Every one
removes Guard before its add. Guard's pad click/touch blocks and right-stick edge
block prevent pad helpers and turning-ramp layers from hiding movement Releases.
Touch releases remain helper cleanup, not guard removal.

The independent in-memory check added **16** cases for both drivers carried into
entry while LS was fully up or down, covering both variants, both exposure
behaviors and both scheduler tie orders. Guard and Steering remained through the
held deflection; recentring removed Guard and retained Steering. Together with
the Cursor checks, **80** modeled observations passed.

First-push protection remains release based, not strict centre detection. Rolling
between directions can release one direction and disarm Guard while another
direction remains held. The plan preserves this existing behavior. Driver
handoffs and ordinary Releases also remain necessary: do not depend on a chord
starting retroactively when its selector becomes held, or on releasing a driver
to undo an already latched chord.

## Steering Modifier 2 cleanup

The changed releases are L1 in `Steering | R1!L1: Modifier 2` and R1 in
`Steering | L1!R1: Modifier 2`, with L2/R2 equivalents in alternative. Their broad
cleanup retains its existing targets and order except for the exact Steering and
Cursor removals. Thus a centred release retains Steering, retains any Cursor
bystander, removes Gyro as before, and removes the driver/modifier/cover family.
The only former beep was attached to the removed Steering command; it must not
be transferred to another removal.

Steering then exposes its existing driver acquisition repeats and full-deflection
clear. A driver still held can reacquire W/S. A full up/down direction exposed
before or during reacquisition can independently trigger the `29031` Soft Press
clear, which repeats every 50 ms, preserves Gyro and emits its existing single
Steering beep and Low bump. This is why a centred release and a release with
full deflection need separate expectations. The change does not promise to keep
Steering through the independently requested stick-clear gesture.

Gyro Modifier 2 still removes Steering in its own four toggle-off releases. The
approved Steering preservation is scoped to the two **Steering** Modifier 2
releases; broadening it to Gyro Modifier 2 would change the requested scope.
The deferred two-driver release-order redesign is not part of this release.

## Haptic ownership and timer isolation

Both W/S layers have 25 active activators per variant. Every source group is
exclusive to its owning W/S layer: default uses switch, LS and RS groups;
alternative adds separate left/right trigger groups. There are no inactive
alternate references, disabled activator entries, mode shifts, or shared groups
in these layers. Setting their activators and supported LS D-pad haptic override
to Off therefore has no shared-group side effect. The four incoming driver adds
in Steering and Entry Guard also need explicit Off, as specified by the plan.

The Mod 0/1 LS-edge Releases keep cleanup-before-add ordering. Their two Double
Tap completion entries keep the 150 ms delay, self-removal first, then the wheel
step. The feedback setting changes no timing or command order.

All **11** Always On windows have explicit empty Full Press replacements on both
stick edges: the two ordinary driver windows, LST, RST, RTP, two ordinary menu
windows, two Steering direction windows and the two combined menu windows.
These intentional blocks suppress Guard's new inward edge and Cursor's exit
while a timed window is active, including an unusual stale stack. They must not
be replaced with extra cleanup. Steering's direction windows also replace the
up/down actions, avoiding an inherited full Steering clear during their timer.
Existing self-first exits and add-last window entry remain required.

The requested mute has an ownership boundary. A Steering Double Tap window
replaces W/S driver presses/releases with its **own** activators; those retain
unspecified haptics because only its automatic completion is included in this
plan. Steering Tap Cover and Double Tap Cover Releases likewise remain outside
the Mod 0/1-release edits. Unrelated inherited pad/Fn feedback, Fn add bumps and
the intentional Steering full-clear feedback remain intact. This review did
not silently expand the approved mute to those other owners.

## Limits and release checks

No additional layer or unplanned binding change is required by this review.
The final release should verify that the fix pipeline preserves the six Cursor
exclusions and two Steering exclusions, and that all other release commands and
settings remain unchanged apart from the approved haptic fields.

Model checks establish configured behavior, not native input delivery or audible
and tactile output. In particular:

- A19/A54 still require a fresh Steam load to verify activator-local inverted
  D-pad edges and both soft/full trigger selection paths.
- Held-input exposure, chord latching and timer/repeat scheduling retain the
  existing native uncertainty; the checks exercise both modeled exposure and
  scheduling cases but cannot settle the client behavior.
- The simulator treats unspecified haptic intensity as zero. Passing scenarios
  cannot prove silence; explicit Off values and a device check are needed.
- Gyro response inheritance was inspected field by field. The simulator does
  not model pointer movement or evaluate the physical gyro activation gate.
