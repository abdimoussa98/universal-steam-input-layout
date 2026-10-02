# Steering cleanup audit — 2026-09-30

Scope: all **16 new layers in both variants**, plus the modified steering
commit transition. Fixes are generated in `build_touch_cleanup`; exports and
binding manifests have been regenerated. Added layer count remains 16 and every
input remains within three activator entries. Previous working layouts are backed up in `pre-steering/neptune/`; both Neptune
JSON/VDF pairs now contain this implementation. Original 36-layer candidate
exports remain unchanged.

## Findings and changes

Several new layers had no explicit touch-release path; protected menu layers
blocked touch entirely. An inherited Base RS touch could therefore expose its
entry behavior, while overridden LS touch lost the usual LST release cleanup.
The generated candidates now define both touch inputs on every new layer.

Every LS release removes LST Entry Point, Tap Cover and Temporary Gyro; every
RS release removes the corresponding RST trio. Releases are side-local, never
ordinary owner/global teardown. Guarded repeating stale-state recovery is a
separate activator, not a substitute for release cleanup.

Normal Modifier 0/1 long-hold transitions target LS Tap Cover. Their two thumb
releases now add that cover **before** the side-local removals. Protected menu
entries similarly add their matching silent Menu Tap Cover before removals.
No Fn is added by a protected entry's release. Completed normal/Mod 2 tap covers and repeat covers have cleanup-only release, preventing parent-transition resurrection.

The release-commit transition keeps edge/click recovery blocked; thumb release
now clears only local stick helpers, without committing, aborting or adding Fn.

## Per-layer exit review

Each row applies in both Default and Alternative. “Side cleanup” means the
corresponding LST/RST trio. Each non-cover layer has both release paths; since 90.7
the four covers inherit theirs.

| New layer | Main exit / cleanup | Thumb-release behavior |
|---|---|---|
| Steering | 2.5-second whole-family exit; menu entry exits steering; owner acquisition cancels fallback timing | Side cleanup only; no early exit or feedback |
| LS Entry Point | Center self-removes; driver acquisition retires guard | Side cleanup only; cannot retire one-time protection |
| R1/R2 W Key | Dominant release removes all temporary steering helpers, keeps membership; held opposite can acquire | Side cleanup; owner-specific guarded recovery retained on both sticks |
| L1/L2 S Key | Symmetric dominant cleanup/takeover | Same, with S-owner guard |
| LS Down Modifier 0 | True center removes maps and opens Down window; other directions remove/consume; inherited owner release clears branch | Add LS Tap Cover first, then side cleanup |
| LS Up Modifier 1 | Symmetric center/reversal lifecycle | Add LS Tap Cover first, then side cleanup |
| R1!L1 / R2!L2 Modifier 2 | Uncovered opposite release clears all; hold/action applies L1/L2 cover | Add existing L1/L2 cover before side cleanup; W-owner recovery guard |
| L1!R1 / L2!R2 Modifier 2 | Uncovered opposite release clears all; hold/action applies R1/R2 cover | Add existing R1/R2 cover before side cleanup; S-owner recovery guard |
| LS Tap Cover | True center clears normal maps and cover; owner/context teardown clears all | Inherits the bank's or owner's touch (90.7); re-adding the active cover is a no-op |
| LS Up Double Tap | Expiry/early resolution self-removes; second Up replaces with repeat; context/owner teardown cancels | Side cleanup only; no early wheel output |
| LS Down Double Tap | Symmetric window exits | Side cleanup only |
| LS Double Tap Cover | Direction release or center removes repeat and adds consumed cover; owner/context teardown clears | Inherits the owner's touch (90.7); no wheel or new modifier on thumb release |
| Menu Left Entry Point | Menu release removes protected pair/normal entry and emits eligible Escape; commit retires prefixed helper | Add Menu Left Tap Cover first, then side cleanup |
| Menu Right Entry Point | Symmetric Tab/commit handling | Add Menu Right Tap Cover first, then side cleanup |
| Menu Left Tap Cover | Menu release removes protected pair/normal entry silently; commit removes helper | Inherits the protected entry's touch (90.7); its cover add is a no-op once active |
| Menu Right Tap Cover | Symmetric silent cleanup | Same, from the Menu Right protected entry |

## Whole-input inheritance and recovery

The touch Release entry is installed with the full input contract because
Steam overrides whole inputs. W/S owners and ordered Modifier 2 variants retain
owner-specific Regular/chord stale-state recovery on both LS and RS. Shared
normal maps/covers/windows have repeating branch recovery gated by **either**
driving control; valid driving is protected, and with neither held the complete
temporary family is removed. They cannot infer a missed dominant release while
only the opposite remains held; that remains an explicit native recovery case,
not a claim that a shared either-control gate proves ownership.

Protected menus/cover recovery is guarded by their own held menu button and
removes only that menu's normal/protected entry and silent cover. Persistent
Steering and its entry guard have release-only touch inputs, avoiding accidental
Base touch-entry routing and avoiding thumb-triggered session/guard teardown.
No broad repeating removal is added to an otherwise valid held transition.

## Delay classification and ordering

- Modifier 0/1's 250 ms layer apply → complete LS Tap Cover on thumb release.
- Protected menu's 300 ms layer apply → complete matching Menu Tap Cover.
- Modifier 2's 200 ms layer apply → complete its opposite-side existing single cover.
- W/S 5 ms direction routing and consumed regular repeating routing → retain physical direction selection;
  do not unconditionally apply both banks or recreate a consumed transition.
