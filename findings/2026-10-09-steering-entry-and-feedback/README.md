# Steering entry, driver recovery and feedback — 90.43

Both variants implement the approved
[plan](../../plans/2026-10-09-steering-entry-guard.md). Validation, both JSON/VDF
exports and matching 90.43 backups are complete. No new layers:
the existing runtime slot 65 becomes `Steering | LS: Entry Guard`, retaining
88 action layers and the other runtime IDs.

## Behavior by layer

| Layer | Change |
|---|---|
| `Transition Set 1` | Entry removes the transition, adds Steering with its existing beep/bump, then silently adds Entry Guard. |
| `Steering \| LS: Entry Guard` | Replaces the old fallback bindings with plain four-way WASD. An already-held movement, or the first movement after centered entry, is protected until direction or normal outer-edge Release. |
| `Steering` | Driver acquisition removes Entry Guard before its existing ramp cleanup and W/S add. Up/down still performs the full Steering-family clear at Soft Press threshold `29031`, repeating at `50 ms`, with the existing Low bump and one beep. |
| W/S driver layers | Up/down adds its modifier only while the driving button is held. Otherwise a repeating owner-family cleanup prevents stale drivers from rebuilding modifiers. |
| LS Modifier 0/1 | All 26 conditional fallback entries per variant cancel their modifier/cover while preserving a still-held W/S owner. The owner's own cleanup handles a missed driver release. |
| LS Modifier 0/1 and their Tap/Double Tap Covers | Eight direction inputs carry valid-driver guards and recovery through to the new owner cleanup. Existing cover delays and wheel-repeat timing remain. |
| Gyro Modifier 2 | The four toggle-off Release entries beep only on Gyro removal. Steering and guard cleanup removals are silent. |
| Steering Modifier 2 | Each of the two existing full-clear Release entries beeps only on Steering removal. Release conditions and haptic settings are unchanged. |

The broader two-bumper release-order fix and its proposed extra covers remain
deferred. All 16 Fn-add activators retain their Low bump and silent beep flag.
This release does not change the physical up/down threshold.

Entry Guard ends on a **direction Release or normal outer-edge Release**,
not necessarily a return to center. Rolling between directions can disarm
it; an up/down direction still fully held afterward may then clear Steering.
That follows the release-based behavior selected in the plan.

## Inheritance and recovery review

| While Entry Guard is active | Effective behavior |
|---|---|
| Stick touches, including a resting thumb at centered entry | Keep first-movement protection. Touch Releases clear only the corresponding ordinary touch helpers. |
| Driver pressed or carried into entry | Repeating acquisition removes the guard before adding W/S. The driver's existing modifiers then take over. |
| Fresh Start/Select | Start Press removes the guard before adding the Stateful menu Entry Point; Fn and menu-plus-stick clear remain available. |
| Opposite menu button carried through entry | Does not consume protection. Release it and press again for a fresh handoff. |
| Right-pad touch/click, left-pad click | Block helper-layer entry so no pad window can hide the guard's movement Releases. |
| Left-pad swipes | Direct Escape/Return/Tab/Backspace outputs; no helper layer. |
| Right-stick movement | Retains camera movement; blocks ramp-layer entry until the guard ends. |
| Full clear or stateful transition | Clears the renamed guard through the existing cleanup lists. Steering's two Always On windows remain first in its up/down clear. |

There are four precise R169/R170 input allowances for centered protection:
both stick touches and both stick edges. Driver/menu handoffs satisfy R171
by removing their source before adding another layer. They require no waiver.
Historical fallback and Entry Guard exceptions remain scoped to their old
layouts; presence/absence gates preserve the frozen builders.

Modifier recovery has two distinct duties. A modifier whose stick condition
has ended can remove itself while its driver remains valid. A driver whose
button is no longer held must stop adding modifiers and remove its own stale
family. Separating both sides prevents the original brief exposure of the
base clear and the missed-release re-add loop found during integration.

## Build and evidence

The [builder](build_candidate.py) extends frozen 90.42 and applies
[entry protection](entry_guard.py), [modifier recovery](modifier_recovery.py),
and [beep ownership](beeps.py) before the standard fix pipeline. Numeric
round trips preserve IDs; the generated candidates are pipeline fixed points.

