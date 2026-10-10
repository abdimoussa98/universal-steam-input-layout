# Restore Steering entry protection

Status: **implemented and validated as 90.43**, both variants, on 2026-10-09.
Both JSON/VDF exports and matching version backups are saved; see the
[release record](../findings/2026-10-09-steering-entry-and-feedback/README.md).
The author added the beep audit corrections to this batch. The dual-bumper
release-order fix remains deferred. Native Steam checks remain listed in the
release record.

The [2026-10-10 follow-up plan](2026-10-10-entry-guard-edge-and-quiet-drivers.md)
adds the inverted driver chord, quieter Steering releases/W/S feedback, and
the revised stateful cleanup in **90.44**. See its
[implementation record](../findings/2026-10-10-steering-entry-and-quiet-drivers/README.md)
for current validation/export status; the design below records 90.43.

Entering Steering with the left stick already deflected must preserve the
initial movement instead of immediately running the up/down clear. The author
also chose to protect the first push when entering with the stick centered.
After that movement is released, the existing full-deflection clear is armed.

Reuse the dormant `Steering | LS: Fallback Guard` slot as
`Steering | LS: Entry Guard`. This keeps **88 action layers** and preserves
the existing runtime IDs. Rebuild its bindings for entry protection; its old
fallback-return behavior must not survive the rename.

## What the older implementations did

| Implementation | Relevant behavior |
|---|---|
| [90.10](../findings/2026-10-01-stateful-transitions/build_candidate.py) | The entry commit removed the transition, added Steering, then added Entry Guard on top. The guard supplied plain WASD. Its normal stick-edge Release or a driver takeover removed it. Centered entry protected the first push. |
| [90.24](../findings/2026-10-04-required-cleanups/build_candidate.py) | Added repeating recovery on stick touches and other inputs, guarded by left-stick deflection. At center, a resting thumb could remove the guard before the first push. Those removals conflict with the behavior now requested. |
| [90.31](../findings/2026-10-04-fallback-window/build_candidate.py) | Added a quiet self-removal to each direction's Release, allowing a shallow push to disarm the guard. Kept the normal edge Release and Steam's default outer-ring radius. |
| [90.33](../findings/2026-10-05-steering-fallback-guard/README.md) | Repurposed the slot as Fallback Guard and stopped adding a guard at Steering entry. |
| [90.42](../findings/2026-10-09-fn-haptics-and-steering-clear/README.md) | Up/down now clears Steering directly. Without entry protection, an already-held full deflection also clears it. |

The selected exit contract follows the later release-based guard: the first
**direction Release or normal outer-edge Release** disarms it. This is not
strict center detection. Rolling between directions can release one direction
and arm the clear; if up/down is then held at full deflection, it can exit
immediately without a return to center. Keep that behavior
explicit in tests and documentation. Do not restore the old inverted-edge
center polling or invent a new radius to approximate center.

## Changes by layer

| Layer or path | Planned change |
|---|---|
| `Transition Set 1` | Restore the entry commit: remove transition, add Steering, add Entry Guard last. Preserve the current single entry beep and Low haptic. |
| Renamed `Steering | LS: Entry Guard` | Plain W/S/A/D, quiet release exits, and protection for the first movement. Match Steering's current four-way source settings; do not retain the fallback's eight-way override. |
| `Steering` up/down | Keep Soft Press, threshold `29031`, repeating removals every `50 ms`, Low haptic and the Steering-removal beep. Its clear removes the renamed guard with the rest of the family. |
| Driver acquisition | Remove Entry Guard before adding the W/S driver layer. Retain current ramp cleanup, repeat settings and modifier behavior. Default uses L1/R1; alternative uses L2/R2. |
| Stateful menu entry | A fresh menu press consumes Entry Guard before applying its current Entry Point, preserving Fn access and menu-plus-stick clear. A menu button carried into entry does not consume protection. |
| Full-clear and recovery owners | Rename existing references and include the guard wherever the existing scope clears Steering. Keep unrelated Gyro, touch-helper and partial-branch cleanup boundaries. |

## Implementation sequence

The same release also incorporates the two investigations completed before
implementation:

- **Modifier 0/1 recovery:** on all 26 fallback entries per variant whose
  guard requires both LS deflection and a driver, remove the invalid stick
  modifier/cover without removing a still-held W/S owner. Keep owner cleanup
  with the owner; update the cleanup generator so rebuilding preserves this
  scope. Verify shallow push → center → RS edge → full push while the driver
  remains held, and stale-owner recovery after a missed driver release.
  Integration also exposed a missed-release loop with the stick still fully
  deflected: after cancelling the modifier, a stale W/S owner's unconditional
  direction add could recreate it immediately. Change each W/S layer's
  up/down to an owner-held repeating add plus interruptible repeating
  owner-family cleanup when that owner is absent. Keep the existing 50 ms
  modifier-add retry, output behavior and two-entry budget. Test fully held
  directions as well as shallow/centered recovery.
  Carry that recovery through the eight direction inputs in LS Modifier 0/1,
  LS Tap Cover and LS Double Tap Cover that hide those owner bindings. Reuse
  their existing driver-guarded cleanup families, retain cover delays and
  wheel-repeat timing, and stay within three entries per input.
  See the [dropout investigation](../findings/2026-10-09-steering-modifier-dropout/README.md).