- Repeat wheel's 5 ms delay, double-window expiry, fallback warning/exit → no
  semantic layer-apply completion on thumb release; never emit early wheel or
  exit feedback as cleanup.
- Existing Always On windows → unchanged self-first isolation. Their Double Tap
  definitions are not blindly removed after adding another layer. The normal
  LST/RST cleanup trio is Entry Point, Tap Cover and Temporary Gyro.

All six semantic delayed-parent releases execute add before removals in one
Release entry. Stored arrays contain the add last. Tests check execution order,
not merely command presence. Each parent's completed cover is independently
checked for no added layer on thumb release.

## Validation and device checks

26 lean binding tests cover exact side cleanup in all 32 new-layer stick inputs
per variant, early-completion targets/order, cleanup-only covers, owner/menu
recovery guards, family teardown, takeover and command budgets. Full suite:
**80 Python tests and 8 Node tests**. VDF serialization verifies keys/values/order.

Device checks: release either thumb before the normal hold/menu deadline;
confirm correct cover is installed with no Fn/wheel leak. Release again inside
the cover and confirm no parent reopens. Test stale owner/menu state after an
overlay, touch already held when a layer is added, and both-stick release near
owner/context changes. Thumb cleanup necessarily issues removals; recheck
ordinary window and fallback Long Press timing under those removals. Native
scheduler, held-output, and shared-cover/reversal gates remain pending.

Latest reuse follow-up: there are no steering-only W/S Tap Cover definitions.
W reuses L1/L2 Tap Cover, S reuses R1/R2 Tap Cover. Their original release and
side-guarded touch recovery retain all old commands/settings and append only
removal of the corresponding Steering Modifier 2 layer. No shared cleanup adds a steering layer, removes the
movement owner, or changes persistent Gyro. Original thumb releases are intact.

Normal consumed state is installed beneath Mod 2 before entry. Removing the corresponding Mod 2 layer exposes this state while retaining W/S. Owner
cleanup removes both reusable covers. Dominant release inherits its owner's
normal cleanup in both uncovered and covered phases; only uncovered opposite
release is the global quick exit. Combined tap covers are unchanged. Test both
ordinary Base/Gyro cover use and steering use; delayed lower-selector cancellation
and restored cover priority remain native gates.

## Final cleanup re-review

Reviewed the generated contracts against the JSON Structure rules for whole-input
inheritance, overlay ownership, scoped recovery, delayed-apply completion and
Always On isolation. The initial pass added no binding changes; the delayed-apply follow-up below corrects that review gap without adding layers.
Added regression checks resolve the effective owner input through actual nested
normal-map/consumed, pending-scroll, repeat and covered/uncovered Mod 2 stacks,
then execute release cleanup. Both variants leave only Base, Gyro and Steering.
Additional checks execute protected menu release and touch recovery: only that
menu's normal/protected entries and silent cover retire; eligible release emits
Tab/Escape once and covered release emits nothing.

All eight Fire Start Delay layer-apply paths per variant now have a matching
uninterruptible Regular Press removal with Hold to Repeat: four W/S Up/Down
selectors use 5/50 ms, the two protected menu entries use 300/350 ms, and the
two Mod 2 entries retain 200/250 ms. Each reset removes only its apply target.
The applied bank or cover overrides that whole input, stopping both parent
activators. Regression tests enumerate all delayed layer applies and check
reset scope, cadence and effective-input replacement. All inputs stay within
three activator entries.

The shared LS Tap Cover cannot use a bank-removal reset: it deliberately stays
above the bank, so that reset would continue stripping a valid modifier. Its
routing now uses Regular Press with 50 ms repeat and no Fire Start Delay, like
owner acquisition. It removes the opposite bank, adds the selected bank and
reasserts itself last; it never removes the selected bank or itself while held.
Center/direction release and owner cleanup still retire the appropriate layers.
Native re-add idempotence and priority remain acceptance gates, including whether
repeated routing interferes with mapped outputs or Mod 2 entry.

Normal hold consumption and fallback/window clocks use Long Press, not Fire
Start Delay. The shared repeat's delayed wheel output receives no layer-removal
reset. No new Always On actions or changes to existing Always On source groups
were introduced.

These checks validate binding structure and ordered command effects, not Steam's
event scheduler. In particular, simultaneous owner/thumb release can race a
thumb's early cover add against owner teardown; an already queued selector or
scroll callback may behave differently after layer removal. Existing guarded
recovery is retained, but immediate race-free behavior is not established.
Run the interruption, held-input and boundary cases in [ACCEPTANCE.md](ACCEPTANCE.md)
before promoting these candidates.

## Neptune installation validation

Applied both candidates byte-for-byte to Neptune at the user's request; see
[installation hashes](neptune-installation.json). Existing Neptune checks now
assert protected-menu transfer/commit, the four cloned gyro-disabled menu
helpers and the matching Steering Mod 2 removal in each reused single cover.
The held-input scanner still reports ten specific Long Press dependency paths
per variant. Its regression check pins those exact pending findings instead of
claiming zero findings or exempting steering generally. They cover hold
consumption and pending-scroll window entry; native acceptance remains open.
The full 80 Python / 8 Node checks validate these configuration contracts, not
completion of those device gates.