The [change report](change-report.txt) was reviewed against the approved
scope. Each variant changes 63 inputs across 20 existing layers: 47 behavior
changes and 16 guard-reference renames. The rebuilt guard is separately shown
as a rename in the report. Menu, Gamepad and global-clear changes outside the
Steering/Gyro work are reference renames only. The [build provenance](rebuild-verification.json)
records matching parent rebuilds, candidate/live hashes, fixed-point results
and the reviewed variant descriptions.

```sh
python3 findings/2026-10-09-steering-entry-and-feedback/build_candidate.py
python3 findings/2026-10-09-steering-entry-and-feedback/build_candidate.py --install
python3 -m tools.audit_build
```

The release record includes the complete change reports, per-variant audit
results, regression results, scenario coverage and unverified assumptions.
The [new scenarios](../../tests/test_scenarios_90_43.py) cover both variants,
Gyro on/off, held input entry, centered first movement, deliberate handoffs,
missed releases, cleanup timing and exact beep requests. The
[static tests](../../tests/test_steering_entry_feedback.py) check the slot,
source settings, command order, cleanup lists and unchanged Fn feedback.

| Final verification | Result |
|---|---|
| [Build audit](build-audit.txt) | Budget, Window, Flow and Cleanup pass for both installed layouts. |
| [Scenario run](validation.log) | 281 methods pass: 225 live, 26 frozen 90.41 and 30 experimental 90.39. |
| [Regression results](validation.json) | 246 distinct cases pass across the initial and targeted follow-up runs. |
| [Changed-layer coverage](scenario-coverage.txt) | Every changed layer is reached; coverage recorded before the new backups. |
| [Beep inventory](beep-inventory.json) | Each variant has 32 beep-bearing entries and 32 beep flags; no entry requests multiple beeps. Ordered JSON/VDF layer commands and flags match. |
| [VDF export](export-verification.json) | Both serializers verify keys, values and order. |
| [Version backups](snapshot-manifest.json) | All four JSON/VDF copies match the live files byte for byte. |

The initial regression run had one failure: the historical R139 decision for
Steering's edge was stale after fallback became Entry Guard. Its presence
scope now requires Fallback Guard. The unchanged live assertion and all
77 affected Flow/exception/rule tests pass in the
[follow-up](validation-followup.log), including four new scope tests.
The other 169 regression cases passed in the initial run. This correction
changes audit applicability, not layout bindings or historical builders.

The full-held recovery scenario includes 1,664 missed-release combinations;
the scrolling-cover scenario adds 64. A separate
[modifier probe](modifier-recovery-verification.json) passes 768 held-driver
and 16 centered stale-driver cases. These remain simulator results; the
[unverified assumptions](unverified-assumptions.txt) and device checks below
record their limits.

Ready-to-load files:
[default VDF](../../neptune/single-set-default_hold-gyro_latest.vdf) and
[alternative VDF](../../neptune/single-set-alternative_hold-gyro_latest.vdf).
Backups are under [versions/neptune/90.43](../../versions/neptune/90.43/).

## Fresh-load checks on the Deck

1. Enter Steering with the stick held fully up/down; also enter centered with
   thumbs resting on either stick. The initial movement stays protected.
   Release it, then fully deflect again: one clear, one beep, one Low bump.
2. Hold W or S, make a shallow up/down push and center it, move the right
   stick, then push up/down again. The held driver must survive throughout.
   Also check recovery after releasing the driver in Steam's menu while the
   left stick stays deflected.
3. Toggle Base/Gyro in both driver press/release orders. Each successful
   toggle should sound once. Check Steering's existing successful full-clear
   route separately; its release-order asymmetry remains deferred.
4. While protected, check camera motion, the temporary pad restrictions,
   fresh menu handoff and both Fn bumps.

Simulation verifies configured events and modeled stacks. It cannot measure
physical Soft Press distance, native ordering between commands, missed-release
delivery, haptic sensation or audible beep suppression/coalescing.