- **One beep per mode change:** in the four Gyro Modifier 2 Release entries,
  keep the Gyro-removal beep and silence the Steering/renamed-guard removals.
  In the two existing Steering Modifier 2 full-clear releases, enable only
  the Steering-removal beep. Preserve all targets, ordering, activation
  conditions, name flags and haptic settings. Fn remains silent. This does
  not implement the deferred two-bumper release-order change. Correct stale
  Fn beep guidance and verify exact request counts, while keeping native
  audio behavior distinct from simulator requests. See the
  [beep audit](../findings/2026-10-09-layer-beep-audit/README.md).

1. Extend the 90.42 builder in a new findings folder. Preflight both layouts
   and work in title form. Rename the dormant slot in place, including every
   reference in the new layout. Preserve the order of action layers and
   presets. Historical builders and their rules remain usable.
2. Replace the guard's saved bindings. Remove all fallback-to-Steering adds,
   the inverted-edge return, fallback swaps, and old Gyro-modifier entry
   paths. Explicitly bind all four directions to their movement keys and add
   quiet Release self-removals. Keep a normal, non-inverted edge Release and
   the default radius. Guard application and removal add no feedback.
3. Restore the transition commit in one binding array. Runtime order is
   `remove Transition Set 1 → add Steering → add Entry Guard`; storage order
   is reversed. Preserve the beep on Steering's add and the existing Low
   feedback on the release activator. Check the held-input case on Steam:
   the simulator's command-array scheduling alone does not establish native
   timing between the two adds.
4. Preserve the author's centered-entry choice. Neither a resting thumb,
   thumb lift, right-stick movement nor an automatic cleanup retry may
   remove a valid guard before its first stick movement. Keep the stick-touch
   release cleanup for each side's ordinary helpers. Do not copy the old
   deflection-guarded repeating self-removals. Record exact R169/R170
   exceptions where required cleanup would otherwise demand early
   self-removal; centered Entry Guard is an intentional live state.
   Driver/menu cancellation already satisfies R171; do not exempt it.
5. Wire driver and menu handoffs to remove the guard before their existing
   target adds. Drivers retain their repeating acquisition so a held driver
   can take over. The guard's two menu inputs use fresh-press-only
   `Start_Press` handoffs: do not inherit Steering's repeating menu adds
   here, since an opposite menu button already held at entry would consume
   protection. After handoff, current Entry Point/Fn behavior resumes.
   Keep bottom-to-top command order and at most three command entries per
   input. Check opposite-driver chords without changing the deferred
   Modifier 2 release-order behavior.
6. Review every inherited layer-add path while the guard is active, including
   right-pad touch/click, left-pad click/swipes and right-stick ramps. For
   the initial implementation, block new pad-helper and ramp entries in
   the guard while retaining plain outputs and camera movement. Left-pad
   swipes use direct Escape/Enter/Tab/Backspace replacements; pad clicks
   explicitly block their helper entries. Ordinary bindings become
   available when protection ends. This keeps the temporary guard's
   releases exposed (R137), including through a held pad touch, and avoids
   removing it on pad entry only to expose an immediate up/down clear.
   Menu and driver handoffs are the deliberate exceptions: the guard is
   removed before another layer is added.
7. Review all Steering clears, transition cancellation and Gamepad entry for
   orphan prevention. The two existing Steering Always On windows must
   still be removed first; Steering itself remains last in the up/down
   clear. The renamed guard replaces the old fallback target in that list.
   Audit any generated cleanup differences individually.
8. Update the rule registry and documentation for a reachable temporary
   Entry Guard. Scope historical fallback exceptions to layouts that still
   contain that fallback; do not blindly rename frozen-build exceptions or
   extend the inverted-edge exemption to the new guard.

The temporary pad/ramp blocks and menu takeover are explicit behavior choices
in this proposal. Preserving all pad gestures during the guarded movement
would require a separate design for windows that hide the guard's Releases;
it should not be introduced as an incidental inheritance change.

## Acceptance checks

- Enter while holding up or down beyond the clear threshold: Steering and
  Entry Guard remain; movement continues; no exit beep or haptic repeats.
- Enter centered, including with thumbs resting on either stick: wait, then
  push in any direction. That first push stays protected until released.
- Release after a shallow push that never reached the outer ring: Entry
  Guard ends and Steering remains. Also check full-radius edge Release and
  direction changes without centering under the documented contract.
- After disarming, a fresh full up/down performs the current complete
  Steering-family clear with its beep and Low bump. A shallow push retains
  Steering. Preserve Gyro and ordinary W/S movement after the clear.
- Acquire either driver while protected, including already-held controls:
  remove the guard before driver entry; verify both modifier orders without
  implementing the deferred symmetric clear.
- Check both fresh menu handoffs, Fn feedback and menu-plus-stick clear.
  A held opposite menu button at entry must not consume protection; after
  its release and a fresh press, the handoff must work normally.
- Hold or activate pad touches, pad clicks and right-stick movement during
  entry protection: no hidden Release and no accidental Steering exit.
- Miss a stick release while Steam's menu is open: driver/menu handoff and
  the next real movement Release recover; full clears leave no guard behind.
- Run every case in both variants and with Gyro on/off. Reverse the current
  `90.42 S2` expectation that held-input entry should exit. Keep explicit
  tests for an already-armed Steering base, and keep historical/experimental
  scenario coverage separate from live coverage.

Run Budget, Window, Flow and Cleanup audits, relevant static tests and the
scenario suite. Record coverage and unresolved Steam assumptions before the
new snapshot. Native checks must confirm held-input release delivery,
transition entry ordering, physical Soft Press thresholds and feedback;
simulator passes cannot measure those.

When implemented and validated, bump both variants together from 90.42,
review descriptions, export both VDFs and save the matching version backups
using `steam-layout-apply`.
